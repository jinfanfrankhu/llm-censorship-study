"""Folk-theory-of-evasion analysis: does a model's surface-trick reach rate
predict its FAILURE against a semantic (topic-aware) censor?

Combines:
- game outcomes per model (from the expN run jsonls): success rate, block rate;
- strategy labels per message (from src.strategy output): surface / semantic / meta.

Headline: across models, correlate surface-trick rate with success rate. The
folk-theory prediction (from Exp M) is a NEGATIVE correlation -- models that reach
for form-tricks (orthographic/wordplay) do worse, because those are transparent to
a semantic censor; the models that stumble into ambiguous description do better.

    python -m src.analyze_folk \
        --runs expN_folk_lenient expN_folk_moderate expN_folk_strict \
        --labels data/strategy_expN_folk_lenient.jsonl ...
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def _short(model: str) -> str:
    return model.split("/")[-1]


def game_by_model(run_names: list[str]) -> dict:
    """model -> {n_trials, success, n_msgs, blocked}"""
    agg = defaultdict(lambda: {"n_trials": 0, "success": 0, "n_msgs": 0, "blocked": 0})
    for run in run_names:
        p = Path("data/raw") / f"{run}.jsonl"
        if not p.exists():
            continue
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            m = _short(r["model"])
            a = agg[m]
            a["n_trials"] += 1
            a["success"] += int(bool(r["success"]))
            for t in r["turns"]:
                a["n_msgs"] += 1
                if t["sender_filtered"].startswith("[message blocked"):
                    a["blocked"] += 1
    return agg


def strategy_by_model(label_paths: list[str]) -> dict:
    """model -> {surface, semantic, meta, total}"""
    agg = defaultdict(lambda: {"surface": 0, "semantic": 0, "meta": 0, "total": 0})
    for lp in label_paths:
        p = Path(lp)
        if not p.exists():
            print(f"[skip] {p} missing")
            continue
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            a = agg[_short(r["model"])]
            a[r["label"]] += 1
            a["total"] += 1
    return agg


def pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return None
    return cov / (vx ** 0.5 * vy ** 0.5)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--labels", nargs="+", required=True)
    args = ap.parse_args()

    game = game_by_model(args.runs)
    strat = strategy_by_model(args.labels)

    models = sorted(set(game) | set(strat))
    print(f"{'model':40} {'succ':>5} {'blk':>5} {'surf%':>6} {'sem%':>6} {'meta%':>6} {'N':>5}")
    rows = []
    for m in models:
        g = game.get(m, {})
        s = strat.get(m, {})
        succ = g["success"] / g["n_trials"] if g.get("n_trials") else None
        blk = g["blocked"] / g["n_msgs"] if g.get("n_msgs") else None
        tot = s.get("total", 0)
        surf = s.get("surface", 0) / tot if tot else None
        sem = s.get("semantic", 0) / tot if tot else None
        meta = s.get("meta", 0) / tot if tot else None
        print(f"{m:40} "
              f"{(f'{succ:.0%}' if succ is not None else '-'):>5} "
              f"{(f'{blk:.0%}' if blk is not None else '-'):>5} "
              f"{(f'{surf:.0%}' if surf is not None else '-'):>6} "
              f"{(f'{sem:.0%}' if sem is not None else '-'):>6} "
              f"{(f'{meta:.0%}' if meta is not None else '-'):>6} "
              f"{tot:>5}")
        if succ is not None and surf is not None:
            rows.append((m, surf, succ))

    print("\n=== folk-theory correlation (across models) ===")
    if len(rows) >= 3:
        xs = [r[1] for r in rows]
        ys = [r[2] for r in rows]
        r = pearson(xs, ys)
        print(f"Pearson(surface_trick_rate, success_rate) = "
              f"{r:.2f}  (n={len(rows)} models)" if r is not None else "undefined")
        print("prediction: NEGATIVE (more surface-tricks -> lower success vs a semantic censor)")
    else:
        print(f"need >=3 models with both metrics; have {len(rows)}")


if __name__ == "__main__":
    main()
