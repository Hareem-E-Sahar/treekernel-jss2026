#!/usr/bin/env bash
# Replication over 10 query sets (decision 2026-10-20; seeds from the user's earlier study; data/pools/replicates/).
# Variant D only (user, 2026-10-20). One retrieval run per method over the union of all replicate queries
# (data/pools/replicates/union.tsv), then each replicate is evaluated from those runs:
#   tree kernels D at the tuned settings (STK l0.8, SSTK l0.1, PTK l0.4 m0.6), BM25, CodeBERT zero-shot and
#   fine-tuned (each query scored by its fold's model), and the RQ4 fusions at the W tuned on the tuning queries.
# usage: scripts/run_replicates.sh   -> results/replicates/{runs,seed<S>/<method>/eval}; finished steps are skipped.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -z "${INHIBITED:-}" ]; then
  exec env INHIBITED=1 systemd-inhibit --what=sleep:idle:handle-lid-switch --who=treekernel \
    --why="replicate runs" "$0" "$@"
fi
CP=kernels/target/classes:$(cat kernels/classpath.txt)
P=data/pools/replicates
U=$P/union.tsv
O=results/replicates/runs
mkdir -p $O
export HF_HOME=third_party/hf HF_HUB_OFFLINE=1

for s in STK:0.8:0 SSTK:0.1:0 PTK:0.4:0.6; do
  IFS=: read -r k l m <<< "$s"
  [ -f $O/D_$k/meta.json ] && continue
  echo "== D $k $(date +%T)"
  java -Xmx6g -Dorg.slf4j.simpleLogger.defaultLogLevel=error -cp "$CP" treekernel.RetrievalRunner \
    data/trees_main/D.tsv $U "$k" "$l" "$m" 14 $O/D_$k 2>&1 | grep -v "corpus methods scored" || true
  [ -f $O/D_$k/meta.json ]
done

[ -f $O/codebert_zs/meta.json ] || .venv/bin/python embed/codebert.py run $O/codebert_zs data/codebert/emb/zeroshot_main.npy --queries $U
[ -f $O/codebert_ft/meta.json ] || .venv/bin/python embed/codebert.py run $O/codebert_ft "data/codebert/emb/fold{k}_main.npy" --folds --queries $U

if [ ! -f $O/bm25/meta.json ]; then
  echo "== BM25 $(date +%T)"
  scripts/es_start.sh > results/replicates/es.log 2>&1 &
  ES=$!
  until curl -s localhost:9201 > /dev/null; do sleep 5; done
  curl -s "localhost:9201/_cluster/health/bcb_main?wait_for_status=yellow&timeout=120s" > /dev/null || true
  if ! curl -sf localhost:9201/bcb_main > /dev/null; then
    .venv/bin/python -I bm25/run_bm25.py index bcb_main data/trees_main/D.tsv data/trees_main/source.tsv
  fi
  .venv/bin/python -I bm25/run_bm25.py query bcb_main $U $O/bm25
  kill $ES; wait $ES || true
fi

fuse() {  # name tk_run other_run tuned_dir
  local w; w=$(basename "$(ls -d "$4"/wsum_w*)" | sed 's/wsum_w//')
  [ -f $O/$1_wsum/meta.json ] || .venv/bin/python eval/fusion.py $2 $3 $O/$1_wsum --method wsum --w "$w"
  [ -f $O/$1_rrf/meta.json ] || .venv/bin/python eval/fusion.py $2 $3 $O/$1_rrf --method rrf
}
fuse PTK_BM25 $O/D_PTK $O/bm25 results/rq4/rq1_PTK
fuse STK_BM25 $O/D_STK $O/bm25 results/rq4/rq2_STK
fuse PTK_CBft $O/D_PTK $O/codebert_ft results/rq4/rq1_PTK_codebert
fuse STK_CBft $O/D_STK $O/codebert_ft results/rq4/rq2_STK_codebert

echo "== evaluate $(date +%T)"
for d in $P/seed*; do
  s=$(basename $d)
  SYN=""
  for t in T1 T2 VST3 ST3 MT3; do SYN="$SYN --syntactic $d/syntactic_$t.tsv:$t"; done
  for r in $O/*/; do
    r=${r%/}
    e=results/replicates/$s/$(basename $r)/eval
    [ -f $e/summary.tsv ] || echo ".venv/bin/python eval/evaluate.py $r $SYN --functional $d/functional.tsv --boot 0 --out $e"
  done
done | xargs -P 3 -I{} sh -c "{} > /dev/null"
echo "all done $(date +%T)"
