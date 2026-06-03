"""Symbol anchor resolver — staleness-resistant citation resolution.

Citations store ``{file, symbol{kind,name}}`` rather than line numbers, so
they survive edits above the symbol. This module resolves a symbol to its
*current* line range + full source in the target repo (axis-knowledge-rag),
so the quiz can show the **real, complete code** behind each question after
the user answers — reinforcing "this code does this role".

Python is resolved precisely via ``ast`` (``Class.method`` aware); TS/TSX/JS
fall back to a regex window. Citations that point at a module docstring,
an ADR section, or a file we can't parse fall back to the snippet that was
bundled into quiz_bank.json at generation time.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

# kinds that don't map to a resolvable code symbol → use bundled snippet
_NON_SYMBOL_KINDS = {"module", "section"}


class ResolveError(Exception):
    pass


def _span(source: str, node: ast.AST) -> tuple[int, int, str]:
    start = node.lineno  # type: ignore[attr-defined]
    end = getattr(node, "end_lineno", start)
    lines = source.splitlines()[start - 1 : end]
    return start, end, "\n".join(lines)


def resolve_python(source: str, name: str) -> tuple[int, int, str]:
    """Resolve a (possibly dotted ``Class.method``) Python symbol.

    Returns ``(start_line, end_line, full_source)``.
    """
    tree = ast.parse(source)
    parts = name.split(".")

    # Class.method → find the class, then the method inside it.
    if len(parts) >= 2:
        cls_name, meth_name = parts[-2], parts[-1]
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == cls_name:
                for sub in node.body:
                    if (
                        isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and sub.name == meth_name
                    ):
                        return _span(source, sub)

    target = parts[-1]
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name == target
        ):
            return _span(source, node)
    raise ResolveError(f"symbol not found: {name}")


def resolve_regex(source: str, name: str, *, window: int = 24) -> tuple[int, int, str]:
    """Best-effort resolution for TS/TSX/JS: match the declaration line and
    return a window of following lines for context."""
    target = re.escape(name.rsplit(".", 1)[-1])
    pat = re.compile(
        rf"(export\s+)?(async\s+)?(function\s+{target}\b"
        rf"|const\s+{target}\b|let\s+{target}\b|class\s+{target}\b"
        rf"|{target}\s*[:=]\s*(\(|async|function|\{{))"
    )
    lines = source.splitlines()
    for i, line in enumerate(lines):
        if pat.search(line):
            start = i + 1
            end = min(len(lines), i + window)
            return start, end, "\n".join(lines[i:end])
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
    return {"file": file_rel, "symbol": symbol_name, "start": start, "end": end, "source": snippet}


def resolve_citation(repo_root: str | Path, citation: dict[str, Any]) -> dict[str, Any]:
    """Try to resolve a quiz citation to real source. Never raises.

    Returns ``{"found": bool, "file", "start", "end", "source"}``.
    Falls back to ``found=False`` for ADR/README sections, module docstrings,
    or anything that can't be parsed — the UI then shows the bundled snippet.
    """
    file_rel = citation.get("file")
    if not file_rel:
        return {"found": False}
    sym = citation.get("symbol") or {}
    if isinstance(sym, dict):
        name, kind = sym.get("name"), sym.get("kind")
    else:
        name, kind = str(sym), None

    if not name or kind in _NON_SYMBOL_KINDS:
        return {"found": False}
    if not (file_rel.endswith((".py", ".ts", ".tsx", ".js"))):
        return {"found": False}

    try:
        r = resolve(repo_root, file_rel, name)
        return {"found": True, **r}
    except Exception:  # noqa: BLE001 — resolution is best-effort; never break grading
        return {"found": False}
