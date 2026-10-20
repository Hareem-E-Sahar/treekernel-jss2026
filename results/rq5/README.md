# RQ5: cost

Run by `scripts/run_timing.sh` (log `results/rq5_run.log`) on 2026-10-18, after all other experiments, with no other experiment running (the Elasticsearch node was up but idle during the kernel runs). Machine: AMD Ryzen 7 8845HS laptop (8 cores / 16 threads), 13 GB RAM, OpenJDK 21. Tables: `results/eval/tables.md` § RQ5.

Tree kernels (`tree_kernels.tsv`; columns variant, kernel, setting, queries, wall seconds, max RSS in KB):
- RetrievalRunner, 1 thread, -Xmx3g, each tuned configuration twice: with 0 queries (`data/pools/timing_empty.tsv`: JVM start, reading the corpus trees, self-similarities) and with 20 queries (`data/pools/timing_queries.tsv`, seed 20261018).
- Per query = (20-query time − 0-query time) / 20, one query against all 14,678 other methods. Runs in `runs/`.
- Peak RSS is reported as measured; with a fixed -Xmx it reflects the JVM's heap growth more than the data, so treat it as an upper bound only.

BM25 (`bm25_index.json`, `runs/bm25_timing_queries/timing.tsv`, `bm25_jvm.json`): a fresh index `bcb_timing` (deleted afterwards), the same 20 queries; `es_took_ms` = Elasticsearch's own time, `client_ms` = including returning all 14,679 scores to Python. ES heap: -Xms2g -Xmx2g.

Preparation (`tree_building.tsv`, `prep/time_trees.py`): tree-sitter parse, each variant and the BM25 tokens for the 14,679 methods, in Python.

Findings:
- Per query: BM25 ≈ 0.1 s; tree kernels 0.5 s (B STK/SSTK) to 14.8 s (A PTK); D PTK, the best RQ1 configuration, 3.4 s. One-off cost 10–51 s for the kernels vs a 3.3 s index build.
- Cost follows the number of matching node pairs, not tree size alone: B (names kept as labels) is the fastest for STK/SSTK, presumably because few productions match (not measured); C (all names → ID) is slower than D despite smaller trees. PTK costs 1.7× (C) to 11× (B) the time of STK on the same variant.

## CodeBERT (added 2026-10-19)

1 thread: model load 3.3 s; 0.37 s per query (encode the query, then cosine against the stored embeddings); corpus encoding estimated at about 6,200 s one method at a time (1,503 s on 8 threads in batches of 32). Fine-tuning the 5 fold models: 6.6 h on 8 threads. Output: `codebert.json`.

## Enlarged corpus (E5, added 2026-10-19)

`scripts/run_timing_e5.sh` → `results/rq5/e5/`. Same protocol on the 72,782-method E5 corpus (main + 58,103 false positives):
variant D tuned kernels, BM25 (fresh index `bcb_timing_e5`, deleted afterwards) and CodeBERT, one thread, the same 20 timing queries.
Elasticsearch ran only during the BM25 step.

| | Main (14,679), s/query | Enlarged (72,782), s/query | Growth |
|---|---|---|---|
| D STK | 1.5 | 6.7 | ×4.6 |
| D SSTK | 1.5 | 7.0 | ×4.6 |
| D PTK | 3.4 | 15.3 | ×4.5 |
| BM25 (incl. returning all scores; `took` 0.74 s) | 0.12 | 0.81 | ×6.8 |
| CodeBERT (encode + cosine) | 0.37 | 0.40 | ×1.1 |

- Set-up for the kernels (0-query run): STK 43 s, SSTK 45 s, PTK 83 s.
- BM25 index: 14.8 s, 64 MB.
- CodeBERT corpus encoding, estimated one method at a time: about 19,600 s (269 ms per method on this sample).
- The corpus is 5× larger. Kernel per-query time grows roughly linearly with it. BM25 grows more than linearly here because
  every query returns all 72,782 scores. CodeBERT's per-query cost is dominated by encoding the query.
- Figure: `paper/figures/rq5_time_e5.pdf`.
