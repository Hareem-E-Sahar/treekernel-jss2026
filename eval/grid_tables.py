"""Sensitivity tables for one variant's grid search (results/grid/<V>/, scripts/run_grid.sh).

usage: grid_tables.py VARIANT [--metric AP] [--root .]

Value = the tuning objective: micro-averaged metric per clone type, averaged over T1-MT3
(evaluate.py's `mean5`). Settings that overflow are shown as "n/c (N)", N = overflowing methods
(results/grid_scan/main_corpus/scan.tsv). Writes results/grid/<V>/tables_<metric>.md.
"""
import argparse
import csv
import re
from pathlib import Path

G = ["0.1", "0.2", "0.4", "0.6", "0.8", "1.0"]
ap = argparse.ArgumentParser()
ap.add_argument("variant")
ap.add_argument("--metric", default="AP")
ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
args = ap.parse_args()
V, R = args.variant, args.root

overflow = {}
for line in open(R / "results/grid_scan/main_corpus/scan.tsv"):
    f = line.rstrip("\n").split("\t")
    if f[0] != f"{V}.tsv":
        continue
    n = int(re.match(r"non-finite=(\d+)", f[4]).group(1))
    overflow[(f[1], f[2])] = n


def value(kernel, l, m=None):
    label = f"lambda={l}" + (f",mu={m}" if m else "")
    d = R / f"results/grid/{V}/{kernel}_l{l}" if m is None else R / f"results/grid/{V}/{kernel}_l{l}_m{m}"
    s = d / "eval/summary.tsv"
    if s.exists():
        for r in csv.DictReader(open(s), delimiter="\t"):
            if r["type"] == "mean5" and r["averaging"] == "micro" and r["metric"] == args.metric:
                return float(r["value"]), None
    n = overflow.get((kernel, label))
    return None, ("n/c (%s)" % f"{n:,}" if n else "not run")


lines = [f"# Grid search on variant {V}: mean {args.metric} over the five clone types (50 tuning queries)", "",
         "n/c (N) = not computable with KeLP as is; N methods overflow.", ""]
best = {}
for kernel in ["STK", "SSTK"]:
    vals = {l: value(kernel, l) for l in G}
    ok = {l: v for l, (v, _) in vals.items() if v is not None}
    b = max(ok, key=ok.get) if ok else None
    best[kernel] = (f"λ = {b}", ok[b]) if b else ("–", None)
    lines += [f"**{kernel}**", "", "| λ | " + " | ".join(G) + " |", "|---" * (len(G) + 1) + "|",
              f"| {args.metric} | " + " | ".join(
                  (f"**{v:.3f}**" if l == b else f"{v:.3f}") if v is not None else note
                  for l, (v, note) in vals.items()) + " |", ""]
vals = {(l, m): value("PTK", l, m) for l in G for m in G}
ok = {k: v for k, (v, _) in vals.items() if v is not None}
b = max(ok, key=ok.get)
best["PTK"] = (f"λ = {b[0]}, μ = {b[1]}", ok[b])
lines += ["**PTK** (rows λ, columns μ)", "", "| λ \\ μ | " + " | ".join(G) + " |", "|---" * (len(G) + 1) + "|"]
for l in G:
    cells = []
    for m in G:
        v, note = vals[(l, m)]
        cells.append((f"**{v:.3f}**" if (l, m) == b else f"{v:.3f}") if v is not None else note)
    lines.append(f"| **{l}** | " + " | ".join(cells) + " |")
lines += ["", "**Best setting per kernel**", "", "| Kernel | Setting | " + args.metric + " |", "|---|---|---|"]
for k, (s, v) in best.items():
    lines.append(f"| {k} | {s} | {v:.3f} |" if v is not None else f"| {k} | {s} | – |")
out = R / f"results/grid/{V}/tables_{args.metric}.md"
out.write_text("\n".join(lines) + "\n")
print("\n".join(lines))
