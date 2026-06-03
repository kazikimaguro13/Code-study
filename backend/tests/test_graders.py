"""Deterministic grader tests — no network, no API key."""

from backend.src.grading.registry import GraderRegistry

reg = GraderRegistry()


def test_location_full_and_partial():
    q = {
        "type": "location",
        "answer": {"file": "backend/src/search.py", "symbol": "fuse_results"},
        "grading": {"symbol_aliases": ["fuse"], "accept_file_only_partial": 0.5},
    }
    # exact
    r = reg.grade({"file": "backend/src/search.py", "symbol": "fuse_results"}, q)
    assert r.score == 1.0 and r.correct
    # alias + backslash path + parens
    r = reg.grade({"file": "backend\\src\\search.py", "symbol": "fuse()"}, q)
    assert r.score == 1.0
    # file only
    r = reg.grade({"file": "backend/src/search.py", "symbol": "nope"}, q)
    assert r.score == 0.5 and not r.correct
    # single-string form
    r = reg.grade("backend/src/search.py:fuse_results", q)
    assert r.score == 1.0
    # wrong file
    r = reg.grade({"file": "backend/src/rag.py", "symbol": "fuse_results"}, q)
    assert r.score == 0.0


def test_fill_blank_quote_and_normalization():
    q = {
        "type": "fill_blank",
        "answer": {"accepted": ["BM25Okapi", "bm25okapi"]},
        "grading": {"casefold": True},
    }
    assert reg.grade("BM25Okapi", q).correct
    assert reg.grade("  bm25okapi ", q).correct
    assert not reg.grade("BM25", q).correct

    q2 = {"type": "fill_blank", "answer": {"accepted": ["'gemini-2.5-flash'"]}, "grading": {}}
    # single vs double quotes treated equal
    assert reg.grade('"gemini-2.5-flash"', q2).correct


def test_mcq():
    q = {"type": "mcq", "answer": {"options": ["a", "b", "c"], "correct_index": 1}}
    assert reg.grade(1, q).correct
    assert not reg.grade(0, q).correct
    assert not reg.grade("x", q).correct


def test_dataflow_modes():
    seq = ["loader", "chunker", "embedder", "vector_store"]
    q = {
        "type": "dataflow",
        "answer": {"sequence": seq},
        "grading": {"mode": "subsequence", "pass_threshold": 0.75,
                    "aliases": [["vector_store", "VectorStore", "vector_store.py"]]},
    }
    assert reg.grade(seq, q).score == 1.0
    # alias resolves
    assert reg.grade(["loader", "chunker", "embedder", "VectorStore"], q).score == 1.0
    # one missing → 3/4 = 0.75 pass
    r = reg.grade(["loader", "chunker", "vector_store"], q)
    assert r.score == 0.75 and r.correct
    # arrow string form
    r = reg.grade("loader → chunker → embedder → vector_store", q)
    assert r.score == 1.0
    # set mode order-insensitive
    q["grading"]["mode"] = "set"
    assert reg.grade(list(reversed(seq)), q).score == 1.0


def test_freetext_keyword_coverage():
    q = {
        "type": "freetext",
        "answer": {
            "model_answer": "...",
            "required_keywords": [
                {"any_of": ["nfkc"]},
                {"any_of": ["カタカナ", "かな", "ひらがな"]},
                {"any_of": ["小文字", "lowercase"]},
            ],
            "forbidden_keywords": ["形態素解析"],
        },
        "grading": {"min_keyword_coverage": 0.7},
    }
    # full coverage (kana variant + JP) → pass
    r = reg.grade("NFKC正規化してカタカナをひらがなに、さらに小文字化する", q)
    assert r.correct and r.score >= 0.7
    # partial coverage → fail
    r = reg.grade("NFKCをかける", q)
    assert not r.correct
    # forbidden term penalty
    r = reg.grade("NFKCしてかなを小文字化、形態素解析する", q)
    assert r.extra["forbidden_hit"] == ["形態素解析"]


def test_unknown_type():
    assert reg.grade("x", {"type": "weird"}).method == "none"
