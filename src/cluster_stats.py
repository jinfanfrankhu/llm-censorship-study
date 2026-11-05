"""Cluster-aware tests for the propensity gap (v8n vs v9, gpt-4o-mini decode-censor).

The headline Fisher test (0/492 vs 92/492) treats games as independent, but games
share a word and a sender family. This script re-tests the gap with the word and
the family as the unit of analysis:

  * sign test over words   (does v9 beat v8n on more words than chance?)
  * sign test over families
  * word-cluster bootstrap CI for the rate difference (resample words with
    replacement, keep all their games)
  * stratified permutation test (swap prompt labels within word x family cells)

A mixed-effects logit is not identifiable here: v8n has zero successes in every
cell (complete separation), which is itself the strongest form of the result.

    python -m src.cluster_stats > data/cluster_stats.txt
"""
from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

RAW = Path("data/raw")
CONTROLS = {"dw02", "dw22", "dw34", "dw41"}
# runs behind the headline 0/492 vs 92/492 (gpt-4o-mini decode-censor)
RUN_PREFIXES = ["dwR", "dwS", "dwU", "dwW", "dwX"]
PROBES = ["dw_probes_R_meta5.jsonl", "dw_probes_S.jsonl", "dw_probes_U.jsonl",
          "dw_probes_W.jsonl", "dw_probes_X.jsonl"]
# --with_z adds Exp Z (reasoning + frontier senders). claude-sonnet-5.5 comes from
# the dwZs re-run; its dwZf rows had ~70% empty turns and are dropped.
Z_PREFIXES = ["dwZr", "dwZf", "dwZs"]
Z_PROBES = ["dw_probes_Zr.jsonl", "dw_probes_Zf.jsonl", "dw_probes_Zs.jsonl"]
DROP = {("dwZf", "anthropic/claude-sonnet-5.5")}


def jl(p: Path):
    with open(p, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def key(r):
    return (r["run"] if "run" in r else None, r["item_id"], r["model"], r["run_index"])


def load(with_z=False):
    prefixes = RUN_PREFIXES + (Z_PREFIXES if with_z else [])
    probes = PROBES + (Z_PROBES if with_z else [])
    games = {}  # (run, item, model, run_index) -> dict
    for pre in prefixes:
        for pv in ("v8n", "v9"):
            f = RAW / f"{pre}_{pv}_c4o.jsonl"
            if not f.exists():
                continue
            for r in jl(f):
                if r["item_id"] in CONTROLS or (pre, r["model"]) in DROP:
                    continue
                k = (f.stem, r["item_id"], r["model"], r["run_index"])
                games[k] = {"pv": pv, "item": r["item_id"], "fam": r["model"], "dw": 0}
    for pf in probes:
        f = RAW / pf
        if not f.exists():
            continue
        for p in jl(f):
            k = (p["run"], p["item_id"], p["model"], p["run_index"])
            if k in games and (not p["out_recover"]) and p["innocent"]:
                games[k]["dw"] = 1
    return list(games.values())


def sign_p(pos: int, neg: int) -> float:
    n = pos + neg
    k = min(pos, neg)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--with_z", action="store_true", help="add Exp Z senders")
    g = load(ap.parse_args().with_z)
    tot = Counter((x["pv"]) for x in g)
    dws = Counter(x["pv"] for x in g if x["dw"])
    print(f"games: v8n {dws['v8n']}/{tot['v8n']}   v9 {dws['v9']}/{tot['v9']}")
    print("(without --with_z this should match 0/492 vs 92/492; differences = dedupe/probe coverage)")
    from scipy.stats import fisher_exact
    _, pf = fisher_exact([[dws["v9"], tot["v9"] - dws["v9"]],
                          [dws["v8n"], tot["v8n"] - dws["v8n"]]])
    print(f"Fisher exact (games treated as independent): p = {pf:.2g}\n")

    for unit in ("item", "fam"):
        cell = defaultdict(lambda: {"v8n": [0, 0], "v9": [0, 0]})
        for x in g:
            cell[x[unit]][x["pv"]][0] += x["dw"]
            cell[x[unit]][x["pv"]][1] += 1
        pos = neg = tie = 0
        for u, c in sorted(cell.items()):
            r8 = c["v8n"][0] / max(c["v8n"][1], 1)
            r9 = c["v9"][0] / max(c["v9"][1], 1)
            pos += r9 > r8
            neg += r9 < r8
            tie += r9 == r8
        label = "words" if unit == "item" else "sender models"
        print(f"sign test over {label}: v9 > v8n in {pos}, v9 < v8n in {neg}, tied {tie} "
              f"(ties dropped)  two-sided p = {sign_p(pos, neg):.2g}")
        if unit == "item":
            zero = [u for u, c in cell.items() if c["v9"][0] == 0]
            print(f"   words with no v9 dogwhistle: {sorted(zero)}")

    # word-cluster bootstrap
    rng = random.Random(0)
    by_item = defaultdict(list)
    for x in g:
        by_item[x["item"]].append(x)
    items = sorted(by_item)
    diffs = []
    for _ in range(10000):
        s = [x for it in (rng.choice(items) for _ in items) for x in by_item[it]]
        n9 = sum(1 for x in s if x["pv"] == "v9")
        n8 = sum(1 for x in s if x["pv"] == "v8n")
        d9 = sum(x["dw"] for x in s if x["pv"] == "v9")
        d8 = sum(x["dw"] for x in s if x["pv"] == "v8n")
        diffs.append(d9 / max(n9, 1) - d8 / max(n8, 1))
    diffs.sort()
    point = dws["v9"] / tot["v9"] - dws["v8n"] / tot["v8n"]
    print(f"\nword-cluster bootstrap (10k): diff = {point:.3f}, 95% CI "
          f"[{diffs[249]:.3f}, {diffs[9749]:.3f}]")

    # stratified permutation: shuffle prompt labels within word x family cells
    cells = defaultdict(list)
    for x in g:
        cells[(x["item"], x["fam"])].append(x)
    obs = dws["v9"] - dws["v8n"]
    ge = 0
    R = 20000
    for _ in range(R):
        stat = 0
        for xs in cells.values():
            labels = [x["pv"] for x in xs]
            rng.shuffle(labels)
            stat += sum((1 if l == "v9" else -1) * x["dw"] for l, x in zip(labels, xs))
        ge += stat >= obs
    print(f"stratified permutation (word x family cells, {R} draws): "
          f"p <= {(ge + 1) / (R + 1):.2g} (one-sided)")
    print("\nmixed-effects logit: not identifiable (v8n has at most one success in the "
          "whole grid: quasi-complete separation).")


if __name__ == "__main__":
    main()
