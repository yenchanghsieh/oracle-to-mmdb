# Oracle to MariaDB Migrator

Conservative agent skill plugin for refactoring Spring Boot persistence code after an Oracle-to-MariaDB migration.

The plugin provides the `oracle-to-mmdb` skill, which coordinates discovery, SQL classification, gated edits, and testing handoff for projects that use MyBatis, JPA, Spring Data, or JdbcTemplate. It is designed for enterprise migrations where only confirmed MariaDB-owned tables should be edited and ambiguous Oracle or cross-database behavior must be reported instead of changed automatically.

The skill is model-neutral. It can run in Claude Code CLI even when your company routes Claude Code through a non-Claude model, because the workflow depends on local `SKILL.md` instructions and deterministic helper scripts rather than model-specific features.

## What It Does

- Finds Oracle-specific SQL, JDBC, Hibernate, MyBatis, and JPA patterns.
- Distinguishes full migrations from partial table-by-table migrations.
- Classifies SQL statements as `MARIADB`, `ORACLE`, `CROSS_DB`, or `UNRESOLVED`.
- Applies only conservative edits after explicit approval gates.
- Writes blocked decisions and a testing handoff under `oracle-to-mmdb-report/`.

## Repository Layout

```text
.claude-plugin/plugin.json
.codex-plugin/plugin.json
skills/oracle-to-mmdb/SKILL.md
skills/oracle-to-mmdb/references/
skills/oracle-to-mmdb/scripts/
skills/oracle-to-mmdb/scripts/tests/
docs/superpowers/plans/
```

Key files:

- `.claude-plugin/plugin.json` - Claude Code plugin manifest.
- `.codex-plugin/plugin.json` - Codex plugin manifest.
- `skills/oracle-to-mmdb/SKILL.md` - main skill workflow and hard gates.
- `skills/oracle-to-mmdb/references/sql-dialect-map.md` - Oracle-to-MariaDB SQL conversion guidance.
- `skills/oracle-to-mmdb/references/config-changes.md` - datasource and Hibernate migration patterns.
- `skills/oracle-to-mmdb/references/mybatis-patterns.md` - MyBatis XML and mapper refactoring guidance.
- `skills/oracle-to-mmdb/references/jpa-patterns.md` - JPA entity, repository, and native query guidance.
- `skills/oracle-to-mmdb/scripts/discover.py` - discovery report generator.
- `skills/oracle-to-mmdb/scripts/classify_sql.py` - SQL table extraction and migration classification helper.

## Claude Code CLI

Claude Code discovers plugin skills from:

```text
<plugin-root>/skills/<skill-name>/SKILL.md
```

This repository already follows that layout:

```text
skills/oracle-to-mmdb/SKILL.md
```

After installing or enabling the plugin in Claude Code, invoke the skill explicitly with:

```text
/oracle-to-mmdb
```

or ask for an Oracle-to-MariaDB Spring Boot migration and let Claude Code load the skill from its description.

If your company uses Claude Code CLI with a non-Claude model, no model-specific configuration is required in this plugin. Avoid adding Claude model names, provider-specific prompts, or plugin agents with fixed model settings unless your internal platform requires them.

## Skill Workflow

The skill is gate-heavy by design:

1. Create `oracle-to-mmdb-report/migration_state.json` in the target project.
2. Run discovery against the target Spring Boot project.
3. Ask whether the migration is full or partial.
4. For partial migrations, confirm the migrated table registry.
5. Classify every SQL statement before any edit.
6. Apply one approved conservative edit batch at a time.
7. Write `blocked.md` and `test_checklist.md` for developer follow-up.

Hard confirmation words:

- `proceed` after discovery file listing.
- `confirmed` after migration registry review.
- `apply` before each edit batch.

## Helper Scripts

Run discovery from the repository root:

```bash
python3 skills/oracle-to-mmdb/scripts/discover.py /path/to/spring-boot-project
```

The script writes:

```text
/path/to/spring-boot-project/oracle-to-mmdb-report/discovery.json
/path/to/spring-boot-project/oracle-to-mmdb-report/discovery.md
```

Use `classify_sql.py` as a library from the skill workflow to extract table names and classify statements against confirmed migrated and Oracle-only table sets.

## Testing

Run the Python helper test suite from the repository root:

```bash
PYTHONPATH=skills/oracle-to-mmdb/scripts pytest skills/oracle-to-mmdb/scripts/tests
```

The tests cover report IO, discovery, SQL classification, and dialect rule metadata.

## Notes

- The skill does not run target project tests automatically.
- The target project report directory is ignored via `.gitignore`.
- Cross-database queries, dynamic table names, unresolved tables, and unsafe dialect rewrites are reported for manual review.
- The plugin intentionally avoids model-specific agent definitions and Claude-only tool restrictions.
