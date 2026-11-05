"""Paper figures. Every number is read from the analysis outputs on disk.

    python -m src.figures            # writes figures/*.pdf and figures/*.png

Figures
  f1_schematic        the game
  f2_propensity       dogwhistles per family, default vs one-sentence prompt
  f3_ablation         which clause of the sentence matters
  f4_censor_ladder    what gets through as the censor gets stronger
  f5_items            per-word x per-family heatmap (v9)
  f6_collateral       catch vs collateral, one line per censor model
  f7_arms_race        four rounds, three arms, two seeds
  f8_ack_funnel       receiver knew -> sender noticed
  f9_ack_evidence     word-level evidence in replies (prior vs reply)
  f10_calibration     receivers' private confidence vs accuracy
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

OUT = Path("figures")
RAW = Path("data/raw")

# Palette (validated categorical slots; see dataviz reference palette).
BLUE, ORANGE, AQUA, YELLOW, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#6250d6"
INK, INK2, MUTED, GRID, PALE = "#1b1b1a", "#52514e", "#8c8b86", "#e6e5e1", "#f4f3f0"
DEFAULT_C, V9_C = "#b9b7b1", BLUE          # default prompt = neutral grey, v9 = blue

COL = 3.25     # one ACL column, inches
WIDE = 6.75    # full width

plt.rcParams.update({
    "font.family": "Arial", "font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.edgecolor": MUTED, "axes.linewidth": 0.6, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "xtick.major.width": 0.6,
    "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False,
    "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "legend.frameon": False, "pdf.fonttype": 42, "savefig.dpi": 300,
    "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.titlepad": 6,
})


# ----------------------------------------------------------------------------- helpers
def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


ROW = re.compile(r"^(\S+)\s+(\S*?)\s*(\d+)\s+(\d+)%\s+(\d+)\s+\|\s+([\d\s]+)\|\s+([\d\s]+)$")


def analysis(path):
    """Parse an analyze_dogwhistle table -> list of dicts."""
    out = []
    for line in open(path, encoding="utf-8"):
        m = ROW.match(line.rstrip())
        if not m:
            continue
        a = [int(x) for x in m.group(6).split()]
        b = [int(x) for x in m.group(7).split()]
        out.append(dict(run=m.group(1), model=m.group(2), n=int(m.group(3)),
                        blk=int(m.group(4)) / 100, D=int(m.group(5)), triple=b[0],
                        kg=b[1], vague=b[5]))
    return out


def jl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def style_axis(ax, grid="y"):
    if grid:
        ax.grid(axis=grid, color=GRID, lw=0.6)
    ax.tick_params(length=2.5)


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight", pad_inches=0.03)
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", pad_inches=0.03, dpi=220)
    plt.close(fig)
    print("wrote", name)


SHORT = {"llama-3.3-70b-": "Llama-3.3-70B", "deepseek-chat": "DeepSeek-V3",
         "qwen-2.5-72b-i": "Qwen-2.5-72B", "gemma-3-27b-it": "Gemma-3-27B",
         "gpt-4.1-mini": "GPT-4.1-mini", "gemini-2.5-fla": "Gemini-2.5-Flash-Lite",
         "claude-haiku-4": "Claude-Haiku-4.5", "deepseek-r1-05": "DeepSeek-R1",
         "qwen3-235b-a22": "Qwen3-235B-Thinking", "gpt-4.1": "GPT-4.1",
         "claude-sonnet-": "Claude-Sonnet-5.5"}


# ----------------------------------------------------------------------------- f1
def f1_schematic():
    fig, ax = plt.subplots(figsize=(WIDE, 1.75))
    ax.set_xlim(-0.1, 10.1)
    ax.set_ylim(0, 2.6)
    ax.axis("off")

    def box(x, w, title, body, col, fill="white"):
        ax.add_patch(FancyBboxPatch((x, 0.62), w, 1.2, boxstyle="round,pad=0.02,rounding_size=0.1",
                                    fc=fill, ec=col, lw=1.2))
        ax.text(x + w / 2, 1.62, title, ha="center", va="center", fontsize=8.5, weight="bold", color=INK)
        ax.text(x + w / 2, 1.12, body, ha="center", va="center", fontsize=6.6, color=INK2,
                linespacing=1.4)

    def arrow(x0, x1, y, ls="-", col=INK2):
        ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>", mutation_scale=8,
                                     lw=1.0, color=col, linestyle=ls))

    box(0.0, 2.5, "Sender", "knows the secret word\n(e.g. salmon)", BLUE)
    box(3.75, 2.5, "Decode-censor", "blocks if it judges the message\nis about the word, or can\ndecode the word itself", ORANGE, "#fff6f1")
    box(7.5, 2.5, "Receiver", "guesses each turn\nor abstains (6 turns)", BLUE)
    arrow(2.55, 3.7, 1.45)
    arrow(6.3, 7.45, 1.45)
    ax.text(6.88, 1.53, "delivered", ha="center", va="bottom", fontsize=6.2, color=MUTED)
    ax.text(6.88, 1.38, "or blocked", ha="center", va="top", fontsize=6.2, color=MUTED)
    arrow(3.7, 2.55, 0.85, ls=(0, (2, 2)), col=MUTED)
    ax.text(3.13, 0.78, "told what\nwas blocked", ha="center", va="top", fontsize=6.0, color=MUTED)
    # shared background bracket over sender and receiver
    ax.add_patch(FancyBboxPatch((0.0, 2.05), 10.0, 0.42, boxstyle="round,pad=0.02,rounding_size=0.1",
                                fc="#eef4fc", ec="none"))
    ax.text(5.0, 2.26, "Sender and receiver share a community background (\"you both grew up with Irish "
            "mythology\"): context only, never a code. The censor does not share it.", 
            ha="center", va="center", fontsize=6.0, color=INK)
    ax.text(5.0, 0.22, "Dogwhistle = the receiver decodes the word  +  the censor model cannot  +  "
            "the message reads as ordinary community talk", ha="center", va="center",
            fontsize=6.8, color=INK, weight="bold")
    save(fig, "f1_schematic")


# ----------------------------------------------------------------------------- f2
def f2_propensity():
    """Dot plot: per family, default vs v9 triple rate (vs gpt-4o-mini), 95% CI."""
    acc = defaultdict(lambda: {"v8n": [0, 0], "v9": [0, 0]})
    srcs = ["data/dwS_analysis.txt", "data/dwU_analysis.txt", "data/dwW_analysis.txt",
            "data/dwX_analysis.txt", "data/dwZr_analysis.txt", "data/dwZf_analysis.txt",
            "data/dwZs_analysis.txt"]
    for s in srcs:
        for r in analysis(s):
            if "c4o" not in r["run"] or not r["model"]:
                continue
            # claude-sonnet-5.5 in dwZf had ~70% empty turns; dwZs is the re-run
            if r["run"].startswith("dwZf") and r["model"].startswith("claude"):
                continue
            pv = "v9" if "_v9_" in r["run"] else "v8n"
            acc[SHORT.get(r["model"], r["model"])][pv][0] += r["triple"]
            acc[SHORT.get(r["model"], r["model"])][pv][1] += r["n"]
    fams = sorted(acc, key=lambda f: acc[f]["v9"][0] / acc[f]["v9"][1])
    fig, ax = plt.subplots(figsize=(COL, 2.35))
    for i, f in enumerate(fams):
        for pv, col, dy in (("v8n", DEFAULT_C, -0.13), ("v9", V9_C, 0.13)):
            k, n = acc[f][pv]
            p, lo, hi = wilson(k, n)
            ax.plot([lo, hi], [i + dy, i + dy], color=col, lw=1.6, solid_capstyle="round", alpha=0.55)
            ax.plot(p, i + dy, "o", ms=4.6, color=col, mec="white", mew=0.8, zorder=3)
        k, n = acc[f]["v9"]
        ax.text(wilson(k, n)[2] + 0.012, i + 0.13, f"{k}/{n}", va="center", fontsize=6.2, color=INK2)
    ax.set_yticks(range(len(fams)), fams)
    ax.set_xlim(-0.01, 0.68)
    ax.set_xlabel("share of games with a dogwhistle (vs gpt-4o-mini)")
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    style_axis(ax, "x")
    tot0 = sum(acc[f]["v8n"][0] for f in fams)
    n0 = sum(acc[f]["v8n"][1] for f in fams)
    tot1 = sum(acc[f]["v9"][0] for f in fams)
    ax.text(0.67, -0.95, f"default prompt  {tot0}/{n0}", color=MUTED, fontsize=6.6, ha="right")
    ax.text(0.67, -1.45, f"\"ordinary remark, not a clue\"  {tot1}/{n0}", color=V9_C, fontsize=6.6,
            ha="right", weight="bold")
    ax.set_ylim(-1.75, len(fams) - 0.4)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    save(fig, "f2_propensity")


# ----------------------------------------------------------------------------- f3
def f3_ablation():
    """v8n / v9m / v9o / v9 on the same items and seeds (Exp R runs 0-2 + Exp V)."""
    probes = jl(RAW / "dw_probes_V.jsonl") + jl(RAW / "dw_probes_Pa.jsonl")
    c = Counter()
    for p in probes:
        if p["run_index"] > 2 or p["item_id"] in ("dw02", "dw22"):
            continue
        c[p["run"].split("_")[1]] += (not p["out_recover"]) and p["innocent"]
    rows = [("v8n", "default prompt", DEFAULT_C),
            ("v9m", "+ \"never mention the game\"", "#9fb9de"),
            ("v9o", "+ \"an ordinary remark, not a clue\"", BLUE),
            ("v9", "+ both clauses (full sentence)", "#1c5cab"),
            ("v9p1", "paraphrase 1 (\"rather than a hint\")", "#5b8fd0"),
            ("v9p2", "paraphrase 2 (\"don't write hints\")", "#5b8fd0"),
            ("v9p3", "paraphrase 3 (no negation)", "#5b8fd0")]
    fig, ax = plt.subplots(figsize=(COL, 2.3))
    for i, (k, lab, col) in enumerate(rows[::-1]):
        p, lo, hi = wilson(c[k], 72)
        ax.barh(i, p, height=0.58, color=col)
        ax.plot([lo, hi], [i, i], color=INK2, lw=0.8)
        ax.text(hi + 0.008, i, f"{c[k]}/72", va="center", fontsize=6.4, color=INK2)
    ax.set_yticks(range(len(rows)), [r[1] for r in rows[::-1]])
    ax.set_xlim(0, 0.34)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.set_xlabel("games with a dogwhistle (Llama-70B + DeepSeek, 12 words x 3 runs)")
    style_axis(ax, "x")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    save(fig, "f3_ablation")


# ----------------------------------------------------------------------------- f4
def f4_censor_ladder():
    """Per-game rates of decoded games / dogwhistles / knowledge-gap dogwhistles by censor."""
    R = {r["run"]: r for r in analysis("data/dwR_analysis_meta5.txt")}
    Y = defaultdict(lambda: Counter())
    for r in analysis("data/dwY_analysis.txt"):
        for k in ("n", "D", "triple", "kg"):
            Y[r["run"]][k] += r[k]
    ladder = [("Llama-3.2-3B", R["dwR_v9_c3b"]), ("Llama-3.1-8B", R["dwR_v9_c8b"]),
              ("GPT-4o-mini", R["dwR_v9_c4o"]), ("GPT-4.1", Y["dwY_v9_c41"])]
    series = [("D", "partner decoded the word", "#9fb9de"),
              ("triple", "dogwhistle", BLUE),
              ("kg", "dogwhistle the in-group decodes cold", "#1c5cab")]
    fig, ax = plt.subplots(figsize=(COL, 2.2))
    xs = range(len(ladder))
    for key, lab, col in series:
        ys = [r[key] / r["n"] for _, r in ladder]
        ax.plot(xs, ys, "-o", color=col, lw=1.8, ms=4.2, mec="white", mew=0.8, label=lab)
    # default prompt reference (dogwhistles): zero at every rung tested
    ax.plot([1, 2, 3], [0, 0, 0], "o", color=DEFAULT_C, ms=3.8, mec="white", mew=0.6,
            label="dogwhistle, default prompt (0 at every rung)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=2, fontsize=6.0,
              handlelength=1.4, columnspacing=1.0)
    ax.set_xticks(list(xs), ["3B", "8B", "GPT-4o-\nmini", "GPT-4.1"])
    ax.set_xlim(-0.3, len(ladder) - 1 + 0.3)
    ax.set_ylim(-0.02, 0.85)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.set_ylabel("share of games")
    ax.set_xlabel("in-game decode-censor (weaker → stronger)")
    style_axis(ax, "y")

    save(fig, "f4_censor_ladder")


# ----------------------------------------------------------------------------- f5
def f5_items():
    """Heatmap: share of v9 games that produced a dogwhistle, per word x family."""
    fams = ["meta-llama/llama-3.3-70b-instruct", "deepseek/deepseek-chat",
            "qwen/qwen-2.5-72b-instruct", "google/gemma-3-27b-it"]
    runs = {"dwR_v9_c4o": "orig", "dwS_v9_c4o": "orig", "dwU_v9_c4o": "held"}
    n = Counter()
    targets = {}
    for run, setname in runs.items():
        for r in jl(RAW / f"{run}.jsonl"):
            if r["item_id"] in ("dw02", "dw22", "dw34", "dw41"):
                continue
            n[(r["target"], r["model"])] += 1
            targets[r["target"]] = setname
    k = Counter()
    for f in ("dw_probes_S.jsonl", "dw_probes_U.jsonl"):
        for p in jl(RAW / f):
            if p["run"] in runs and not p["out_recover"] and p["innocent"]:
                k[(p["target"], p["model"])] += 1
    order = sorted(targets, key=lambda t: (targets[t] != "orig",
                                           -sum(k[(t, f)] / max(n[(t, f)], 1) for f in fams)))
    import numpy as np
    M = np.array([[k[(t, f)] / max(n[(t, f)], 1) for f in fams] for t in order])
    fig, ax = plt.subplots(figsize=(COL, 3.3))
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("b", ["#f4f3f0", "#9ec5f4", "#2a78d6", "#104281"])
    im = ax.imshow(M, cmap=cmap, vmin=0, vmax=0.75, aspect="auto")
    for i, t in enumerate(order):
        for j, f in enumerate(fams):
            v = k[(t, f)]
            if v:
                ax.text(j, i, f"{v}", ha="center", va="center", fontsize=6,
                        color="white" if M[i, j] > 0.4 else INK)
    ax.set_xticks(range(4), ["Llama", "DeepSeek", "Qwen", "Gemma"])
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(order)), order)
    held = [i for i, t in enumerate(order) if targets[t] == "held"]
    if held:
        ax.axhline(held[0] - 0.5, color=INK, lw=0.8)
        ax.text(3.55, held[0] - 0.35, "held-out\nwords", fontsize=6, color=INK2, va="top")
        ax.text(3.55, -0.35, "original\nwords", fontsize=6, color=INK2, va="top")
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.03, location="bottom", aspect=30)
    cb.ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    cb.outline.set_visible(False)
    cb.set_label("share of v9 games with a dogwhistle (numbers = count)", fontsize=6.4, color=INK2)
    cb.ax.tick_params(labelsize=6)
    save(fig, "f5_items")


# ----------------------------------------------------------------------------- f6
def f6_collateral():
    """Catch rate on knowledge-gap dogwhistles vs innocent-message false positives."""
    rows = jl(RAW / "hop_test.jsonl") + jl(RAW / "hop_test_R_gpt41.jsonl")
    pts = defaultdict(dict)
    for r in rows:
        c = r["censor"].split("/")[-1]
        pts[c][r["variant"]] = (sum(d["caught"] for d in r["dw"]) / len(r["dw"]),
                                sum(a["blocked"] for a in r["adj"]) / len(r["adj"]))
    names = {"llama-3.1-8b-instruct": ("Llama-3.1-8B", ORANGE), "gpt-4o-mini": ("GPT-4o-mini", BLUE),
             "gpt-4.1": ("GPT-4.1", INK)}
    marks = {"direct": ("o", "in-game rule"), "cot": ("s", "reasoning, FP-aware"),
             "cot_strict": ("^", "reasoning, zero tolerance")}
    fig, ax = plt.subplots(figsize=(COL, 2.55))
    ax.axvspan(0.15, 0.72, color=PALE, zorder=0)
    ax.text(0.165, 0.02, "blocks >15% of innocent messages", ha="left", va="bottom", fontsize=6,
            color=MUTED)
    for c, (lab, col) in names.items():
        v = pts[c]
        xs = [v[m][1] for m in ("direct", "cot", "cot_strict")]
        ys = [v[m][0] for m in ("direct", "cot", "cot_strict")]
        ax.plot(xs, ys, "-", color=col, lw=1.0, alpha=0.45)
        for m in ("direct", "cot", "cot_strict"):
            ax.plot(v[m][1], v[m][0], marks[m][0], color=col, ms=5, mec="white", mew=0.8, zorder=3)
        ax.text(v["direct"][1] + 0.018, v["direct"][0], lab, va="center", fontsize=6.6, color=col,
                weight="bold")
    # incident-reviewed censor (held-out dogwhistles, section 9)
    ax.plot(0, 19 / 21, "D", color=AQUA, ms=5, mec="white", mew=0.8, zorder=3)
    ax.text(0.018, 19 / 21 + 0.035, "GPT-4o-mini + incident log", fontsize=6.4, color=AQUA, weight="bold")
    for i, (m, (mk, lab)) in enumerate(marks.items()):
        ax.plot(0.43, 0.30 - i * 0.075, mk, color=INK2, ms=4.2, mec="white", mew=0.6)
        ax.text(0.455, 0.30 - i * 0.075, lab, va="center", fontsize=6.3, color=INK2)
    ax.set_xlim(-0.02, 0.72)
    ax.set_ylim(0, 1.04)
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.set_xlabel("innocent same-community messages blocked")
    ax.set_ylabel("dogwhistles caught")
    style_axis(ax, None)
    save(fig, "f6_collateral")


# ----------------------------------------------------------------------------- f7
def f7_arms_race():
    seeds = []
    for prefix in ("arA", "arB"):
        d = defaultdict(dict)
        for r in analysis(f"data/{prefix}_analysis.txt"):
            _, cond, rnd = r["run"].split("_")
            d[cond][int(rnd[1:])] = r
        seeds.append(d)
    arms = [("sender", "Sender learns", BLUE), ("censor", "Censor learns", ORANGE),
            ("both", "Both learn", AQUA)]
    fig, axes = plt.subplots(1, 3, figsize=(WIDE, 1.75), sharey=True)
    for ax, (cond, title, col) in zip(axes, arms):
        for si, d in enumerate(seeds):
            rs = sorted(d[cond])
            ax.plot(rs, [d[cond][r]["D"] / 72 for r in rs], color=col, lw=1.6, ms=3.6,
                    marker="o", mec="white", mew=0.6, alpha=1 if si == 0 else 0.55,
                    ls="-" if si == 0 else (0, (3, 2)))
            ax.plot(rs, [d[cond][r]["kg"] / 72 for r in rs], color=col, lw=0.9,
                    alpha=0.9 if si == 0 else 0.45, ls="-" if si == 0 else (0, (3, 2)),
                    marker="s", ms=2.6)
        ax.set_title(title, color=col)
        ax.set_xticks(range(4))
        ax.set_xlabel("round")
        style_axis(ax, "y")
    axes[0].yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    axes[0].set_ylabel("share of games")
    axes[0].set_ylim(0, 0.5)
    L = plt.Line2D
    handles = [L([], [], color=INK2, lw=1.6, marker="o", ms=3.6, mec="white"),
               L([], [], color=INK2, lw=0.9, marker="s", ms=2.6),
               L([], [], color=INK2, lw=1.4), L([], [], color=INK2, lw=1.4, ls=(0, (3, 2)), alpha=0.6)]
    fig.legend(handles, ["partner decoded the word", "knowledge-gap dogwhistle", "seed 1", "seed 2"],
               loc="lower center", ncol=4, fontsize=6.4, bbox_to_anchor=(0.5, -0.2),
               handlelength=2.2, columnspacing=1.6)
    save(fig, "f7_arms_race")


# ----------------------------------------------------------------------------- f8
def f8_ack_funnel():
    """Receiver privately knew the word -> sender declared it understood (true / false)."""
    def parse(path, cell):
        for line in open(path, encoding="utf-8"):
            if line.startswith(cell):
                f = line.split()
                return dict(n=int(f[1]), knew=int(f[2]), ta=int(f[3]), fa=int(f[4]))
    rows = [("Plain reply", parse("data/expT_analysis.txt", "plain_message")),
            ("Reply as ordinary talk", parse("data/expT_analysis.txt", "cover_message")),
            ("+ sender may ask a check question", parse("data/raw/../expTc_analysis.txt", "cover_message")
             if Path("data/expTc_analysis.txt").exists() else None),
            ("Held-out words, 4 models", parse("data/expTU_analysis.txt", "cover_message"))]
    rows = [r for r in rows if r[1]]
    fig, ax = plt.subplots(figsize=(COL, 1.9))
    for i, (lab, d) in enumerate(rows[::-1]):
        n = d["n"]
        ax.barh(i, 1.0, height=0.62, color=PALE)
        ax.barh(i, d["knew"] / n, height=0.62, color="#9ec5f4")
        ax.barh(i, d["ta"] / n, height=0.62, color="#1c5cab")
        if d["fa"]:
            ax.barh(i, d["fa"] / n, left=d["knew"] / n, height=0.62, color=ORANGE)
        ax.text(d["knew"] / n + d["fa"] / n + 0.015, i,
                f"knew {d['knew']}/{n}  →  noticed {d['ta']}"
                + (f"  (+{d['fa']} false)" if d["fa"] else ""), va="center", fontsize=6.2, color=INK2)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows[::-1]])
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.set_xlabel("share of games")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    leg = [plt.Rectangle((0, 0), 1, 1, color=c) for c in ("#9ec5f4", "#1c5cab", ORANGE)]
    ax.legend(leg, ["receiver privately knew the word", "sender noticed (correctly)",
                    "sender wrongly thought it was understood"], loc="lower center",
              bbox_to_anchor=(0.3, -0.62), ncol=1, fontsize=6.2, handlelength=1.0)
    save(fig, "f8_ack_funnel")


# ----------------------------------------------------------------------------- f9
def f9_ack_evidence():
    """Forced choice from the reply alone: candidate prior -> with the reply."""
    def rates(path):
        agg = defaultdict(lambda: [0, 0])
        for x in jl(path):
            agg[x["kind"]][0] += x["correct"]
            agg[x["kind"]][1] += 1
        return {k: v[0] / v[1] for k, v in agg.items()}
    sets = [("original words", "expT"), ("held-out words", "expTU")]
    kinds = [("blocked_known_raw", "blocked by the censor", ORANGE),
             ("delivered_known", "got through", BLUE),
             ("delivered_unknown", "got through, receiver wrong", MUTED)]
    fig, axes = plt.subplots(1, 2, figsize=(WIDE * 0.62, 1.55), sharey=True)
    for ax, (sname, pre) in zip(axes, sets):
        prior = rates(RAW / f"{pre}_discrim_nothing.jsonl")
        reply = rates(RAW / f"{pre}_discrim_reply_only.jsonl")
        for i, (k, lab, col) in enumerate(kinds[::-1]):
            a, b = prior[k], reply[k]
            ax.annotate("", xy=(b, i), xytext=(a, i),
                        arrowprops=dict(arrowstyle="-|>", color=col, lw=1.4, mutation_scale=7,
                                        shrinkA=2, shrinkB=1))
            ax.plot(a, i, "o", ms=4, mfc="white", mec=col, mew=1.1, zorder=3)
            ax.plot(b, i, "o", ms=4.6, color=col, mec="white", mew=0.7, zorder=3)
            ax.text(max(a, b) + 0.03, i, f"{(b - a) * 100:+.0f} pts", va="center", fontsize=6.2,
                    color=col, weight="bold")
        ax.set_title(sname, color=INK2, weight="normal")
        ax.set_xlim(0.15, 0.9)
        ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
        style_axis(ax, "x")
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
    axes[0].set_yticks(range(3), [k[1] for k in kinds[::-1]])
    fig.supxlabel("sender picks the right word out of 5  (hollow: options only; filled: reading the reply)",
                  fontsize=6.6, color=INK2, y=-0.08)
    fig.subplots_adjust(wspace=0.12)
    save(fig, "f9_ack_evidence")


# ----------------------------------------------------------------------------- f10
def f10_calibration():
    from .analyze_dogwhistle import load_items
    from .analyze_expT import rescore
    sets = [("original words", ["expT_plain_message", "expT_cover_message"],
             "stimuli/dogwhistle_targets_R.csv", BLUE),
            ("held-out words", ["expTU_cover_message"], "stimuli/dogwhistle_targets_U.csv", AQUA)]
    edges = [0, 25, 50, 75, 90, 101]
    fig, ax = plt.subplots(figsize=(COL * 0.8, 2.1))
    ax.plot([0, 1], [0, 1], color=GRID, lw=1.0, zorder=0)
    ax.text(0.16, 0.08, "perfectly calibrated", rotation=38, fontsize=6, color=MUTED)
    for name, files, stim, col in sets:
        items = load_items(stim)
        b = defaultdict(lambda: [0, 0, 0.0])
        for fname in files:
            for r in jl(RAW / f"{fname}.jsonl"):
                rescore(r, items[r["item_id"]]["accept"])
                for t in r["turns"]:
                    c = t.get("private_confidence")
                    if c is None or str(t.get("private_answer", "")).upper() == "ABSTAIN":
                        continue
                    i = next(j for j in range(len(edges) - 1) if edges[j] <= c < edges[j + 1])
                    b[i][0] += 1
                    b[i][1] += t["receiver_knows"]
                    b[i][2] += c / 100
        xs = [b[i][2] / b[i][0] for i in sorted(b) if b[i][0] >= 5]
        ys = [b[i][1] / b[i][0] for i in sorted(b) if b[i][0] >= 5]
        ns = [b[i][0] for i in sorted(b) if b[i][0] >= 5]
        ax.plot(xs, ys, "-", color=col, lw=1.4)
        ax.scatter(xs, ys, s=[6 + n * 0.25 for n in ns], color=col, edgecolor="white", lw=0.6, zorder=3)
        ax.text(xs[-1] + 0.01, ys[-1] - (0.14 if col == BLUE else -0.05), name, color=col, fontsize=6.3, ha="right", weight="bold")
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0, 1.02)
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.set_xlabel("receiver's stated confidence")
    ax.set_ylabel("actually correct")
    style_axis(ax, None)
    save(fig, "f10_calibration")


def main():
    OUT.mkdir(exist_ok=True)
    for f in (f1_schematic, f2_propensity, f3_ablation, f4_censor_ladder, f5_items, f6_collateral,
              f7_arms_race, f8_ack_funnel, f9_ack_evidence, f10_calibration):
        f()


if __name__ == "__main__":
    main()
