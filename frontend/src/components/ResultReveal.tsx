"use client";

import Link from "next/link";
import type { CitationView, GradeResult } from "@/lib/api";
import { findTerms } from "@/lib/glossary";

function TermNotes({ text }: { text: string }) {
  const terms = findTerms(text);
  if (terms.length === 0) return null;
  return (
    <div className="mt-3 rounded-lg border border-slate-200 bg-white p-3">
      <div className="mb-1 text-xs font-semibold text-slate-500">🔖 この問題に出てくる用語</div>
      <ul className="space-y-1.5">
        {terms.map((t) => (
          <li key={t.id} className="text-sm leading-relaxed">
            <Link href={`/glossary#${t.id}`} className="font-medium text-accent">{t.term}</Link>
            <span className="text-slate-700">：{t.definition}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function CodeReveal({ citation }: { citation: CitationView }) {
  const real = Boolean(citation.resolved && citation.source);
  const code = real ? citation.source : citation.snippet;
  if (!code && !citation.file) return null;
  const startLine = citation.start_line ?? 1;
  const lines = (code ?? "").split("\n");
  return (
    <div className="mt-3">
      <div className="mb-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
        <span>{real ? "実際のコード" : "該当箇所（抜粋）"}:</span>
        <span className="font-mono text-slate-700">{citation.file}</span>
        {real && citation.start_line != null && (
          <span className="text-slate-400">
            L{citation.start_line}
            {citation.end_line != null && citation.end_line !== citation.start_line ? `–${citation.end_line}` : ""}
          </span>
        )}
        {citation.adr_ref && <span className="text-accent">{citation.adr_ref}</span>}
      </div>
      {code && real && (
        <pre className="max-h-96 overflow-auto rounded bg-slate-900 p-3 text-xs leading-relaxed text-slate-100">
          {lines.map((ln, i) => (
            <div key={i} className="flex">
              <span className="mr-3 inline-block w-8 shrink-0 select-none text-right text-slate-500">{startLine + i}</span>
              <span className="whitespace-pre">{ln || " "}</span>
            </div>
          ))}
        </pre>
      )}
      {code && !real && (
        <pre className="max-h-96 overflow-auto whitespace-pre-wrap break-words rounded bg-slate-900 p-3 text-xs leading-relaxed text-slate-100">
          {code}
        </pre>
      )}
      {!real && (
        <p className="mt-1 text-[11px] text-slate-400">
          ※ 全文は {citation.file} を参照（axis リポジトリが隣接フォルダにあれば実コードを自動表示します）
        </p>
      )}
    </div>
  );
}

export function ResultReveal({ result, prompt = "", onNext }: { result: GradeResult; prompt?: string; onNext: () => void }) {
  const pct = Math.round(result.score * 100);
  return (
    <div className={`mt-4 rounded-xl border p-5 ${result.correct ? "border-green-300 bg-green-50" : "border-amber-300 bg-amber-50"}`}>
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
      <CodeReveal citation={result.citation} />
      <TermNotes text={`${prompt} ${result.explanation ?? ""}`} />
      <div className="mt-4 flex items-center gap-3 text-sm">
        <button className="rounded-lg bg-accent px-4 py-2 font-medium text-white" onClick={onNext}>次の問題へ</button>
        {result.next_due && <span className="text-slate-500">次回復習: {result.next_due}</span>}
      </div>
    </div>
  );
}
