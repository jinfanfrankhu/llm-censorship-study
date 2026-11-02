"""Analyze the topic-aware FP-budgeted censor.

Two parts:
1. Game outcome per strictness (from Exp K runs): success, in-loop block rate.
2. Standalone censor ROC on a fixed message pool (main_v2 plain clues):
   - recall = a censor enforcing concept C blocks C's own clue messages;
   - FP     = that same censor also blocks clue messages about OTHER concepts.
   Averaged over concepts. Shows whether catching on-topic messages forces
   collateral blocking of innocent lookalikes (the Weibo false-positive cost).

    python -m src.analyze_topic --judge openai/gpt-4o-mini --concepts 8 --k 5
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from .censor import TopicCensor
from .client import Client

STRICTNESS = ["lenient", "moderate", "strict"]


def game_stats(run_name: str) -> dict:
    p = Path("data/raw") / f"{run_name}.jsonl"
    if not p.exists():
        return {}
    trials = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    n = len(trials)
    msgs = blocked = 0
    for t in trials:
        for tr in t["turns"]:
            msgs += 1
            if tr["sender_filtered"].startswith("[message blocked"):
                blocked += 1
    return {"n": n, "success": sum(t["success"] for t in trials) / n,
            "block_rate": blocked / msgs if msgs else 0}


def pool_by_concept(run="main_v2") -> dict[str, list[str]]:
    p = Path("data/raw") / f"{run}.jsonl"
    by = defaultdict(list)
    for line in open(p, encoding="utf-8"):
        r = json.loads(line)
        for t in r["turns"]:
            raw = (t.get("sender_raw") or "").strip()
            if raw and not t["audit_flags"]:  # plain clues only
                by[r["target"]].append(" ".join(raw.split()))
    return by


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--judge", default="openai/gpt-4o-mini")
    ap.add_argument("--concepts", type=int, default=8)
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()

    print("=== game outcome per strictness (Exp K) ===")
    print(f"{'strictness':10} {'success':8} {'block_rate':10} {'n':3}")
    for s in STRICTNESS:
        g = game_stats(f"expK_topic_{s}")
        if g:
            print(f"{s:10} {g['success']:7.0%} {g['block_rate']:9.0%} {g['n']:3}")

    pool = pool_by_concept()
    concepts = [c for c in pool if len(pool[c]) >= args.k]
    rng = random.Random(0)
    concepts = rng.sample(concepts, min(args.concepts, len(concepts)))
    client = Client(budget_usd_max=10.0)

    print(f"\n=== standalone censor ROC ({len(concepts)} concepts, k={args.k} msgs each) ===")
    print(f"{'strictness':10} {'recall':8} {'FP':8}  (recall=blocks own topic; FP=blocks other topics)")
    for s in STRICTNESS:
        rec_hits = rec_tot = fp_hits = fp_tot = 0
        for C in concepts:
            cen = TopicCensor(C, client, args.judge, strictness=s)
            for m in pool[C][: args.k]:
                rec_tot += 1; rec_hits += cen.decide_block(m)
            others = [m for oc in concepts if oc != C for m in pool[oc][:2]]
            for m in rng.sample(others, min(args.k, len(others))):
                fp_tot += 1; fp_hits += cen.decide_block(m)
        print(f"{s:10} {rec_hits/rec_tot:7.0%} {fp_hits/fp_tot:7.0%}")
    print(f"\njudge spend ${client.spend_usd:.4f}")


if __name__ == "__main__":
    main()
