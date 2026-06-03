"""Validate data/quiz_bank.json — the deterministic quality gate.

Checks, per question:
  * unique ids
  * evidence_substring actually appears in citation.snippet
    (this is what prevents hallucinated answers — a question can't claim
     something the cited code doesn't show)
  * required answer/grading fields exist for the question type
  * mcq.correct_index in range; dataflow.sequence non-empty
Exits non-zero on any failure so CI can gate on it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1] / "data" / "quiz_bank.json"
VALID_TYPES = {"location", "fill_blank", "mcq", "dataflow", "freetext"}
VALID_DIFF = {"L1", "L2", "L3", "L4"}


def validate(bank: dict) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    for q in bank.get("questions", []):
        qid = q.get("id", "<no-id>")
        if qid in seen_ids:
            errors.append(f"{qid}: duplicate id")
        seen_ids.add(qid)

        if q.get("type") not in VALID_TYPES:
            errors.append(f"{qid}: bad type {q.get('type')!r}")
        if q.get("difficulty") not in VALID_DIFF:
            errors.append(f"{qid}: bad difficulty {q.get('difficulty')!r}")
        if not q.get("prompt"):
            errors.append(f"{qid}: empty prompt")

        cit = q.get("citation", {})
        ev = cit.get("evidence_substring", "")
        snip = cit.get("snippet", "")
        if not ev:
            errors.append(f"{qid}: missing evidence_substring")
        elif ev not in snip:
            errors.append(f"{qid}: evidence_substring NOT found in snippet")

        ans = q.get("answer", {})
        t = q.get("type")
        if t == "location":
            if not ans.get("file"):
                errors.append(f"{qid}: location missing answer.file")
        elif t == "fill_blank":
            if not ans.get("accepted"):
                errors.append(f"{qid}: fill_blank missing answer.accepted")
        elif t == "mcq":
            opts = ans.get("options", [])
            ci = ans.get("correct_index", -1)
            if not opts:
                errors.append(f"{qid}: mcq missing options")
            elif not (0 <= ci < len(opts)):
                errors.append(f"{qid}: mcq correct_index out of range")
        elif t == "dataflow":
            if not ans.get("sequence"):
                errors.append(f"{qid}: dataflow missing sequence")
        elif t == "freetext":
            if not ans.get("required_keywords"):
                errors.append(f"{qid}: freetext missing required_keywords")
    return errors


def _warn_resolved(bank: dict) -> list[str]:
    """Soft checks for spec_001 citation embedding (non-fatal warnings)."""
    warnings: list[str] = []
    _NON_SYMBOL_KINDS = {"module", "section"}
    for q in bank.get("questions", []):
        qid = q.get("id", "<no-id>")
        cit = q.get("citation", {})
        sym = cit.get("symbol") or {}
        kind = sym.get("kind") if isinstance(sym, dict) else None
        file_rel = cit.get("file", "")
        is_resolvable = (
            file_rel
            and file_rel.endswith((".py", ".ts", ".tsx", ".js"))
            and kind not in _NON_SYMBOL_KINDS
            and sym.get("name")
        )
        if is_resolvable and not cit.get("source"):
            warnings.append(f"{qid}: resolvable citation lacks embedded source (run build_bank.py)")
    return warnings


def main() -> int:
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    errors = validate(bank)
    n = len(bank.get("questions", []))
    if errors:
        print(f"VALIDATION FAILED ({len(errors)} issue(s)) over {n} questions:")
        for e in errors:
            print("  -", e)
        return 1
    # difficulty / type distribution
    from collections import Counter
    diff = Counter(q["difficulty"] for q in bank["questions"])
    typ = Counter(q["type"] for q in bank["questions"])
    print(f"OK: {n} questions valid.")
    print("  difficulty:", dict(diff))
    print("  type:", dict(typ))
    # soft warnings for spec_001 source embedding
    warns = _warn_resolved(bank)
    if warns:
        print(f"\nWarnings ({len(warns)} — not errors, fix by running scripts/build_bank.py):")
        for w in warns[:5]:
            print("  -", w)
        if len(warns) > 5:
            print(f"  ... and {len(warns) - 5} more")
    else:
        axis_commit = bank.get("meta", {}).get("axis_commit", "n/a")
        resolved = sum(1 for q in bank["questions"] if q.get("citation", {}).get("source"))
        print(f"  source embedding: {resolved}/{n} resolved (axis_commit={axis_commit})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
