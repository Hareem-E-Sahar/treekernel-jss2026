# Replication over 10 query sets

Corpus with false positives (72,782 methods; exact copies of the query ignored). Seeds 55, 1375, 2084, 2802, 3389, 3501, 6251, 8241, 8828, 9080 (the user's seeds from the earlier study); each replicate = 100 queries per clone type + 100 functional queries (`exp_v2/data/replicates/`, a copy of `data/pools/replicates/`). Variant D at the tuned settings; fusion at the W tuned on the tuning queries. MAP per type, mean5 = mean of the five types, functional = MAP@R.

## Across replicates: mean ± SD (min–max)

| Method | T1 | T2 | VST3 | ST3 | MT3 | mean5 | functional |
|---|---|---|---|---|---|---|---|
| D STK | 1.000 ± 0.000 (1.000–1.000) | 0.994 ± 0.003 (0.989–1.000) | 0.989 ± 0.008 (0.968–1.000) | 0.911 ± 0.017 (0.888–0.933) | 0.512 ± 0.043 (0.445–0.556) | 0.881 ± 0.008 (0.868–0.889) | 0.137 ± 0.021 (0.111–0.171) |
| D SSTK | 1.000 ± 0.000 (1.000–1.000) | 0.994 ± 0.003 (0.989–1.000) | 0.990 ± 0.005 (0.984–1.000) | 0.918 ± 0.020 (0.893–0.951) | 0.520 ± 0.045 (0.449–0.564) | 0.885 ± 0.009 (0.872–0.895) | 0.137 ± 0.021 (0.108–0.174) |
| D PTK | 1.000 ± 0.000 (1.000–1.000) | 0.994 ± 0.003 (0.989–1.000) | 0.987 ± 0.008 (0.970–1.000) | 0.924 ± 0.019 (0.904–0.958) | 0.555 ± 0.044 (0.472–0.611) | 0.892 ± 0.009 (0.877–0.908) | 0.121 ± 0.020 (0.088–0.164) |
| BM25 | 0.998 ± 0.003 (0.991–1.000) | 0.892 ± 0.018 (0.851–0.916) | 0.924 ± 0.017 (0.901–0.949) | 0.791 ± 0.028 (0.750–0.825) | 0.446 ± 0.038 (0.400–0.506) | 0.810 ± 0.008 (0.796–0.820) | 0.305 ± 0.023 (0.273–0.338) |
| CodeBERT zs | 1.000 ± 0.001 (0.997–1.000) | 0.958 ± 0.020 (0.916–0.978) | 0.955 ± 0.017 (0.926–0.987) | 0.809 ± 0.020 (0.768–0.835) | 0.396 ± 0.043 (0.338–0.482) | 0.824 ± 0.010 (0.810–0.845) | 0.109 ± 0.015 (0.092–0.140) |
| CodeBERT ft | 1.000 ± 0.001 (0.997–1.000) | 0.931 ± 0.018 (0.910–0.962) | 0.949 ± 0.020 (0.904–0.973) | 0.780 ± 0.020 (0.750–0.816) | 0.461 ± 0.035 (0.401–0.504) | 0.824 ± 0.009 (0.815–0.842) | 0.310 ± 0.025 (0.274–0.339) |
| PTK+BM25 wsum | 1.000 ± 0.000 (1.000–1.000) | 0.996 ± 0.003 (0.990–1.000) | 0.990 ± 0.007 (0.980–0.999) | 0.943 ± 0.017 (0.922–0.969) | 0.661 ± 0.043 (0.574–0.712) | 0.918 ± 0.008 (0.906–0.928) | 0.193 ± 0.021 (0.158–0.232) |
| PTK+BM25 RRF | 0.999 ± 0.002 (0.996–1.000) | 0.987 ± 0.008 (0.967–0.993) | 0.981 ± 0.008 (0.971–0.994) | 0.911 ± 0.018 (0.885–0.942) | 0.600 ± 0.033 (0.530–0.643) | 0.896 ± 0.006 (0.887–0.903) | 0.217 ± 0.021 (0.186–0.254) |
| PTK+CodeBERT ft wsum | 1.000 ± 0.000 (1.000–1.000) | 0.996 ± 0.003 (0.991–1.000) | 0.990 ± 0.007 (0.981–1.000) | 0.944 ± 0.013 (0.929–0.967) | 0.672 ± 0.039 (0.607–0.725) | 0.920 ± 0.007 (0.910–0.930) | 0.285 ± 0.024 (0.244–0.312) |
| PTK+CodeBERT ft RRF | 1.000 ± 0.000 (1.000–1.000) | 0.979 ± 0.015 (0.949–0.998) | 0.982 ± 0.011 (0.959–1.000) | 0.909 ± 0.013 (0.890–0.926) | 0.619 ± 0.037 (0.546–0.677) | 0.898 ± 0.008 (0.887–0.913) | 0.229 ± 0.019 (0.198–0.256) |
| STK+BM25 wsum | 0.998 ± 0.003 (0.991–1.000) | 0.892 ± 0.018 (0.851–0.916) | 0.924 ± 0.017 (0.901–0.949) | 0.791 ± 0.028 (0.750–0.825) | 0.446 ± 0.038 (0.400–0.506) | 0.810 ± 0.008 (0.796–0.820) | 0.305 ± 0.023 (0.273–0.338) |
| STK+BM25 RRF | 0.999 ± 0.002 (0.996–1.000) | 0.984 ± 0.009 (0.968–0.994) | 0.975 ± 0.009 (0.957–0.987) | 0.888 ± 0.023 (0.863–0.921) | 0.537 ± 0.042 (0.469–0.598) | 0.877 ± 0.009 (0.866–0.893) | 0.229 ± 0.021 (0.200–0.263) |
| STK+CodeBERT ft wsum | 1.000 ± 0.000 (1.000–1.000) | 0.982 ± 0.011 (0.964–0.998) | 0.977 ± 0.018 (0.934–0.997) | 0.847 ± 0.017 (0.829–0.880) | 0.533 ± 0.035 (0.453–0.568) | 0.868 ± 0.008 (0.851–0.878) | 0.320 ± 0.026 (0.284–0.353) |
| STK+CodeBERT ft RRF | 1.000 ± 0.000 (1.000–1.000) | 0.981 ± 0.013 (0.956–1.000) | 0.982 ± 0.013 (0.954–0.999) | 0.898 ± 0.016 (0.876–0.926) | 0.580 ± 0.037 (0.505–0.640) | 0.888 ± 0.007 (0.880–0.898) | 0.245 ± 0.020 (0.214–0.282) |

## Comparisons per replicate

Paired query bootstrap within each replicate (2,000 resamples). Better / n.s. / worse = number of the 10 replicates in which A is significantly better than B, not significantly different, significantly worse. Mean Δ = mean of A − B over replicates.

| A | B | Measure | Mean Δ (min–max) | Better / n.s. / worse |
|---|---|---|---|---|
| D PTK | BM25 | T1 | +0.002 (+0.000 to +0.009) | 0 / 10 / 0 |
| D PTK | BM25 | T2 | +0.103 (+0.078 to +0.140) | 10 / 0 / 0 |
| D PTK | BM25 | VST3 | +0.064 (+0.047 to +0.083) | 9 / 1 / 0 |
| D PTK | BM25 | ST3 | +0.133 (+0.085 to +0.177) | 10 / 0 / 0 |
| D PTK | BM25 | MT3 | +0.109 (+0.054 to +0.210) | 6 / 4 / 0 |
| D PTK | BM25 | mean5 | +0.082 (+0.063 to +0.109) | 10 / 0 / 0 |
| D PTK | BM25 | functional | -0.184 (-0.212 to -0.151) | 0 / 0 / 10 |
| D PTK | CodeBERT ft | T1 | +0.000 (+0.000 to +0.003) | 0 / 10 / 0 |
| D PTK | CodeBERT ft | T2 | +0.063 (+0.032 to +0.088) | 10 / 0 / 0 |
| D PTK | CodeBERT ft | VST3 | +0.039 (+0.010 to +0.084) | 6 / 4 / 0 |
| D PTK | CodeBERT ft | ST3 | +0.145 (+0.102 to +0.177) | 10 / 0 / 0 |
| D PTK | CodeBERT ft | MT3 | +0.094 (+0.043 to +0.154) | 5 / 5 / 0 |
| D PTK | CodeBERT ft | mean5 | +0.068 (+0.053 to +0.087) | 10 / 0 / 0 |
| D PTK | CodeBERT ft | functional | -0.189 (-0.238 to -0.154) | 0 / 0 / 10 |
| CodeBERT ft | BM25 | T1 | +0.001 (+0.000 to +0.005) | 0 / 10 / 0 |
| CodeBERT ft | BM25 | T2 | +0.040 (+0.013 to +0.074) | 4 / 6 / 0 |
| CodeBERT ft | BM25 | VST3 | +0.025 (-0.005 to +0.070) | 2 / 8 / 0 |
| CodeBERT ft | BM25 | ST3 | -0.011 (-0.048 to +0.044) | 0 / 10 / 0 |
| CodeBERT ft | BM25 | MT3 | +0.015 (-0.067 to +0.059) | 0 / 10 / 0 |
| CodeBERT ft | BM25 | mean5 | +0.014 (-0.005 to +0.029) | 2 / 8 / 0 |
| CodeBERT ft | BM25 | functional | +0.005 (-0.017 to +0.052) | 1 / 9 / 0 |
| D STK | BM25 | mean5 | +0.071 (+0.058 to +0.094) | 10 / 0 / 0 |
| D STK | BM25 | functional | -0.168 (-0.202 to -0.131) | 0 / 0 / 10 |
| D SSTK | BM25 | mean5 | +0.074 (+0.060 to +0.097) | 10 / 0 / 0 |
| D SSTK | BM25 | functional | -0.168 (-0.201 to -0.132) | 0 / 0 / 10 |
| D STK | CodeBERT ft | mean5 | +0.057 (+0.032 to +0.070) | 10 / 0 / 0 |
| D STK | CodeBERT ft | functional | -0.173 (-0.216 to -0.134) | 0 / 0 / 10 |
| D SSTK | CodeBERT ft | mean5 | +0.061 (+0.035 to +0.074) | 10 / 0 / 0 |
| D SSTK | CodeBERT ft | functional | -0.173 (-0.215 to -0.134) | 0 / 0 / 10 |
| CodeBERT ft | CodeBERT zs | mean5 | +0.001 (-0.018 to +0.024) | 0 / 10 / 0 |
| CodeBERT ft | CodeBERT zs | functional | +0.201 (+0.167 to +0.235) | 10 / 0 / 0 |
| PTK+BM25 wsum | D PTK | ST3 | +0.018 (+0.008 to +0.042) | 3 / 7 / 0 |
| PTK+BM25 wsum | D PTK | MT3 | +0.105 (+0.065 to +0.141) | 10 / 0 / 0 |
| PTK+BM25 wsum | D PTK | mean5 | +0.026 (+0.015 to +0.035) | 10 / 0 / 0 |
| PTK+BM25 wsum | BM25 | ST3 | +0.152 (+0.106 to +0.189) | 10 / 0 / 0 |
| PTK+BM25 wsum | BM25 | MT3 | +0.215 (+0.171 to +0.284) | 10 / 0 / 0 |
| PTK+BM25 wsum | BM25 | mean5 | +0.108 (+0.090 to +0.123) | 10 / 0 / 0 |
| PTK+BM25 RRF | D PTK | ST3 | -0.014 (-0.032 to +0.017) | 0 / 9 / 1 |
| PTK+BM25 RRF | D PTK | MT3 | +0.045 (+0.002 to +0.092) | 4 / 6 / 0 |
| PTK+BM25 RRF | D PTK | mean5 | +0.003 (-0.011 to +0.016) | 1 / 9 / 0 |
| PTK+BM25 RRF | BM25 | ST3 | +0.119 (+0.091 to +0.149) | 10 / 0 / 0 |
| PTK+BM25 RRF | BM25 | MT3 | +0.154 (+0.103 to +0.224) | 10 / 0 / 0 |
| PTK+BM25 RRF | BM25 | mean5 | +0.085 (+0.075 to +0.098) | 10 / 0 / 0 |
| PTK+CodeBERT ft wsum | D PTK | ST3 | +0.019 (+0.009 to +0.037) | 1 / 9 / 0 |
| PTK+CodeBERT ft wsum | D PTK | MT3 | +0.117 (+0.081 to +0.145) | 10 / 0 / 0 |
| PTK+CodeBERT ft wsum | D PTK | mean5 | +0.028 (+0.020 to +0.036) | 10 / 0 / 0 |
| PTK+CodeBERT ft wsum | CodeBERT ft | ST3 | +0.164 (+0.139 to +0.190) | 10 / 0 / 0 |
| PTK+CodeBERT ft wsum | CodeBERT ft | MT3 | +0.211 (+0.177 to +0.237) | 10 / 0 / 0 |
| PTK+CodeBERT ft wsum | CodeBERT ft | mean5 | +0.096 (+0.085 to +0.109) | 10 / 0 / 0 |
| PTK+CodeBERT ft RRF | D PTK | ST3 | -0.015 (-0.039 to +0.022) | 0 / 9 / 1 |
| PTK+CodeBERT ft RRF | D PTK | MT3 | +0.063 (+0.021 to +0.109) | 7 / 3 / 0 |
| PTK+CodeBERT ft RRF | D PTK | mean5 | +0.005 (-0.006 to +0.019) | 2 / 8 / 0 |
| PTK+CodeBERT ft RRF | CodeBERT ft | ST3 | +0.130 (+0.108 to +0.167) | 10 / 0 / 0 |
| PTK+CodeBERT ft RRF | CodeBERT ft | MT3 | +0.158 (+0.115 to +0.180) | 10 / 0 / 0 |
| PTK+CodeBERT ft RRF | CodeBERT ft | mean5 | +0.074 (+0.059 to +0.087) | 10 / 0 / 0 |
| STK+BM25 wsum | D STK | functional | +0.168 (+0.131 to +0.202) | 10 / 0 / 0 |
| STK+BM25 wsum | BM25 | functional | +0.000 (+0.000 to +0.000) | 0 / 10 / 0 |
| STK+BM25 RRF | D STK | functional | +0.092 (+0.078 to +0.105) | 10 / 0 / 0 |
| STK+BM25 RRF | BM25 | functional | -0.076 (-0.097 to -0.053) | 0 / 0 / 10 |
| STK+CodeBERT ft wsum | D STK | functional | +0.183 (+0.146 to +0.228) | 10 / 0 / 0 |
| STK+CodeBERT ft wsum | CodeBERT ft | functional | +0.011 (+0.006 to +0.014) | 9 / 1 / 0 |
| STK+CodeBERT ft RRF | D STK | functional | +0.109 (+0.086 to +0.125) | 10 / 0 / 0 |
| STK+CodeBERT ft RRF | CodeBERT ft | functional | -0.064 (-0.090 to -0.048) | 0 / 0 / 10 |

## Pooled over the replicates, bootstrap over functionalities

Distinct queries (functionalities): T1 901 (32), T2 650 (29), VST3 823 (30), ST3 916 (36), MT3 924 (36), functional 975 (39). Paired bootstrap resampling whole functionalities (2,000 resamples), so queries from the same functionality move together; * = 95% CI excludes 0.

| Method | T1 | T2 | VST3 | ST3 | MT3 | mean5 | functional |
|---|---|---|---|---|---|---|---|
| D STK | 1.000 | 0.994 | 0.989 | 0.911 | 0.514 | 0.882 | 0.137 |
| D SSTK | 1.000 | 0.994 | 0.990 | 0.919 | 0.521 | 0.885 | 0.136 |
| D PTK | 1.000 | 0.995 | 0.987 | 0.924 | 0.554 | 0.892 | 0.121 |
| BM25 | 0.999 | 0.890 | 0.923 | 0.789 | 0.450 | 0.810 | 0.304 |
| CodeBERT zs | 1.000 | 0.960 | 0.952 | 0.809 | 0.395 | 0.823 | 0.110 |
| CodeBERT ft | 1.000 | 0.934 | 0.942 | 0.777 | 0.459 | 0.822 | 0.311 |
| PTK+BM25 wsum | 1.000 | 0.996 | 0.990 | 0.944 | 0.660 | 0.918 | 0.193 |
| PTK+BM25 RRF | 0.999 | 0.988 | 0.982 | 0.911 | 0.600 | 0.896 | 0.217 |
| PTK+CodeBERT ft wsum | 1.000 | 0.995 | 0.990 | 0.945 | 0.671 | 0.920 | 0.286 |
| PTK+CodeBERT ft RRF | 1.000 | 0.981 | 0.980 | 0.910 | 0.618 | 0.898 | 0.230 |
| STK+BM25 wsum | 0.999 | 0.890 | 0.923 | 0.789 | 0.450 | 0.810 | 0.304 |
| STK+BM25 RRF | 0.999 | 0.984 | 0.976 | 0.887 | 0.538 | 0.877 | 0.229 |
| STK+CodeBERT ft wsum | 1.000 | 0.981 | 0.974 | 0.846 | 0.533 | 0.867 | 0.321 |
| STK+CodeBERT ft RRF | 1.000 | 0.982 | 0.980 | 0.897 | 0.580 | 0.888 | 0.246 |

| A | B | Measure | A | B | A − B | 95% CI (clustered) |
|---|---|---|---|---|---|---|
| D PTK | BM25 | T1 | 1.000 | 0.999 | +0.001 | +0.000 to +0.003 |
| D PTK | BM25 | T2 | 0.995 | 0.890 | +0.105 * | +0.053 to +0.134 |
| D PTK | BM25 | VST3 | 0.987 | 0.923 | +0.064 * | +0.012 to +0.102 |
| D PTK | BM25 | ST3 | 0.924 | 0.789 | +0.135 * | +0.057 to +0.221 |
| D PTK | BM25 | MT3 | 0.554 | 0.450 | +0.104 * | +0.013 to +0.223 |
| D PTK | BM25 | mean5 | 0.892 | 0.810 | +0.082 * | +0.053 to +0.111 |
| D PTK | BM25 | functional | 0.121 | 0.304 | -0.183 * | -0.271 to -0.115 |
| D PTK | CodeBERT ft | T1 | 1.000 | 1.000 | +0.000 | +0.000 to +0.001 |
| D PTK | CodeBERT ft | T2 | 0.995 | 0.934 | +0.062 * | +0.017 to +0.131 |
| D PTK | CodeBERT ft | VST3 | 0.987 | 0.942 | +0.045 * | +0.016 to +0.086 |
| D PTK | CodeBERT ft | ST3 | 0.924 | 0.777 | +0.147 * | +0.070 to +0.224 |
| D PTK | CodeBERT ft | MT3 | 0.554 | 0.459 | +0.094 | -0.002 to +0.202 |
| D PTK | CodeBERT ft | mean5 | 0.892 | 0.822 | +0.070 * | +0.038 to +0.099 |
| D PTK | CodeBERT ft | functional | 0.121 | 0.311 | -0.189 * | -0.266 to -0.130 |
| CodeBERT ft | BM25 | T1 | 1.000 | 0.999 | +0.001 | +0.000 to +0.003 |
| CodeBERT ft | BM25 | T2 | 0.934 | 0.890 | +0.044 | -0.041 to +0.107 |
| CodeBERT ft | BM25 | VST3 | 0.942 | 0.923 | +0.019 | -0.024 to +0.059 |
| CodeBERT ft | BM25 | ST3 | 0.777 | 0.789 | -0.012 | -0.081 to +0.077 |
| CodeBERT ft | BM25 | MT3 | 0.459 | 0.450 | +0.009 | -0.053 to +0.087 |
| CodeBERT ft | BM25 | mean5 | 0.822 | 0.810 | +0.012 | -0.015 to +0.042 |
| CodeBERT ft | BM25 | functional | 0.311 | 0.304 | +0.006 | -0.029 to +0.042 |
| D STK | BM25 | mean5 | 0.882 | 0.810 | +0.072 * | +0.047 to +0.093 |
| D STK | BM25 | functional | 0.137 | 0.304 | -0.168 * | -0.242 to -0.112 |
| D SSTK | BM25 | mean5 | 0.885 | 0.810 | +0.075 * | +0.050 to +0.097 |
| D SSTK | BM25 | functional | 0.136 | 0.304 | -0.168 * | -0.244 to -0.112 |
| D STK | CodeBERT ft | mean5 | 0.882 | 0.822 | +0.059 * | +0.031 to +0.084 |
| D STK | CodeBERT ft | functional | 0.137 | 0.311 | -0.174 * | -0.241 to -0.126 |
| D SSTK | CodeBERT ft | mean5 | 0.885 | 0.822 | +0.062 * | +0.034 to +0.089 |
| D SSTK | CodeBERT ft | functional | 0.136 | 0.311 | -0.174 * | -0.242 to -0.126 |
| CodeBERT ft | CodeBERT zs | mean5 | 0.822 | 0.823 | -0.001 | -0.025 to +0.024 |
| CodeBERT ft | CodeBERT zs | functional | 0.311 | 0.110 | +0.201 * | +0.150 to +0.274 |
| PTK+BM25 wsum | D PTK | ST3 | 0.944 | 0.924 | +0.019 * | +0.004 to +0.035 |
| PTK+BM25 wsum | D PTK | MT3 | 0.660 | 0.554 | +0.106 * | +0.070 to +0.146 |
| PTK+BM25 wsum | D PTK | mean5 | 0.918 | 0.892 | +0.026 * | +0.018 to +0.034 |
| PTK+BM25 wsum | BM25 | ST3 | 0.944 | 0.789 | +0.155 * | +0.086 to +0.233 |
| PTK+BM25 wsum | BM25 | MT3 | 0.660 | 0.450 | +0.210 * | +0.141 to +0.305 |
| PTK+BM25 wsum | BM25 | mean5 | 0.918 | 0.810 | +0.108 * | +0.084 to +0.133 |
| PTK+BM25 RRF | D PTK | ST3 | 0.911 | 0.924 | -0.013 | -0.044 to +0.017 |
| PTK+BM25 RRF | D PTK | MT3 | 0.600 | 0.554 | +0.046 | -0.028 to +0.103 |
| PTK+BM25 RRF | D PTK | mean5 | 0.896 | 0.892 | +0.004 | -0.011 to +0.018 |
| PTK+BM25 RRF | BM25 | ST3 | 0.911 | 0.789 | +0.122 * | +0.067 to +0.184 |
| PTK+BM25 RRF | BM25 | MT3 | 0.600 | 0.450 | +0.150 * | +0.106 to +0.200 |
| PTK+BM25 RRF | BM25 | mean5 | 0.896 | 0.810 | +0.086 * | +0.067 to +0.103 |
| PTK+CodeBERT ft wsum | D PTK | ST3 | 0.945 | 0.924 | +0.020 * | +0.002 to +0.039 |
| PTK+CodeBERT ft wsum | D PTK | MT3 | 0.671 | 0.554 | +0.118 * | +0.074 to +0.170 |
| PTK+CodeBERT ft wsum | D PTK | mean5 | 0.920 | 0.892 | +0.028 * | +0.019 to +0.039 |
| PTK+CodeBERT ft wsum | CodeBERT ft | ST3 | 0.945 | 0.777 | +0.168 * | +0.098 to +0.238 |
| PTK+CodeBERT ft wsum | CodeBERT ft | MT3 | 0.671 | 0.459 | +0.212 * | +0.152 to +0.292 |
| PTK+CodeBERT ft wsum | CodeBERT ft | mean5 | 0.920 | 0.822 | +0.098 * | +0.072 to +0.123 |
| PTK+CodeBERT ft RRF | D PTK | ST3 | 0.910 | 0.924 | -0.014 | -0.049 to +0.023 |
| PTK+CodeBERT ft RRF | D PTK | MT3 | 0.618 | 0.554 | +0.064 * | +0.009 to +0.119 |
| PTK+CodeBERT ft RRF | D PTK | mean5 | 0.898 | 0.892 | +0.006 | -0.008 to +0.020 |
| PTK+CodeBERT ft RRF | CodeBERT ft | ST3 | 0.910 | 0.777 | +0.133 * | +0.083 to +0.182 |
| PTK+CodeBERT ft RRF | CodeBERT ft | MT3 | 0.618 | 0.459 | +0.159 * | +0.112 to +0.215 |
| PTK+CodeBERT ft RRF | CodeBERT ft | mean5 | 0.898 | 0.822 | +0.075 * | +0.057 to +0.093 |
| STK+BM25 wsum | D STK | functional | 0.304 | 0.137 | +0.168 * | +0.112 to +0.242 |
| STK+BM25 wsum | BM25 | functional | 0.304 | 0.304 | +0.000 | +0.000 to +0.000 |
| STK+BM25 RRF | D STK | functional | 0.229 | 0.137 | +0.092 * | +0.066 to +0.127 |
| STK+BM25 RRF | BM25 | functional | 0.229 | 0.304 | -0.076 * | -0.118 to -0.044 |
| STK+CodeBERT ft wsum | D STK | functional | 0.321 | 0.137 | +0.184 * | +0.135 to +0.253 |
| STK+CodeBERT ft wsum | CodeBERT ft | functional | 0.321 | 0.311 | +0.010 * | +0.003 to +0.019 |
| STK+CodeBERT ft RRF | D STK | functional | 0.246 | 0.137 | +0.109 * | +0.082 to +0.145 |
| STK+CodeBERT ft RRF | CodeBERT ft | functional | 0.246 | 0.311 | -0.065 * | -0.098 to -0.040 |
