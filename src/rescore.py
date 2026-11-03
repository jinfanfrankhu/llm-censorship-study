"""Recompute honest success for existing runs (offline, no API calls).

    python -m src.rescore [--runs A B ...]

Applies the referee-v2 rule (src/scoring.py): a win whose winning-turn clue was
fully blocked is a receiver-filler artifact and does not count. Dedupes by trial
key (keep first occurrence) per the orphan-python gotcha. Prints raw vs honest
success per run and per sender model.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from .scoring import rescore_record

KEY = ("item_id", "model", "receiver_model", "informed", "forbidden_level", "run_index")


def load_dedup(path: Path) -> list[dict]:
    seen, out = set(), []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        k = tuple(r.get(f, r.get("model")) for f in KEY)
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="*", default=None)
    ap.add_argument("--by_model", action="store_true")
    a = ap.parse_args()
    paths = ([Path("data/raw") / f"{r}.jsonl" for r in a.runs] if a.runs
             else sorted(Path("data/raw").glob("*.jsonl")))
    print(f"{'run':28} {'n':>5} {'raw':>6} {'honest':>7} {'voided':>7} {'%wins void':>10} {'lenient':>8}")
    for p in paths:
        recs = load_dedup(p)
        groups = defaultdict(list)
        for r in recs:
            groups[(p.stem, r["model"] if a.by_model else "")].append(rescore_record(r))
        for (run, m), sc in groups.items():
            n = len(sc); raw = sum(s["success_raw"] for s in sc)
            hon = sum(s["success"] for s in sc); vd = sum(s["voided"] for s in sc)
            len_ = sum(s["success_lenient"] for s in sc)
            label = run if not m else f"{run}|{m.split('/')[-1]}"
            print(f"{label[:28]:28} {n:5} {raw/n:6.1%} {hon/n:7.1%} {vd:7} "
                  f"{(vd/raw if raw else 0):10.0%} {len_/n:8.1%}")


if __name__ == "__main__":
    main()
