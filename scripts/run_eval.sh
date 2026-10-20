#!/usr/bin/env bash
# Evaluation runs (PLAN.md §5.1): the 584 evaluation queries (data/pools/eval_queries.tsv) against
# the reduced corpus (data/trees_main), evaluated for RQ1 (syntactic_<type>.tsv) and RQ2 (functional.tsv).
# usage: scripts/run_eval.sh [threads] VARIANT:KERNEL:LAMBDA:MU ...   (MU = 0 for STK/SSTK)
# Output: results/eval/<V>/<K>_l<λ>[_m<μ>]/ ; finished runs are skipped. Holds a sleep inhibitor.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -z "${INHIBITED:-}" ]; then
  exec env INHIBITED=1 systemd-inhibit --what=sleep:idle:handle-lid-switch --who=treekernel \
    --why="evaluation runs" "$0" "$@"
fi
THREADS=$1; shift
CP=kernels/target/classes:$(cat kernels/classpath.txt)
SYN=""
for t in T1 T2 VST3 ST3 MT3; do SYN="$SYN --syntactic data/pools/syntactic_$t.tsv:$t"; done
for s in "$@"; do
  IFS=: read -r V k l m <<< "$s"
  d=results/eval/$V/${k}_l$l
  if [ "$k" = PTK ]; then d=${d}_m$m; fi
  if [ ! -f "$d/meta.json" ]; then
    echo "== $V $k l=$l m=$m $(date +%T)"
    java -Xmx6g -Dorg.slf4j.simpleLogger.defaultLogLevel=error -cp "$CP" treekernel.RetrievalRunner \
      data/trees_main/$V.tsv data/pools/eval_queries.tsv "$k" "$l" "$m" "$THREADS" "$d" 2>&1 | grep -v "corpus methods scored"
  fi
  [ -f "$d/eval/summary.tsv" ] || .venv/bin/python eval/evaluate.py "$d" $SYN --functional data/pools/functional.tsv
done
echo "all done $(date +%T)"
