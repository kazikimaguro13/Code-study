"""Location grader — "which file / which function implements X?".

Fully deterministic. The user answer is ``{"file": ..., "symbol": ...}``
(the UI may also accept a single free string that we split). Grading:

- file + symbol match               → 1.0
- file matches, symbol wrong/empty  → ``accept_file_only_partial`` (default 0.5)
- file wrong                        → 0.0

Symbol matching is loose: aliases from ``grading.symbol_aliases`` and the
dotted-tail of the symbol are all accepted.
"""

from __future__ import annotations

from typing import Any

from backend.src.grading.base import GradeResult, clamp01
from backend.src.grading.normalize import normalize_path, normalize_symbol, symbol_tail


def _parse_answer(user_answer: Any) -> tuple[str, str]:
    if isinstance(user_answer, dict):
        return str(user_answer.get("file", "")), str(user_answer.get("symbol", ""))
    # Single string: "backend/src/search.py:fuse_results" or "fuse_results"
    s = str(user_answer or "")
    if ":" in s:
        f, sym = s.split(":", 1)
        return f.strip(), sym.strip()
    if "/" in s or s.endswith(".py") or s.endswith(".ts") or s.endswith(".tsx"):
        return s.strip(), ""
    return "", s.strip()


def _symbol_matches(given: str, answer: str, aliases: list[str]) -> bool:
    g = normalize_symbol(given)
    if not g:
        return False
    candidates = {normalize_symbol(answer), symbol_tail(answer)}
    candidates |= {normalize_symbol(a) for a in aliases}
    candidates |= {symbol_tail(a) for a in aliases}
    candidates.discard("")
    return g in candidates or symbol_tail(given) in candidates


class LocationGrader:
    type = "location"

    def grade(self, user_answer: Any, question: dict[str, Any]) -> GradeResult:
        ans = question.get("answer", {})
        grading = question.get("grading", {})
        ans_file = str(ans.get("file", ""))
        ans_symbol = str(ans.get("symbol", ""))
        aliases = list(grading.get("symbol_aliases", []))
        file_only = float(grading.get("accept_file_only_partial", 0.5))
        pass_threshold = float(grading.get("pass_threshold", 0.99))

        u_file, u_symbol = _parse_answer(user_answer)
        file_ok = normalize_path(u_file) == normalize_path(ans_file)
        symbol_ok = _symbol_matches(u_symbol, ans_symbol, aliases)

        if file_ok and symbol_ok:
            score, detail = 1.0, "file と symbol が一致"
        elif file_ok and not ans_symbol:
            score, detail = 1.0, "file 一致（symbol 不問の問題）"
        elif file_ok:
            score = file_only
            detail = f"file は正解 / symbol が未一致（部分点 {file_only}）"
        else:
            score, detail = 0.0, "file が不一致"

        score = clamp01(score)
        return GradeResult(
            score=score,
            correct=score >= pass_threshold,
            detail=detail,
            expected={"file": ans_file, "symbol": ans_symbol},
            method=self.type,
        )
