"""Quiz service: selection logic, grading orchestration, progress reporting.

Wires together the QuizBank, the ProgressStore (SM-2-lite), and the grader
registry. The selection policy implements the spec:

    1. due review questions first (spaced repetition)
    2. remaining slots filled with new questions, weighted toward the
       least-mastered modules.
"""

from __future__ import annotations

import random
from typing import Any

from backend.src.grading.registry import GraderRegistry
from backend.src.store.progress import ProgressStore
from backend.src.store.quiz_bank import QuizBank


class QuizService:
    def __init__(
        self,
        bank: QuizBank,
        progress: ProgressStore,
        registry: GraderRegistry | None = None,
        *,
        rng: random.Random | None = None,
    ) -> None:
        self.bank = bank
        self.progress = progress
        self.registry = registry or GraderRegistry()
        self._rng = rng or random.Random()

    # ---- selection -------------------------------------------------
    def next_questions(self, n: int = 10, *, module: str | None = None) -> list[dict]:
        pool = self.bank.by_module(module) if module else self.bank.all()
        pool_ids = {q["id"] for q in pool}
        due = [qid for qid in self.progress.due_question_ids() if qid in pool_ids]
        seen = self.progress.seen_question_ids()

        chosen: list[str] = []
        for qid in due:
            if len(chosen) >= n:
                break
            chosen.append(qid)

        if len(chosen) < n:
            unseen = [q for q in pool if q["id"] not in seen and q["id"] not in chosen]
            mastery = self.module_mastery()
            # Lower mastery → higher weight (weakest-first).
            def weight(q: dict) -> float:
                m = mastery.get(q.get("module", ""), {}).get("mastery", 0.0)
                return (1.0 - m) + 0.05
            self._rng.shuffle(unseen)
            unseen.sort(key=weight, reverse=True)
            for q in unseen:
                if len(chosen) >= n:
                    break
                chosen.append(q["id"])

        # If still short (everything seen & not due), recycle lowest-mastery seen.
        if len(chosen) < n:
            remaining = [q["id"] for q in pool if q["id"] not in chosen]
            remaining.sort(key=lambda qid: self.progress.question_mastery(qid))
            chosen.extend(remaining[: n - len(chosen)])

        return [self.bank.public_view(self.bank.get(qid)) for qid in chosen if self.bank.get(qid)]

    # ---- grading ---------------------------------------------------
    def grade(self, q_id: str, user_answer: Any) -> dict[str, Any]:
        q = self.bank.get(q_id)
        if q is None:
            return {"error": f"unknown question id: {q_id}"}
        result = self.registry.grade(user_answer, q)
        self.progress.record_attempt(q_id, result.score, result.correct)
        srs = self.progress.srs_state(q_id) or {}
        citation = q.get("citation", {})
        return {
            "q_id": q_id,
            "score": result.score,
            "correct": result.correct,
            "detail": result.detail,
            "expected": result.expected,
            "method": result.method,
            "used_llm": result.used_llm,
            "explanation": q.get("explanation", ""),
            "citation": {
                "file": citation.get("file"),
                "symbol": citation.get("symbol"),
                "adr_ref": citation.get("adr_ref"),
                "snippet": citation.get("snippet", ""),
            },
            "next_due": srs.get("due_date"),
            "correct_streak": srs.get("correct_streak"),
        }

    # ---- reporting -------------------------------------------------
    def module_mastery(self) -> dict[str, dict[str, Any]]:
        counts = self.bank.count_by_module()
        out: dict[str, dict[str, Any]] = {}
        for module, total in counts.items():
            qs = self.bank.by_module(module)
            masteries = [self.progress.question_mastery(q["id"]) for q in qs]
            seen = self.progress.seen_question_ids()
            attempted = sum(1 for q in qs if q["id"] in seen)
            out[module] = {
                "total": total,
                "attempted": attempted,
                "coverage": round(attempted / total, 3) if total else 0.0,
                "mastery": round(sum(masteries) / total, 3) if total else 0.0,
            }
        return out

    def overview(self) -> dict[str, Any]:
        mm = self.module_mastery()
        total_q = len(self.bank)
        overall_mastery = (
            round(sum(m["mastery"] * m["total"] for m in mm.values()) / total_q, 3)
            if total_q
            else 0.0
        )
        return {
            "total_questions": total_q,
            "attempts": self.progress.attempt_count(),
            "due_count": len(self.progress.due_question_ids()),
            "overall_mastery": overall_mastery,
            "modules": mm,
            "meta": self.bank.meta,
        }
