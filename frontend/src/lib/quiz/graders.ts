// TS port of backend/src/grading/*.py — deterministic graders for all 5 question types.

import { normalizeText, normalizePath, normalizeSymbol, symbolTail } from "./normalize";
import type { Question } from "./types";

export interface InternalGradeResult {
  score: number;
  correct: boolean;
  detail: string;
  expected: unknown;
  method: string;
  used_llm: boolean;
  extra: Record<string, unknown>;
}

function clamp01(x: number): number {
  return Math.max(0, Math.min(1, x));
}

// ---- location (mirrors location.py) ----

function parseLocationAnswer(userAnswer: unknown): [string, string] {
  if (typeof userAnswer === "object" && userAnswer !== null) {
    const a = userAnswer as Record<string, unknown>;
    return [String(a.file ?? ""), String(a.symbol ?? "")];
  }
  const s = String(userAnswer ?? "");
  if (s.includes(":")) {
    const idx = s.indexOf(":");
    return [s.slice(0, idx).trim(), s.slice(idx + 1).trim()];
  }
  if (s.includes("/") || s.endsWith(".py") || s.endsWith(".ts") || s.endsWith(".tsx")) {
    return [s.trim(), ""];
  }
  return ["", s.trim()];
}

function symbolMatches(given: string, answer: string, aliases: string[]): boolean {
  const g = normalizeSymbol(given);
  if (!g) return false;
  const candidates = new Set([
    normalizeSymbol(answer),
    symbolTail(answer),
    ...aliases.map((a) => normalizeSymbol(a)),
    ...aliases.map((a) => symbolTail(a)),
  ]);
  candidates.delete("");
  return candidates.has(g) || candidates.has(symbolTail(given));
}

export function gradeLocation(userAnswer: unknown, question: Question): InternalGradeResult {
  const ans = question.answer;
  const grading = question.grading;
  const ansFile = ans.file ?? "";
  const ansSymbol = ans.symbol ?? "";
  const aliases = grading.symbol_aliases ?? [];
  const fileOnlyPartial = grading.accept_file_only_partial ?? 0.5;
  const passThreshold = grading.pass_threshold ?? 0.99;

  const [uFile, uSymbol] = parseLocationAnswer(userAnswer);
  const fileOk = normalizePath(uFile) === normalizePath(ansFile);
  const symbolOk = symbolMatches(uSymbol, ansSymbol, aliases);

  let score: number;
  let detail: string;
  if (fileOk && symbolOk) {
    score = 1.0;
    detail = "file と symbol が一致";
  } else if (fileOk && !ansSymbol) {
    score = 1.0;
    detail = "file 一致（symbol 不問の問題）";
  } else if (fileOk) {
    score = fileOnlyPartial;
    detail = `file は正解 / symbol が未一致（部分点 ${fileOnlyPartial}）`;
  } else {
    score = 0.0;
    detail = "file が不一致";
  }

  return {
    score: clamp01(score),
    correct: clamp01(score) >= passThreshold,
    detail,
    expected: { file: ansFile, symbol: ansSymbol },
    method: "location",
    used_llm: false,
    extra: {},
  };
}

// ---- fill_blank (mirrors fill_blank.py) ----

function fold(s: string, casefold: boolean): string {
  s = String(s)
    .trim()
    .replace(/^`|`$/g, "");
  s = s.replace(/“|”/g, '"').replace(/‘|’/g, "'");
  s = s.replace(/'/g, '"');
  if (casefold) s = s.toLowerCase();
  return s;
}

export function gradeFillBlank(userAnswer: unknown, question: Question): InternalGradeResult {
  const accepted = (question.answer.accepted ?? []).map(String);
  const casefold = Boolean(question.grading.casefold);

  const u = fold(String(userAnswer ?? ""), casefold);
  const foldedAccepted = new Set(accepted.map((a) => fold(a, casefold)));
  const ok = u !== "" && foldedAccepted.has(u);

  return {
    score: ok ? 1.0 : 0.0,
    correct: ok,
    detail: ok ? "正解と一致" : "受理候補のいずれにも一致せず",
    expected: accepted,
    method: "fill_blank",
    used_llm: false,
    extra: {},
  };
}

// ---- mcq (mirrors mcq.py) ----

export function gradeMcq(userAnswer: unknown, question: Question): InternalGradeResult {
  const correctIndex =
    typeof question.answer.correct_index === "number" ? question.answer.correct_index : -1;
  let chosen: number;
  const parsed = parseInt(String(userAnswer), 10);
  chosen = isNaN(parsed) ? -1 : parsed;

  const ok = chosen === correctIndex && correctIndex >= 0;
  const options = question.answer.options ?? [];
  const expectedText =
    correctIndex >= 0 && correctIndex < options.length ? options[correctIndex] : correctIndex;

  return {
    score: ok ? 1.0 : 0.0,
    correct: ok,
    detail: ok ? "正しい選択肢" : "誤った選択肢",
    expected: { correct_index: correctIndex, text: expectedText },
    method: "mcq",
    used_llm: false,
    extra: {},
  };
}

// ---- dataflow (mirrors dataflow.py) ----

function buildAliasMap(aliases: string[][]): Record<string, string> {
  const out: Record<string, string> = {};
  for (const group of aliases) {
    if (!group.length) continue;
    const canon = symbolTail(group[0]);
    for (const member of group) {
      out[symbolTail(member)] = canon;
      out[normalizeSymbol(member)] = canon;
    }
  }
  return out;
}

function canonicalize(token: string, aliasMap: Record<string, string>): string {
  const t = symbolTail(token);
  return aliasMap[t] ?? aliasMap[normalizeSymbol(token)] ?? t;
}

function lcsLen(a: string[], b: string[]): number {
  if (!a.length || !b.length) return 0;
  const dp = Array.from({ length: a.length + 1 }, () => new Array<number>(b.length + 1).fill(0));
  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      dp[i][j] =
        a[i - 1] === b[j - 1]
          ? dp[i - 1][j - 1] + 1
          : Math.max(dp[i - 1][j], dp[i][j - 1]);
    }
  }
  return dp[a.length][b.length];
}

function splitDataflow(s: string): string[] {
  let r = s;
  for (const sep of ["→", "->", "=>", "\n", ",", "、", ">"]) {
    r = r.split(sep).join("|");
  }
  return r
    .split("|")
    .map((p) => p.trim())
    .filter(Boolean);
}

export function gradeDataflow(userAnswer: unknown, question: Question): InternalGradeResult {
  const grading = question.grading;
  const mode = grading.mode ?? "subsequence";
  const passThreshold = grading.pass_threshold ?? 0.8;
  const aliasMap = buildAliasMap(grading.aliases ?? []);

  const expected = (question.answer.sequence ?? []).map((x) => canonicalize(x, aliasMap));
  const rawList =
    typeof userAnswer === "string"
      ? splitDataflow(userAnswer)
      : Array.isArray(userAnswer)
        ? (userAnswer as unknown[]).map(String)
        : [];
  const given = rawList.map((x) => canonicalize(x, aliasMap));

  if (!expected.length) {
    return {
      score: 0,
      correct: false,
      detail: "正解列が空",
      expected: [],
      method: "dataflow",
      used_llm: false,
      extra: {},
    };
  }

  let score: number;
  let detail: string;
  if (mode === "set") {
    const es = new Set(expected);
    const gs = new Set(given);
    const inter = Array.from(es).filter((x) => gs.has(x)).length;
    const union = new Set(Array.from(es).concat(Array.from(gs))).size || 1;
    score = inter / union;
    detail = `集合一致 ${inter}/${es.size}（Jaccard ${score.toFixed(2)}）`;
  } else if (mode === "ordered") {
    const hits = expected.filter((e, i) => i < given.length && given[i] === e).length;
    score = hits / expected.length;
    detail = `完全順序一致 ${hits}/${expected.length}`;
  } else {
    const lcs = lcsLen(expected, given);
    score = lcs / expected.length;
    detail = `順序保持の共通部分列 ${lcs}/${expected.length}`;
  }

  return {
    score: clamp01(score),
    correct: clamp01(score) >= passThreshold,
    detail,
    expected: question.answer.sequence ?? [],
    method: "dataflow",
    used_llm: false,
    extra: {},
  };
}

// ---- freetext (mirrors freetext.py — LLM escalation omitted per spec) ----

function groupSatisfied(textNorm: string, group: { any_of: string[] }): boolean {
  return group.any_of.some((syn) => textNorm.includes(normalizeText(String(syn))));
}

export function gradeFreetext(userAnswer: unknown, question: Question): InternalGradeResult {
  const ans = question.answer;
  const grading = question.grading;
  const groups = ans.required_keywords ?? [];
  const forbidden = (ans.forbidden_keywords ?? []).map(String);
  const minCov = grading.min_keyword_coverage ?? 0.7;
  const forbiddenPenalty = grading.forbidden_penalty ?? 0.34;

  const textNorm = normalizeText(String(userAnswer ?? ""));
  let coverage: number;
  if (!groups.length) {
    coverage = textNorm ? 1.0 : 0.0;
  } else {
    const satisfied = groups.filter((g) => groupSatisfied(textNorm, g)).length;
    coverage = satisfied / groups.length;
  }

  const hitForbidden = forbidden.filter((f) => textNorm.includes(normalizeText(f)));
  const penalty = forbiddenPenalty * hitForbidden.length;

  let citeNote = "";
  if (grading.require_citation) {
    const cite = question.citation;
    const wantFile = normalizePath(cite.file ?? "");
    const sym = cite.symbol;
    const symName =
      sym && typeof sym === "object" && "name" in sym ? String((sym as { name: string }).name) : "";
    const wantSym = normalizeSymbol(symName);
    const ansStr = String(userAnswer ?? "");
    if (
      (wantFile && normalizePath(ansStr).includes(wantFile)) ||
      (wantSym && normalizeSymbol(ansStr).includes(wantSym))
    ) {
      coverage = Math.min(1.0, coverage + 0.15);
      citeNote = " / 出典言及ボーナス +0.15";
    }
  }

  const score = clamp01(coverage - penalty);
  let detail = `キーワード被覆 ${coverage.toFixed(2)}（しきい値 ${minCov}）`;
  if (hitForbidden.length) {
    detail += ` / 禁止語 ${JSON.stringify(hitForbidden)} 検出 -${penalty.toFixed(2)}`;
  }
  detail += citeNote;

  return {
    score,
    correct: score >= minCov,
    detail,
    expected: ans.model_answer ?? "",
    method: "freetext",
    used_llm: false,
    extra: { coverage, forbidden_hit: hitForbidden },
  };
}

// ---- dispatcher ----

export function grade(userAnswer: unknown, question: Question): InternalGradeResult {
  switch (question.type) {
    case "location":
      return gradeLocation(userAnswer, question);
    case "fill_blank":
      return gradeFillBlank(userAnswer, question);
    case "mcq":
      return gradeMcq(userAnswer, question);
    case "dataflow":
      return gradeDataflow(userAnswer, question);
    case "freetext":
      return gradeFreetext(userAnswer, question);
    default:
      return {
        score: 0,
        correct: false,
        detail: "unknown type",
        expected: null,
        method: "none",
        used_llm: false,
        extra: {},
      };
  }
}
