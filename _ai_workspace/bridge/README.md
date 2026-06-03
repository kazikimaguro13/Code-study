# bridge — Cowork × Claude Code 連携運用（Code-study）

このフォルダは **Cowork（戦略・spec起草・レビュー）と Claude Code（実装・push・重作業）の仕様書/結果のやりとり場所**。axis-knowledge-rag と同じ流儀。

## レイアウト

```
_ai_workspace/bridge/
├── README.md          ← この文書
├── dispatch.sh        ← CC に spec を投げる helper（既定 dev-b）
├── templates/
│   ├── spec_template.md
│   └── result_template.md
├── inbox/             ← Cowork が書く spec_NNN.md（CC が読む）
│   └── INDEX.md       ← 進捗一覧
├── outbox/            ← CC が書く result_NNN.md（Cowork が読む）
└── archive/           ← 完了ペアを日付フォルダへ
```

## 二拠点構成（重要）

- **Desktop コピー** `C:\Users\cocor\Desktop\就活\Code-study`（Cowork がマウントで編集／spec起草）
- **WSL クローン** `~/projects/Code-study`（CC の開発本拠地／dispatch 実行）
- 同期は **GitHub 経由**（`kazikimaguro13/Code-study`）。Cowork が spec を push → WSL で `git pull` → CC が実装 → push → Cowork が pull/レビュー。

## 運用ルーチン

1. **spec 起草（Cowork → inbox）**: `templates/spec_template.md` を雛形に、触ってよいファイル・成功条件・出力先を明示。`inbox/INDEX.md` に1行追記。push。
2. **dispatch（WSL）**: `cd ~/projects/Code-study && git pull && bash _ai_workspace/bridge/dispatch.sh 001`
   - alias 切替: `... dispatch.sh 001 a`（dev-b が上限の時 dev-a 等）
3. **レビュー（Cowork ← outbox）**: `outbox/result_NNN.md` を読み、次を設計。

## 命名規則

- `spec_001.md`, `spec_002.md` … 連番3桁。結果は同番号 `result_001.md`。
- アーカイブは `archive/YYYY-MM-DD/` にペアで移動。

## Cowork 直接 vs CC dispatch の判断

- 1〜2ファイル / 〜30行、動作確認・デバッグ、フロントのローカル開発、**クイズ問題の著作（axisソースを読む判断）** → Cowork 直接
- 5+ファイル / 100+行、git push/deploy、既存バックエンド改修、大規模リファクタ → CC に dispatch
