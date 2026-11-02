"""Compare human ratings to the judge on the two objective tasks.

Reads ratings/validation_sheet.csv (human) + ratings/ai_and_truth.csv (truth +
AI). Reports: decodability (human/AI vs true word), human-AI guess agreement,
and evasion-label agreement (3-way and binary) with Cohen's kappa.

    python -m src.validate_judge
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from .game import guess_is_correct, _normalize


def _first_word(s: str) -> str:
    toks = [t for t in _normalize(s or "").split() or [_normalize(s or "")] if t]
    return toks[0] if toks else ""


def _norm_level(s: str) -> str:
    s = (s or "").strip().lower()
    for lv in ("clear", "some", "normal"):
        if lv in s:
            return lv
    return ""


def cohen_kappa(a: list[str], b: list[str]) -> float:
    cats = sorted(set(a) | set(b))
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum((ca[c] / n) * (cb[c] / n) for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def main():
    human = {r["id"]: r for r in csv.DictReader(open("ratings/validation_sheet.csv", encoding="utf-8"))}
    truth = {r["id"]: r for r in csv.DictReader(open("ratings/ai_and_truth.csv", encoding="utf-8"))}
    ids = sorted(human, key=int)

    # --- decodability (guess the hidden word) ---
    h_correct = ai_correct = h_ai_match = both = 0
    h_blank = 0
    for i in ids:
        tw = truth[i]["true_word"]
        hg = _first_word(human[i].get("your_guess", ""))
        ag = _first_word(truth[i]["ai_guess"])
        if not hg:
            h_blank += 1
        else:
            both += 1
            h_correct += guess_is_correct(hg, tw)
            h_ai_match += (hg == ag or guess_is_correct(hg, ag))
        ai_correct += guess_is_correct(ag, tw)

    n = len(ids)
    print(f"=== decodability (guess the hidden word), n={n} ===")
    print(f"  human correct : {h_correct}/{both} answered ({h_blank} left blank)")
    print(f"  AI correct    : {ai_correct}/{n}")
    print(f"  human==AI guess: {h_ai_match}/{both} (agree on the word, right or wrong)")

    # --- evasion label agreement ---
    hl, al = [], []
    for i in ids:
        h = _norm_level(human[i].get("evasion_normal_some_clear", ""))
        a = _norm_level(truth[i]["ai_evasion"])
        if h and a:
            hl.append(h); al.append(a)
    exact = sum(x == y for x, y in zip(hl, al)) / len(hl)
    kappa3 = cohen_kappa(hl, al)
    binm = {"normal": "no", "some": "yes", "clear": "yes"}
    hb = [binm[x] for x in hl]; ab = [binm[x] for x in al]
    binacc = sum(x == y for x, y in zip(hb, ab)) / len(hb)
    kappa2 = cohen_kappa(hb, ab)

    print(f"\n=== evasion label agreement, n={len(hl)} ===")
    print(f"  3-way (normal/some/clear): exact {exact:.0%}  kappa {kappa3:.2f}")
    print(f"  binary (evasive y/n)     : exact {binacc:.0%}  kappa {kappa2:.2f}")
    print("\n  confusion (rows=human, cols=AI):")
    cats = ["normal", "some", "clear"]
    print("          " + "  ".join(f"{c:>6}" for c in cats))
    for hc in cats:
        row = [sum(1 for x, y in zip(hl, al) if x == hc and y == ac) for ac in cats]
        print(f"  {hc:>7} " + "  ".join(f"{v:>6}" for v in row))


if __name__ == "__main__":
    main()
