# BM25 (Elasticsearch)

Elasticsearch 8.19.15 (the user's copy in `elasticsearch-8.19.15-linux-x86_64/`, run with its own config, data
and logs in `third_party/es/`; `scripts/es_start.sh`, localhost:9201, 2 GB heap). One shard, so IDF is corpus-wide.
BM25 k1 = 1.2, b = 0.75 (Elasticsearch defaults; not tuned, decided 2026-10-18).

- Tokens: `bm25/code_tokens.py`: word-like tokens of the method source (keywords, identifiers, numbers, words in
  literals and comments; punctuation dropped); identifiers also split on camelCase/snake_case/digits, all lowercased.
  Indexed with a whitespace tokenizer + lowercase filter.
- Query `all` (primary): every query token is a term; a term occurring n times in the query has boost n.
- Query `mlt` (secondary): More Like This with Elasticsearch's defaults, as in the user's earlier study.
- Every corpus method gets a score (non-matching = 0), written in RetrievalRunner's format, so
  `eval/evaluate.py` evaluates BM25 exactly like the kernels.

Runs: `bm25/run_bm25.py index bcb_main data/trees_main/D.tsv data/trees_main/source.tsv`, then
`bm25/run_bm25.py query bcb_main data/pools/eval_queries.tsv results/bm25/eval/all [--mode mlt]`
(also `tuning/` on the tuning queries, used for the RQ4 fusion weight).

Check (2026-10-18): six query–document scores recomputed by hand with the BM25 formula agree up to the constant
factor k1 + 1 = 2.2 that Lucene includes (rank-preserving), with < 1% deviations from Lucene's compressed
document lengths.
