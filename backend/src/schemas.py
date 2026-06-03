"""Pydantic request/response models for the quiz API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class NextRequest(BaseModel):
    n: int = 10
    module: str | None = None


class QuestionView(BaseModel):
    id: str
    type: str
    difficulty: str | None = None
    module: str | None = None
    tags: list[str] = []
    prompt: str
    options: list[str] | None = None
    pool: list[str] | None = None


class NextResponse(BaseModel):
    questions: list[QuestionView]


class GradeRequest(BaseModel):
    q_id: str
    # Answer shape depends on type: str | int | list[str] | {file,symbol}
    answer: Any


class CitationView(BaseModel):
    file: str | None = None
    symbol: Any = None
    adr_ref: str | None = None
    snippet: str | None = None


class GradeResponse(BaseModel):
    q_id: str
    score: float
    correct: bool
    detail: str
    expected: Any = None
    method: str
    used_llm: bool
    explanation: str
    citation: CitationView
    next_due: str | None = None
    correct_streak: int | None = None
