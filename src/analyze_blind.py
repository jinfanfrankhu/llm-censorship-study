"""Analyze the blind FP-budgeted censor sweep.

For each strictness: communication success + how often game messages were blocked
(from the run), and the FALSE-POSITIVE rate = fraction of an innocent-message
bank the censor blocks. The thesis: you cannot drive success down without
driving the false-positive rate up.

    python -m src.analyze_blind --judge openai/gpt-4o-mini
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .censor import BlindCensor
from .client import Client

STRICTNESS = ["lenient", "moderate", "strict"]


def game_stats(run_name: str) -> dict:
    p = Path("data/raw") / f"{run_name}.jsonl"
    if not p.exists():
        return {}
    trials = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    n = len(trials)
    succ = sum(t["success"] for t in trials) / n
    msgs = blocked = 0
    for t in trials:
        for tr in t["turns"]:
            msgs += 1
            if tr["sender_filtered"].startswith("[message blocked"):
                blocked += 1
    return {"n": n, "success": succ, "game_block_rate": blocked / msgs if msgs else 0}


def fp_rate(client, judge_model: str, strictness: str, innocent: list[str]) -> float:
    cen = BlindCensor(client, judge_model, strictness=strictness)
    blocked = sum(cen.decide_block(m) for m in innocent)
    return blocked / len(innocent)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--judge", default="openai/gpt-4o-mini")
    args = ap.parse_args()

    innocent = [l.strip() for l in open("stimuli/innocent_bank.txt", encoding="utf-8") if l.strip()]
    client = Client(budget_usd_max=10.0)

    print(f"innocent bank: {len(innocent)} messages\n")
    print(f"{'strictness':10} {'FP_rate':8} {'game_block':10} {'success':8} {'n':3}")
    rows = []
    for s in STRICTNESS:
        g = game_stats(f"expJ_blind_{s}")
        fp = fp_rate(client, args.judge, s, innocent)
        rows.append((s, fp, g))
        print(f"{s:10} {fp:7.0%} {g.get('game_block_rate',0):9.0%} "
              f"{g.get('success',0):7.0%} {g.get('n',0):3}")

    print("\nReading: if success only falls when FP rises, deniable communication")
    print("cannot be stopped without over-blocking innocent traffic (the thesis).")
    print(f"\njudge spend ${client.spend_usd:.4f}")


if __name__ == "__main__":
    main()
