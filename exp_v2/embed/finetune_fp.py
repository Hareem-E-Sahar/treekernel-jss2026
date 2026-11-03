"""exp_v2: fine-tune CodeBERT with BigCloneBench's false positives as hard negatives (decided 2026-10-31).

usage (from the repository root; exp_v2/scripts/run_codebert_fp.sh runs everything in order):
  finetune_fp.py finetune FOLD [STEPS]   -> data/codebert/models_fp/fold<FOLD>/
  finetune_fp.py encode FOLD             -> data/codebert/emb/fpft_fold<FOLD>_e5.npy (72,782 methods, order of D.tsv)

Same as embed/codebert.py finetune (folds, functionalities, sampling, loss, optimiser, steps, seed, 256 tokens), plus:
  - Hard negatives: for each of the 16 pairs (a, b) of functionality t, one false positive judged for t is added to
    the batch, when t has one. Loss: a against [b; negatives] and b against [a; negatives] (InfoNCE, temperature
    0.05), averaged; the other pairs' methods stay negatives as before.
  - No leakage: model k uses only false positives whose judged functionalities all lie outside fold k (the rule used
    for the true positives).
  - Memory: gradient checkpointing (recomputes activations in the backward pass; same gradients).
  - Excluded: false positives whose source equals (ignoring whitespace) a true positive of a functionality they are
    judged false for (160), so the model is never told that a method differs from an exact copy of itself.
False positives: those in the corpus (data/trees_e5, judged false for the functionalities in its functionality_ids).
"""
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "embed"))
import codebert as cb  # noqa: E402

TREES = ROOT / "data/trees_e5/D.tsv"
SOURCE = ROOT / "data/trees_e5/source.tsv"
MODELS = cb.D / "models_fp"
THREADS = 14   # embed/codebert.py uses 8; the thread count changes speed, not the method
_setup = cb.torch_setup


def torch_setup():
    torch = _setup()
    torch.set_num_threads(THREADS)
    return torch


cb.torch_setup = torch_setup   # also used by cb.encode


def false_positives(src):
    """fp id -> functionalities it is judged false for (exact copies of a true positive of those removed)"""
    fpf = {}
    for l in SOURCE.read_bytes().split(b"\n")[1:]:
        if l:
            i, fs, _ = l.decode("utf-8", "replace").split("\t", 2)
            fpf[i] = set(fs.split(","))
    main = set(cb.ids_of(cb.TREES))
    fpf = {i: v for i, v in fpf.items() if i not in main}
    tasks = cb.tasks_of(main)
    key = {}
    for c in main:
        for t in tasks[c]:
            key.setdefault(t, set()).add(re.sub(r"\s+", "", src[c]))
    copies = {i for i, v in fpf.items() if any(re.sub(r"\s+", "", src[i]) in key.get(t, ()) for t in v)}
    return {i: v for i, v in fpf.items() if i not in copies}, len(copies)


def finetune(k, steps=500, pairs=16, lr=2e-5, temp=0.05, maxlen=256):
    torch = torch_setup()
    rng = np.random.default_rng(cb.SEED + k)
    fold_of, _ = cb.read_folds()
    corpus = cb.ids_of(cb.TREES)
    tasks = cb.tasks_of(corpus)
    src = cb.sources(SOURCE)
    members = defaultdict(list)
    for c in corpus:
        if tasks[c] and all(fold_of[t] != k for t in tasks[c]):
            for t in tasks[c]:
                members[t].append(c)
    funcs = sorted((t for t in members if len(members[t]) >= 2), key=int)
    p = np.sqrt([len(members[t]) for t in funcs])
    p /= p.sum()
    fpf, n_copies = false_positives(src)
    hard = defaultdict(list)
    for i, v in sorted(fpf.items(), key=lambda x: int(x[0])):
        if all(fold_of.get(t, -1) != k for t in v):
            for t in v:
                hard[t].append(i)
    tok, m = cb.load_model(cb.MODEL)
    m.gradient_checkpointing_enable()   # memory: 48 inputs per batch instead of 32; same computation
    m.train()
    opt = torch.optim.AdamW(m.parameters(), lr=lr, weight_decay=0.01)
    warm = steps // 10
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: (s + 1) / warm if s < warm else max(0.0, (steps - s) / (steps - warm)))
    out = MODELS / f"fold{k}"
    log = []
    t0 = time.time()
    for step in range(steps):
        fs = rng.choice(funcs, size=pairs, replace=False, p=p)
        a, b = zip(*(rng.choice(members[t], size=2, replace=False) for t in fs))
        h = tuple(hard[t][rng.integers(len(hard[t]))] for t in fs if hard[t])
        x = tok([src[i] for i in a + b + h], padding=True, truncation=True, max_length=maxlen, return_tensors="pt")
        with torch.autocast("cpu", dtype=torch.bfloat16):
            e = m(**x).last_hidden_state[:, 0]
        e = torch.nn.functional.normalize(e.float(), dim=-1)
        ea, eb, eh = e[:pairs], e[pairs:2 * pairs], e[2 * pairs:]
        y = torch.arange(pairs)
        loss = (torch.nn.functional.cross_entropy(ea @ torch.cat([eb, eh]).T / temp, y)
                + torch.nn.functional.cross_entropy(eb @ torch.cat([ea, eh]).T / temp, y)) / 2
        loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
        opt.step()
        sched.step()
        opt.zero_grad()
        log.append((step, loss.item(), len(h)))
        if step % 25 == 0 or step == steps - 1:
            print(f"  fold {k} step {step} loss {np.mean([v for _, v, _ in log[-25:]]):.3f} {time.time() - t0:.0f}s", flush=True)
    out.mkdir(parents=True, exist_ok=True)
    m.save_pretrained(out)
    with open(out / "train_log.tsv", "w") as o:
        o.write("step\tloss\thard_negatives\n")
        o.writelines(f"{s}\t{v:.5f}\t{n}\n" for s, v, n in log)
    (out / "train_meta.json").write_text(json.dumps({
        "fold": k, "base": cb.MODEL, "steps": steps, "pairs_per_batch": pairs, "lr": lr, "temperature": temp,
        "max_len": maxlen, "seed": cb.SEED + k, "training_functionalities": len(funcs),
        "training_methods": len({c for t in funcs for c in members[t]}),
        "hard_negative_pool": len({i for t in funcs for i in hard[t]}),
        "functionalities_with_hard_negatives": sum(1 for t in funcs if hard[t]),
        "excluded_exact_copies": n_copies,
        "hard_negatives_per_batch_mean": round(float(np.mean([n for *_, n in log])), 2),
        "threads": torch.get_num_threads(), "seconds": round(time.time() - t0, 1)}))
    print(f"fold {k} trained in {time.time() - t0:.0f}s -> {out}")


if __name__ == "__main__":
    cmd, k, *a = sys.argv[1:]
    if cmd == "finetune":
        finetune(int(k), *(int(x) for x in a[:1]))
    elif cmd == "encode":
        cb.encode(str(MODELS / f"fold{k}"), TREES, SOURCE, cb.D / f"emb/fpft_fold{k}_e5.npy")
    else:
        sys.exit(__doc__)
