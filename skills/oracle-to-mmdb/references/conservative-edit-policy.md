# Conservative Edit Policy

The skill may edit only code that satisfies all of these conditions:

1. The target file is listed in discovery output.
2. The statement or entity maps only to confirmed migrated MariaDB tables.
3. The required conversion rule is marked `safe_auto_convert`.
4. The planned diff is shown before the edit batch begins.
5. The user has approved the batch.

The skill must not edit:

- Queries with unresolved table names.
- Queries joining migrated and Oracle-only tables.
- Dynamic SQL where table names are assembled from parameters.
- `CONNECT BY`, `MERGE`, Oracle outer join `(+)`, or complex `DECODE` without review.
- Service methods that write to both datasources without explicit user approval.

Blocked items are written to `oracle-to-mmdb-report/blocked.md` with file path, line number when available, reason, and suggested next decision.
