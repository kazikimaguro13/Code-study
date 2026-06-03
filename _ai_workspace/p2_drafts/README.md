# P2 drafts — 問題バンク拡充の staging

spec_001（静的化＋採点TS移植＋build_bank拡張）が `quiz_bank.json` / `build_bank.py` を触るため、コンフリクト回避として **P2 の新規問題はここに先行蓄積**する（`data/quiz_bank.json` は直接いじらない）。

## 形式
各 `batch_NN.json` は quiz_bank と**同一スキーマ**の question オブジェクト配列。
- citation-first：先に出典スパンを固定し、`evidence_substring` は必ず `snippet` 内に実在させる。
- merge は spec_001 のスキーマ確定後：build_bank.py に追記 or ローダで結合 → `validate_bank.py` でゲート。

## 進捗
- batch_01: feedback / gap_detection / marker / parent_storage ＋ 逆向き問題（12問）
- 予定: api.py / frontend 3Dグラフ系 / MCPツール群 / evaluation・ragas / L3データフロー増 / 逆向き問題増 → 計 +70〜100 で 120〜150 問へ
