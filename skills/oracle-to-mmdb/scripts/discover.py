import argparse
import re
from pathlib import Path

from report_io import ensure_report_dir, write_json, write_markdown


TEXT_EXTENSIONS = {".java", ".xml", ".yml", ".yaml", ".properties", ".gradle"}
ORACLE_PATTERNS = [
    "ROWNUM",
    "NVL(",
    "DECODE(",
    "SYSDATE",
    "TO_DATE",
    "CONNECT BY",
    "FROM DUAL",
    "OracleDriver",
    "Oracle12cDialect",
    "ojdbc",
    "VARCHAR2",
    "NUMBER(",
    "CLOB",
    "BLOB",
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
        entities.append(
            {
                "file": _relative(path, root),
                "entity": class_match.group(1) if class_match else path.stem,
                "table": table_match.group(1) if table_match else path.stem,
            }
        )
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
