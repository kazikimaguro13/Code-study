"""Grader protocol + shared result type.

A *Grader* maps ``(user_answer, question)`` to a :class:`GradeResult`.
Every grader except the optional free-text LLM escalation is **fully
deterministic** — no network, no API key required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class GradeResult:
    """Outcome of grading a single answer.

    Attributes:
        score: 0.0–1.0. Partial credit allowed (e.g. file-only location hit).
        correct: convenience flag, ``score >= pass_threshold``.
        detail: human-readable explanation of how the score was derived.
        expected: the canonical answer, surfaced to the UI on reveal.
        method: which grader produced this ("location", "freetext", ...).
        used_llm: True only when free-text escalation actually called an LLM.
    """

    score: float
    correct: bool
    detail: str
    expected: Any = None
    method: str = ""
    used_llm: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


class Grader(Protocol):
    type: str

    def grade(self, user_answer: Any, question: dict[str, Any]) -> GradeResult: ...


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))
