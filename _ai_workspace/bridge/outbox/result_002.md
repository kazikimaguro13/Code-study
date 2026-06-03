# result_002: P2 問題バンク拡充のマージ（p2_drafts → quiz_bank 再生成＋実コード埋め込み＋validate）

- **Spec**: `inbox/spec_002.md`
- **Executor**: Claude Code (dev-b / kazikimaguro13)
- **Started**: 2026-06-04 07:08
- **Finished**: 2026-06-04 07:15
- **Status**: partial（commit 済み、push 承認待ち）

## 1. 要約

`scripts/build_bank.py` に `_ai_workspace/p2_drafts/batch_*.json` を昇順読み込みして `Q` へ append する処理と id 重複 assert を追加した。再生成後の `data/quiz_bank.json` は 51 問 → 83 問（+32）。新問の code citation にも `_embed_sources()` で source/start_line/end_line を埋め込み（55/83 解決）。validate・vitest・next build はすべて緑。commit 済み。push はユーザー承認待ち。

## 2. 変更ファイル

```
 scripts/build_bank.py |  12 ++++++++++
 data/quiz_bank.json   | 1274 ++++++++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 1286 insertions(+)
```

## 3. 主要な変更点（ハイライト）

### `scripts/build_bank.py`

既存 `add(...)` 群の直後（`_embed_sources()` 呼び出し前）に staging 取り込みブロックを挿入。`_ROOT` / `json` は既存 import を流用し、追加 import は `glob` のみ。id 重複は assert で即 fail。

```python
import glob as _glob
_DRAFT_DIR = _ROOT / "_ai_workspace" / "p2_drafts"
for _fp in sorted(_glob.glob(str(_DRAFT_DIR / "batch_*.json"))):
    with open(_fp, encoding="utf-8") as _f:
        for q in json.load(_f).get("questions", []):
            Q.append(q)
_ids = [q["id"] for q in Q]
assert len(_ids) == len(set(_ids)), f"duplicate ids: {[i for i in _ids if _ids.count(i) > 1]}"
```

append は `_embed_sources()` の前なので、新問も既存問と同じ source 埋め込み処理が適用される。

### `data/quiz_bank.json`

83 問に再生成（batch_01: 11問、batch_02: 10問、batch_03: 11問を確認）。id 重複なし。

## 4. テスト・品質チェック結果

```
$ python3 scripts/build_bank.py
source embedding: 55/83 citations resolved (axis HEAD=0ec909d)
wrote 83 questions -> /home/nakashima/projects/Code-study/data/quiz_bank.json

$ python3 scripts/validate_bank.py
OK: 83 questions valid.
  difficulty: {'L1': 27, 'L2': 38, 'L3': 5, 'L4': 13}
  type: {'location': 24, 'fill_blank': 9, 'freetext': 9, 'dataflow': 5, 'mcq': 36}

Warnings (1 — not errors, fix by running scripts/build_bank.py):
  - q_rev_004: resolvable citation lacks embedded source (run build_bank.py)

$ cd frontend && npx vitest run
 ✓ src/lib/quiz/__tests__/graders.test.ts  (25 tests) 15ms
 Test Files  1 passed (1)
      Tests  25 passed (25)

$ npx next build
 ✓ Compiled successfully
 ✓ Generating static pages (7/7)

$ git log --oneline -1
4b3b020 spec_002: merge P2 question batches into quiz_bank with embedded source
```

## 5. 想定外だったこと / 判断ポイント

- **validate warning（q_rev_004）**: `frontend/src/lib/graphClient.ts` の `GraphNode` interface が resolver で `found=False` を返したため source 未埋め込み。validate は WARNING（error でなく OK 判定）であり、spec の「解決不可は snippet フォールバックのまま（必須化しない）」に合致するため続行した。
- **`import glob`**: spec のサンプルコードでは `import glob, json, os` だったが、`json` と `Path`（`_ROOT`）は既に import 済みのため `import glob as _glob` のみ追加してクリーンにした。

## 6. Open questions

なし（p2_drafts の問題内容に明らかな誤りは見当たらなかった）。

## 7. 動作確認手順（ユーザー）

```
1. cd ~/projects/Code-study
2. python3 scripts/validate_bank.py
   確認: "OK: 83 questions valid." と表示されること（Warning 1件は非エラー）
3. cd frontend && npx vitest run
   確認: 25 tests passed
4. push 承認時:
   git push origin main
   確認: GitHub (kazikimaguro13/Code-study) の main に 4b3b020 が反映されること
```

## 8. push について

spec の指示「push は朝、ユーザー承認のもとで実行」に従い **push は未実施**。
承認いただけたら以下を実行してください：

```bash
cd ~/projects/Code-study
git push origin main
```

## 9. 次の提案（任意）

- spec_003 候補: batch_04+ が追加された場合、本 spec を再 dispatch するだけで冪等に再生成可能（設計済み）。
- `q_rev_004` の source 埋め込み: resolver が TypeScript の `interface` シンボルに未対応の可能性。resolver を拡張すれば Warning が消える。
