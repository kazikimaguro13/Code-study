"use client";

import { useEffect, useState } from "react";
import { api, type Overview } from "@/lib/api";

function Bar({ value, color }: { value: number; color: string }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded bg-slate-100">
      <div className={`h-full ${color}`} style={{ width: `${Math.round(value * 100)}%` }} />
    </div>
  );
}

export default function Dashboard() {
  const [ov, setOv] = useState<Overview | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.overview().then(setOv).catch((e) => setError(String(e)));
  }, []);

  if (error)
    return <p className="text-sm text-red-700">バックエンドに接続できません（{error}）。</p>;
  if (!ov) return <p className="text-slate-500">読み込み中…</p>;

  const modules = Object.entries(ov.modules).sort((a, b) => a[1].mastery - b[1].mastery);

  return (
    <div>
      <h1 className="mb-4 text-xl font-bold">ダッシュボード</h1>

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="総問題数" value={String(ov.total_questions)} />
        <Stat label="総回答数" value={String(ov.attempts)} />
        <Stat label="復習待ち" value={String(ov.due_count)} />
        <Stat label="総合習得度" value={`${Math.round(ov.overall_mastery * 100)}%`} />
      </div>

      <h2 className="mb-2 text-sm font-semibold text-slate-600">モジュール別 習得度 / カバレッジ（弱点順）</h2>
      <div className="space-y-3">
        {modules.map(([name, m]) => (
          <div key={name} className="rounded-lg border bg-white p-3">
            <div className="mb-1 flex items-center justify-between text-sm">
              <span className="font-mono text-xs text-slate-600">{name}</span>
              <span className="text-slate-500">
                習得 {Math.round(m.mastery * 100)}% / 着手 {m.attempted}/{m.total}
              </span>
            </div>
            <Bar value={m.mastery} color="bg-accent" />
            <div className="mt-1">
              <Bar value={m.coverage} color="bg-emerald-400" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border bg-white p-3">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}
