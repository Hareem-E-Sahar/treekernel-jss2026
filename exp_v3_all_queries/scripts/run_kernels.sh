#!/usr/bin/env bash
# exp_v3_all_queries (revision_plan.md, R1-C1a): STK, SSTK and PTK on every eligible query (exp_v2/data/full/union.tsv,
# 14,587 queries) against the corpus with false positives (data/trees_e5/D.tsv), variant D, at the settings tuned in
# exp_v2 (exp_v2/tuning/selected.json; PTK terminal factor 1). Rows already scored in the exp_v2 replicate and
# size-complexity runs are reused; only the remaining queries are scored, in chunks below the runner's 2 GB buffer
# limit; exp_v2/eval/merge_runs.py then assembles one run per kernel (rows copied unchanged, so the result equals a
# single run over all queries). exp_v2 code and results are only read.
# usage: exp_v3_all_queries/scripts/run_kernels.sh [threads]   -> exp_v3_all_queries/results/runs/D_{STK,SSTK,PTK}
set -euo pipefail
cd "$(dirname "$0")/../.."
if [ -z "${INHIBITED:-}" ]; then
  exec env INHIBITED=1 systemd-inhibit --what=sleep:idle:handle-lid-switch --who=treekernel \
    --why="exp_v3 kernels on all queries" "$0" "$@"
fi
THREADS=${1:-14}
CP=kernels/target/classes:$(cat kernels/classpath.txt)
TREES=data/trees_e5/D.tsv
U=exp_v2/data/full/union.tsv
REP=exp_v2/results/fp/runs
SZ=exp_v2/results/size_complexity/runs
SEL=exp_v2/tuning/selected.json
R=exp_v3_all_queries/results
O=$R/runs
N=$R/new_queries
CHUNK=1500
mkdir -p $O $N
cp $SEL $R/selected.json

# queries without a kernel row in the exp_v2 replicate or size-complexity runs, in chunks
if [ ! -f $N/done ]; then
  comm -23 <(tail -n +2 $U | cut -f1 | sort) <(cat $REP/D_PTK/query_ids.txt $SZ/D_PTK/query_ids.txt | sort -u) \
    | sort -n > $N/all.txt
  rm -f $N/part*.tsv
  split -l $CHUNK -d -a 2 $N/all.txt $N/chunk
  for c in $N/chunk*; do { echo function_id; cat $c; } > $N/part${c##*chunk}.tsv; rm $c; done
  touch $N/done
fi
echo "queries: $(($(wc -l < $U) - 1)); new: $(wc -l < $N/all.txt) in $(ls $N/part*.tsv | wc -l) chunks $(date '+%F %T')"

for k in STK SSTK PTK; do
  name=$(.venv/bin/python -c "import json; print(json.load(open('$SEL'))['settings']['$k']['run'])")
  l=$(sed -E 's/^[A-Z]+_l([0-9.]+).*/\1/' <<< "$name")
  m=$(sed -nE 's/.*_m([0-9.]+)$/\1/p' <<< "$name"); m=${m:-0}
  [ -f $O/D_$k/meta.json ] && continue
  parts=""
  for p in $N/part*.tsv; do
    d=$N/D_${k}_$(basename $p .tsv)
    parts="$parts $d"
    [ -f $d/meta.json ] && continue
    echo "== D $k ($name) $(basename $p) $(date '+%F %T')"
    java -Xmx8g -Dorg.slf4j.simpleLogger.defaultLogLevel=error -cp "$CP" treekernel.RetrievalRunner \
      $TREES $p "$k" "$l" "$m" "$THREADS" $d 2>&1 | grep -v "corpus methods scored" || true
    [ -f $d/meta.json ]
  done
  .venv/bin/python exp_v2/eval/merge_runs.py $U $O/D_$k $REP/D_$k $SZ/D_$k $parts
  rm -r $parts
done
touch $R/KERNELS_DONE
echo "kernels done $(date '+%F %T')"
