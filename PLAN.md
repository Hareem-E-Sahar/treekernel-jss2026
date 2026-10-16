# Plan: tree kernels vs BM25 for Java code similarity on BigCloneBench

*Last revised 2026-10-13. Decisions are listed in §9.*

**Goal.** Compare tree kernels, a measure of **syntactic** similarity, with BM25, a measure of **lexical** similarity, for finding similar Java methods. The user's earlier work evaluated BM25; this study adds tree kernels (KeLP, https://github.com/SAG-KeLP/kelp-full) and compares the two on the same data.

**Main finding to test, from the pilot.** Tree kernels find syntactic clones (Type 1 to moderate Type 3) almost perfectly, but rank "same task, written differently" (WT3/T4) only somewhat better than random (`results/retrieval_pilot/README.md`). The study measures where each measure works, clone type by clone type.

## 1. Research questions (final, 2026-10-13)

- **RQ1. Syntactic similarity.** How well do tree kernels retrieve syntactic clones of each type (T1, T2, VST3, ST3, MT3), compared with BM25?
- **RQ2. Functional similarity.** How well do tree kernels retrieve code that implements the same task (same BCB functionality, mostly WT3/T4 clones), compared with BM25?
- **RQ3. Representation.** Which tree kernel (STK, SSTK, PTK) and which tree representation (variants A–D) works best? How much of the kernels' success comes from lexical content inside the trees (B vs C vs D)?
- **RQ4. Complementarity.** Do tree kernels and BM25 succeed on the same queries and clones, or on different ones? Does combining their scores improve retrieval?
- **RQ5. Cost.** What does each measure cost in computation time and memory?

## 2. Background: BigCloneBench

BigCloneBench (BCB) labels clone pairs inside a large Java corpus (IJaDataset). Each pair has a clone type:

- **T1**: identical code (apart from whitespace and comments).
- **T2**: identical apart from renamed identifiers and literals.
- **T3**: modified copies, graded by syntactic similarity: very strong (VST3), strong (ST3), moderate (MT3) and weak (WT3).
- **T4**: same task, written differently. WT3 and T4 are reported together.

Clone types follow the BigCloneEval convention: T1 and T2 come from `syntactic_type`. T3 is graded by min(line similarity, token similarity) after normalisation: VST3 ≥ 0.9, ST3 ≥ 0.7, MT3 ≥ 0.5, and anything lower is WT3/T4.

BCB was built per **functionality**, a task such as "Copy File" or "Bubble Sort Array". For each of its 43 functionalities, candidate functions were found with a **keyword or regex search**, recorded in the `functionalities.search_heuristic` column (e.g. `getConnection AND jdbc`). Judges then marked each candidate as a **true positive** (implements the task) or a **false positive** (matched the search but doesn't implement the task). True positives of the same functionality are clones of each other.

## 3. Data

### 3.1 Files

| Path | Contents |
|---|---|
| `data/bcb.pgdump/bcb` | Full BCB PostgreSQL plain-text dump (14 GB). Never restored; streamed by the scripts in about 45 s per pass. |
| `data/IJaDataset_BCEvalVersion/bcb_reduced/` | BCB-reduced source files: 43 functionality folders, each with `default`, `selected` and `sample` subfolders. 50,532 distinct files. A function is lines `startline..endline` of file `functions.name` in the subfolder matching `functions.type`. |
| `data/full_bcb/` | Extracted tables (`scripts/extract_full_bcb.py`): `tp_functionalities.tsv`, `judged.tsv`, `functions.tsv`, `functionalities.tsv`, `clone_type_counts.tsv`. Also `syntactic_clone_pairs.tsv`: all 160,086 T1–MT3 pairs (`scripts/extract_syntactic_clones.py`). |
| `data/trees/` | Source and KeLP trees for all 14,780 true positives, variants A–D (`prep/build_trees.py`). The experiments use `data/trees_main/` (14,679 methods, §4.1). |
| `data/pools/queries.tsv` | 100 uniformly sampled true positives (seed 20261011), used by the pilot. |

### 3.2 The benchmark in numbers (extracted 2026-10-11/12)

- **14,780 true-positive functions** across all 43 functionalities, taken from the `clones` table. 209 of them belong to two functionalities. All 14,780 parse cleanly with tree-sitter-java.
- The `judged` table lists 15,583 true positives. The 922 extra functions had split verdicts (judged both true and false positive), and BCB leaves them out of `clones`. BCB's 101 reference samples are in `clones` but were never judged.
- **58,322 false-positive functions**, i.e. judged false positive and true positive for no functionality. They are very uneven across functionalities.
- **Clone pairs by type** (whole benchmark):

  | Type | Pairs | Share | Functions involved | Functionalities |
  |---|---|---|---|---|
  | T1 | 48,116 | 0.56% | 3,793 | 37 |
  | T2 | 4,234 | 0.05% | 1,024 | 31 |
  | VST3 | 4,577 | 0.05% | 2,019 | 32 |
  | ST3 | 16,818 | 0.20% | 4,700 | 39 |
  | MT3 | 86,341 | 1.01% | 7,782 | 40 |
  | WT3/T4 | 8,424,067 | 98.14% | | |

  T1–MT3 together: 160,086 pairs involving 10,493 distinct functions.
- **BCB-reduced files.** 38,484 of the 50,532 files contain only false positives, 10,524 only true positives, and 1,524 both. (The user's earlier BM25 experiment used these 50,532 files as its corpus.)

### 3.3 Definitions

- **True positive function for functionality f:** a function that appears in a `clones` row with `functionality_id = f`.
- **False positive function:** judged false positive for some functionality and true positive for none.
- **Clone pair of type t:** a pair in `clones` whose type (§2) is t.
- **Same-functionality pair:** both functions are true positives of a common functionality. This matches the `clones` table to within 288 pairs out of 8.58M.

## 4. Evaluation design

### 4.1 Corpus

All 14,780 true-positive methods **minus 101 excluded for overflow = 14,679** (decided 2026-10-16). Every query is ranked against every other method in the corpus. The same corpus is used by every kernel and by BM25.
- **Overflow exclusion:** a method is excluded if KeLP's SSTK self-similarity at its default λ = 0.4 overflows (32-bit float) on any variant A–D. They are the largest ~0.7% of methods: on C every method above 2,559 nodes is excluded and, apart from 4 exceptions, none below 1,027. The exceptions overflow only on raw A: 3 methods holding one giant string literal (~4,000 raw nodes from escape sequences, 18 nodes on C) and one of 484 nodes on C. List: `data/corpus/excluded_overflow.tsv`; filtered trees: `data/trees_main/` (`prep/apply_overflow_exclusion.py`).
- **Effect:** no syntactic or tuning query and no syntactic relevant method is excluded. One functional query (3375723) was replaced by a random true positive (481375, seed 20261016). Functional queries lose on average 0.7% (at most 5.1%) of their relevant methods. The paper must state the exclusion and the size bias it implies.

False positives are **not** in the main corpus, because the focus is syntactic similarity and per-type evaluation doesn't need them. They are an optional robustness experiment (E5).

### 4.2 Query sets

All query sets are sampled with fixed seeds and saved under `data/pools/`. Sets used for tuning and for reporting share no functions.

| Query set | Size | Drawn from | Used for |
|---|---|---|---|
| **Tuning** | 50 (10 per type T1–MT3) | functions with at least one clone of that type | choosing kernel, variant and hyperparameters, optimising the syntactic metric |
| **Functional** | 100 | all true positives, uniformly | RQ2 |
| **Syntactic, per type** | 100 per type for T1, T2, VST3, ST3, MT3 | functions with at least one clone of that type | RQ1 |

- A function may serve as a query for several syntactic types; it is then scored once and evaluated for each.
- The existing `data/pools/queries.tsv` (pilot) can serve as the functional set. It was never used for tuning; it was used only to size the tuning set.

### 4.3 Ground truth, metrics and averaging

Full discussion: **`docs/evaluation_design.md`**. In short:

- **Ground truth.**
  - RQ1: relevant = the query's clones of type t; the query's other clones are removed from the ranking.
  - RQ2: relevant = every method of the same task.
- **Metrics.** **All** metrics are computed in every experiment (decided 2026-10-13): P@1/5/10, Recall@1/5/10/100, R-precision, MRR, MAP, MAP@R, median/mean rank. Ties get average ranks.
  - Primary metrics (decided 2026-10-13): MAP per clone type for RQ1; MAP@R for RQ2.
  - Tuning objective: average MAP over the five types.
- **Averaging.** Micro and macro (over represented functionalities) are both reported (decided 2026-10-13).
- **Breakdowns (not stratified sampling).** Queries are random within each clone type's pool. Results are then broken down by task (macro average) and by task category: pattern vs name tasks, as defined by BCB's search method. Method size later. Sensitivity analysis: bootstrap over queries (`docs/evaluation_design.md` §4.8).
- **Significance.** Wilcoxon signed-rank, paired by query; bootstrap confidence intervals.

**Complementarity (RQ4).**
- Per-query and per-clone win/loss between the best tree kernel and BM25, plus overlap of their top-10 results.
- Score fusion: reciprocal rank fusion, and a weighted sum of normalised scores with the weight tuned on the tuning set.

## 5. Measures

### 5.1 Tree kernels

- **Trees:** variants A–D, described in `docs/tree_variants.md` (revised 2026-10-12: readable labels, statements and primitive types kept).
  - A, raw: the full syntax tree.
  - B, pruned: punctuation and most keywords removed.
  - C, abstracted: B with names → `ID`/`TYPE` and literals → `NUM`/`STR`/…
  - D, abstracted but keeping API names: C with called-method and type names kept.
- **Kernels:** normalised, K(a,b)/√(K(a,a)·K(b,b)).

  | Kernel | Grid |
  |---|---|
  | STK | λ ∈ {0.1, 0.4, 0.8, 1.0} |
  | SSTK | λ ∈ {0.1, 0.2, 0.4, 0.6, 0.8, 1.0} |
  | PTK | λ ∈ {0.1, 0.4, 0.8}, μ ∈ {0.1, 0.4, 0.8} |
  | *Grid restriction* | Settings where KeLP's float kernels still give non-finite values on the reduced corpus (§4.1) are not computable. They are **kept in the sensitivity tables as "not computable (float overflow)"**, annotated with the number of overflowing methods, not silently dropped (decided 2026-10-16). Final grid: `results/grid_scan/README.md`. |
| SPTK | **Future work** (decided 2026-10-13). It adds soft lexical matching via identifier embeddings, the natural next step for combining syntactic and lexical similarity. |

- **Tuning:** 4 variants × 19 settings = 76 configurations on the 50 tuning queries. To save time: first pick the variant with SSTK at one λ, then search the grid.

### 5.2 BM25

- Same corpus, same query sets, same metrics.
- **Implementation: Elasticsearch** (decided 2026-10-13). Analyser, tokenisation and parameters are to be finalised later. Tree-kernel experiments come first.

## 6. Experiments

| ID | What | Answers |
|---|---|---|
| **E1** | Tune tree kernels (variant, kernel, hyperparameters) and BM25 (O2) on the tuning queries | prerequisite |
| **E2** | Syntactic evaluation: per-type query sets, best configurations + BM25 | RQ1 |
| **E3** | Functional evaluation: 100 uniform queries, best configurations + BM25 | RQ2 |
| **E4** | Representation ablation: all variants and kernels at their tuned settings on E2/E3 queries | RQ3 |
| **E5** (optional) | Robustness: add the 58,322 false positives to the corpus and rerun E2/E3 for the best configurations. Also measures the keyword-search bias (§8). | RQ1–2 |
| **E6** | Complementarity and fusion | RQ4 |
| **E7** | Cost: time per query, memory, index or preparation time, for both measures | RQ5 |

**Cost estimate for tree kernels** (`results/timing/README.md`). One query against the whole corpus costs 14,779 evaluations.
- **Tuning:** 50 queries × 76 configurations ≈ 55 min, up to about 2 h.
- **E2 + E3 for one configuration:** at most 600 queries ≈ 8.9M evaluations, about 2–30 min depending on kernel and variant, or up to 2× that on this laptop.
- BM25 takes seconds throughout.
- **Memory:** variant C needs 4.4 GB for the whole corpus. Variants A and B need candidates loaded in batches (to be built before E2).

## 7. Implementation

```
scripts/   data extraction and checks
prep/      query sampling, source extraction, tree building (build_trees.py, show_variants.py)
kernels/   Java/Maven: RetrievalRunner (KeLP kernels as is; query × corpus scores, streamed),
           GridFiniteScan (which settings overflow), PairSimilarity, KernelTiming/SelfKernels (timing),
           KernelCheck, ParseCheck (correctness checks). LogTreeKernels, PartialTreeKernelDouble,
           LogKernelCheck, PtkDoubleCheck: overflow-free reference versions, NOT used for results
eval/      metrics (retrieval_metrics.py, rank_by_clone_type.py), timing analysis
results/   timing/, retrieval_pilot/, then one folder per experiment
docs/      tree_variants.md, codexglue_findings.md
```

KeLP is built from source with known bugs worked around: a thread-safety race and shared delta matrices. See `third_party/README.md`.

Built 2026-10-14: query sampling (`prep/sample_queries.py`) and the retrieval runner (streamed corpus, query-vs-query pairs included, log-space SSTK/STK, giant-method memory handling).

Still to build:
- the metrics script: all metrics, average ranks for ties, micro/macro, category breakdown, bootstrap;
- the tuning driver (76 configurations);
- BM25 (Elasticsearch).

## 8. Threats to validity

- **Keyword-search bias.** BCB's candidates were found by keyword or regex search. Every true positive therefore contains its task's search terms, which favours lexical measures such as BM25 on same-task retrieval. Every false positive contains them too, which works against BM25 when they are included (E5). Variant D, which keeps API names, is affected similarly.
- **Lexical clone-type definition.** T3 subtypes are defined by line and token similarity, i.e. a lexical measure. BM25 may look strong on T3 partly for that reason.
- **Same-project copies.** 88% of T1 pairs (42,533 of 48,116) are within one project, often the same file in different branches or versions. These are trivial for any measure and may make T1 look solved. Same- vs cross-project stratification was considered and not selected (`docs/evaluation_design.md` §4.1).
- **Label noise.** Many WT3/T4 labels are questionable (Krinke & Ragkhitwetsagul, 2022, 2025).
- **Unlabelled pairs.** Pairs from different functionalities are assumed not to be clones, although some are syntactically similar (e.g. Copy File vs Copy Directory). The syntactic evaluation ranks type-t clones against such pairs, so a "non-clone" ranked first may in fact be a genuine but unlabelled clone.
- **Imbalance.** Functionality sizes differ by two orders of magnitude; report macro averages alongside micro.
- **Single dataset.** Results are for BigCloneBench only. CodeNet Java250 was considered as a second dataset with labels independent of wording and was set aside for now (2026-10-12).
- **Novelty.** Tree kernels for clone detection are established (Corazza et al., ICSM 2010). The contribution is the systematic syntactic-vs-lexical comparison, not a new method.

## 9. Decisions and open questions

**Decided**
| Date | Decision |
|---|---|
| 2026-10-11 | Full BigCloneBench database as the benchmark (method level). |
| 2026-10-11 | Queries ranked against every other true positive in the corpus. |
| 2026-10-12 | Tree variants revised (readable labels, statements and primitive types kept). |
| 2026-10-12 | 50 tuning queries, kept separate from all reported queries. |
| 2026-10-12 | BigCloneBench only; CodeXGLUE and CodeNet not used for now. |
| 2026-10-12 | Compare tree kernels with BM25. The user's earlier 100 queries are not reused; BM25 is rerun here on the new query sets. |
| 2026-10-12 | Syntactic evaluation with 100 queries per clone type (T1–MT3); uniform queries for the functional evaluation. |
| 2026-10-12 | False positives not in the main corpus; optional robustness experiment E5. |
| 2026-10-13 | Tuning: 50 queries, 10 per clone type T1–MT3, optimising the syntactic metric (objective: average MAP over types). |
| 2026-10-13 | SPTK is future work, not part of this study. |
| 2026-10-13 | Compute all metrics in every experiment; choose the paper's metrics later. |
| 2026-10-13 | Report micro averages and macro averages over represented functionalities. |
| 2026-10-13 | Results broken down by task category; method size later. |
| 2026-10-13 | Category = BCB search method: 6 pattern tasks vs 37 name tasks. |
| 2026-10-13 | Keep random query sampling (no stratified sampling apart from per-clone-type pools). Results are broken down by task and category afterwards. Sensitivity analysis = bootstrap over queries; replication optional, not planned. The category comparison is exploratory. |
| 2026-10-13 | Primary metrics: MAP (RQ1), MAP@R (RQ2). The five RQs are final. |
| 2026-10-13 | BM25 via Elasticsearch, details later; tree kernels run first. |
| 2026-10-14 | Query sets sampled (`data/pools/README.md`): 50 tuning; 100 per clone type; 100 functional (pilot sample); 584 distinct evaluation methods. |
| 2026-10-14 | ~~O5 → option A: SSTK and STK in log space, double precision (KeLP's floats overflow); all methods kept, λ grid unchanged. PTK stays KeLP's.~~ *(superseded 2026-10-15)* |
| 2026-10-16 | **Overflow handling, option 1:** KeLP as is; the 101 methods whose SSTK λ = 0.4 self-similarity overflows on any variant are excluded from the corpus (all kernels and BM25); settings that still overflow are reported as "not computable" cells in the sensitivity analysis, with overflow counts, and justified by the literature on large decay values (diagonal problem). Extended-range reimplementation (option 2) rejected. |
| 2026-10-15 | **Use KeLP as is** (all three kernels in KeLP's 32-bit floats, KeLP's own STK). Grid settings for which KeLP produces non-finite values are removed from tuning (scan: `results/grid_scan/`). Harness workarounds that don't change values (thread safety, per-thread delta matrices, memory for giant methods) stay. This resolves O5, O6 (KeLP's STK) and O7. |

**Open**
- **O2. BM25 details:** Elasticsearch analyser/tokenisation and k1/b. To finalise before the BM25 runs.

## 10. Order of work

1. Done: data extraction, tree building, KeLP harness, timing, pilot retrieval (2026-10-11/12).
2. Done 2026-10-13: RQs, ground truth, metrics, averaging and stratification (`docs/evaluation_design.md`). BM25 details (O2) are deferred.
3. Sample the tuning, functional and per-type query sets.
4. Build the retrieval runner (query-vs-query pairs included, candidate batching), BM25 and the per-type metric.
5. Tree kernels: E1 tuning → E2/E3 → E4. Then BM25 (after O2) → E6 → E7, then E5 if time allows. Bootstrap intervals are computed with every evaluation.
