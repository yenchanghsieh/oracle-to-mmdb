# Conservative Oracle to MariaDB Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the existing Oracle-to-MariaDB migration skill into a conservative Codex plugin that directly edits enterprise Spring Boot projects only after report-backed classification and user approval.

**Architecture:** Keep one main skill as the coordinator and add deterministic Python scanner scripts for discovery, SQL inventory, table classification, and report merging. Use read-only multi-agent discovery as an optional workflow, then perform edits sequentially through the coordinator skill with strict gates for ambiguous or risky changes.

**Tech Stack:** Codex plugin/skill layout, Python 3 standard library, pytest for script tests, Spring Boot/MyBatis/JPA migration references.

---

## File Structure

- Create: `.codex-plugin/plugin.json`
- Move: `SKILL.md` -> `skills/oracle-to-mmdb/SKILL.md`
- Move: `references/*.md` -> `skills/oracle-to-mmdb/references/*.md`
- Create: `skills/oracle-to-mmdb/references/multi-agent-workflow.md`
- Create: `skills/oracle-to-mmdb/references/conservative-edit-policy.md`
- Create: `skills/oracle-to-mmdb/scripts/discover.py`
- Create: `skills/oracle-to-mmdb/scripts/classify_sql.py`
- Create: `skills/oracle-to-mmdb/scripts/dialect_rules.py`
- Create: `skills/oracle-to-mmdb/scripts/report_io.py`
- Create tests under `skills/oracle-to-mmdb/scripts/tests/`
- Modify: `.gitignore`

## Task 1: Convert Repository to Plugin Layout

**Files:**
- Create: `.codex-plugin/plugin.json`
- Move: `SKILL.md` -> `skills/oracle-to-mmdb/SKILL.md`
- Move: `references/config-changes.md` -> `skills/oracle-to-mmdb/references/config-changes.md`
- Move: `references/jpa-patterns.md` -> `skills/oracle-to-mmdb/references/jpa-patterns.md`
- Move: `references/mybatis-patterns.md` -> `skills/oracle-to-mmdb/references/mybatis-patterns.md`
- Move: `references/sql-dialect-map.md` -> `skills/oracle-to-mmdb/references/sql-dialect-map.md`
- Modify: `.gitignore`

- [ ] **Step 1: Create plugin directories**

Run:

```bash
mkdir -p .codex-plugin skills/oracle-to-mmdb/references
```

Expected: directories exist.

- [ ] **Step 2: Move the existing skill and references**

Run:

```bash
git mv SKILL.md skills/oracle-to-mmdb/SKILL.md
git mv references/config-changes.md skills/oracle-to-mmdb/references/config-changes.md
git mv references/jpa-patterns.md skills/oracle-to-mmdb/references/jpa-patterns.md
git mv references/mybatis-patterns.md skills/oracle-to-mmdb/references/mybatis-patterns.md
git mv references/sql-dialect-map.md skills/oracle-to-mmdb/references/sql-dialect-map.md
rmdir references
```

Expected: all existing skill content is preserved under `skills/oracle-to-mmdb/`.

- [ ] **Step 3: Add plugin manifest**

Create `.codex-plugin/plugin.json`:

```json
{
  "schema_version": "v1",
  "name": "oracle-to-mmdb",
  "version": "0.1.0",
  "description": "Conservative Oracle-to-MariaDB migration assistant for Spring Boot projects using MyBatis and JPA.",
  "interface": {
    "display_name": "Oracle to MariaDB Migrator",
    "short_description": "Safely refactor Spring Boot persistence code from Oracle to MariaDB.",
    "default_prompt": "Use the oracle-to-mmdb skill to conservatively migrate a Spring Boot project from Oracle to MariaDB."
  }
}
```

- [ ] **Step 4: Update `.gitignore`**

Append:

```gitignore
__pycache__/
.pytest_cache/
oracle-to-mmdb-report/
*.pyc
```

- [ ] **Step 5: Verify moved references are still discoverable**

Run:

```bash
rg "config-changes.md|sql-dialect-map.md|mybatis-patterns.md|jpa-patterns.md" skills/oracle-to-mmdb/SKILL.md
```

Expected: all four reference filenames are still mentioned.

- [ ] **Step 6: Commit layout conversion**

Run:

```bash
git add .codex-plugin .gitignore skills
git commit -m "chore: convert migration skill to plugin layout"
```

## Task 2: Add Conservative Workflow References

**Files:**
- Create: `skills/oracle-to-mmdb/references/multi-agent-workflow.md`
- Create: `skills/oracle-to-mmdb/references/conservative-edit-policy.md`
- Modify: `skills/oracle-to-mmdb/SKILL.md`

- [ ] **Step 1: Add multi-agent workflow reference**

Create `skills/oracle-to-mmdb/references/multi-agent-workflow.md`:

```markdown
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
```

- [ ] **Step 2: Add conservative edit policy**

Create `skills/oracle-to-mmdb/references/conservative-edit-policy.md`:

```markdown
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
```

- [ ] **Step 3: Reference both files from the skill**

In `skills/oracle-to-mmdb/SKILL.md`, add these rows to the Reference Files table:

```markdown
| `multi-agent-workflow.md` | Read-only agent scopes and report contracts | Discovery |
| `conservative-edit-policy.md` | Enterprise edit gates and blocked-change rules | Before edits |
```

- [ ] **Step 4: Add direct-editing principle near Execution Rules**

Add this paragraph under `## Execution Rules`:

```markdown
Enterprise conservative mode is the default. Use helper scripts and optional read-only agents for discovery, but perform project edits sequentially from the coordinator. Never edit a SQL statement unless its table classification and conversion rule are both recorded in the current report.
```

- [ ] **Step 5: Commit workflow references**

Run:

```bash
git add skills/oracle-to-mmdb/SKILL.md skills/oracle-to-mmdb/references
git commit -m "docs: add conservative multi-agent workflow"
```

## Task 3: Implement Shared Report IO

**Files:**
- Create: `skills/oracle-to-mmdb/scripts/report_io.py`
- Create: `skills/oracle-to-mmdb/scripts/tests/test_report_io.py`

- [ ] **Step 1: Create scripts and tests directories**

Run:

```bash
mkdir -p skills/oracle-to-mmdb/scripts/tests
```

- [ ] **Step 2: Write tests for report IO**

Create `skills/oracle-to-mmdb/scripts/tests/test_report_io.py`:

```python
from pathlib import Path

from report_io import ensure_report_dir, write_json, write_markdown


def test_write_json_creates_parent_and_stable_output(tmp_path):
    path = tmp_path / "oracle-to-mmdb-report" / "discovery.json"
    write_json(path, {"b": 2, "a": 1})
    assert path.read_text(encoding="utf-8") == '{\n  "a": 1,\n  "b": 2\n}\n'


def test_write_markdown_creates_parent(tmp_path):
    path = tmp_path / "oracle-to-mmdb-report" / "discovery.md"
    write_markdown(path, "# Discovery\n")
    assert path.read_text(encoding="utf-8") == "# Discovery\n"


def test_ensure_report_dir_returns_default_path(tmp_path):
    root = Path(tmp_path)
    assert ensure_report_dir(root) == root / "oracle-to-mmdb-report"
```

- [ ] **Step 3: Run test to verify it fails**

Run:

```bash
PYTHONPATH=skills/oracle-to-mmdb/scripts pytest skills/oracle-to-mmdb/scripts/tests/test_report_io.py -q
```

Expected: FAIL because `report_io` does not exist.

- [ ] **Step 4: Implement report IO**

Create `skills/oracle-to-mmdb/scripts/report_io.py`:

```python
import json
from pathlib import Path
from typing import Any


def ensure_report_dir(project_root: Path) -> Path:
    report_dir = project_root / "oracle-to-mmdb-report"
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
```

- [ ] **Step 5: Run test to verify it passes**

Run:

```bash
PYTHONPATH=skills/oracle-to-mmdb/scripts pytest skills/oracle-to-mmdb/scripts/tests/test_report_io.py -q
```

Expected: `3 passed`.

- [ ] **Step 6: Commit report IO**

Run:

```bash
git add skills/oracle-to-mmdb/scripts
git commit -m "test: add report IO helpers"
```

## Task 4: Implement Discovery Scanner

**Files:**
- Create: `skills/oracle-to-mmdb/scripts/discover.py`
- Create fixture files under `skills/oracle-to-mmdb/scripts/tests/fixtures/spring-app/`
- Create: `skills/oracle-to-mmdb/scripts/tests/test_discover.py`

- [ ] **Step 1: Create minimal Spring Boot fixture**

Run:

```bash
mkdir -p skills/oracle-to-mmdb/scripts/tests/fixtures/spring-app/src/main/java/com/example/entity
mkdir -p skills/oracle-to-mmdb/scripts/tests/fixtures/spring-app/src/main/java/com/example/repository
mkdir -p skills/oracle-to-mmdb/scripts/tests/fixtures/spring-app/src/main/resources/mapper
```

Create fixture files:

```text
pom.xml: contains ojdbc8 dependency.
application.yml: contains Oracle JDBC URL, OracleDriver, and Oracle12cDialect.
OrderEntity.java: contains @Entity, @Table(name = "ORDERS"), @SequenceGenerator, and VARCHAR2 columnDefinition.
OrderRepository.java: contains native @Query with ROWNUM.
OrderMapper.xml: contains mapper SQL with NVL and ROWNUM.
```

- [ ] **Step 2: Write discovery tests**

Create `skills/oracle-to-mmdb/scripts/tests/test_discover.py`:

```python
from pathlib import Path

from discover import discover_project


FIXTURE = Path(__file__).parent / "fixtures" / "spring-app"


def test_discover_detects_oracle_config_and_persistence_layers():
    report = discover_project(FIXTURE)
    assert report["persistence_layers"]["jpa"] is True
    assert report["persistence_layers"]["mybatis"] is True
    assert report["persistence_layers"]["jdbc_template"] is False
    assert "pom.xml" in report["oracle_candidates"]
    assert "src/main/resources/application.yml" in report["oracle_candidates"]


def test_discover_finds_entities_repositories_and_mappers():
    report = discover_project(FIXTURE)
    assert report["entities"] == [
        {
            "file": "src/main/java/com/example/entity/OrderEntity.java",
            "entity": "OrderEntity",
            "table": "ORDERS",
        }
    ]
    assert "src/main/java/com/example/repository/OrderRepository.java" in report["repositories"]
    assert "src/main/resources/mapper/OrderMapper.xml" in report["mybatis_mappers"]
```

- [ ] **Step 3: Run discovery tests to verify they fail**

Run:

```bash
PYTHONPATH=skills/oracle-to-mmdb/scripts pytest skills/oracle-to-mmdb/scripts/tests/test_discover.py -q
```

Expected: FAIL because `discover.py` does not exist.

- [ ] **Step 4: Implement discovery scanner**

Create `skills/oracle-to-mmdb/scripts/discover.py` with:

```python
import argparse
import re
from pathlib import Path

from report_io import ensure_report_dir, write_json, write_markdown


TEXT_EXTENSIONS = {".java", ".xml", ".yml", ".yaml", ".properties", ".gradle"}
ORACLE_PATTERNS = [
    "ROWNUM", "NVL(", "DECODE(", "SYSDATE", "TO_DATE", "CONNECT BY",
    "FROM DUAL", "OracleDriver", "Oracle12cDialect", "ojdbc", "VARCHAR2",
    "NUMBER(", "CLOB", "BLOB",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _iter_text_files(root: Path):
    for path in root.rglob("*"):
        if ".git" in path.parts or "target" in path.parts or path.is_dir():
            continue
        if path.name in {"pom.xml", "build.gradle"} or path.suffix in TEXT_EXTENSIONS:
            yield path


def _extract_entities(root: Path) -> list[dict[str, str]]:
    entities = []
    for path in root.rglob("*.java"):
        text = _read(path)
        if "@Entity" not in text:
            continue
        class_match = re.search(r"\bclass\s+(\w+)", text)
        table_match = re.search(r"@Table\s*\([^)]*name\s*=\s*\"([^\"]+)\"", text, re.DOTALL)
        entities.append({
            "file": _relative(path, root),
            "entity": class_match.group(1) if class_match else path.stem,
            "table": table_match.group(1) if table_match else path.stem,
        })
    return sorted(entities, key=lambda item: item["file"])


def discover_project(root: Path) -> dict:
    root = root.resolve()
    files = list(_iter_text_files(root))
    contents = {path: _read(path) for path in files}
    oracle_candidates = [
        _relative(path, root)
        for path, text in contents.items()
        if any(pattern in text for pattern in ORACLE_PATTERNS)
    ]
    repositories = [
        _relative(path, root)
        for path, text in contents.items()
        if path.suffix == ".java" and ("JpaRepository" in text or "Repository<" in text or "@Query" in text)
    ]
    mybatis_mappers = [
        _relative(path, root)
        for path, text in contents.items()
        if (path.suffix == ".xml" and "<mapper" in text) or (path.suffix == ".java" and "@Mapper" in text)
    ]
    all_text = "\n".join(contents.values())
    return {
        "project_root": root.as_posix(),
        "oracle_candidates": sorted(oracle_candidates),
        "persistence_layers": {
            "mybatis": bool(mybatis_mappers),
            "jpa": "@Entity" in all_text or bool(repositories),
            "spring_data": bool(repositories),
            "jdbc_template": "JdbcTemplate" in all_text or "NamedParameterJdbcTemplate" in all_text,
        },
        "entities": _extract_entities(root),
        "repositories": sorted(repositories),
        "mybatis_mappers": sorted(mybatis_mappers),
    }


def _markdown(report: dict) -> str:
    lines = ["# Oracle to MariaDB Discovery", "", "## Persistence Layers"]
    for key, value in report["persistence_layers"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Oracle Candidates"])
    for path in report["oracle_candidates"]:
        lines.append(f"- {path}")
    lines.extend(["", "## Entities"])
    for entity in report["entities"]:
        lines.append(f"- {entity['entity']} -> {entity['table']} ({entity['file']})")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    args = parser.parse_args()
    report = discover_project(args.project_root)
    report_dir = ensure_report_dir(args.project_root)
    write_json(report_dir / "discovery.json", report)
    write_markdown(report_dir / "discovery.md", _markdown(report))


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run discovery tests to verify they pass**

Run:

```bash
PYTHONPATH=skills/oracle-to-mmdb/scripts pytest skills/oracle-to-mmdb/scripts/tests/test_discover.py -q
```

Expected: `2 passed`.

- [ ] **Step 6: Commit discovery scanner**

Run:

```bash
git add skills/oracle-to-mmdb/scripts
git commit -m "test: add Spring Boot discovery scanner"
```

## Task 5: Implement SQL Classifier

**Files:**
- Create: `skills/oracle-to-mmdb/scripts/classify_sql.py`
- Create: `skills/oracle-to-mmdb/scripts/tests/test_classify_sql.py`

- [ ] **Step 1: Write classifier tests**

Create `skills/oracle-to-mmdb/scripts/tests/test_classify_sql.py`:

```python
from classify_sql import classify_statement, extract_table_names


def test_extract_table_names_from_common_dml():
    sql = "SELECT * FROM ORDERS o JOIN PAYMENT p ON p.ORDER_ID = o.ID WHERE ROWNUM <= 10"
    assert extract_table_names(sql) == ["ORDERS", "PAYMENT"]


def test_classifies_mariadb_when_all_tables_migrated():
    result = classify_statement("SELECT * FROM ORDERS WHERE ROWNUM <= 10", {"ORDERS"}, {"INVOICE"})
    assert result["classification"] == "MARIADB"
    assert result["tables"] == ["ORDERS"]


def test_classifies_oracle_when_all_tables_are_oracle_only():
    result = classify_statement("SELECT * FROM INVOICE", {"ORDERS"}, {"INVOICE"})
    assert result["classification"] == "ORACLE"


def test_classifies_cross_db_for_mixed_tables():
    result = classify_statement("SELECT * FROM ORDERS o JOIN INVOICE i ON i.ORDER_ID = o.ID", {"ORDERS"}, {"INVOICE"})
    assert result["classification"] == "CROSS_DB"


def test_unresolved_table_blocks_editing():
    result = classify_statement("SELECT * FROM UNKNOWN_TABLE", {"ORDERS"}, {"INVOICE"})
    assert result["classification"] == "UNRESOLVED"
    assert result["editable"] is False
```

- [ ] **Step 2: Implement classifier**

Create `skills/oracle-to-mmdb/scripts/classify_sql.py`:

```python
import re


TABLE_PATTERN = re.compile(r"\b(?:FROM|JOIN|INTO|UPDATE)\s+([A-Za-z_][\w$#.]*)", re.IGNORECASE)


def _normalize_table(name: str) -> str:
    return name.split(".")[-1].strip('"').upper()


def extract_table_names(sql: str) -> list[str]:
    tables = {_normalize_table(match.group(1)) for match in TABLE_PATTERN.finditer(sql)}
    return sorted(tables)


def classify_statement(sql: str, migrated_tables: set[str], oracle_tables: set[str]) -> dict:
    migrated = {table.upper() for table in migrated_tables}
    oracle = {table.upper() for table in oracle_tables}
    tables = extract_table_names(sql)
    table_set = set(tables)
    unresolved = sorted(table_set - migrated - oracle)
    if not tables or unresolved:
        classification = "UNRESOLVED"
    elif table_set <= migrated:
        classification = "MARIADB"
    elif table_set <= oracle:
        classification = "ORACLE"
    else:
        classification = "CROSS_DB"
    return {
        "classification": classification,
        "tables": tables,
        "unresolved_tables": unresolved,
        "editable": classification == "MARIADB",
    }
```

- [ ] **Step 3: Run classifier tests**

Run:

```bash
PYTHONPATH=skills/oracle-to-mmdb/scripts pytest skills/oracle-to-mmdb/scripts/tests/test_classify_sql.py -q
```

Expected: `5 passed`.

- [ ] **Step 4: Commit classifier**

Run:

```bash
git add skills/oracle-to-mmdb/scripts
git commit -m "test: add conservative SQL classifier"
```

## Task 6: Add Version-Aware Dialect Rule Metadata

**Files:**
- Create: `skills/oracle-to-mmdb/scripts/dialect_rules.py`
- Create: `skills/oracle-to-mmdb/scripts/tests/test_dialect_rules.py`
- Modify: `skills/oracle-to-mmdb/references/sql-dialect-map.md`

- [ ] **Step 1: Write dialect rule tests**

Create `skills/oracle-to-mmdb/scripts/tests/test_dialect_rules.py`:

```python
from dialect_rules import RULES, rules_by_safety


def test_safe_rules_include_simple_null_and_date_conversions():
    safe = rules_by_safety("safe_auto_convert")
    assert "NVL_SIMPLE" in safe
    assert "SYSDATE" in safe


def test_complex_rules_are_not_safe_auto_convert():
    assert RULES["CONNECT_BY"]["safety"] == "do_not_auto_convert"
    assert RULES["MERGE_INTO"]["safety"] == "needs_review"
```

- [ ] **Step 2: Implement dialect metadata**

Create `skills/oracle-to-mmdb/scripts/dialect_rules.py`:

```python
RULES = {
    "NVL_SIMPLE": {
        "oracle": "NVL(x, y)",
        "mariadb": "IFNULL(x, y)",
        "safety": "safe_auto_convert",
        "note": "Safe for simple two-argument expressions. Review nested calls manually.",
    },
    "SYSDATE": {
        "oracle": "SYSDATE",
        "mariadb": "NOW()",
        "safety": "safe_auto_convert",
        "note": "Use NOW(6) if fractional seconds are required.",
    },
    "ROWNUM_LIMIT": {
        "oracle": "ROWNUM <= n",
        "mariadb": "LIMIT n",
        "safety": "needs_review",
        "note": "Preserve ORDER BY semantics before converting pagination.",
    },
    "DECODE": {
        "oracle": "DECODE(expr, ...)",
        "mariadb": "CASE WHEN ... END",
        "safety": "needs_review",
        "note": "Oracle NULL and type coercion behavior must be checked.",
    },
    "MERGE_INTO": {
        "oracle": "MERGE INTO",
        "mariadb": "INSERT ... ON DUPLICATE KEY UPDATE",
        "safety": "needs_review",
        "note": "Requires key/index validation.",
    },
    "CONNECT_BY": {
        "oracle": "CONNECT BY",
        "mariadb": "WITH RECURSIVE",
        "safety": "do_not_auto_convert",
        "note": "Requires semantic rewrite and manual review.",
    },
}


def rules_by_safety(safety: str) -> dict[str, dict[str, str]]:
    return {name: rule for name, rule in RULES.items() if rule["safety"] == safety}
```

- [ ] **Step 3: Add safety labels to SQL dialect reference**

Add near the top of `skills/oracle-to-mmdb/references/sql-dialect-map.md`:

```markdown
## Conservative Automation Safety

| Safety | Meaning |
|--------|---------|
| `safe_auto_convert` | The coordinator may edit after table classification and batch approval. |
| `needs_review` | The coordinator must show the query and proposed rewrite before editing. |
| `version_dependent` | The dialect research agent must confirm target MariaDB support first. |
| `do_not_auto_convert` | Report as blocked unless the user explicitly asks for a manual rewrite. |
```

- [ ] **Step 4: Run dialect tests**

Run:

```bash
PYTHONPATH=skills/oracle-to-mmdb/scripts pytest skills/oracle-to-mmdb/scripts/tests/test_dialect_rules.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit dialect metadata**

Run:

```bash
git add skills/oracle-to-mmdb/scripts skills/oracle-to-mmdb/references/sql-dialect-map.md
git commit -m "test: add conservative dialect rule metadata"
```

## Task 7: Update Skill Workflow to Use Scripts and Agents

**Files:**
- Modify: `skills/oracle-to-mmdb/SKILL.md`

- [ ] **Step 1: Add script-first discovery command**

In `Phase 0A: Discovery`, add:

```bash
python3 skills/oracle-to-mmdb/scripts/discover.py <spring-boot-project-root>
```

State that manual `rg` checks are fallback validation, not the primary report source.

- [ ] **Step 2: Add multi-agent discovery option**

In `Phase 0A: Discovery`, add:

```markdown
For large enterprise projects, use read-only discovery agents before editing:

1. Config agent
2. JPA agent
3. MyBatis agent
4. Service/transaction agent
5. Dialect research agent when target versions are unknown

Load `multi-agent-workflow.md` before dispatching agents. Agents produce reports only; the coordinator performs all edits.
```

- [ ] **Step 3: Add classifier requirement to Phase 0B**

In `Phase 0B: Table Classification`, add:

```markdown
Use `classify_sql.py` logic for every SQL statement. A statement is editable only when classification is `MARIADB` and all applied conversion rules are `safe_auto_convert` or explicitly approved after review.
```

- [ ] **Step 4: Change file gates to batch gates plus per-file diff summaries**

Replace the hard requirement to wait for `"next"` after every file with:

```markdown
Enterprise default: ask for approval before each edit batch, then show a diff summary after every file. Stop immediately if an edit reveals unresolved table ownership, dynamic table names, or cross-database behavior not present in the approved batch.
```

- [ ] **Step 5: Run reference check**

Run:

```bash
rg "discover.py|classify_sql.py|multi-agent-workflow.md|conservative-edit-policy.md" skills/oracle-to-mmdb/SKILL.md
```

Expected: all four terms are present.

- [ ] **Step 6: Commit skill workflow update**

Run:

```bash
git add skills/oracle-to-mmdb/SKILL.md
git commit -m "docs: wire scripts into conservative migration workflow"
```

## Task 8: Run Full Local Verification

**Files:**
- No source edits unless verification exposes a defect.

- [ ] **Step 1: Run all Python tests**

Run:

```bash
PYTHONPATH=skills/oracle-to-mmdb/scripts pytest skills/oracle-to-mmdb/scripts/tests -q
```

Expected: all tests pass.

- [ ] **Step 2: Run discovery script against fixture**

Run:

```bash
python3 skills/oracle-to-mmdb/scripts/discover.py skills/oracle-to-mmdb/scripts/tests/fixtures/spring-app
```

Expected: creates `skills/oracle-to-mmdb/scripts/tests/fixtures/spring-app/oracle-to-mmdb-report/discovery.json` and `discovery.md`.

- [ ] **Step 3: Inspect generated discovery JSON**

Run:

```bash
python3 -m json.tool skills/oracle-to-mmdb/scripts/tests/fixtures/spring-app/oracle-to-mmdb-report/discovery.json
```

Expected: valid JSON containing Oracle candidates, JPA enabled, MyBatis enabled, and `OrderEntity -> ORDERS`.

- [ ] **Step 4: Remove generated fixture report**

Run:

```bash
rm -rf skills/oracle-to-mmdb/scripts/tests/fixtures/spring-app/oracle-to-mmdb-report
```

Expected: generated report is removed and no test fixture output remains tracked.

- [ ] **Step 5: Check git status**

Run:

```bash
git status --short
```

Expected: clean working tree.

## Task 9: Final Documentation and Handoff

**Files:**
- Modify: `skills/oracle-to-mmdb/SKILL.md`

- [ ] **Step 1: Add usage summary to skill**

Add after the skill title:

```markdown
## Usage Summary

1. Run discovery against the target Spring Boot project.
2. Confirm full or partial migration mode.
3. Confirm the migrated table registry.
4. Approve one conservative edit batch at a time.
5. Review `oracle-to-mmdb-report/blocked.md` for manual decisions.
6. Run compile/tests only after explicit approval.
```

- [ ] **Step 2: Verify no stale root references remain**

Run:

```bash
rg "references/" .
```

Expected: references point to `skills/oracle-to-mmdb/references/` or are relative within the skill.

- [ ] **Step 3: Commit final docs**

Run:

```bash
git add skills/oracle-to-mmdb
git commit -m "docs: add conservative migration usage summary"
```

- [ ] **Step 4: Report branch status**

Run:

```bash
git log --oneline --decorate -5
git status --short
```

Expected: recent commits are visible and working tree is clean.

## Self-Review

- Spec coverage: The plan covers plugin packaging, conservative direct-edit policy, read-only multi-agent discovery, scanner scripts, SQL classification, version-aware dialect rule metadata, and verification.
- Placeholder scan: No task uses TBD/TODO/fill-in language. The plan includes concrete files, commands, and code for each implementation step.
- Type consistency: Python module names and imported functions are consistent across tasks: `report_io`, `discover`, `classify_sql`, and `dialect_rules`.
- Scope check: The first implementation version intentionally stops at scanner/report infrastructure and workflow wiring. Actual project-file refactoring rules remain coordinator-driven in the skill, which is safer for enterprise migrations.
