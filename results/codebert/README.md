# CodeBERT baseline (zero-shot and fine-tuned)

Added after reviewers objected to calling zero-shot CodeBERT a strong embedding baseline. CodeBERT appears wherever BM25
does (RQ1, RQ2, RQ4, E5, RQ5), so the comparison covers lexical (BM25), embedding (CodeBERT) and structural (tree kernel) methods.
Code: `embed/codebert.py`, `scripts/run_codebert.sh`, `scripts/run_codebert_rq4.sh`. All tables: `results/eval/tables.md`.

## Setup

- Model: `microsoft/codebert-base`. Embedding: CLS token, L2-normalised; score = cosine. Inputs are truncated to 512 tokens
  (41% of methods are longer; the median is 427 tokens). CPU only, bf16 autocast.
- Runs use the same format as the other methods. The run stores the cosine as logk, so evaluate.py's score is exp(cos), which
  gives the same ranking as the cosine.
- **Fine-tuning:** 5 folds by functionality (`data/codebert/folds.tsv`). Functionalities that share an evaluation query are
  kept in the same fold. Folds hold 218/92/92/91/91 evaluation queries. The model for fold k trains only on methods whose
  functionalities all lie outside fold k. Each query (evaluation, tuning and timing) is scored by its own fold's model, so no
  model ever sees a query's functionality. CodeXGLUE's BCB train split could not be used: it contains 212 of the 584
  evaluation queries.
- **Recipe** (fixed, not tuned):
  - bi-encoder, symmetric InfoNCE with in-batch negatives, temperature 0.05;
  - 16 pairs per batch, drawn from 16 distinct functionalities (functionalities sampled ∝ sqrt(size));
  - AdamW, lr 2e-5, weight decay 0.01, 500 steps, 10% warm-up then linear decay, grad clip 1.0;
  - training inputs truncated to 256 tokens (512 ran out of memory); retrieval still uses 512.
- **Training:** loss fell from about 2.95 (mean of the first 25 steps) to 0.18–0.44 (mean of the last 25 steps) in every fold.
  Each fold took 75–87 min on 8 threads, 6.6 h in total.

## Results (main corpus; paired bootstrap, 95%)

| | T1 | T2 | VST3 | ST3 | MT3 | RQ1 mean | RQ2 MAP@R |
|---|---|---|---|---|---|---|---|
| D PTK (tuned) | 1.000 | 1.000 | 1.000 | 0.973 | 0.654 | **0.926** | 0.165 |
| BM25 | 1.000 | 0.969 | 0.989 | 0.854 | 0.630 | 0.888 | 0.477 |
| CodeBERT zero-shot | 1.000 | 0.992 | 0.981 | 0.882 | 0.485 | 0.868 | 0.171 |
| CodeBERT fine-tuned | 1.000 | 0.990 | 0.983 | 0.906 | **0.673** | 0.910 | **0.486** |

- **Fine-tuning helps a lot.** RQ1 mean rises by 0.042 and RQ2 MAP@R by 0.315; both gains are significant.
- **RQ1:** PTK vs fine-tuned CodeBERT:
  - mean +0.015, not significant (CI −0.003 to +0.034);
  - PTK is significantly better on ST3 (+0.068) and VST3 (+0.017);
  - MT3 differs by −0.019, not significant.
  - STK and SSTK tie with fine-tuned CodeBERT.
  - Fine-tuned CodeBERT beats BM25 (+0.022, significant).
- **RQ2:** fine-tuned CodeBERT and BM25 are level (−0.009, not significant). Every tree kernel is significantly worse
  (by 0.24–0.32).
- **RQ4:**
  - PTK and fine-tuned CodeBERT are complementary on MT3: PTK alone finds 9% of the relevant items, CodeBERT alone 16%.
  - Fusing PTK with fine-tuned CodeBERT (W=0.6) gives RQ1 mean 0.955 and MT3 0.796, significantly better than both
    components. This is close to PTK + BM25 (0.957 / 0.810).
  - For RQ2, fusing STK with fine-tuned CodeBERT selects W=0.1 and reaches 0.487, the same as CodeBERT alone (n.s.).
    RRF falls to 0.360.
- **E5 (false positives added):**
  - Fine-tuned CodeBERT drops further than the tree kernels (RQ1 mean −0.079; MAP@R −0.237, to 0.249, about the same as
    BM25's 0.259).
  - PTK and STK are significantly better than fine-tuned CodeBERT on the RQ1 mean (+0.051, +0.023) but significantly worse
    on MAP@R.
- **RQ5** (1 thread):
  - 0.37 s per query: encode the query, then cosine against the stored embeddings. BM25 takes 0.12 s; D STK and D PTK take
    1.5–3.4 s.
  - Preparation: about 6,200 s to encode the corpus one method at a time (estimated), or 1,503 s with 8 threads and
    batches of 32.
  - Fine-tuning adds 6.6 h.

## Caveats

- Truncation to 512 tokens at retrieval (256 in training) hurts long methods.
- A single fixed recipe; no hyperparameter search.
- Fold 0 is larger (218 queries), because functionalities that share queries are kept in one fold.
- RQ4 fusion uses only the fine-tuned model.
- The E5 T1 drop (also seen for the other methods) comes from exact copies of three queries among the false positives
  (see `results/e5/README.md`).
