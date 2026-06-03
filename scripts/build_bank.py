from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

REPO = "axis-knowledge-rag"
REPO_COMMIT = "0ec909d"
AXIS_REPO = Path.home() / "projects" / "axis-knowledge-rag"
OUT = _ROOT / "data" / "quiz_bank.json"
Q: list[dict] = []
def add(**kw): Q.append(kw)
def loc(file, sym, aliases=None, partial=0.5):
    return {"file": file, "symbol": sym}, {"symbol_aliases": aliases or [sym], "accept_file_only_partial": partial}

# ---- search.py ----
af, ag = loc("backend/src/search.py", "SearchEngine.search", ["search","fuse_results","fuse"])
add(id="q_search_001", difficulty="L1", type="location", module="backend/src/search.py", tags=["fusion","bm25"],
    prompt="ベクトル類似度スコアとBM25スコアを重み付き和で融合し最終ランキングを作る処理は、どのクラスのどのメソッド？（ファイルとシンボル）",
    citation={"file":"backend/src/search.py","symbol":{"kind":"method","name":"SearchEngine.search"},
      "evidence_substring":"final = (1.0 - bm25_weight) * r.score + bm25_weight * bm25","adr_ref":None,
      "snippet":"if use_bm25:\n    bm25_scores = self._bm25_index.score(query)\n    for r in results:\n        bm25 = bm25_scores.get(r.id, 0.0)\n        final = (1.0 - bm25_weight) * r.score + bm25_weight * bm25"},
    answer=af, grading=ag, explanation="融合はSearchEngine.search()のインライン処理。vectorとBM25をbm25_weightで線形結合し再ソート。")
add(id="q_search_002", difficulty="L2", type="fill_blank", module="backend/src/search.py", tags=["fusion"],
    prompt="融合スコアの空欄を埋めよ:\n    final = (1.0 - bm25_weight) * r.score + ____ * bm25",
    citation={"file":"backend/src/search.py","symbol":{"kind":"method","name":"SearchEngine.search"},
      "evidence_substring":"bm25_weight * bm25","adr_ref":None,
      "snippet":"final = (1.0 - bm25_weight) * r.score + bm25_weight * bm25"},
    answer={"accepted":["bm25_weight"]}, grading={"casefold":True},
    explanation="vectorに(1-w)、BM25にwを掛ける重み付き和。w=bm25_weight。")
add(id="q_search_003", difficulty="L2", type="fill_blank", module="backend/src/search.py", tags=["scoring"],
    prompt="Chromaの距離distをスコアに変換する式の空欄を埋めよ:\n    score = max(0.0, min(1.0, 1.0 - ____))",
    citation={"file":"backend/src/search.py","symbol":{"kind":"function","name":"_to_results"},
      "evidence_substring":"score = max(0.0, min(1.0, 1.0 - dist))","adr_ref":None,
      "snippet":"dist = distances[i] if distances else 0.0\n        score = max(0.0, min(1.0, 1.0 - dist))"},
    answer={"accepted":["dist","distance"]}, grading={"casefold":True},
    explanation="コサイン距離distを1-distで類似度化し[0,1]にクランプ。")
add(id="q_search_004", difficulty="L2", type="freetext", module="backend/src/search.py", tags=["gap-detection"],
    prompt="SearchEngine._record_gap の役割を一文で説明せよ。",
    citation={"file":"backend/src/search.py","symbol":{"kind":"method","name":"SearchEngine._record_gap"},
      "evidence_substring":'reason="no_results"',"adr_ref":None,
      "snippet":'if not results:\n    self._gap_store.record(query=query, reason="no_results", n_results=0)\ntop = float(results[0].score)\nif top < self._gap_low_score_threshold:\n    self._gap_store.record(query=query, reason="low_score", ...)'},
    answer={"model_answer":"検索が無結果またはスコアが低かった時にナレッジギャップとして記録するフック。",
      "required_keywords":[{"any_of":["no_results","無結果","0件","結果がない"]},{"any_of":["low_score","スコアが低い","しきい値","閾値"]},{"any_of":["記録","ログ","record","ギャップ"]}],
      "forbidden_keywords":[]}, grading={"min_keyword_coverage":0.66},
    explanation="検索品質が低いクエリを記録しナレッジの穴を分析する。gap_store=Noneならno-op。")
add(id="q_search_005", difficulty="L3", type="dataflow", module="backend/src/search.py", tags=["pipeline"],
    prompt="自然文クエリのsearch()が結果を返すまでの主要ステップを順に並べよ。",
    citation={"file":"backend/src/search.py","symbol":{"kind":"method","name":"SearchEngine.search"},
      "evidence_substring":"embedding = self._embedder.embed(q_norm)","adr_ref":None,
      "snippet":"q_norm = self._normalizer(query)\nembedding = self._embedder.embed(q_norm)\nraw = self._store.query(embedding=embedding, ...)\nbm25_scores = self._bm25_index.score(query)\n# fuse, then time decay"},
    answer={"sequence":["normalizer","embedder","vector_store.query","bm25_index.score","fuse","time_decay"]},
    grading={"mode":"subsequence","pass_threshold":0.66,"aliases":[["normalizer","正規化"],["embedder","embed","埋め込み"],["vector_store.query","vector_store","chroma","vector"],["bm25_index.score","bm25"],["fuse","融合","重み付き和"],["time_decay","decay","時間減衰"]]},
    pool=["bm25_index.score","time_decay","normalizer","vector_store.query","embedder","fuse"],
    explanation="正規化→埋め込み→ベクトル検索→BM25→重み付き和で融合・再ソート→時間減衰。")
add(id="q_search_006", difficulty="L2", type="mcq", module="backend/src/search.py", tags=["fusion"],
    prompt="search(bm25_weight=0.0) を呼ぶと挙動はどうなる？",
    citation={"file":"backend/src/search.py","symbol":{"kind":"method","name":"SearchEngine.search"},
      "evidence_substring":"falls back to the v0.5","adr_ref":None,
      "snippet":"bm25_weight: 0.0 falls back to the v0.5 vector-only behaviour, 1.0 ranks purely by BM25."},
    answer={"options":["BM25のみでランキング","v0.5相当のベクトル検索のみにフォールバック","エラーになる","軸メタデータのみで絞り込む"],"correct_index":1},
    explanation="0.0でBM25寄与ゼロ＝ベクトルのみ(v0.5)。1.0で純BM25。")

# ---- bm25_index.py ----
add(id="q_bm25_001", difficulty="L1", type="location", module="backend/src/bm25_index.py", tags=["bm25","tokenize"],
    prompt="形態素解析なしで日本語を扱う『文字n-gramトークナイザ』はどのファイルのどの関数？",
    citation={"file":"backend/src/bm25_index.py","symbol":{"kind":"function","name":"_tokenize"},
      "evidence_substring":"tokens.append(text[i : i + 2])","adr_ref":None,
      "snippet":"def _tokenize(text):\n    tokens.extend(text)  # n=1\n    for i in range(len(text)-1):\n        tokens.append(text[i : i + 2])  # n=2"},
    answer=loc("backend/src/bm25_index.py","_tokenize",["_tokenize","tokenize"])[0], grading=loc("backend/src/bm25_index.py","_tokenize",["_tokenize","tokenize"])[1],
    explanation="_tokenizeはn=1,2の文字n-gram。形態素解析器の依存を避ける。")
add(id="q_bm25_002", difficulty="L2", type="mcq", module="backend/src/bm25_index.py", tags=["bm25","design"],
    prompt="BM25に形態素解析でなく文字n-gramを選んだ主な理由は？",
    citation={"file":"backend/src/bm25_index.py","symbol":{"kind":"function","name":"_tokenize"},
      "evidence_substring":"avoids","adr_ref":None,
      "snippet":"character n-gram (n=1,2) on normalized text — avoids the morphological analyzer dependency while still usable for Japanese."},
    answer={"options":["n-gramが常に高精度","形態素解析器への依存を避けつつ日本語で使える","英語専用化","Chromaの要求"],"correct_index":1},
    explanation="追加依存(形態素解析器)を増やさない方針。")
add(id="q_bm25_003", difficulty="L2", type="freetext", module="backend/src/bm25_index.py", tags=["bm25","scoring"],
    prompt="BM25Index.scoreが生スコアをmin-max正規化して[0,1]にするのはなぜ？",
    citation={"file":"backend/src/bm25_index.py","symbol":{"kind":"method","name":"BM25Index.score"},
      "evidence_substring":"so they can be summed with cosine similarity","adr_ref":None,
      "snippet":"Raw BM25 scores are min-max normalized to [0,1] so they can be summed with cosine similarity.\nnorm_scores = (scores - s_min) / (s_max - s_min)"},
    answer={"model_answer":"コサイン類似度(0〜1)と重み付き和で足せるようスケールを揃えるため。",
      "required_keywords":[{"any_of":["コサイン","cosine","ベクトル","類似度"]},{"any_of":["足","加算","和","融合","sum","合算","スケール","揃え"]}],"forbidden_keywords":[]},
    grading={"min_keyword_coverage":0.5}, explanation="スケールを[0,1]に揃えてコサインと同じ土俵で重み付き和。")
add(id="q_bm25_004", difficulty="L1", type="fill_blank", module="backend/src/bm25_index.py", tags=["bm25","library"],
    prompt="BM25モデル構築の空欄(使用クラス名)を埋めよ:\n    model = ____(tokenized)",
    citation={"file":"backend/src/bm25_index.py","symbol":{"kind":"method","name":"BM25Index.build"},
      "evidence_substring":"model = BM25Okapi(tokenized)","adr_ref":None,
      "snippet":"from rank_bm25 import BM25Okapi\nmodel = BM25Okapi(tokenized)"},
    answer={"accepted":["BM25Okapi","BM25Okapi(tokenized)"]}, grading={"casefold":True},
    explanation="rank_bm25のBM25Okapiを使用。")

# ---- _decay.py ----
add(id="q_decay_001", difficulty="L1", type="fill_blank", module="backend/src/_decay.py", tags=["time-decay"],
    prompt="指数減衰係数の空欄を埋めよ:\n    return math.exp(-math.log(2) * age_days / ____)",
    citation={"file":"backend/src/_decay.py","symbol":{"kind":"function","name":"decay_factor"},
      "evidence_substring":"age_days / half_life_days","adr_ref":None,
      "snippet":"return math.exp(-math.log(2) * age_days / half_life_days)"},
    answer={"accepted":["half_life_days"]}, grading={"casefold":True}, explanation="半減期ベースの指数減衰。age=half_lifeで0.5。")
add(id="q_decay_002", difficulty="L2", type="mcq", module="backend/src/_decay.py", tags=["time-decay"],
    prompt="経過日数がちょうどhalf_life_daysのとき減衰係数は？",
    citation={"file":"backend/src/_decay.py","symbol":{"kind":"function","name":"decay_factor"},
      "evidence_substring":"At age=half_life_days: 0.5","adr_ref":None,
      "snippet":"At age=half_life_days: 0.5; at age=2*half_life_days: 0.25"},
    answer={"options":["1.0","0.5","0.25","0.0"],"correct_index":1}, explanation="半減期の定義どおり0.5。")
add(id="q_decay_003", difficulty="L2", type="location", module="backend/src/_decay.py", tags=["time-decay"],
    prompt="ベーススコアと減衰係数を重み付きでブレンドする関数は？（ファイルとシンボル）",
    citation={"file":"backend/src/_decay.py","symbol":{"kind":"function","name":"blend_score"},
      "evidence_substring":"return base_score * (1.0 - w * (1.0 - decay))","adr_ref":None,
      "snippet":"def blend_score(base_score, decay, weight):\n    w = max(0.0, min(1.0, weight))\n    return base_score * (1.0 - w * (1.0 - decay))"},
    answer=loc("backend/src/_decay.py","blend_score")[0], grading=loc("backend/src/_decay.py","blend_score")[1],
    explanation="final = base*(1-w*(1-decay))。weightで減衰の効きを調整。")
add(id="q_decay_004", difficulty="L4", type="mcq", module="docs/adr/ADR-021-time-weighted-decay.md", tags=["time-decay","design"],
    prompt="Time-Weighted Decayをデフォルト無効(opt-in)にした設計判断の理由は？(ADR-021)",
    citation={"file":"docs/adr/ADR-021-time-weighted-decay.md","symbol":{"kind":"section","name":"Decision"},
      "evidence_substring":"enabled: true","adr_ref":"ADR-021",
      "snippet":"config.ymlでenabled: trueにすると有効。opt-in(デフォルト無効)。新しさ優遇が全ユーザーに望ましいとは限らないため。"},
    answer={"options":["未完成だから","新しさ優遇が常に望ましいとは限らず、望む人だけ有効化できるように","計算コストが高すぎる","Chroma非対応"],"correct_index":1},
    explanation="鮮度バイアスは用途依存。デフォルト無効で必要な人だけ有効化。")

# ---- normalizer.py ----
add(id="q_norm_001", difficulty="L1", type="freetext", module="backend/src/normalizer.py", tags=["japanese"],
    prompt="Normalizerが表記ゆれ吸収のために行う3つの変換を挙げよ。",
    citation={"file":"backend/src/normalizer.py","symbol":{"kind":"function","name":"normalize_text"},
      "evidence_substring":'unicodedata.normalize("NFKC", s)',"adr_ref":None,
      "snippet":'s = unicodedata.normalize("NFKC", s)\ns = _katakana_to_hiragana(s)\ns = s.lower()'},
    answer={"model_answer":"NFKC正規化、カタカナ→ひらがな、小文字化。",
      "required_keywords":[{"any_of":["nfkc"]},{"any_of":["カタカナ","かな","ひらがな"]},{"any_of":["小文字","lowercase","lower"]}],
      "forbidden_keywords":["形態素","ステミング","stemming"]}, grading={"min_keyword_coverage":0.66},
    explanation="NFKC+カナ→かな+lowercase。クエリと索引対象の両方にかけて表記ゆれ吸収。")
add(id="q_norm_002", difficulty="L1", type="location", module="backend/src/normalizer.py", tags=["japanese"],
    prompt="カタカナをひらがなにコードポイントシフトで変換する関数は？（ファイルとシンボル）",
    citation={"file":"backend/src/normalizer.py","symbol":{"kind":"function","name":"_katakana_to_hiragana"},
      "evidence_substring":"cp - _KATAKANA_START + _HIRAGANA_START","adr_ref":None,
      "snippet":"if _KATAKANA_START <= cp <= _KATAKANA_END:\n    out.append(chr(cp - _KATAKANA_START + _HIRAGANA_START))"},
    answer=loc("backend/src/normalizer.py","_katakana_to_hiragana",["_katakana_to_hiragana","katakana_to_hiragana"])[0],
    grading=loc("backend/src/normalizer.py","_katakana_to_hiragana",["_katakana_to_hiragana","katakana_to_hiragana"])[1],
    explanation="カタカナブロックをひらがな開始へコードポイント差分でシフト。")
add(id="q_norm_003", difficulty="L4", type="mcq", module="backend/src/normalizer.py", tags=["design","dependencies"],
    prompt="正規化を外部ライブラリでなく自前実装している理由は？",
    citation={"file":"backend/src/normalizer.py","symbol":{"kind":"module","name":"module docstring"},
      "evidence_substring":"LangChain / 外部ライブラリ非依存","adr_ref":"ADR-001",
      "snippet":"NFKC + カタカナ→ひらがな + lowercase。LangChain / 外部ライブラリ非依存。"},
    answer={"options":["外部の方が遅い","依存を薄くし内部挙動を読める方針(LangChain不採用)","ライセンス制約","日本語は外部では不可能"],"correct_index":1},
    explanation="『自前実装・薄い依存』がaxisの核方針。")

# ---- chunker.py ----
add(id="q_chunk_001", difficulty="L1", type="mcq", module="backend/src/chunker.py", tags=["parent-doc"],
    prompt="Parent Document Retrievalで parent と child はそれぞれ何の単位？",
    citation={"file":"backend/src/chunker.py","symbol":{"kind":"module","name":"module docstring"},
      "evidence_substring":"H2-level sections","adr_ref":"ADR-017",
      "snippet":"parents: H2-level sections (or whole doc when no H2). children: smaller sub-blocks within each parent (H3+/paragraph/token cap)."},
    answer={"options":["parent=ファイル全体/child=H2","parent=H2セクション/child=その中の小ブロック","parent=段落/child=文","ともにファイル単位"],"correct_index":1},
    explanation="parent=H2(LLMに渡す塊)、child=小ブロック(検索・embedの単位)。")
add(id="q_chunk_002", difficulty="L2", type="location", module="backend/src/chunker.py", tags=["parent-doc"],
    prompt="parentの一意ID({doc_id}#{slug})を生成する関数は？（ファイルとシンボル）",
    citation={"file":"backend/src/chunker.py","symbol":{"kind":"function","name":"_make_parent_id"},
      "evidence_substring":'return f"{doc_id}#{slug}"',"adr_ref":None,
      "snippet":'slug = _slugify(title)\nif not _is_strong_slug(slug):\n    slug = hashlib.md5(...).hexdigest()[:8]\nreturn f"{doc_id}#{slug}"'},
    answer=loc("backend/src/chunker.py","_make_parent_id",["_make_parent_id","make_parent_id"])[0],
    grading=loc("backend/src/chunker.py","_make_parent_id",["_make_parent_id","make_parent_id"])[1],
    explanation="弱いslug(ASCII英字なし)はmd5 8桁にフォールバック。")
add(id="q_chunk_003", difficulty="L2", type="mcq", module="backend/src/chunker.py", tags=["parent-doc","bugfix"],
    prompt="日本語見出しで_make_parent_idがmd5ハッシュにフォールバックするのはなぜ?(spec_055)",
    citation={"file":"backend/src/chunker.py","symbol":{"kind":"function","name":"_make_parent_id"},
      "evidence_substring":"parent_id collisions","adr_ref":None,
      "snippet":'JP "## 1. 目的" → "1" weak slug. fall back to md5-hex to avoid parent_id collisions when two JP H2s share the same numeric prefix.'},
    answer={"options":["md5が短い","数字だけのslugで別見出しが衝突するため回避","セキュリティ","ASCII禁止"],"correct_index":1},
    explanation="『1.目的』『1.結論』が共にslug『1』で衝突する問題をmd5で回避。")
add(id="q_chunk_004", difficulty="L2", type="freetext", module="backend/src/chunker.py", tags=["parent-doc","slug"],
    prompt="_is_strong_slug が True を返す条件は？",
    citation={"file":"backend/src/chunker.py","symbol":{"kind":"function","name":"_is_strong_slug"},
      "evidence_substring":"at least one ASCII","adr_ref":None,
      "snippet":'A slug is "strong" iff it contains at least one ASCII [a-z] letter. Empty/numeric-only are weak.'},
    answer={"model_answer":"slugが空でなくASCII英字[a-z]を1文字以上含むとき。",
      "required_keywords":[{"any_of":["ascii","英字","アルファベット","a-z","英文字"]},{"any_of":["1文字","少なくとも","含","一文字"]}],"forbidden_keywords":[]},
    grading={"min_keyword_coverage":0.5}, explanation="ASCII英字を含むslugだけ『強い』。数字/記号のみや空は弱い。")

# ---- vector_store.py ----
add(id="q_vs_001", difficulty="L1", type="mcq", module="backend/src/vector_store.py", tags=["storage"],
    prompt="VectorStoreがベクトルと軸メタデータの保存に使うのは？",
    citation={"file":"backend/src/vector_store.py","symbol":{"kind":"module","name":"module docstring"},
      "evidence_substring":"ChromaDB wrapper","adr_ref":None,
      "snippet":"ChromaDB wrapper for storing Documents with axis metadata."},
    answer={"options":["FAISS","ChromaDB","Pinecone","SQLiteのみ"],"correct_index":1},
    explanation="ChromaDBをローカル永続で使用。軸メタデータも格納し検索前に絞り込む。")
add(id="q_vs_002", difficulty="L2", type="location", module="backend/src/vector_store.py", tags=["live-ingest","spec_056"],
    prompt="チャンク単位で特定docを索引から削除する(live ingestの冪等更新用)メソッドは？（ファイルとシンボル）",
    citation={"file":"backend/src/vector_store.py","symbol":{"kind":"method","name":"VectorStore.delete_doc"},
      "evidence_substring":"def delete_doc(self, doc_id","adr_ref":None,
      "snippet":"def delete_doc(self, doc_id: str) -> int:\n    # spec_056: chunk-level removal for idempotent re-ingest"},
    answer=loc("backend/src/vector_store.py","delete_doc")[0], grading=loc("backend/src/vector_store.py","delete_doc")[1],
    explanation="既存メモ更新はdelete_doc+再ingestで冪等(spec_056)。")
add(id="q_vs_003", difficulty="L2", type="mcq", module="backend/src/vector_store.py", tags=["parent-doc","storage"],
    prompt="Parent Document方式で、childはChromaにembedされるがparentはどこに永続化される?(spec_037)",
    citation={"file":"backend/src/vector_store.py","symbol":{"kind":"module","name":"module docstring"},
      "evidence_substring":"SQLite sidecar","adr_ref":"ADR-023",
      "snippet":"add_chunks() embeds child sub-blocks into Chroma while persisting parents to a SQLite sidecar (parents.db). spec_037 migrates from parents.json to SQLite."},
    answer={"options":["Chromaにparentもembed","SQLiteサイドカー(parents.db)","メモリのみ","localStorage"],"correct_index":1},
    explanation="childだけembed、parentはSQLiteサイドカー。spec_037でparents.jsonから移行。")

# ---- graph.py ----
add(id="q_graph_001", difficulty="L1", type="mcq", module="backend/src/graph.py", tags=["graphrag"],
    prompt="KnowledgeGraphはどのライブラリのどんなグラフ型で構築される？",
    citation={"file":"backend/src/graph.py","symbol":{"kind":"method","name":"KnowledgeGraph.__init__"},
      "evidence_substring":"nx.DiGraph","adr_ref":"ADR-024",
      "snippet":"def __init__(self, graph: nx.DiGraph): ...  # networkx>=3.0. source->target means source.refs contains target."},
    answer={"options":["Neo4jの無向グラフ","networkxの有向グラフ(DiGraph)","Chromaのグラフ索引","自前隣接リスト"],"correct_index":1},
    explanation="networkxのDiGraph。refs:からsource→targetの有向辺。")
add(id="q_graph_002", difficulty="L2", type="location", module="backend/src/graph.py", tags=["graphrag"],
    prompt="あるノードから指定ホップ内の隣接ノードをBFSで集めるメソッドは？（ファイルとシンボル）",
    citation={"file":"backend/src/graph.py","symbol":{"kind":"method","name":"KnowledgeGraph.neighbors_within_hop"},
      "evidence_substring":"def neighbors_within_hop","adr_ref":None,
      "snippet":"def neighbors_within_hop(self, doc_id, hop=1, max_neighbors=10):\n    # BFS over the DiGraph"},
    answer=loc("backend/src/graph.py","neighbors_within_hop")[0], grading=loc("backend/src/graph.py","neighbors_within_hop")[1],
    explanation="search(graph_expand=True)がtop hitsのこれを呼び隣接docをマージ。")
add(id="q_graph_003", difficulty="L2", type="fill_blank", module="backend/src/search.py", tags=["graphrag"],
    prompt="グラフ拡張で隣接ノードをマージする際、元ヒットのスコアに掛ける減衰係数は？\n    score = source.score × ____",
    citation={"file":"backend/src/search.py","symbol":{"kind":"method","name":"SearchEngine.search"},
      "evidence_substring":"0.7","adr_ref":"ADR-024",
      "snippet":"merge 1-hop refs neighbours of the top 5 hits with a 0.7x score decay relative to their source."},
    answer={"accepted":["0.7","0.7倍","x0.7","×0.7"]}, grading={"casefold":True},
    explanation="隣接は元の0.7倍スコアで追加され再ソート。")
add(id="q_graph_004", difficulty="L4", type="mcq", module="docs/adr/ADR-024-graphrag-retrieval-expansion.md", tags=["graphrag","design"],
    prompt="グラフ層にNeo4jでなくin-processのnetworkxを選んだ理由は?(ADR-024)",
    citation={"file":"docs/adr/ADR-024-graphrag-retrieval-expansion.md","symbol":{"kind":"section","name":"Alternatives"},
      "evidence_substring":"local-first ethos","adr_ref":"ADR-024",
      "snippet":"Neo4j rejected: sidecar daemon for <=10k edges doesn't fit the local-first ethos. In-process networkx chosen: zero extra processes."},
    answer={"options":["networkxが高速","別プロセス不要でlocal-first方針に合い<=10k辺に十分","Neo4jは日本語非対応","Chroma統合済み"],"correct_index":1},
    explanation="数千〜1万辺にdaemonは過剰。プロセス追加ゼロのnetworkxがlocal-firstに合致。")

# ---- embedder.py ----
add(id="q_embed_001", difficulty="L1", type="mcq", module="backend/src/embedder.py", tags=["embedder"],
    prompt="EmbedderがProtocolの背後に持つ3バックエンドは？",
    citation={"file":"backend/src/embedder.py","symbol":{"kind":"module","name":"module docstring"},
      "evidence_substring":"Gemini / Ollama / Dummy","adr_ref":"ADR-026",
      "snippet":"Embedder backends (Gemini / Ollama / Dummy) behind a Protocol."},
    answer={"options":["OpenAI/Cohere/HF","Gemini/Ollama/Dummy","Claude/Gemini/GPT","FAISS/Chroma/Pinecone"],"correct_index":1},
    explanation="Gemini(既定)/Ollama(オンプレ)/Dummy(キー無し)をProtocolで抽象化。")
add(id="q_embed_002", difficulty="L2", type="location", module="backend/src/embedder.py", tags=["embedder","factory"],
    prompt="設定に応じて適切なEmbedder実装を選んで返すファクトリ関数は？（ファイルとシンボル）",
    citation={"file":"backend/src/embedder.py","symbol":{"kind":"function","name":"make_embedder"},
      "evidence_substring":"def make_embedder","adr_ref":None,
      "snippet":"def make_embedder(cfg=None) -> Embedder:\n    # picks Gemini/Ollama/Dummy based on config/keys"},
    answer=loc("backend/src/embedder.py","make_embedder")[0], grading=loc("backend/src/embedder.py","make_embedder")[1],
    explanation="configと利用可能キーから選択。キー無しはDummyEmbedder。")
add(id="q_embed_003", difficulty="L4", type="mcq", module="backend/src/embedder.py", tags=["embedder","design"],
    prompt="GEMINI_API_KEY未設定時にDummyEmbedder(ハッシュ由来の決定的ベクトル)へフォールバックする狙いは？",
    citation={"file":"backend/src/embedder.py","symbol":{"kind":"module","name":"module docstring"},
      "evidence_substring":"without hitting the network","adr_ref":None,
      "snippet":"falls back to DummyEmbedder — deterministic hash-derived 768-dim vectors so downstream paths can be exercised in CI / offline dev without hitting the network."},
    answer={"options":["本番でもDummyで十分","キー無し/CI/オフラインでも下流コードパスを動作確認できるように","Geminiコストを無くす","セキュリティ要件"],"correct_index":1},
    explanation="DUMMYモードでキー無しでもUI・検索を通せる。CI/オフライン用。")

# ---- rag.py ----
add(id="q_rag_001", difficulty="L1", type="location", module="backend/src/rag.py", tags=["rag","context"],
    prompt="検索ヒットのparent本文を連結してLLMに渡すコンテキストを組み立てる関数は？（ファイルとシンボル）",
    citation={"file":"backend/src/rag.py","symbol":{"kind":"function","name":"build_context"},
      "evidence_substring":"def build_context","adr_ref":"ADR-017",
      "snippet":"def build_context(results, max_chars=8000):\n    # concatenate parent bodies, trimmed"},
    answer=loc("backend/src/rag.py","build_context",["build_context","_format_context"])[0],
    grading=loc("backend/src/rag.py","build_context",["build_context","_format_context"])[1],
    explanation="parent全文を連結しmax_charsでトリムしてプロンプトへ。")
add(id="q_rag_002", difficulty="L2", type="fill_blank", module="backend/src/rag.py", tags=["rag","gemini"],
    prompt="GeminiBackendの既定モデル名(DEFAULT_MODEL)を答えよ。",
    citation={"file":"backend/src/rag.py","symbol":{"kind":"class","name":"GeminiBackend"},
      "evidence_substring":'DEFAULT_MODEL = "gemini-2.5-flash"',"adr_ref":"ADR-031",
      "snippet":'class GeminiBackend:\n    DEFAULT_MODEL = "gemini-2.5-flash"'},
    answer={"accepted":["gemini-2.5-flash",'"gemini-2.5-flash"']}, grading={"casefold":True},
    explanation="gemini-2.5-flashをtemperature=0.2で使用。")
add(id="q_rag_003", difficulty="L1", type="mcq", module="backend/src/rag.py", tags=["rag","backends"],
    prompt="GenerationBackend Protocolに実装された4バックエンドは？",
    citation={"file":"backend/src/rag.py","symbol":{"kind":"module","name":"backends"},
      "evidence_substring":"class DummyGenerationBackend","adr_ref":"ADR-031",
      "snippet":"class ClaudeBackend: ...\nclass GeminiBackend: ...\nclass OllamaBackend: ...\nclass DummyGenerationBackend: ..."},
    answer={"options":["Claude/GPT-4/Gemini/Llama","Claude/Gemini/Ollama/Dummy","Gemini/Ollama/FAISS/Dummy","Claude/Ollama/Dummyの3つ"],"correct_index":1},
    explanation="Claude(既定)/Gemini/Ollama/Dummy。autoモードで実行時選択。")
add(id="q_rag_004", difficulty="L4", type="mcq", module="docs/adr/ADR-031-gemini-generation-backend.md", tags=["rag","design"],
    prompt="v0.9.1でGemini生成バックエンドとautoモードを追加した主な動機は?(ADR-031)",
    citation={"file":"docs/adr/ADR-031-gemini-generation-backend.md","symbol":{"kind":"section","name":"Context"},
      "evidence_substring":"already holding a Gemini key","adr_ref":"ADR-031",
      "snippet":"Many users come into the Cowork plugin already holding a Gemini key (the embedder requires it). google-generativeai is already a dependency, so adding Gemini generation costs zero new packages."},
    answer={"options":["GeminiがClaudeより高性能","埋め込み用にGeminiキーを既に持つ人が追加依存ゼロで生成も賄えるため","Anthropic廃止","オフライン化"],"correct_index":1},
    explanation="2つ目のキー無しで回答を得られるonboarding改善。")
add(id="q_rag_005", difficulty="L3", type="dataflow", module="backend/src/rag.py", tags=["rag","pipeline"],
    prompt="RAGPipeline.answerが回答を返すまでの主要ステップを順に並べよ。",
    citation={"file":"backend/src/rag.py","symbol":{"kind":"method","name":"RAGPipeline.answer"},
      "evidence_substring":"build_context","adr_ref":None,
      "snippet":"results = self._engine.search(question)\ncontext = build_context(results)\ntext = self._call_generation(system, messages)\n# parse [N] citations -> cited_ids"},
    answer={"sequence":["search","build_context","generate","citation"]},
    grading={"mode":"subsequence","pass_threshold":0.75,"aliases":[["search","retrieve","検索"],["build_context","context","コンテキスト","文脈"],["generate","生成","llm"],["citation","引用","cited_ids","出典"]]},
    pool=["build_context","citation","search","generate"],
    explanation="検索→build_contextで連結→LLM生成→[N]引用パースしてcited_ids/sources。")

# ---- mcp_server ----
add(id="q_mcp_001", difficulty="L1", type="mcq", module="mcp_server/server.py", tags=["mcp"],
    prompt="MCPサーバが使うトランスポートは？",
    citation={"file":"mcp_server/server.py","symbol":{"kind":"module","name":"module docstring"},
      "evidence_substring":"stdio transport","adr_ref":None,
      "snippet":"axis_knowledge_rag MCP server (stdio transport, FastMCP-based)."},
    answer={"options":["HTTP/SSE","stdio","WebSocket","gRPC"],"correct_index":1},
    explanation="FastMCPベースのstdio。python -m mcp_serverで起動。")
add(id="q_mcp_002", difficulty="L2", type="location", module="mcp_server/server.py", tags=["mcp","live-ingest"],
    prompt="メモを受け取りbackend経由のlive ingestを起動するMCPツール関数は？（ファイルとシンボル）",
    citation={"file":"mcp_server/server.py","symbol":{"kind":"function","name":"axis_ingest_memo"},
      "evidence_substring":"async def axis_ingest_memo","adr_ref":None,
      "snippet":"async def axis_ingest_memo(params: IngestInput) -> str:\n    # spec_056: triggers live ingest via backend"},
    answer=loc("mcp_server/server.py","axis_ingest_memo")[0], grading=loc("mcp_server/server.py","axis_ingest_memo")[1],
    explanation="_live_ingest_via_backendを呼びリビルド無しで約1秒で検索可能に(spec_056)。")

# ---- frontend ----
add(id="q_fe_001", difficulty="L1", type="location", module="frontend/src/lib/api.ts", tags=["frontend"],
    prompt="フロントがFastAPIを叩くAPIクライアント(search/answer/axes等)はどのファイル？",
    citation={"file":"frontend/src/lib/api.ts","symbol":{"kind":"const","name":"api"},
      "evidence_substring":"export const api =","adr_ref":None,
      "snippet":"export const api = {\n  axes: () => jsonFetch('/api/axes'),\n  search: (body) => jsonFetch('/api/search', {...}),\n};"},
    answer=loc("frontend/src/lib/api.ts","api",["api","jsonFetch"],0.7)[0],
    grading=loc("frontend/src/lib/api.ts","api",["api","jsonFetch"],0.7)[1],
    explanation="lib/api.tsのapiオブジェクト。型はbackend/src/schemas.pyをミラー。")
add(id="q_fe_002", difficulty="L2", type="mcq", module="frontend/src/lib/citations.ts", tags=["frontend","citation"],
    prompt="citations.tsが[N]マーカーをパースする際、コードフェンスやインラインコード内の[1]をどう扱う?(spec_039)",
    citation={"file":"frontend/src/lib/citations.ts","symbol":{"kind":"function","name":"buildSkipRanges"},
      "evidence_substring":"code fences","adr_ref":None,
      "snippet":"Markers inside Markdown code fences or inline code spans are preserved as literal text (spec_039) — arr[1] in a code block is not a citation."},
    answer={"options":["引用として扱う","リテラル文字として扱い引用にしない(skip range)","エラー","全削除"],"correct_index":1},
    explanation="コード領域をskip rangeで除外。Python側_build_skip_rangesをミラー。")
add(id="q_fe_003", difficulty="L1", type="fill_blank", module="frontend/src/lib/api.ts", tags=["frontend","config"],
    prompt="API_BASEのデフォルト値(環境変数未設定時)を答えよ。",
    citation={"file":"frontend/src/lib/api.ts","symbol":{"kind":"const","name":"API_BASE"},
      "evidence_substring":"http://localhost:8000","adr_ref":None,
      "snippet":'const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";'},
    answer={"accepted":['"http://localhost:8000"',"http://localhost:8000"]}, grading={"casefold":True},
    explanation="未設定時はhttp://localhost:8000(ローカルFastAPI)。")

# ---- design L4 ----
add(id="q_design_001", difficulty="L4", type="mcq", module="docs/adr/ADR-017-parent-document-retrieval.md", tags=["design","parent-doc"],
    prompt="Parent Document Retrievalで『parentもchildも両方embed』案(Hierarchical Embeddings)が却下された理由は?(ADR-017)",
    citation={"file":"docs/adr/ADR-017-parent-document-retrieval.md","symbol":{"kind":"section","name":"Alternatives"},
      "evidence_substring":"ストレージコスト 2 倍","adr_ref":"ADR-017",
      "snippet":"(c) Hierarchical Embeddings 却下: ストレージコスト 2 倍 + 埋め込みAPIコスト2倍。検索フローが複雑化。"},
    answer={"options":["精度が下がる","ストレージと埋め込みAPIが2倍になり検索フローも複雑化","Chroma非対応","日本語不可"],"correct_index":1},
    explanation="childのみembed、parentはsidecar。両方embedはコスト2倍・複雑化で不利。")
add(id="q_design_002", difficulty="L4", type="freetext", module="README.md", tags=["design","philosophy"],
    prompt="axisがLangChain/LlamaIndexを使わず自前実装している利点を、READMEの主張に沿って説明せよ。",
    citation={"file":"README.md","symbol":{"kind":"section","name":"特徴"},
      "evidence_substring":"依存が薄く、内部挙動が読める","adr_ref":None,
      "snippet":"LangChain / LlamaIndex 不使用、自前実装 — 依存が薄く、内部挙動が読める。薄いラッパで構成。"},
    answer={"model_answer":"依存が薄く内部挙動を読んで理解・デバッグできる。薄いラッパで学習・保守しやすい。",
      "required_keywords":[{"any_of":["依存","ライブラリ","dependency"]},{"any_of":["読める","理解","挙動","追える","把握","デバッグ","透明"]}],"forbidden_keywords":[]},
    grading={"min_keyword_coverage":0.5}, explanation="薄い依存=内部が読める=学習・デバッグ・改造しやすい。axisのコア哲学。")

# ---- conversational rag / citations / loader / integrity / conversation ----
add(id="q_rewrite_001", difficulty="L2", type="mcq", module="backend/src/question_rewriter.py", tags=["conversational-rag"],
    prompt="follow-up質問をstandaloneクエリに書き換えた後、その書き換え後の文は何に使われる？",
    citation={"file":"backend/src/question_rewriter.py","symbol":{"kind":"module","name":"module docstring"},
      "evidence_substring":"used as the retrieval query","adr_ref":"ADR-018",
      "snippet":"The standalone form is used as the retrieval query; the original question is still used for answer generation."},
    answer={"options":["生成にも検索にも書き換え後","検索に使い、生成には元の質問","ログだけ","表示だけ"],"correct_index":1},
    explanation="standaloneは検索用。生成には元質問を渡しユーザーの言い回しを保つ。")
add(id="q_rewrite_002", difficulty="L4", type="mcq", module="backend/src/question_rewriter.py", tags=["conversational-rag","robustness"],
    prompt="rewrite_questionがAPIキー無し・ネットワークエラー等で失敗したときの挙動は？",
    citation={"file":"backend/src/question_rewriter.py","symbol":{"kind":"function","name":"rewrite_question"},
      "evidence_substring":"fall back to the original question","adr_ref":"ADR-018",
      "snippet":"All failures (no API key, network error, quota, oversized output) fall back to the original question so chat UX never blocks."},
    answer={"options":["例外でチャット停止","元の質問にフォールバックしUXを止めない","空文字で検索","前回回答を再利用"],"correct_index":1},
    explanation="書き換えは最適化。失敗時は元質問で検索しUXをブロックしない。")
add(id="q_cite_001", difficulty="L1", type="location", module="backend/src/_citations.py", tags=["citation"],
    prompt="RAG出力の[N]引用マーカーをパース・検証する関数は？（ファイルとシンボル）",
    citation={"file":"backend/src/_citations.py","symbol":{"kind":"function","name":"parse_and_validate_citations"},
      "evidence_substring":"def parse_and_validate_citations","adr_ref":None,
      "snippet":"def parse_and_validate_citations(text, n_sources, ...):\n    # normalize [1,2]->[1][2], strip out-of-range, skip code spans"},
    answer=loc("backend/src/_citations.py","parse_and_validate_citations",["parse_and_validate_citations","extract_citations"],0.6)[0],
    grading=loc("backend/src/_citations.py","parse_and_validate_citations",["parse_and_validate_citations","extract_citations"],0.6)[1],
    explanation="マーカー正規化・範囲外除去・コード領域スキップ。フロントcitations.tsがミラー。")
add(id="q_cite_002", difficulty="L2", type="mcq", module="backend/src/_citations.py", tags=["citation","robustness"],
    prompt="LLMが出典数を超える範囲外のN(例:出典3件なのに[5])を出した場合、_citationsはどうする？",
    citation={"file":"backend/src/_citations.py","symbol":{"kind":"module","name":"module docstring"},
      "evidence_substring":"strips markers that reference an N out of range","adr_ref":None,
      "snippet":"strips markers that reference an N out of range (the LLM occasionally hallucinates indices beyond the source count)"},
    answer={"options":["そのまま表示","範囲外マーカーを除去しユーザーに漏らさない","エラー","出典を自動増加"],"correct_index":1},
    explanation="ハルシネートされた範囲外indexは見せず、範囲内だけ残す。")
add(id="q_loader_001", difficulty="L1", type="location", module="backend/src/loader.py", tags=["loader"],
    prompt="YAML frontmatter付きMarkdown1ファイルを読み込みDocumentに変換する関数は？（ファイルとシンボル）",
    citation={"file":"backend/src/loader.py","symbol":{"kind":"function","name":"load_document"},
      "evidence_substring":"def load_document","adr_ref":None,
      "snippet":"def load_document(path, normalizer=None) -> Document:\n    # parse YAML frontmatter + body via `frontmatter`"},
    answer=loc("backend/src/loader.py","load_document",["load_document","load_directory"],0.6)[0],
    grading=loc("backend/src/loader.py","load_document",["load_document","load_directory"],0.6)[1],
    explanation="load_documentが単一、load_directoryが一括。Day1の主成果物。")
add(id="q_integ_001", difficulty="L2", type="mcq", module="backend/src/integrity.py", tags=["integrity"],
    prompt="integrity.pyの主な役割は？",
    citation={"file":"backend/src/integrity.py","symbol":{"kind":"module","name":"module docstring"},
      "evidence_substring":"points to an existing","adr_ref":None,
      "snippet":"Reference integrity checker. Validates that every refs entry points to an existing document id, surfaces orphans / cycles."},
    answer={"options":["ベクトル次元検証","各refsの参照先実在を検証しorphan/cycleを報告","APIキー検証","Markdown文法検証"],"correct_index":1},
    explanation="refsの壊れた参照・孤立・循環を検出。参照健全性チェック専用。")
add(id="q_conv_001", difficulty="L2", type="mcq", module="backend/src/conversation.py", tags=["conversational-rag","storage"],
    prompt="ConversationStore Protocolの3実装は？",
    citation={"file":"backend/src/conversation.py","symbol":{"kind":"module","name":"module docstring"},
      "evidence_substring":"RedisStore","adr_ref":"ADR-022",
      "snippet":"Three implementations: MemoryStore (in-memory), SqliteStore (file-backed, default v0.8+), RedisStore (optional, multi-host)."},
    answer={"options":["Memory/File/S3","Memory/Sqlite/Redis","Sqlite/Postgres/Redis","Memory/Chroma/Redis"],"correct_index":1},
    explanation="Memory/Sqlite/Redis。make_conversation_storeがbackendで選択、失敗時Memoryへ。")
add(id="q_conv_002", difficulty="L4", type="mcq", module="backend/src/conversation.py", tags=["conversational-rag","design"],
    prompt="v0.8+で会話履歴のデフォルトbackendをSqliteStoreにした理由は？",
    citation={"file":"backend/src/conversation.py","symbol":{"kind":"class","name":"SqliteStore"},
      "evidence_substring":"Survives process restarts","adr_ref":"ADR-022",
      "snippet":"SqliteStore — file-backed sqlite3 (WAL mode), default for v0.8+. Survives process restarts and is safe across uvicorn workers."},
    answer={"options":["メモリより高速","再起動後も履歴が残り複数uvicorn worker間で安全","Redis廃止","暗号化"],"correct_index":1},
    explanation="WALのsqlite3で永続化＆マルチワーカー安全。Memoryは揮発・単一プロセス向け。")


def _get_axis_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=AXIS_REPO, text=True
        ).strip()
    except Exception:
        return "unknown"


def _embed_sources() -> int:
    """Embed real source code into each citation that points at a resolvable symbol.

    Returns the number of citations successfully resolved.
    """
    try:
        from backend.src.anchor.resolver import resolve_citation as _rc
    except ImportError as exc:
        print(f"Warning: cannot import resolver ({exc}), skipping source embedding")
        return 0

    resolved = 0
    for q in Q:
        cit = q.get("citation", {})
        if not cit:
            continue
        try:
            result = _rc(AXIS_REPO, cit)
            if result.get("found"):
                cit["source"] = result["source"]
                cit["start_line"] = result["start"]
                cit["end_line"] = result["end"]
                resolved += 1
        except Exception:
            pass
    return resolved


resolved_count = _embed_sources()
axis_commit = _get_axis_commit()
print(f"source embedding: {resolved_count}/{len(Q)} citations resolved (axis HEAD={axis_commit})")

data = {
    "meta": {
        "repo": REPO,
        "repo_commit": REPO_COMMIT,
        "generator": "claude (cowork chat)",
        "schema_version": 1,
        "difficulty_levels": {"L1": "場所当て", "L2": "役割・振る舞い", "L3": "データフロー", "L4": "設計意図"},
        "axis_commit": axis_commit,
    },
    "questions": Q,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {len(Q)} questions -> {OUT}")
