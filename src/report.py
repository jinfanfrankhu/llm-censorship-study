"""Richer analysis across one or more runs: metrics, adaptation, filter
awareness, strategy signals, and cross-run comparison.

    python -m src.report --runs main_v2                 # one run, full report
    python -m src.report --runs pilot_v1 expA_v2        # compare runs

Reads data/raw/<run>.jsonl. Prints to stdout (capture into FINDINGS.md).
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd

from .analyze import FILTER_KEYWORDS, load_trials, trial_summary_row

# Words that signal the sender is giving up / stalling rather than re-encoding.
GIVEUP_PAT = re.compile(r"\b(i can'?t|cannot|not allowed|unable to|give up|i'?m stuck|no idea)\b", re.I)
NEGATION_PAT = re.compile(r"^\s*(no\b|not\b|it'?s not|that'?s not)", re.I)


def df_for(run: str) -> pd.DataFrame:
    trials = load_trials(Path("data/raw") / f"{run}.jsonl")
    df = pd.DataFrame(trial_summary_row(t) for t in trials)
    df["run"] = run
    return df


def metrics_by_cell(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["run", "model", "freq_band", "informed", "forbidden_level"])
    return g.agg(
        n=("success", "size"),
        success=("success", "mean"),
        turns=("turns_to_success", "mean"),
        redaction=("redaction_rate", "mean"),
        leet=("flag_leetspeak", "sum"),
        space=("flag_spacing", "sum"),
        substr=("flag_substring", "sum"),
        near=("flag_near_miss", "sum"),
        cost=("cost_usd", "sum"),
    ).reset_index()


def adaptation_table(runs: list[str]) -> pd.DataFrame:
    """Redaction rate by turn index per (run, model) -- do senders adapt?"""
    hit = defaultdict(int)
    tot = defaultdict(int)
    neg = defaultdict(int)
    for run in runs:
        for t in load_trials(Path("data/raw") / f"{run}.jsonl"):
            m = t["model"].split("/")[-1]
            for tr in t["turns"]:
                key = (run, m, tr["turn"])
                tot[key] += 1
                if tr["filter_hits"]:
                    hit[key] += 1
                if NEGATION_PAT.search(tr["sender_raw"] or ""):
                    neg[key] += 1
    rows = []
    for key in sorted(tot):
        run, m, turn = key
        rows.append({
            "run": run, "model": m, "turn": turn, "n": tot[key],
            "redaction": round(hit[key] / tot[key], 3),
            "negation": round(neg[key] / tot[key], 3),
        })
    return pd.DataFrame(rows)


def filter_awareness(runs: list[str]) -> pd.DataFrame:
    """Fraction of trials whose sender text ever names the filter, by condition."""
    rows = []
    for run in runs:
        agg = defaultdict(lambda: [0, 0])  # (model, informed) -> [aware, total]
        for t in load_trials(Path("data/raw") / f"{run}.jsonl"):
            m = t["model"].split("/")[-1]
            aware = any(
                any(k in (tr["sender_raw"] or "").lower() for k in FILTER_KEYWORDS)
                for tr in t["turns"]
            )
            cell = agg[(m, t["informed"])]
            cell[1] += 1
            cell[0] += int(aware)
        for (m, informed), (a, n) in sorted(agg.items()):
            rows.append({"run": run, "model": m, "informed": informed,
                         "n": n, "mentions_filter": round(a / n, 3)})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", nargs="+", required=True)
    args = ap.parse_args()
    pd.set_option("display.max_rows", None, "display.max_columns", None, "display.width", 240)

    dfs = []
    for r in args.runs:
        p = Path("data/raw") / f"{r}.jsonl"
        if not p.exists():
            print(f"[skip] {p} missing")
            continue
        dfs.append(df_for(r))
    if not dfs:
        return
    df = pd.concat(dfs, ignore_index=True)

    print("=" * 100)
    print("METRICS BY CELL (run x model x freq_band x informed x level)")
    print("=" * 100)
    print(metrics_by_cell(df).to_string(index=False))

    print("\n" + "=" * 100)
    print("MODEL SUMMARY (collapsed over targets/levels/runs)")
    print("=" * 100)
    msum = df.groupby(["run", "model"]).agg(
        n=("success", "size"), success=("success", "mean"),
        redaction=("redaction_rate", "mean"),
        leet=("flag_leetspeak", "sum"), space=("flag_spacing", "sum"),
        substr=("flag_substring", "sum"), near=("flag_near_miss", "sum"),
        cost=("cost_usd", "sum"),
    ).reset_index()
    print(msum.to_string(index=False))

    print("\n" + "=" * 100)
    print("ADAPTATION: redaction & negation rate by turn")
    print("=" * 100)
    print(adaptation_table(args.runs).to_string(index=False))

    print("\n" + "=" * 100)
    print("FILTER AWARENESS: fraction of trials where sender names the filter")
    print("=" * 100)
    print(filter_awareness(args.runs).to_string(index=False))

    print(f"\nTOTAL trials: {len(df)} | total cost: ${df['cost_usd'].sum():.4f}")


if __name__ == "__main__":
    main()
