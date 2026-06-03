export interface GlossaryEntry {
  id: string;
  term: string;
  reading?: string;
  aliases?: string[];
  definition: string;
  axisNote?: string;
}

export const GLOSSARY: GlossaryEntry[] = [
  { id: "hybrid-search", term: "ハイブリッド検索（3-way）", aliases: ["ハイブリッド", "3-way", "3way"], definition: "複数の検索方式を組み合わせて1つのランキングにすること。axis では軸メタデータ絞り込み・ベクトル検索・BM25 の3つを融合する。", axisNote: "search.py の search() が3スコアを重み付き和で統合。" },
  { id: "bm25", term: "BM25", aliases: ["bm25okapi", "okapi"], definition: "キーワードの一致度で文書をスコアリングする古典的な検索アルゴリズム。語の出現頻度と希少性を加味する。意味は見ず字面で測る。", axisNote: "bm25_index.py。rank_bm25 の BM25Okapi を使用。" },
  { id: "rrf", term: "相互ランク融合（RRF）", aliases: ["rrf", "reciprocal rank fusion", "融合", "重み付き和"], definition: "複数のランキングを1つに合成する手法。axis では vector スコアと BM25 スコアを重み（bm25_weight）で線形結合して足し合わせる。", axisNote: "final = (1 - bm25_weight) * vector + bm25_weight * bm25。" },
  { id: "vector-search", term: "ベクトル検索 / 埋め込み（embedding）", aliases: ["ベクトル検索", "embedding", "埋め込み", "ベクトル"], definition: "文章を数値ベクトルに変換し、意味の近さ（ベクトルの距離）で検索する方式。字面が違っても意味が近ければヒットする。", axisNote: "embedder.py が Gemini などでベクトル化、ChromaDB に保存。" },
  { id: "cosine", term: "コサイン類似度", aliases: ["コサイン", "cosine"], definition: "2つのベクトルの向きの近さ（0〜1）。1に近いほど意味が近い。検索では距離 dist を 1 - dist でスコア化する。" },
  { id: "chromadb", term: "ChromaDB", aliases: ["chroma", "chromadb"], definition: "ローカルで動くベクトルデータベース。埋め込みベクトルとメタデータを保存し、近傍検索（類似ベクトル探索）を提供する。", axisNote: "vector_store.py がラップ。軸メタデータも metadata に格納。" },
  { id: "parent-document", term: "Parent Document Retrieval（Small-to-Big）", aliases: ["parent document", "small-to-big", "parent-doc"], definition: "小さい単位（child）で検索し、ヒットしたら大きい単位（parent）を回答に渡す手法。検索精度と文脈量を両立させる。", axisNote: "chunker.py。child=小ブロックで検索、parent=H2セクション全文をLLMへ。" },
  { id: "chunk", term: "チャンク / parent・child", aliases: ["チャンク", "chunk", "parent", "child", "chunking", "チャンク分割"], definition: "文書を検索しやすい単位に分割した塊。axis では parent=H2セクション、child=その中の小ブロック（H3/段落/トークン上限で分割）。" },
  { id: "nfkc", term: "NFKC（Unicode正規化）", aliases: ["nfkc"], definition: "全角・半角や合成文字などの表記ゆれを統一する Unicode 正規化形式。例：'ＡＢ'→'AB'。検索の取りこぼしを防ぐ。", axisNote: "normalizer.py が NFKC＋カナ→かな＋小文字化をかける。" },
  { id: "normalize", term: "正規化（normalization）", aliases: ["正規化", "normalization", "normalizer"], definition: "テキストを比較しやすい標準形に揃える前処理。クエリと索引の両方に同じ変換をかけることで表記ゆれを吸収する。" },
  { id: "ngram", term: "n-gram（文字 n-gram）", aliases: ["n-gram", "ngram", "n gram"], definition: "文字や単語を n 個ずつ区切ったもの。'あいう'の2-gramは'あい','いう'。形態素解析なしで日本語を扱える簡便なトークン化。", axisNote: "bm25_index.py の _tokenize が n=1,2 の文字 n-gram を生成。" },
  { id: "morphological", term: "形態素解析", aliases: ["形態素解析", "形態素", "mecab"], definition: "日本語文を単語に分割し品詞を判定する処理（MeCab など）。高精度だが外部ライブラリ依存になる。axis は依存を避け n-gram を採用。" },
  { id: "time-decay", term: "時間減衰 / 半減期（half-life）", aliases: ["時間減衰", "half-life", "half_life", "decay", "半減期"], definition: "新しい文書のスコアを少し優遇する仕組み。半減期日数で指数的に減衰（その日数経過で係数0.5）。axis ではデフォルト無効の opt-in。", axisNote: "_decay.py。decay = exp(-ln2 * 経過日数 / half_life_days)。" },
  { id: "graphrag", term: "GraphRAG", aliases: ["graphrag", "graph rag"], definition: "文書間のつながり（グラフ）を検索に使う手法。ヒット文書の隣接文書も結果に加え、編集者が貼った関連（refs）を活かす。", axisNote: "graph.py。refs から有向グラフを作り1ホップ隣接を0.7倍で合流。" },
  { id: "networkx", term: "networkx / 有向グラフ（DiGraph）", aliases: ["networkx", "digraph", "有向グラフ"], definition: "Python のグラフ処理ライブラリ。DiGraph は向きのある辺を持つグラフ。axis は別プロセス不要な in-process グラフ層に採用。" },
  { id: "bfs", term: "BFS（幅優先探索）", aliases: ["bfs", "幅優先"], definition: "グラフを近いノードから順に辿る探索法。あるノードから「何ホップ以内の隣接ノード」を集めるのに使う。", axisNote: "graph.py の neighbors_within_hop。" },
  { id: "refs", term: "refs（参照）", aliases: ["refs", "参照"], definition: "文書の YAML frontmatter に書く「関連する別文書ID」のリスト。integrity チェックと GraphRAG の両方で使われる。" },
  { id: "protocol", term: "Protocol（プロトコル / 構造的型）", aliases: ["protocol", "プロトコル"], definition: "Python で「このメソッドを持っていれば良い」と振る舞いだけ定める型。継承不要で差し替え可能な実装を作れる。", axisNote: "Embedder / GenerationBackend / ConversationStore が Protocol。" },
  { id: "factory", term: "ファクトリ（factory）", aliases: ["factory", "ファクトリ", "make_embedder", "make_"], definition: "設定や状況に応じて適切な実装インスタンスを生成して返す関数/仕組み。呼び出し側は具体的な実装を意識しなくて済む。", axisNote: "make_embedder() が config からバックエンドを選ぶ。" },
  { id: "mcp", term: "MCP（Model Context Protocol）", aliases: ["mcp"], definition: "LLMクライアント（Claude Desktop 等）に外部ツールや知識を接続する標準プロトコル。axis は検索/RAGを MCP ツールとして公開する。", axisNote: "mcp_server/server.py。axis_search などのツールを提供。" },
  { id: "stdio", term: "stdio（標準入出力トランスポート）", aliases: ["stdio"], definition: "プロセスの標準入力/出力を通して通信する方式。MCPサーバをクライアントが子プロセスとして起動して繋ぐときに使う。" },
  { id: "fastmcp", term: "FastMCP", aliases: ["fastmcp"], definition: "MCPサーバを手軽に書くための Python フレームワーク。関数に印を付けるだけでMCPツールにできる。" },
  { id: "conversational-rag", term: "Conversational RAG（履歴付きRAG）", aliases: ["conversational rag", "conversational-rag", "履歴付き"], definition: "会話履歴を保持しフォローアップ質問にも答えられるRAG。代名詞を含む質問を文脈から独立した形に書き換えてから検索する。", axisNote: "conversation.py（履歴保存）＋ question_rewriter.py（書き換え）。" },
  { id: "standalone-query", term: "standalone クエリ（独立クエリ）", aliases: ["standalone", "独立クエリ", "書き換え", "rewrite"], definition: "文脈依存の質問を、履歴なしでも意味が通る検索用の文に書き換えたもの。検索にだけ使い、回答生成には元の質問を使う。" },
  { id: "citation", term: "インライン引用 [N]", aliases: ["引用", "citation", "cited", "出典"], definition: "回答文中に出典番号 [1] を埋め込む方式。クリックで該当出典に飛べる。範囲外の番号やコード内の[1]は除去/無視する。", axisNote: "_citations.py（Python）と citations.ts（フロント）が対で実装。" },
  { id: "sm2", term: "間隔反復 / SM-2", aliases: ["間隔反復", "sm-2", "sm2", "spaced repetition", "復習"], definition: "正解した項目ほど復習間隔を伸ばし、間違えた項目は早く再出題する記憶定着の手法。このクイズの復習スケジューリングに使用。", axisNote: "（このツール側）store/progress.py が SM-2 lite を実装。" },
  { id: "slug", term: "slug", aliases: ["slug"], definition: "タイトルなどから作る、ID/URL向けの短い文字列（英数字とハイフン）。axis は日本語見出しが弱いslugになる場合md5にフォールバック。" },
  { id: "frontmatter", term: "YAML frontmatter", aliases: ["frontmatter", "yaml", "フロントマター"], definition: "Markdownファイル冒頭に '---' で囲んで書くメタデータ（タイトル・カテゴリ・refs等）。axis のナレッジはこの形式で軸メタデータを持つ。" },
  { id: "fastapi", term: "FastAPI", aliases: ["fastapi", "uvicorn"], definition: "Python の高速なWeb APIフレームワーク。型ヒントから自動でバリデーションとAPIドキュメントを生成する。", axisNote: "axis/このツールのバックエンド。" },
  { id: "nextjs", term: "Next.js（App Router）", aliases: ["next.js", "nextjs", "app router"], definition: "React 製のWebアプリフレームワーク。App Router は app/ ディレクトリのフォルダ構成がそのままページURLになる方式。" },
  { id: "cors", term: "CORS", aliases: ["cors"], definition: "別オリジン（別ポート等）からのブラウザ通信を許可/制限する仕組み。フロント(3000)からAPI(8000)を叩くには許可設定が要る。" },
  { id: "rag", term: "RAG（検索拡張生成）", aliases: ["rag", "retrieval augmented"], definition: "まず関連文書を検索し、その内容をLLMに渡して回答させる仕組み。LLM単体より根拠に基づいた回答ができ、出典も示せる。", axisNote: "rag.py の RAGPipeline が 検索→文脈構築→生成→引用 を担う。" },
  { id: "idempotent", term: "冪等（idempotent）", aliases: ["冪等", "idempotent"], definition: "同じ操作を何回行っても結果が同じになる性質。axis のメモ更新は delete_doc + 再ingest で冪等にしている。" },
  { id: "minmax", term: "min-max 正規化", aliases: ["min-max", "minmax"], definition: "値を最小0・最大1の範囲に揃える変換。BM25の生スコアを[0,1]に直し、コサイン類似度と同じ土俵で足し合わせるために使う。" },
];

const NORM = (s: string) => s.toLowerCase();

export function findTerms(text: string): GlossaryEntry[] {
  if (!text) return [];
  const hay = NORM(text);
  const hits: GlossaryEntry[] = [];
  for (const e of GLOSSARY) {
    const needles = [e.term, ...(e.aliases ?? [])].map(NORM);
    if (needles.some((n) => n.length >= 2 && hay.includes(n))) hits.push(e);
  }
  return hits;
}
