# Revision plan

How each reviewer comment on the initial submission will be addressed. Decisions here are proposals until the
supervisor approves them; nothing is run until then. Experiments refer to exp_v2 (corpus with false positives, 72,782
methods), the only setting in the revised paper.

Status: **proposed** (discussed, awaiting supervisor approval) · **approved** · **done** · **open** (still under discussion).

| Comment | Topic | Action | New compute | Status |
|---|---|---|---|---|
| R1-C1a | Query sampling not stratified by type, size, complexity | Evaluate every eligible query (14,587) instead of samples | Kernels on 6,793 more queries, about 13 h | proposed |
| R1-C1b | Kernel hyper-parameters at defaults, no sensitivity analysis | λ/μ grid and PTK terminal-factor sweep (0.25–4) reported as table and figure; factor stays 1 | done: sweep run 2026-11-03 (about 20 min) | proposed |
| R1-C2a | CodeBERT only zero-shot; embedding weakness over-generalised | Report fine-tuned CodeBERT next to zero-shot in all RQs; reword claims to "zero-shot"; scoped caveats | none: fine-tuned runs exist (2026-11-02) | proposed |
| R1-C3 | Java only, GumTree, label noise not quantified | Options recorded (bound by ignoring false positives; Type-2 near-copies; cite Krinke & Ragkhitwetsagul for WT3/T4); cross-language limits discussed | re-evaluation only (A, B) | open |

---

## R1-C1a: sampling design

> Sampling design: 100-query repeated sampling is not stratified by clone type, size, or complexity, risking
> composition bias. (Suggestion: adopt stratified sampling controlled for clone type/size/complexity, or add
> sensitivity analysis.)

**Decision (proposed):** evaluate all methods on **every eligible query** instead of samples of 100.
- Eligible queries: every true positive in the corpus (14,679) minus the 50 tuning queries and the 42 methods whose
  functionalities span CodeBERT folds = **14,587** (`exp_v2/data/full/`, `exp_v2/prep/full_queries.py`).
  Per set: T1 3,746, T2 998, VST3 1,991, ST3 4,652, MT3 7,722, functional 14,587.
- **No sampling, so no composition bias.** Clone types are evaluated separately (each type on all queries that have a
  clone of that type); the query mix by size and complexity is BigCloneBench's own; size and complexity are analysed
  explicitly in RQ3 (unchanged).
- Inference: 95% CIs from the paired bootstrap over functionalities, as now.
- RQ1, RQ2 and RQ4 then use the same queries; the hybrid is compared with the full-ranking kernels on every query.
- **RQ3 design (changed from the initial submission):** the initial submission pooled RQ3 queries from one pool by
  size and complexity thresholds. The revision uses the exp_v2 design: a syntactic part (as RQ1: each clone type
  evaluated separately, then the mean over the five types) and a functional part (as RQ2), per group, on every
  eligible query in the group. Reason: the groups differ in clone-type mix (eligible queries: T1 is 33% of the
  high-complexity type-queries vs 18% of the low; MT3 21% vs 42%), so a pooled design confounds size and complexity
  with clone type. The split also keeps the syntactic part free of WT3/T4 label noise (R1-C3).
  Small cells (small T2 53, small VST3 12, high T2 57 queries) are whole groups; their wide CIs are accepted and
  reported as they are.
- **The 10 replicate sets stay where they are** (results and code unchanged in the repository).
- Not added: a per-functionality (macro) analysis; the reviewer did not ask for it.

**Compute:** BM25, CodeBERT (zero-shot, fine-tuned) and the hybrid already have runs on all 14,587 queries (RQ4).
The kernels have 7,794 of them (replicates and RQ3); the other 6,793 take about 13 h with the multi-threaded runner
(STK and SSTK about 3 h each, PTK about 6.5 h). Disk: about 4 GB of scores per kernel (68 GB free).

**Background for the response:** BigCloneBench's "8.5 million clones" are clone pairs. Our 14,679 true positives give
8,451,359 same-functionality pairs (BCB: 8.58M over 14,780 true positives; 101 removed because KeLP overflows on them).
Queries are methods, so the population of queries is the true positives, not the pairs.

**Response (draft):** We no longer sample queries. All methods are evaluated on every eligible query (N = 14,587), so
no composition bias can arise from sampling. Clone types are evaluated separately, and the effect of size and
complexity is analysed explicitly in RQ3.

---

## R1-C1b: kernel hyper-parameters

> Tree-kernel hyper-parameters use defaults without sensitivity analysis. (Suggestion: perform kernel hyper-parameter
> sensitivity study (λ, μ, terminal factor).)

**Decision (proposed): a terminal-factor analysis of PTK.**
- **What:** PTK at the tuned λ 0.4, μ 0.6, with terminal factor ∈ {0.25, 0.5, 0.75, 1, 2, 4}, on
  the 50 tuning queries against the full corpus; MAP for RQ1 (mean over T1–MT3) and RQ2, as for the λ/μ grid.
- **Overflow check first:** a factor above 1 makes KeLP's float overflow more likely; non-computable values are
  reported as such, like the λ/μ grid (`exp_v2/tuning/scan.tsv`).
- **Code:** `RetrievalRunner` fixes the factor at 1 (`new PartialTreeKernel(lambda, mu, 1f, "ast")`); the shared
  runner stays unchanged, so the factor is passed through an exp_v2 copy (as for `HybridRerank`).
- Only PTK has a terminal factor; STK and SSTK have λ alone.
- **Current reasoning for 1** (`exp_v2/DESIGN.md`): leaves are neither favoured nor penalised beyond λ and μ; in
  variant D the leaves carry the lexical content, so a factor above 1 shifts PTK towards lexical matching.

**Already available, no compute:** the λ/μ grid on the 50 tuning queries (`exp_v2/tuning/grid.tsv`), 32 settings, MAP
for RQ1 and RQ2:

| Kernel | Range | RQ1 | RQ2 |
|---|---|---|---|
| STK | λ 0.1 → 1.0 | 0.815 → 0.868 (λ 1.0), rising steadily | 0.214 → 0.232 |
| SSTK | λ 0.1 / 0.2 / 0.4 | 0.889 / 0.858 / 0.727 | 0.227 / 0.229 / 0.175 |
| PTK | 21 computable (λ, μ) | 0.849 → 0.916 (λ 0.4, μ 0.6); μ matters far more than λ | 0.187 → 0.217 |

Not computable (KeLP overflows): SSTK λ ≥ 0.6; PTK λ 0.2 μ 1.0, λ 1.0 μ 0.1 and 0.2, and the remaining larger
(λ, μ) pairs.

**Decision (proposed): report the λ/μ grid as the sensitivity analysis for λ and μ, as both a table and a figure.**
- Table: MAP for RQ1 and RQ2 per setting and kernel, non-computable settings marked with their number of overflowing
  methods.
- Figure: STK and SSTK as MAP against λ; PTK as a λ × μ heat map (one panel each for RQ1 and RQ2). The terminal-factor
  results are added to the same table and figure (PTK, MAP against the factor).
- No new compute: from `exp_v2/tuning/grid.tsv` and `exp_v2/tuning/scan.tsv`.

**Result (run 2026-11-03, `exp_v2/scripts/run_terminal_factor.sh` → `exp_v2/tuning/terminal_factor.tsv`):** PTK at
λ 0.4, μ 0.6 on the 50 tuning queries; factor 1 reproduces the tuning run byte for byte. BM25 overlap = mean share of
PTK's top 10 / top 100 also in BM25's top 10 / top 100 (query and its ignored exact copies excluded).

| Terminal factor | RQ1 MAP (mean T1–MT3) | RQ2 MAP (functional) | BM25 overlap, top 10 | BM25 overlap, top 100 |
|---|---|---|---|---|
| 0.25 | 0.893 | 0.186 | 0.520 | 0.325 |
| 0.5 | 0.910 | 0.200 | 0.524 | 0.339 |
| 0.75 | 0.913 | 0.210 | 0.522 | 0.342 |
| **1** (used) | 0.916 | 0.217 | 0.520 | 0.344 |
| 1.25 | **0.917** | **0.222** | 0.522 | 0.350 |
| 1.5, 1.75, 2, 4 | not computable: KeLP float overflow on the self-similarity of large methods (2,182–3,845 nodes) | | | |

- **1.25 is the best computable factor**, by a small margin over 1: RQ1 +0.0015, RQ2 +0.005 (50 queries). 1.25 is the
  largest computable value tried; 1.5 and above overflow.
- **Lexical check:** the top-10 overlap with BM25 does not change with the factor (0.52); the top-100 overlap rises
  slightly (0.325 → 0.350). So the data give only weak support for "a higher factor makes PTK more lexical"; the
  argument cannot replace the measurement.
- 1.25 is computable for any query set: the overflow occurs in the self-similarities K(c, c), which the run computed
  for all 72,782 methods.
- Not yet done: counting the overflowing methods for the non-computable factors (`GridFiniteScan` fixes the factor at
  1).

**Cost if 1.25 is adopted:** PTK is rerun at factor 1.25 on all 14,587 eligible queries (about 14 h instead of the
6.5 h planned under R1-C1a), from which the replicate and RQ3 runs are assembled (both are subsets); the hybrid's PTK
second stage, the PTK fusions (W re-tuned) and everything evaluated from them are redone. λ and μ were tuned at factor
1; adopting 1.25 at fixed λ, μ is a one-coordinate change, not a joint re-tune.

**Decision (proposed): (b) keep terminal factor 1** and report the sweep as a sensitivity analysis.
- The best computable factor, 1.25, is higher by only 0.0015 (RQ1) and 0.005 (RQ2) MAP on 50 tuning queries, within
  noise; MAP changes little between 0.75 and 1.25.
- Keeping 1 avoids re-tuning one parameter while λ and μ stay tuned at 1, and about 7.5 h of extra PTK compute.
- In the paper: the sweep goes into the sensitivity table and figure, with 1.25 shown as slightly higher and factors
  of 1.5 and above marked not computable (KeLP float overflow); the text states that 1 is kept and why.
- No PTK reruns: the all-queries runs of R1-C1a use factor 1.

**Response (draft):** The revised version tunes λ (all kernels) and μ (PTK) over {0.1, 0.2, 0.4, 0.6, 0.8, 1.0} on
separate tuning queries and reports the full grid as a sensitivity analysis (table and figure), including settings
that cannot be computed because KeLP overflows. We also vary PTK's terminal factor from 0.25 to 4: MAP changes little
between 0.75 and 1.25, factors of 1.5 and above overflow, and we keep KeLP's default of 1.

---

## R1-C2a: baseline fairness (CodeBERT)

> Baseline fairness: CodeBERT is evaluated only zero-shot; conclusions on embedding weakness risk
> over-generalisation. (Suggestion: add fine-tuned CodeBERT results or strengthen zero-shot caveats.)

**Decision (proposed): both. Report fine-tuned CodeBERT next to zero-shot CodeBERT in every RQ, and add caveats that
are limited to what was not tested.**
- **No new compute:** fine-tuned CodeBERT (bi-encoder, contrastive, 5 folds by functionality, BigCloneBench false
  positives as hard negatives; `exp_v2/embed/finetune_fp.py`) is already in all exp_v2 tables and figures for RQ1–RQ4,
  rerun 2026-11-02.
- **Why not caveats alone:** fine-tuning changes the RQ2 conclusion, so the reviewer's concern is correct. RQ2 MAP
  (10 replicates): CodeBERT zero-shot 0.149, STK / SSTK / PTK 0.191 / 0.190 / 0.169, BM25 0.444, CodeBERT fine-tuned
  0.437 (best nP@5 and nP@10; significantly better than every kernel on every metric). The weakness is zero-shot
  CodeBERT's, not that of embeddings in general.
- **Numbers to update:** the figures above are from the 10 replicate sets; once R1-C1a is done, the paper and the
  response quote the all-queries results (N = 14,587).
- **RQ1 holds against the stronger baseline:** the kernels stay significantly better than fine-tuned CodeBERT on
  syntactic clones (e.g. T2, VST3, ST3). Since the fine-tuning rerun, the kernels' lead on MT3 nP@k is not
  significant.
- **Rewording:** every claim of embedding weakness (abstract, RQ2 discussion, conclusion) is limited to zero-shot
  CodeBERT or revised in light of the fine-tuned results.
- **Caveats (threats to validity):**
  - one model (microsoft/codebert-base), as a bi-encoder only; larger code models and cross-encoder re-rankers
    (e.g. Arshad et al., IWSC 2022) are not evaluated, since a cross-encoder cannot rank 72,782 methods per query on
    CPU; re-ranking with one is future work;
  - one fine-tuning recipe, trained on BigCloneBench functionalities; the test functionalities are not seen in
    training (folds by functionality), but the domain is the same;
  - fine-tuned CodeBERT learns BigCloneBench's functionality labels, which are noisy for WT3/T4 pairs (R1-C3); part
    of its RQ2 gain may be learning BigCloneBench's labelling rather than functional similarity;
  - fine-tuning has costs the kernels do not: labelled data and 3.7–6.2 h of training per fold model, plus 2.8–4.0 h
    of corpus encoding per model (timing table).

**Response (draft):** We now report CodeBERT fine-tuned contrastively on BigCloneBench (5 folds by functionality,
with false positives as hard negatives) next to zero-shot CodeBERT in all RQs. Fine-tuning closes the gap on
functional similarity (MAP 0.149 → 0.437, on par with BM25 and above the tree kernels); on syntactic clones, the tree
kernels remain significantly better. We have revised the claims accordingly and limited our conclusions to the models
and settings evaluated.

---

## R1-C3: label noise and generalisability

> Java-only (BigCloneBench), AST parsing via GumTree, and known label noise are acknowledged but not quantitatively
> analysed for cross-language generalisability. (Suggestion: quantify BigCloneBench label-noise impact and discuss
> cross-language AST/tree-kernel limitations.)

Status: **open**. The options are recorded here; the user decides later. No manual labelling is possible, so options
that need human judgement are excluded.

### What the literature says (verified 2026-11-04)

- **Krinke & Ragkhitwetsagul, "BigCloneBench Considered Harmful for Machine Learning", IWSC 2022**
  (DOI 10.1109/IWSC55060.2022.00008): a manual sample of WT3/T4 pairs, **86%** false positives.
- **Follow-up, "How the Misuse of a Dataset Harmed Semantic Clone Detection", arXiv:2505.04311 (2025)**
  (check the authors and venue before citing): 406 WT3/T4 pairs, stratified over the 43 functionalities, judged on
  whether both methods have the same *main* functionality: 27 true, 379 false = **93.3%** false positives
  (Copy File 4.7% true, Zip Files 24.3%, Secure Hash 0%). The 93% figure belongs to this paper, not the 2022 one.
- The same paper states that T1, T2 and the moderate, strong and very strong T3 pairs are unproblematic (they are
  textually similar), and that BigCloneBench "can still be used for its original purpose, the evaluation of syntactic
  or textual clone detection". It also notes that no pair was manually validated, that at least 15% of the clones are
  subjective or have validation errors (cited from BigCloneBench's authors), and that pairs of different
  functionalities are not necessarily true negatives.

### Effect on each RQ

- **RQ1: largely unaffected, but not completely.**
  - Relevant = the query's T1/T2/VST3/ST3/MT3 clones, the types the critique calls unproblematic.
  - WT3/T4 pairs do not enter RQ1: the query's other same-functionality methods are removed from its ranking.
  - **Remaining exposure:** the non-relevant side. A method outside the query's functionality labels (a BigCloneBench
    false positive, or a true positive of another functionality) can still be a syntactic clone of the query. RQ1
    counts it as non-relevant. Only whitespace-identical copies are handled now (`exp_v2/data/fp_copies.tsv`: 368
    false positives for 146 queries, ignored). This penalises the syntactic methods most, so the kernels' RQ1 results
    are, if anything, conservative.
- **RQ2: directly affected.** Relevant = every method of the query's functionality, so the relevant set is dominated
  by WT3/T4 pairs, of which about 93% are not functionally similar by the stricter criterion. RQ2 therefore measures
  agreement with BigCloneBench's functionality labels, not functional similarity. Absolute values are not meaningful
  as functional similarity; comparisons between methods remain comparisons on the same labels, but a method trained on
  those labels (fine-tuned CodeBERT) is favoured.
- **RQ3 and RQ4:** both report two parts. The syntactic part (as RQ1: per clone type T1–MT3 and their mean,
  other same-functionality methods removed) does not use WT3/T4 pairs. The functional part (as RQ2: every
  same-functionality method relevant) does, and is affected like RQ2.

### Options for quantifying it (not decided)

**A. Bound the effect of false-positive labels (re-evaluation only).** Re-evaluate the existing runs with every false
positive ignored (as if unjudged) next to the current setting (non-relevant). If the conclusions hold at both
extremes, noise in the false-positive labels cannot overturn them. Needs an "ignore all false positives" option in
`exp_v2/eval/evaluate.py`. Addresses the RQ1 exposure above and the RQ2 non-relevant side; not the noise in RQ2's
relevant set.

**B. Count the Type-2 near-copies (script + re-evaluation).** Extend `exp_v2/prep/fp_copies.py` from
whitespace-identical copies to copies identical after normalising identifiers and literals (Type-2), for false
positives and for true positives of other functionalities. Report the counts as a direct measure of mislabelling,
and re-evaluate with them ignored in RQ1.

**C. Manual audit: excluded** (no manual labelling possible).

**D. RQ2: no correction possible without manual labels.** Instead: cite the 93.3% estimate, reframe RQ2 as agreement
with BigCloneBench's functionality labels, state that absolute RQ2 values do not measure functional
similarity, and flag fine-tuned CodeBERT's advantage from training on those labels (R1-C2a). An optional automatic
check is whether the method ranking in RQ2 holds per functionality, e.g. on Secure Hash and Zip Files, whose label
quality the follow-up reports; with only a few functionalities this is weak evidence.

### Cross-language limits (discussion only, no experiment)

- Language-agnostic: STK, SSTK and PTK work on any labelled ordered tree.
- Java-specific: node vocabulary and granularity from GumTree's Java parser (other parsers, e.g. tree-sitter or
  srcML, give trees of different shape and size); the variant D choice of which leaves carry lexical content; the
  tuned λ and μ; the overflow limits, which depend on tree size.
- Dynamically typed languages lack type declarations, which put lexical signal into the leaves.
- Clones across languages (e.g. Java to C#) cannot be matched by tree kernels without a shared AST; CodeBERT
  partly can.
- Future work: a multi-language benchmark (e.g. SemanticCloneBench, GPTCloneBench, CodeNet).

### Response (draft, depends on the options chosen)

We now discuss BigCloneBench's label quality explicitly. Following Krinke and Ragkhitwetsagul, who found about 93% of
sampled WT3/T4 pairs not to be functionally similar while T1–T3 pairs are reliable, RQ1 relies only on the reliable
clone types, whereas RQ2 measures agreement with BigCloneBench's functionality labels, and we interpret it as such.
[A/B: We bound the effect of mislabelled false positives by re-evaluating with all false positives ignored; the
conclusions hold at both extremes.] We added a discussion of what in our pipeline is specific to Java and GumTree and
what carries over to other languages.
