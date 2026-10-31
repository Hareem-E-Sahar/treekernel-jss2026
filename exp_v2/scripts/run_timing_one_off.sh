#!/usr/bin/env bash
# exp_v2 one-off costs on the corpus with false positives (72,782 methods), next to exp_v2/scripts/run_timing.sh:
#   building the variant-D trees (tree-sitter parse + variant D, one thread; exp_v2/prep/time_trees.py)
#   building the BM25 index (bm25/run_bm25.py index, into a temporary index that is deleted afterwards; Elasticsearch
#   uses its own threads, the client tokenises on one)
# CodeBERT's one-off cost (corpus encoding) is exp_v2/hybrid/timing_codebert.py --encode-sample.
# usage: exp_v2/scripts/run_timing_one_off.sh   -> exp_v2/results/timing/{trees.tsv,bm25_index.json}
set -euo pipefail
cd "$(dirname "$0")/../.."
if [ -z "${INHIBITED:-}" ]; then
  exec env INHIBITED=1 systemd-inhibit --what=sleep:idle:handle-lid-switch --who=treekernel \
    --why="exp_v2 one-off timing" "$0" "$@"
fi
O=exp_v2/results/timing
pgrep -f "org.elasticsearch|RetrievalRunner|HybridRerank" > /dev/null && { echo "another run is active; timing needs an idle machine"; exit 1; }
.venv/bin/python -I exp_v2/prep/time_trees.py data/trees_e5/source.tsv | tee $O/trees.tsv
scripts/es_start.sh > $O/es_index.log 2>&1 &
ES=$!
until curl -s localhost:9201 > /dev/null; do sleep 5; done
# run_bm25.py writes results/bm25/index_<name>.json relative to the working directory: run it from exp_v2/
(cd exp_v2 && ../.venv/bin/python -I ../bm25/run_bm25.py index bcb_timing_v2 "$PWD/../data/trees_e5/D.tsv" \
  "$PWD/../data/trees_e5/source.tsv")
mv exp_v2/results/bm25/index_bcb_timing_v2.json $O/bm25_index.json
rmdir exp_v2/results/bm25 2>/dev/null || true
curl -s -X DELETE localhost:9201/bcb_timing_v2 > /dev/null
kill $ES; wait $ES || true
cat $O/bm25_index.json
