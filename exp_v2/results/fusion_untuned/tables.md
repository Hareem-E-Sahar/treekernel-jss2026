# Fusion with and without tuning W, and the hybrid (10 replicate sets, corpus with false positives)

## RQ1 (MAP, mean over the five types)

| Method | mean ± SD over the 10 seeds |
|---|---|
| PTK | 0.892 ± 0.009 |
| BM25 | 0.810 ± 0.008 |
| CodeBERT ft | 0.840 ± 0.010 |
| PTK+BM25 wsum, tuned W=0.9 | 0.918 ± 0.008 |
| PTK+BM25 wsum, W=0.5 (untuned) | 0.878 ± 0.010 |
| PTK+BM25 RRF (no parameter) | 0.896 ± 0.006 |
| PTK+CodeBERT ft wsum, tuned W=0.5 | 0.917 ± 0.008 |
| PTK+CodeBERT ft wsum, W=0.5 (untuned) | 0.917 ± 0.008 |
| PTK+CodeBERT ft RRF (no parameter) | 0.903 ± 0.009 |
| BM25→PTK hybrid, k=100 | 0.840 ± 0.006 |
| BM25→PTK hybrid, k=200 | 0.861 ± 0.006 |

| A | B | A − B | 95% CI |
|---|---|---|---|
| PTK+BM25 wsum, W=0.5 (untuned) | PTK+BM25 wsum, tuned W=0.9 | -0.039 * | -0.054 to -0.020 |
| PTK+BM25 wsum, W=0.5 (untuned) | PTK | -0.014 | -0.035 to +0.014 |
| PTK+BM25 wsum, W=0.5 (untuned) | BM25 | +0.069 * | +0.048 to +0.091 |
| PTK+BM25 wsum, tuned W=0.9 | PTK | +0.026 * | +0.017 to +0.036 |
| PTK+BM25 wsum, tuned W=0.9 | BM25 | +0.108 * | +0.071 to +0.143 |
| PTK+CodeBERT ft wsum, W=0.5 (untuned) | PTK+CodeBERT ft wsum, tuned W=0.5 | +0.000 | +0.000 to +0.000 |
| PTK+CodeBERT ft wsum, W=0.5 (untuned) | PTK | +0.025 * | +0.013 to +0.040 |
| PTK+CodeBERT ft wsum, W=0.5 (untuned) | CodeBERT ft | +0.078 * | +0.050 to +0.112 |
| PTK+CodeBERT ft wsum, tuned W=0.5 | PTK | +0.025 * | +0.013 to +0.040 |
| PTK+CodeBERT ft wsum, tuned W=0.5 | CodeBERT ft | +0.078 * | +0.050 to +0.112 |
| BM25→PTK hybrid, k=100 | PTK | -0.051 * | -0.084 to -0.013 |
| BM25→PTK hybrid, k=100 | BM25 | +0.031 * | +0.020 to +0.045 |
| BM25→PTK hybrid, k=100 | PTK+BM25 wsum, tuned W=0.9 | -0.077 * | -0.106 to -0.046 |
| BM25→PTK hybrid, k=200 | PTK | -0.030 * | -0.058 to -0.000 |
| BM25→PTK hybrid, k=200 | BM25 | +0.052 * | +0.033 to +0.072 |
| BM25→PTK hybrid, k=200 | PTK+BM25 wsum, tuned W=0.9 | -0.056 * | -0.082 to -0.032 |

## RQ2 (functional MAP)

| Method | mean ± SD over the 10 seeds |
|---|---|
| STK | 0.191 ± 0.021 |
| BM25 | 0.444 ± 0.021 |
| CodeBERT ft | 0.437 ± 0.030 |
| STK+BM25 wsum, tuned W=0.0 | 0.444 ± 0.021 |
| STK+BM25 wsum, W=0.5 (untuned) | 0.430 ± 0.023 |
| STK+BM25 RRF (no parameter) | 0.360 ± 0.021 |
| STK+CodeBERT ft wsum, tuned W=0.2 | 0.445 ± 0.030 |
| STK+CodeBERT ft wsum, W=0.5 (untuned) | 0.434 ± 0.029 |
| STK+CodeBERT ft RRF (no parameter) | 0.369 ± 0.023 |
| BM25→STK hybrid, k=100 | 0.439 ± 0.021 |
| BM25→STK hybrid, k=200 | 0.437 ± 0.021 |

| A | B | A − B | 95% CI |
|---|---|---|---|
| STK+BM25 wsum, W=0.5 (untuned) | STK+BM25 wsum, tuned W=0.0 | -0.015 * | -0.026 to -0.001 |
| STK+BM25 wsum, W=0.5 (untuned) | STK | +0.238 * | +0.174 to +0.326 |
| STK+BM25 wsum, W=0.5 (untuned) | BM25 | -0.015 * | -0.026 to -0.001 |
| STK+BM25 wsum, tuned W=0.0 | STK | +0.253 * | +0.186 to +0.345 |
| STK+BM25 wsum, tuned W=0.0 | BM25 | +0.000 | +0.000 to +0.000 |
| STK+CodeBERT ft wsum, W=0.5 (untuned) | STK+CodeBERT ft wsum, tuned W=0.2 | -0.011 * | -0.021 to -0.001 |
| STK+CodeBERT ft wsum, W=0.5 (untuned) | STK | +0.244 * | +0.186 to +0.325 |
| STK+CodeBERT ft wsum, W=0.5 (untuned) | CodeBERT ft | -0.003 | -0.016 to +0.012 |
| STK+CodeBERT ft wsum, tuned W=0.2 | STK | +0.255 * | +0.195 to +0.337 |
| STK+CodeBERT ft wsum, tuned W=0.2 | CodeBERT ft | +0.008 * | +0.003 to +0.014 |
| BM25→STK hybrid, k=100 | STK | +0.249 * | +0.182 to +0.338 |
| BM25→STK hybrid, k=100 | BM25 | -0.004 | -0.013 to +0.000 |
| BM25→STK hybrid, k=100 | STK+BM25 wsum, tuned W=0.0 | -0.004 | -0.013 to +0.000 |
| BM25→STK hybrid, k=200 | STK | +0.246 * | +0.180 to +0.333 |
| BM25→STK hybrid, k=200 | BM25 | -0.007 * | -0.018 to -0.001 |
| BM25→STK hybrid, k=200 | STK+BM25 wsum, tuned W=0.0 | -0.007 * | -0.018 to -0.001 |

## Cost per query (exp_v2/results/hybrid/timing.tsv)

| Step | mean ms |
|---|---|
| BM25 top 200 (first stage) | 14 |
| STK on the top 200 (second stage) | 112 |
| STK on the top 100 (second stage) | 62 |
| STK full ranking (72,782 methods) | 16,747 |
| SSTK on the top 200 (second stage) | 116 |
| SSTK on the top 100 (second stage) | 63 |
| SSTK full ranking (72,782 methods) | 16,520 |
| PTK on the top 200 (second stage) | 259 |
| PTK on the top 100 (second stage) | 144 |
| PTK full ranking (72,782 methods) | 35,588 |
