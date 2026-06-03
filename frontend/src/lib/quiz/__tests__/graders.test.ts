// Parity tests — TS ports of backend/tests/test_graders.py and test_progress_service.py.
// Each case matches the Python test exactly to guarantee grading equivalence.

import { describe, it, expect } from "vitest";
import { grade } from "../graders";
import { schedule } from "../srs";
import type { Question } from "../types";

function q(partial: Partial<Question> & { type: Question["type"] }): Question {
  return {
    id: "test",
    difficulty: "L1",
    module: null,
    tags: [],
    prompt: "",
    citation: { file: null, symbol: null, adr_ref: null, snippet: null },
    answer: {},
    grading: {},
    explanation: "",
    ...partial,
  } as Question;
}

// ---- location ----

describe("location grader", () => {
  const question = q({
    type: "location",
    answer: { file: "backend/src/search.py", symbol: "fuse_results" },
    grading: { symbol_aliases: ["fuse"], accept_file_only_partial: 0.5 },
  });

  it("exact match", () => {
    const r = grade({ file: "backend/src/search.py", symbol: "fuse_results" }, question);
    expect(r.score).toBe(1.0);
    expect(r.correct).toBe(true);
  });

  it("alias + backslash path + parens", () => {
    const r = grade({ file: "backend\\src\\search.py", symbol: "fuse()" }, question);
    expect(r.score).toBe(1.0);
  });

  it("file only → partial score", () => {
    const r = grade({ file: "backend/src/search.py", symbol: "nope" }, question);
    expect(r.score).toBe(0.5);
    expect(r.correct).toBe(false);
  });

  it("single-string colon form", () => {
    const r = grade("backend/src/search.py:fuse_results", question);
    expect(r.score).toBe(1.0);
  });

  it("wrong file", () => {
    const r = grade({ file: "backend/src/rag.py", symbol: "fuse_results" }, question);
    expect(r.score).toBe(0.0);
  });
});

// ---- fill_blank ----

describe("fill_blank grader", () => {
  it("casefold match", () => {
    const question = q({
      type: "fill_blank",
      answer: { accepted: ["BM25Okapi", "bm25okapi"] },
      grading: { casefold: true },
    });
    expect(grade("BM25Okapi", question).correct).toBe(true);
    expect(grade("  bm25okapi ", question).correct).toBe(true);
    expect(grade("BM25", question).correct).toBe(false);
  });

  it("single vs double quote equivalence", () => {
    const question = q({
      type: "fill_blank",
      answer: { accepted: ["'gemini-2.5-flash'"] },
      grading: {},
    });
    expect(grade('"gemini-2.5-flash"', question).correct).toBe(true);
  });
});

// ---- mcq ----

describe("mcq grader", () => {
  const question = q({
    type: "mcq",
    answer: { options: ["a", "b", "c"], correct_index: 1 },
  });

  it("correct index", () => expect(grade(1, question).correct).toBe(true));
  it("wrong index", () => expect(grade(0, question).correct).toBe(false));
  it("invalid input", () => expect(grade("x", question).correct).toBe(false));
});

// ---- dataflow ----

describe("dataflow grader", () => {
  const seq = ["loader", "chunker", "embedder", "vector_store"];
  const question = q({
    type: "dataflow",
    answer: { sequence: seq },
    grading: {
      mode: "subsequence",
      pass_threshold: 0.75,
      aliases: [["vector_store", "VectorStore", "vector_store.py"]],
    },
  });

  it("exact match", () => expect(grade(seq, question).score).toBe(1.0));

  it("alias resolves", () => {
    expect(grade(["loader", "chunker", "embedder", "VectorStore"], question).score).toBe(1.0);
  });

  it("one missing → 3/4 = 0.75 pass", () => {
    const r = grade(["loader", "chunker", "vector_store"], question);
    expect(r.score).toBe(0.75);
    expect(r.correct).toBe(true);
  });

  it("arrow string form", () => {
    expect(grade("loader → chunker → embedder → vector_store", question).score).toBe(1.0);
  });

  it("set mode order-insensitive", () => {
    const qSet = q({
      type: "dataflow",
      answer: { sequence: seq },
      grading: {
        mode: "set",
        pass_threshold: 0.75,
        aliases: [["vector_store", "VectorStore", "vector_store.py"]],
      },
    });
    expect(grade([...seq].reverse(), qSet).score).toBe(1.0);
  });
});

// ---- freetext ----

describe("freetext grader", () => {
  const question = q({
    type: "freetext",
    answer: {
      model_answer: "...",
      required_keywords: [
        { any_of: ["nfkc"] },
        { any_of: ["カタカナ", "かな", "ひらがな"] },
        { any_of: ["小文字", "lowercase"] },
      ],
      forbidden_keywords: ["形態素解析"],
    },
    grading: { min_keyword_coverage: 0.7 },
  });

  it("full coverage → pass", () => {
    const r = grade("NFKC正規化してカタカナをひらがなに、さらに小文字化する", question);
    expect(r.correct).toBe(true);
    expect(r.score).toBeGreaterThanOrEqual(0.7);
  });

  it("partial coverage → fail", () => {
    const r = grade("NFKCをかける", question);
    expect(r.correct).toBe(false);
  });

  it("forbidden term penalty applied", () => {
    const r = grade("NFKCしてかなを小文字化、形態素解析する", question);
    expect((r.extra as { forbidden_hit: string[] }).forbidden_hit).toEqual(["形態素解析"]);
  });
});

// ---- unknown type ----

it("unknown type returns method=none", () => {
  const question = q({ type: "location" });
  // @ts-expect-error testing unknown type
  question.type = "weird";
  expect(grade("x", question).method).toBe("none");
});

// ---- SRS / SM-2-lite (mirrors test_progress_service.py) ----

describe("SRS schedule", () => {
  it("first correct: streak=1, interval=1, ease increases", () => {
    const s = schedule(null, 1.0, true);
    expect(s.correct_streak).toBe(1);
    expect(s.interval_days).toBe(1);
    expect(s.ease).toBeCloseTo(2.6, 5);
  });

  it("second correct: streak=2, interval=3", () => {
    const s1 = schedule(null, 1.0, true);
    const s2 = schedule(s1, 1.0, true);
    expect(s2.correct_streak).toBe(2);
    expect(s2.interval_days).toBe(3);
  });

  it("third correct: interval grows by ease", () => {
    let s = schedule(null, 1.0, true);
    s = schedule(s, 1.0, true);
    const s3 = schedule(s, 1.0, true);
    expect(s3.correct_streak).toBe(3);
    expect(s3.interval_days).toBe(Math.max(1, Math.round(3 * s.ease)));
  });

  it("incorrect resets streak and interval, ease drops", () => {
    // null → correct (ease 2.5→2.6) → incorrect (ease 2.6→2.4)
    let s = schedule(null, 1.0, true);
    s = schedule(s, 0.0, false);
    expect(s.correct_streak).toBe(0);
    expect(s.interval_days).toBe(0);
    expect(s.ease).toBeCloseTo(2.4, 5);
  });

  it("ease floor is 1.3", () => {
    let s = schedule(null, 0.0, false);
    for (let i = 0; i < 20; i++) s = schedule(s, 0.0, false);
    expect(s.ease).toBe(1.3);
  });

  it("ease ceiling is 2.7", () => {
    let s = schedule(null, 1.0, true);
    for (let i = 0; i < 20; i++) s = schedule(s, 1.0, true);
    expect(s.ease).toBe(2.7);
  });
});
