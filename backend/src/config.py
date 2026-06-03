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
        if target:
            target_repo: Path | None = Path(target)
        else:
            # Default to the sibling axis-knowledge-rag checkout (the common
            # layout: both repos live under the same parent folder). This lets
            # the quiz show real source out of the box with no configuration.
            sibling = _ROOT.parent / "axis-knowledge-rag"
            target_repo = sibling if sibling.exists() else None
        origins = os.environ.get(
            "QUIZ_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
        )
        return cls(
            quiz_bank_path=Path(bank),
            progress_db_path=Path(db),
            target_repo=target_repo,
            cors_origins=[o.strip() for o in origins.split(",") if o.strip()],
        )
