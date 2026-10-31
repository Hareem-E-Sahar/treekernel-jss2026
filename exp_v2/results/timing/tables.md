# Cost of evaluating the 100 RQ2 queries of one replicate set (one thread, 72,782-method corpus)

| Group | Method | Set-up (s) | Per query (s) | 100 queries (s) | Note |
|---|---|---|---|---|---|
| full ranking | STK | 45.8 | 6.733 | 719 |  |
| full ranking | SSTK | 40.8 | 6.977 | 738 |  |
| full ranking | PTK | 73.6 | 15.508 | 1624 |  |
| full ranking | BM25 |  | 0.700 | 70 | Elasticsearch took 0.646 s per query |
| full ranking | CodeBERT | 7.2 | 0.409 | 41 | encode + cosine; corpus embeddings precomputed |
| hybrid stage 1 | BM25 top 200 |  | 0.013 | 1 | Elasticsearch took 0.010 s |
| hybrid stage 2 (k=100) | STK | 0.1 | 0.057 | 6 | kernel evaluations alone 0.021 s per query |
| hybrid stage 2 (k=200) | STK | 0.1 | 0.093 | 9 | kernel evaluations alone 0.041 s per query |
| hybrid stage 2 (k=100) | SSTK | 0.1 | 0.054 | 5 | kernel evaluations alone 0.021 s per query |
| hybrid stage 2 (k=200) | SSTK | 0.1 | 0.091 | 9 | kernel evaluations alone 0.040 s per query |
| hybrid stage 2 (k=100) | PTK | 0.1 | 0.080 | 8 | kernel evaluations alone 0.045 s per query |
| hybrid stage 2 (k=200) | PTK | 0.1 | 0.144 | 14 | kernel evaluations alone 0.090 s per query |

## Hybrid against the full kernel ranking (per query)

| Kernel | k | Hybrid (stage 1 + 2), s | Full ranking, s | Speed-up |
|---|---|---|---|---|
| STK | 100 | 0.070 | 6.73 | 96× |
| STK | 200 | 0.107 | 6.73 | 63× |
| SSTK | 100 | 0.067 | 6.98 | 104× |
| SSTK | 200 | 0.105 | 6.98 | 67× |
| PTK | 100 | 0.093 | 15.51 | 166× |
| PTK | 200 | 0.157 | 15.51 | 98× |
