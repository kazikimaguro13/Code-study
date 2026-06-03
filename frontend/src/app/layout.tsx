import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "axis-code-quiz",
  description: "axis-knowledge-rag のコード理解クイズ",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>
        <header className="border-b bg-white">
          <nav className="mx-auto flex max-w-3xl items-center gap-6 px-4 py-3">
            <Link href="/" className="font-bold text-accent">axis-code-quiz</Link>
            <Link href="/" className="text-sm text-slate-600 hover:text-ink">出題</Link>
            <Link href="/review" className="text-sm text-slate-600 hover:text-ink">復習</Link>
            <Link href="/dashboard" className="text-sm text-slate-600 hover:text-ink">ダッシュボード</Link>
            <Link href="/glossary" className="text-sm text-slate-600 hover:text-ink">用語集</Link>
          </nav>
        </header>
        <main className="mx-auto max-w-3xl px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
