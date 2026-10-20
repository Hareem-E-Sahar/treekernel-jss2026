# RQ4: complementarity and fusion

Built by `eval/tune_fusion.py` and `eval/fusion.py`; complementarity by `eval/complementarity.py`. Tables: `results/eval/tables.md` § RQ4.

- `rq1_PTK/`: D PTK (λ 0.4, μ 0.6) + BM25, W tuned for RQ1 (mean MAP over types).
- `rq2_STK/`: D STK (λ 0.8) + BM25, W tuned for RQ2 (MAP@R). STK is D's best kernel on RQ2.

Each holds `tuning.tsv` (objective per W on the 50 tuning queries), `tuning_runs/`, the selected `wsum_w<W>/` and `rrf/`, all evaluated on the 584 evaluation queries.

Methods:
- Weighted sum: W·TK + (1 − W)·BM25/max, TK = normalised kernel score in [0, 1], BM25 divided by the query's maximum score. W ∈ {0, 0.1, …, 1}, ties broken toward the larger W.
- RRF: Σ 1/(60 + rank), ranks over the corpus with ties averaged; no parameter.
- Sanity check: W = 0 reproduces BM25, W = 1 reproduces the kernel.

Findings:
- RQ1: W = 0.8. Fusion beats both components: mean MAP 0.957 (PTK 0.926, BM25 0.888), MT3 0.810 (PTK 0.654, BM25 0.630). RRF helps less (0.939) and loses to PTK on ST3.
- RQ2: W = 0.0, i.e. adding the kernel never helps BM25 on the tuning queries; RRF hurts (0.336 vs 0.477).
- Complementarity (D PTK vs BM25, MT3): of the clones ranked within the top R, 46% are found by both, 21% only by PTK, 18% only by BM25. On the functional set the kernel finds 8% that BM25 misses, but BM25 finds 36% that the kernel misses.

## CodeBERT (added 2026-10-19)

PTK + fine-tuned CodeBERT (W=0.6): RQ1 mean 0.955, MT3 0.796, significantly better than both components. That is close to PTK + BM25 (0.957 / 0.810). STK + CodeBERT ft for RQ2: W=0.1 gives 0.487, the same as CodeBERT alone. Output: `rq1_PTK_codebert/`, `rq2_STK_codebert/`. Details: `results/codebert/README.md`.
