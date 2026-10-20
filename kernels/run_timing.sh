#!/usr/bin/env bash
# Time STK / SSTK / PTK on tree variants A-D: 100 queries x N random candidates each.
# usage: kernels/run_timing.sh [nCandidates] [budgetSecondsPerRun] [threads]
set -euo pipefail
cd "$(dirname "$0")"
N=${1:-500}; BUDGET=${2:-600}; THREADS=${3:-16}
CP=target/kernels-0.1.jar:$(cat classpath.txt)
OUT=../results/timing
mkdir -p "$OUT"
for v in C D B A; do
  for spec in "STK 0.4 0" "SSTK 0.4 0" "PTK 0.4 0.4"; do
    set -- $spec
    java -Xmx3g -Dorg.slf4j.simpleLogger.defaultLogLevel=error -cp "$CP" treekernel.KernelTiming \
      ../data/trees/$v.tsv ../data/pools/queries.tsv "$1" "$2" "$3" "$N" "$THREADS" 1 "$BUDGET" \
      "$OUT/${v}_$1.tsv" | sed "s/^/[$v] /"
  done
done
