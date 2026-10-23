# Replication over 10 query sets

Main corpus (14,679 true positives; no false positives). Seeds 55, 1375, 2084, 2802, 3389, 3501, 6251, 8241, 8828, 9080 (the user's seeds from the earlier study); each replicate = 100 queries per clone type + 100 functional queries (`exp_v2/data/replicates/`, a copy of `data/pools/replicates/`). Variant D at the tuned settings; fusion at the W tuned on the tuning queries. MAP per type, mean5 = mean of the five types, functional = MAP@R.

## Across replicates: mean ± SD (min–max)

| Method | T1 | T2 | VST3 | ST3 | MT3 | mean5 | functional |
|---|---|---|---|---|---|---|---|
| D STK | 1.000 ± 0.000 (1.000–1.000) | 0.999 ± 0.002 (0.995–1.000) | 1.000 ± 0.002 (0.995–1.000) | 0.967 ± 0.008 (0.953–0.978) | 0.661 ± 0.041 (0.583–0.712) | 0.925 ± 0.008 (0.910–0.936) | 0.242 ± 0.021 (0.210–0.273) |
| D SSTK | 1.000 ± 0.000 (1.000–1.000) | 0.999 ± 0.001 (0.997–1.000) | 0.999 ± 0.003 (0.990–1.000) | 0.970 ± 0.010 (0.953–0.981) | 0.668 ± 0.041 (0.588–0.716) | 0.927 ± 0.009 (0.909–0.938) | 0.242 ± 0.021 (0.208–0.276) |
| D PTK | 1.000 ± 0.000 (1.000–1.000) | 1.000 ± 0.000 (1.000–1.000) | 0.995 ± 0.006 (0.981–1.000) | 0.969 ± 0.013 (0.954–0.991) | 0.709 ± 0.034 (0.654–0.771) | 0.935 ± 0.007 (0.925–0.947) | 0.212 ± 0.022 (0.180–0.257) |
| BM25 | 1.000 ± 0.000 (1.000–1.000) | 0.972 ± 0.011 (0.948–0.988) | 0.973 ± 0.009 (0.959–0.985) | 0.895 ± 0.022 (0.851–0.920) | 0.657 ± 0.034 (0.615–0.723) | 0.899 ± 0.007 (0.889–0.915) | 0.555 ± 0.021 (0.527–0.598) |
| CodeBERT zs | 1.000 ± 0.000 (1.000–1.000) | 0.982 ± 0.009 (0.967–0.998) | 0.978 ± 0.011 (0.959–0.993) | 0.902 ± 0.014 (0.884–0.921) | 0.579 ± 0.037 (0.524–0.626) | 0.888 ± 0.009 (0.878–0.899) | 0.203 ± 0.014 (0.189–0.227) |
| CodeBERT ft | 1.000 ± 0.000 (1.000–1.000) | 0.988 ± 0.010 (0.971–1.000) | 0.989 ± 0.010 (0.969–1.000) | 0.928 ± 0.014 (0.905–0.945) | 0.724 ± 0.022 (0.693–0.753) | 0.926 ± 0.006 (0.912–0.933) | 0.577 ± 0.030 (0.534–0.623) |
| PTK+BM25 wsum | 1.000 ± 0.000 (1.000–1.000) | 1.000 ± 0.000 (1.000–1.000) | 0.998 ± 0.004 (0.990–1.000) | 0.987 ± 0.008 (0.973–1.000) | 0.826 ± 0.029 (0.775–0.878) | 0.962 ± 0.006 (0.952–0.974) | 0.329 ± 0.024 (0.297–0.367) |
| PTK+BM25 RRF | 1.000 ± 0.000 (1.000–1.000) | 1.000 ± 0.000 (0.999–1.000) | 0.998 ± 0.004 (0.992–1.000) | 0.972 ± 0.012 (0.954–0.986) | 0.777 ± 0.028 (0.731–0.816) | 0.949 ± 0.006 (0.939–0.958) | 0.389 ± 0.022 (0.366–0.428) |
| PTK+CodeBERT ft wsum | 1.000 ± 0.000 (1.000–1.000) | 1.000 ± 0.000 (1.000–1.000) | 0.997 ± 0.004 (0.991–1.000) | 0.991 ± 0.004 (0.987–1.000) | 0.860 ± 0.024 (0.826–0.893) | 0.970 ± 0.005 (0.963–0.976) | 0.518 ± 0.023 (0.485–0.551) |
| PTK+CodeBERT ft RRF | 1.000 ± 0.000 (1.000–1.000) | 0.996 ± 0.005 (0.986–1.000) | 0.996 ± 0.004 (0.987–1.000) | 0.986 ± 0.008 (0.977–0.998) | 0.821 ± 0.026 (0.775–0.862) | 0.960 ± 0.005 (0.950–0.967) | 0.411 ± 0.019 (0.382–0.441) |
| STK+BM25 wsum | 1.000 ± 0.000 (1.000–1.000) | 0.972 ± 0.011 (0.948–0.988) | 0.973 ± 0.009 (0.959–0.985) | 0.895 ± 0.022 (0.851–0.920) | 0.657 ± 0.034 (0.615–0.723) | 0.899 ± 0.007 (0.889–0.915) | 0.555 ± 0.021 (0.527–0.598) |
| STK+BM25 RRF | 1.000 ± 0.000 (1.000–1.000) | 0.998 ± 0.004 (0.988–1.000) | 1.000 ± 0.001 (0.996–1.000) | 0.960 ± 0.017 (0.932–0.977) | 0.716 ± 0.037 (0.655–0.774) | 0.935 ± 0.008 (0.922–0.947) | 0.402 ± 0.020 (0.375–0.428) |
| STK+CodeBERT ft wsum | 1.000 ± 0.000 (1.000–1.000) | 0.993 ± 0.008 (0.981–1.000) | 0.993 ± 0.008 (0.979–1.000) | 0.953 ± 0.007 (0.943–0.964) | 0.756 ± 0.028 (0.717–0.796) | 0.939 ± 0.005 (0.931–0.945) | 0.578 ± 0.029 (0.534–0.622) |
| STK+CodeBERT ft RRF | 1.000 ± 0.000 (1.000–1.000) | 0.996 ± 0.005 (0.986–1.000) | 0.997 ± 0.005 (0.986–1.000) | 0.979 ± 0.014 (0.955–0.997) | 0.771 ± 0.034 (0.707–0.834) | 0.949 ± 0.006 (0.939–0.960) | 0.436 ± 0.018 (0.405–0.465) |

## Comparisons per replicate

Paired query bootstrap within each replicate (2,000 resamples). Better / n.s. / worse = number of the 10 replicates in which A is significantly better than B, not significantly different, significantly worse. Mean Δ = mean of A − B over replicates.

| A | B | Measure | Mean Δ (min–max) | Better / n.s. / worse |
|---|---|---|---|---|
| D PTK | BM25 | T1 | +0.000 (+0.000 to +0.000) | 0 / 10 / 0 |
| D PTK | BM25 | T2 | +0.028 (+0.012 to +0.052) | 10 / 0 / 0 |
| D PTK | BM25 | VST3 | +0.022 (+0.002 to +0.041) | 3 / 7 / 0 |
| D PTK | BM25 | ST3 | +0.074 (+0.050 to +0.116) | 9 / 1 / 0 |
| D PTK | BM25 | MT3 | +0.052 (-0.018 to +0.122) | 2 / 8 / 0 |
| D PTK | BM25 | mean5 | +0.035 (+0.014 to +0.047) | 9 / 1 / 0 |
| D PTK | BM25 | functional | -0.343 (-0.376 to -0.322) | 0 / 0 / 10 |
| D PTK | CodeBERT ft | T1 | +0.000 (+0.000 to +0.000) | 0 / 10 / 0 |
| D PTK | CodeBERT ft | T2 | +0.012 (+0.000 to +0.029) | 2 / 8 / 0 |
| D PTK | CodeBERT ft | VST3 | +0.006 (-0.011 to +0.031) | 3 / 7 / 0 |
| D PTK | CodeBERT ft | ST3 | +0.041 (+0.023 to +0.064) | 3 / 7 / 0 |
| D PTK | CodeBERT ft | MT3 | -0.015 (-0.048 to +0.032) | 0 / 10 / 0 |
| D PTK | CodeBERT ft | mean5 | +0.009 (-0.001 to +0.021) | 1 / 9 / 0 |
| D PTK | CodeBERT ft | functional | -0.366 (-0.429 to -0.323) | 0 / 0 / 10 |
| CodeBERT ft | BM25 | T1 | +0.000 (+0.000 to +0.000) | 0 / 10 / 0 |
| CodeBERT ft | BM25 | T2 | +0.017 (-0.002 to +0.043) | 4 / 6 / 0 |
| CodeBERT ft | BM25 | VST3 | +0.016 (-0.012 to +0.037) | 4 / 6 / 0 |
| CodeBERT ft | BM25 | ST3 | +0.033 (-0.014 to +0.091) | 1 / 9 / 0 |
| CodeBERT ft | BM25 | MT3 | +0.067 (+0.013 to +0.095) | 6 / 4 / 0 |
| CodeBERT ft | BM25 | mean5 | +0.027 (+0.014 to +0.037) | 8 / 2 / 0 |
| CodeBERT ft | BM25 | functional | +0.022 (-0.002 to +0.074) | 2 / 8 / 0 |
| D STK | BM25 | mean5 | +0.026 (+0.012 to +0.035) | 8 / 2 / 0 |
| D STK | BM25 | functional | -0.313 (-0.356 to -0.287) | 0 / 0 / 10 |
| D SSTK | BM25 | mean5 | +0.028 (+0.011 to +0.037) | 8 / 2 / 0 |
| D SSTK | BM25 | functional | -0.313 (-0.356 to -0.288) | 0 / 0 / 10 |
| D STK | CodeBERT ft | mean5 | -0.001 (-0.016 to +0.017) | 0 / 9 / 1 |
| D STK | CodeBERT ft | functional | -0.335 (-0.390 to -0.291) | 0 / 0 / 10 |
| D SSTK | CodeBERT ft | mean5 | +0.001 (-0.017 to +0.017) | 0 / 9 / 1 |
| D SSTK | CodeBERT ft | functional | -0.335 (-0.389 to -0.292) | 0 / 0 / 10 |
| CodeBERT ft | CodeBERT zs | mean5 | +0.038 (+0.022 to +0.048) | 9 / 1 / 0 |
| CodeBERT ft | CodeBERT zs | functional | +0.374 (+0.324 to +0.415) | 10 / 0 / 0 |
| PTK+BM25 wsum | D PTK | ST3 | +0.018 (+0.006 to +0.029) | 8 / 2 / 0 |
| PTK+BM25 wsum | D PTK | MT3 | +0.118 (+0.070 to +0.142) | 10 / 0 / 0 |
| PTK+BM25 wsum | D PTK | mean5 | +0.028 (+0.018 to +0.035) | 10 / 0 / 0 |
| PTK+BM25 wsum | BM25 | ST3 | +0.092 (+0.066 to +0.134) | 10 / 0 / 0 |
| PTK+BM25 wsum | BM25 | MT3 | +0.170 (+0.096 to +0.237) | 10 / 0 / 0 |
| PTK+BM25 wsum | BM25 | mean5 | +0.063 (+0.044 to +0.073) | 10 / 0 / 0 |
| PTK+BM25 RRF | D PTK | ST3 | +0.003 (-0.008 to +0.023) | 0 / 10 / 0 |
| PTK+BM25 RRF | D PTK | MT3 | +0.068 (+0.019 to +0.112) | 8 / 2 / 0 |
| PTK+BM25 RRF | D PTK | mean5 | +0.015 (+0.005 to +0.028) | 8 / 2 / 0 |
| PTK+BM25 RRF | BM25 | ST3 | +0.077 (+0.056 to +0.108) | 10 / 0 / 0 |
| PTK+BM25 RRF | BM25 | MT3 | +0.120 (+0.093 to +0.159) | 10 / 0 / 0 |
| PTK+BM25 RRF | BM25 | mean5 | +0.050 (+0.042 to +0.056) | 10 / 0 / 0 |
| PTK+CodeBERT ft wsum | D PTK | ST3 | +0.022 (+0.009 to +0.037) | 8 / 2 / 0 |
| PTK+CodeBERT ft wsum | D PTK | MT3 | +0.151 (+0.097 to +0.178) | 10 / 0 / 0 |
| PTK+CodeBERT ft wsum | D PTK | mean5 | +0.035 (+0.024 to +0.038) | 10 / 0 / 0 |
| PTK+CodeBERT ft wsum | CodeBERT ft | ST3 | +0.063 (+0.044 to +0.085) | 10 / 0 / 0 |
| PTK+CodeBERT ft wsum | CodeBERT ft | MT3 | +0.135 (+0.098 to +0.161) | 10 / 0 / 0 |
| PTK+CodeBERT ft wsum | CodeBERT ft | mean5 | +0.044 (+0.037 to +0.051) | 10 / 0 / 0 |
| PTK+CodeBERT ft RRF | D PTK | ST3 | +0.017 (+0.006 to +0.027) | 5 / 5 / 0 |
| PTK+CodeBERT ft RRF | D PTK | MT3 | +0.112 (+0.064 to +0.134) | 10 / 0 / 0 |
| PTK+CodeBERT ft RRF | D PTK | mean5 | +0.025 (+0.017 to +0.030) | 10 / 0 / 0 |
| PTK+CodeBERT ft RRF | CodeBERT ft | ST3 | +0.058 (+0.036 to +0.075) | 10 / 0 / 0 |
| PTK+CodeBERT ft RRF | CodeBERT ft | MT3 | +0.097 (+0.077 to +0.131) | 10 / 0 / 0 |
| PTK+CodeBERT ft RRF | CodeBERT ft | mean5 | +0.034 (+0.025 to +0.043) | 10 / 0 / 0 |
| STK+BM25 wsum | D STK | functional | +0.313 (+0.287 to +0.356) | 10 / 0 / 0 |
| STK+BM25 wsum | BM25 | functional | +0.000 (+0.000 to +0.000) | 0 / 10 / 0 |
| STK+BM25 RRF | D STK | functional | +0.160 (+0.150 to +0.183) | 10 / 0 / 0 |
| STK+BM25 RRF | BM25 | functional | -0.153 (-0.173 to -0.132) | 0 / 0 / 10 |
| STK+CodeBERT ft wsum | D STK | functional | +0.336 (+0.294 to +0.389) | 10 / 0 / 0 |
| STK+CodeBERT ft wsum | CodeBERT ft | functional | +0.001 (-0.004 to +0.005) | 1 / 9 / 0 |
| STK+CodeBERT ft RRF | D STK | functional | +0.194 (+0.172 to +0.214) | 10 / 0 / 0 |
| STK+CodeBERT ft RRF | CodeBERT ft | functional | -0.141 (-0.175 to -0.119) | 0 / 0 / 10 |

## Pooled over the replicates, bootstrap over functionalities

Distinct queries (functionalities): T1 901 (32), T2 650 (29), VST3 823 (30), ST3 916 (36), MT3 924 (36), functional 975 (39). Paired bootstrap resampling whole functionalities (2,000 resamples), so queries from the same functionality move together; * = 95% CI excludes 0.

| Method | T1 | T2 | VST3 | ST3 | MT3 | mean5 | functional |
|---|---|---|---|---|---|---|---|
| D STK | 1.000 | 0.999 | 0.999 | 0.967 | 0.663 | 0.926 | 0.243 |
| D SSTK | 1.000 | 0.999 | 0.999 | 0.970 | 0.669 | 0.927 | 0.242 |
| D PTK | 1.000 | 1.000 | 0.995 | 0.970 | 0.709 | 0.935 | 0.212 |
| BM25 | 1.000 | 0.968 | 0.972 | 0.895 | 0.660 | 0.899 | 0.555 |
| CodeBERT zs | 1.000 | 0.985 | 0.978 | 0.903 | 0.578 | 0.889 | 0.204 |
| CodeBERT ft | 1.000 | 0.991 | 0.988 | 0.928 | 0.725 | 0.926 | 0.578 |
| PTK+BM25 wsum | 1.000 | 1.000 | 0.999 | 0.988 | 0.827 | 0.963 | 0.329 |
| PTK+BM25 RRF | 1.000 | 1.000 | 0.998 | 0.973 | 0.777 | 0.950 | 0.390 |
| PTK+CodeBERT ft wsum | 1.000 | 1.000 | 0.997 | 0.992 | 0.860 | 0.970 | 0.520 |
| PTK+CodeBERT ft RRF | 1.000 | 0.998 | 0.995 | 0.987 | 0.821 | 0.960 | 0.412 |
| STK+BM25 wsum | 1.000 | 0.968 | 0.972 | 0.895 | 0.660 | 0.899 | 0.555 |
| STK+BM25 RRF | 1.000 | 0.997 | 1.000 | 0.960 | 0.716 | 0.934 | 0.402 |
| STK+CodeBERT ft wsum | 1.000 | 0.995 | 0.992 | 0.954 | 0.758 | 0.940 | 0.579 |
| STK+CodeBERT ft RRF | 1.000 | 0.998 | 0.996 | 0.978 | 0.771 | 0.949 | 0.437 |

| A | B | Measure | A | B | A − B | 95% CI (clustered) |
|---|---|---|---|---|---|---|
| D PTK | BM25 | T1 | 1.000 | 1.000 | +0.000 | +0.000 to +0.000 |
| D PTK | BM25 | T2 | 1.000 | 0.968 | +0.032 * | +0.007 to +0.061 |
| D PTK | BM25 | VST3 | 0.995 | 0.972 | +0.024 | -0.000 to +0.062 |
| D PTK | BM25 | ST3 | 0.970 | 0.895 | +0.074 * | +0.027 to +0.143 |
| D PTK | BM25 | MT3 | 0.709 | 0.660 | +0.049 | -0.035 to +0.158 |
| D PTK | BM25 | mean5 | 0.935 | 0.899 | +0.036 * | +0.014 to +0.062 |
| D PTK | BM25 | functional | 0.212 | 0.555 | -0.342 * | -0.445 to -0.246 |
| D PTK | CodeBERT ft | T1 | 1.000 | 1.000 | +0.000 | +0.000 to +0.000 |
| D PTK | CodeBERT ft | T2 | 1.000 | 0.991 | +0.009 * | +0.003 to +0.021 |
| D PTK | CodeBERT ft | VST3 | 0.995 | 0.988 | +0.008 | -0.006 to +0.018 |
| D PTK | CodeBERT ft | ST3 | 0.970 | 0.928 | +0.041 * | +0.003 to +0.072 |
| D PTK | CodeBERT ft | MT3 | 0.709 | 0.725 | -0.016 | -0.087 to +0.051 |
| D PTK | CodeBERT ft | mean5 | 0.935 | 0.926 | +0.008 | -0.009 to +0.023 |
| D PTK | CodeBERT ft | functional | 0.212 | 0.578 | -0.366 * | -0.464 to -0.286 |
| CodeBERT ft | BM25 | T1 | 1.000 | 1.000 | +0.000 | +0.000 to +0.000 |
| CodeBERT ft | BM25 | T2 | 0.991 | 0.968 | +0.023 | -0.006 to +0.052 |
| CodeBERT ft | BM25 | VST3 | 0.988 | 0.972 | +0.016 | -0.008 to +0.055 |
| CodeBERT ft | BM25 | ST3 | 0.928 | 0.895 | +0.033 | -0.018 to +0.108 |
| CodeBERT ft | BM25 | MT3 | 0.725 | 0.660 | +0.065 * | +0.012 to +0.142 |
| CodeBERT ft | BM25 | mean5 | 0.926 | 0.899 | +0.027 * | +0.011 to +0.050 |
| CodeBERT ft | BM25 | functional | 0.578 | 0.555 | +0.024 | -0.021 to +0.071 |
| D STK | BM25 | mean5 | 0.926 | 0.899 | +0.026 * | +0.006 to +0.053 |
| D STK | BM25 | functional | 0.243 | 0.555 | -0.312 * | -0.412 to -0.223 |
| D SSTK | BM25 | mean5 | 0.927 | 0.899 | +0.028 * | +0.008 to +0.055 |
| D SSTK | BM25 | functional | 0.242 | 0.555 | -0.313 * | -0.413 to -0.222 |
| D STK | CodeBERT ft | mean5 | 0.926 | 0.926 | -0.001 | -0.016 to +0.014 |
| D STK | CodeBERT ft | functional | 0.243 | 0.578 | -0.336 * | -0.435 to -0.259 |
| D SSTK | CodeBERT ft | mean5 | 0.927 | 0.926 | +0.001 | -0.015 to +0.016 |
| D SSTK | CodeBERT ft | functional | 0.242 | 0.578 | -0.336 * | -0.436 to -0.259 |
| CodeBERT ft | CodeBERT zs | mean5 | 0.926 | 0.889 | +0.038 * | +0.025 to +0.052 |
| CodeBERT ft | CodeBERT zs | functional | 0.578 | 0.204 | +0.374 * | +0.309 to +0.454 |
| PTK+BM25 wsum | D PTK | ST3 | 0.988 | 0.970 | +0.019 * | +0.011 to +0.029 |
| PTK+BM25 wsum | D PTK | MT3 | 0.827 | 0.709 | +0.118 * | +0.088 to +0.158 |
| PTK+BM25 wsum | D PTK | mean5 | 0.963 | 0.935 | +0.028 * | +0.022 to +0.036 |
| PTK+BM25 wsum | BM25 | ST3 | 0.988 | 0.895 | +0.093 * | +0.049 to +0.157 |
| PTK+BM25 wsum | BM25 | MT3 | 0.827 | 0.660 | +0.167 * | +0.099 to +0.267 |
| PTK+BM25 wsum | BM25 | mean5 | 0.963 | 0.899 | +0.064 * | +0.045 to +0.088 |
| PTK+BM25 RRF | D PTK | ST3 | 0.973 | 0.970 | +0.003 | -0.019 to +0.021 |
| PTK+BM25 RRF | D PTK | MT3 | 0.777 | 0.709 | +0.068 | -0.002 to +0.124 |
| PTK+BM25 RRF | D PTK | mean5 | 0.950 | 0.935 | +0.015 * | +0.000 to +0.027 |
| PTK+BM25 RRF | BM25 | ST3 | 0.973 | 0.895 | +0.078 * | +0.040 to +0.134 |
| PTK+BM25 RRF | BM25 | MT3 | 0.777 | 0.660 | +0.117 * | +0.070 to +0.173 |
| PTK+BM25 RRF | BM25 | mean5 | 0.950 | 0.899 | +0.050 * | +0.036 to +0.068 |
| PTK+CodeBERT ft wsum | D PTK | ST3 | 0.992 | 0.970 | +0.022 * | +0.014 to +0.037 |
| PTK+CodeBERT ft wsum | D PTK | MT3 | 0.860 | 0.709 | +0.151 * | +0.115 to +0.198 |
| PTK+CodeBERT ft wsum | D PTK | mean5 | 0.970 | 0.935 | +0.035 * | +0.028 to +0.045 |
| PTK+CodeBERT ft wsum | CodeBERT ft | ST3 | 0.992 | 0.928 | +0.064 * | +0.030 to +0.090 |
| PTK+CodeBERT ft wsum | CodeBERT ft | MT3 | 0.860 | 0.725 | +0.135 * | +0.074 to +0.195 |
| PTK+CodeBERT ft wsum | CodeBERT ft | mean5 | 0.970 | 0.926 | +0.043 * | +0.030 to +0.057 |
| PTK+CodeBERT ft RRF | D PTK | ST3 | 0.987 | 0.970 | +0.017 * | +0.008 to +0.033 |
| PTK+CodeBERT ft RRF | D PTK | MT3 | 0.821 | 0.709 | +0.113 * | +0.086 to +0.151 |
| PTK+CodeBERT ft RRF | D PTK | mean5 | 0.960 | 0.935 | +0.025 * | +0.020 to +0.034 |
| PTK+CodeBERT ft RRF | CodeBERT ft | ST3 | 0.987 | 0.928 | +0.058 * | +0.026 to +0.084 |
| PTK+CodeBERT ft RRF | CodeBERT ft | MT3 | 0.821 | 0.725 | +0.097 * | +0.033 to +0.159 |
| PTK+CodeBERT ft RRF | CodeBERT ft | mean5 | 0.960 | 0.926 | +0.034 * | +0.020 to +0.048 |
| STK+BM25 wsum | D STK | functional | 0.555 | 0.243 | +0.312 * | +0.223 to +0.412 |
| STK+BM25 wsum | BM25 | functional | 0.555 | 0.555 | +0.000 | +0.000 to +0.000 |
| STK+BM25 RRF | D STK | functional | 0.402 | 0.243 | +0.160 * | +0.125 to +0.198 |
| STK+BM25 RRF | BM25 | functional | 0.402 | 0.555 | -0.152 * | -0.214 to -0.096 |
| STK+CodeBERT ft wsum | D STK | functional | 0.579 | 0.243 | +0.337 * | +0.257 to +0.439 |
| STK+CodeBERT ft wsum | CodeBERT ft | functional | 0.579 | 0.578 | +0.001 | -0.005 to +0.009 |
| STK+CodeBERT ft RRF | D STK | functional | 0.437 | 0.243 | +0.194 * | +0.160 to +0.238 |
| STK+CodeBERT ft RRF | CodeBERT ft | functional | 0.437 | 0.578 | -0.141 * | -0.199 to -0.097 |
