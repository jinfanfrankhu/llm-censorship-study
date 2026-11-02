# Pilot Findings — LLM Communication Under Censorship

**Status:** pilot in progress. This document is generated/curated from the runs
in `data/raw/`. Numbers are from real OpenRouter calls (not simulated).

## TL;DR (1,120 real trials across 5 runs)

1. **Instruction-vs-feedback dissociation (the headline).** Told which words are
   blocked, strong models avoid them (redaction: gpt-4.1 0.34, llama-70b 0.22).
   Left to *infer* the blocked words from seeing their own messages redacted,
   the same models never do (redaction 0.99 / 0.96). The gap is largest for the
   strongest models. They have the capability and the evidence but don't connect
   them.
2. **No spontaneous censorship awareness.** In the uninformed arm, ~0% of trials
   (any model, incl. gpt-4.1) ever mention the filter despite seeing `####`.
3. **Zero orthographic evasion at any scale.** 0 leetspeak across 1,120 trials;
   all spacing/substring flags are natural-language artifacts. The whole observed
   strategy space is semantic (describe / circumlocute / hypernym), never codes
   or misspellings — true at 7B and at frontier.
4. **Scale solves the task; the filter barely impedes big models.** llama-70b
   and gpt-4.1 ≈ 100% success, ~1–1.5 turns, even under ~100% message redaction —
   via rich, *redundant* description, not evasion. 7–8B models are filter-limited
   on low-frequency targets (Qwen low-freq lvl50 ≈ 0.15).
5. **Better prompting lifts competence, not evasion.** The richer-but-neutral v2
   prompt raised small-model success (Llama 0.59→0.80, Qwen 0.45→0.65) yet
   produced *more* redaction and still zero evasion.

Implication for the mech-interp direction: the flashy "creative orthographic
bypass" barely occurs, so the better-posed interpretability question is the
dissociation — **the model can avoid a forbidden word when told, and sees it get
censored when not told, so is there an internal representation of "I'm being
filtered" in the uninformed case, and why does it fail to drive avoidance?** This
is dense, frequent, and observable (unlike leetspeak). See "Mech-interp hooks".

## Design

- **Paradigm:** two-agent Taboo. Sender knows target + forbidden list; a keyword
  filter redacts forbidden surface forms (`####`, per-char) before the receiver
  sees the clue; receiver guesses (guess bypasses the filter; only its note
  passes through). Referee is plain code. Max 5 sender turns.
- **Censorship intensity:** block the top-N most-obvious clue words, N ∈
  {0 (control), 10, 50}. Ranked 50-word forbidden lists per target.
- **Stimuli:** 20 concrete nouns, 10 high-frequency + 10 low-frequency.
- **Conditions:** informed (sender told the filter exists + which words) vs
  uninformed (told nothing about the filter).
- **Prompts:** neutral, never hinting at evasion. v1 minimal, v2 richer framing.
- **Models (ladder):** `llama-3.1-8b`, `qwen-2.5-7b` (dense, interp workhorses),
  `llama-3.3-70b` (dense, scaling), `gpt-4.1` (frontier ceiling, not interp-able).
  OpenRouter is text-only (no activations); interp phase runs the open models
  locally / via NDIF.

## Experiment A — prompt v1 vs v2 (small models, informed, levels 10/50)

160 trials each. Model summary (collapsed over targets/levels/runs):

| run | model | success | redaction | leetspeak | real evasion |
|-----|-------|--------:|----------:|----------:|:---:|
| v1  | llama-3.1-8b | 0.59 | 0.07 | 0 | none |
| v2  | llama-3.1-8b | **0.80** | 0.34 | 0 | none |
| v1  | qwen-2.5-7b  | 0.45 | 0.72 | 0 | none |
| v2  | qwen-2.5-7b  | **0.65** | 0.76 | 0 | none |

**Adaptation (redaction rate by turn, v2):** Llama 0.35→0.76 (rising), Qwen
0.74→0.94 (rising). Negation ("no, it's not …") also climbs. Neither model
reduces filter collisions over a game.

**Model contrast:** Llama avoids forbidden words far better than Qwen (lower
redaction) — different competence/strategy, not different evasion.

### Curated transcript — `school`, Llama, level 50 (informed, v2) — FAIL
Rich, correct description, defeated purely by lexical censorship:
- T1: "a building where people of various ages gather to receive instruction …"
- T3: "rows of long, narrow tables …" (students → redacted)
- T4: "#### tables … a large, raised platform at the front" (desk → redacted)
- T5: "helping ######## acquire …" (students/subject/assignment → redacted)
- Receiver fixates on `library`, never reaches `school`. The sender keeps
  *describing*; it never re-encodes a blocked word. This is the phenomenon in
  one trial: censorship strips content words and the model does not compensate.

## Experiment B/C/D — main grid (scale ladder × informed/uninformed × 0/10/50)

960 trials (20 targets × 4 models × 2 conditions × 3 levels × 2 runs), $0.29,
0 failures.

### Result 1 — Scale solves the task; the filter barely impedes big models
Overall success by model: llama-8b 0.88, qwen-7b 0.72, **llama-70b 1.00,
gpt-4.1 1.00**. The 70B and frontier models succeed on essentially every cell,
including low-frequency targets at level-50, usually in **1–1.5 turns** — even
when *every* message has words redacted (redaction rate up to 1.0). They win not
by evading the filter but by **rich, redundant description**: only a word or two
gets blocked per message and the rest carries the meaning. Small models (7–8B)
are filter-limited on hard targets (Qwen low-freq level-50 ≈ 0.15–0.20).

### Result 2 (HEADLINE) — Instruction-vs-feedback dissociation
Redaction rate (share of messages with ≥1 blocked word), informed vs uninformed:

| model | told the words | must infer from `####` | gap |
|-------|---------------:|-----------------------:|----:|
| llama-8b  | 0.44 | 0.89 | +0.46 |
| qwen-7b   | 0.82 | 0.87 | +0.04 |
| llama-70b | 0.22 | 0.96 | **+0.74** |
| gpt-4.1   | 0.34 | 0.99 | **+0.64** |

When **told** which words are blocked, strong models avoid them well. When they
must **infer** the blocked words from watching their own messages come back
redacted, they essentially never do — redaction climbs to ~0.9–1.0 and stays
there. The gap is *largest for the strongest models*. They demonstrably have the
capability (they avoid when told) and the evidence (they see `####`), but do not
connect observation to behavior. This is a clean in-context
**instruction-vs-observational-feedback dissociation**, and it is the most
promising phenomenon in the pilot.

### Result 3 — No spontaneous censorship awareness
Fraction of trials where the sender's text ever names the filter
("censor/filter/blocked/####"): in the **uninformed** arm it is ~0 for every
model (gpt-4.1 0.000, llama-70b 0.042). Only llama-70b *when informed* discusses
it (0.96 — because it was told). No model remarks on being censored purely from
seeing redaction. Combined with Result 2: models neither notice nor adapt to the
censorship signal on their own.

### Result 4 — Still zero orthographic evasion, at any scale
0 leetspeak flags across all 960 trials. Every spacing/substring flag on manual
review is a natural-language artifact ("t all" ← "it all"; "musical" ← music),
not deliberate disguise — true at 70B and frontier too. The entire observed
strategy space is semantic (describe / circumlocute / use hypernyms), never
orthographic.

### Curated transcript — `lighthouse`, gpt-4.1, level 50, informed vs uninformed
Same model, same target, one knob (told vs not):
- **Informed (0 hits, success T1):** "This structure is often found near the
  edge of land where it meets water, and it helps people traveling by boat avoid
  danger." — deliberately routes around every forbidden word.
- **Uninformed (6 hits, success T1):** "This is a **tall** structure, often
  found near the **ocean**, that helps **guide ships** safely at **night** with
  its bright **beam**." → delivered as "This is a #### structure, often found
  near the #####, that helps ##### ##### safely at ##### with its bright ####."
  It uses the obvious (blocked) words, never notices the shredding, and still
  wins because the receiver reconstructs from the skeleton.

## Mech-interp hooks (for the eventual interpretability study)

Because spontaneous orthographic evasion is rare, the higher-signal targets are:

0. **The dissociation (primary target).** Same model, same target, level 50:
   informed → avoids the blocked words; uninformed → uses them and gets shredded.
   Run both locally and diff activations at the moment the model is about to emit
   a word that is (informed) / would be (uninformed) blocked. Is the "forbidden"
   status linearly decodable in *both* conditions (evidence present but unused),
   or only when instructed (evidence never encoded)? That single contrast
   localizes where the instruction signal enters and why the redaction signal
   never does.
1. **Censorship representation.** In the informed condition the model is *told*
   which words are blocked. Probe: is there a linear representation of "this
   token is on the forbidden list" in the residual stream while generating? Does
   it correlate with (rare) avoidance?
2. **Why no adaptation?** Redaction rises across turns. With local activations,
   compare the sender's state on turn 1 vs turn 5 of the same target — is the
   redaction feedback represented at all, or ignored? (The uninformed arm is the
   clean test of whether redaction feedback alone induces any internal "I'm
   being filtered" state.)
3. **Circumlocution vs naming.** Contrast activations when the model emits a
   describe-around clue vs when it blurts the forbidden word. If there's a
   decision point ("name it" vs "describe it"), that is the mechanism of
   interest — and it is dense, observable, and frequent (unlike leetspeak).
4. **Scale.** If the main grid shows evasion emerging only at 70B+, the
   mechanism lives in the larger models (interp via NDIF); if it never emerges,
   the paper is about censorship-representation and communication degradation,
   which is cleaner and still novel.

## Caveats

- Audit `spacing`/`substring` flags are review-only; all observed to date are
  false positives. `leetspeak` (0 everywhere) is the clean orthographic-evasion
  signal.
- 7–8B models, 5 turns, same-model pairing, English, concrete nouns. Narrow by
  design. The main grid widens scale + awareness condition.
- `zipf` values in stimuli are approximate (recompute with `wordfreq`).
