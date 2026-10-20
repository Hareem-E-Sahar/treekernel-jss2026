#!/usr/bin/env bash
# E5 (PLAN.md §6): the 584 evaluation queries against the main corpus plus BigCloneBench's
# false positives (data/trees_e5/D.tsv, built by prep/build_e5_corpus.py). Variant D, tuned settings.
# usage: scripts/run_e5.sh [threads] KERNEL:LAMBDA:MU ...   -> results/e5/D/<K>_l<λ>[_m<μ>]/
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -z "${INHIBITED:-}" ]; then
  exec env INHIBITED=1 systemd-inhibit --what=sleep:idle:handle-lid-switch --who=treekernel \
    --why="E5 runs" "$0" "$@"
fi
THREADS=$1; shift
CP=kernels/target/classes:$(cat kernels/classpath.txt)
SYN=""
for t in T1 T2 VST3 ST3 MT3; do SYN="$SYN --syntactic data/pools/syntactic_$t.tsv:$t"; done
for s in "$@"; do
  IFS=: read -r k l m <<< "$s"
  d=results/e5/D/${k}_l$l
  if [ "$k" = PTK ]; then d=${d}_m$m; fi
  if [ ! -f "$d/meta.json" ]; then
    echo "== E5 $k l=$l m=$m $(date +%T)"
    java -Xmx8g -Dorg.slf4j.simpleLogger.defaultLogLevel=error -cp "$CP" treekernel.RetrievalRunner \
      data/trees_e5/D.tsv data/pools/eval_queries.tsv "$k" "$l" "$m" "$THREADS" "$d" 2>&1 | grep -v "corpus methods scored"
  fi
  [ -f "$d/eval/summary.tsv" ] || .venv/bin/python eval/evaluate.py "$d" $SYN --functional data/pools/functional.tsv
done
echo "all done $(date +%T)"
