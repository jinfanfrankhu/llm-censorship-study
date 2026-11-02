"""Deniability-frontier pilot: score existing sender messages for decodability
vs suspicion, to see whether evasion/permission actually buys deniability.

    python -m src.frontier --runs main_v2 expE_permission expH_onset_v3 \
        --judge openai/gpt-4o-mini --sample 180

For each sampled sender turn we record:
- D  : decodable? (did the receiver guess correctly that turn)
- St : topic-aware suspicion 0-10 (censor that knows the word)
- Sb : blind suspicion 0-10 (fresh monitor, no topic)
- disguise: did the turn carry a real leetspeak/spacing audit flag

Then aggregate by prompt_version and by disguise, to test:
  H1 disguise lowers St (hides from a topic-aware censor)?   -> predicted NO
  H2 disguise raises Sb (looks conspicuous when read cold)?  -> predicted YES
i.e. orthographic evasion is both detectable AND conspicuous; real deniability
needs semantic subtlety.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from .client import Client
from .suspicion import score


def load_messages(runs: list[str]) -> list[dict]:
    rows = []
    for run in runs:
        p = Path("data/raw") / f"{run}.jsonl"
        if not p.exists():
            print(f"[skip] {p} missing")
            continue
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            pv = r.get("prompt_version", "?")
            model = r["model"].split("/")[-1]
            for t in r["turns"]:
                raw = t.get("sender_raw") or ""
                if not raw.strip():
                    continue
                disguise = any(f["type"] in ("leetspeak", "spacing") for f in t["audit_flags"])
                rows.append({
                    "run": run, "prompt_version": pv, "model": model,
                    "target": r["target"], "turn": t["turn"],
                    "D": int(bool(t["correct"])), "disguise": disguise,
                    "message": raw,
                })
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--judge", default="openai/gpt-4o-mini")
    ap.add_argument("--sample", type=int, default=180)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rows = load_messages(args.runs)
    random.Random(args.seed).shuffle(rows)

    # Oversample disguise turns (they're rare) so the contrast is estimable.
    disg = [r for r in rows if r["disguise"]]
    plain = [r for r in rows if not r["disguise"]]
    keep = disg[: args.sample // 2] + plain[: args.sample - len(disg[: args.sample // 2])]
    print(f"{len(rows)} messages available; scoring {len(keep)} "
          f"({len([r for r in keep if r['disguise']])} disguise, "
          f"{len([r for r in keep if not r['disguise']])} plain)")

    client = Client(budget_usd_max=10.0)
    for i, r in enumerate(keep, 1):
        r["St"] = score(client, args.judge, r["message"], r["target"], "topic")
        r["Sb"] = score(client, args.judge, r["message"], r["target"], "blind")
        if i % 25 == 0:
            print(f"  scored {i}/{len(keep)} (spend ${client.spend_usd:.4f})")

    out = Path("data") / f"frontier_{'_'.join(args.runs)[:40]}.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for r in keep:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def agg(subset, label):
        n = len(subset)
        if not n:
            return
        D = sum(r["D"] for r in subset) / n
        St = sum(r["St"] for r in subset if r["St"] is not None) / n
        Sb = sum(r["Sb"] for r in subset if r["Sb"] is not None) / n
        print(f"  {label:28} n={n:3}  D={D:.2f}  St(topic)={St:.2f}  Sb(blind)={Sb:.2f}")

    print("\n=== by disguise ===")
    agg([r for r in keep if r["disguise"]], "disguise (leet/space)")
    agg([r for r in keep if not r["disguise"]], "plain")

    print("\n=== by prompt_version ===")
    for pv in sorted({r["prompt_version"] for r in keep}):
        agg([r for r in keep if r["prompt_version"] == pv], f"prompt {pv}")

    print("\n=== decodable messages only (D=1): what's their suspicion? ===")
    agg([r for r in keep if r["D"] and r["disguise"]], "D=1 & disguise")
    agg([r for r in keep if r["D"] and not r["disguise"]], "D=1 & plain")
    print(f"\nscored data -> {out} | total judge spend ${client.spend_usd:.4f}")


if __name__ == "__main__":
    main()
