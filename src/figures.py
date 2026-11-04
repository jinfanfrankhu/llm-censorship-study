"""Paper figures (draft). Numbers are copied from the analysis outputs named
next to each block; re-run those analyses and update here if they change.

    python -m src.figures            # writes figures/*.pdf and *.png
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

OUT = Path("figures")
# Validated categorical palette (dataviz reference instance, slots 1-3, light).
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.size": 8, "axes.edgecolor": INK2, "axes.labelcolor": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.axisbelow": True, "legend.frameon": False,
    "pdf.fonttype": 42,
})


def wilson(k, n, z=1.96):
    if n == 0:
        return 0, 0, 0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0, c - h), min(1, c + h)


def fig_propensity():
    """F2. Dogwhistle triples per trial vs gpt-4o-mini decode-censor, gap items.
    Source: data/dwS_analysis.txt (dwR_*_c4o 6 runs/item; dwS_*_c4o 3 runs)."""
    fam = [("llama-3.3-70b", 0, 72, 9, 72), ("deepseek-chat", 0, 72, 19, 72),
           ("qwen-2.5-72b", 0, 36, 5, 36), ("gemma-3-27b", 1, 36, 3, 36)]
    fig, ax = plt.subplots(figsize=(3.3, 2.2))
    w = 0.36
    for i, (name, k0, n0, k1, n1) in enumerate(fam):
        for off, k, n, col, lab in ((-w / 2, k0, n0, ORANGE, "default (v8n)"),
                                    (w / 2, k1, n1, BLUE, "innocence named (v9)")):
            p, lo, hi = wilson(k, n)
            ax.bar(i + off, p, w * 0.92, color=col, label=lab if i == 0 else None)
            ax.errorbar(i + off, p, yerr=[[p - lo], [hi - p]], color=INK2,
                        lw=0.8, capsize=2)
            ax.text(i + off, hi + 0.012, f"{k}/{n}", ha="center", va="bottom",
                    fontsize=6, color=INK2)
    ax.set_xticks(range(len(fam)), [f[0].replace("-", "-\n", 1) for f in fam], fontsize=6.5)
    ax.set_ylabel("dogwhistle triples / trial")
    ax.set_ylim(0, 0.55)
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper right", fontsize=6.5)
    return fig, "f2_propensity"


def fig_collateral():
    """F3. Catch rate on the 42 Exp R knowledge-gap dogwhistles vs false-positive
    rate on 70 topic-adjacent innocents. Source: FINDINGS_dogwhistle.md s8
    (src/hop_test.py) and s9 (src/learned_fp.py: primed censor, 19/21 held-out
    DW caught, 0/60 adjacent FP)."""
    pts = [("8B direct", 3 / 42, 0 / 70, ORANGE), ("8B CoT FP-aware", 19 / 42, 27 / 70, ORANGE),
           ("8B CoT zero-tol.", 33 / 42, 35 / 70, ORANGE),
           ("4o-mini direct", 24 / 42, 0 / 70, BLUE), ("4o-mini CoT FP-aware", 18 / 42, 3 / 70, BLUE),
           ("4o-mini CoT zero-tol.", 38 / 42, 28 / 70, BLUE),
           ("4o-mini + incident log", 19 / 21, 0 / 60, AQUA)]
    fig, ax = plt.subplots(figsize=(3.3, 2.4))
    for name, catch, fp, col in pts:
        ax.scatter(fp, catch, s=26, color=col, edgecolor="white", linewidth=1, zorder=3)
        dx, dy, ha = {"4o-mini CoT zero-tol.": (0, 0.05, "center"),
                      "8B CoT FP-aware": (0, -0.06, "center"),
                      "4o-mini CoT FP-aware": (0.015, -0.035, "left"),
                      "8B CoT zero-tol.": (-0.015, 0, "right")}.get(name, (0.015, 0, "left"))
        ax.annotate(name, (fp, catch), xytext=(fp + dx, catch + dy), fontsize=6,
                    color=INK2, va="center", ha=ha)
    ax.set_xlabel("false positives on innocent same-topic messages")
    ax.set_ylabel("dogwhistles caught")
    ax.set_xlim(-0.03, 0.6)
    ax.set_ylim(0, 1.0)
    return fig, "f3_collateral"


def _arms(prefix):
    """D (decoded games) and KG-DW per round per arm, from the analysis text."""
    path = Path(f"data/{prefix}_analysis.txt")
    if not path.exists():
        return None
    res = defaultdict(dict)
    for line in open(path, encoding="utf-8"):
        f = line.split()
        if not f or not f[0].startswith(prefix + "_"):
            continue
        _, cond, rnd = f[0].split("_")
        nums = [x for x in f[1:] if x.replace("%", "").isdigit()]
        # columns: n blk% D | outRec inRec meta innoc nat ctrl | TRIPLE KG-DW deep allu ctx vague
        n, D = int(nums[0]), int(nums[2])
        kg = int(nums[10])
        vague = int(nums[14])
        res[cond][int(rnd[1:])] = (n, D, kg, vague)
    return res


def fig_arms():
    """F4. Arms race per round: decoded games (D) and knowledge-gap dogwhistles.
    Source: data/arA_analysis.txt (seed 1) and data/arB_analysis.txt (seed 2)."""
    seeds = [s for s in (_arms("arA"), _arms("arB")) if s]
    cols = {"sender": BLUE, "censor": ORANGE, "both": AQUA}
    labels = {"sender": "sender learns", "censor": "censor learns", "both": "both learn"}
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.2), sharex=True)
    for j, (ax, idx, yl) in enumerate(zip(axes, (1, 2), ("decoded games / 72", "KG dogwhistles / 72"))):
        for cond in ("sender", "censor", "both"):
            for si, s in enumerate(seeds):
                if cond not in s:
                    continue
                rs = sorted(s[cond])
                ys = [s[cond][r][idx] for r in rs]
                ax.plot(rs, ys, color=cols[cond], lw=2 if si == 0 else 1.2,
                        ls="-" if si == 0 else "--", marker="o", ms=3.5,
                        label=f"{labels[cond]}" if si == 0 and j == 0 else None)
        ax.set_xticks(range(4))
        ax.set_xlabel("round")
        ax.set_ylabel(yl)
        ax.set_ylim(0, None)
    axes[0].legend(fontsize=6.5, loc="upper right")
    if len(seeds) > 1:
        axes[1].text(0.98, 0.95, "solid: seed 1, dashed: seed 2", transform=axes[1].transAxes,
                     ha="right", va="top", fontsize=6, color=INK2)
    fig.tight_layout()
    return fig, "f4_arms_race"


def fig_ack():
    """F5. Covert acknowledgment: forced-choice target identification from the
    receiver's reply alone. Source: data/expT_discrim_reply_only.txt (s11c)."""
    path = Path("data/raw/expT_discrim_reply_only.jsonl")
    agg = defaultdict(lambda: [0, 0])
    for l in open(path, encoding="utf-8"):
        x = json.loads(l)
        agg[x["kind"]][0] += x["correct"]
        agg[x["kind"]][1] += 1
    order = [("blocked_known_raw", "blocked by censor\n(receiver knew)", ORANGE),
             ("delivered_known", "delivered\n(receiver knew)", BLUE),
             ("delivered_unknown", "delivered\n(receiver wrong)", INK2)]
    fig, ax = plt.subplots(figsize=(3.3, 2.0))
    for i, (k, lab, col) in enumerate(order):
        hit, n = agg[k]
        p, lo, hi = wilson(hit, n)
        ax.bar(i, p, 0.6, color=col)
        ax.errorbar(i, p, yerr=[[p - lo], [hi - p]], color=INK2, lw=0.8, capsize=2)
        ax.text(i, hi + 0.02, f"{hit}/{n}", ha="center", fontsize=6, color=INK2)
    ax.axhline(0.2, color=INK2, lw=0.8, ls=":")
    ax.text(-0.45, 0.21, "chance", fontsize=6, color=INK2, ha="left", va="bottom")
    ax.set_xticks(range(3), [o[1] for o in order], fontsize=6.5)
    ax.set_ylabel("sender picks the target\n(5-way, reply alone)")
    ax.set_ylim(0, 1)
    ax.grid(axis="x", visible=False)
    return fig, "f5_ack_evidence"


def main():
    OUT.mkdir(exist_ok=True)
    for f in (fig_propensity, fig_collateral, fig_arms, fig_ack):
        fig, name = f()
        fig.tight_layout()
        fig.savefig(OUT / f"{name}.pdf")
        fig.savefig(OUT / f"{name}.png", dpi=200)
        plt.close(fig)
        print("wrote", name)


if __name__ == "__main__":
    main()
