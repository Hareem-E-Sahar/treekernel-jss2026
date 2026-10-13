# Plan: tree kernels for Java code similarity on BigCloneBench

Goal: evaluate KeLP's tree kernels (https://github.com/SAG-KeLP/kelp-full) for measuring source-code similarity, with similar-code retrieval as the end goal.

**Primary benchmark: the full BigCloneBench database. Secondary: the CodeXGLUE version, for comparison with published numbers** (decided 2026-10-11).

## 0. Background: BigCloneBench

BigCloneBench (BCB) labels clone pairs inside a large Java corpus (IJaDataset). Each pair has a clone type:

- **T1**: identical code.
- **T2**: identical apart from renamed identifiers and literals.
- **T3**: modified copies, split by syntactic similarity: very strong (VST3), strong (ST3), moderate (MT3) and weak (WT3).
- **T4**: same function, written differently. WT3 and T4 are reported together.

Clone types follow the BigCloneEval convention: T1 and T2 come from `syntactic_type`. T3 is graded by min(line similarity, token similarity): VST3 ≥ 0.9, ST3 ≥ 0.7, MT3 ≥ 0.5, and anything lower is WT3/T4.

BCB was built per **functionality**, a task such as "Copy File" or "Bubble Sort Array". For each of its 43 functionalities, candidate functions were found with a search heuristic (a keyword or regex pattern). Judges then marked each candidate as a **true positive** (it implements the task) or a **false positive** (it matched the pattern but doesn't implement the task). True positives of the same functionality are clones of each other.

**Label noise.** Krinke & Ragkhitwetsan show that many T4 labels are questionable and that unlabelled pairs aren't reliably non-clones. They make this argument in *"BigCloneBench Considered Harmful for Machine Learning"* (2022) and *"How the Misuse of a Dataset Harmed Semantic Clone Detection"* (2025). Report results by clone type and treat absolute numbers carefully.

## 1. Data

### 1.1 Files

| Path | Contents |
|---|---|
| `data/bcb.pgdump/bcb` | Full BCB PostgreSQL plain-text dump (14 GB). Tables include `clones` (8.58M pairs), `false_positives`, `functions` (22M), `functionalities` (43), `judged` and `tagged`. |
| `data/IJaDataset_BCEvalVersion/bcb_reduced/<functionality>/<default\|selected\|sample>/<file>.java` | Source files. A function is lines `startline..endline` of file `functions.name` in the folder matching `functions.type`. |
| `data/codexglue_bcb/` | CodeXGLUE BCB: `data.jsonl` and `{train,valid,test}.txt` (secondary benchmark). |
| `data/bcb_subset/`, `data/bcb_joined/` | Rows of the dump for the CodeXGLUE functions, and CodeXGLUE pairs annotated with clone type and functionality. |

The dump never needs restoring into PostgreSQL. A streaming pass over it takes about 45 s (`scripts/extract_bcb_subset.py`).

### 1.2 Size of the full benchmark (extracted 2026-10-11)

`scripts/extract_full_bcb.py` streams the dump (about 50 s) and writes `data/full_bcb/`: `tp_functionalities.tsv`, `judged.tsv`, `functions.tsv`, `functionalities.tsv` and `clone_type_counts.tsv`.

- **14,780 true-positive functions** across all 43 functionalities, taken from `clones`. 209 of them are true positives for two functionalities.
- The `judged` table marks 15,583 functions as true positives. The difference is explained:
  - 922 were judged **both** true and false positive by different judges, and BCB leaves these split verdicts out of `clones`.
  - 101 functions are in `clones` but not `judged`. These are BCB's reference samples, which were never judged.
- **About 58,000 false positives.** These are hard negatives: they match the same search pattern as real solutions but don't do the task. They're very uneven: Copy File has 32,899 and Download From Web 12,713, while File Dialog and Initialize Java Eclipse Project have none.
- **Functionality sizes are very uneven.** Copy File has 3,049 true positives; Setup SGV Event Handler has 10.
- **Parsing.** All 14,780 functions parse cleanly with tree-sitter-java (`prep/build_trees.py`).

### 1.3 Definitions

- **True positive function for functionality f:** a function that appears in a `clones` row with `functionality_id = f`.
- **False positive function:** a function judged false positive for some functionality and true positive for none.
- **Relevant pair:** a pair present in `clones`. Its clone type is attached. A function that's a true positive for two functionalities is relevant to both.
- **Non-relevant pair:** any other pair. Treating pairs from different functionalities as non-clones is an assumption. It's reasonable for function-level retrieval, but a threat to validity (see §7).

### 1.4 Retrieval design (decided 2026-10-11)

- **Queries.** **100 true positives sampled uniformly** from all 14,780, with no per-functionality stratification. The sample uses seed 20261011 and is stored in `data/pools/queries.tsv`. It covers 24 functionalities.
- **Candidates.** **Every other true positive in the benchmark**, i.e. 14,779 per query. Every query therefore has all of its real clones among the candidates.
- **Cost.** 100 × 14,779 = **1,477,900 kernel evaluations** per configuration. This grows linearly with the number of queries, which is the knob for controlling cost.
- **False positives as extra distractors.** Not decided. Adding all ~58,000 would raise the cost to about 7.3M evaluations per configuration.
- **Tuning (proposal, not yet decided).** Use a second, disjoint set of uniformly sampled queries, ranked against the same corpus. The kernels are unsupervised and only hyperparameters are chosen, so sharing the candidate corpus doesn't leak labels.
  - The pilot (`results/retrieval_pilot/README.md`, rerun 2026-10-12) suggests about 40–50 tuning queries. **Decided 2026-10-12: 50 tuning queries**, sampled uniformly and kept separate from the 100 test queries. They resolve MAP@R differences of about 0.02 between configurations, and cost 0.5× a test run per configuration.
- **Averaging.** With uniform queries, Copy File supplies about 20 of the 100. Report micro averages, which reflect the benchmark's natural mix, and macro averages over the functionalities that are represented.

### 1.5 CodeXGLUE version (secondary benchmark): findings (checked 2026-10-11)

Scripts: `scripts/inspect_codexglue_bcb.py`, `scripts/split_components.py` and `scripts/verify_bcb_join.py`.

- **Basic counts.** There are 9,126 functions. Every function ID used in a pair exists in `data.jsonl`, and no pair has conflicting labels.
- **No function leakage between splits.** Train uses 7,302 functions, valid 912 and test 912, and no function appears in more than one split.
- **Duplicated training pairs.** `train.txt` lists 225,431 pairs twice, once in each order. That leaves 675,597 unique pairs: 225,431 positive and 450,166 negative.
- **Valid and test are fully labelled.** Each has 912 × 911 / 2 = 415,416 pairs, which is every possible pair.
- **The join with full BCB is exact.** CodeXGLUE `idx` is the BCB `functions.id`. For 9,118 of the 9,126 functions, the source text matches the IJaDataset file lines exactly, and the other 8 differ slightly. Every CodeXGLUE positive pair is a BCB clone. In train, 1 negative is actually a BCB clone, and 90 negatives are BCB false positives.
- **Clone types are about 98% WT3/T4.**

  | split | T1 | T2 | VST3 | ST3 | MT3 | WT3/T4 |
  |---|---|---|---|---|---|---|
  | train | 572 | 118 | 84 | 359 | 2,046 | 222,252 |
  | valid | 244 | 38 | 26 | 68 | 525 | 52,938 |
  | test | 143 | 68 | 16 | 141 | 592 | 55,860 |

- **Test clone groups map to functionalities.** The groups are Copy File (285, which also contains a Zip Files clique of 8), Secure Hash (138), Download From Web (90), Execute update and rollback (73), Connect to FTP Server (19), Bubble Sort Array (14), Setup SGV (2) and Initialize Java Eclipse Project (2). The other 289 test functions are rejected "Download From Web" candidates.
- **Validation.** Its 189-function group joins Secure Hash and Execute update and rollback through shared functions, so it isn't transitive. Use the pair labels as relevance judgements, not group membership.
- **Why it's secondary.** Test covers only 9 of the 43 functionalities, and one functionality (Copy File) holds 285 of the 623 functions that have a clone. Its value is comparability with machine-learning papers that report F1 on these splits.

## 2. Research questions

- **RQ1.** How well does each tree kernel (STK, SSTK, PTK, SPTK) separate clones from non-clones, broken down by clone type?
- **RQ2.** How well does ranking by a normalised kernel retrieve functionally similar code across BCB's 43 functionalities?
- **RQ3.** Which preprocessing choices matter most: identifier abstraction, pruning, keeping API call names?
- **RQ4.** How do tree kernels compare with lexical and neural baselines, in both accuracy and cost?

## 3. From code to trees

- **Source text.** For full BCB, cut lines `startline..endline` from the IJaDataset file. For CodeXGLUE, use `data.jsonl`. The two agree for 9,118 of the 9,126 shared functions.
- **Parser: tree-sitter-java.** It tolerates syntax errors, which matters because BCB functions are fragments cut out of files. Report how many trees contain `ERROR` nodes.
- **Tree variants** (these form the RQ3 ablation). Full description, worked example and known weaknesses: `docs/tree_variants.md`.
  - Revised 2026-10-12: labels are readable, statements and blocks are no longer collapsed, and primitive types are kept. The old hex encoding also caused false matches between long string literals. Details are in the document's change history.
  - **A, raw:** the full concrete syntax tree.
  - **B, pruned:** remove punctuation and keyword tokens, and collapse chains where a node has one child.
  - **C, B plus abstraction:** replace local variable, parameter and field names with `ID`, and literals with `NUM`, `STR` or `BOOL`.
  - **D, C but keeping API names:** keep method-call names and type names, such as `FileInputStream` or `read`. These are often the strongest signal for T4 clones. Note the risk: BCB's search heuristics are mostly API names, so variant D partly rediscovers how the benchmark was built (see §7).
- **Size control.** Cap trees at a maximum node count or depth, or truncate deep expression subtrees. Record the size distribution, because cost and normalisation both depend on it.
- **Output.** One KeLP-format line per function: `<id> |BT:ast| (method_declaration ...) |ET|`.

## 4. Kernels and hyperparameters

Always wrap kernels in `NormalizationKernel`, so that scores fall in [0, 1] and large methods don't win by default.

| Kernel | Grid |
|---|---|
| STK | λ ∈ {0.1, 0.4, 0.8, 1.0} |
| SSTK | λ ∈ {0.1, 0.2, 0.4, 0.6, 0.8, 1.0} |
| PTK | λ ∈ {0.1, 0.4, 0.8}, μ ∈ {0.1, 0.4, 0.8} |
| SPTK (optional, later) | PTK grid, plus a node similarity based on identifier embeddings (e.g. word2vec on sub-tokenised identifiers, trained on functions that are neither tuning nor test queries) |

Choose hyperparameters on the **tuning queries** only. Report on the **100 test queries**. The full grid is 4 variants × 19 kernel settings = 76 configurations. Narrow it down in stages: pick the variant with SSTK at one λ, then search the grid with that variant.

Optional supervised stage: KeLP has pair kernels, e.g. K((a,b),(c,d)) = K(a,c)·K(b,d) + K(a,d)·K(b,c). An SVM trained on these learns what counts as a clone, rather than relying on a fixed similarity threshold. Only try this if the unsupervised results justify it. It would need a separate set of training pairs.

## 5. Experiments

All experiments in E1 and E2 use one score matrix per configuration: 100 queries × 14,779 candidates (§1.4).

**E1: retrieval on full BCB (RQ2, RQ3). Primary result.**
- Queries: the 100 uniformly sampled true positives. Candidates: every other true positive in the benchmark, plus false positives if that's decided (§1.4). Rank the candidates by normalised K(query, candidate).
- Relevant: the query's `clones` pairs.
- Metrics: MAP@R, Precision@1/5/10 and MRR. Report both micro averages and **macro averages over the 43 functionalities**, and per functionality.
- **False-positive analysis:** how often a false positive of the query's own functionality is ranked above its true clones. This measures whether the kernel captures behaviour or just shared API vocabulary.
- **Scaling variant:** retrieve the top 100 candidates with TF-IDF, then re-rank them with the kernel. Then run it on the full 15.6k true positives + 58k false positives without capping. Report accuracy and speed against full ranking.

**E2: pairwise clone detection by type on full BCB (RQ1).**
- Use the same query × candidate scores: relevant pairs against non-relevant ones.
- Report ROC-AUC, plus recall by clone type at a threshold tuned on the tuning queries (T1, T2, VST3, ST3, MT3, WT3/T4), following BigCloneEval.
- 100 queries can leave too few T1–ST3 pairs. Count them. If there are too few, also score **all** T1–ST3 pairs from the full `clones` table that don't involve a tuning query. Scoring a list of pairs costs one evaluation per pair, so this is cheap.

**E3: CodeXGLUE comparison (secondary).**
- Score the 415,416 CodeXGLUE test pairs. Report F1 at a threshold tuned on CodeXGLUE validation, with ROC-AUC alongside.
- Report by clone type using `data/bcb_joined/test_pairs_labelled.tsv`.
- This gives a number that can be compared directly with published CodeXGLUE results.

**E4: baselines and cost (RQ4).**
- Lexical: token TF-IDF cosine and token Jaccard, computed on the same abstraction variants.
- Classic clone detectors (optional): NiCad or SourcererCC.
- Neural, zero-shot: cosine similarity of UniXcoder or CodeBERT embeddings. Compare with published fine-tuned CodeXGLUE numbers with care, because CodeXGLUE's test set is dominated by a few functionalities.
- Cost: kernel evaluations per second against tree size for each kernel (first measurement done 2026-10-11, see §8 step 2), index build time, and per-query latency for full ranking and re-ranking.

## 6. Implementation layout

```
scripts/   data checks and extraction (already present)
prep/      Python: sample queries, extract source, tree-sitter parsing,
           variants A–D, export to KeLP format
kernels/   Java/Maven: depends on kelp-additional-kernels; computes query×candidate
           matrices and pair lists in parallel with a self-kernel cache; writes scores to TSV
eval/      Python: MAP@R/P@k/MRR (micro and macro), AUC and per-type recall, F1 for CodeXGLUE,
           baselines, plots
configs/   one JSON per run (kernel, hyperparameters, variant, query set), so every result is traceable
```

Environment checked on 2026-10-11: OpenJDK 21, Maven 3.8.7, Python 3.12, 16 cores, ~13 GB RAM. tree-sitter is not yet installed (`pip install tree-sitter tree-sitter-java`).

## 7. Threats to validity

- **Label noise.** BCB labels are noisy, especially for T4 (Krinke & Ragkhitwetsan).
- **Unlabelled pairs.** Pairs from different functionalities are assumed not to be clones. Two functions from different functionalities may still be syntactically similar, for example Copy File and Copy Directory, or Zip Files and Decompress zip archive.
- **Benchmark construction bias.** BCB's candidates were found with API-name search patterns. Kernels that keep API names (variant D) may score well partly because of how the benchmark was built. The false-positive analysis in E1 probes this directly.
- **Imbalance.** Functionality sizes differ by two orders of magnitude, so report macro averages alongside micro.
- **Parsing.** Parse errors and the tree-size cap silently discard structure.
- **Overlap with neural pretraining.** IJaDataset projects may be in neural models' pretraining data, which would favour the neural baselines.
- **Novelty.** Tree kernels are an established clone-detection technique. Corazza et al. (ICSM 2010) applied them to ASTs, so present this work as a systematic re-evaluation of KeLP's kernel family on BCB, not as a new method.

## 8. Order of work

1. **Extract data and sample queries.** Done 2026-10-11 (§1.2, §1.4).
2. **Measure cost (E4).** Done 2026-10-11 and rerun 2026-10-12 on the revised trees, see `results/timing/README.md`. A full run (100 queries × all true positives, 1.48M evaluations) takes about 0.4–5 min per configuration. Budget up to 2× that for long runs, because this laptop slows down under sustained load. The full 76-configuration grid takes about 110 min, up to about 3.5 h. Memory is the binding constraint: 4.4 GB resident for all variant-C trees, so raw trees need candidates loaded in batches. Still to decide: false-positive distractors (~5× cost) and the number of tuning queries.
3. **Tune.** Pick the variant, then kernel hyperparameters, on the tuning queries.
4. **E1 retrieval with the 100 test queries.** This is the primary result.
5. **E2 per-type detection.** Reuse the E1 matrix and add the extra T1–ST3 pairs if needed.
6. **E3 CodeXGLUE comparison.**
7. **Baselines and the TF-IDF → kernel re-ranking at full scale.**
8. **SPTK and pair-kernel SVM**, only if earlier results justify them.
