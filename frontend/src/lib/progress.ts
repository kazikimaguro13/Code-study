// localStorage-backed progress store. Mirrors backend/src/store/progress.py (ProgressStore).
// SSR guard: all reads/writes check typeof window !== 'undefined'.

import { schedule, type SrsState } from "./quiz/srs";

const STORAGE_KEY = "code-study:v1:progress";

interface AttemptRecord {
  q_id: string;
  ts: string;
  score: number;
  correct: boolean;
}

interface ProgressData {
  srs: Record<string, SrsState>;
  attempts: AttemptRecord[];
}

function load(): ProgressData {
  if (typeof window === "undefined") return { srs: {}, attempts: [] };
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { srs: {}, attempts: [] };
    return JSON.parse(raw) as ProgressData;
  } catch {
    return { srs: {}, attempts: [] };
  }
}

function save(data: ProgressData): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

export function recordAttempt(qId: string, score: number, correct: boolean): SrsState {
  const data = load();
  data.attempts.push({ q_id: qId, ts: new Date().toISOString(), score, correct });
  const current = data.srs[qId] ?? null;
  const next = schedule(current, score, correct);
  next.q_id = qId;
  data.srs[qId] = next;
  save(data);
  return next;
}

export function srsState(qId: string): SrsState | null {
  return load().srs[qId] ?? null;
}

export function dueQuestionIds(): string[] {
  const today = new Date().toISOString().slice(0, 10);
  return Object.values(load().srs)
    .filter((s) => s.due_date <= today)
    .sort((a, b) => a.due_date.localeCompare(b.due_date))
    .map((s) => s.q_id);
}

export function seenIds(): Set<string> {
  return new Set(Object.keys(load().srs));
}

export function questionMastery(qId: string): number {
  const s = load().srs[qId];
  if (!s) return 0;
  const streakFactor = Math.min(1.0, s.correct_streak / 3.0);
  return Math.round((0.5 * streakFactor + 0.5 * s.last_score) * 1000) / 1000;
}

export function attemptCount(): number {
  return load().attempts.length;
}
