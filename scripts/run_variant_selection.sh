#!/usr/bin/env bash
# Variant selection (PLAN.md §5.1, decided 2026-10-16): every variant x kernel at KeLP's
# default setting (lambda = mu = 0.4) on the 50 tuning queries, reduced corpus (data/trees_main).
# usage: scripts/run_variant_selection.sh [threads]
set -euo pipefail
cd "$(dirname "$0")/.."
THREADS=${1:-14}
CP=kernels/target/classes:$(cat kernels/classpath.txt)
OUT=results/variant_selection
for v in C D B A; do
  for k in STK SSTK PTK; do
    d=$OUT/${v}_${k}
    if [ -f "$d/meta.json" ]; then echo "skip $d (done)"; continue; fi
    echo "== $v $k $(date +%T)"
    java -Xmx6g -Dorg.slf4j.simpleLogger.defaultLogLevel=error -cp "$CP" treekernel.RetrievalRunner \
      data/trees_main/$v.tsv data/pools/tuning.tsv $k 0.4 0.4 "$THREADS" "$d" 2>&1 | grep -v "corpus methods scored"
  done
done
echo "all done $(date +%T)"
