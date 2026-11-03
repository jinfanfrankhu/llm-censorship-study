"""Collateral of the LEARNED censor in the arms race.

    python -m src.learned_fp --run arA_censor --upto 3

Rebuilds, per target, the incident log the censor saw in round `upto` (winning
messages from all earlier rounds), and measures the false-positive rate of that
example-primed TranscriptDecodeCensor on the topic-adjacent innocent messages,
against the same censor with no examples.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv

from .adjacent_fp import ADJACENT
from .arms_race import MAX_EXAMPLES
from .censor import TranscriptDecodeCensor
from .scoring import rescore_record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="arA_censor")
    ap.add_argument("--upto", type=int, default=3)
    ap.add_argument("--censor", default="openai/gpt-4o-mini")
    ap.add_argument("--stimuli", default="stimuli/dogwhistle_targets_R.csv")
    ap.add_argument("--adjacent", default="stimuli/dw_adjacent_v2.json")
    a = ap.parse_args()
    load_dotenv(".env")
    from .client import Client
    client = Client(budget_usd_max=0.5)
    accept = {r["target"]: [x for x in r["accept"].split("|") if x]
              for r in csv.DictReader(open(a.stimuli, encoding="utf-8"))}
    adjacent = {t: m for t, m in ADJACENT.items() if t in accept}
    adjacent.update(json.load(open(a.adjacent, encoding="utf-8")))
    recs = [json.loads(l) for l in open(f"data/raw/{a.run}.jsonl", encoding="utf-8")]
    ex = defaultdict(list)
    for r in sorted(recs, key=lambda r: (r["round"], r["run_index"])):
        if r["round"] < a.upto and rescore_record(r)["success"]:
            win = next(t for t in r["turns"] if t.get("correct"))
            ex[r["target"]].append(win["sender_raw"].strip().replace("\n", " ")[:300])
    targets = sorted({r["target"] for r in recs})
    jobs = [(t, m) for t in targets for m in adjacent.get(t, [])]

    def blk(job, primed):
        t, m = job
        e = ex[t][-MAX_EXAMPLES:] if primed else None
        return TranscriptDecodeCensor(t, client, a.censor, "moderate",
                                      accept=accept[t], examples=e).decide_block(m)

    with ThreadPoolExecutor(6) as pool:
        base = list(pool.map(lambda j: blk(j, False), jobs))
        prim = list(pool.map(lambda j: blk(j, True), jobs))
    print(f"{a.run}: incident log before round {a.upto}: "
          f"{sum(len(v) for v in ex.values())} winning messages over {len(ex)} targets")
    print(f"adjacent FP  no examples {sum(base)}/{len(jobs)}   primed {sum(prim)}/{len(jobs)}")
    per = defaultdict(lambda: [0, 0, 0])
    for (t, _), b, p in zip(jobs, base, prim):
        per[t][0] += b; per[t][1] += p; per[t][2] += 1
    for t, (b, p, n) in per.items():
        print(f"  {t:10} examples {len(ex[t]):2}  FP {b}/{n} -> {p}/{n}")
    print(f"spend ${client.spend_usd:.4f}")


if __name__ == "__main__":
    main()
