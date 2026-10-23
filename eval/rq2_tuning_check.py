"""RQ2 tuning check: settings chosen by MAP@R (functional relevance) vs by the RQ1 objective, on the tuning queries.

usage: .venv/bin/python eval/rq2_tuning_check.py   -> results/rq2_tuning_check/selection.tsv (+ printed table)
Inputs: results/grid/<V>/<setting>/eval (RQ1 objective: mean5 micro AP) and
results/rq2_tuning_check/grid/<V>/<setting>/eval (functional micro AP@R; scripts/run_rq2_tuning_check.sh).
Ties: the higher value wins; equal values keep the setting listed first (sorted by name).
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
G = ROOT / "results/grid"
C = ROOT / "results/rq2_tuning_check"


def value(path, typ, metric):
    for r in csv.DictReader(open(path / "eval/summary.tsv"), delimiter="\t"):
        if r["type"] == typ and r["category"] == "all" and r["averaging"] == "micro" and r["metric"] == metric:
            return float(r["value"])
    raise KeyError(path)


rows = []
for v in "ABCD":
    for k in ("STK", "SSTK", "PTK"):
        runs = sorted(p for p in (C / "grid" / v).glob(f"{k}_l*") if (p / "eval/summary.tsv").exists())
        res = [(p.name, value(G / v / p.name, "mean5", "AP"), value(p, "functional", "AP@R")) for p in runs]
        by1 = max(res, key=lambda x: x[1])
        by2 = max(res, key=lambda x: x[2])
        rows.append((v, k, len(res), by1[0], by1[1], by1[2], by2[0], by2[1], by2[2]))

hdr = ["variant", "kernel", "settings", "rq1_choice", "rq1_choice_mean5", "rq1_choice_mapr",
       "rq2_choice", "rq2_choice_mean5", "rq2_choice_mapr"]
with open(C / "selection.tsv", "w") as o:
    o.write("\t".join(hdr) + "\n")
    for r in rows:
        o.write("\t".join(f"{x:.4f}" if isinstance(x, float) else str(x) for x in r) + "\n")
print("| Variant | Kernel | Settings | Chosen by RQ1 objective | its MAP@R | Chosen by MAP@R | its MAP@R | Δ MAP@R | its RQ1 mean |")
print("|---|---|---|---|---|---|---|---|---|")
for v, k, n, s1, a1, m1, s2, a2, m2 in rows:
    print(f"| {v} | {k} | {n} | {s1} | {m1:.3f} | {s2} | {m2:.3f} | {m2 - m1:+.3f} | {a2:.3f} |")
