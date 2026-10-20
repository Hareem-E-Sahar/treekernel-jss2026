"""E5 corpus: the main corpus (data/trees_main, 14,679 methods) plus BigCloneBench's false
positives (data/trees_fp, built by build_fp_trees.py), variant D only.

False positives are excluded by the same rule as the main corpus (PLAN.md §4.1): KeLP's SSTK
self-similarity at λ = 0.4 overflows (here checked on D, the only variant used in E5). In
addition, any false positive that overflows at one of the E5 settings (D's tuned settings) is
excluded, so every E5 run is computable. Overflow ids: results/e5/scan/ (GridFiniteScan).

usage: build_e5_corpus.py   -> data/trees_e5/{D,source}.tsv, data/corpus/e5_excluded_fp.tsv
"""
from pathlib import Path

R = Path(__file__).resolve().parent.parent
SETTINGS = ["SSTK_0.4", "SSTK_0.1", "STK_0.8", "PTK_0.4_0.6"]
excl = {}
for s in SETTINGS:
    f = R / f"results/e5/scan/D_{s}.ids"
    assert (R / "results/e5/scan/scan.tsv").read_text().count("\n") >= 4, "scan not finished"
    if f.exists():
        for line in f.read_text().split("\n"):
            if line.strip() and not line.startswith("function_id"):
                fid = line.split("\t")[0]
                excl.setdefault(fid, []).append(s)
out = R / "data/trees_e5"
out.mkdir(exist_ok=True)
for name in ["D", "source"]:
    main = (R / f"data/trees_main/{name}.tsv").read_bytes().split(b"\n")
    fp = (R / f"data/trees_fp/{name}.tsv").read_bytes().split(b"\n")
    kept = [l for l in fp[1:] if l and l.split(b"\t", 1)[0].decode() not in excl]
    with open(out / f"{name}.tsv", "wb") as o:      # bytes: the source contains raw \r
        o.write(main[0] + b"\n")
        o.writelines(l + b"\n" for l in main[1:] if l)
        o.writelines(l + b"\n" for l in kept)
    print(f"{name}: {sum(1 for l in main[1:] if l)} main + {len(kept)} false positives")
with open(R / "data/corpus/e5_excluded_fp.tsv", "w") as o:
    o.write("function_id\toverflows_at\n")
    o.writelines(f"{k}\t{','.join(v)}\n" for k, v in sorted(excl.items(), key=lambda x: int(x[0])))
print(f"false positives excluded for overflow: {len(excl)}")
