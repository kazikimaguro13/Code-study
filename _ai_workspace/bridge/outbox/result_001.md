# result_001: 採点ロジックTS移植＋Next.js static export＋Vercel自動デプロイ（完全静的化）

- **Spec**: `inbox/spec_001.md`
- **Executor**: Claude Code (dev-b / kazikimaguro13)
- **Started**: 2026-06-03 23:40
- **Finished**: 2026-06-03 23:55
- **Status**: done

## 1. 要約

FastAPI ランタイムを完全排除し、Next.js を pure-static 化した。採点・出題選択・SRS進捗の全ロジックを Python から TypeScript へ移植（5形式すべて）。quiz_bank.json は build 時にバンドルされ、進捗は localStorage に永続化される。`next build`（`output:'export'`）成功・vitest 25/25 pass を確認し、`git push origin main`（kazikimaguro13）完了。

## 2. 変更ファイル

```
 data/quiz_bank.json                                | citation.source/start_line/end_line 追加 (34/51 解決)
 frontend/.gitignore                                | 新規作成 (/out 含む)
 frontend/next.config.mjs                           | output:'export' + images.unoptimized 追加
 frontend/package.json                              | test スクリプト + vitest devDep 追加
 frontend/src/app/dashboard/page.tsx               | api.overview() → engine.overview()
 frontend/src/components/QuestionCard.tsx           | import を @/lib/quiz/types へ変更
 frontend/src/components/QuizRunner.tsx             | api.next/grade → engine.nextQuestions/grade
 frontend/src/components/ResultReveal.tsx           | import を @/lib/quiz/types へ変更
 frontend/src/lib/progress.ts                       | 新規: localStorage SRS 永続化
 frontend/src/lib/quiz/__tests__/graders.test.ts    | 新規: パリティテスト (25ケース)
 frontend/src/lib/quiz/engine.ts                    | 新規: 出題選択・採点・overview エンジン
 frontend/src/lib/quiz/graders.ts                   | 新規: 5形式グレーダ TS 移植
 frontend/src/lib/quiz/normalize.ts                 | 新規: テキスト正規化 TS 移植
 frontend/src/lib/quiz/srs.ts                       | 新規: SM-2-lite SRS TS 移植
 frontend/src/lib/quiz/types.ts                     | 新規: 共有型定義
 scripts/build_bank.py                              | source 埋め込み処理追加
 scripts/validate_bank.py                           | 解決済み citation soft 検証追加
 18 files changed, 3031 insertions(+), 73 deletions(-)
```

## 3. 主要な変更点（ハイライト）

### `frontend/src/lib/quiz/graders.ts`
Python の `backend/src/grading/` 5ファイルを 1 TS ファイルへ集約移植。`grade()` ディスパッチャ、`gradeLocation/FillBlank/Mcq/Dataflow/Freetext` を 1対1 で実装。LLM escalation は静的方針のため省略（spec 指示通り）。

### `frontend/src/lib/quiz/engine.ts`
`backend/src/service.py` の出題選択ロジックを移植。quiz_bank.json を `import` でバンドル。due 優先 → 弱点モジュール重み付けランダム → 低mastery補充の3段階選択を再現。

### `frontend/src/lib/progress.ts`
SQLite の代わりに `localStorage` を使用（`code-study:v1:progress` キー）。`typeof window !== 'undefined'` ガードで SSR/ビルド時クラッシュを回避。

### `scripts/build_bank.py`
`backend.src.anchor.resolver.resolve_citation()` を import し、各 citation のシンボルを axis-knowledge-rag リポジトリに対して解決。51問中 34問の `source/start_line/end_line` を埋め込み。`meta.axis_commit` に axis HEAD を記録。

### `frontend/next.config.mjs`
`output: 'export'` + `images: { unoptimized: true }` 追加。全ルートが Static で出力されることを確認。

## 4. テスト・品質チェック結果

```
$ cd frontend && npx vitest run
 RUN  v1.6.1 /home/nakashima/projects/Code-study/frontend
 ✓ src/lib/quiz/__tests__/graders.test.ts  (25 tests) 15ms
 Test Files  1 passed (1)
      Tests  25 passed (25)
   Duration  1.06s

$ npx next build
 ✓ Compiled successfully
 ✓ Generating static pages (7/7)
 Route (app)                  Size     First Load JS
 ┌ ○ /                        138 B          102 kB
 ├ ○ /dashboard               1.13 kB        88.3 kB
 ├ ○ /glossary                5.88 kB        93.1 kB
 └ ○ /review                  138 B          102 kB
 ○  (Static) prerendered as static content

$ python3 scripts/validate_bank.py
OK: 51 questions valid.
  difficulty: {'L1': 17, 'L2': 23, 'L3': 2, 'L4': 9}
  type: {'location': 13, 'fill_blank': 7, 'freetext': 5, 'dataflow': 2, 'mcq': 24}
  source embedding: 34/51 resolved (axis_commit=0ec909d)

$ git log --oneline -1
9e9268b spec_001: static export + TS grading port + embed real source
```

## 5. 想定外だったこと / 判断ポイント

- **`api.ts` の扱い**: 削除せず残置（未使用化）。`_ai_workspace/` 問題ではないため変更リスクを最小化。既存の問題問題 `q_fe_003`（`API_BASE`のデフォルト値を答える問題）が `lib/api.ts` を引用しているため、消すと quiz_bank の citation が壊れる。
- **vitest parity テストの ease drop ケース**: `null→correct→incorrect` のシーケンスで Python テストは「null から直接 incorrect」を想定していたが、TS テストでは「correct の後の incorrect」をテストしていた（ease 2.3 vs 2.4）。シーケンスを明記しコメントで補足。
- **interval 上限**: SM-2-lite に Python 実装と同じく上限なし → TS の Date.setDate に大数を渡すと `Invalid time value`。365日上限を追加（実用 SRS の範囲内、Python は datetime の最大値まで対応）。
- **Set のスプレッド構文**: Next.js のビルドターゲット設定で `[...set]` がコンパイルエラー → `Array.from(es)` + `.concat(Array.from(gs))` に変更。
- **`lib/api.ts` の削除**: デフォルト「削除」の方針だったが、上記理由で残置。URL fetch は未使用（engine.ts で完結）。

## 6. Open questions

なし（すべて判断・実施済み）。

## 7. 動作確認手順（ユーザー）

### ローカルで out/ を確認する

```bash
cd ~/projects/Code-study/frontend
npx next build          # out/ が生成される
npx serve out           # または: python3 -m http.server -d out 8080
# → http://localhost:3000 (or 8080) を開く
# 出題 → 回答 → 採点 → 実コード表示 → ダッシュボード → 用語集 → 復習
# FastAPI (port 8000) を起動しなくても全機能が動く
```

### Vercel への初回デプロイ（ユーザーが 3クリック）

1. https://vercel.com にログイン → **Add New Project**
2. GitHub の `kazikimaguro13/Code-study` リポジトリを選択
3. 設定画面で以下を確認:
   - **Framework Preset**: Next.js（自動検出される）
   - **Root Directory**: `frontend`（← ここが重要：変更が必要）
   - **Build Command**: `next build`（デフォルトのまま）
   - **Output Directory**: `out`（`output:'export'` により自動）
4. **Deploy** をクリック → 完了

以降は `git push origin main` で自動再デプロイされる。

### quiz_bank.json の実コード再埋め込み

axis リポジトリを更新した後:
```bash
cd ~/projects/Code-study
python3 scripts/build_bank.py     # 再解決 + quiz_bank.json 更新
python3 scripts/validate_bank.py  # 検証
cd frontend && npx next build     # 再ビルド
git add data/quiz_bank.json && git commit -m "chore: refresh source embeddings"
git push origin main
```

## 8. 次の提案（任意）

- **spec_002 候補 (P2)**: 問題バンク 120〜150問へ拡充。build_bank.py の add() 呼び出しを追記するだけで動く（スキーマ互換）。
- `lib/api.ts` の削除: P2 で `q_fe_003` の citation を `lib/quiz/engine.ts` に更新すれば、api.ts を安全に削除できる。
- freetext の LLM 採点: サーバーレス関数（Vercel Edge Functions）を使えば静的方針を維持しつつ LLM 判定を追加できる。
