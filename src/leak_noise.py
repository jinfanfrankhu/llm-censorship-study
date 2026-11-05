"""How much random blocking does a censor need to close the block side channel?

    python -m src.leak_noise > data/leak_noise.txt

Offline, from the Exp PB replies and decoder judgments (no API calls). A noisy
censor blocks every reply its decode rule blocks, plus each other reply with
probability r, and announces all blocks alike. For an ideal sender that reads
a block as 'knows' and otherwise uses the decoder's judgment of the text, the
expected paired accuracy for a T-vs-U or T-vs-R pair with censor decisions
(ca, cb) is

    P(neither shown blocked) * decoder accuracy on the raw pair
  + P(only the target-holder shown blocked) * 1
  + P(both shown blocked) * 0.5

Collateral is the share of replies the censor's own rule let through that are
now blocked anyway (= r), and the resulting block rate for receivers who do not
know (U). The natural-game likelihood ratio of a block (Exp TB 'read' games:
45% of knowing replies blocked vs 16% of non-knowing) is shown for comparison.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

RAW = Path("data/raw")
RATES = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
K_NAT, N_NAT = 0.45, 0.16  # P(block | knows), P(block | not), Exp TB natural games


def jl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def main():
    reps = jl(RAW / "ackPB_replies.jsonl")
    dec = [x for x in jl(RAW / "ackPB_decode.jsonl") if x["chosen"] and x["view"] == "raw"]
    acc = defaultdict(list)
    flags = {}
    for x in dec:
        k = (tuple(x["key"]), x["pair"])
        acc[k].append(x["correct"])
        flags[k] = (x["blocked_a"], x["blocked_b"])
    u_block = sum(x["blocked"] for x in reps if x["cond"] == "U") / sum(x["cond"] == "U" for x in reps)
    t_block = sum(x["blocked"] for x in reps if x["cond"] == "T") / sum(x["cond"] == "T" for x in reps)
    print("Leak vs random blocking (ideal block-reading sender, Exp PB pairs)\n")
    print(f"{'r':>4} | {'T vs U':>6} {'T vs R':>6} | {'U blocked':>9} {'T blocked':>9} | natural-game LR of a block")
    for r in RATES:
        out = {}
        for pair in ("TU", "TR"):
            tot = n = 0.0
            for k, v in acc.items():
                if k[1] != pair:
                    continue
                ca, cb = flags[k]
                pa = 1.0 if ca else r
                pb = 1.0 if cb else r
                d = sum(v) / len(v)
                e = (1 - pa) * (1 - pb) * d + pa * (1 - pb) * 1.0 + pa * pb * 0.5
                tot += e
                n += 1
            out[pair] = tot / n
        lr = (K_NAT + (1 - K_NAT) * r) / (N_NAT + (1 - N_NAT) * r)
        print(f"{r:4.1f} | {out['TU']:6.0%} {out['TR']:6.0%} | "
              f"{u_block + (1 - u_block) * r:9.0%} {t_block + (1 - t_block) * r:9.0%} | {lr:4.2f}")
    print("\nr = share of replies the censor's rule let through that it blocks anyway.")
    print("T vs U / T vs R = expected paired accuracy of the ideal reader (50% = no leak).")


if __name__ == "__main__":
    main()
