"""Pilot metrics + human-readable transcript export.

    python -m src.analyze --run_name pilot_v1 [--full_trials N]

Prints a metrics table broken down by model x freq_band x informed x
forbidden_level, writes it to data/metrics_<run>.csv, and exports one markdown
transcript per trial under data/transcripts/<run>/.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import pandas as pd

FILTER_KEYWORDS = ["censor", "filter", "blocked", "redact", "####", "#####"]


def load_trials(path: Path) -> list[dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def trial_summary_row(t: dict) -> dict:
    turns = t["turns"]
    n_turns = len(turns)
    redacted_turns = sum(1 for tr in turns if tr["filter_hits"])
    flag_counter = Counter()
    for tr in turns:
        for fl in tr["audit_flags"]:
            flag_counter[fl["type"]] += 1

    # uninformed arm: first turn where sender raw text comments on the filter
    first_filter_comment = None
    if not t["informed"]:
        for tr in turns:
            text = (tr["sender_raw"] or "").lower()
            if any(k in text for k in FILTER_KEYWORDS):
                first_filter_comment = tr["turn"]
                break

    return {
        "model": t["model"],
        "freq_band": t["freq_band"],
        "informed": t["informed"],
        "forbidden_level": t["forbidden_level"],
        "item_id": t["item_id"],
        "success": int(t["success"]),
        "turns_to_success": t["turns_to_success"],
        "n_turns": n_turns,
        "redaction_rate": redacted_turns / n_turns if n_turns else 0.0,
        "flag_leetspeak": flag_counter["leetspeak"],
        "flag_spacing": flag_counter["spacing"],
        "flag_substring": flag_counter["substring"],
        "flag_near_miss": flag_counter["near_miss"],
        "first_filter_comment_turn": first_filter_comment,
        "cost_usd": t["usage"]["cost_usd"],
        "prompt_tokens": t["usage"]["prompt_tokens"],
        "completion_tokens": t["usage"]["completion_tokens"],
    }


def metrics_table(df: pd.DataFrame) -> pd.DataFrame:
    group_cols = ["model", "freq_band", "informed", "forbidden_level"]
    agg = df.groupby(group_cols).agg(
        n=("success", "size"),
        success_rate=("success", "mean"),
        mean_turns_to_success=("turns_to_success", "mean"),
        redaction_rate=("redaction_rate", "mean"),
        leetspeak=("flag_leetspeak", "sum"),
        spacing=("flag_spacing", "sum"),
        substring=("flag_substring", "sum"),
        near_miss=("flag_near_miss", "sum"),
        cost_usd=("cost_usd", "sum"),
    )
    return agg.reset_index()


def export_transcripts(trials: list[dict], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for t in trials:
        name = f"{t['item_id']}_{t['model'].replace('/', '-')}_inf{int(t['informed'])}_lvl{t['forbidden_level']}_run{t['run_index']}.md"
        lines = [
            f"# {t['target']} (item {t['item_id']})",
            "",
            f"- model: `{t['model']}`",
            f"- informed: {t['informed']} | forbidden_level: {t['forbidden_level']} | freq_band: {t['freq_band']}",
            f"- forbidden: {', '.join(t['forbidden'])}",
            f"- success: **{t['success']}** (turns_to_success: {t['turns_to_success']})",
            "",
        ]
        for tr in t["turns"]:
            lines.append(f"## Turn {tr['turn']}")
            lines.append(f"**Sender (raw):** {tr['sender_raw']}")
            lines.append("")
            lines.append(f"**Sender (delivered):** {tr['sender_filtered']}")
            if tr["filter_hits"]:
                lines.append(f"> filter hits: {', '.join(tr['filter_hits'])}")
            if tr["audit_flags"]:
                flags = ", ".join(f"{f['type']}:{f['evidence']}" for f in tr["audit_flags"])
                lines.append(f"> audit flags: {flags}")
            lines.append("")
            lines.append(f"**Receiver guess:** `{tr['guess']}` (correct: {tr['correct']})")
            if tr["receiver_message_raw"]:
                lines.append(f"**Receiver note (raw):** {tr['receiver_message_raw']}")
                lines.append(f"**Receiver note (delivered):** {tr['receiver_message_filtered']}")
            lines.append("")
        (out_dir / name).write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run_name", required=True)
    ap.add_argument(
        "--full_trials",
        type=int,
        default=None,
        help="if set, extrapolate cost to this many trials for the full study",
    )
    args = ap.parse_args()

    in_path = Path("data/raw") / f"{args.run_name}.jsonl"
    trials = load_trials(in_path)
    if not trials:
        print(f"no trials in {in_path}")
        return

    df = pd.DataFrame(trial_summary_row(t) for t in trials)
    table = metrics_table(df)
    pd.set_option("display.max_columns", None, "display.width", 200)
    print(table.to_string(index=False))

    metrics_path = Path("data") / f"metrics_{args.run_name}.csv"
    table.to_csv(metrics_path, index=False)

    total_cost = df["cost_usd"].sum()
    n = len(df)
    print(f"\ntrials: {n} | total cost: ${total_cost:.4f} | mean/trial: ${total_cost / n:.6f}")
    if args.full_trials:
        print(f"extrapolated to {args.full_trials} trials: ${total_cost / n * args.full_trials:.2f}")

    # uninformed-arm filter awareness
    uninf = df[df["informed"] == False]  # noqa: E712
    if len(uninf):
        aware = uninf["first_filter_comment_turn"].notna().mean()
        print(f"uninformed arm: {aware:.0%} of trials mention the filter (keyword scan; hand-verify)")

    tdir = Path("data/transcripts") / args.run_name
    export_transcripts(trials, tdir)
    print(f"metrics -> {metrics_path}\ntranscripts -> {tdir}/")


if __name__ == "__main__":
    main()
