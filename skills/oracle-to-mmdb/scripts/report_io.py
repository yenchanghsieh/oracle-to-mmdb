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
