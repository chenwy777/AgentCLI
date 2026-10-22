from __future__ import annotations

import py_compile
from pathlib import Path


def diagnose_file(path: str | Path) -> list[str]:
    file_path = Path(path)
    if file_path.suffix != ".py":
        return []
    try:
        py_compile.compile(str(file_path), doraise=True)
    except py_compile.PyCompileError as exc:
        return [str(exc)]
    return []
