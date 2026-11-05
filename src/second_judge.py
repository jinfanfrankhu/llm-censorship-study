"""Second-family innocence judges (reviewer check on the single ORDINARY judge).

The innocence flag rests on one LLM judge (mistral-small, ORDINARY_SYS) validated
against one human rater. This script re-asks the same ORDINARY/CLUE question to
judges from other families and reports:

  A. agreement of every judge with the PI's human ratings on the validation
     sheets (ratings/dw_validation_PI_rated.csv, ratings/dw_validation2.csv);
  B. for every dogwhistle triple behind the headline (gpt-4o-mini decode-censor
     runs, gap items only), whether each second judge also calls the winning
     message ORDINARY, and the triple counts per prompt if innocence requires
     all judges to agree.

    python -m src.second_judge > data/second_judge.txt
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from dotenv import load_dotenv

from .analyze_dogwhistle import ORDINARY_SYS, OUTSIDER
from .client import Client

RAW = Path("data/raw")
CONTROLS = {"dw02", "dw22", "dw34", "dw41"}
HEADLINE_PROBES = ["dw_probes_R_meta5.jsonl", "dw_probes_S.jsonl", "dw_probes_U.jsonl",
                   "dw_probes_W.jsonl", "dw_probes_X.jsonl", "dw_probes_Zr.jsonl",
                   "dw_probes_Zf.jsonl", "dw_probes_Zs.jsonl", "dw_probes_Pa.jsonl",
                   "dw_probes_M.jsonl"]
JUDGES = ["openai/gpt-4.1-mini", "google/gemini-2.5-flash"]
SHEETS = [("ratings/dw_validation_PI_rated.csv", "ratings/dw_validation_PI_key.jsonl"),
          ("ratings/dw_validation2.csv", "ratings/dw_validation2_key.jsonl")]


def jl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def ask(client, model, msg):
    rec = client.chat(model, [{"role": "system", "content": ORDINARY_SYS},
                              {"role": "user", "content": msg}],
                      run_index=0, temperature=0.0, max_tokens=12)
    out = (rec.get("content") or "").strip().upper()
    if not out:
        rec = client.chat(model, [{"role": "system", "content": ORDINARY_SYS},
                                  {"role": "user", "content": msg}],
                          run_index=0, temperature=0.0, max_tokens=2000)
        out = (rec.get("content") or "").strip().upper()
    return "ORDINARY" in out


def kappa(pairs):
    n = len(pairs)
    if not n:
        return float("nan")
    po = sum(a == b for a, b in pairs) / n
    pa = sum(a for a, _ in pairs) / n
    pb = sum(b for _, b in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def part_a(client, judges):
    print("A. Agreement with the PI's human ratings (ORDINARY = human YES)")
    rows = []
    for sheet, key in SHEETS:
        if not Path(sheet).exists():
            continue
        keyed = {k["idx"]: k for k in jl(key)}
        with open(sheet, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                h = (r.get("HUMAN_plausible_ordinary_reading(YES/NO)") or "").strip().upper()
                if h not in ("YES", "NO"):
                    continue
                k = keyed.get(int(r["idx"]))
                if k is None:
                    continue
                rows.append((h == "YES", k["winning_msg"]))
    print(f"   {len(rows)} human-rated messages; human YES on {sum(h for h, _ in rows)}")
    for j in [OUTSIDER] + judges:
        pairs = [(h, ask(client, j, m)) for h, m in rows]
        called = [h for h, o in pairs if o]
        prec = sum(called) / len(called) if called else float("nan")
        print(f"   {j:44} ORDINARY on {len(called):3}; precision vs human {prec:.2f} "
              f"({sum(called)}/{len(called)}); kappa {kappa(pairs):.2f}")


def part_b(client, judges):
    print("\nB. Headline triples (gpt-4o-mini decode-censor runs, gap items) re-judged")
    seen = {}
    for pf in HEADLINE_PROBES:
        f = RAW / pf
        if not f.exists():
            continue
        for p in jl(f):
            if not p["run"].endswith("_c4o") or p["item_id"] in CONTROLS:
                continue
            seen[(p["run"], p["item_id"], p["model"], p["run_index"])] = p
    triples = [p for p in seen.values() if not p["out_recover"] and p["innocent"]]
    print(f"   {len(triples)} triples from {len(seen)} probed successes")
    agree = Counter()
    by_pv = defaultdict(Counter)
    for p in triples:
        votes = [ask(client, j, p["winning_msg"]) for j in judges]
        for j, v in zip(judges, votes):
            agree[j] += v
        by_pv[p["prompt_version"]]["triple"] += 1
        by_pv[p["prompt_version"]]["all_judges"] += all(votes)
        by_pv[p["prompt_version"]]["any_judge"] += any(votes)
        if not all(votes):
            print(f"   - split: {p['run']} {p['model'].split('/')[-1][:16]} {p['target']}: "
                  f"{[int(v) for v in votes]} | {p['winning_msg'][:140]!r}")
    for j in judges:
        print(f"   {j:44} also ORDINARY on {agree[j]}/{len(triples)} triples")
    print("   per prompt: triple (mistral) / kept if all second judges agree / kept if any")
    for pv in sorted(by_pv):
        c = by_pv[pv]
        print(f"   {pv:6} {c['triple']:4} {c['all_judges']:4} {c['any_judge']:4}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judges", nargs="+", default=JUDGES)
    ap.add_argument("--budget", type=float, default=1.0)
    a = ap.parse_args()
    load_dotenv(".env")
    client = Client(budget_usd_max=a.budget)
    part_a(client, a.judges)
    part_b(client, a.judges)
    print(f"\nspend ${client.spend_usd:.4f}")


if __name__ == "__main__":
    main()
