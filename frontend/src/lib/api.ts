// API client for the FastAPI quiz backend. Types mirror backend/src/schemas.py.

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export type QType = "location" | "fill_blank" | "mcq" | "dataflow" | "freetext";

export interface QuestionView {
  id: string;
  type: QType;
  difficulty: string | null;
  module: string | null;
  tags: string[];
  prompt: string;
  options?: string[] | null;
  pool?: string[] | null;
}

export interface CitationView {
  file: string | null;
  symbol: unknown;
  adr_ref: string | null;
  snippet: string | null;
}

export interface GradeResult {
  q_id: string;
  score: number;
  correct: boolean;
  detail: string;
  expected: unknown;
  method: string;
  used_llm: boolean;
  explanation: string;
  citation: CitationView;
  next_due: string | null;
  correct_streak: number | null;
}

export interface ModuleStat {
  total: number;
  attempted: number;
  coverage: number;
  mastery: number;
}

export interface Overview {
  total_questions: number;
  attempts: number;
  due_count: number;
  overall_mastery: number;
  modules: Record<string, ModuleStat>;
  meta: Record<string, unknown>;
}

async function jsonFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status} ${await res.text()}`);
  return (await res.json()) as T;
}

export const api = {
  health: () => jsonFetch<{ status: string; questions: number }>("/api/health"),
  next: (n = 10, module?: string) =>
    jsonFetch<{ questions: QuestionView[] }>("/api/quiz/next", {
      method: "POST",
      body: JSON.stringify({ n, module: module ?? null }),
    }),
  grade: (q_id: string, answer: unknown) =>
    jsonFetch<GradeResult>("/api/quiz/grade", {
      method: "POST",
      body: JSON.stringify({ q_id, answer }),
    }),
  overview: () => jsonFetch<Overview>("/api/quiz/overview"),
};
