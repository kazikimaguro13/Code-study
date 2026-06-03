"""FastAPI app exposing the code-understanding quiz.

Endpoints (mirrors the shape of axis-knowledge-rag's backend/src/api.py):
    GET  /api/health
    POST /api/quiz/next        → pick questions (due-first, weakest-module)
    POST /api/quiz/grade       → grade an answer + record SRS progress
    GET  /api/quiz/overview    → mastery / coverage dashboard data
    GET  /api/quiz/question/{id} (public view, for deep links)
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.src.config import Settings
from backend.src.schemas import (
    GradeRequest,
    GradeResponse,
    NextRequest,
    NextResponse,
)
from backend.src.service import QuizService
from backend.src.store.progress import ProgressStore
from backend.src.store.quiz_bank import QuizBank

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("quiz")

settings = Settings.load()
app = FastAPI(title="axis-code-quiz", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # Allow localhost/127.0.0.1 on ANY port so a shifted dev port (3001, …)
    # doesn't get blocked by CORS.
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)

_service: QuizService | None = None


def get_service() -> QuizService:
    global _service
    if _service is None:
        bank = QuizBank.load(settings.quiz_bank_path)
        progress = ProgressStore(settings.progress_db_path)
        _service = QuizService(bank, progress, target_repo=settings.target_repo)
        logger.info(
            "Loaded quiz_bank: %d questions (target_repo=%s)",
            len(bank),
            settings.target_repo,
        )
    return _service


@app.get("/api/health")
def health() -> dict:
    svc = get_service()
    return {
        "status": "ok",
        "questions": len(svc.bank),
        "modules": len(svc.bank.modules()),
        "meta": svc.bank.meta,
    }


@app.post("/api/quiz/next", response_model=NextResponse)
def quiz_next(req: NextRequest) -> NextResponse:
    svc = get_service()
    qs = svc.next_questions(n=req.n, module=req.module)
    return NextResponse(questions=qs)


@app.post("/api/quiz/grade", response_model=GradeResponse)
def quiz_grade(req: GradeRequest) -> GradeResponse:
    svc = get_service()
    result = svc.grade(req.q_id, req.answer)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return GradeResponse(**result)


@app.get("/api/quiz/overview")
def quiz_overview() -> dict:
    return get_service().overview()


@app.get("/api/quiz/question/{q_id}")
def quiz_question(q_id: str) -> dict:
    svc = get_service()
    q = svc.bank.get(q_id)
    if q is None:
        raise HTTPException(status_code=404, detail="unknown question id")
    return svc.bank.public_view(q)
