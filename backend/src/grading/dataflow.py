"""Dataflow grader — order/sequence matching with partial credit.

The answer is an ordered ``sequence`` of module/function names describing
a pipeline (e.g. loader → chunker → embedder → vector_store → search.fuse).
Three grading modes:

- ``set``         : order-insensitive set overlap (Jaccard).
- ``subsequence`` : longest-common-subsequence ratio (rewards correct
                    relative ordering even with gaps).
- ``ordered``     : full positional match (strict).

Aliases collapse equivalent spellings (``loader`` / ``loader.py`` /
``MarkdownLoader``). Fully deterministic.
"""

from __future__ import annotations

from typing import Any

from backend.src.grading.base import GradeResult, clamp01
from backend.src.grading.normalize import normalize_symbol, symbol_tail


def _canon(token: str, alias_map: dict[str, str]) -> str:
    t = symbol_tail(token)
    return alias_map.get(t, alias_map.get(normalize_symbol(token), t))


def _build_alias_map(aliases: list[list[str]]) -> dict[str, str]:
    """Each group maps every member to the group's first (canonical) member."""
    out: dict[str, str] = {}
    for group in aliases:
        if not group:
            continue
        canon = symbol_tail(group[0])
        for member in group:
            out[symbol_tail(member)] = canon
            out[normalize_symbol(member)] = canon
    return out


def _lcs_len(a: list[str], b: list[str]) -> int:
    if not a or not b:
        return 0
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[len(a)][len(b)]


class DataflowGrader:
    type = "dataflow"

    def grade(self, user_answer: Any, question: dict[str, Any]) -> GradeResult:
        ans = question.get("answer", {})
        grading = question.get("grading", {})
        mode = grading.get("mode", "subsequence")
        pass_threshold = float(grading.get("pass_threshold", 0.8))
        alias_map = _build_alias_map(grading.get("aliases", []))

        expected = [_canon(x, alias_map) for x in ans.get("sequence", [])]
        if isinstance(user_answer, str):
            raw = [p for p in _split(user_answer) if p.strip()]
        else:
            raw = [str(x) for x in (user_answer or [])]
        given = [_canon(x, alias_map) for x in raw]

        if not expected:
            return GradeResult(0.0, False, "正解列が空", expected, self.type)

        if mode == "set":
            es, gs = set(expected), set(given)
            inter = len(es & gs)
            union = len(es | gs) or 1
            score = inter / union
            detail = f"集合一致 {inter}/{len(es)}（Jaccard {score:.2f}）"
        elif mode == "ordered":
            hits = sum(1 for i, e in enumerate(expected) if i < len(given) and given[i] == e)
            score = hits / len(expected)
            detail = f"完全順序一致 {hits}/{len(expected)}"
        else:  # subsequence (default)
            lcs = _lcs_len(expected, given)
            score = lcs / len(expected)
            detail = f"順序保持の共通部分列 {lcs}/{len(expected)}"

        score = clamp01(score)
        return GradeResult(
            score=score,
            correct=score >= pass_threshold,
            detail=detail,
            expected=ans.get("sequence", []),
            method=self.type,
        )


def _split(s: str) -> list[str]:
    for sep in ["→", "->", "=>", "\n", ",", "、", ">"]:
        s = s.replace(sep, "|")
    return [p.strip() for p in s.split("|")]
