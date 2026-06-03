"""Progress (SM-2-lite) + service selection tests."""

import random
from datetime import date, timedelta

from backend.src.service import QuizService
from backend.src.store.progress import ProgressStore
from backend.src.store.quiz_bank import QuizBank


def _bank():
    qs = [
        {"id": "q1", "type": "mcq", "module": "m_a", "difficulty": "L1",
         "prompt": "?", "answer": {"options": ["x", "y"], "correct_index": 0},
         "citation": {}, "explanation": "e"},
        {"id": "q2", "type": "mcq", "module": "m_a", "difficulty": "L1",
         "prompt": "?", "answer": {"options": ["x", "y"], "correct_index": 1},
         "citation": {}, "explanation": "e"},
        {"id": "q3", "type": "mcq", "module": "m_b", "difficulty": "L2",
         "prompt": "?", "answer": {"options": ["x", "y"], "correct_index": 0},
         "citation": {}, "explanation": "e"},
    ]
    return QuizBank(qs, {"repo_commit": "test"})


def test_sm2_schedule_grows_and_resets(tmp_path):
    p = ProgressStore(tmp_path / "p.db")
    # first correct → interval 1, due tomorrow
    s = p.record_attempt("q1", 1.0, True)
    assert s["interval_days"] == 1
    assert s["due_date"] == (date.today() + timedelta(days=1)).isoformat()
    # second correct → interval 3
    s = p.record_attempt("q1", 1.0, True)
    assert s["interval_days"] == 3
    # wrong → reset, due today, ease drops
    s = p.record_attempt("q1", 0.0, False)
    assert s["correct_streak"] == 0 and s["interval_days"] == 0
    assert s["ease"] < 2.7


def test_service_due_first_then_weakest(tmp_path):
    svc = QuizService(_bank(), ProgressStore(tmp_path / "p.db"), rng=random.Random(0))
    # Nothing seen yet → returns new questions
    first = svc.next_questions(n=2)
    assert len(first) == 2
    # Grade q3 wrong so it becomes due; ensure it resurfaces
    svc.grade("q3", 1)  # wrong (correct_index 0)
    due_ids = svc.progress.due_question_ids()
    assert "q3" in due_ids


def test_overview_shape(tmp_path):
    svc = QuizService(_bank(), ProgressStore(tmp_path / "p.db"))
    svc.grade("q1", 0)  # correct
    ov = svc.overview()
    assert ov["total_questions"] == 3
    assert "m_a" in ov["modules"]
    assert 0.0 <= ov["overall_mastery"] <= 1.0
