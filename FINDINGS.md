# Pilot Findings — LLM Communication Under Censorship

**Status:** pilot in progress. This document is generated/curated from the runs
in `data/raw/`. Numbers are from real OpenRouter calls (not simulated).

## TL;DR (so far)

1. **The dominant strategy is semantic circumlocution, not orthographic evasion.**
   Across 320+ trials, models get meaning past a keyword filter by *describing*
   the concept (function, material, location, distinctive features). Deliberate
   orthographic tricks (leetspeak, letter-spacing, deliberate misspelling) are
   **essentially absent**: 0 leetspeak flags; every spacing/substring flag on
   manual review was a false positive (natural text), not real evasion.
2. **Models do not route around the filter; they collide with it.** Redaction
   rate *rises* across turns rather than falling — when easy angles run out,
   senders use more on-topic (forbidden) words, not fewer. No visible
   adaptation to the censorship signal.
3. **Better prompting lifts competence but not evasion.** A richer,
   strategy-neutral prompt (v2) raised success substantially (Llama 0.59→0.80,
   Qwen 0.45→0.65) — so weak early results were partly a weak-clue-giver
   problem. But v2 produces *more* redaction (richer clues hit the filter more)
   and still zero orthographic evasion.
4. **Censorship intensity degrades communication, especially for the weaker
   model on hard targets.** Low-frequency targets + level-50 filtering is where
   success collapses (Qwen low-freq lvl50 ≈ 0.05–0.15).

Implication for the mech-interp direction: the flashy "creative orthographic
bypass" behavior barely occurs at 7–8B, so the better-posed interpretability
question is about **censorship representation and (non-)adaptation** — does the
model internally represent "I am being filtered," and why does that not steer
generation away from blocked words? See "Mech-interp hooks" below. The main grid
(adding 70B + a frontier model) tests whether evasion emerges with scale.

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

_Running (960 trials). Results appended when complete:_
- Does orthographic evasion emerge at 70B / frontier scale?
- Uninformed arm: do senders *notice* the filter (mention it, change behavior)
  purely from seeing their messages redacted?
- Level-0 control isolates censorship effect from baseline Taboo difficulty.

<!-- MAIN_GRID_RESULTS -->

## Mech-interp hooks (for the eventual interpretability study)

Because spontaneous orthographic evasion is rare, the higher-signal targets are:

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
