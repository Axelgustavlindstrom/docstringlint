# docstringlint

Source: https://github.com/Axelgustavlindstrom/docstringlint

Audit Python files for missing or empty docstrings.

## About

`docstringlint` answers a simple maintenance question: *“Which Python objects are missing docstrings?”* It statically scans a source tree and reports missing or empty docstrings for modules, classes, and functions/methods. It is useful for enforcing documentation standards in local codebases and CI.

## Features

- Detect missing module, class, and function/method docstrings
- Detect empty docstrings
- Multiple output formats: plain text, Markdown table, and JSON
- `--check` mode for CI and pre-commit hooks
- Scope output to specific rule codes with `--rule`
- Ignore specific path segments with `--ignore`
- Pure stdlib implementation with no non-stdlib runtime dependencies

## Installation

```bash
python -m pip install -e .
```

## Usage

```bash
# Scan a directory
docstringlint src/

# Scan a single file
docstringlint mymodule.py

# CI mode: exit 1 when issues are found
docstringlint src/ --check

# JSON output for scripting
docstringlint src/ --format json

# Limit to specific rules
docstringlint src/ --rule DOC002 --rule DOC003

# Ignore hidden directories
docstringlint src/ --ignore tests --ignore __pycache__
```

## Rules

| Code  | Description                          |
|-------|--------------------------------------|
| DOC001 | Missing module docstring             |
| DOC002 | Missing class docstring              |
| DOC003 | Missing function/method docstring    |
| DOC004 | Empty docstring                      |

## Exit codes

- `0` — no issues found, or `--check` not requested
- `1` — issues found in `--check` mode
- `2` — invalid input path or runtime error

## Project structure

```
docstringlint/
  docstringlint.py
  pyproject.toml
  README.md
  .gitignore
  tests/
    test_docstringlint.py
```

## Tags

python, docstring, lint, static-analysis, cli, developer-tools
