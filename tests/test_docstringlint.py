"""Tests for docstringlint."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from docstringlint import scan, format_json, format_markdown, main


def _write_tmp(content: str, suffix: str = ".py") -> Path:
    fd, path = tempfile.mkstemp(suffix=suffix, prefix="docstringlint-test-")
    Path(path).write_text(content, encoding="utf-8")
    return Path(path)


def test_clean_file_has_no_issues() -> None:
    source = '"""Module docstring."""\n\nclass Foo:\n    """Class docstring."""\n\n    def method(self):\n        """Method docstring."""\n        pass\n'
    path = _write_tmp(source)
    report = scan(str(path))
    assert report.is_empty()
    path.unlink()


def test_missing_docstrings_detected() -> None:
    source = "\nclass Foo:\n    def method(self):\n        pass\n"
    path = _write_tmp(source)
    report = scan(str(path))
    assert not report.is_empty()
    codes = [issue.code for issue in report.issues]
    assert "DOC001" in codes
    assert "DOC002" in codes
    assert "DOC003" in codes
    path.unlink()


def test_empty_docstring_detected() -> None:
    source = '"""Module docstring."""\n\nclass Foo:\n    """"""\n\n    def method(self):\n        pass\n'
    path = _write_tmp(source)
    report = scan(str(path))
    assert not report.is_empty()
    codes = [issue.code for issue in report.issues]
    assert "DOC003" in codes
    assert "DOC004" in codes
    path.unlink()


def test_directory_scan_accumulates_issues() -> None:
    with tempfile.TemporaryDirectory(prefix="docstringlint-dir-") as td:
        root = Path(td)
        clean = root / "clean.py"
        clean.write_text('"""Clean module."""\n', encoding="utf-8")
        dirty = root / "dirty.py"
        dirty.write_text("\ndef foo():\n    pass\n", encoding="utf-8")

        report = scan(td)
        assert not report.is_empty()
        paths = {issue.path for issue in report.issues}
        assert str(dirty) in paths
        assert str(clean) not in paths


def test_markdown_format_contains_table_header() -> None:
    source = "\ndef foo():\n    pass\n"
    path = _write_tmp(source)
    report = scan(str(path))
    text = format_markdown(report)
    assert "| File |" in text
    assert "DOC001" in text
    path.unlink()


def test_json_format_is_valid_json() -> None:
    import json

    source = "\ndef foo():\n    pass\n"
    path = _write_tmp(source)
    report = scan(str(path))
    parsed = json.loads(format_json(report))
    assert isinstance(parsed, list)
    assert parsed[0]["code"] == "DOC001"
    path.unlink()


def test_main_check_exit_code() -> None:
    source = "\ndef foo():\n    pass\n"
    path = _write_tmp(source)
    rc = main(["--check", str(path)])
    assert rc == 1
    path.unlink()


def test_main_clean_exit_code() -> None:
    source = '"""Clean."""\n\ndef foo():\n    """Does foo."""\n    pass\n'
    path = _write_tmp(source)
    rc = main(["--check", str(path)])
    assert rc == 0
    path.unlink()
