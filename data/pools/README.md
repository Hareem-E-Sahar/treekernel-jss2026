# Query sets

Drawn by `prep/sample_queries.py` on 2026-10-14 (seed 20261014; per-type evaluation seeds 20261015–20261019).
See `PLAN.md` §4.2 and `docs/evaluation_design.md`.

| Set | Queries | Pool it was drawn from | Pattern-task queries | Tasks represented | Median clones of the type per query |
|---|---|---|---|---|---|
| `syntactic_T1.tsv` | 100 | 3,793 methods with a T1 clone, minus tuning queries | 11 | 24 | 3 |
| `syntactic_T2.tsv` | 100 | 1,024 methods with a T2 clone, minus tuning queries | 8 | 21 | 1 |
| `syntactic_VST3.tsv` | 100 | 2,019 methods with a VST3 clone, minus tuning queries | 7 | 24 | 2 |
| `syntactic_ST3.tsv` | 100 | 4,700 methods with a ST3 clone, minus tuning queries | 19 | 24 | 3 |
| `syntactic_MT3.tsv` | 100 | 7,782 methods with a MT3 clone, minus tuning queries | 10 | 20 | 8 |
| `functional.tsv` | 100 | all 14,780 true positives (pilot sample, seed 20261011) | 5 | 24 | – |
| `tuning.tsv` | 50 | 10 per type from each type's pool, excluding the functional set | 4 | 18 | – |

`all_queries.tsv`: 634 distinct methods (evaluation sets overlap; tuning is disjoint from all of them).
`eval_queries.tsv`: 584 distinct evaluation queries (runner input for E2/E3); `tuning.tsv` is the runner input for E1.

Overlap between evaluation sets (methods in more than one):
16 methods.

## Overflow exclusion (2026-10-16)

101 methods are excluded from the corpus because KeLP's SSTK overflows on them (`PLAN.md` §4.1, `data/corpus/excluded_overflow.tsv`).
None of them is a tuning or syntactic query. One functional query, 3375723, was excluded and replaced by 481375, a random true positive that is neither excluded nor already a query (`prep/apply_overflow_exclusion.py`, seed 20261016).
The table above describes the sets as originally drawn. After the replacement (3375723 was task 10, name; 481375 is task 7 Bubble Sort, pattern) the functional set has **6** pattern-task queries and represents **25** tasks. `all_queries.tsv` and `eval_queries.tsv` are updated; counts stay 634 and 584.
