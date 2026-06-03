# spec_001: 採点ロジックTS移植＋Next.js static export＋Vercel自動デプロイ（完全静的化）

- **Author**: Cowork
- **Created**: 2026-06-03
- **Target**: Claude Code (`dev-b`)
- **Project**: `~/projects/Code-study`
- **Status**: pending
- **Bundles**: なし（P1の基盤。後続の P2＝問題拡充とスキーマ非衝突であること）

## 1. 目的

現状、本ツールは **FastAPI(8000) ＋ Next.js(3000) の2プロセス**で動き、使うたびに `uvicorn` と `npm run dev` をシェルで立てる必要がある。ユーザーのゴールは「**シェルを開かずブラウザURLだけで使える常設ツール**」。

採点は完全に決定的（秘密情報・重い計算なし）、quiz_bank は静的データ、進捗は単一ユーザーのもの。よってサーバーは本質的に不要。**採点・出題選択・進捗・実コード表示をすべてブラウザ内で完結させ、Next.js を static export して Vercel に自動デプロイする**。

```
[現状] Next.js(3000) --fetch--> FastAPI(8000) [採点/出題/進捗/実コード解決] + quiz_bank.json + progress.db(sqlite) + axisローカル読取
[変更後] 完全静的 Next.js（採点/出題/進捗をTSでブラウザ内実行、進捗=localStorage、実コードは生成時にquiz_bank.jsonへ埋め込み済み）→ Vercelにpushで自動公開。FastAPIはランタイム不要に。
```

Python バックエンド（`backend/`）と生成・検証スクリプト（`scripts/`）は **ビルド／開発ツールとして残す**（退役させない）。本番ランタイムは純静的フロントのみ。

## 2. 制約

### 触ってよい / 新規作成
- `frontend/src/lib/quiz/` （新規ディレクトリ）— 採点・SM-2・出題選択・型を TS で実装（`backend/src/grading/` と `store/progress.py`・`service.py` のミラー）。
- `frontend/src/lib/progress.ts` （新規）— localStorage 永続化。
- `frontend/src/components/QuizRunner.tsx`・`app/dashboard/page.tsx` — `lib/api.ts` の fetch をローカルエンジン呼び出しに置換。
- `frontend/next.config.mjs` — `output: 'export'` 追加。
- `frontend/src/lib/api.ts` — 削除 or 未使用化（型は `lib/quiz/types.ts` へ移す）。
- `scripts/build_bank.py` — 各 citation に**実コード全文＋行範囲を埋め込む**よう拡張（後述 3-4）。`scripts/validate_bank.py` — 追加フィールドの検証を足す。
- `data/quiz_bank.json` — build_bank 再生成で更新（埋め込み版）。
- デプロイ設定：`vercel.json`（必要なら）、`frontend/.gitignore`（`/out` 追加）、`README.md` 更新。
- TS パリティテスト：`frontend/src/lib/quiz/__tests__/`（vitest など軽量で）。

### 触ってはいけない / 維持
- **`data/quiz_bank.json` の「問題」スキーマは変更禁止**（id/type/difficulty/module/prompt/answer/grading/citation/explanation の構造）。**追加してよいのは citation 内の `source` / `start_line` / `end_line` と meta の `axis_commit` のみ**。理由：後続 P2（問題大量追加）が同スキーマ前提で並行進行するため、構造変更は衝突する。
- `backend/`（Python採点）は**消さない**。TS はこれを仕様として移植し、両者一致を担保。
- 既存の採点仕様（部分点・別名・しきい値・freetextキーワード被覆）を変えない。挙動互換。

### コーディングルール
- TS グレーダは `backend/src/grading/*.py` の関数と1対1対応させ、同じ入出力・同じしきい値。
- 新規ライブラリは最小限（テストに vitest 程度は可）。`package.json` 更新。
- localStorage キーは `code-study:v1:progress` のように versioned に。

### デプロイ
- `git push origin main`（dev-b / GitHub: kazikimaguro13）。
- Vercel の初回 import/deploy は**ユーザーが手動**（3クリック）。CC はリポジトリ側の設定（`output:'export'` 等）を整え、`next build` がローカルで通ることまで担保。Vercelアカウント作業はやらない/やれない。

## 3. やってほしいこと

### 3-1. TS 採点エンジン（`frontend/src/lib/quiz/`）
`backend/src/grading/` を移植。ファイル構成案：
- `types.ts` — Question / Citation / GradeResult 型（`backend/src/schemas.py`・quiz_bank の構造に一致）。
- `normalize.ts` — `normalize_text`（NFKC＋カナ→ひらがな＋lower＋空白畳み）/ `normalizePath` / `normalizeSymbol` / `symbolTail`。`backend/src/grading/normalize.py` を忠実移植。
- `graders.ts` — `gradeLocation` / `gradeFillBlank` / `gradeMcq` / `gradeDataflow`（LCS部分点・set/subsequence/ordered）/ `gradeFreetext`（any_ofグループ被覆＋禁止語＋出典加点）。freetext の LLM エスカレーションは**入れない**（静的方針）。`min_keyword_coverage` 等は quiz_bank の grading から読む。
- `srs.ts` — SM-2 lite（`store/progress.py` の `_schedule` 移植：正解 interval 1→3→×ease、ease上限2.7／誤答 reset・ease-0.2・floor1.3、due_date計算）。
- `engine.ts` — 出題選択（due優先→未出題を弱点モジュール重み付け→端数は低マスタリ補充）＋ `module_mastery`／`overview`（`service.py` 移植）。quiz_bank は静的 import。
- `__tests__/` — `backend/tests/test_graders.py`・`test_progress_service.py` の各ケースを TS へ移植（パリティの最低保証）。

### 3-2. 進捗（`frontend/src/lib/progress.ts`）
localStorage に SRS 状態と attempts を保存（`store/progress.py` のテーブル相当を JSON で）。SSR 回避のため `typeof window !== 'undefined'` ガード。API：`recordAttempt(qId, score, correct)` / `srsState(qId)` / `dueQuestionIds()` / `seenIds()` / `questionMastery(qId)` / `attemptCount()`。

### 3-3. UI 配線
- `QuizRunner.tsx`：`api.next()` → `engine.nextQuestions(n)`、`api.grade()` → `engine.grade(qId, answer)`（同期 or Promise.resolve）。エラー時の「バックエンドに接続できません」分岐は不要に。
- `dashboard/page.tsx`：`api.overview()` → `engine.overview()`。
- `ResultReveal` / `QuestionCard` / `glossary` は表示はそのまま。`ResultReveal` の実コード表示は `citation.source`（埋め込み済み）を使う（既にフォールバック実装あり）。
- **注意**：静的化により採点用の正解は quiz_bank ごとクライアントに同梱される（サーバーで隠せない）。単一ユーザーの自習ツールとして**許容**。その旨 README に一文。

### 3-4. `build_bank.py` に実コード埋め込み
生成時に各 citation を `~/projects/axis-knowledge-rag`（CC環境に存在）に対して解決し、`citation.source`（関数/クラス全文）・`start_line`・`end_line` を埋め込む。`backend/src/anchor/resolver.py` の `resolve_citation()` を import して再利用。解決不可（ADR/README等）は従来の `snippet` フォールバックのまま。`meta.axis_commit` に axis の HEAD を記録。`validate_bank.py` は「resolved な citation には source が入っている」等の緩い検査を追加（必須化はしない＝ADRはsnippet）。

### 3-5. static export 設定
- `next.config.mjs` に `output: 'export'`（必要に応じ `images.unoptimized: true`）。
- 全ページが client/static で動くこと（動的 route・server action 不使用を確認）。
- `frontend/.gitignore` に `/out`。

### 3-6. デプロイ・コミット
```bash
cd ~/projects/Code-study
git add -A
git commit -m "spec_001: static export + TS grading port + embed real source"
git push origin main
```

### 3-7. 動作確認
```bash
cd ~/projects/Code-study/frontend && npm install && npx next build   # → out/ 生成、全ルート成功
npx vitest run                                                        # → パリティテスト pass（あれば）
# out/ を簡易サーブして手動確認: 出題→採点→実コード表示→ダッシュボード→用語集→復習
```

### 3-8. 結果を `outbox/result_001.md` に書く
`templates/result_template.md` の構造で。特に：採点パリティの結果、`next build` ログ要約、Vercel 設定でユーザーがやる手順、判断ポイント。

## 4. 成功条件

- [ ] `npx next build`（`output:'export'`）が成功し `out/` が生成される。
- [ ] 8000番（FastAPI）を起動せずに、出題・採点（5形式）・復習・ダッシュボード・用語集・実コード表示が全部動く。
- [ ] TS グレーダが Python 版とケース一致（移植テスト pass）。
- [ ] quiz_bank.json の「問題」スキーマは不変（追加は citation.source/start_line/end_line と meta.axis_commit のみ）。
- [ ] 進捗が localStorage で永続（リロードで保持）。
- [ ] `git commit + push` 実施。Vercel 初回 import 手順を result に明記。

## 5. 出力先

`~/projects/Code-study/_ai_workspace/bridge/outbox/result_001.md`

## 6. 質問があるとき（判断ポイント）

迷ったら停止して result の Open questions に書き status=blocked。特に：
- vitest を入れてよいか（テスト基盤の追加可否）。入れたくないなら node スクリプトのパリティ確認で代替可。
- `lib/api.ts` は削除 vs 残置（未使用化）。デフォルト削除でよいが、判断割れたら残置で。
- Vercel で `output:'export'` を使うか、Vercel ネイティブ（export なし）に任せるか。**まず `output:'export'` で純静的**を優先（GitHub Pages 等にも移植可能になる）。

## 7. 補足

### 設計の意図
- 採点が決定的＝サーバー不要。静的化で「常設URL・無料・メンテ不要」を最小コストで実現。
- 実コードは生成時埋め込みにすることで、ランタイムの axis 依存を消す（ユーザー端末に axis が無くても実コードが出る）。

### 将来の拡張余地（別 spec）
- spec_002 候補（P2）：問題バンク 120〜150問へ拡充（Cowork が著作、同スキーマで追記）。
- コミット連動の鮮度チェック（axis 更新時に citation 再解決して stale 検出）。
- freetext の LLM 採点／MCP「どこ？」ヒント（要ランタイム＝サーバーレス関数。静的方針と別軸）。
