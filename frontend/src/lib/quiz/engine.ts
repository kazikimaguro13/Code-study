// Client-side quiz engine. Mirrors backend/src/service.py (QuizService).
// quiz_bank.json is bundled at build time — no server required.

import quizBankRaw from "../../../../data/quiz_bank.json";
import * as graders from "./graders";
import * as progress from "../progress";
import type {
  Question,
  QuestionView,
  GradeResult,
  Overview,
  CitationView,
  ModuleStat,
} from "./types";

interface QuizBankJson {
  meta: Record<string, unknown>;
  questions: Question[];
}

const bank = quizBankRaw as unknown as QuizBankJson;
const allQuestions: Question[] = bank.questions;
const questionMap = new Map<string, Question>(allQuestions.map((q) => [q.id, q]));

function shuffle<T>(arr: T[]): T[] {
  const r = [...arr];
  for (let i = r.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [r[i], r[j]] = [r[j], r[i]];
  }
  return r;
}

export function nextQuestions(n = 10, module?: string): { questions: QuestionView[] } {
  const pool = module ? allQuestions.filter((q) => q.module === module) : allQuestions;
  const poolIdSet = new Set(pool.map((q) => q.id));

  const due = progress.dueQuestionIds().filter((id) => poolIdSet.has(id));
  const seen = progress.seenIds();

  const chosen: string[] = [];
  for (const qid of due) {
    if (chosen.length >= n) break;
    chosen.push(qid);
  }

  if (chosen.length < n) {
    const chosenSet = new Set(chosen);
    let unseen = shuffle(pool.filter((q) => !seen.has(q.id) && !chosenSet.has(q.id)));
    const mm = moduleMastery();

    unseen.sort((a, b) => {
      const wA = 1.0 - (mm[a.module ?? ""]?.mastery ?? 0) + 0.05;
      const wB = 1.0 - (mm[b.module ?? ""]?.mastery ?? 0) + 0.05;
      return wB - wA;
    });

    for (const q of unseen) {
      if (chosen.length >= n) break;
      chosen.push(q.id);
    }
  }

  if (chosen.length < n) {
    const chosenSet = new Set(chosen);
    const remaining = pool
      .filter((q) => !chosenSet.has(q.id))
      .sort((a, b) => progress.questionMastery(a.id) - progress.questionMastery(b.id));
    chosen.push(...remaining.slice(0, n - chosen.length).map((q) => q.id));
  }

  const questions = chosen
    .map((id) => questionMap.get(id))
    .filter((q): q is Question => q !== undefined)
    .map(toPublicView);

  return { questions };
}

function toPublicView(q: Question): QuestionView {
  return {
    id: q.id,
    type: q.type,
    difficulty: q.difficulty,
    module: q.module,
    tags: q.tags,
    prompt: q.prompt,
    options: q.answer.options ?? null,
    pool: q.pool ?? null,
  };
}

export function grade(q_id: string, userAnswer: unknown): GradeResult {
  const q = questionMap.get(q_id);
  if (!q) throw new Error(`unknown question id: ${q_id}`);

  const result = graders.grade(userAnswer, q);
  const srs = progress.recordAttempt(q_id, result.score, result.correct);

  const cite = q.citation;
  const hasSource = Boolean(cite.source);

  const citationView: CitationView = {
    file: cite.file,
    symbol: cite.symbol,
    adr_ref: cite.adr_ref,
    snippet: cite.snippet,
    source: cite.source ?? null,
    resolved: hasSource,
    start_line: cite.start_line ?? null,
    end_line: cite.end_line ?? null,
  };

  return {
    q_id,
    score: result.score,
    correct: result.correct,
    detail: result.detail,
    expected: result.expected,
    method: result.method,
    used_llm: result.used_llm,
    explanation: q.explanation,
    citation: citationView,
    next_due: srs.due_date,
    correct_streak: srs.correct_streak,
  };
}

export function moduleMastery(): Record<string, ModuleStat> {
  const seen = progress.seenIds();
  const counts: Record<string, Question[]> = {};
  for (const q of allQuestions) {
    const m = q.module ?? "";
    (counts[m] ??= []).push(q);
  }

  const out: Record<string, ModuleStat> = {};
  for (const [mod, qs] of Object.entries(counts)) {
    const total = qs.length;
    const attempted = qs.filter((q) => seen.has(q.id)).length;
    const masteries = qs.map((q) => progress.questionMastery(q.id));
    out[mod] = {
      total,
      attempted,
      coverage: total ? Math.round((attempted / total) * 1000) / 1000 : 0,
      mastery:
        total ? Math.round((masteries.reduce((a, b) => a + b, 0) / total) * 1000) / 1000 : 0,
    };
  }
  return out;
}

export function overview(): Overview {
  const mm = moduleMastery();
  const totalQ = allQuestions.length;
  const vals = Object.values(mm);
  const overallMastery = totalQ
    ? Math.round(
        (vals.reduce((acc, m) => acc + m.mastery * m.total, 0) / totalQ) * 1000,
      ) / 1000
    : 0;

  return {
    total_questions: totalQ,
    attempts: progress.attemptCount(),
    due_count: progress.dueQuestionIds().length,
    overall_mastery: overallMastery,
    modules: mm,
    meta: bank.meta,
  };
}
