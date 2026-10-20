"""CodeBERT baseline (zero-shot and fine-tuned), same queries, candidates and metrics as the tree kernels.

usage (run from the repository root; scripts/run_codebert.sh runs everything in order):
  codebert.py folds                         -> data/codebert/folds.tsv, query_folds.tsv
  codebert.py finetune FOLD                 -> data/codebert/models/fold<FOLD>/
  codebert.py encode MODEL TREES SOURCE OUT -> OUT.npy (one L2-normalised vector per method, order of TREES)
  codebert.py run OUT EMB [--folds] [--trees T] [--queries Q] -> run directory in RetrievalRunner's format (eval/evaluate.py);
                                               with --folds, EMB is a pattern with {k}
  codebert.py timing EMB OUT.json [TREES SOURCE]   -> RQ5 cost on one thread (default: main corpus)

Model: microsoft/codebert-base. Embedding = last-layer CLS vector (as in the earlier zero-shot setup),
L2-normalised; similarity = cosine. Input = the method source, truncated to 512 tokens (41% of methods
are longer). bf16 autocast on CPU, weights in fp32 (cosine to fp32 embeddings >= 0.99999).

Fine-tuning (bi-encoder, so the whole corpus can be ranked as for the other methods):
  5 folds by functionality. Functionalities that share an evaluation query are in the same fold; folds are
  balanced by number of evaluation queries. Model k is trained on methods whose functionalities all lie
  outside fold k and scores only the queries of fold k, against the whole corpus. So no evaluation query
  and none of its functionalities is seen in training.
  Positives: two methods of the same functionality (BigCloneBench true positives). Each batch = 16
  pairs from 16 different functionalities (sampled proportional to sqrt(#methods)); the other 30
  methods in the batch are the negatives. Symmetric InfoNCE, temperature 0.05. AdamW, lr 2e-5, weight
  decay 0.01, 500 steps, 10% linear warm-up then linear decay, training inputs truncated to 256 tokens
  (memory). Fixed a priori, not tuned (as BM25 uses Elasticsearch defaults). Seed 20261018.
Run format: logk = cosine (query itself NaN), logself = 0, so evaluate.py's score is exp(cosine),
which ranks identically to the cosine.
"""
import csv
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bm25"))
from code_tokens import unescape  # noqa: E402

MODEL = "microsoft/codebert-base"
D = ROOT / "data/codebert"
SEED = 20261018
NFOLD = 5
QUERIES = ROOT / "data/pools/eval_queries.tsv"
TREES = ROOT / "data/trees_main/D.tsv"
SOURCE = ROOT / "data/trees_main/source.tsv"


def ids_of(trees):
    return [l.split(b"\t", 1)[0].decode() for l in Path(trees).read_bytes().split(b"\n")[1:] if l]


def sources(path):
    """id -> source text (bytes, split on \\n only: the text contains raw \\r)."""
    out = {}
    for l in Path(path).read_bytes().split(b"\n")[1:]:
        if l:
            f = l.decode("utf-8", "replace").split("\t")
            out[f[0]] = unescape(f[2])
    return out


def tasks_of(ids):
    s = set(ids)
    t = defaultdict(set)
    for r in csv.DictReader(open(ROOT / "data/full_bcb/tp_functionalities.tsv"), delimiter="\t"):
        if r["function_id"] in s:
            t[r["function_id"]].add(r["functionality_id"])
    return t


def query_ids(queries=QUERIES):
    return [r["function_id"] for r in csv.DictReader(open(queries), delimiter="\t")]


# ---------------------------------------------------------------- folds
def folds():
    corpus = ids_of(TREES)
    tasks = tasks_of(corpus)
    qs = query_ids()
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for q in qs:
        t = sorted(tasks[q])
        for a in t[1:]:
            parent[find(a)] = find(t[0])
    alltasks = sorted({t for c in corpus for t in tasks[c]}, key=int)
    comp = defaultdict(list)
    for t in alltasks:
        comp[find(t)].append(t)
    nq = {r: sum(1 for q in qs if find(next(iter(tasks[q]))) == r) for r in comp}
    nm = {r: sum(1 for c in corpus if any(find(t) == r for t in tasks[c])) for r in comp}
    load = [0] * NFOLD
    fold_of = {}
    for r in sorted(comp, key=lambda r: (-nq[r], -nm[r], int(r))):     # greedy: largest first
        k = min(range(NFOLD), key=lambda i: (load[i], i))
        load[k] += nq[r]
        for t in comp[r]:
            fold_of[t] = k
    D.mkdir(parents=True, exist_ok=True)
    with open(D / "folds.tsv", "w") as o:
        o.write("functionality_id\tfold\n")
        o.writelines(f"{t}\t{fold_of[t]}\n" for t in alltasks)
    with open(D / "query_folds.tsv", "w") as o:
        o.write("function_id\tfold\n")
        for q in qs:
            ks = {fold_of[t] for t in tasks[q]}
            assert len(ks) == 1, q
            o.write(f"{q}\t{ks.pop()}\n")
    for k in range(NFOLD):
        ft = [t for t in alltasks if fold_of[t] == k]
        train = [c for c in corpus if tasks[c] and all(fold_of[t] != k for t in tasks[c])]
        print(f"fold {k}: {load[k]} queries, {len(ft)} functionalities held out, {len(train)} training methods")


def read_folds():
    f = {r["functionality_id"]: int(r["fold"]) for r in csv.DictReader(open(D / "folds.tsv"), delimiter="\t")}
    q = {r["function_id"]: int(r["fold"]) for r in csv.DictReader(open(D / "query_folds.tsv"), delimiter="\t")}
    return f, q


# ---------------------------------------------------------------- model
def torch_setup():
    import torch
    torch.set_num_threads(8)
    torch.manual_seed(SEED)
    return torch


def load_model(name):
    from transformers import AutoModel, AutoTokenizer
    return AutoTokenizer.from_pretrained(MODEL), AutoModel.from_pretrained(name)


def encode(model, trees, source, out, batch=32):
    torch = torch_setup()
    tok, m = load_model(model)
    m.eval()
    ids = ids_of(trees)
    src = sources(source)
    texts = [src[i] for i in ids]
    lens = [len(t) for t in texts]
    order = np.argsort(lens, kind="stable")
    emb = np.zeros((len(ids), m.config.hidden_size), np.float32)
    t0 = time.time()
    with torch.no_grad(), torch.autocast("cpu", dtype=torch.bfloat16):
        for s in range(0, len(ids), batch):
            idx = order[s:s + batch]
            x = tok([texts[i] for i in idx], padding=True, truncation=True, max_length=512, return_tensors="pt")
            v = m(**x).last_hidden_state[:, 0].float()
            emb[idx] = torch.nn.functional.normalize(v, dim=-1).numpy()
            if s // batch % 50 == 0:
                print(f"  {s + len(idx)}/{len(ids)} {time.time() - t0:.0f}s", flush=True)
    np.save(out, emb)
    Path(str(out) + ".json").write_text(json.dumps({"model": str(model), "trees": str(trees), "n": len(ids),
                                                    "seconds": round(time.time() - t0, 1)}))
    print(f"encoded {len(ids)} methods in {time.time() - t0:.0f}s -> {out}")


def finetune(k, steps=500, pairs=16, lr=2e-5, temp=0.05, maxlen=256):
    torch = torch_setup()
    rng = np.random.default_rng(SEED + k)
    fold_of, _ = read_folds()
    corpus = ids_of(TREES)
    tasks = tasks_of(corpus)
    src = sources(SOURCE)
    members = defaultdict(list)
    for c in corpus:
        if tasks[c] and all(fold_of[t] != k for t in tasks[c]):
            for t in tasks[c]:
                members[t].append(c)
    funcs = sorted((t for t in members if len(members[t]) >= 2), key=int)
    p = np.sqrt([len(members[t]) for t in funcs])
    p /= p.sum()
    tok, m = load_model(MODEL)
    m.train()
    opt = torch.optim.AdamW(m.parameters(), lr=lr, weight_decay=0.01)
    warm = steps // 10
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: (s + 1) / warm if s < warm else max(0.0, (steps - s) / (steps - warm)))
    out = D / f"models/fold{k}"
    log = []
    t0 = time.time()
    for step in range(steps):
        fs = rng.choice(funcs, size=pairs, replace=False, p=p)
        a, b = zip(*(rng.choice(members[t], size=2, replace=False) for t in fs))
        x = tok([src[i] for i in a + b], padding=True, truncation=True, max_length=maxlen, return_tensors="pt")
        with torch.autocast("cpu", dtype=torch.bfloat16):
            e = m(**x).last_hidden_state[:, 0]
        e = torch.nn.functional.normalize(e.float(), dim=-1)
        sim = e[:pairs] @ e[pairs:].T / temp
        y = torch.arange(pairs)
        loss = (torch.nn.functional.cross_entropy(sim, y) + torch.nn.functional.cross_entropy(sim.T, y)) / 2
        loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
        opt.step()
        sched.step()
        opt.zero_grad()
        log.append((step, loss.item()))
        if step % 25 == 0 or step == steps - 1:
            print(f"  fold {k} step {step} loss {np.mean([v for _, v in log[-25:]]):.3f} {time.time() - t0:.0f}s", flush=True)
    out.mkdir(parents=True, exist_ok=True)
    m.save_pretrained(out)
    with open(out / "train_log.tsv", "w") as o:
        o.write("step\tloss\n")
        o.writelines(f"{s}\t{v:.5f}\n" for s, v in log)
    (out / "train_meta.json").write_text(json.dumps({
        "fold": k, "base": MODEL, "steps": steps, "pairs_per_batch": pairs, "lr": lr, "temperature": temp,
        "max_len": maxlen, "seed": SEED + k, "training_functionalities": len(funcs),
        "training_methods": len({c for t in funcs for c in members[t]}), "seconds": round(time.time() - t0, 1)}))
    print(f"fold {k} trained in {time.time() - t0:.0f}s -> {out}")


def timing(emb, out, trees=TREES, source=SOURCE, sample=200):
    """RQ5, one thread like the tree kernels: model load (one-off); encoding one method at a time for a
    random sample of corpus methods (preparation = mean x corpus size); per query = encoding one of the
    20 timing queries + cosine against the corpus embeddings (emb)."""
    torch = torch_setup()
    torch.set_num_threads(1)
    t = time.time()
    tok, m = load_model(MODEL)
    m.eval()
    load_s = time.time() - t
    corpus = ids_of(trees)
    col = {c: i for i, c in enumerate(corpus)}
    src = sources(source)
    E = torch.from_numpy(np.load(emb))
    assert len(E) == len(corpus), (len(E), len(corpus))
    rng = np.random.default_rng(SEED)
    sample_ids = [corpus[i] for i in rng.choice(len(corpus), sample, replace=False)]
    tq = [r["function_id"] for r in csv.DictReader(open(ROOT / "data/pools/timing_queries.tsv"), delimiter="\t")]

    def enc(i):
        x = tok([src[i]], truncation=True, max_length=512, return_tensors="pt")
        v = m(**x).last_hidden_state[:, 0].float()
        return torch.nn.functional.normalize(v, dim=-1)[0]
    per_method, per_query = [], []
    with torch.no_grad(), torch.autocast("cpu", dtype=torch.bfloat16):
        enc(corpus[0])                                  # warm-up
        for i in sample_ids:
            t = time.time()
            enc(i)
            per_method.append(time.time() - t)
        for q in tq:
            t = time.time()
            s = E @ enc(q)
            s[col[q]] = float("nan")
            per_query.append(time.time() - t)
    Path(out).write_text(json.dumps({
        "threads": 1, "model_load_s": round(load_s, 2), "sample_methods": sample,
        "encode_ms_per_method_mean": round(1000 * float(np.mean(per_method)), 1),
        "corpus_encoding_s_estimate": round(float(np.mean(per_method)) * len(corpus), 1),
        "query_s_mean": round(float(np.mean(per_query)), 3), "query_s_min": round(min(per_query), 3),
        "query_s_max": round(max(per_query), 3), "n_queries": len(tq), "n_corpus": len(corpus)}, indent=1))
    print(Path(out).read_text())


# ---------------------------------------------------------------- run
def run(out, emb, use_folds=False, trees=TREES, queries=QUERIES):
    """emb: one .npy (zero-shot) or a pattern with {k} (one per fold; each query row is scored by the
    model of the fold that holds the query's functionalities)."""
    corpus = ids_of(trees)
    col = {c: i for i, c in enumerate(corpus)}
    qs = query_ids(queries)
    logk = np.zeros((len(qs), len(corpus)))
    if use_folds:
        fold_of, _ = read_folds()
        tasks = tasks_of(qs)
        qfold = {}
        for q in qs:
            ks = {fold_of[t] for t in tasks[q]}
            assert len(ks) == 1, f"query {q} spans folds {ks}"
            qfold[q] = ks.pop()
        E = {k: np.load(emb.format(k=k)) for k in range(NFOLD)}
        for r, q in enumerate(qs):
            e = E[qfold[q]]
            logk[r] = e @ e[col[q]]
    else:
        e = np.load(emb)
        logk = (e[[col[q] for q in qs]] @ e.T).astype(np.float64)
    for r, q in enumerate(qs):
        logk[r, col[q]] = np.nan
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    logk.astype("<f8").tofile(out / "logk.f64")
    np.zeros(len(corpus)).astype("<f8").tofile(out / "logself.f64")
    (out / "query_ids.txt").write_text("\n".join(qs) + "\n")
    (out / "corpus_ids.txt").write_text("\n".join(corpus) + "\n")
    (out / "meta.json").write_text(json.dumps({"kernel": "CodeBERT", "model": MODEL, "embeddings": str(emb),
                                               "fine_tuned": use_folds, "pooling": "CLS", "max_len": 512,
                                               "queries": str(queries), "n_queries": len(qs), "n_corpus": len(corpus)}))
    print(f"run: {len(qs)} queries x {len(corpus)} -> {out}")


if __name__ == "__main__":
    cmd, *a = sys.argv[1:]
    if cmd == "folds":
        folds()
    elif cmd == "finetune":
        finetune(int(a[0]), *(int(x) for x in a[1:2]))
    elif cmd == "encode":
        encode(a[0], a[1], a[2], a[3])
    elif cmd == "timing":
        timing(*a[:4])
    elif cmd == "run":
        opt = {k: a[a.index(k) + 1] for k in ("--trees", "--queries") if k in a}
        run(a[0], a[1], "--folds" in a, opt.get("--trees", TREES), opt.get("--queries", QUERIES))
    else:
        sys.exit(__doc__)
