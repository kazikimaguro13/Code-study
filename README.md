# axis-code-quiz (Code-study)

`axis-knowledge-rag` のコードを「どこに・どう・なぜ」実装されているかを、出題で能動的に理解するための**常設コード学習ツール**。

問題は axis のソース＋ADR/spec を根拠に **citation-first**（出典先付け）で作られ、採点は**可能な限り非AI（決定的・ルールベース）**。APIキー無しで完結して動きます。間隔反復（SM-2 lite）で習得度を継続トラッキングします。

> 設計の全体像は [`../axis-knowledge-rag/axis-code-quiz_design.md`](../axis-knowledge-rag/axis-code-quiz_design.md) を参照。

---

## 構成

```
Code-study/
  backend/          # FastAPI + 採点ロジック（Python, 依存は fastapi/uvicorn/pydantic のみ）
    src/
      grading/      # 形式別グレーダ（location/fill_blank/mcq/dataflow/freetext）+ normalize
      store/        # quiz_bank ローダ / progress(sqlite, SM-2 lite)
      anchor/       # シンボル→現HEAD行範囲の解決（鮮度検証 / 将来機能）
      service.py    # 出題選択（due優先→弱点モジュール）・採点・集計
      main.py       # API: /api/quiz/{next,grade,overview}
    tests/          # 決定的グレーダ + SM-2 + service のテスト
  frontend/         # Next.js 14 (App Router) — axis と同構成
    src/app/        # 出題 / review / dashboard
    src/lib/api.ts  # 型付き APIクライアント
  data/
    quiz_bank.json  # 生成済みの問題バンク（51問, repo_commit 紐付け）
    progress.db     # 学習履歴（自動生成, git管理外）
  scripts/
    build_bank.py   # 問題バンク生成（Claude起草の問題を直列化）
    validate_bank.py# 品質ゲート: evidence_substring がsnippetに実在するか等を検証
```

## 採点方針（非AI）

| 形式 | 採点 | AI |
|---|---|---|
| location（場所当て） | ファイル/シンボル一致・別名許容・部分点 | 不要 |
| fill_blank（穴埋め） | 正規化後の文字列照合 | 不要 |
| mcq（選択式 / L4設計意図含む） | index一致 | 不要 |
| dataflow（データフロー） | 順序の部分列一致(LCS)・別名・集合モード | 不要 |
| freetext（記述） | キーワード被覆(any_ofグループ)＋禁止語＋出典照合 | 任意エスカレーションのみ |

`freetext` の意味採点だけ本質的に難しいため、既定はキーワード被覆で近似し、`llm_escalation` を設定すると灰色ゾーンだけ LLM 判定に回せます（既定 off でも完全動作）。

## 起動

```bash
# 1) バックエンド（ポート8000）
cd Code-study
pip install -r backend/requirements.txt
uvicorn backend.src.main:app --reload     # http://localhost:8000/docs

# 2) フロントエンド（ポート3000）
cd frontend
npm install
npm run dev                                # http://localhost:3000
```

API キーは不要です。`data/quiz_bank.json` を読み込んで即出題できます。

## 問題バンクの再生成・検証

```bash
python scripts/build_bank.py      # data/quiz_bank.json を生成
python scripts/validate_bank.py   # 品質ゲート（evidence照合・スキーマ検証）
```

MVP では問題は **Claude（Cowork チャット）が起草** → `build_bank.py` で直列化 → `validate_bank.py` で機械検証、という流れ。将来は同じ JSON スキーマのまま Gemini API 版ジェネレータに差し替えてコミット連動の自動再生成へ拡張できます（採点・UI は無改変）。

## 難易度

L1 場所当て / L2 役割・振る舞い / L3 データフロー / L4 設計意図（ADR/spec 起点）。

## ステータス

MVP（フェーズ1〜3前倒し）: 決定的採点・51問・FastAPI・Next.js UI（出題/復習/ダッシュボード）・SM-2 lite。
今後: TS/MCP対応の出題拡充、コミット連動の自動再生成、axis MCP を使った「どこ？」ヒント、freetext の LLM 任意採点。
