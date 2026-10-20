# Evaluation runs (2026-10-17/18)

584 evaluation queries (`data/pools/eval_queries.tsv`) against the reduced corpus (`data/trees_main/<V>.tsv`, 14,679 methods); KeLP as is.
Run: `scripts/run_eval.sh 14 V:KERNEL:λ:μ ...` (log: `run.log`, about 2.5 h for the 18 runs). Each run is evaluated with
`eval/evaluate.py RUN --syntactic data/pools/syntactic_<T>.tsv:<T> (×5) --functional data/pools/functional.tsv`.
Tables by research question: `eval/eval_tables.py` → `tables.md`.

- Tuned settings for every variant × kernel (12 runs; from `results/grid/<V>/README.md`).
- Default setting λ = μ = 0.4 for D and C only (6 runs; secondary RQ3 table, effect of tuning). A and B defaults skipped for now (2026-10-17).

Open point: B's STK and SSTK score highest on the functional set (MAP@R ≈ 0.25 vs 0.15–0.19 for all other runs, A included). Not yet examined.
