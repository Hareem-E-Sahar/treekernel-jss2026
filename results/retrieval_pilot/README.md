# Retrieval pilot (2026-10-12)

*Rerun 2026-10-12 on the revised trees (`docs/tree_variants.md`). The numbers from the old trees are at the end.*

**Caveat (found 2026-10-14):** in the SSTK runs, 39 corpus methods had an infinite self-similarity (KeLP float overflow, see `third_party/README.md` item 4). Their normalised scores were `NaN`, and the metrics script sorted them arbitrarily. The SSTK numbers here are therefore slightly affected. PTK is not affected. All results will be recomputed in the real experiments.

This is the first end-to-end retrieval run. It covers two kernel settings on variant C, without tuning. It exists to size the tuning set, **not** as a result for the paper.

- **Queries:** the 100 uniformly sampled true positives (`data/pools/queries.tsv`).
- **Candidates:** every other true positive in the benchmark *except the other 99 queries*, i.e. 14,680 per query. The harness skips query-vs-query pairs, and the final runs must include them.
- **Relevant:** a candidate that is a true positive of a functionality the query belongs to. This matches the `clones` table to within 288 pairs out of 8.58M.
- **Scoring:** normalised kernel, K(q,c) / √(K(q,q)·K(c,c)).
- **Metrics:**
  - MAP@R: average precision over the first R results, where R = the query's number of relevant candidates.
  - R-precision: fraction of the top R that are relevant.
  - P@1 and P@10: fraction of the top 1 or top 10 that are relevant.

Reproduce:

```bash
cd kernels
CP=target/kernels-0.1.jar:$(cat classpath.txt)
J="java -Xmx4g -Dorg.slf4j.simpleLogger.defaultLogLevel=error -cp $CP"
OUT=../results/retrieval_pilot
# kernel scores (PTK about 3 min, SSTK about 1.5 min) and self-similarities (about 10 s each)
$J treekernel.KernelTiming ../data/trees/C.tsv ../data/pools/queries.tsv PTK 0.4 0.4 100000 16 1 3000 $OUT/C_PTK_full.tsv
$J treekernel.SelfKernels ../data/trees/C.tsv PTK 0.4 0.4 16 $OUT/C_PTK_self.tsv
$J treekernel.KernelTiming ../data/trees/C.tsv ../data/pools/queries.tsv SSTK 0.4 0 100000 16 1 3000 $OUT/C_SSTK_full.tsv
$J treekernel.SelfKernels ../data/trees/C.tsv SSTK 0.4 0 16 $OUT/C_SSTK_self.tsv
cd ..
python3 -I eval/retrieval_metrics.py data/full_bcb results/retrieval_pilot \
    C_PTK:results/retrieval_pilot/C_PTK_full.tsv:results/retrieval_pilot/C_PTK_self.tsv \
    C_SSTK:results/retrieval_pilot/C_SSTK_full.tsv:results/retrieval_pilot/C_SSTK_self.tsv
```

## Results

| Configuration | MAP@R | R-precision | P@1 | P@10 |
|---|---|---|---|---|
| PTK λ=0.4 μ=0.4, variant C | 0.119 | 0.232 | 0.81 | 0.63 |
| SSTK λ=0.4, variant C | 0.083 | 0.187 | 0.61 | 0.44 |

Per-query values are in `C_PTK_per_query.tsv` and `C_SSTK_per_query.tsv`; the full output is in `metrics.txt`.

How to read this: the top-ranked result is a correct match for 81 of 100 queries (PTK). But MAP@R is low, because most functionalities have hundreds of relevant functions and only a small share of them rank high. Many solutions to the same task are written very differently, which is BigCloneBench's WT3/T4 problem.

## How many tuning queries? (query-count analysis)

- MAP@R varies a lot from query to query: the standard deviation is 0.155 for PTK and 0.124 for SSTK. So one MAP@R number from n queries is uncertain by about ±0.155/√n:
  - ±0.049 with 10 queries
  - ±0.022 with 50 queries
  - ±0.015 with 100 queries
- **Tuning compares configurations on the same queries**, so what matters is the spread of the *difference*. Here the per-query standard deviation of PTK − SSTK is 0.064.
  - The uncertainty of the difference is about ±0.020 with 10 queries, ±0.009 with 50 and ±0.006 with 100.
  - PTK beats SSTK on 81 of 100 queries. Random subsets of 10 queries pick the same winner 99.2% of the time, and subsets of 20 or more 100% of the time.
- To tell two configurations apart reliably (a difference of two standard errors), the number of queries needed is about (2 × 0.064 / difference)²:

  | MAP@R difference to detect | Queries needed |
  |---|---|
  | 0.03 | ~18 |
  | 0.02 | ~41 |
  | 0.01 | ~164 |

- **Caveats.**
  - This spread comes from a single pair of configurations, so it's itself a rough estimate. On the old trees it was 0.042, which would have needed only about a third as many queries.
  - Neighbouring hyperparameter settings (e.g. λ=0.4 vs 0.6) will likely differ by less than two different kernels do, but their per-query differences may also be less spread out.

## False positives

BigCloneBench found its candidates for each task with a keyword or regex search. Judges then rejected the ones that matched the search but don't implement the task. These rejected functions are the "false positives". Example from Bubble Sort, whose search pattern was `a[i] = a[i+1]`:

True positive (does bubble sort):

```java
public void Sort(int a[]) {
    for (int i = a.length; --i >= 0; ) {
        for (int j = 0; j < i; j++) {
            if (a[j] > a[j + 1]) {
                int temp = a[j];
                a[j] = a[j + 1];
                a[j + 1] = temp;
            }
        }
    }
}
```

False positive (matched the pattern, but deletes an element from an array):

```java
public boolean delete(long value) {
    int j;
    for (j = 0; j < nElems; j++) if (value == a[j]) break;
    if (j == nElems) return false; else {
        for (int k = j; k < nElems; k++) a[k] = a[k + 1];
        nElems--;
        return true;
    }
}
```

The current candidate set contains only true positives, i.e. functions that correctly implement one of the 43 tasks. Adding the ~58,000 false positives as extra non-relevant candidates would test whether a kernel can tell "does the same thing" apart from "looks similar" (same loops, same APIs).

## Old trees (2026-10-11): superseded

| Configuration | MAP@R | R-precision | P@1 | P@10 |
|---|---|---|---|---|
| PTK λ=0.4 μ=0.4, variant C | 0.114 | 0.224 | 0.79 | 0.62 |
| SSTK λ=0.4, variant C | 0.088 | 0.189 | 0.60 | 0.44 |

Per-query standard deviation of the PTK − SSTK difference: 0.042.

## Where true clones are ranked, by clone type (2026-10-12)

Files:
- `scripts/extract_query_clone_types.py`: clone types for all 131,338 clone pairs involving a query, written to `query_clone_types.tsv`.
- `eval/rank_by_clone_type.py`: produces `rank_by_clone_type.txt`.

PTK λ=0.4 μ=0.4, variant C, with 14,680 candidates per query. "Median rank" is the position as a percentage of the list; a random ranking would give 50%.

| Clone type | Pairs | Median score | Median rank | Within top R | Within top 10 |
|---|---|---|---|---|---|
| T1 | 385 | 1.000 | 0.2% | 100% | 31% |
| T2 | 171 | 1.000 | 0.3% | 100% | 16% |
| VST3 | 32 | 0.998 | 0.1% | 100% | 53% |
| ST3 | 114 | 0.984 | 0.1% | 100% | 41% |
| MT3 | 891 | 0.955 | 0.9% | 76% | 12% |
| WT3/T4 | 128,663 | 0.910 | 34% | 26% | 0.2% |
| not a clone | (sample) | 0.885 | | | |

Reading:
- **T1 to strong T3:** clones that are syntactically similar are found almost perfectly.
- **MT3:** mostly found.
- **WT3/T4 (98% of all clones):** these do the same task but are written differently. They are ranked only somewhat better than random. Their median score (0.910) is close to that of non-clones (0.885).

SSTK shows the same pattern and is weaker on ST3, MT3 and WT3/T4. Part of the WT3/T4 weakness may be label noise, because Krinke & Ragkhitwetsagul found many WT3/T4 pairs not to be functionally similar at all.
