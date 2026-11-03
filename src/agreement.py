"""Human vs judge agreement on the blind dogwhistle validation sheet.

    python -m src.agreement

Reads ratings/dw_validation.csv (human columns filled) and the hidden key
ratings/dw_validation_key.jsonl, and reports, per judge:
  decode     : human cold guess correct  vs  censor model's cold guess correct
  plausible  : human YES/NO              vs  plausibility judge (plausible_raw)
  innocent   : human plausible AND human gist does not name the target
               vs  the pipeline's `innocent` flag (plausible & no meta-leak &
               gist does not name target)
  triple     : D & not-decoded & innocent, human labels vs pipeline labels
Cohen's kappa + raw agreement + the confusion counts.
"""
from __future__ import annotations

import csv
import json


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return po, (po - pe) / (1 - pe) if pe < 1 else float("nan")


def conf(a, b):
    return {"HY_JY": sum(x and y for x, y in zip(a, b)),
            "HY_JN": sum(x and not y for x, y in zip(a, b)),
            "HN_JY": sum(not x and y for x, y in zip(a, b)),
            "HN_JN": sum(not x and not y for x, y in zip(a, b))}


def main(sheet="ratings/dw_validation.csv", key="ratings/dw_validation_key.jsonl"):
    rows = {int(r["idx"]): r for r in csv.DictReader(open(sheet, encoding="utf-8-sig"))}
    keys = {k["idx"]: k for k in map(json.loads, open(key, encoding="utf-8"))}
    accept = {}
    for r in csv.DictReader(open("stimuli/dogwhistle_targets.csv", encoding="utf-8")):
        accept[r["target"]] = [x.lower() for x in (r["accept"] or r["target"]).split("|")]
    H = {"decode": [], "plausible": [], "innocent": [], "triple": []}
    J = {"decode": [], "plausible": [], "innocent": [], "triple": []}
    for i in sorted(rows):
        r, k = rows[i], keys[i]
        acc = accept[k["target"]]
        hg = r["HUMAN_guess_secret_word_from_transcript"].strip().lower()
        hdec = any(a in hg for a in acc)
        hpl = r["HUMAN_plausible_ordinary_reading(YES/NO)"].strip().lower().startswith("y")
        gist = r["HUMAN_innocent_gist"].strip().lower()
        hinn = hpl and not any(a in gist for a in acc)
        jpl = str(k.get("plausible_raw", "")).strip().upper().startswith("YES")
        H["decode"].append(hdec); J["decode"].append(k["out_recover"])
        H["plausible"].append(hpl); J["plausible"].append(jpl)
        H["innocent"].append(hinn); J["innocent"].append(k["innocent"])
        H["triple"].append((not hdec) and hinn)
        J["triple"].append((not k["out_recover"]) and k["innocent"])
    n = len(rows)
    print(f"n={n} (all winning messages, i.e. D=1)\n")
    for m in H:
        po, kp = kappa(H[m], J[m])
        print(f"{m:10} human+ {sum(H[m]):2}/{n}  judge+ {sum(J[m]):2}/{n}  "
              f"agree {po:.2f}  kappa {kp:+.2f}  {conf(H[m], J[m])}")


if __name__ == "__main__":
    main()
