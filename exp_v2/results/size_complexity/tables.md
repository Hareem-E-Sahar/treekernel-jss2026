# Size and complexity

Corpus with false positives; variant D at the tuned settings; 10 seeds. Groups: small LOC <= 6, large LOC >= 10, low McCabe <= 10, high McCabe > 10 (Checkstyle); low_large / high_large = low / high queries with LOC >= 10.

## Mean ± SD over the seeds: MAP per type, mean5, MAP@R (functional)

| Group | Method | T1 MAP | T2 MAP | VST3 MAP | ST3 MAP | MT3 MAP | mean5 MAP | functional MAP@R |
|---|---|---|---|---|---|---|---|---|
| small | STK | 1.000 ± 0.000 | 1.000 ± 0.000 (all) | 0.745 ± 0.000 (all) | 0.957 ± 0.013 | 0.673 ± 0.021 | 0.875 ± 0.006 | 0.503 ± 0.024 |
| small | SSTK | 1.000 ± 0.000 | 1.000 ± 0.000 (all) | 0.781 ± 0.000 (all) | 0.959 ± 0.014 | 0.684 ± 0.023 | 0.885 ± 0.006 | 0.505 ± 0.025 |
| small | PTK | 1.000 ± 0.000 | 1.000 ± 0.000 (all) | 0.801 ± 0.000 (all) | 0.984 ± 0.008 | 0.782 ± 0.032 | 0.913 ± 0.008 | 0.488 ± 0.030 |
| small | BM25 | 1.000 ± 0.000 | 0.707 ± 0.000 (all) | 0.353 ± 0.000 (all) | 0.790 ± 0.028 | 0.303 ± 0.028 | 0.631 ± 0.006 | 0.605 ± 0.020 |
| small | CodeBERT zs | 1.000 ± 0.000 | 0.968 ± 0.000 (all) | 0.654 ± 0.000 (all) | 0.945 ± 0.021 | 0.540 ± 0.024 | 0.821 ± 0.006 | 0.434 ± 0.031 |
| small | CodeBERT ft | 1.000 ± 0.000 | 0.817 ± 0.000 (all) | 0.448 ± 0.000 (all) | 0.953 ± 0.018 | 0.641 ± 0.037 | 0.772 ± 0.008 | 0.597 ± 0.022 |
| large | STK | 1.000 ± 0.000 | 0.997 ± 0.004 | 0.991 ± 0.004 | 0.898 ± 0.021 | 0.452 ± 0.027 | 0.868 ± 0.006 | 0.092 ± 0.013 |
| large | SSTK | 1.000 ± 0.000 | 0.997 ± 0.004 | 0.991 ± 0.005 | 0.906 ± 0.019 | 0.466 ± 0.029 | 0.872 ± 0.005 | 0.092 ± 0.014 |
| large | PTK | 1.000 ± 0.000 | 0.997 ± 0.004 | 0.990 ± 0.006 | 0.901 ± 0.026 | 0.481 ± 0.035 | 0.874 ± 0.009 | 0.082 ± 0.016 |
| large | BM25 | 0.998 ± 0.002 | 0.931 ± 0.026 | 0.954 ± 0.020 | 0.800 ± 0.031 | 0.448 ± 0.029 | 0.826 ± 0.010 | 0.274 ± 0.031 |
| large | CodeBERT zs | 1.000 ± 0.001 | 0.967 ± 0.016 | 0.973 ± 0.018 | 0.773 ± 0.023 | 0.368 ± 0.037 | 0.816 ± 0.010 | 0.072 ± 0.009 |
| large | CodeBERT ft | 1.000 ± 0.001 | 0.963 ± 0.017 | 0.963 ± 0.020 | 0.789 ± 0.024 | 0.456 ± 0.032 | 0.834 ± 0.013 | 0.290 ± 0.025 |
| low | STK | 1.000 ± 0.000 | 0.995 ± 0.004 | 0.987 ± 0.004 | 0.880 ± 0.021 | 0.504 ± 0.025 | 0.873 ± 0.009 | 0.134 ± 0.019 |
| low | SSTK | 1.000 ± 0.000 | 0.996 ± 0.003 | 0.990 ± 0.006 | 0.886 ± 0.017 | 0.514 ± 0.023 | 0.877 ± 0.007 | 0.134 ± 0.019 |
| low | PTK | 1.000 ± 0.000 | 0.997 ± 0.002 | 0.991 ± 0.005 | 0.932 ± 0.016 | 0.547 ± 0.023 | 0.893 ± 0.006 | 0.122 ± 0.020 |
| low | BM25 | 0.999 ± 0.002 | 0.882 ± 0.027 | 0.925 ± 0.014 | 0.749 ± 0.028 | 0.462 ± 0.035 | 0.803 ± 0.009 | 0.315 ± 0.025 |
| low | CodeBERT zs | 1.000 ± 0.002 | 0.962 ± 0.015 | 0.956 ± 0.012 | 0.774 ± 0.026 | 0.388 ± 0.038 | 0.816 ± 0.010 | 0.104 ± 0.016 |
| low | CodeBERT ft | 1.000 ± 0.000 | 0.957 ± 0.007 | 0.949 ± 0.020 | 0.777 ± 0.031 | 0.502 ± 0.033 | 0.837 ± 0.011 | 0.329 ± 0.027 |
| high | STK | 1.000 ± 0.000 | 1.000 ± 0.000 (all) | 0.995 ± 0.003 | 0.950 ± 0.011 | 0.730 ± 0.028 | 0.935 ± 0.005 | 0.041 ± 0.007 |
| high | SSTK | 1.000 ± 0.000 | 1.000 ± 0.000 (all) | 0.996 ± 0.004 | 0.950 ± 0.011 | 0.732 ± 0.026 | 0.935 ± 0.005 | 0.041 ± 0.007 |
| high | PTK | 1.000 ± 0.000 | 1.000 ± 0.000 (all) | 0.964 ± 0.012 | 0.690 ± 0.031 | 0.484 ± 0.031 | 0.828 ± 0.008 | 0.036 ± 0.006 |
| high | BM25 | 0.997 ± 0.003 | 1.000 ± 0.000 (all) | 0.994 ± 0.003 | 0.978 ± 0.006 | 0.836 ± 0.022 | 0.961 ± 0.005 | 0.171 ± 0.019 |
| high | CodeBERT zs | 0.999 ± 0.001 | 0.991 ± 0.000 (all) | 0.993 ± 0.005 | 0.899 ± 0.022 | 0.637 ± 0.040 | 0.904 ± 0.009 | 0.043 ± 0.008 |
| high | CodeBERT ft | 0.999 ± 0.001 | 0.991 ± 0.000 (all) | 0.993 ± 0.005 | 0.883 ± 0.019 | 0.667 ± 0.040 | 0.907 ± 0.009 | 0.181 ± 0.018 |
| low_large | STK | 1.000 ± 0.000 | 0.997 ± 0.003 | 0.989 ± 0.004 | 0.872 ± 0.022 | 0.459 ± 0.030 | 0.863 ± 0.011 | 0.107 ± 0.011 |
| low_large | SSTK | 1.000 ± 0.000 | 0.997 ± 0.003 | 0.991 ± 0.006 | 0.878 ± 0.018 | 0.469 ± 0.031 | 0.867 ± 0.010 | 0.107 ± 0.012 |
| low_large | PTK | 1.000 ± 0.000 | 0.997 ± 0.003 | 0.992 ± 0.003 | 0.924 ± 0.016 | 0.494 ± 0.027 | 0.881 ± 0.007 | 0.096 ± 0.010 |
| low_large | BM25 | 0.999 ± 0.002 | 0.927 ± 0.031 | 0.952 ± 0.019 | 0.771 ± 0.033 | 0.473 ± 0.035 | 0.824 ± 0.009 | 0.292 ± 0.031 |
| low_large | CodeBERT zs | 0.999 ± 0.002 | 0.960 ± 0.019 | 0.965 ± 0.009 | 0.746 ± 0.026 | 0.348 ± 0.054 | 0.804 ± 0.011 | 0.084 ± 0.013 |
| low_large | CodeBERT ft | 1.000 ± 0.000 | 0.968 ± 0.008 | 0.952 ± 0.019 | 0.754 ± 0.030 | 0.465 ± 0.050 | 0.828 ± 0.011 | 0.306 ± 0.031 |
| high_large | STK | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.995 ± 0.003 | 0.950 ± 0.011 | 0.730 ± 0.028 | 0.935 ± 0.005 | 0.041 ± 0.007 |
| high_large | SSTK | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.996 ± 0.004 | 0.950 ± 0.011 | 0.732 ± 0.026 | 0.935 ± 0.005 | 0.041 ± 0.007 |
| high_large | PTK | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.964 ± 0.012 | 0.690 ± 0.031 | 0.484 ± 0.031 | 0.828 ± 0.008 | 0.036 ± 0.006 |
| high_large | BM25 | 0.997 ± 0.003 | 1.000 ± 0.000 | 0.994 ± 0.003 | 0.978 ± 0.006 | 0.836 ± 0.022 | 0.961 ± 0.005 | 0.171 ± 0.019 |
| high_large | CodeBERT zs | 0.999 ± 0.001 | 0.991 ± 0.000 | 0.993 ± 0.005 | 0.899 ± 0.022 | 0.637 ± 0.040 | 0.904 ± 0.009 | 0.043 ± 0.008 |
| high_large | CodeBERT ft | 0.999 ± 0.001 | 0.991 ± 0.000 | 0.993 ± 0.005 | 0.883 ± 0.019 | 0.667 ± 0.040 | 0.907 ± 0.009 | 0.181 ± 0.018 |

## Mean ± SD over the seeds: Mean over the five types (RQ1) and functional (RQ2): nP@5, nP@10, MRR

| Group | Method | mean5 nP@5 | mean5 nP@10 | mean5 MRR | functional nP@5 | functional nP@10 | functional MRR |
|---|---|---|---|---|---|---|---|
| small | STK | 0.903 ± 0.007 | 0.930 ± 0.006 | 0.917 ± 0.004 | 0.871 ± 0.021 | 0.849 ± 0.019 | 0.943 ± 0.020 |
| small | SSTK | 0.916 ± 0.006 | 0.930 ± 0.007 | 0.925 ± 0.004 | 0.873 ± 0.019 | 0.847 ± 0.018 | 0.941 ± 0.020 |
| small | PTK | 0.942 ± 0.007 | 0.948 ± 0.008 | 0.937 ± 0.005 | 0.838 ± 0.023 | 0.814 ± 0.021 | 0.927 ± 0.031 |
| small | BM25 | 0.655 ± 0.009 | 0.673 ± 0.007 | 0.677 ± 0.010 | 0.889 ± 0.017 | 0.864 ± 0.012 | 0.960 ± 0.014 |
| small | CodeBERT zs | 0.862 ± 0.006 | 0.878 ± 0.007 | 0.884 ± 0.005 | 0.818 ± 0.025 | 0.780 ± 0.025 | 0.915 ± 0.017 |
| small | CodeBERT ft | 0.813 ± 0.008 | 0.810 ± 0.008 | 0.812 ± 0.008 | 0.881 ± 0.018 | 0.856 ± 0.017 | 0.942 ± 0.012 |
| large | STK | 0.904 ± 0.004 | 0.902 ± 0.004 | 0.923 ± 0.009 | 0.601 ± 0.040 | 0.541 ± 0.039 | 0.769 ± 0.038 |
| large | SSTK | 0.906 ± 0.005 | 0.905 ± 0.003 | 0.926 ± 0.010 | 0.603 ± 0.035 | 0.540 ± 0.035 | 0.776 ± 0.033 |
| large | PTK | 0.904 ± 0.009 | 0.903 ± 0.009 | 0.929 ± 0.012 | 0.565 ± 0.043 | 0.506 ± 0.041 | 0.744 ± 0.035 |
| large | BM25 | 0.860 ± 0.010 | 0.866 ± 0.009 | 0.879 ± 0.013 | 0.708 ± 0.036 | 0.671 ± 0.034 | 0.840 ± 0.035 |
| large | CodeBERT zs | 0.854 ± 0.012 | 0.861 ± 0.012 | 0.882 ± 0.013 | 0.581 ± 0.027 | 0.524 ± 0.026 | 0.756 ± 0.030 |
| large | CodeBERT ft | 0.871 ± 0.011 | 0.873 ± 0.013 | 0.890 ± 0.015 | 0.728 ± 0.033 | 0.694 ± 0.035 | 0.846 ± 0.034 |
| low | STK | 0.908 ± 0.007 | 0.908 ± 0.008 | 0.933 ± 0.007 | 0.664 ± 0.027 | 0.618 ± 0.031 | 0.821 ± 0.027 |
| low | SSTK | 0.913 ± 0.007 | 0.910 ± 0.008 | 0.935 ± 0.007 | 0.661 ± 0.031 | 0.619 ± 0.032 | 0.821 ± 0.027 |
| low | PTK | 0.921 ± 0.007 | 0.920 ± 0.006 | 0.942 ± 0.006 | 0.637 ± 0.037 | 0.588 ± 0.036 | 0.798 ± 0.032 |
| low | BM25 | 0.838 ± 0.009 | 0.842 ± 0.008 | 0.866 ± 0.008 | 0.755 ± 0.039 | 0.719 ± 0.039 | 0.867 ± 0.028 |
| low | CodeBERT zs | 0.855 ± 0.011 | 0.859 ± 0.010 | 0.887 ± 0.011 | 0.648 ± 0.035 | 0.597 ± 0.035 | 0.806 ± 0.029 |
| low | CodeBERT ft | 0.873 ± 0.010 | 0.875 ± 0.010 | 0.893 ± 0.009 | 0.766 ± 0.041 | 0.743 ± 0.041 | 0.874 ± 0.022 |
| high | STK | 0.959 ± 0.006 | 0.956 ± 0.006 | 0.958 ± 0.006 | 0.452 ± 0.042 | 0.393 ± 0.031 | 0.693 ± 0.046 |
| high | SSTK | 0.958 ± 0.006 | 0.956 ± 0.006 | 0.958 ± 0.006 | 0.449 ± 0.040 | 0.393 ± 0.031 | 0.683 ± 0.046 |
| high | PTK | 0.855 ± 0.009 | 0.854 ± 0.010 | 0.872 ± 0.006 | 0.383 ± 0.035 | 0.332 ± 0.026 | 0.601 ± 0.058 |
| high | BM25 | 0.973 ± 0.005 | 0.976 ± 0.005 | 0.967 ± 0.005 | 0.631 ± 0.039 | 0.562 ± 0.041 | 0.807 ± 0.034 |
| high | CodeBERT zs | 0.925 ± 0.009 | 0.930 ± 0.010 | 0.920 ± 0.009 | 0.457 ± 0.057 | 0.405 ± 0.050 | 0.685 ± 0.066 |
| high | CodeBERT ft | 0.933 ± 0.009 | 0.935 ± 0.009 | 0.928 ± 0.011 | 0.576 ± 0.053 | 0.539 ± 0.050 | 0.756 ± 0.060 |
| low_large | STK | 0.900 ± 0.008 | 0.899 ± 0.010 | 0.923 ± 0.010 | 0.635 ± 0.035 | 0.587 ± 0.038 | 0.802 ± 0.036 |
| low_large | SSTK | 0.902 ± 0.009 | 0.901 ± 0.010 | 0.925 ± 0.010 | 0.631 ± 0.038 | 0.588 ± 0.041 | 0.799 ± 0.034 |
| low_large | PTK | 0.912 ± 0.009 | 0.910 ± 0.008 | 0.935 ± 0.007 | 0.602 ± 0.048 | 0.552 ± 0.049 | 0.773 ± 0.042 |
| low_large | BM25 | 0.854 ± 0.008 | 0.861 ± 0.008 | 0.877 ± 0.009 | 0.735 ± 0.045 | 0.698 ± 0.044 | 0.853 ± 0.036 |
| low_large | CodeBERT zs | 0.840 ± 0.012 | 0.844 ± 0.011 | 0.874 ± 0.011 | 0.620 ± 0.040 | 0.567 ± 0.039 | 0.787 ± 0.032 |
| low_large | CodeBERT ft | 0.864 ± 0.012 | 0.866 ± 0.011 | 0.885 ± 0.009 | 0.748 ± 0.047 | 0.724 ± 0.048 | 0.864 ± 0.022 |
| high_large | STK | 0.959 ± 0.006 | 0.956 ± 0.006 | 0.958 ± 0.006 | 0.452 ± 0.042 | 0.393 ± 0.031 | 0.693 ± 0.046 |
| high_large | SSTK | 0.958 ± 0.006 | 0.956 ± 0.006 | 0.958 ± 0.006 | 0.449 ± 0.040 | 0.393 ± 0.031 | 0.683 ± 0.046 |
| high_large | PTK | 0.855 ± 0.009 | 0.854 ± 0.010 | 0.872 ± 0.006 | 0.383 ± 0.035 | 0.332 ± 0.026 | 0.601 ± 0.058 |
| high_large | BM25 | 0.973 ± 0.005 | 0.976 ± 0.005 | 0.967 ± 0.005 | 0.631 ± 0.039 | 0.562 ± 0.041 | 0.807 ± 0.034 |
| high_large | CodeBERT zs | 0.925 ± 0.009 | 0.930 ± 0.010 | 0.920 ± 0.009 | 0.457 ± 0.057 | 0.405 ± 0.050 | 0.685 ± 0.066 |
| high_large | CodeBERT ft | 0.933 ± 0.009 | 0.935 ± 0.009 | 0.928 ± 0.011 | 0.576 ± 0.053 | 0.539 ± 0.050 | 0.756 ± 0.060 |

## Distinct queries per group (functionalities)

| Group | T1 | T2 | VST3 | ST3 | MT3 | mean5 | functional |
|---|---|---|---|---|---|---|---|
| small | 419 (16) | 53 (8) | 12 (3) | 442 (13) | 499 (18) | 1425 (22) | 593 (28) |
| large | 856 (31) | 570 (28) | 784 (30) | 890 (33) | 925 (34) | 4025 (38) | 957 (37) |
| low | 871 (32) | 630 (29) | 780 (31) | 897 (36) | 957 (36) | 4135 (40) | 965 (41) |
| high | 450 (20) | 57 (11) | 280 (18) | 331 (23) | 304 (20) | 1422 (26) | 802 (31) |
| low_large | 650 (31) | 459 (27) | 709 (31) | 671 (32) | 763 (36) | 3252 (38) | 830 (38) |
| high_large | 450 (20) | 57 (11) | 280 (18) | 331 (23) | 304 (20) | 1422 (26) | 802 (31) |

## Interaction: does A's advantage over B change between the groups?

D = (A − B on group 1) − (A − B on group 2), pooled distinct queries; * = 95% CI excludes 0 (bootstrap over functionalities, jointly for both groups). MAP for the types and mean5, MAP@R for functional.

| Group 1 vs 2 | A | B | Measure | A − B (1) | A − B (2) | D | 95% CI |
|---|---|---|---|---|---|---|---|
| small vs large | PTK | BM25 | T1 | +0.000 | +0.002 | -0.002 | -0.004 to +0.000 |
| small vs large | PTK | BM25 | T2 | +0.293 | +0.072 | +0.221 | -0.049 to +0.429 |
| small vs large | PTK | BM25 | VST3 | +0.447 | +0.035 | +0.413 | -0.028 to +0.900 |
| small vs large | PTK | BM25 | ST3 | +0.191 | +0.099 | +0.092 | -0.049 to +0.307 |
| small vs large | PTK | BM25 | MT3 | +0.483 | +0.033 | +0.450 * | +0.145 to +0.703 |
| small vs large | PTK | BM25 | mean5 | +0.283 | +0.048 | +0.235 * | +0.087 to +0.388 |
| small vs large | PTK | BM25 | functional | -0.125 | -0.190 | +0.065 | -0.123 to +0.204 |
| small vs large | PTK | CodeBERT ft | T1 | +0.000 | +0.000 | -0.000 | -0.001 to +0.000 |
| small vs large | PTK | CodeBERT ft | T2 | +0.183 | +0.032 | +0.151 | -0.021 to +0.454 |
| small vs large | PTK | CodeBERT ft | VST3 | +0.353 | +0.029 | +0.324 | -0.016 to +0.521 |
| small vs large | PTK | CodeBERT ft | ST3 | +0.030 | +0.112 | -0.082 | -0.139 to +0.025 |
| small vs large | PTK | CodeBERT ft | MT3 | +0.150 | +0.028 | +0.122 * | +0.001 to +0.239 |
| small vs large | PTK | CodeBERT ft | mean5 | +0.143 | +0.040 | +0.103 | -0.008 to +0.201 |
| small vs large | PTK | CodeBERT ft | functional | -0.115 | -0.205 | +0.090 | -0.028 to +0.187 |
| small vs large | STK | BM25 | T1 | +0.000 | +0.002 | -0.002 | -0.004 to +0.000 |
| small vs large | STK | BM25 | T2 | +0.293 | +0.072 | +0.221 | -0.049 to +0.429 |
| small vs large | STK | BM25 | VST3 | +0.391 | +0.037 | +0.354 | -0.032 to +0.895 |
| small vs large | STK | BM25 | ST3 | +0.169 | +0.098 | +0.070 | -0.066 to +0.232 |
| small vs large | STK | BM25 | MT3 | +0.371 | +0.004 | +0.367 * | +0.111 to +0.570 |
| small vs large | STK | BM25 | mean5 | +0.245 | +0.043 | +0.202 * | +0.052 to +0.361 |
| small vs large | STK | BM25 | functional | -0.110 | -0.180 | +0.069 | -0.059 to +0.176 |
| small vs large | STK | CodeBERT ft | T1 | +0.000 | +0.000 | -0.000 | -0.001 to +0.000 |
| small vs large | STK | CodeBERT ft | T2 | +0.183 | +0.032 | +0.151 | -0.021 to +0.454 |
| small vs large | STK | CodeBERT ft | VST3 | +0.297 | +0.031 | +0.265 | -0.019 to +0.517 |
| small vs large | STK | CodeBERT ft | ST3 | +0.008 | +0.112 | -0.104 * | -0.170 to -0.016 |
| small vs large | STK | CodeBERT ft | MT3 | +0.039 | -0.000 | +0.040 | -0.084 to +0.181 |
| small vs large | STK | CodeBERT ft | mean5 | +0.105 | +0.035 | +0.070 | -0.042 to +0.180 |
| small vs large | STK | CodeBERT ft | functional | -0.101 | -0.195 | +0.094 * | +0.021 to +0.171 |
| small vs large | SSTK | BM25 | T1 | +0.000 | +0.002 | -0.002 | -0.004 to +0.000 |
| small vs large | SSTK | BM25 | T2 | +0.293 | +0.072 | +0.221 | -0.049 to +0.429 |
| small vs large | SSTK | BM25 | VST3 | +0.427 | +0.038 | +0.390 | -0.033 to +0.895 |
| small vs large | SSTK | BM25 | ST3 | +0.171 | +0.105 | +0.066 | -0.069 to +0.229 |
| small vs large | SSTK | BM25 | MT3 | +0.384 | +0.019 | +0.365 * | +0.096 to +0.583 |
| small vs large | SSTK | BM25 | mean5 | +0.255 | +0.047 | +0.208 * | +0.056 to +0.361 |
| small vs large | SSTK | BM25 | functional | -0.108 | -0.180 | +0.071 | -0.065 to +0.182 |
| small vs large | SSTK | CodeBERT ft | T1 | +0.000 | +0.000 | -0.000 | -0.001 to +0.000 |
| small vs large | SSTK | CodeBERT ft | T2 | +0.183 | +0.032 | +0.151 | -0.021 to +0.454 |
| small vs large | SSTK | CodeBERT ft | VST3 | +0.333 | +0.032 | +0.301 | -0.019 to +0.517 |
| small vs large | SSTK | CodeBERT ft | ST3 | +0.010 | +0.119 | -0.108 * | -0.168 to -0.022 |
| small vs large | SSTK | CodeBERT ft | MT3 | +0.051 | +0.014 | +0.038 | -0.088 to +0.166 |
| small vs large | SSTK | CodeBERT ft | mean5 | +0.115 | +0.039 | +0.076 | -0.041 to +0.181 |
| small vs large | SSTK | CodeBERT ft | functional | -0.099 | -0.195 | +0.096 * | +0.019 to +0.176 |
| small vs large | CodeBERT ft | BM25 | T1 | +0.000 | +0.002 | -0.002 | -0.004 to +0.000 |
| small vs large | CodeBERT ft | BM25 | T2 | +0.110 | +0.040 | +0.069 | -0.173 to +0.177 |
| small vs large | CodeBERT ft | BM25 | VST3 | +0.094 | +0.006 | +0.089 | -0.026 to +0.389 |
| small vs large | CodeBERT ft | BM25 | ST3 | +0.161 | -0.013 | +0.174 * | +0.034 to +0.323 |
| small vs large | CodeBERT ft | BM25 | MT3 | +0.332 | +0.005 | +0.328 * | +0.027 to +0.587 |
| small vs large | CodeBERT ft | BM25 | mean5 | +0.140 | +0.008 | +0.132 * | +0.026 to +0.226 |
| small vs large | CodeBERT ft | BM25 | functional | -0.010 | +0.015 | -0.025 | -0.126 to +0.035 |
| low vs high | PTK | BM25 | T1 | +0.001 | +0.005 | -0.004 | -0.012 to +0.002 |
| low vs high | PTK | BM25 | T2 | +0.116 | +0.000 | +0.116 * | +0.061 to +0.158 |
| low vs high | PTK | BM25 | VST3 | +0.068 | -0.026 | +0.094 * | +0.046 to +0.147 |
| low vs high | PTK | BM25 | ST3 | +0.185 | -0.297 | +0.482 * | +0.333 to +0.614 |
| low vs high | PTK | BM25 | MT3 | +0.087 | -0.340 | +0.427 * | +0.322 to +0.533 |
| low vs high | PTK | BM25 | mean5 | +0.091 | -0.132 | +0.223 * | +0.174 to +0.264 |
| low vs high | PTK | BM25 | functional | -0.193 | -0.138 | -0.055 | -0.115 to +0.014 |
| low vs high | PTK | CodeBERT ft | T1 | +0.000 | +0.001 | -0.001 | -0.004 to +0.000 |
| low vs high | PTK | CodeBERT ft | T2 | +0.039 | +0.009 | +0.030 | -0.003 to +0.066 |
| low vs high | PTK | CodeBERT ft | VST3 | +0.045 | -0.026 | +0.071 * | +0.032 to +0.121 |
| low vs high | PTK | CodeBERT ft | ST3 | +0.153 | -0.205 | +0.358 * | +0.188 to +0.528 |
| low vs high | PTK | CodeBERT ft | MT3 | +0.047 | -0.186 | +0.233 * | +0.123 to +0.333 |
| low vs high | PTK | CodeBERT ft | mean5 | +0.057 | -0.081 | +0.138 * | +0.086 to +0.193 |
| low vs high | PTK | CodeBERT ft | functional | -0.207 | -0.144 | -0.063 * | -0.124 to -0.008 |
| low vs high | STK | BM25 | T1 | +0.001 | +0.005 | -0.004 | -0.012 to +0.002 |
| low vs high | STK | BM25 | T2 | +0.114 | +0.000 | +0.114 * | +0.061 to +0.157 |
| low vs high | STK | BM25 | VST3 | +0.065 | +0.001 | +0.063 * | +0.015 to +0.114 |
| low vs high | STK | BM25 | ST3 | +0.134 | -0.027 | +0.161 * | +0.093 to +0.218 |
| low vs high | STK | BM25 | MT3 | +0.044 | -0.108 | +0.151 * | +0.042 to +0.234 |
| low vs high | STK | BM25 | mean5 | +0.071 | -0.026 | +0.097 * | +0.051 to +0.131 |
| low vs high | STK | BM25 | functional | -0.181 | -0.133 | -0.048 | -0.103 to +0.014 |
| low vs high | STK | CodeBERT ft | T1 | +0.000 | +0.001 | -0.001 | -0.004 to +0.000 |
| low vs high | STK | CodeBERT ft | T2 | +0.038 | +0.009 | +0.029 | -0.005 to +0.066 |
| low vs high | STK | CodeBERT ft | VST3 | +0.041 | +0.002 | +0.040 * | +0.012 to +0.083 |
| low vs high | STK | CodeBERT ft | ST3 | +0.101 | +0.065 | +0.036 | -0.042 to +0.123 |
| low vs high | STK | CodeBERT ft | MT3 | +0.003 | +0.047 | -0.043 | -0.186 to +0.060 |
| low vs high | STK | CodeBERT ft | mean5 | +0.037 | +0.025 | +0.012 | -0.029 to +0.052 |
| low vs high | STK | CodeBERT ft | functional | -0.195 | -0.139 | -0.056 * | -0.112 to -0.007 |
| low vs high | SSTK | BM25 | T1 | +0.001 | +0.005 | -0.004 | -0.012 to +0.002 |
| low vs high | SSTK | BM25 | T2 | +0.115 | +0.000 | +0.115 * | +0.061 to +0.158 |
| low vs high | SSTK | BM25 | VST3 | +0.066 | +0.002 | +0.064 * | +0.015 to +0.116 |
| low vs high | SSTK | BM25 | ST3 | +0.140 | -0.027 | +0.167 * | +0.092 to +0.229 |
| low vs high | SSTK | BM25 | MT3 | +0.053 | -0.107 | +0.160 * | +0.054 to +0.246 |
| low vs high | SSTK | BM25 | mean5 | +0.075 | -0.025 | +0.101 * | +0.054 to +0.135 |
| low vs high | SSTK | BM25 | functional | -0.181 | -0.133 | -0.048 | -0.103 to +0.014 |
| low vs high | SSTK | CodeBERT ft | T1 | +0.000 | +0.001 | -0.001 | -0.004 to +0.000 |
| low vs high | SSTK | CodeBERT ft | T2 | +0.038 | +0.009 | +0.029 | -0.004 to +0.066 |
| low vs high | SSTK | CodeBERT ft | VST3 | +0.043 | +0.002 | +0.041 * | +0.012 to +0.086 |
| low vs high | SSTK | CodeBERT ft | ST3 | +0.107 | +0.065 | +0.043 | -0.046 to +0.135 |
| low vs high | SSTK | CodeBERT ft | MT3 | +0.013 | +0.047 | -0.034 | -0.166 to +0.066 |
| low vs high | SSTK | CodeBERT ft | mean5 | +0.040 | +0.025 | +0.015 | -0.024 to +0.057 |
| low vs high | SSTK | CodeBERT ft | functional | -0.195 | -0.139 | -0.056 * | -0.112 to -0.006 |
| low vs high | CodeBERT ft | BM25 | T1 | +0.001 | +0.003 | -0.002 | -0.011 to +0.002 |
| low vs high | CodeBERT ft | BM25 | T2 | +0.077 | -0.009 | +0.085 * | +0.014 to +0.143 |
| low vs high | CodeBERT ft | BM25 | VST3 | +0.023 | -0.000 | +0.024 | -0.025 to +0.068 |
| low vs high | CodeBERT ft | BM25 | ST3 | +0.033 | -0.092 | +0.125 * | +0.020 to +0.221 |
| low vs high | CodeBERT ft | BM25 | MT3 | +0.040 | -0.154 | +0.195 * | +0.060 to +0.344 |
| low vs high | CodeBERT ft | BM25 | mean5 | +0.035 | -0.050 | +0.085 * | +0.021 to +0.142 |
| low vs high | CodeBERT ft | BM25 | functional | +0.014 | +0.006 | +0.008 | -0.025 to +0.051 |
| low_large vs high_large | PTK | BM25 | T1 | +0.001 | +0.005 | -0.003 | -0.012 to +0.003 |
| low_large vs high_large | PTK | BM25 | T2 | +0.071 | +0.000 | +0.071 * | +0.025 to +0.135 |
| low_large vs high_large | PTK | BM25 | VST3 | +0.045 | -0.026 | +0.071 * | +0.037 to +0.108 |
| low_large vs high_large | PTK | BM25 | ST3 | +0.158 | -0.297 | +0.454 * | +0.302 to +0.583 |
| low_large vs high_large | PTK | BM25 | MT3 | +0.024 | -0.340 | +0.364 * | +0.265 to +0.444 |
| low_large vs high_large | PTK | BM25 | mean5 | +0.060 | -0.132 | +0.191 * | +0.148 to +0.226 |
| low_large vs high_large | PTK | BM25 | functional | -0.197 | -0.138 | -0.059 | -0.123 to +0.010 |
| low_large vs high_large | PTK | CodeBERT ft | T1 | +0.000 | +0.001 | -0.001 | -0.004 to +0.000 |
| low_large vs high_large | PTK | CodeBERT ft | T2 | +0.027 | +0.009 | +0.018 | -0.009 to +0.046 |
| low_large vs high_large | PTK | CodeBERT ft | VST3 | +0.044 | -0.026 | +0.070 * | +0.030 to +0.124 |
| low_large vs high_large | PTK | CodeBERT ft | ST3 | +0.170 | -0.205 | +0.375 * | +0.199 to +0.548 |
| low_large vs high_large | PTK | CodeBERT ft | MT3 | +0.030 | -0.186 | +0.216 * | +0.100 to +0.320 |
| low_large vs high_large | PTK | CodeBERT ft | mean5 | +0.054 | -0.081 | +0.136 * | +0.084 to +0.188 |
| low_large vs high_large | PTK | CodeBERT ft | functional | -0.210 | -0.144 | -0.067 * | -0.132 to -0.010 |
| low_large vs high_large | STK | BM25 | T1 | +0.001 | +0.005 | -0.003 | -0.012 to +0.003 |
| low_large vs high_large | STK | BM25 | T2 | +0.071 | +0.000 | +0.071 * | +0.025 to +0.135 |
| low_large vs high_large | STK | BM25 | VST3 | +0.042 | +0.001 | +0.041 * | +0.011 to +0.074 |
| low_large vs high_large | STK | BM25 | ST3 | +0.106 | -0.027 | +0.133 * | +0.065 to +0.188 |
| low_large vs high_large | STK | BM25 | MT3 | -0.010 | -0.108 | +0.097 | -0.015 to +0.174 |
| low_large vs high_large | STK | BM25 | mean5 | +0.042 | -0.026 | +0.068 * | +0.027 to +0.097 |
| low_large vs high_large | STK | BM25 | functional | -0.185 | -0.133 | -0.052 | -0.110 to +0.008 |
| low_large vs high_large | STK | CodeBERT ft | T1 | +0.000 | +0.001 | -0.001 | -0.004 to +0.000 |
| low_large vs high_large | STK | CodeBERT ft | T2 | +0.027 | +0.009 | +0.018 | -0.009 to +0.046 |
| low_large vs high_large | STK | CodeBERT ft | VST3 | +0.041 | +0.002 | +0.040 * | +0.011 to +0.085 |
| low_large vs high_large | STK | CodeBERT ft | ST3 | +0.118 | +0.065 | +0.053 | -0.029 to +0.139 |
| low_large vs high_large | STK | CodeBERT ft | MT3 | -0.004 | +0.047 | -0.051 | -0.190 to +0.055 |
| low_large vs high_large | STK | CodeBERT ft | mean5 | +0.036 | +0.025 | +0.012 | -0.027 to +0.048 |
| low_large vs high_large | STK | CodeBERT ft | functional | -0.198 | -0.139 | -0.059 * | -0.118 to -0.010 |
| low_large vs high_large | SSTK | BM25 | T1 | +0.001 | +0.005 | -0.003 | -0.012 to +0.003 |
| low_large vs high_large | SSTK | BM25 | T2 | +0.071 | +0.000 | +0.071 * | +0.025 to +0.135 |
| low_large vs high_large | SSTK | BM25 | VST3 | +0.043 | +0.002 | +0.041 * | +0.012 to +0.075 |
| low_large vs high_large | SSTK | BM25 | ST3 | +0.112 | -0.027 | +0.139 * | +0.061 to +0.201 |
| low_large vs high_large | SSTK | BM25 | MT3 | -0.001 | -0.107 | +0.106 | -0.001 to +0.182 |
| low_large vs high_large | SSTK | BM25 | mean5 | +0.045 | -0.025 | +0.071 * | +0.030 to +0.101 |
| low_large vs high_large | SSTK | BM25 | functional | -0.185 | -0.133 | -0.053 | -0.111 to +0.007 |
| low_large vs high_large | SSTK | CodeBERT ft | T1 | +0.000 | +0.001 | -0.001 | -0.004 to +0.000 |
| low_large vs high_large | SSTK | CodeBERT ft | T2 | +0.027 | +0.009 | +0.018 | -0.009 to +0.046 |
| low_large vs high_large | SSTK | CodeBERT ft | VST3 | +0.042 | +0.002 | +0.040 * | +0.010 to +0.088 |
| low_large vs high_large | SSTK | CodeBERT ft | ST3 | +0.125 | +0.065 | +0.060 | -0.033 to +0.154 |
| low_large vs high_large | SSTK | CodeBERT ft | MT3 | +0.005 | +0.047 | -0.042 | -0.170 to +0.065 |
| low_large vs high_large | SSTK | CodeBERT ft | mean5 | +0.040 | +0.025 | +0.015 | -0.024 to +0.053 |
| low_large vs high_large | SSTK | CodeBERT ft | functional | -0.199 | -0.139 | -0.060 * | -0.119 to -0.011 |
| low_large vs high_large | CodeBERT ft | BM25 | T1 | +0.001 | +0.003 | -0.002 | -0.011 to +0.004 |
| low_large vs high_large | CodeBERT ft | BM25 | T2 | +0.044 | -0.009 | +0.052 | -0.006 to +0.113 |
| low_large vs high_large | CodeBERT ft | BM25 | VST3 | +0.001 | -0.000 | +0.001 | -0.036 to +0.030 |
| low_large vs high_large | CodeBERT ft | BM25 | ST3 | -0.012 | -0.092 | +0.079 | -0.024 to +0.175 |
| low_large vs high_large | CodeBERT ft | BM25 | MT3 | -0.006 | -0.154 | +0.148 * | +0.013 to +0.284 |
| low_large vs high_large | CodeBERT ft | BM25 | mean5 | +0.005 | -0.050 | +0.056 * | +0.001 to +0.106 |
| low_large vs high_large | CodeBERT ft | BM25 | functional | +0.013 | +0.006 | +0.008 | -0.024 to +0.049 |
