# Evaluation design: ground truth, metrics, averaging and stratification

*Written 2026-10-13 from the discussion with the user. Decisions are marked **Decided**; everything else is a proposal. Numbers come from the full BigCloneBench database (`data/full_bcb/`).*

## 1. Ground truth per research question

Corpus: the 14,780 true-positive methods minus 101 excluded for float overflow, i.e. 14,679 (`PLAN.md` §4.1). Every query is ranked against every other method in the corpus.

| RQ | Query | Relevant (should rank high) | Not relevant | Removed from the ranking |
|---|---|---|---|---|
| **RQ1** syntactic, per clone type t ∈ {T1, T2, VST3, ST3, MT3} | a method with at least one clone of type t | the query's clones of type t | methods from other tasks (functionalities) | the query's other clones (other types, mostly WT3/T4) |
| **RQ2** functional | a uniformly sampled true positive | every method implementing the same task, i.e. its clones of any type | methods from other tasks | nothing |
| **RQ3** representation | as RQ1 and RQ2: the same ground truths, compared across kernels and tree variants | | | |
| **RQ4** complementarity | as RQ1 and RQ2: the same ground truths, compared query by query and clone by clone between tree kernels and BM25 | | | |
| **RQ5** cost | no ground truth | | | |
| **Tuning** | 50 methods, 10 per type T1–MT3 (**Decided**) | as RQ1 | as RQ1 | as RQ1 |

**Why RQ1 removes the query's other clones.** Example: a query has 3 Type-1 copies, 2 moderate Type-3 clones and 900 WT3/T4 clones. For the Type-1 evaluation, the 3 copies are ranked against about 13,900 methods from other tasks, and the other 902 clones are taken out of the list.
- Counting them as *wrong* would punish a measure for finding real clones.
- Counting them as *right* would mix Type 4 into a syntactic evaluation.

The question becomes simply: *does the measure put a Type-t clone above unrelated code?*

**Where "relevant" comes from.** A pair is relevant if it is in BCB's `clones` table. Its type follows the BigCloneEval convention: T1/T2 from `syntactic_type`; T3 graded by min(line, token similarity): VST3 ≥ 0.9, ST3 ≥ 0.7, MT3 ≥ 0.5. For RQ2, "same task" is equivalent to the `clones` table to within 288 pairs out of 8.58M.

**Caveats.**
- **Unlabelled clones.** Methods from other tasks are *assumed* not to be clones, but a few may be genuinely similar code that BCB never labelled (e.g. Copy File vs Copy Directory). A "wrong" result ranked first may be a correct, unlabelled clone. Worth checking by hand for a sample of top-ranked "non-clones".
- **Label noise.** Many WT3/T4 labels are questionable (Krinke & Ragkhitwetsagul). This affects RQ2 more than RQ1.

## 2. Metrics

**Decided:** every experiment computes **all** metrics below. Which ones appear in the paper is decided later.

### 2.1 Definitions

For one query: the ranked list of candidates, and R = the number of relevant candidates (R_t for type t in RQ1). The ranking excludes the query itself and, for RQ1, the removed items.

| Metric | Definition | What it answers |
|---|---|---|
| **P@k** (k = 1, 5, 10) | relevant items in the top k, divided by k | how clean are the first k results? |
| **Recall@k** (k = 1, 5, 10, 100) | relevant items in the top k, divided by R | what share of the relevant items is in the top k? |
| **R-precision** | relevant items in the top R, divided by R | P@k with k chosen per query as R |
| **MRR** | mean of 1 / (rank of the first relevant item) | is at least one relevant item found early? |
| **MAP** (full) | mean over relevant items of the precision at that item's rank | quality of the whole ranking, with partial credit |
| **MAP@R** | like MAP, but only relevant items within the top R count, and the sum is divided by R (Musgrave et al. 2020) | standard code-retrieval metric (POJ-104, CodeNet) |
| **Median / mean rank** of the relevant items | position in the list, also as a percentile | where do relevant items land? Diagnostic. |

**Ties.** Many T1/T2 clones score exactly 1.0, and BM25 scores also tie. A tie is treated as if every tied item were at the average of the tied positions. For example, if the relevant item and two others share ranks 1–3, it counts as rank 2. Breaking ties arbitrarily would let file order decide results. *Implementation (`eval/ranking.py`, 2026-10-16):* tied items take their expected positions under a random order within the tie. Cut-off metrics (P@k, Recall@k, R-precision) use the expected number of relevant items above the cut-off. For rank metrics, the j-th of h relevant items in a tie group of m items starting at position a is placed at a − 1 + j(m+1)/(h+1). This keeps precision ≤ 1 when several relevant items tie, and the mean rank equals the average of the tied positions.

### 2.2 How many relevant items queries have, and what that means

**RQ1:** clones of type t per method.

| Type | Median | Queries with exactly 1 | Queries with ≥ 10 | Largest |
|---|---|---|---|---|
| T1 | 3 | 34% | 36% | 148 |
| T2 | 1 | 51% | 17% | 53 |
| VST3 | 2 | 42% | 12% | 108 |
| ST3 | 3 | 32% | 22% | 156 |
| MT3 | 8 | 16% | 47% | 240 |

**RQ2:** hundreds to thousands of relevant items per query. Copy File alone has 3,049 methods. The smallest task has 10, so R ≥ 9.

What that means for each metric:

| Metric | RQ1 (few relevant items, 1–240) | RQ2 (many relevant items) |
|---|---|---|
| P@5, P@10 | **Misleading.** With 1 relevant clone the best possible P@10 is 0.1, which is the case for half the T2 queries. Use Recall@k instead. | Good: almost every query has more than 10 relevant items. |
| Recall@k | Good. | Tiny for large tasks (10 of 3,049 is at most 0.3%); not informative. |
| MAP@R | Harsh: with R_t = 1 it becomes all-or-nothing (rank 1 → 1, rank 2 → 0). | **Good**, and the standard in code retrieval. It ignores how thousands of WT3/T4 clones are ordered deep in the list. |
| MAP (full) | **Good:** copes with 1–240 relevant items and gives partial credit (lone clone at rank 2 → 0.5). | Dominated by positions thousands of places down. |
| MRR | Good secondary view: "is at least one copy found?" | Nearly saturated (pilot: 81% correct first result), so weakly discriminating. |

**Proposed primary metric** (used for tuning and significance tests; all others are still computed):
- **RQ1: MAP per clone type.**
- **RQ2: MAP@R.**
- **Tuning objective:** average of MAP over the five types, on the tuning queries.

## 3. Averaging

**Decided:** report **micro and macro averages**.

- **Micro:** the mean over queries. Every query counts equally, so tasks with many queries weigh more. This reflects the benchmark's natural mix.
- **Macro over represented functionalities:** first the mean per task, over that task's queries, then the mean over tasks. Every task that has at least one query counts equally.
  - A query that belongs to two tasks (209 methods do) counts in each with weight ½.
  - Report how many tasks are represented and the number of queries per task. A task with one or two queries makes the macro average noisy.

**Why it matters here:** the query pools are concentrated.

| Query pool | Methods | Largest task | Tasks making up half the pool |
|---|---|---|---|
| T1 | 3,827 | Copy File, 20% | 6 |
| T2 | 1,032 | Copy File, 32% | 3 |
| VST3 | 2,035 | Copy File, 24% | 5 |
| ST3 | 4,739 | Copy File, 22% | 5 |
| MT3 | 7,826 | Copy File, 22% | 4 |
| all true positives (RQ2) | 14,992 | Copy File, 20% | 5 |

(Methods in two tasks are counted in both.)

With micro averaging alone, "tree kernels beat BM25" could really mean "tree kernels beat BM25 on file-copying code". If micro and macro agree, the conclusion is robust; if they disagree, that is itself a finding.

**Significance tests** (Wilcoxon signed-rank, paired by query) use queries as the unit, i.e. they test the micro comparison.

## 4. Breaking results down by subgroup

**Terminology (clarified 2026-10-13).** We do **not** use stratified sampling, i.e. choosing queries so that groups are balanced. Queries are drawn at random. "Stratification" in this section means **breaking the results down by subgroup after sampling**: grouping the per-query results by task or category. That needs no extra computation.

The one exception is clone type. RQ1 draws 100 queries from each type's pool, which is stratified sampling by clone type. It's unavoidable, because RQ1 asks about each type separately. Within each type, queries are random.

**Decided 2026-10-13:**
- **Use:** API-centred vs algorithmic tasks (§4.2).
- **Later:** method size (§4.3), documented now and analysed after the main results.
- **Not selected:** same- vs cross-project (§4.1), number of relevant items (§4.4) and lexical-similarity bands (§4.5). They stay documented here. §4.1's finding (88% of T1 pairs are same-project copies) is listed as a threat to validity.

Grouping can in principle be used at two stages:
- **Sampling:** forcing balance in which queries are drawn.
- **Reporting:** breaking results down after the fact. This costs no extra computation, because every query's result is kept.

Apart from clone type, which defines RQ1's query sets, **all of these are proposed for reporting only**. They are exploratory, so present them as analyses, not as additional hypothesis tests.

### 4.1 Same-project vs cross-project clones (not selected; kept as a threat to validity)

BCB records each method's project (known for all 14,780 true positives, 4,871 projects). The share of clone pairs **within one project** differs enormously by type:

| Type | Same-project pairs |
|---|---|
| T1 | 42,533 / 48,116 = **88%** |
| T2 | 588 / 4,234 = 14% |
| VST3 | 2,386 / 4,577 = 52% |
| ST3 | 5,476 / 16,818 = 33% |
| MT3 | 3,586 / 86,341 = 4% |

Same-project T1 clones are often the same file in different branches or versions (paths such as `/branches/version-2/trunk/...`). They are trivial for any measure, and they could make T1 look solved. Cross-project clones are the realistic case for code search.

Proposal: report RQ1 separately for same-project and cross-project clones. If the cross-project T1 pool is too small for a reliable estimate, consider stratifying the T1 *sampling* by this as well.

### 4.2 API-centred vs algorithmic tasks (**selected**; final definition in §4.8)

This bears directly on lexical vs syntactic similarity. Proposed grouping of BCB's 43 tasks, **to be reviewed by the user**:

- **Algorithmic (8 tasks, 1,563 true positives):** Bubble Sort Array, Get Prime Factors, Shuffle Array in Place, Binary Search, Fibonacci, GCD, Transpose a Matrix, Test Palindrome. These are defined by control flow and arithmetic, with generic names (`i`, `j`, `a`).
- **Borderline (3 tasks, 874):** Resize Array, Delete Folder and Contents, Parse CSV File.
- **API-centred (32 tasks, 12,555):** the rest, e.g. Download From Web, Connect to FTP Server, Send E-Mail, Secure Hash. These are defined by which library calls are made.

Hypothesis: BM25 does relatively better on API-centred tasks, where shared vocabulary such as `getConnection` carries meaning, and tree kernels do relatively better on algorithmic tasks, where structure carries meaning. BCB's keyword-search construction also differs between the two: API names for API-centred tasks, code patterns for algorithmic ones.

The pools are uneven:

| Type | API-centred | Algorithmic | Borderline |
|---|---|---|---|
| T1 | 24,506 | 22,692 | 918 |
| T2 | 4,104 | 78 | 52 |
| VST3 | 3,716 | 369 | 492 |
| ST3 | 12,230 | 3,328 | 1,260 |
| MT3 | 66,822 | 15,518 | 4,001 |

Algorithmic tasks are only 11% of true positives but 47% of T1 pairs, i.e. lots of identical copies of a few sorting and maths routines. T2 is almost entirely API-centred.

### 4.3 Method size (**later**: analyse after the main results)

Tree kernels are normalised, but very small methods share many fragments with everything, and very large ones are expensive and diverse. BM25 has its own length normalisation. Report results by size quartile of the query: BCB's `tokens` column or tree node count. This connects to the cost results (RQ5).

### 4.4 Number of relevant items (diagnostic; not selected)

Queries with one clone versus queries in large duplicate clusters (up to 240 clones) behave differently, and several metrics depend on R directly (§2.2). Report results by R band (1, 2–9, ≥ 10) as a diagnostic.

### 4.5 Lexical similarity of the clone pair (not selected)

BCB stores line and token similarity for every clone pair; this is what grades T3. A finer binning, e.g. in steps of 0.1, would show where along the lexical-similarity scale tree kernels start to beat BM25, or stop beating it. This is closely tied to the clone types themselves, so it partly repeats RQ1; it's optional.

### 4.6 Not recommended

- **Hosting site** (SourceForge vs Google Code, `host` column): no reason to expect an effect.
- **Licence:** same.

### 4.7 Stratifying by task (functionality) vs by task category

These two are often confused, but they serve different purposes. They are also nested: every category is a group of tasks.

| | By task (43 BCB functionalities) | By category (API-centred vs algorithmic) |
|---|---|---|
| **Purpose** | Robustness: is a result driven by a few large tasks (Copy File is 20–32% of every pool)? | Hypothesis: does the *kind* of code decide whether lexical or syntactic similarity works better? |
| **Where the labels come from** | BCB itself (objective) | A grouping we define (see criteria below) |
| **Number of strata** | 43, many with no queries | 2 (plus borderline) |
| **Queries per stratum with 100 random queries** | about 0–25; most tasks get 0–3 | API about 74–85, algorithmic only **9–19**, borderline 5–9 |
| **What it supports** | the macro average (decided); per-task results are too noisy to test | a per-group comparison and a test of whether the BM25-vs-tree-kernel gap differs between groups, *if each group has enough queries* |
| **Confounds** | none beyond imbalance | Algorithmic tasks have many duplicate copies (47% of all T1 pairs). Their BCB search was by code pattern instead of names, which favours structural measures by construction, just as name searches favour BM25 (§4.2, PLAN §8). |

**Both are used.** Task stratification gives the macro average. Category stratification gives the hypothesis test. The macro average can also be computed *within* each category.

**Problem: with random sampling, the algorithmic group is too small.** Expected algorithmic queries out of 100 random ones per pool:

| Pool | API-centred | Algorithmic | Borderline | Algorithmic tasks with any method |
|---|---|---|---|---|
| T1 | 74 | 17 | 9 | 8 |
| T2 | 85 | 9 | 5 | 6 |
| VST3 | 81 | 11 | 8 | 5 |
| ST3 | 74 | 19 | 7 | 8 |
| MT3 | 80 | 13 | 7 | 8 |
| RQ2 (all true positives) | 84 | 10 | 6 | 8 |

About 10–19 queries cannot support a per-group comparison: the standard error of a MAP average is roughly 0.15/√n, i.e. about ±0.04 for 15 queries.

**Proposal: stratified sampling by category, then reweighting.**
- Per clone type, and for RQ2, sample **50 API-centred and 50 algorithmic** queries instead of 100 random ones. Borderline tasks are left out of the category comparison, or sampled separately in small numbers.
- Overall (micro) averages are then **reweighted to the natural proportions**, so they still describe the benchmark as it is. Example: if the natural mix is 85% API / 15% algorithmic, overall = 0.85 × API mean + 0.15 × algorithmic mean.
- The number of queries and the cost are unchanged.
- **Exception, T2:** the algorithmic T2 pool has only ~90 methods, and 65 of them come from one task (Transpose a Matrix). Algorithmic T2 results would effectively be Transpose-a-Matrix results. Either cap the queries per task, or report algorithmic T2 with this caveat.

**Criteria for the category (decision needed).**

- **(a) Judgement: what defines the task.** Tasks defined by computation on plain data with generic names are *algorithmic*: Bubble Sort, Get Prime Factors, Shuffle Array in Place, Binary Search, Fibonacci, GCD, Transpose a Matrix, Test Palindrome (8). Tasks defined by which library calls are made are *API-centred*. Borderline: Resize Array, Delete Folder and Contents, Parse CSV File.
- **(b) Objective: how BCB found the task's candidates** (`functionalities.search_heuristic`).
  - *Code-pattern* tasks were found by a regex over code shape with any identifier names: Bubble Sort (`a[i] = a[i+1]`), Get Prime Factors (`while (n % i == 0)`), Binary Search (`= (a + b) / 2`), Fibonacci (`return f(n-1) + f(n-2)`), GCD (`while (x != 0) … x = y % x`) and Transpose a Matrix (`a[i][j] = b[j][i]`) (6).
  - *Name* tasks were found by API names or keywords: all others. That includes Shuffle Array in Place (`random.nextInt`), Test Palindrome (the word `palindrome`), and the three borderline tasks (`arraycopy`, `listFiles`, `readLine`).

(a) and (b) agree on 6 of the 8 algorithmic tasks and differ on Shuffle and Palindrome.
- **For (b):** it is reproducible without a human judge, there is no borderline group, and it ties the stratum directly to the construction bias. It answers "are measures favoured by how BCB found the clones?"
- **Against (b):** for exactly that reason, a difference between groups may come from how the benchmark was built rather than from the kind of code.
- **For (a):** it matches the intuitive hypothesis ("algorithmic code vs API code").
- **Against (a):** a judgement call. A second person should check it, and the agreement be reported.

### 4.8 Decisions (2026-10-13)

- **Category criterion: (b), BCB's search method.**
  - **Pattern tasks (6):** Bubble Sort Array (7), Get Prime Factors (12), Binary Search (14), Fibonacci (20), GCD (26), Transpose a Matrix (41).
  - **Name tasks:** the other 37, including Shuffle Array in Place and Test Palindrome. There is no borderline group.
- **Sampling stays random (simple).** No 50/50 stratified sampling. Results are broken down afterwards:
  - **by task:** for the macro average;
  - **by category:** for the hypothesis.
- **Sensitivity analysis: bootstrap over queries** (decided 2026-10-13). The question is whether conclusions depend on *which* random queries were drawn.
  - For every reported average and difference, resample the queries with replacement (e.g. 10,000 times) and report 95% intervals, plus how often each conclusion holds across resamples. Examples: "PTK beats SSTK in 99.8% of resamples"; "tree kernels beat BM25 on T1 in X%".
  - This reuses existing results, so it costs nothing extra.
  - Limitation: it can't detect a sample that is unrepresentative in a systematic way. Random sampling guards against that.
  - *Optional, not planned:* replicate the final configurations on a second random query set (new seed).
- **Consequence for the category hypothesis.** With random sampling, the pattern group is small. Expected pattern-task queries out of 100 random ones:

  | Pool | Pattern-task queries | Largest pattern task's share of that group |
  |---|---|---|
  | T1 | ~13 | 38% |
  | T2 | ~9 | 73% (Transpose a Matrix) |
  | VST3 | ~11 | 68% |
  | ST3 | ~15 | 31% |
  | MT3 | ~13 | 32% |
  | RQ2 | ~9 | 37% |

  The category comparison is therefore **exploratory**: report it with bootstrap intervals and expect them to be wide (about ±0.04 MAP for ~13 queries). If it shows a clear trend, a follow-up with more pattern-task queries can confirm it.
- **Primary metrics confirmed:** MAP per clone type for RQ1; MAP@R for RQ2; tuning objective = average MAP over the five types. All metrics are still computed.

## 5. Open points

All open points from 2026-10-13 are resolved (§4.8). The only caveat left: algorithmic/pattern T2 results are dominated by Transpose a Matrix; report them with that caveat.
