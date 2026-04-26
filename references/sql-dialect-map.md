# SQL Dialect Map: Oracle -> MariaDB

## 1. String Functions

| Oracle | MariaDB |
|--------|---------|
| 'a' || 'b' | CONCAT('a','b') or keep || (both work) |
| SUBSTR(s, pos, len) | SUBSTRING(s, pos, len) |
| INSTR(s, sub) | LOCATE(sub, s) |
| LENGTH(s) | CHAR_LENGTH(s) for chars |
| CHR(n) | CHAR(n) |
| LPAD/RPAD/LTRIM/RTRIM/TRIM/UPPER/LOWER/REPLACE | same in MariaDB |
| REGEXP_REPLACE(s, pat, rep) | REGEXP_REPLACE(s, pat, rep) -- MariaDB 10.0+ |

## 2. Date/Time Functions

| Oracle | MariaDB |
|--------|---------|
| SYSDATE | NOW() or CURRENT_TIMESTAMP |
| SYSTIMESTAMP | NOW(6) |
| TO_DATE('2023-01-01','YYYY-MM-DD') | STR_TO_DATE('2023-01-01','%Y-%m-%d') |
| TO_CHAR(date,'YYYY-MM-DD') | DATE_FORMAT(date,'%Y-%m-%d') |
| TO_CHAR(date,'HH24:MI:SS') | TIME_FORMAT(date,'%H:%i:%s') |
| TRUNC(date) | DATE(date) |
| TRUNC(date,'MM') | DATE_FORMAT(date,'%Y-%m-01') |
| ADD_MONTHS(date, n) | DATE_ADD(date, INTERVAL n MONTH) |
| MONTHS_BETWEEN(d1, d2) | TIMESTAMPDIFF(MONTH, d2, d1) |
| LAST_DAY(date) | LAST_DAY(date) -- same |
| EXTRACT(YEAR FROM date) | YEAR(date) |
| date + 1 (add 1 day) | DATE_ADD(date, INTERVAL 1 DAY) |

### Format code mapping

| Oracle | MariaDB | Meaning |
|--------|---------|---------|
| YYYY | %Y | 4-digit year |
| MM | %m | Month number |
| DD | %d | Day |
| HH24 | %H | 24h hour |
| MI | %i | Minutes |
| SS | %s | Seconds |
| MON | %b | Abbreviated month |
| AM/PM | %p | AM/PM |

## 3. Numeric Functions

| Oracle | MariaDB |
|--------|---------|
| TRUNC(n, d) | TRUNCATE(n, d) |
| ROUND/MOD/POWER/SQRT/ABS/CEIL/FLOOR/SIGN | same in MariaDB |
| TO_NUMBER(s) | CAST(s AS DECIMAL) or s + 0 |

## 4. Null Handling

| Oracle | MariaDB |
|--------|---------|
| NVL(x, default) | IFNULL(x, default) |
| NVL2(x, notnull_val, null_val) | IF(x IS NOT NULL, notnull_val, null_val) |
| NULLIF(a, b) | NULLIF(a, b) -- same |
| COALESCE(a, b, c) | COALESCE(a, b, c) -- same |

## 5. Control Flow

| Oracle | MariaDB |
|--------|---------|
| DECODE(x, v1,r1, v2,r2, default) | CASE WHEN x=v1 THEN r1 WHEN x=v2 THEN r2 ELSE default END |
| CASE WHEN ... END | same in MariaDB |

## 6. Aggregation and Analytics

| Oracle | MariaDB |
|--------|---------|
| LISTAGG(col,',') WITHIN GROUP (ORDER BY col) | GROUP_CONCAT(col ORDER BY col SEPARATOR ',') |
| ROW_NUMBER() OVER (...) | same -- MariaDB 10.2+ |
| RANK() / DENSE_RANK() / LAG() / LEAD() | same -- MariaDB 10.2+ |
| PIVOT | No native -- use MAX(CASE WHEN ... END) pattern |

## 7. Sequence and Identity

| Oracle | MariaDB |
|--------|---------|
| seq.NEXTVAL | NEXT VALUE FOR seq (MariaDB 10.3+) |
| Column DEFAULT seq.NEXTVAL | AUTO_INCREMENT (preferred) |

JPA: Replace GenerationType.SEQUENCE + @SequenceGenerator with GenerationType.IDENTITY.

## 8. Pagination

| Oracle | MariaDB |
|--------|---------|
| WHERE ROWNUM <= N | LIMIT N |
| Nested ROWNUM pagination | LIMIT offset, count |

```sql
-- Oracle pagination
SELECT * FROM (
  SELECT a.*, ROWNUM rnum FROM (SELECT col FROM t ORDER BY id) a WHERE ROWNUM <= 20
) WHERE rnum > 10

-- MariaDB
SELECT col FROM t ORDER BY id LIMIT 10, 10
```

## 9. Set Operations

| Oracle | MariaDB |
|--------|---------|
| MINUS | EXCEPT |
| INTERSECT | INTERSECT -- MariaDB 10.3+ |
| UNION / UNION ALL | same |

## 10. Joins and Hierarchical Queries

| Oracle | MariaDB |
|--------|---------|
| (+) outer join | Use standard LEFT/RIGHT JOIN |
| FROM DUAL | Remove entirely |
| CONNECT BY PRIOR (tree) | WITH RECURSIVE CTE |

```sql
-- Oracle CONNECT BY
SELECT LEVEL, name FROM categories
CONNECT BY PRIOR id = parent_id START WITH parent_id IS NULL

-- MariaDB recursive CTE
WITH RECURSIVE tree AS (
  SELECT id, name, parent_id, 1 AS lvl FROM categories WHERE parent_id IS NULL
  UNION ALL
  SELECT c.id, c.name, c.parent_id, t.lvl+1 FROM categories c JOIN tree t ON c.parent_id=t.id
)
SELECT lvl, name FROM tree
```

## 11. Data Types

| Oracle | MariaDB |
|--------|---------|
| VARCHAR2(n) | VARCHAR(n) |
| NUMBER(p,s) | DECIMAL(p,s) |
| NUMBER (no precision) | DECIMAL / INT / BIGINT by use case |
| DATE (includes time) | DATETIME |
| TIMESTAMP | DATETIME(6) |
| CLOB | LONGTEXT |
| NCLOB | LONGTEXT CHARACTER SET utf8mb4 |
| BLOB | LONGBLOB |
| RAW(n) | VARBINARY(n) |
| LONG RAW | LONGBLOB |
| BOOLEAN (PL/SQL) | TINYINT(1) or BOOLEAN |

## 12. DML Patterns

MERGE INTO -> INSERT ... ON DUPLICATE KEY UPDATE:
```sql
-- Oracle
MERGE INTO target t USING source s ON (t.id = s.id)
WHEN MATCHED THEN UPDATE SET t.name = s.name
WHEN NOT MATCHED THEN INSERT (id, name) VALUES (s.id, s.name)

-- MariaDB
INSERT INTO target (id, name)
SELECT id, name FROM source
ON DUPLICATE KEY UPDATE name = VALUES(name)
```

INSERT ALL -> multi-row INSERT:
```sql
-- Oracle
INSERT ALL
  INTO t VALUES (1,'a') INTO t VALUES (2,'b')
SELECT 1 FROM DUAL

-- MariaDB
INSERT INTO t VALUES (1,'a'), (2,'b')
```

## 13. Oracle Hints

| Oracle hint | MariaDB approach |
|-------------|-----------------|
| /*+ FULL(t) */ | Remove, let optimizer decide |
| /*+ ORDERED */ | STRAIGHT_JOIN |
| /*+ INDEX(t IDX) */ | USE INDEX (IDX) after table name |
| /*+ NO_INDEX(t IDX) */ | IGNORE INDEX (IDX) |

```sql
-- Oracle
SELECT /*+ INDEX(t MY_INDEX) */ * FROM my_table t WHERE id = 1

-- MariaDB
SELECT * FROM my_table USE INDEX (MY_INDEX) WHERE id = 1
```

---

## 14. JPQL-Specific Patterns (JPA / Spring Data)

JPQL is largely database-agnostic — Hibernate translates it to the target dialect automatically.
However, Oracle codebases often embed Oracle-specific expressions via `FUNCTION()` or
`@NamedNativeQuery`. This section covers what to scan for.

### 14.1 Portability rules

| Query type | Portability | Action |
|------------|-------------|--------|
| JPQL derived method (`findByStatus`) | ✅ Fully portable | No change needed |
| JPQL `@Query` (no nativeQuery) | ✅ Mostly portable | Scan for `FUNCTION()` calls only |
| Native `@Query` (`nativeQuery=true`) | ❌ Not portable | Full Phase 2 dialect conversion |
| `@NamedNativeQuery` on entity | ❌ Not portable | Full Phase 2 dialect conversion |
| `EntityManager.createNativeQuery()` | ❌ Not portable | Full Phase 2 dialect conversion |
| `EntityManager.createQuery()` (JPQL) | ✅ Mostly portable | Scan for `FUNCTION()` calls only |

### 14.2 FUNCTION() wrapper — Oracle-specific calls in JPQL

Oracle codebases sometimes use `FUNCTION('oracle_func', ...)` in JPQL to call Oracle-specific
functions. These must be replaced with portable JPQL equivalents or removed.

```java
// Oracle JPQL — using FUNCTION() to call NVL
@Query("SELECT o FROM Order o WHERE FUNCTION('NVL', o.status, 'PENDING') = :s")
List<Order> findOrders(@Param("s") String s);

// MariaDB — COALESCE is standard JPQL, no FUNCTION() wrapper needed
@Query("SELECT o FROM Order o WHERE COALESCE(o.status, 'PENDING') = :s")
List<Order> findOrders(@Param("s") String s);
```

Common `FUNCTION()` replacements:

| Oracle FUNCTION() call | JPQL portable equivalent |
|------------------------|--------------------------|
| `FUNCTION('NVL', x, y)` | `COALESCE(x, y)` |
| `FUNCTION('DECODE', x, v, r, d)` | `CASE WHEN x = v THEN r ELSE d END` |
| `FUNCTION('TO_CHAR', d, 'YYYY-MM-DD')` | Use native query or format in Java |
| `FUNCTION('TRUNC', d)` | `FUNCTION('DATE', d)` or switch to native query |
| `FUNCTION('ADD_MONTHS', d, n)` | Switch to native query |

### 14.3 JPQL that references Oracle column types

Column type issues surface at schema validation, not in JPQL strings — fix is in the `@Entity` class. See `jpa-patterns.md` Section 1.

### 14.4 Oracle-resident entity scan trap

Spring Data derived query methods look safe but still route to the wrong datasource if the
repository package is picked up by the wrong `@EnableJpaRepositories`. Always verify:

```
com.example.repository.mariadb.*  → scanned by mariadbEntityManagerFactory only
com.example.repository.oracle.*   → scanned by oracleEntityManagerFactory only
```

A `findByStatus()` method on an Oracle-resident entity pointing to the MariaDB EMF will
silently query the wrong database (or fail at startup with a "table not found" error).

### 14.5 Grep pattern to find all JPQL / native queries

```bash
# Find all @Query annotations
grep -rn "@Query" src/main/java --include="*.java"

# Find native queries specifically
grep -rn "nativeQuery\s*=\s*true" src/main/java --include="*.java"

# Find FUNCTION() calls in JPQL
grep -rn "FUNCTION(" src/main/java --include="*.java"

# Find NamedNativeQuery on entities
grep -rn "@NamedNativeQuery\|@NamedQuery" src/main/java --include="*.java"

# Find EntityManager native query calls
grep -rn "createNativeQuery" src/main/java --include="*.java"
```
