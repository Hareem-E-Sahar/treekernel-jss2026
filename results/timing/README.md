# Kernel timing

*Rerun 2026-10-12 on the revised trees (readable labels, statements and primitive types kept; see `docs/tree_variants.md`). The first run (2026-10-11, old trees) is summarised at the end.*

Machine: AMD Ryzen 7 8845HS (8 cores / 16 threads), 13 GB RAM, OpenJDK 21, KeLP 2.2.4-SNAPSHOT (see `third_party/README.md`). Normal desktop use in the background (browser, editor).

Setup:
- 100 queries (`data/pools/queries.tsv`, uniform over the 14,780 true positives, seed 20261011).
- Each query against 500 random other true positives: 50,000 evaluations per run, 16 threads.
- Kernels: STK λ=0.4, SSTK λ=0.4, PTK λ=0.4 μ=0.4, unnormalised. Normalisation needs one extra self-kernel per function (14,780 evaluations, about 10 s).

Reproduce:

```bash
kernels/run_timing.sh 500 600 16 | tee results/timing/summary.log
python3 -I eval/timing_report.py results/timing data/trees data/pools/queries.tsv
```

Files:
- `summary.log`: harness output.
- `<variant>_<kernel>.tsv`: one row per pair (tree sizes, nanoseconds, kernel value).
- `report.txt`: the full table, including the effect of capping tree size.

## Predicted wall time for one full retrieval run

One full run is 100 queries × 14,779 candidates = 1.48M evaluations.

- "Model" fits log(time) = a + b·log(n_query · n_candidate) on the sampled pairs and sums it over the real sizes of all 1.48M pairs.
- "Sample" is the plain extrapolation of the 50,000-pair throughput.

| Variant | STK model / sample | SSTK model / sample | PTK model / sample |
|---|---|---|---|
| A raw | 1.4 / 1.6 min | 1.4 / 1.6 min | 4.3 / 5.0 min |
| B pruned | 0.4 / 0.4 min | 0.4 / 0.4 min | 1.9 / 2.4 min |
| C abstracted | 0.9 / 1.2 min | 0.9 / 1.1 min | 1.3 / 1.8 min |
| D abstracted + API names | 0.7 / 0.9 min | 0.7 / 0.9 min | 1.2 / 1.5 min |

## How reliable these numbers are

**The model is right about tree sizes.** Two complete runs were done (variant C, PTK, all 100 queries × all 14,680 non-query true positives = 1,468,000 evaluations):

| Date | Predicted (model / sample) | Actual |
|---|---|---|
| 2026-10-11 (old trees) | 3.2 / 3.8 min | 3.5 min |
| 2026-10-12 (new trees) | 1.3 / 1.8 min | 2.8 min |

**The machine's speed is not stable.** In the 2026-10-12 complete run, pairs of the *same size* took 1.5–1.7× longer than in the short sample, uniformly across all size ranges. The very largest pairs, which the sample never contained, explain only 0.6% of the time. So the miss comes from the laptop running slower during a long sustained run (heat, power management or background load), not from the model.

The same effect shows between days. The old and new variant-A trees time the same when run back to back (subtree kernel 1.02 vs 1.00 ms per pair, PTK 3.6–3.9 vs 3.8–3.9 ms). Yet the 2026-10-11 grid measured 1.51 ms for the same kernel. Label length has no measurable effect on speed.

**Planning rule:** budget up to **2× the short-sample estimates** for long runs on this laptop.

## Observations

- Cost per pair grows roughly with n_query × n_candidate. The fitted exponent is 0.98–1.06 for PTK, 0.81–0.89 for STK and SSTK on A, C and D, and 0.67 for STK and SSTK on B.
- Abstraction (C, D) makes STK and SSTK slower than pruning alone (B), because renaming everything to `ID`/`TYPE` creates many more matching productions. For PTK it's the other way round, because C and D trees are smaller.
- The time per pair is heavy-tailed: the median is 0.13–0.9 ms, the 99th percentile 3–37 ms. Capping tree size at 500 nodes would cut PTK on raw trees from 4.3 to 0.4 min, but drop 28% of the corpus for A. A cap changes what is evaluated, so it's a design decision, not a free speed-up.
- **Memory is the binding constraint, not time.** Holding all 14,780 variant-C trees used 4.4 GB of memory (measured 2026-10-11). Raw trees (A) are about 2.5× larger. Full runs on A and B need candidates loaded in batches, or more RAM.
- The harness skips query-vs-query pairs (100 × 99 = 9,900). The real retrieval run must include them, because other queries are valid candidates too.

## Implications for the plan

- 100 queries × all true positives: about 0.4–5 min per configuration, or up to about 10 min with the 2× rule.
- **Full tuning grid.** Per variant there are 4 STK + 6 SSTK + 9 PTK settings, 76 configurations in total. Over 100 queries this sums to about 110 min with the model estimates (A 53, B 21, C 21, D 18 min), or up to about 3.5 h with the 2× rule. It scales linearly with the number of tuning queries.
- **Adding all ~58,000 false positives** (about 7.3M evaluations) costs about 5× these numbers.

## First run (2026-10-11, old trees): superseded

The first grid used the previous trees (hex-encoded labels, statements collapsed, primitive types dropped). It measured PTK at 9.3 min on A, 4.2 on B, 3.2 on C and 2.7 on D (model estimates), and STK/SSTK at 0.5–2.1 min. B–D trees are now about 7–9% larger, but the 2026-10-12 numbers are lower overall mainly because the machine ran faster that day (see above).
