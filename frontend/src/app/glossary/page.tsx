"use client";
import { useMemo, useState } from "react";
import { GLOSSARY } from "@/lib/glossary";

export default function GlossaryPage() {
  const [q, setQ] = useState("");
  const filtered = useMemo(() => {
    const k = q.trim().toLowerCase();
    if (!k) return GLOSSARY;
    return GLOSSARY.filter((e) =>
      [e.term, e.definition, e.axisNote ?? "", ...(e.aliases ?? [])].join(" ").toLowerCase().includes(k),
    );
  }, [q]);
  return (
    <div>
      <h1 className="mb-1 text-xl font-bold">用語集</h1>
      <p className="mb-4 text-sm text-slate-500">このクイズ／axis に出てくる専門用語を平易に。問題の解説からもここへ飛べます。</p>
      <input className="mb-5 w-full rounded-lg border px-3 py-2 text-sm" placeholder="絞り込み（例: BM25, 正規化, グラフ）" value={q} onChange={(e) => setQ(e.target.value)} />
      <div className="space-y-3">
        {filtered.map((e) => (
          <div key={e.id} id={e.id} className="scroll-mt-20 rounded-lg border bg-white p-4 target:ring-2 target:ring-accent">
            <div className="flex flex-wrap items-baseline gap-2">
              <h2 className="font-bold">{e.term}</h2>
              {e.reading && <span className="text-xs text-slate-400">{e.reading}</span>}
            </div>
            <p className="mt-1 text-sm leading-relaxed text-slate-700">{e.definition}</p>
            {e.axisNote && (<p className="mt-1 text-xs text-slate-500"><span className="font-medium">axis での実装: </span>{e.axisNote}</p>)}
          </div>
        ))}
        {filtered.length === 0 && <p className="text-sm text-slate-500">該当する用語がありません。</p>}
      </div>
    </div>
  );
}
