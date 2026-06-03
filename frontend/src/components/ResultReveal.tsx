"use client";

import type { GradeResult } from "@/lib/api";

export function ResultReveal({ result, onNext }: { result: GradeResult; onNext: () => void }) {
  const pct = Math.round(result.score * 100);
  return (
    <div
      className={`mt-4 rounded-xl border p-5 ${
        result.correct ? "border-green-300 bg-green-50" : "border-amber-300 bg-amber-50"
      }`}
    >
      <div className="flex items-center gap-3">
        <span className={`text-lg font-bold ${result.correct ? "text-green-700" : "text-amber-700"}`}>
          {result.correct ? "正解" : "おしい / 不正解"}
        </span>
        <span className="text-sm text-slate-600">スコア {pct}%</span>
        {result.used_llm && <span className="text-xs text-slate-400">(LLM採点)</span>}
      </div>

      <p className="mt-1 text-sm text-slate-600">{result.detail}</p>

      {result.expected != null && (
        <p className="mt-2 text-sm">
          <span className="font-medium">正解: </span>
          <span className="font-mono">{JSON.stringify(result.expected)}</span>
        </p>
      )}

      {result.explanation && <p className="mt-2 text-sm leading-relaxed">{result.explanation}</p>}

      {result.citation?.snippet && (
        <div className="mt-3">
          <div className="mb-1 text-xs text-slate-500">
            出典: <span className="font-mono">{result.citation.file}</span>
            {result.citation.adr_ref && <span className="ml-2 text-accent">{result.citation.adr_ref}</span>}
          </div>
          <pre className="overflow-x-auto rounded bg-slate-900 p-3 text-xs text-slate-100">
            {result.citation.snippet}
          </pre>
        </div>
      )}

      <div className="mt-4 flex items-center gap-3 text-sm">
        <button className="rounded-lg bg-accent px-4 py-2 font-medium text-white" onClick={onNext}>
          次の問題へ
        </button>
        {result.next_due && <span className="text-slate-500">次回復習: {result.next_due}</span>}
      </div>
    </div>
  );
}
