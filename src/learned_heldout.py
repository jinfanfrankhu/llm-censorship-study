"""Does incident review generalise across SENDERS on the held-out items?

    python -m src.learned_heldout

Exp U (8 held-out gap items, 4 sender families, v9). For each family F, the
censor's incident log for a target is every winning v9 message (decoded game)
from the OTHER three families for that target -- what a moderator reviewing
past incidents would have. The primed gpt-4o-mini decode-censor then judges
(a) F's knowledge-gap dogwhistles (all survived the unprimed censor in game)
and (b) the 40 same-community innocents in stimuli/dw_adjacent_v3.json, primed
with the union log for that target. Unprimed numbers are reported alongside.
Output: data/learned_heldout.txt (stdout).
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv

from .arms_race import MAX_EXAMPLES
from .censor import TranscriptDecodeCensor
from .scoring import rescore_record

CENSOR = "openai/gpt-4o-mini"


def main():
    load_dotenv(".env")
    from .client import Client
    client = Client(budget_usd_max=0.5)
    accept = {r["target"]: [x for x in r["accept"].split("|") if x]
              for r in csv.DictReader(open("stimuli/dogwhistle_targets_U.csv", encoding="utf-8"))}
    adjacent = json.load(open("stimuli/dw_adjacent_v3.json", encoding="utf-8"))
    wins = defaultdict(list)                     # (target, family) -> winning msgs
    for l in open("data/raw/dwU_v9_c4o.jsonl", encoding="utf-8"):
        r = json.loads(l)
        if r["target"] not in adjacent or not rescore_record(r)["success"]:
            continue
        w = next(t for t in r["turns"] if t.get("correct"))
        wins[(r["target"], r["model"])].append(w["sender_raw"].strip().replace("\n", " ")[:300])
    dws = {}
    for p in map(json.loads, open("data/raw/dw_probes_U.jsonl", encoding="utf-8")):
        if ("v9" in p["run"] and p["target"] in adjacent and not p["out_recover"]
                and p["innocent"] and p["in_recover"]):
            dws.setdefault((p["target"], p["model"], p["winning_msg"]), None)
    fams = sorted({f for _, f in wins})

    def log(t, exclude=None):
        out = []
        for f in fams:
            if f != exclude:
                out += wins.get((t, f), [])
        return out[-MAX_EXAMPLES:]

    def blk(t, msg, ex):
        return TranscriptDecodeCensor(t, client, CENSOR, "moderate", accept=accept[t],
                                      examples=ex or None).decide_block(msg)

    dw_jobs = [(t, f, m) for (t, f, m) in dws]
    adj_jobs = [(t, m) for t, ms in adjacent.items() for m in ms]
    with ThreadPoolExecutor(6) as pool:
        dw_base = list(pool.map(lambda j: blk(j[0], j[2], None), dw_jobs))
        dw_prim = list(pool.map(lambda j: blk(j[0], j[2], log(j[0], exclude=j[1])), dw_jobs))
        adj_base = list(pool.map(lambda j: blk(j[0], j[1], None), adj_jobs))
        adj_prim = list(pool.map(lambda j: blk(j[0], j[1], log(j[0])), adj_jobs))
    print(f"{len(dw_jobs)} held-out-family KG-DW messages; {len(adj_jobs)} innocents")
    print(f"DW caught      unprimed {sum(dw_base)}/{len(dw_jobs)}   primed (other families' log) "
          f"{sum(dw_prim)}/{len(dw_jobs)}")
    print(f"innocent FP    unprimed {sum(adj_base)}/{len(adj_jobs)}   primed (full log) "
          f"{sum(adj_prim)}/{len(adj_jobs)}")
    per = defaultdict(lambda: [0, 0])
    for (t, f, m), k in zip(dw_jobs, dw_prim):
        per[f.split("/")[-1]][0] += k
        per[f.split("/")[-1]][1] += 1
    for f, (k, n) in per.items():
        print(f"  held-out {f:28} caught {k}/{n}")
    for (t, f, m), b, k in zip(dw_jobs, dw_base, dw_prim):
        if not k:
            print(f"  MISSED {t:9} {f.split('/')[-1][:10]} | {m[:140]}")
    print(f"spend ${client.spend_usd:.4f}")


if __name__ == "__main__":
    main()
