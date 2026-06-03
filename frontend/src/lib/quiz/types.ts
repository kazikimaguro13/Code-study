// Shared types for the client-side quiz engine.
// Mirrors backend/src/schemas.py and quiz_bank.json structure.

export type QType = "location" | "fill_blank" | "mcq" | "dataflow" | "freetext";

export interface CitationSymbol {
  kind: string;
  name: string;
}

export interface Citation {
  file: string | null;
  symbol: CitationSymbol | { kind?: string; name?: string } | null;
  evidence_substring?: string;
  adr_ref: string | null;
  snippet: string | null;
  // Embedded by scripts/build_bank.py (spec_001)
  source?: string | null;
  start_line?: number | null;
  end_line?: number | null;
}

export interface QuestionAnswer {
  file?: string;
  symbol?: string;
  accepted?: string[];
  options?: string[];
  correct_index?: number;
  sequence?: string[];
  required_keywords?: Array<{ any_of: string[] }>;
  forbidden_keywords?: string[];
  model_answer?: string;
}

export interface QuestionGrading {
  symbol_aliases?: string[];
  accept_file_only_partial?: number;
  pass_threshold?: number;
  casefold?: boolean;
  mode?: "set" | "subsequence" | "ordered";
  aliases?: string[][];
  min_keyword_coverage?: number;
  forbidden_penalty?: number;
  require_citation?: boolean;
}

export interface Question {
  id: string;
  difficulty: string | null;
  type: QType;
  module: string | null;
  tags: string[];
  prompt: string;
  citation: Citation;
  answer: QuestionAnswer;
  grading: QuestionGrading;
  explanation: string;
  pool?: string[];
}

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
  source: string | null;
  resolved: boolean;
  start_line: number | null;
  end_line: number | null;
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
