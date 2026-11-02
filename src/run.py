"""CLI: run all trials from a config.

    python -m src.run --config config/pilot.yaml [--dry-run] [--limit N]

Resumable: trials already present in the output JSONL are skipped, so a crashed
or budget-halted run can be restarted without re-calling the API.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import yaml
from tqdm import tqdm

from .client import BudgetExceeded, Client
from .game import run_trial
from .mock import MockClient


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_stimuli(path: str) -> list[dict]:
    items = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            forbidden = [w.strip() for w in row["forbidden"].split("|") if w.strip()]
            items.append(
                {
                    "item_id": row["item_id"],
                    "target": row["target"].strip(),
                    "freq_band": row.get("freq_band", "").strip(),
                    "zipf": float(row["zipf"]) if row.get("zipf") else None,
                    "forbidden": forbidden,
                }
            )
    return items


def existing_keys(out_path: Path) -> set[tuple]:
    keys = set()
    if not out_path.exists():
        return keys
    with open(out_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            keys.add((r["item_id"], r["model"], r["informed"], r["forbidden_level"], r["run_index"]))
    return keys


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True)
    ap.add_argument("--stimuli", default="stimuli/targets.csv")
    ap.add_argument("--dry-run", action="store_true", help="use the mock model (no API cost)")
    ap.add_argument("--limit", type=int, default=None, help="cap number of NEW trials this run")
    args = ap.parse_args()

    cfg = load_config(args.config)
    items = load_stimuli(args.stimuli)

    run_name = cfg["run_name"]
    models = cfg["models"]
    informed_conditions = cfg["conditions"]["informed"]
    forbidden_levels = cfg["filter"]["forbidden_levels"]
    redaction = cfg["filter"]["redaction"]
    max_turns = cfg["max_turns"]
    runs_per_item = cfg["runs_per_item"]
    sampling = cfg["sampling"]
    seed_base = cfg["seed_base"]
    budget = cfg["budget_usd_max"]
    prompt_version = cfg.get("prompt_version", "v2")

    out_path = Path("data/raw") / f"{run_name}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = existing_keys(out_path)

    client = MockClient(budget_usd_max=budget) if args.dry_run else Client(budget_usd_max=budget)

    # Warn once per item whose ranked list is shorter than the largest level.
    max_level = max(forbidden_levels)
    for item in items:
        if max_level > len(item["forbidden"]):
            print(
                f"[warn] item {item['item_id']} ({item['target']}) has only "
                f"{len(item['forbidden'])} forbidden words; levels above that use all of them."
            )

    # Build the full trial grid.
    grid = []
    for item in items:
        for model in models:
            for informed in informed_conditions:
                for level in forbidden_levels:
                    for run_index in range(runs_per_item):
                        grid.append((item, model, informed, level, run_index))

    todo = [g for g in grid if (g[0]["item_id"], g[1], g[2], g[3], g[4]) not in done]
    if args.limit is not None:
        todo = todo[: args.limit]

    print(f"{len(grid)} trials total | {len(done)} already done | running {len(todo)} now")

    written = 0
    try:
        with open(out_path, "a", encoding="utf-8") as out:
            for item, model, informed, level, run_index in tqdm(todo, desc=run_name):
                record = run_trial(
                    client,
                    item=item,
                    model=model,
                    informed=informed,
                    forbidden_level=level,
                    run_index=run_index,
                    max_turns=max_turns,
                    redaction=redaction,
                    sampling=sampling,
                    seed=seed_base + run_index,
                    prompt_version=prompt_version,
                )
                record["run_name"] = run_name
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                out.flush()
                written += 1
    except BudgetExceeded as e:
        print(f"\n[budget] stopped: {e}. {written} trials written; rerun to resume.")
        return

    spend = getattr(client, "spend_usd", 0.0)
    print(f"done. wrote {written} trials. approx spend ${spend:.4f}")


if __name__ == "__main__":
    main()
