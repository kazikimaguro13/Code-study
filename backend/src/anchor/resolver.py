"""Symbol anchor resolver — staleness-resistant citation resolution.

Citations store ``{file, symbol{kind,name}}`` rather than line numbers, so
they survive edits above the symbol. This module resolves a symbol to its
*current* line range + source snippet in the target repo.

MVP note: the quiz UI shows the snippet **bundled into quiz_bank.json** at
generation time, so the tool works without the target repo present. This
resolver powers the optional ``verify_bank.py`` freshness check (and a
future "open at current location" feature). Python is supported via ``ast``;
other languages fall back to a regex scan.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any


class ResolveError(Exception):
    pass


def resolve_python(source: str, name: str) -> tuple[int, int, str]:
    """Return (start_line, end_line, snippet) for a top-level or nested
    function/class named ``name`` (last dotted segment honored)."""
    target = name.rsplit(".", 1)[-1]
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ) and node.name == target:
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            lines = source.splitlines()[start - 1 : end]
            return start, end, "\n".join(lines)
    raise ResolveError(f"symbol not found: {name}")


def resolve_regex(source: str, name: str) -> tuple[int, int, str]:
    """Best-effort resolution for non-Python files (TS/TSX/JS)."""
    target = re.escape(name.rsplit(".", 1)[-1])
    pat = re.compile(
        rf"(export\s+)?(async\s+)?(function\s+{target}\b"
        rf"|const\s+{target}\b|class\s+{target}\b|{target}\s*[:=]\s*\()",
    )
    for i, line in enumerate(source.splitlines(), start=1):
        if pat.search(line):
            return i, i, line.strip()
    raise ResolveError(f"symbol not found (regex): {name}")


def resolve(repo_root: str | Path, file_rel: str, symbol_name: str) -> dict[str, Any]:
    path = Path(repo_root) / file_rel
    if not path.exists():
        raise ResolveError(f"file not found: {file_rel}")
    source = path.read_text(encoding="utf-8")
    if file_rel.endswith(".py"):
        start, end, snippet = resolve_python(source, symbol_name)
    else:
        start, end, snippet = resolve_regex(source, symbol_name)
    return {"file": file_rel, "symbol": symbol_name, "start": start, "end": end, "snippet": snippet}
