# Multi-Agent Workflow

Use agents for read-only discovery and research. Do not allow parallel agents to edit the target Spring Boot project unless the coordinator assigns disjoint files after classification.

## Discovery Agents

Config agent:
- Inspect Maven/Gradle files, Spring datasource properties, and datasource configuration classes.
- Output `config-report.json`.
- Do not edit.

JPA agent:
- Inspect entities, repositories, `@Query`, `@NamedQuery`, `@NamedNativeQuery`, and `EntityManager` usage.
- Output `jpa-report.json`.
- Do not edit.

MyBatis agent:
- Inspect mapper interfaces and XML mapper files.
- Extract SQL ids, SQL text, and referenced tables.
- Output `mybatis-report.json`.
- Do not edit.

Service/transaction agent:
- Inspect services for mixed repository/mapper usage and transaction annotations.
- Output `transaction-risk-report.json`.
- Do not edit.

Dialect research agent:
- Verify Oracle/MariaDB SQL differences against primary vendor docs and target database versions.
- Update rule recommendations only after recording source URLs and version notes.
- Do not edit project code.

## Coordinator Rule

The coordinator merges reports, asks the user to confirm the migration registry, and performs edits sequentially. Any unresolved table, dynamic SQL statement, cross-database query, or transaction risk is written to `oracle-to-mmdb-report/blocked.md`.
