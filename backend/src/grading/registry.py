"""Grader registry — dispatch a question to its format-specific grader."""

from __future__ import annotations

from typing import Any

from backend.src.grading.base import GradeResult
from backend.src.grading.dataflow import DataflowGrader
from backend.src.grading.fill_blank import FillBlankGrader
from backend.src.grading.freetext import FreetextGrader, LLMJudge
from backend.src.grading.location import LocationGrader
from backend.src.grading.mcq import MCQGrader


class GraderRegistry:
    def __init__(self, llm_judge: LLMJudge | None = None) -> None:
        self._graders = {
            g.type: g
            for g in (
                LocationGrader(),
                FillBlankGrader(),
                MCQGrader(),
                DataflowGrader(),
                FreetextGrader(llm_judge=llm_judge),
            )
        }

    def grade(self, user_answer: Any, question: dict[str, Any]) -> GradeResult:
        qtype = question.get("type", "")
        grader = self._graders.get(qtype)
        if grader is None:
            return GradeResult(
                score=0.0,
                correct=False,
                detail=f"未対応の出題形式: {qtype!r}",
                method="none",
            )
        return grader.grade(user_answer, question)


__all__ = ["GraderRegistry"]
