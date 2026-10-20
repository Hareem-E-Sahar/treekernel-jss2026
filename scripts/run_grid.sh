#!/usr/bin/env bash
# Grid search on one variant (PLAN.md §5.1): 50 tuning queries, reduced corpus (data/trees_main).
# Common grid (decided 2026-10-17): every lambda and mu in {0.1, 0.2, 0.4, 0.6, 0.8, 1.0}.
#   STK: lambda (6 settings); SSTK: lambda (6); PTK: lambda x mu (36).
# Each setting is first checked for float overflow (GridFiniteScan, cached in
# results/grid_scan/main_corpus/scan.tsv); settings that overflow are skipped and reported
# as "not computable". The run holds a sleep inhibitor so the laptop doesn't suspend.
# usage: scripts/run_grid.sh VARIANT [threads]
set -euo pipefail
cd "$(dirname "$0")/.."
V=$1; THREADS=${2:-14}
if [ -z "${INHIBITED:-}" ]; then
  exec env INHIBITED=1 systemd-inhibit --what=sleep:idle:handle-lid-switch --who=treekernel \
    --why="grid search $V" "$0" "$@"
fi
CP=kernels/target/classes:$(cat kernels/classpath.txt)
OUT=results/grid/$V
SCAN=results/grid_scan/main_corpus/scan.tsv
mkdir -p "$OUT"
G="0.1 0.2 0.4 0.6 0.8 1.0"
SETTINGS=""
for l in $G; do SETTINGS="$SETTINGS STK:$l:0"; done
for l in $G; do SETTINGS="$SETTINGS SSTK:$l:0"; done
for l in $G; do for m in $G; do SETTINGS="$SETTINGS PTK:$l:$m"; done; done

for s in $SETTINGS; do
  IFS=: read -r k l m <<< "$s"
  label="lambda=$l"; d=$OUT/${k}_l${l}
  if [ "$k" = PTK ]; then label="$label,mu=$m"; d=${d}_m$m; fi
  key=$(printf '%s.tsv\t%s\t%s\t' "$V" "$k" "$label")
  if ! grep -qF "$key" "$SCAN"; then
    spec="$k:$l"; if [ "$k" = PTK ]; then spec="$spec:$m"; fi
    java -Xmx6g -DdumpDir=results/grid_scan/main_corpus -cp "$CP" treekernel.GridFiniteScan \
      data/trees_main/$V.tsv "$THREADS" 1800 "$spec" 2>/dev/null >> "$SCAN"
  fi
  if ! grep -F "$key" "$SCAN" | grep -q "non-finite=0"; then
    echo "-- $k $label: not computable ($(grep -F "$key" "$SCAN" | cut -f5))"
    continue
  fi
  if [ ! -f "$d/meta.json" ]; then
    echo "== $k $label $(date +%T)"
    java -Xmx6g -Dorg.slf4j.simpleLogger.defaultLogLevel=error -cp "$CP" treekernel.RetrievalRunner \
      data/trees_main/$V.tsv data/pools/tuning.tsv "$k" "$l" "$m" "$THREADS" "$d" 2>&1 | grep -v "corpus methods scored"
  fi
  [ -f "$d/eval/per_query.tsv" ] || .venv/bin/python eval/evaluate.py "$d" --syntactic data/pools/tuning.tsv > /dev/null
done
echo "all done $(date +%T)"
