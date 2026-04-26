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
