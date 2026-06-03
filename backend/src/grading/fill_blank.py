"""Fill-in-the-blank grader — deterministic string match.

The question prompt contains a single ``____`` blank standing for one
identifier / literal / constant. The answer carries an ``accepted`` list of
equivalent strings. Matching is done after light normalization (trim,
unify quote characters, optional case-fold).
"""

from __future__ import annotations

from typing import Any

from backend.src.grading.base import GradeResult


def _fold(s: str, *, casefold: bool) -> str:
    s = str(s).strip().strip("`")
    s = s.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    # Treat single/double quotes as equivalent for string literals.
    s = s.replace("'", '"')
    if casefold:
        s = s.lower()
    return s


class FillBlankGrader:
    type = "fill_blank"

    def grade(self, user_answer: Any, question: dict[str, Any]) -> GradeResult:
        ans = question.get("answer", {})
        grading = question.get("grading", {})
        accepted = [str(a) for a in ans.get("accepted", [])]
        casefold = bool(grading.get("casefold", False))

        u = _fold(user_answer, casefold=casefold)
        folded_accepted = {_fold(a, casefold=casefold) for a in accepted}
        ok = u in folded_accepted and u != ""

        return GradeResult(
            score=1.0 if ok else 0.0,
            correct=ok,
            detail="正解と一致" if ok else "受理候補のいずれにも一致せず",
            expected=accepted,
            method=self.type,
        )
