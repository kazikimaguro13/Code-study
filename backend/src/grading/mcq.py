"""Multiple-choice grader — deterministic index match.

Used for selection questions including L4 *design-intent* questions
(ADR/spec grounded), which lets us grade "why was this designed this way?"
without any LLM.
"""

from __future__ import annotations

from typing import Any

from backend.src.grading.base import GradeResult


class MCQGrader:
    type = "mcq"

    def grade(self, user_answer: Any, question: dict[str, Any]) -> GradeResult:
        ans = question.get("answer", {})
        correct_index = int(ans.get("correct_index", -1))
        try:
            chosen = int(user_answer)
        except (TypeError, ValueError):
            chosen = -1

        ok = chosen == correct_index and correct_index >= 0
        options = question.get("answer", {}).get("options", [])
        expected_text = (
            options[correct_index]
            if 0 <= correct_index < len(options)
            else correct_index
        )
        return GradeResult(
            score=1.0 if ok else 0.0,
            correct=ok,
            detail="正しい選択肢" if ok else "誤った選択肢",
            expected={"correct_index": correct_index, "text": expected_text},
            method=self.type,
        )
