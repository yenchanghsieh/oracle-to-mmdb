# JPA Patterns: Oracle -> MariaDB

## 1. Entity Class — Column Definitions

Oracle codebases often use `columnDefinition` to pin DDL types. These must be removed or
replaced on migrated entities — Hibernate will infer the correct MariaDB type from the Java type.

### 1.1 String / text types

```java
// Oracle — REMOVE columnDefinition
@Column(columnDefinition = "VARCHAR2(255)")
private String name;

// MariaDB — let Hibernate infer VARCHAR(255)
@Column(length = 255)
private String name;

// Oracle CLOB
@Column(columnDefinition = "CLOB")
private String body;

// MariaDB — @Lob maps to LONGTEXT automatically
@Lob
@Column
private String body;

// Oracle NCLOB
@Column(columnDefinition = "NCLOB")
private String content;

// MariaDB
@Lob
@Column(columnDefinition = "LONGTEXT CHARACTER SET utf8mb4")
private String content;
```

### 1.2 Numeric types

```java
// Oracle NUMBER(19,2)
@Column(columnDefinition = "NUMBER(19,2)")
private BigDecimal amount;

// MariaDB — use precision/scale attributes
@Column(precision = 19, scale = 2)
private BigDecimal amount;

// Oracle NUMBER (integer-used)
@Column(columnDefinition = "NUMBER(10)")
private Integer count;

// MariaDB — no columnDefinition needed
@Column
private Integer count;
```

### 1.3 Binary / LOB types

```java
// Oracle BLOB
@Column(columnDefinition = "BLOB")
private byte[] attachment;

// MariaDB — @Lob maps to LONGBLOB
@Lob
@Column
private byte[] attachment;

// Oracle RAW(16) — e.g. for UUIDs stored as raw bytes
@Column(columnDefinition = "RAW(16)")
private byte[] id;

// MariaDB
@Column(columnDefinition = "VARBINARY(16)")
private byte[] id;
```

### 1.4 Date / time types

```java
// Oracle DATE (stores date + time)
@Column(columnDefinition = "DATE")
private Date createdAt;

// MariaDB — Oracle DATE includes time component; use DATETIME
@Column(columnDefinition = "DATETIME")
private LocalDateTime createdAt;

// Oracle TIMESTAMP
@Column(columnDefinition = "TIMESTAMP")
private Timestamp updatedAt;

// MariaDB
@Column
private LocalDateTime updatedAt;   // Hibernate maps LocalDateTime -> DATETIME(6)
```

---

## 2. Entity Class — ID Generation

### 2.1 Sequence → IDENTITY (standard case)

```java
// Oracle — REMOVE both annotations
@Id
@GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "user_seq")
@SequenceGenerator(name = "user_seq", sequenceName = "USER_SEQ", allocationSize = 1)
private Long id;

// MariaDB — AUTO_INCREMENT via IDENTITY
@Id
@GeneratedValue(strategy = GenerationType.IDENTITY)
private Long id;
```

### 2.2 MariaDB native sequence (10.3+) — use when sequence semantics are required

```java
// If you need explicit sequence control (e.g. gaps are not acceptable):
@Id
@GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "user_seq")
@SequenceGenerator(name = "user_seq", sequenceName = "user_seq",
                   allocationSize = 1, initialValue = 1)
private Long id;
```

Requires creating the sequence in MariaDB:
```sql
CREATE SEQUENCE user_seq START WITH 1 INCREMENT BY 1;
```

---

## 3. Named Queries on Entity Classes

### 3.1 @NamedQuery (JPQL) — largely portable

```java
// Usually no change needed — Hibernate translates JPQL to target dialect
@NamedQuery(name = "Order.findActive",
    query = "SELECT o FROM Order o WHERE o.status = 'ACTIVE'")

// Exception: scan for FUNCTION() calls (see sql-dialect-map.md Section 14.2)
@NamedQuery(name = "Order.findByStatus",
    query = "SELECT o FROM Order o WHERE FUNCTION('NVL', o.status, 'PENDING') = :s")
// Fix:
@NamedQuery(name = "Order.findByStatus",
    query = "SELECT o FROM Order o WHERE COALESCE(o.status, 'PENDING') = :s")
```

### 3.2 @NamedNativeQuery — requires full dialect conversion

```java
// Oracle
@NamedNativeQuery(name = "Order.findTopN",
    query = "SELECT * FROM orders WHERE status = :s AND ROWNUM <= :n",
    resultClass = Order.class)

// MariaDB
@NamedNativeQuery(name = "Order.findTopN",
    query = "SELECT * FROM orders WHERE status = :s LIMIT :n",
    resultClass = Order.class)
```

Apply all Phase 2 dialect conversions to the SQL string.

---

## 4. Spring Data Repository — @Query Methods

### 4.1 JPQL @Query (nativeQuery = false) — mostly portable

```java
// No change needed for standard JPQL
@Query("SELECT o FROM Order o WHERE o.status = :status AND o.customerId = :cid")
List<Order> findByStatusAndCustomer(@Param("status") String status,
                                    @Param("cid") Long cid);

// ONLY change needed: replace FUNCTION() wrappers (see sql-dialect-map.md Section 14.2)
```

Derived method names (`findByStatusAndCreatedAtAfter`, `countByStatus`, etc.) generate JPQL
internally — no SQL to convert. Verify only that the entity's table is in `migrated_tables[]`.

### 4.2 Native @Query (nativeQuery = true) — full dialect conversion required

```java
// Oracle
@Query(nativeQuery = true,
    value = "SELECT id, NVL(name,'Unknown') AS name FROM orders " +
            "WHERE status = :s AND ROWNUM <= :n")
List<Order> findOrders(@Param("s") String s, @Param("n") int n);

// MariaDB
@Query(nativeQuery = true,
    value = "SELECT id, IFNULL(name,'Unknown') AS name FROM orders " +
            "WHERE status = :s LIMIT :n")
List<Order> findOrders(@Param("s") String s, @Param("n") int n);
```

### 4.3 Native @Query with Pageable — countQuery is mandatory

Spring Data appends `LIMIT`/`OFFSET` to native queries when `Pageable` is passed.
A `countQuery` is always required for `Page<T>` return type.

```java
// Oracle — REMOVE manual ROWNUM pagination, ADD countQuery
// Before (broken pattern — manual pagination conflicts with Pageable):
@Query(nativeQuery = true,
    value = "SELECT * FROM (SELECT a.*, ROWNUM rn FROM orders a WHERE ROWNUM <= 20) WHERE rn > 10")
Page<Order> findPaged(Pageable pageable);

// MariaDB — let Pageable handle LIMIT; just provide base query + countQuery
@Query(nativeQuery = true,
    value = "SELECT * FROM orders WHERE status = :s",
    countQuery = "SELECT COUNT(*) FROM orders WHERE status = :s")
Page<Order> findByStatus(@Param("s") String s, Pageable pageable);
```

**Rule**: never write `LIMIT` or `OFFSET` in a native query that also accepts a `Pageable`.
Spring Data will append them automatically — having both causes double-pagination errors.

### 4.4 Modifying queries

```java
// Oracle
@Modifying
@Query(nativeQuery = true,
    value = "UPDATE orders SET status = :s, updated_at = SYSDATE WHERE id = :id")
int updateStatus(@Param("s") String s, @Param("id") Long id);

// MariaDB
@Modifying
@Query(nativeQuery = true,
    value = "UPDATE orders SET status = :s, updated_at = NOW() WHERE id = :id")
int updateStatus(@Param("s") String s, @Param("id") Long id);
```

Always pair `@Modifying` with `@Transactional` on the calling service method.

---

## 5. EntityManager — Direct Usage

### 5.1 Native queries via createNativeQuery

```java
// Oracle
List<Order> orders = entityManager.createNativeQuery(
    "SELECT * FROM orders WHERE ROWNUM <= 10 AND status = :s", Order.class)
    .setParameter("s", "ACTIVE")
    .getResultList();

// MariaDB
List<Order> orders = entityManager.createNativeQuery(
    "SELECT * FROM orders WHERE status = :s LIMIT 10", Order.class)
    .setParameter("s", "ACTIVE")
    .getResultList();
```

### 5.2 JPQL queries via createQuery — FUNCTION() cleanup only

```java
// Oracle JPQL with FUNCTION() — find and replace
entityManager.createQuery(
    "SELECT o FROM Order o WHERE FUNCTION('NVL', o.status, 'PENDING') = :s", Order.class);

// MariaDB
entityManager.createQuery(
    "SELECT o FROM Order o WHERE COALESCE(o.status, 'PENDING') = :s", Order.class);
```

### 5.3 Pagination via EntityManager (replace ROWNUM with setFirstResult/setMaxResults)

```java
// Oracle — manual ROWNUM pagination in SQL string
String sql = "SELECT * FROM orders WHERE status = :s AND ROWNUM <= :maxRow";
query.setParameter("maxRow", offset + pageSize);

// MariaDB — use JPA pagination API instead; works for both JPQL and native queries
entityManager.createNativeQuery("SELECT * FROM orders WHERE status = :s", Order.class)
    .setParameter("s", "ACTIVE")
    .setFirstResult(offset)        // 0-based
    .setMaxResults(pageSize)
    .getResultList();
```

---

## 6. Split Repository Pattern (Partial Migration)

When Oracle-resident and migrated entities exist in the same service, split repositories
into separate packages so each `@EnableJpaRepositories` picks up only the correct ones.

### Package layout

```
com.example.repository.mariadb/    <- scanned by mariadbEntityManagerFactory
com.example.repository.oracle/     <- scanned by oracleEntityManagerFactory
```

### Service layer — inject both

```java
@Service
public class FinanceService {
    private final OrderRepository orderRepo;       // MariaDB
    private final InvoiceRepository invoiceRepo;   // Oracle

    public FinanceSummary getSummary(Long orderId) {
        Order order = orderRepo.findById(orderId).orElseThrow();
        Invoice invoice = invoiceRepo.findByOrderId(orderId);
        return new FinanceSummary(order, invoice);
    }
}
```

### Entity package layout

```
com.example.entity.mariadb/    <- scanned by mariadbEntityManagerFactory.packages(...)
com.example.entity.oracle/     <- scanned by oracleEntityManagerFactory.packages(...)
```

Do NOT place Oracle and MariaDB entity classes in the same package — each EMF's
`.packages("com.example.entity.mariadb")` will cause it to pick up both, leading to
cross-dialect schema validation failures or incorrect DDL generation.

---

## 7. Schema Validation

When `spring.jpa.hibernate.ddl-auto=validate`, Hibernate compares entity metadata against
the actual database schema on startup. After migration, common failure points:

| Failure | Cause | Fix |
|---------|-------|-----|
| `Schema-validation: missing column` | Column renamed or `@Column(name=...)` mismatch | Align entity name with actual column |
| `Schema-validation: wrong column type` | `columnDefinition` still says `VARCHAR2` | Remove or update `columnDefinition` (see Section 1) |
| `Schema-validation: missing table` | Entity package scanned by wrong EMF | Move entity to correct package (see Section 6) |
| `Could not determine type for: java.time.LocalDateTime` | Missing Hibernate Java 8 time support | Add `hibernate-java8` dependency (Spring Boot 2.x only) |
| `SequenceStyleGenerator: could not locate sequence` | `@SequenceGenerator` still references Oracle sequence | Replace with `GenerationType.IDENTITY` (see Section 2) |

Run validation in a staging environment before prod. Use `ddl-auto: validate` not `update`
to avoid accidental schema mutations.

---

## 8. TypeHandlers and Custom Conversions

### 8.1 Boolean: Oracle NUMBER(1) → MariaDB BOOLEAN

Oracle stores booleans as `NUMBER(1)`. Hibernate's standard `BooleanType` handles this
without a custom converter in most cases. If a custom `AttributeConverter` exists, verify it:

```java
// Custom converter is usually unnecessary for MariaDB — remove if present:
@Converter(autoApply = true)
public class BooleanToNumberConverter implements AttributeConverter<Boolean, Integer> { ... }

// MariaDB TINYINT(1) / BOOLEAN maps directly to Java Boolean via Hibernate
@Column
private Boolean active;  // maps to TINYINT(1) — no converter needed
```

### 8.2 Timestamps: java.time.* support

Hibernate 5+ (Spring Boot 2.5+) supports `java.time.*` natively:

```java
@Column
private LocalDate birthDate;         // → DATE
private LocalDateTime createdAt;     // → DATETIME(6)
private OffsetDateTime updatedAt;    // → DATETIME(6) with offset handling
```

If on an older Hibernate (< 5), add the `hibernate-java8` module:
```xml
<dependency>
    <groupId>org.hibernate</groupId>
    <artifactId>hibernate-java8</artifactId>
</dependency>
```

### 8.3 CLOB → String

Oracle `CLOB` fields mapped as `String` with a `ClobTypeHandler` or `@Lob` need no special
handler in MariaDB. Remove any Oracle-specific type handler:

```java
// Oracle — remove ClobTypeHandler if it was registered via Hibernate TypeDef
// @TypeDef(name="clob", typeClass=org.hibernate.type.ClobType.class)  <- REMOVE

// MariaDB — @Lob on String is sufficient
@Lob
@Column
private String htmlContent;   // Hibernate maps to LONGTEXT
```

---

## 9. Grep Patterns for JPA Oracle Debt

Run these to build the file candidate list for Phase 3B:

```bash
# Sequence generators — all candidates for IDENTITY migration
grep -rn "GenerationType.SEQUENCE\|@SequenceGenerator" src/main/java --include="*.java"

# columnDefinition with Oracle types
grep -rn "columnDefinition.*VARCHAR2\|columnDefinition.*NUMBER\|columnDefinition.*CLOB\|columnDefinition.*BLOB" \
  src/main/java --include="*.java"

# Oracle dialect references
grep -rn "Oracle.*Dialect\|hibernate.dialect.*[Oo]racle" \
  src/main/java src/main/resources --include="*.java" --include="*.yml" --include="*.properties"

# Native queries
grep -rn "nativeQuery\s*=\s*true\|@NamedNativeQuery\|createNativeQuery" \
  src/main/java --include="*.java"

# FUNCTION() in JPQL
grep -rn "FUNCTION(" src/main/java --include="*.java"

# javax vs jakarta — identify which namespace the project uses
grep -rn "import javax.persistence\|import jakarta.persistence" \
  src/main/java --include="*.java" | head -5
```
