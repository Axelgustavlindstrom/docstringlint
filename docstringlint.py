"""docstringlint: audit Python files for missing or empty docstrings."""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, TextIO


@dataclass
class Issue:
    path: str
    line: int
    code: str
    message: str
    node: str


@dataclass
class Report:
    issues: List[Issue] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.issues


_RULES = {
    "DOC001": "Missing module docstring",
    "DOC002": "Missing class docstring",
    "DOC003": "Missing function/method docstring",
    "DOC004": "Empty docstring",
}


def _extract_docstring(node: ast.AST) -> Optional[str]:
    if isinstance(getattr(node, "body", [None])[0], ast.Expr) and isinstance(
        getattr(node, "body", [None])[0].value, ast.Constant
    ):
        return getattr(node, "body", [None])[0].value.value
    return None


def _lint_file(path: Path) -> List[Issue]:
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    issues: List[Issue] = []
    module_doc = ast.get_docstring(tree, clean=False)
    if not module_doc:
        issues.append(
            Issue(
                path=str(path),
                line=1,
                code="DOC001",
                message=_RULES["DOC001"],
                node=path.name,
            )
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            doc = ast.get_docstring(node, clean=False)
            if doc is None or doc.strip() == "":
                issues.append(
                    Issue(
                        path=str(path),
                        line=node.lineno,
                        code="DOC002",
                        message=_RULES["DOC002"],
                        node=node.name,
                    )
                )
                if doc is not None and doc.strip() == "":
                    issues.append(
                        Issue(
                            path=str(path),
                            line=node.lineno,
                            code="DOC004",
                            message=_RULES["DOC004"],
                            node=node.name,
                        )
                    )
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    doc = ast.get_docstring(child, clean=False)
                    if doc is None or doc.strip() == "":
                        issues.append(
                            Issue(
                                path=str(path),
                                line=child.lineno,
                                code="DOC003",
                                message=_RULES["DOC003"],
                                node=f"{node.name}.{child.name}",
                            )
                        )
                        if doc is not None and doc.strip() == "":
                            issues.append(
                                Issue(
                                    path=str(path),
                                    line=child.lineno,
                                    code="DOC004",
                                    message=_RULES["DOC004"],
                                    node=f"{node.name}.{child.name}",
                                )
                            )
        elif isinstance(node, ast.FunctionDef):
            doc = ast.get_docstring(node, clean=False)
            if doc is None or doc.strip() == "":
                issues.append(
                    Issue(
                        path=str(path),
                        line=node.lineno,
                        code="DOC003",
                        message=_RULES["DOC003"],
                        node=node.name,
                    )
                )
                if doc is not None and doc.strip() == "":
                    issues.append(
                        Issue(
                            path=str(path),
                            line=node.lineno,
                            code="DOC004",
                            message=_RULES["DOC004"],
                            node=node.name,
                        )
                    )

    return issues


def _default_ignore(path: Path) -> bool:
    return (
        any(part.startswith(".") for part in path.parts) or path.name == "__pycache__"
    )


def scan(
    target: str,
    *,
    rules: Optional[List[str]] = None,
    ignore: Optional[List[str]] = None,
) -> Report:
    root = Path(target).resolve()
    if not root.exists():
        raise ValueError(f"Path does not exist: {target}")

    ignore_names = set(ignore or [])
    ruleset = set(rules) if rules else set(_RULES.keys())

    report = Report()
    files = []
    if root.is_file() and root.suffix == ".py":
        files.append(root)
    elif root.is_dir():
        for path in sorted(root.rglob("*.py")):
            if any(part in ignore_names for part in path.parts):
                continue
            files.append(path)

    for path in files:
        for issue in _lint_file(path):
            if issue.code not in ruleset:
                continue
            report.issues.append(issue)

    return report


def format_plain(report: Report) -> str:
    if report.is_empty():
        return "No docstring issues found.\n"
    return (
        "\n".join(
            f"{issue.path}:{issue.line}: {issue.code} {issue.message} ({issue.node})"
            for issue in report.issues
        )
        + "\n"
    )


def format_markdown(report: Report) -> str:
    if report.is_empty():
        return "No docstring issues found.\n"
    lines = ["| File | Line | Code | Node | Issue |", "| --- | --- | --- | --- | --- |"]
    for issue in report.issues:
        lines.append(
            f"| {issue.path} | {issue.line} | {issue.code} | {issue.node} | {issue.message} |"
        )
    return "\n".join(lines) + "\n"


def format_json(report: Report) -> str:
    import json

    payload = [
        {
            "path": issue.path,
            "line": issue.line,
            "code": issue.code,
            "node": issue.node,
            "message": issue.message,
        }
        for issue in report.issues
    ]
    return json.dumps(payload, indent=2) + "\n"


def main(argv: Optional[List[str]] = None, stdout: Optional[TextIO] = None) -> int:
    import argparse

    if stdout is None:
        stdout = sys.stdout

    parser = argparse.ArgumentParser(
        prog="docstringlint", description="Lint Python docstrings"
    )
    parser.add_argument("target", help="Python file or directory to scan")
    parser.add_argument(
        "--format",
        choices=("plain", "markdown", "json"),
        default="plain",
        help="Output format",
    )
    parser.add_argument("--rule", action="append", help="Limit to specific rule code")
    parser.add_argument(
        "--ignore", action="append", help="Ignore paths containing this segment"
    )
    parser.add_argument(
        "--check", action="store_true", help="Exit with 1 when issues are found"
    )
    args = parser.parse_args(argv)

    try:
        report = scan(args.target, rules=args.rule, ignore=args.ignore)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.format == "markdown":
        sys.stdout.write(format_markdown(report))
    elif args.format == "json":
        sys.stdout.write(format_json(report))
    else:
        sys.stdout.write(format_plain(report))

    if args.check and not report.is_empty():
        return 1
    return 0
