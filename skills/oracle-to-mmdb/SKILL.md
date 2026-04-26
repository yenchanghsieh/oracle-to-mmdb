---
name: oracle-to-mmdb
description: >
  Refactors codebases after an Oracle-to-MariaDB migration. Handles SQL dialect
  conversion, MyBatis mapper/XML updates, JPA entity and Spring Data repository
  refactoring, dual-datasource configuration, and partial migrations where only
  some tables have moved. Trigger when the user needs to migrate or fix
  Oracle-specific SQL/Java code for MariaDB, configure dual datasources, or
  route queries across both databases. Does not run tests — produces a
  test_checklist.md handoff instead.
---

# Oracle -> MariaDB Refactor Skill

## Usage Summary

1. Run discovery against the target Spring Boot project.
2. Confirm full or partial migration mode.
3. Confirm the migrated table registry.
4. Approve one conservative edit batch at a time.
5. Review `oracle-to-mmdb-report/blocked.md` for manual decisions.
6. Run compile/tests only after explicit approval.

## ⛔ HARD GATES — Do Not Cross Without User Confirmation

| Gate | Trigger | Required Response |
|------|---------|-------------------|
| GATE-0 | Phase 0A complete — file list output | `"proceed"` |
| GATE-1 | Migration Registry confirmed | `"confirmed"` |
| GATE-BATCH | Before each conservative edit batch | `"apply"` |

Do not batch across gates. Do not continue if the confirmation word has not been typed.

---

## Required First Action — State Initialization

Before any grep, analysis, or code change, create `/tmp/migration_state.json`:

```json
{
  "mode": null,
  "migrated_tables": [],
  "oracle_tables": [],
  "persistence_layers": {
    "mybatis": false,
    "jpa": false,
    "spring_data": false,
    "jdbc_template": false
  },
  "files": {
    "pending": [],
    "in_progress": null,
    "done": [],
    "skipped_oracle": [],
    "flagged_cross_db": [],
    "flagged_jpa_native": []
  },
  "current_phase": 0
}
```

Update this file after every action. This is the single source of truth for session recovery.

---

## Resume Protocol

If the session was interrupted:

1. Read `/tmp/migration_state.json`
2. Report to user: files done / in-progress / pending
3. Ask: *"Resume from Phase [X] on [in_progress]? Reply 'yes' or 'restart'."*
4. Do NOT re-run Phase 0A unless state file is missing or user says `"restart"`

---

## Scope Decision

Ask before touching any code:

> "Has the entire database been migrated to MariaDB, or only specific tables?
> If partial, please list the migrated tables."

Set `mode` to `"full"` or `"partial"` in `migration_state.json`.
Full migration skips Phase 0B entirely. Partial migration requires Phase 0B before any edits.

---

## Execution Rules

Enterprise conservative mode is the default. Use helper scripts and optional read-only agents for discovery, but perform project edits sequentially from the coordinator. Never edit a SQL statement unless its table classification and conversion rule are both recorded in the current report.

1. Re-read `migration_state.json` at the start of every turn
2. Max 2 files open simultaneously; state `"Closing [filename] from context"` before opening the next
3. Processing order: config → entities → repositories → mappers → DAOs → services
4. After each file: update state JSON and show diff summary
5. Files > ~400 lines: split at method/query boundaries
6. Targeted replacements only — never rewrite entire files
7. Reserve ~20k tokens as working buffer — save state, output checkpoint message, and stop if approaching limit

Enterprise default: ask for approval before each edit batch, then show a diff summary after every file. Stop immediately if an edit reveals unresolved table ownership, dynamic table names, or cross-database behavior not present in the approved batch.

---

## Phase 0A: Discovery

### 0A.1 Find Oracle candidates

Run script-first discovery:

```bash
python3 skills/oracle-to-mmdb/scripts/discover.py <spring-boot-project-root>
```

Use manual `rg` or `grep` checks as fallback validation, not the primary report source.

For large enterprise projects, use read-only discovery agents before editing:

1. Config agent
2. JPA agent
3. MyBatis agent
4. Service/transaction agent
5. Dialect research agent when target versions are unknown

Load `multi-agent-workflow.md` before dispatching agents. Agents produce reports only; the coordinator performs all edits.

```bash
# SQL-level Oracle patterns
grep -rl --include="*.java" --include="*.xml" --include="*.properties" --include="*.yml" \
  -e "ROWNUM" -e "ROWID" -e "NVL\b" -e "DECODE\b" -e "SYSDATE" -e "TO_DATE" \
  -e "CONNECT BY" -e "DUAL" -e "MERGE INTO" -e "oracle" -e "OracleDriver" \
  -e "ojdbc" -e "oracle.jdbc" \
  .

# JPA/Hibernate Oracle patterns
grep -rl --include="*.java" --include="*.yml" --include="*.properties" \
  -e "Oracle.*Dialect" -e "SequenceGenerator" -e "GenerationType.SEQUENCE" \
  -e "nativeQuery\s*=\s*true" -e "NamedNativeQuery" \
  -e "columnDefinition.*VARCHAR2" -e "columnDefinition.*NUMBER" \
  -e "columnDefinition.*CLOB"    -e "columnDefinition.*BLOB" \
  .
```

### 0A.2 Detect persistence layers

```bash
grep -rl --include="*.java" --include="*.xml" \
  -e "@Mapper" -e "SqlSession" -e "MapperScan" . | head -3        # MyBatis

grep -rl --include="*.java" \
  -e "@Entity" -e "JpaRepository" -e "EntityManager" . | head -3  # JPA / Spring Data

grep -rl --include="*.java" \
  -e "JdbcTemplate" -e "NamedParameterJdbcTemplate" . | head -3   # JdbcTemplate
```

Set `persistence_layers` flags in `migration_state.json`. Report detected layers to user.

### 0A.3 Categorize and populate pending list

Categorize each candidate file by type and populate `files.pending[]` in `migration_state.json`.

⛔ **GATE-0**: Show full categorized file list. Wait for `"proceed"`.

---

## Phase 0B: Table Classification *(partial migration only — skip if full)*

### 0B.1 Build Migration Registry

Confirm migrated table list with user. Record confirmed tables under MIGRATED, ORACLE-ONLY, and CROSS-DB keys in `migration_state.json`.

⛔ **GATE-1**: Show registry. Wait for `"confirmed"`.

### 0B.2 Classify every SQL/JPQL statement

Apply before touching any query — in MyBatis XML, `@Query`, `@NamedNativeQuery`,
`EntityManager.createNativeQuery()`, and inline JdbcTemplate SQL equally.

Use `classify_sql.py` logic for every SQL statement. A statement is editable only when classification is `MARIADB` and all applied conversion rules are `safe_auto_convert` or explicitly approved after review.

```
FOR each SQL/JPQL statement:
  1. Extract all table names (FROM, JOIN, INTO, UPDATE)
     For JPQL: resolve entity names → table names via @Table(name=...)
  2. ALL tables in migrated_tables[]?
        YES → [MARIADB] — proceed to Phase 2 conversion
        NO  → ALL tables in oracle_tables[]?
                YES → [ORACLE] — add comment, SKIP
                NO  → [CROSS-DB] — add comment, add to flagged_cross_db[], SKIP
  3. Never edit a query without a classification label

SPECIAL CASES:
  - JPQL non-native @Query: classify by entity table; only scan for FUNCTION() calls
  - Spring Data derived methods (findByX): classify at entity level only
  - Criteria API / Specifications: classify at entity level only
```

Helper — extract table names:
```bash
grep -oiP '(?<=\bFROM\s|JOIN\s|INTO\s|UPDATE\s)\w+' <file> | sort -u
# JPQL: resolve entity → table
grep -A2 "@Table" <EntityClass>.java | grep "name\s*="
```

### 0B.3 Cross-DB query default path

Default: **split into two queries, merge in Java service layer.**
Present other options (CDC/ETL, keep on Oracle, DB link) only if user asks or split is infeasible.

---

## Phase 1: Configuration

*Load `config-changes.md`. Unload after.*

**Full migration — do:**
- Replace ojdbc → mariadb-java-client in pom.xml
- Update `spring.datasource.*` to MariaDB URL + driver
- Replace Oracle Hibernate dialect with `MariaDBDialect` (or remove to auto-detect)
- Remove Oracle-specific Hibernate properties

**Partial migration — do:**
- Keep ojdbc, add mariadb-java-client
- Configure two named datasources in application.yml
- Wire separate `SqlSessionFactory` (MyBatis) and/or `EntityManagerFactory` (JPA) per datasource
- Set `@Primary` on MariaDB beans; `@Qualifier` on all mapper/repository injections
- Set Hibernate dialect per `EntityManagerFactory` via JPA properties map

See `config-changes.md` for all details and examples.

⛔ **GATE-BATCH** before applying approved config changes; show a diff summary after each config file.

---

## Phase 2: SQL Dialect Conversion

*Load `sql-dialect-map.md`. Unload after. Partial: apply to [MARIADB]-classified queries only.*

All conversion patterns are in `sql-dialect-map.md` — string/date/numeric functions, null handling,
control flow, aggregation, sequences, pagination, set ops, joins, data types, DML, Oracle hints,
and JPQL portability rules.

⛔ **GATE-BATCH** before applying approved SQL changes; show a diff summary after each changed file.

---

## Phase 3A: MyBatis Mapper Refactoring

*Skip if `persistence_layers.mybatis = false`.*
*Load `mybatis-patterns.md`. Unload after.*

**Per file:**
1. Classify every query (Phase 0B.2)
2. Convert [MARIADB] queries
3. Add classification comments to [ORACLE] queries; do not edit them
4. Add [CROSS-DB] queries to `flagged_cross_db[]`
5. Verify resultMap / parameterType / resultType still valid
6. Check dynamic SQL tags (if, choose, foreach) for embedded Oracle SQL

See `mybatis-patterns.md` for all conversion patterns and examples.

⛔ **GATE-BATCH** before applying approved mapper changes; show a diff summary after each mapper file.

---

## Phase 3B: JPA / Spring Data Refactoring

*Skip if `persistence_layers.jpa = false` AND `persistence_layers.spring_data = false`.*
*Load `jpa-patterns.md`. Unload after.*

**Process order:** entity classes → repository interfaces → DAO classes.

**Entity classes — for each entity in `migrated_tables[]`:**
- Replace `GenerationType.SEQUENCE` + `@SequenceGenerator` → `GenerationType.IDENTITY`
- Remove/replace Oracle `columnDefinition` values (VARCHAR2, NUMBER, CLOB, BLOB)
- Convert `@NamedNativeQuery` SQL using Phase 2 rules
- Scan `@NamedQuery` JPQL for `FUNCTION()` calls

**Repository interfaces:**
- Derived method names: classify at entity level only; no SQL to convert
- JPQL `@Query` (non-native): scan for `FUNCTION()` calls only
- Native `@Query`: full Phase 2 conversion; add to `flagged_jpa_native[]`
- Native `@Query` + `Pageable`: ensure `countQuery` exists; remove any manual LIMIT

**DAO classes with EntityManager:**
- `createNativeQuery()`: full Phase 2 conversion
- `createQuery()` JPQL: scan for `FUNCTION()` calls only
- Replace ROWNUM-based pagination → `setFirstResult()` / `setMaxResults()`

See `jpa-patterns.md` for all code patterns and examples.

⛔ **GATE-BATCH** before applying approved entity/repository/DAO changes; show a diff summary after each file.

---

## Phase 4: Java Import and Driver Cleanup

- **Full migration**: remove `oracle.jdbc.*` imports; add `org.mariadb.jdbc.Driver`
- **Partial migration**: keep Oracle imports; add MariaDB alongside
- Grep for remaining inline Oracle SQL in service layer:

```bash
grep -n "createNativeQuery\|JdbcTemplate\|ROWNUM\|NVL(\|SYSDATE\|DECODE(\|FROM DUAL\|\.NEXTVAL" \
  src/main/java/**/*.java
```

⛔ **GATE-BATCH** before applying approved Java cleanup changes; show a diff summary after each file.

---

## Phase 5: Pagination Audit

Cross-check that all pagination was handled correctly in Phases 3A/3B.

| Pattern | Expected outcome |
|---------|-----------------|
| MyBatis ROWNUM | Replaced with `LIMIT #{offset}, #{pageSize}` |
| Spring Data JPQL + Pageable | Unchanged — portable |
| Spring Data native + Pageable | Has `countQuery`; no manual LIMIT in query string |
| EntityManager native | Uses `setFirstResult()` / `setMaxResults()` — no ROWNUM |

Flag any remaining ROWNUM in [MARIADB]-classified queries as a blocker before proceeding.

---

## Phase 6: Testing Handoff

Testing is **not** part of this skill's execution scope. Do not attempt to run tests.
Output `test_checklist.md` for the developer, then stop.

**Checklist must cover:**

*General*: unit tests, MariaDB integration tests, pagination/dates/nulls/auto-increment,
[partial] Oracle tests still pass, [partial] datasource routing verified.

*MyBatis*: [MARIADB] queries syntax-clean, useGeneratedKeys correct, dynamic SQL valid,
LIMIT pagination correct.

*JPA / Spring Data*: Hibernate schema validation passes, IDENTITY inserts correct,
all `flagged_jpa_native[]` entries verified, `FUNCTION()` replacements tested,
`Page<T>` totalElements correct, no double-LIMIT on native+Pageable,
`@Lob` fields round-trip, [partial] Oracle repos use Oracle datasource,
[partial] no EMF cross-contamination.

*Cross-datasource risk*: methods writing to both datasources marked
`// TODO: CROSS-DB TRANSACTION RISK`. Resolution options: JTA (Atomikos/Bitronix),
compensating logic, restructure, Saga pattern.

---

## Reference Files

| File | Contents | Load in phase |
|------|----------|---------------|
| `config-changes.md` | pom.xml, YAML, datasource bean classes, javax/jakarta, transaction routing | Phase 1 |
| `sql-dialect-map.md` | Full SQL conversion table + JPQL portability patterns | Phase 2 |
| `mybatis-patterns.md` | Split mapper, XML conversions, pagination, selectKey, TypeHandlers | Phase 3A |
| `jpa-patterns.md` | Entity columns/IDs, @Query patterns, Pageable rules, split repository, schema validation | Phase 3B |
| `multi-agent-workflow.md` | Read-only agent scopes and report contracts | Discovery |
| `conservative-edit-policy.md` | Enterprise edit gates and blocked-change rules | Before edits |
