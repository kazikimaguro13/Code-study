# spec_NNN: <短いタイトル>

- **Author**: Cowork
- **Created**: YYYY-MM-DD
- **Target**: Claude Code (`dev-b`)
- **Project**: `~/projects/Code-study`
- **Status**: pending
- **Bundles**: 関連する spec の番号 / 前提となる spec

## 1. 目的

なぜこの spec を書いているか、現状とゴール。1〜3 段落で簡潔に。

```
[現状]
...

[変更後]
...
```

## 2. 制約

### 触ってよいファイル
- `path/to/file1` — 何を変更
- `path/to/file2` — 何を追加

### 触ってはいけないもの
- `<other dirs>` — 理由
- 既存の <X> 機能 — 後方互換のため

### コーディングルール
- 既存の <パターン> に倣う
- 新規ライブラリ追加は最小限
- (依存追加するなら) requirements.txt / package.json を更新

### デプロイ
- `git push origin main` で auto-deploy（dev-b アカウント / GitHub: kazikimaguro13）

## 3. やってほしいこと

具体的なステップ。コードスケッチ、API 仕様、ファイル構造を含めて、Claude Code が迷わない解像度で書く。

### 3-1. <ステップ 1>

### 3-2. <ステップ 2>

### 3-3. デプロイ・コミット

```bash
cd ~/projects/Code-study
git add -A
git commit -m "spec_NNN: <内容>"
git push origin main
```

### 3-4. 動作確認

### 3-5. 結果を `outbox/result_NNN.md` に書く

`templates/result_template.md` の構造で。diff・テスト結果・判断ポイント・ユーザー向け動作確認手順。

## 4. 成功条件

- [ ] <条件 1>
- [ ] 既存ルート / 機能に影響ない (regression なし)
- [ ] git commit + push 実施

## 5. 出力先

`~/projects/Code-study/_ai_workspace/bridge/outbox/result_NNN.md`

## 6. 質問があるとき

迷ったら作業を停止して outbox/result_NNN.md の "Open questions" に質問を書き、status を `blocked` にして終了。

## 7. 補足

### 設計の意図
...
