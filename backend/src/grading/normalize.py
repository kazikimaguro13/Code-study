"""Text / symbol / path normalization for deterministic grading.

Mirrors the spirit of axis-knowledge-rag's ``backend/src/normalizer.py``
(NFKC + カタカナ→ひらがな + lowercase) so that Japanese free-text answers
match consistently. Adds code-oriented helpers (path / symbol folding).
"""

from __future__ import annotations

import re
import unicodedata

_KATAKANA_START = 0x30A1
_KATAKANA_END = 0x30F6
_HIRAGANA_START = 0x3041


def _katakana_to_hiragana(text: str) -> str:
    out: list[str] = []
    for ch in text:
        cp = ord(ch)
        if _KATAKANA_START <= cp <= _KATAKANA_END:
            out.append(chr(cp - _KATAKANA_START + _HIRAGANA_START))
        else:
            out.append(ch)
    return "".join(out)


def normalize_text(text: str) -> str:
    """NFKC + katakana→hiragana + lowercase + collapse whitespace.

    Used for free-text keyword matching where Japanese writing variants
    (全角/半角・カナ/かな・大文字小文字) must not cause false negatives.
    """
    if not text:
        return ""
    s = unicodedata.normalize("NFKC", text)
    s = _katakana_to_hiragana(s)
    s = s.lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_path(path: str) -> str:
    """Fold a file path so equivalent spellings compare equal.

    - backslashes → forward slashes
    - strip a leading ``backend/src/`` style prefix is *not* done (paths are
      compared whole), but leading ``./`` and surrounding spaces are removed
    - lowercase (case-insensitive file systems / casual typing)
    """
    if not path:
        return ""
    s = path.strip().replace("\\", "/")
    s = re.sub(r"^\./", "", s)
    s = re.sub(r"/+", "/", s)
    return s.lower()


# Accept "fuse_results", "fuse", "SearchEngine.search", "search()" etc.
_SYMBOL_STRIP_RE = re.compile(r"[()\s]")


def normalize_symbol(symbol: str) -> str:
    """Fold a symbol reference.

    Strips parentheses / whitespace, lowercases, and keeps only the last
    dotted segment so ``SearchEngine.fuse`` and ``fuse`` can be compared by
    callers that opt into loose matching (the grader decides).
    """
    if not symbol:
        return ""
    s = _SYMBOL_STRIP_RE.sub("", symbol).lower()
    return s


def symbol_tail(symbol: str) -> str:
    """Return the final dotted segment of a (normalized) symbol."""
    s = normalize_symbol(symbol)
    return s.rsplit(".", 1)[-1] if s else s
