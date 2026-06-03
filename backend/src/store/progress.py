"""Learning progress store: SQLite + SM-2-lite spaced repetition.

Tracks every attempt and an SRS (spaced-repetition) state per question so
the tool can (a) resurface due questions, (b) compute per-module mastery,
and (c) report coverage. Pure stdlib ``sqlite3`` — no extra deps.

SM-2-lite schedule (simplified Anki/SuperMemo):
    correct   → interval grows: 1d, 3d, then ×ease; ease nudges up to 2.7
    incorrect → reset streak, due tomorrow, ease drops (floor 1.3)
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    q_id      TEXT NOT NULL,
    ts        TEXT NOT NULL,
    score     REAL NOT NULL,
    correct   INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS srs (
    q_id           TEXT PRIMARY KEY,
    attempts       INTEGER NOT NULL DEFAULT 0,
    correct_streak INTEGER NOT NULL DEFAULT 0,
    ease           REAL NOT NULL DEFAULT 2.5,
    interval_days  INTEGER NOT NULL DEFAULT 0,
    due_date       TEXT NOT NULL,
    last_score     REAL NOT NULL DEFAULT 0,
    last_seen      TEXT
);
"""


class ProgressStore:
    def __init__(self, db_path: str | Path) -> None:
        self._path = str(db_path)
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # ---- recording -------------------------------------------------
    def record_attempt(self, q_id: str, score: float, correct: bool) -> dict[str, Any]:
        now = datetime.now()
        self._conn.execute(
            "INSERT INTO attempts (q_id, ts, score, correct) VALUES (?,?,?,?)",
            (q_id, now.isoformat(), float(score), int(correct)),
        )
        srs = self._get_srs(q_id)
        new = self._schedule(srs, score, correct, today=now.date())
        new["q_id"] = q_id
        self._conn.execute(
            """INSERT INTO srs (q_id, attempts, correct_streak, ease, interval_days,
                                due_date, last_score, last_seen)
               VALUES (:q_id,:attempts,:correct_streak,:ease,:interval_days,
                       :due_date,:last_score,:last_seen)
               ON CONFLICT(q_id) DO UPDATE SET
                 attempts=:attempts, correct_streak=:correct_streak, ease=:ease,
                 interval_days=:interval_days, due_date=:due_date,
                 last_score=:last_score, last_seen=:last_seen""",
            new,
        )
        self._conn.commit()
        return new

    def _get_srs(self, q_id: str) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT * FROM srs WHERE q_id=?", (q_id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def _schedule(
        srs: dict[str, Any] | None, score: float, correct: bool, *, today: date
    ) -> dict[str, Any]:
        attempts = (srs["attempts"] if srs else 0) + 1
        ease = srs["ease"] if srs else 2.5
        streak = srs["correct_streak"] if srs else 0
        interval = srs["interval_days"] if srs else 0

        if correct:
            streak += 1
            if streak == 1:
                interval = 1
            elif streak == 2:
                interval = 3
            else:
                interval = max(1, round(interval * ease))
            ease = min(2.7, ease + 0.1)
        else:
            streak = 0
            interval = 0  # due again immediately / next session
            ease = max(1.3, ease - 0.2)

        due = today + timedelta(days=interval)
        return {
            "q_id": srs["q_id"] if srs else None,  # filled by caller path
            "attempts": attempts,
            "correct_streak": streak,
            "ease": round(ease, 3),
            "interval_days": interval,
            "due_date": due.isoformat(),
            "last_score": float(score),
            "last_seen": datetime.now().isoformat(),
        }

    # ---- queries ---------------------------------------------------
    def due_question_ids(self, on: date | None = None) -> list[str]:
        on = on or date.today()
        rows = self._conn.execute(
            "SELECT q_id FROM srs WHERE due_date <= ? ORDER BY due_date ASC",
            (on.isoformat(),),
        ).fetchall()
        return [r["q_id"] for r in rows]

    def seen_question_ids(self) -> set[str]:
        rows = self._conn.execute("SELECT q_id FROM srs").fetchall()
        return {r["q_id"] for r in rows}

    def srs_state(self, q_id: str) -> dict[str, Any] | None:
        return self._get_srs(q_id)

    def question_mastery(self, q_id: str) -> float:
        """0–1 mastery for a single question from streak + last score."""
        srs = self._get_srs(q_id)
        if not srs:
            return 0.0
        streak_factor = min(1.0, srs["correct_streak"] / 3.0)
        return round(0.5 * streak_factor + 0.5 * srs["last_score"], 3)

    def all_srs(self) -> dict[str, dict[str, Any]]:
        rows = self._conn.execute("SELECT * FROM srs").fetchall()
        return {r["q_id"]: dict(r) for r in rows}

    def attempt_count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) AS c FROM attempts").fetchone()["c"]

    def close(self) -> None:
        self._conn.close()
