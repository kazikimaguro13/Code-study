"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type GradeResult, type QuestionView } from "@/lib/api";
import { QuestionCard } from "./QuestionCard";
import { ResultReveal } from "./ResultReveal";

export function QuizRunner({ title, sessionSize = 8 }: { title: string; sessionSize?: number }) {
  const [queue, setQueue] = useState<QuestionView[]>([]);
  const [idx, setIdx] = useState(0);
  const [result, setResult] = useState<GradeResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [done, setDone] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await api.next(sessionSize);
      setQueue(r.questions);
      setIdx(0);
      setResult(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [sessionSize]);

  useEffect(() => {
    load();
  }, [load]);

  async function submit(answer: unknown) {
    const q = queue[idx];
    if (!q) return;
    try {
      const r = await api.grade(q.id, answer);
      setResult(r);
      setDone((d) => d + 1);
    } catch (e) {
      setError(String(e));
    }
  }

  function next() {
    setResult(null);
    if (idx + 1 < queue.length) setIdx(idx + 1);
    else load();
  }

  if (loading) return <p className="text-slate-500">読み込み中…</p>;
  if (error)
    return (
      <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-700">
        バックエンドに接続できません（{error}）。FastAPI を起動してください:
        <pre className="mt-2 text-xs">uvicorn backend.src.main:app --reload</pre>
      </div>
    );
  if (queue.length === 0) return <p className="text-slate-500">出題できる問題がありません。</p>;

  const q = queue[idx];
  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">{title}</h1>
        <span className="text-sm text-slate-500">
          {idx + 1} / {queue.length}（今回 {done} 問回答）
        </span>
      </div>
      <QuestionCard q={q} disabled={result !== null} onSubmit={submit} />
      {result && <ResultReveal result={result} prompt={q.prompt} onNext={next} />}
    </div>
  );
}
