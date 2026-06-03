# spec_002: P2 問題バンク拡充のマージ（p2_drafts → quiz_bank 再生成＋実コード埋め込み＋validate）

- **Author**: Cowork
- **Created**: 2026-06-03
- **Target**: Claude Code (`dev-b`)
- **Project**: `~/projects/Code-study`
- **Status**: pending
- **Bundles**: spec_001（静的化・build_bank の source 埋め込み済み）が前提

## 1. 目的

Cowork が `_ai_workspace/p2_drafts/batch_*.json` に**新規問題を staging 済み**（現時点 batch_01〜03 = 32問、以後 batch_04+ が追加されうる）。これらを既存 `data/quiz_bank.json` にマージし、spec_001 で実装した「実コード埋め込み」を新問にも適用して再生成・検証する。

```
[現状] data/quiz_bank.json = 51問（spec_001でcitation.source埋め込み済み）。新問は p2_drafts/*.json に分離保管。
[変更後] build_bank.py が p2_drafts/*.json も取り込み、全問（51＋staging分）を1つの quiz_bank.json に再生成。新問の code citation にも source/start_line/end_line を埋め込む。validate 通過。TS採点テスト・next build も緑のまま。
```

## 2. 制約

### 触ってよいファイル
- `scripts/build_bank.py` — `_ai_workspace/p2_drafts/batch_*.json` を読み込み、各 `questions` を Q に append する処理を追加（既存の add(...) 群の後、data 組み立て前）。
- `scripts/validate_bank.py` — 変更不要のはず（既存検証で足りる）。必要なら id 一意・evidence実在の検査を強化。
- `data/quiz_bank.json` — 再生成で更新（生成物）。
- `_ai_workspace/bridge/inbox/INDEX.md` — spec_002 を done に更新（任意）。

### 触ってはいけない
- 採点ロジック（`frontend/src/lib/quiz/`・`backend/src/grading/`）— 変更不要（新問は既存5形式のみ使用）。
- `_ai_workspace/p2_drafts/*.json` の中身 — **Cowork の著作物。原則改変しない**（誤りを見つけたら result の Open questions に報告して停止）。
- 問題スキーマ — 不変。

### コーディングルール
- p2_drafts 取り込みは「ファイル名昇順で安定」。各 batch の `questions` 配列をそのまま流用（既に quiz_bank と同一スキーマ）。
- マージ後 **id 重複が無いこと**を生成時に assert（あれば fail）。
- source 埋め込みは spec_001 と同じ `resolve_citation()` 経由。解決不可（ADR/README/module docstring）は snippet フォールバックのまま（必須化しない）。

### デプロイ
- commit はしてよい。**push は朝バッチ（ユーザーが承認できる時間帯）に行う**。push 段でブロックされたら待機し、result に「push 承認待ち」と明記して status=partial で終了してもよい。

## 3. やってほしいこと

### 3-1. build_bank.py に staging 取り込みを追加
```python
# 既存 add(...) 群の後、data 組み立て前に:
import glob, json, os
_DRAFT_DIR = os.path.join(os.path.dirname(__file__), "..", "_ai_workspace", "p2_drafts")
for fp in sorted(glob.glob(os.path.join(_DRAFT_DIR, "batch_*.json"))):
    with open(fp, encoding="utf-8") as f:
        for q in json.load(f).get("questions", []):
            Q.append(q)
# id 一意 assert
ids = [q["id"] for q in Q]
assert len(ids) == len(set(ids)), f"duplicate ids: {[i for i in ids if ids.count(i) > 1]}"
```
（既存の source 埋め込み処理が Q 全体に適用されるよう、append はその処理の前に置く。spec_001 の実装位置に合わせて調整可。）

### 3-2. 再生成・検証
```bash
cd ~/projects/Code-study
python3 scripts/build_bank.py          # → data/quiz_bank.json 再生成（全問）
python3 scripts/validate_bank.py       # → OK、問題数が増えていること
cd frontend && npx vitest run          # → 採点パリティ 緑のまま
npx next build                         # → static export 緑のまま（quiz_bank同梱）
```

### 3-3. コミット（push は朝）
```bash
cd ~/projects/Code-study
git add -A
git commit -m "spec_002: merge P2 question batches into quiz_bank with embedded source"
# git push origin main   ← 朝、ユーザー承認のもとで実行
```

### 3-4. 結果を outbox/result_002.md に書く
問題数（before/after）、source 解決数、validate 出力、vitest/next build 結果、push 状態（済 or 承認待ち）。

## 4. 成功条件
- [ ] quiz_bank.json が 51 + staging 分（現状 +32 = 83、batch追加分も全部）に増えている。
- [ ] validate_bank.py OK、id 重複なし、evidence 実在。
- [ ] 新問の code citation に source 埋め込み（解決可能なもの）。
- [ ] vitest・next build 緑のまま（採点/ビルドに regression なし）。
- [ ] commit 済み。push は朝に実施（または承認待ちで status=partial）。

## 5. 出力先
`~/projects/Code-study/_ai_workspace/bridge/outbox/result_002.md`

## 6. 質問があるとき
- p2_drafts の問題に明らかな誤り（evidence不一致・誤答キー等）を見つけたら、**勝手に直さず** Open questions に列挙して status=blocked。Cowork が修正する。

## 7. 補足
- 本 spec は「Cowork=著作・判断、CC=機械的マージ＋ビルド」の分担。新問の追加（batch_04+）後も同じ spec を再 dispatch すれば最新の staging を取り込んで再生成できる（冪等）。
