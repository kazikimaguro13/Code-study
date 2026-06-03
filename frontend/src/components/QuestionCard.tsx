"use client";

import { useState } from "react";
import type { QuestionView } from "@/lib/api";

const DIFF_LABEL: Record<string, string> = {
  L1: "L1 場所当て",
  L2: "L2 役割・振る舞い",
  L3: "L3 データフロー",
  L4: "L4 設計意図",
};

export function QuestionCard({
  q,
  disabled,
  onSubmit,
}: {
  q: QuestionView;
  disabled: boolean;
  onSubmit: (answer: unknown) => void;
}) {
  const [file, setFile] = useState("");
  const [symbol, setSymbol] = useState("");
  const [text, setText] = useState("");
  const [choice, setChoice] = useState<number | null>(null);

  function buildAnswer(): unknown {
    switch (q.type) {
      case "location":
        return { file, symbol };
      case "mcq":
        return choice;
      case "dataflow":
        return text; // comma / arrow separated; backend splits + alias-maps
      default:
        return text; // fill_blank, freetext
    }
  }

  const canSubmit =
    q.type === "mcq" ? choice !== null : q.type === "location" ? file.trim() !== "" : text.trim() !== "";

  return (
    <div className="rounded-xl border bg-white p-5 shadow-sm">
      <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
        <span className="rounded bg-accent/10 px-2 py-0.5 font-medium text-accent">
          {DIFF_LABEL[q.difficulty ?? ""] ?? q.difficulty}
        </span>
        <span className="rounded bg-slate-100 px-2 py-0.5 text-slate-600">{q.type}</span>
        {q.module && <span className="font-mono text-slate-400">{q.module}</span>}
      </div>

      <p className="mb-4 whitespace-pre-wrap text-[15px] font-medium leading-relaxed">{q.prompt}</p>

      {q.type === "location" && (
        <div className="space-y-2">
          <input
            className="w-full rounded border px-3 py-2 font-mono text-sm"
            placeholder="ファイル (例: backend/src/search.py)"
            value={file}
            onChange={(e) => setFile(e.target.value)}
            disabled={disabled}
          />
          <input
            className="w-full rounded border px-3 py-2 font-mono text-sm"
            placeholder="シンボル (例: SearchEngine.search) — 任意"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            disabled={disabled}
          />
        </div>
      )}

      {q.type === "mcq" && (
        <div className="space-y-2">
          {(q.options ?? []).map((opt, i) => (
            <label
              key={i}
              className={`flex cursor-pointer items-start gap-2 rounded border px-3 py-2 text-sm ${
                choice === i ? "border-accent bg-accent/5" : "border-slate-200"
              }`}
            >
              <input
                type="radio"
                name={q.id}
                checked={choice === i}
                onChange={() => setChoice(i)}
                disabled={disabled}
                className="mt-1"
              />
              <span>{opt}</span>
            </label>
          ))}
        </div>
      )}

      {(q.type === "fill_blank" || q.type === "freetext" || q.type === "dataflow") && (
        <textarea
          className="w-full rounded border px-3 py-2 font-mono text-sm"
          rows={q.type === "freetext" ? 4 : 2}
          placeholder={
            q.type === "dataflow"
              ? "ステップを順に（例: normalizer → embedder → ...）"
              : q.type === "fill_blank"
                ? "空欄に入る語"
                : "説明を記述"
          }
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={disabled}
        />
      )}

      <button
        className="mt-4 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
        disabled={disabled || !canSubmit}
        onClick={() => onSubmit(buildAnswer())}
      >
        回答する
      </button>
    </div>
  );
}
