"""Load and index the generated question bank (quiz_bank.json)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class QuizBank:
    def __init__(self, questions: list[dict[str, Any]], meta: dict[str, Any]) -> None:
        self._questions = questions
        self._by_id = {q["id"]: q for q in questions}
        self.meta = meta

    @classmethod
    def load(cls, path: str | Path) -> "QuizBank":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(data.get("questions", []), data.get("meta", {}))

    def __len__(self) -> int:
        return len(self._questions)

    def all(self) -> list[dict[str, Any]]:
        return list(self._questions)

    def get(self, q_id: str) -> dict[str, Any] | None:
        return self._by_id.get(q_id)

    def modules(self) -> list[str]:
        seen: list[str] = []
        for q in self._questions:
            m = q.get("module", "")
            if m and m not in seen:
                seen.append(m)
        return seen

    def by_module(self, module: str) -> list[dict[str, Any]]:
        return [q for q in self._questions if q.get("module") == module]

    def count_by_module(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for q in self._questions:
            out[q.get("module", "")] = out.get(q.get("module", ""), 0) + 1
        return out

    def public_view(self, q: dict[str, Any]) -> dict[str, Any]:
        """Strip answer/grading internals before sending a question to the UI."""
        view = {
            "id": q["id"],
            "type": q["type"],
            "difficulty": q.get("difficulty"),
            "module": q.get("module"),
            "tags": q.get("tags", []),
            "prompt": q["prompt"],
        }
        if q["type"] == "mcq":
            view["options"] = q.get("answer", {}).get("options", [])
        if q["type"] == "dataflow":
            view["pool"] = q.get("pool", [])  # optional shuffled candidate steps
        return view
