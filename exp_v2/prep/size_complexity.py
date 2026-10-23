"""Size and cyclomatic complexity of every true positive (the methods that can be queries).

usage: .venv/bin/python exp_v2/prep/size_complexity.py   -> exp_v2/data/size_complexity.tsv

  loc              physical lines of the method: endline - startline + 1 (BCB functions.tsv), = lines of its source
  normalized_size  BCB's own size column (lines after BCB's normalisation), for reference
  cc               McCabe cyclomatic complexity from Checkstyle 10.21.1 (third_party/checkstyle), check
                   CyclomaticComplexity with its defaults (if, while, do, for, ?:, catch, each case, &&, || count 1;
                   switchBlockAsSingleDecisionPoint = false), max = 0 so every method is reported.
                   Each method is wrapped in a class of its own; methods of anonymous or local classes inside it are
                   reported separately by Checkstyle and are not part of its value (the first report, i.e. the
                   outermost method, is taken).
  cc_status        ok / parse_error (Checkstyle could not parse the method; cc empty)
"""
import csv
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bm25"))
from code_tokens import unescape  # noqa: E402

JAR = ROOT / "third_party/checkstyle/checkstyle-10.21.1-all.jar"
CONFIG = """<?xml version="1.0"?>
<!DOCTYPE module PUBLIC "-//Checkstyle//DTD Checkstyle Configuration 1.3//EN" "https://checkstyle.org/dtds/configuration_1_3.dtd">
<module name="Checker">
  <property name="charset" value="UTF-8"/>
  <property name="severity" value="warning"/>
  <module name="TreeWalker">
    <module name="CyclomaticComplexity"><property name="max" value="0"/></module>
  </module>
</module>
"""
BATCH = 2000
REPORT = re.compile(r"M(\d+)\.java:(\d+):\d+: Cyclomatic Complexity is (\d+)")
ERROR = re.compile(r"M(\d+)\.java")

tp = [l.split("\t", 1)[0] for l in open(ROOT / "data/trees_main/D.tsv").read().splitlines()[1:]]
tps = set(tp)
meta = {r["id"]: r for r in csv.DictReader(open(ROOT / "data/full_bcb/functions.tsv"), delimiter="\t") if r["id"] in tps}
src = {}
# rows end at \n only: sources can contain a bare \r, which csv and text-mode iteration would treat as a row end
for line in (ROOT / "data/trees_main/source.tsv").read_bytes().decode("utf-8").split("\n")[1:]:
    if line:
        i, _, esc = line.split("\t", 2)
        if i in tps:
            src[i] = unescape(esc)
assert set(src) == tps, f"source missing for {len(tps - set(src))} methods"

cc, errors = {}, set()
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    (tmp / "config.xml").write_text(CONFIG)
    files = {}
    for i in tp:
        files[i] = tmp / f"M{i}.java"
        files[i].write_text(f"class M{i} {{\n{src[i]}\n}}\n", encoding="utf-8")
    todo = list(tp)
    while todo:
        # Checkstyle abandons the rest of a run when a file fails to parse: rerun what was not reported, without it
        batch = todo[:BATCH]
        p = subprocess.run(["java", "-jar", str(JAR), "-c", str(tmp / "config.xml"), *map(str, (files[i] for i in batch))],
                           capture_output=True, text=True)
        first = {}
        for line in p.stdout.splitlines():
            m = REPORT.search(line)
            if m and (m.group(1) not in first or int(m.group(2)) < first[m.group(1)][0]):
                first[m.group(1)] = (int(m.group(2)), int(m.group(3)))
        failed = {m.group(1) for line in p.stderr.splitlines() for m in [ERROR.search(line)] if m} - set(first)
        if not first and not failed:
            raise RuntimeError(p.stdout[-2000:] + p.stderr[-2000:])
        errors |= failed
        cc.update({i: v for i, (_, v) in first.items()})
        todo = [i for i in todo if i not in cc and i not in errors]
        print(f"{len(cc)} measured, {len(errors)} parse errors, {len(todo)} to go", file=sys.stderr)

out = ROOT / "exp_v2/data/size_complexity.tsv"
with open(out, "w") as o:
    o.write("function_id\tloc\tnormalized_size\tcc\tcc_status\n")
    for i in tp:
        loc = int(meta[i]["endline"]) - int(meta[i]["startline"]) + 1
        assert loc == src[i].count("\n") + 1, i
        st = "ok" if i in cc else "parse_error"
        o.write(f"{i}\t{loc}\t{meta[i]['normalized_size']}\t{cc.get(i, '')}\t{st}\n")
print(f"{out}: {len(tp)} methods, cc for {len(cc)}, parse errors {len(tp) - len(cc)}")
