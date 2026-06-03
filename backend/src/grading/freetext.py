"""Free-text grader — non-AI keyword coverage, optional LLM escalation.

This is the only format that is *semantically* hard. We approximate
understanding deterministically:

1. **Required-keyword coverage.** ``required_keywords`` is a list of
   *groups*; each group is ``{"any_of": [...]}``. A group is satisfied if
   the (normalized) user text contains any of its synonyms. Coverage =
   satisfied groups / total groups.
2. **Forbidden keywords.** Each present forbidden term applies a penalty.
3. **Citation bonus (optional).** If ``require_citation`` is set, mentioning
   the correct file/symbol adds credit (reuses location-style matching).

Pass if coverage ≥ ``min_keyword_coverage`` (default 0.7).

**Limits (honest):** correct paraphrases that avoid the keywords are
under-credited; keyword-stuffing without understanding is over-credited.
For borderline scores an optional ``llm_judge`` callable can be injected to
escalate — but the grader works fully offline when it is ``None``.
"""

from __future__ import annotations

from typing import Any, Callable

from backend.src.grading.base import GradeResult, clamp01
from backend.src.grading.normalize import normalize_path, normalize_symbol, normalize_text

# Signature: (user_text, question) -> float in [0,1]
LLMJudge = Callable[[str, dict[str, Any]], float]


def _group_satisfied(text_norm: str, group: dict[str, Any]) -> bool:
    for syn in group.get("any_of", []):
        if normalize_text(str(syn)) in text_norm:
            return True
    return False


class FreetextGrader:
    type = "freetext"

    def __init__(self, llm_judge: LLMJudge | None = None) -> None:
        self._llm_judge = llm_judge

    def grade(self, user_answer: Any, question: dict[str, Any]) -> GradeResult:
        ans = question.get("answer", {})
        grading = question.get("grading", {})
        groups = list(ans.get("required_keywords", []))
        forbidden = [str(f) for f in ans.get("forbidden_keywords", [])]
        min_cov = float(grading.get("min_keyword_coverage", 0.7))
        escalation = grading.get("llm_escalation", "off")  # off|borderline|on
        forbidden_penalty = float(grading.get("forbidden_penalty", 0.34))

        text_norm = normalize_text(str(user_answer or ""))
        if not groups:
            coverage = 1.0 if text_norm else 0.0
        else:
            satisfied = sum(1 for g in groups if _group_satisfied(text_norm, g))
            coverage = satisfied / len(groups)

        # Forbidden / misconception penalty.
        hit_forbidden = [f for f in forbidden if normalize_text(f) in text_norm]
        penalty = forbidden_penalty * len(hit_forbidden)

        # Optional citation credit.
        cite_note = ""
        if grading.get("require_citation"):
            cite = question.get("citation", {})
            want_file = normalize_path(str(cite.get("file", "")))
            want_sym = normalize_symbol(str((cite.get("symbol") or {}).get("name", "")))
            if (want_file and want_file in normalize_path(str(user_answer))) or (
                want_sym and want_sym in normalize_symbol(str(user_answer))
            ):
                coverage = min(1.0, coverage + 0.15)
                cite_note = " / 出典言及ボーナス +0.15"

        score = clamp01(coverage - penalty)
        used_llm = False
        method = self.type

        # Escalate to LLM judge if configured and (always | borderline band).
        band = abs(score - min_cov) <= 0.15
        if self._llm_judge is not None and (
            escalation == "on" or (escalation == "borderline" and band)
        ):
            try:
                llm_score = clamp01(self._llm_judge(str(user_answer or ""), question))
                # Blend: trust the LLM but keep deterministic floor visible.
                score = clamp01(0.5 * score + 0.5 * llm_score)
                used_llm = True
                method = "freetext+llm"
            except Exception:  # noqa: BLE001 — never let grading crash
                pass

        detail = f"キーワード被覆 {coverage:.2f}（しきい値 {min_cov}）"
        if hit_forbidden:
            detail += f" / 禁止語 {hit_forbidden} 検出 -{penalty:.2f}"
        detail += cite_note

        return GradeResult(
            score=score,
            correct=score >= min_cov,
            detail=detail,
            expected=ans.get("model_answer", ""),
            method=method,
            used_llm=used_llm,
            extra={"coverage": coverage, "forbidden_hit": hit_forbidden},
        )
