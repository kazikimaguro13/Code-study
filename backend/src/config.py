"""Configuration for the quiz backend (env-driven, sane local defaults)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Repo root = two levels up from this file (backend/src/config.py).
_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Settings:
    quiz_bank_path: Path
    progress_db_path: Path
    # Path to the codebase being studied (used by the optional anchor
    # resolver for live snippet freshness; not required for MVP).
    target_repo: Path | None
    cors_origins: list[str]

    @classmethod
    def load(cls) -> "Settings":
        bank = os.environ.get("QUIZ_BANK_PATH", str(_ROOT / "data" / "quiz_bank.json"))
        db = os.environ.get("PROGRESS_DB_PATH", str(_ROOT / "data" / "progress.db"))
        target = os.environ.get("TARGET_REPO")
        origins = os.environ.get(
            "QUIZ_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
        )
        return cls(
            quiz_bank_path=Path(bank),
            progress_db_path=Path(db),
            target_repo=Path(target) if target else None,
            cors_origins=[o.strip() for o in origins.split(",") if o.strip()],
        )
