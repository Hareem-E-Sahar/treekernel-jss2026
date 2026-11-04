#!/usr/bin/env bash
# exp_v2 PTK terminal-factor analysis (revision_plan.md, R1-C1b): PTK at the tuned lambda 0.4, mu 0.6 with terminal
# factor 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 4 on the 50 tuning queries against the corpus with false positives, evaluated as the
# lambda/mu grid (exp_v2/eval/tune.py). Factor 1 is checked byte-identical to the tuning run
# exp_v2/tuning/grid/PTK_l0.4_m0.6. A factor at which KeLP's float overflows stops the runner; it is marked not
# computable with the runner's message.
# usage: exp_v2/scripts/run_terminal_factor.sh [threads]   -> exp_v2/tuning/terminal_factor/; finished runs are skipped.
set -euo pipefail
cd "$(dirname "$0")/../.."
if [ -z "${INHIBITED:-}" ]; then
  exec env INHIBITED=1 systemd-inhibit --what=sleep:idle:handle-lid-switch --who=treekernel \
    --why="exp_v2 PTK terminal factor" "$0" "$@"
fi
THREADS=${1:-14}
CP=kernels/target/classes:$(cat kernels/classpath.txt)
[ -f exp_v2/kernels/classes/treekernel/RetrievalRunnerTF.class ] || javac -cp "$CP" -d exp_v2/kernels/classes \
  exp_v2/kernels/src/treekernel/RetrievalRunnerTF.java
CP=exp_v2/kernels/classes:$CP
TREES=data/trees_e5/D.tsv
TQ=exp_v2/data/tuning.tsv
O=exp_v2/tuning/terminal_factor
mkdir -p $O

for t in 1 0.25 0.5 0.75 1.25 1.5 1.75 2 4; do
  d=$O/PTK_l0.4_m0.6_t$t
  [ -f $d/meta.json ] || [ -f $d/NOT_COMPUTABLE ] && continue
  echo "== PTK lambda 0.4 mu 0.6 terminal factor $t $(date +%T)"
  mkdir -p $d
  if java -Xmx8g -Dorg.slf4j.simpleLogger.defaultLogLevel=error -cp "$CP" treekernel.RetrievalRunnerTF \
       $TREES $TQ 0.4 0.6 $t "$THREADS" $d > $d/runner.log 2>&1; then
    rm -f $d/runner.log
  else
    grep -q "not finite" $d/runner.log || { echo "runner failed (not an overflow): $d/runner.log"; exit 1; }
    grep -o "PTK value .*" $d/runner.log | head -1 > $d/NOT_COMPUTABLE
    echo "   not computable: $(cat $d/NOT_COMPUTABLE)"
  fi
  if [ "$t" = 1 ]; then
    for f in logk.f64 logself.f64 query_ids.txt corpus_ids.txt; do
      cmp -s $d/$f exp_v2/tuning/grid/PTK_l0.4_m0.6/$f || { echo "factor 1 differs from the tuning run: $f"; exit 1; }
    done
    echo "   factor 1 byte-identical to exp_v2/tuning/grid/PTK_l0.4_m0.6"
  fi
done

.venv/bin/python exp_v2/eval/terminal_factor.py
echo "terminal factor done $(date +%T)"
