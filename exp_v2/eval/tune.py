"""exp_v2 tuning on the corpus with false positives: KeLP settings, fusion kernels and fusion weights.

usage: .venv/bin/python exp_v2/eval/tune.py   (after exp_v2/scripts/run_tuning.sh)
  -> exp_v2/tuning/{grid.tsv, selected.json, fusion/<name>/tuning.tsv}

All on the 50 tuning queries (exp_v2/data/tuning.tsv), corpus data/trees_e5/D.tsv (72,782 methods), false positives
that are exact copies of the query ignored (exp_v2/data/fp_copies.tsv). Same procedure as the frozen experiment:
  settings: per kernel, the computable grid setting with the highest RQ1 objective (mean over T1-MT3 of micro MAP);
  fusion kernels: the kernel with the highest RQ1 objective (fused for RQ1) and the one with the highest functional
    MAP (fused for RQ2), each at its selected setting;
  fusion weight: W in {0, 0.1, ..., 1} maximising the same objective; ties -> the larger W (more tree kernel).
Ties between settings: the higher value wins; equal values keep the first setting in grid order.
Override (decided 2026-10-21): RQ2 fuses STK, as in the frozen experiment, whichever kernel the rule picks (the three are
within noise on the tuning queries). Both are recorded.
RQ2 objective (decided 2026-10-25): functional MAP. It was MAP@R until then; the selected W are the same under both
(STK + BM25 0.0, STK + CodeBERT ft 0.2), so no run changed, and under MAP the rule itself picks STK for RQ2.
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "exp_v2/eval"))
from fusion import fuse  # noqa: E402

T = ROOT / "exp_v2/tuning"
TQ = ROOT / "exp_v2/data/tuning.tsv"
IGN = ROOT / "exp_v2/data/fp_copies.tsv"
G = ["0.1", "0.2", "0.4", "0.6", "0.8", "1.0"]
OTHERS = {"BM25": T / "runs/bm25", "CodeBERT ft": T / "runs/codebert_ft"}


def evaluate(run):
    if not (Path(run) / "eval/summary.tsv").exists():
        subprocess.run([sys.executable, str(ROOT / "exp_v2/eval/evaluate.py"), str(run), "--syntactic", str(TQ),
                        "--functional", str(TQ), "--ignore", str(IGN), "--boot", "0"], check=True, stdout=subprocess.DEVNULL)
    v = {}
    for r in csv.DictReader(open(Path(run) / "eval/summary.tsv"), delimiter="\t"):
        if r["category"] == "all" and r["averaging"] == "micro":
            if r["type"] == "mean5" and r["metric"] == "AP":
                v["rq1"] = float(r["value"])
            if r["type"] == "functional" and r["metric"] == "AP":
                v["rq2"] = float(r["value"])
    return v


def grid_order():
    out = [f"STK_l{l}" for l in G] + [f"SSTK_l{l}" for l in G] + [f"PTK_l{l}_m{m}" for l in G for m in G]
    return out


rows, best = [], {}
for name in grid_order():
    d = T / "grid" / name
    k = name.split("_")[0]
    if (d / "meta.json").exists():
        v = evaluate(d)
        rows.append((name, "ok", v["rq1"], v["rq2"]))
        if k not in best or v["rq1"] > best[k][1]:
            best[k] = (name, v["rq1"], v["rq2"])
    elif (d / "NOT_COMPUTABLE").exists():
        rows.append((name, (d / "NOT_COMPUTABLE").read_text().strip(), None, None))
with open(T / "grid.tsv", "w") as o:
    o.write("setting\tstatus\trq1_mean5_map\trq2_map\n")
    for n, st, a, b in rows:
        o.write(f"{n}\t{st}\t{'' if a is None else f'{a:.6f}'}\t{'' if b is None else f'{b:.6f}'}\n")

by_rule = {"rq1": max(best, key=lambda k: best[k][1]), "rq2": max(best, key=lambda k: best[k][2])}
OVERRIDE = {"rq2": "STK"}
fusion_kernel = {**by_rule, **OVERRIDE}
weights = {}
for obj, k in fusion_kernel.items():
    for olab, orun in OTHERS.items():
        name = f"{obj}_{k}_{'bm25' if olab == 'BM25' else 'codebert_ft'}"
        res = []
        for i in range(11):
            w = i / 10
            d = T / "fusion" / name / f"wsum_w{w:.1f}"
            if not (d / "meta.json").exists():
                fuse(T / "grid" / best[k][0], orun, d, "wsum", w)
            res.append((w, evaluate(d)[obj]))
        wbest = max(res, key=lambda r: (round(r[1], 6), r[0]))[0]
        with open(T / "fusion" / name / "tuning.tsv", "w") as o:
            o.write(f"w\t{obj}\n" + "".join(f"{w:.1f}\t{v:.6f}\n" for w, v in res))
        weights[name] = {"kernel": k, "other": olab, "objective": obj, "w": wbest}
        print(f"{name}: W = {wbest:.1f}")

sel = {"settings": {k: {"run": v[0], "rq1_mean5_map": v[1], "rq2_map": v[2]} for k, v in best.items()},
       "fusion_kernel": fusion_kernel, "fusion_kernel_by_rule": by_rule,
       "fusion_kernel_override": "rq2: STK, as in the frozen experiment (the kernels are within noise on the tuning queries)",
       "fusion": weights,
       "others_on_tuning_queries": {lab: evaluate(r) for lab, r in OTHERS.items()}}
(T / "selected.json").write_text(json.dumps(sel, indent=2))
print(json.dumps(sel, indent=2))
