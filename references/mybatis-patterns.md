# MyBatis Patterns: Oracle -> MariaDB

## 1. Split Mapper Pattern (Partial Migration)

When a single mapper contains both [MARIADB] and [ORACLE] queries, split it into two
mapper interfaces each bound to the correct SqlSessionFactory via separate @MapperScan packages.

### Before (problematic)
```
com.example.mapper.FinanceMapper      <- mixed Oracle + MariaDB queries
```

### After (split)
```
com.example.mapper.mariadb.PaymentMapper  <- bound to mariadbSqlSessionFactory
com.example.mapper.oracle.InvoiceMapper   <- bound to oracleSqlSessionFactory
```

Service layer injects and calls both:
```java
@Service
public class FinanceService {
    private final PaymentMapper paymentMapper;  // MariaDB
    private final InvoiceMapper invoiceMapper;  // Oracle

    public FinanceSummary getSummary(Long id) {
        return new FinanceSummary(
            paymentMapper.getPayment(id),   // hits MariaDB
            invoiceMapper.getInvoice(id)    // hits Oracle
        );
    }
}
```

---

## 2. Common XML Conversions

Only apply to [MARIADB]-classified queries.

```xml
<!-- BEFORE (Oracle) -->
<select id="findActive" resultType="User">
  SELECT id, NVL(name, 'Unknown') AS name, SYSDATE AS ts
  FROM users WHERE status = 'ACTIVE' AND ROWNUM <= 100
</select>

<!-- AFTER (MariaDB) -->
<select id="findActive" resultType="User">
  SELECT id, IFNULL(name, 'Unknown') AS name, NOW() AS ts
  FROM users WHERE status = 'ACTIVE' LIMIT 100
</select>
```

Conversion cheat sheet:

| Oracle | MariaDB |
|--------|---------|
| NVL(x,y) | IFNULL(x,y) |
| SYSDATE | NOW() |
| TO_DATE('s','YYYY-MM-DD') | STR_TO_DATE('s','%Y-%m-%d') |
| TO_CHAR(d,'YYYY-MM-DD') | DATE_FORMAT(d,'%Y-%m-%d') |
| TO_CHAR(d,'HH24:MI:SS') | TIME_FORMAT(d,'%H:%i:%s') |
| TRUNC(date) | DATE(date) |
| TRUNC(n,d) | TRUNCATE(n,d) |
| ADD_MONTHS(d,n) | DATE_ADD(d, INTERVAL n MONTH) |
| DECODE(x,v,r,def) | CASE WHEN x=v THEN r ELSE def END |
| FROM DUAL | (remove) |
| ROWNUM <= N | LIMIT N (move outside WHERE) |
| MINUS | EXCEPT |
| LISTAGG(c,',') WITHIN GROUP (...) | GROUP_CONCAT(c ORDER BY ... SEPARATOR ',') |

Oracle -> MariaDB format codes: YYYY->%Y, MM->%m, DD->%d, HH24->%H, MI->%i, SS->%s

---

## 3. Pagination

```xml
<!-- BEFORE: Oracle nested ROWNUM -->
<select id="list" parameterType="PageParam" resultType="User">
  SELECT * FROM (
    SELECT u.*, ROWNUM rnum FROM (
      SELECT id, name FROM users ORDER BY created_at DESC
    ) u WHERE ROWNUM &lt;= #{endRow}
  ) WHERE rnum &gt; #{startRow}
</select>

<!-- AFTER: MariaDB LIMIT -->
<select id="list" parameterType="PageParam" resultType="User">
  SELECT id, name FROM users
  ORDER BY created_at DESC
  LIMIT #{offset}, #{pageSize}
</select>
```

PageParam Java class:
```java
public class PageParam {
    private int pageNumber; // 1-based
    private int pageSize;
    public int getOffset() { return (pageNumber - 1) * pageSize; }
}
```

PageHelper plugin alternative -- SQL stays as plain SELECT, plugin appends LIMIT automatically:
```xml
<dependency>
    <groupId>com.github.pagehelper</groupId>
    <artifactId>pagehelper-spring-boot-starter</artifactId>
    <version>1.4.6</version>
</dependency>
```
```java
PageHelper.startPage(pageNum, pageSize);
List<User> list = userMapper.listUsers();
PageInfo<User> info = new PageInfo<>(list);
```

---

## 4. SelectKey -> useGeneratedKeys

```xml
<!-- BEFORE: Oracle sequence -->
<insert id="insert" parameterType="User">
  <selectKey keyProperty="id" resultType="long" order="BEFORE">
    SELECT user_seq.NEXTVAL FROM DUAL
  </selectKey>
  INSERT INTO users (id, name, email) VALUES (#{id}, #{name}, #{email})
</insert>

<!-- AFTER: MariaDB AUTO_INCREMENT -->
<insert id="insert" parameterType="User"
        useGeneratedKeys="true" keyProperty="id" keyColumn="id">
  INSERT INTO users (name, email) VALUES (#{name}, #{email})
</insert>
```

Remove id from the INSERT column list. Generated key is set back on the User object.

MariaDB sequence (10.3+) if needed:
```xml
<selectKey keyProperty="id" resultType="long" order="BEFORE">
  SELECT NEXT VALUE FOR user_seq
</selectKey>
```

---

## 5. Dynamic SQL Patterns

ROWNUM guard -> move LIMIT outside WHERE block:
```xml
<!-- BEFORE -->
<where>
  <if test="status != null">AND status = #{status}</if>
  <if test="maxRows != null">AND ROWNUM &lt;= #{maxRows}</if>
</where>

<!-- AFTER -->
<where>
  <if test="status != null">AND status = #{status}</if>
</where>
<if test="maxRows != null">LIMIT #{maxRows}</if>
```

Date range:
```xml
<!-- BEFORE -->
AND created_at BETWEEN TO_DATE(#{start}, 'YYYY-MM-DD') AND TO_DATE(#{end}, 'YYYY-MM-DD')

<!-- AFTER (pass Java LocalDate -- JDBC handles conversion) -->
AND created_at BETWEEN #{start} AND #{end}
```

TO_CHAR date filter:
```xml
<!-- BEFORE --> AND TO_CHAR(created_at, 'YYYY-MM-DD') = #{searchDate}
<!-- AFTER  --> AND DATE(created_at) = #{searchDate}
```

---

## 6. Result Mapping

CLOB -> LONGTEXT (no handler needed):
```xml
<!-- BEFORE -->
<result property="body" column="body" jdbcType="CLOB"
        typeHandler="org.apache.ibatis.type.ClobTypeHandler"/>
<!-- AFTER -->
<result property="body" column="body"/>
```

Oracle DATE (stores time) -> DATETIME:
```xml
<result property="createdAt" column="created_at" javaType="java.time.LocalDateTime"/>
```

---

## 7. Annotation-Based Mappers

```java
// Function conversion
@Select("SELECT IFNULL(name, 'N/A') FROM users WHERE id = #{id}")
String getUserName(Long id);

// Identity insert
@Insert("INSERT INTO users (name) VALUES (#{name})")
@Options(useGeneratedKeys = true, keyProperty = "id")
void insertUser(User user);

// Pagination
@Select("SELECT * FROM users LIMIT #{offset}, #{size}")
List<User> listUsers(@Param("offset") int offset, @Param("size") int size);
```

---

## 8. TypeHandlers

Boolean: Oracle NUMBER(1) with custom handler -> MariaDB BOOLEAN (TINYINT(1)).
Standard MyBatis BooleanTypeHandler works without modification.

Timestamps: MyBatis 3.4.5+ supports java.time.* natively, no custom handler needed.
```xml
<result property="createdAt" column="created_at" javaType="java.time.LocalDateTime"/>
<result property="date"      column="date"       javaType="java.time.LocalDate"/>
```

Strings: Remove ClobTypeHandler. MariaDB LONGTEXT maps to String automatically.
