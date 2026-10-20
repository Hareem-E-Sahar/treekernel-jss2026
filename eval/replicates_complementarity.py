"""RQ4 complementarity on the 10 replicate query sets (eval/complementarity.py, per replicate).

usage: .venv/bin/python eval/replicates_complementarity.py   -> results/replicates/complementarity.tsv

For PTK (variant D, tuned) vs BM25 and vs fine-tuned CodeBERT, per replicate and query set: queries won / tied / lost
(primary metric), relevant items found within the top R by both, PTK only, the other only, neither, and top-10 overlap.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
from complementarity import analyse  # noqa: E402

R = ROOT / "results/replicates"
P = ROOT / "data/pools/replicates"
PAIRS = [("BM25", "bm25"), ("CodeBERT ft", "codebert_ft")]
SEEDS = sorted((p.name for p in P.glob("seed*")), key=lambda s: int(s[4:]))

with open(R / "complementarity.tsv", "w") as o:
    o.write("other\tseed\tset\tqueries\tptk_better\ttie\tother_better\tboth\tptk_only\tother_only\tneither\ttop10_overlap\n")
    for lab, d in PAIRS:
        for s in SEEDS:
            res = analyse(R / "runs/D_PTK", R / "runs" / d, pools=P / s,
                          evals=(R / s / "D_PTK/eval", R / s / d / "eval"))
            for t, n, w, ti, lo, f, ov in res:
                o.write(f"{lab}\t{s[4:]}\t{t}\t{n}\t{w}\t{ti}\t{lo}\t" + "\t".join(map(str, f)) + f"\t{ov:.4f}\n")
            print(lab, s, flush=True)
print("->", R / "complementarity.tsv")
