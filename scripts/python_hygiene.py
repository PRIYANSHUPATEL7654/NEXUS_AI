"""Dependency-free Python source hygiene checks for CI and local release gates."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


def python_files(arguments: list[str]) -> list[Path]:
    files: list[Path] = []
    for argument in arguments:
        path = Path(argument)
        if path.is_dir():
            files.extend(path.rglob("*.py"))
        elif path.suffix == ".py":
            files.append(path)
        else:
            raise ValueError(f"Not a Python file or directory: {argument}")
    return sorted(set(files))


def check_file(path: Path) -> list[str]:
    problems: list[str] = []
    source = path.read_text(encoding="utf-8")

    try:
        ast.parse(source, filename=str(path))
    except SyntaxError as error:
        problems.append(f"{path}:{error.lineno}: {error.msg}")

    for number, line in enumerate(source.splitlines(), start=1):
        if line != line.rstrip():
            problems.append(f"{path}:{number}: trailing whitespace")
        indentation = line[: len(line) - len(line.lstrip())]
        if "\t" in indentation:
            problems.append(f"{path}:{number}: tab used for indentation")
        if line.startswith(("<<<<<<<", "=======", ">>>>>>>")):
            problems.append(f"{path}:{number}: unresolved merge marker")

    return problems


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python python_hygiene.py PATH [PATH ...]", file=sys.stderr)
        return 2

    try:
        files = python_files(sys.argv[1:])
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    problems = [problem for path in files for problem in check_file(path)]
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1

    print(f"Python hygiene passed for {len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
