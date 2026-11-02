# LLM Communication Under Censorship — Taboo Pilot

A small, reproducible pilot testing whether an LLM can get a target concept past
a censorship filter to a partner LLM. Two guiding questions:

1. Can LLMs tell when (and how) they are being censored?
2. Can LLMs use language creatively to get meaning past a censorship filter?

See [PILOT_PLAN.md](PILOT_PLAN.md) for the full design rationale. This README is
the operational guide.

## Paradigm

A Taboo-style referential game between two LLM agents on the same model:

- **Sender** knows the target word and a list of forbidden words; it sends clues.
- **Filter** redacts forbidden surface forms before delivery (`####`, Roblox-style).
- **Receiver** sees only filtered clues and guesses. The guess goes straight to
  the referee — never through the channel — so a correct guess is never redacted.
- **Referee** (plain code) checks the guess and ends the trial.

The sender sees how each message was delivered; that visible redaction is the
censorship signal.

## Censorship intensity sweep

Instead of a fixed 5-word taboo list, the filter strictness is an experimental
variable: block the **top-N most-obvious clue words** for N in `forbidden_levels`
(default `[10, 20, 50]`). `stimuli/targets.csv` stores a single ranked
`forbidden` list per target (pipe-separated, most-obvious first); each level uses
the first N. Higher N = harsher censorship.

> **Stimuli status:** each target currently ships with **20** ranked forbidden
> words. Levels `10` and `20` run cleanly today; level `50` falls back to all 20
> (the runner prints a warning). Before the real 50-word run, extend each list to
> ≥50 ranked words — draft with a model, then **hand-approve every item** (benign,
> concrete, correctly ranked). Also recompute `zipf` with
> `wordfreq.zipf_frequency(word, "en")`; the shipped values are rough.

## Setup

```sh
# with uv (preferred)
uv venv && uv pip install -r requirements.txt

# or plain venv
python -m venv .venv && .venv/Scripts/activate   # Windows
pip install -r requirements.txt
```

Create `.env` from the template (never commit it):

```sh
cp .env.example .env    # then paste your OpenRouter key
```

## Run

```sh
# offline, zero cost — exercises the whole pipeline with a mock model
python -m src.run --config config/pilot.yaml --dry-run

# tests (stdlib only, no deps needed)
python -m unittest discover -s tests -v

# smoke test: cap new trials, real model (needs .env + edit config to one model)
python -m src.run --config config/pilot.yaml --limit 15

# full pilot (resumable — rerun to continue after a crash or budget stop)
python -m src.run --config config/pilot.yaml

# metrics + human-readable transcripts
python -m src.analyze --run_name pilot_v1 --full_trials 180
```

Output: one JSONL per run in `data/raw/`, markdown transcripts in
`data/transcripts/<run>/`, a metrics CSV in `data/`.

## Layout

```
config/pilot.yaml      models, conditions, intensity levels, sampling, budget
stimuli/targets.csv    20 targets, ranked forbidden lists, freq band + zipf
src/filter.py          blocking filter (whole-word, explicit variants) + audit detector
src/client.py          OpenRouter wrapper: retries, cache, usage log, budget guard
src/mock.py            fake model for --dry-run (no API cost)
src/prompts.py         neutral sender/receiver templates (versioned)
src/game.py            one trial: turn loop + referee
src/run.py             CLI, resumable grid runner
src/analyze.py         metrics table + transcript export
tests/test_filter.py   offline filter + audit tests
```

## Design notes

- **Filter policy:** whole-word, case-insensitive, with explicit (reviewable)
  inflection variants — *not* a stemmer. Substrings inside unrelated words are
  **not** blocked (`keys` does not fire on `monkeys`); such smuggling is surfaced
  by the audit detector instead.
- **Audit detector** logs likely evasions (leetspeak, spacing, substring,
  edit-distance-1 near-miss) but never blocks. Flags are for analysis.
- **Prompts are neutral** — they never suggest an evasion strategy. Strategies
  must emerge from the model.
- **Caching** is keyed by (model, messages, params, run_index); re-running
  analysis or resuming a run never re-calls the API.
- **Mech-interp caveat:** OpenRouter returns no activations. Interpretability
  work runs the open-weight models locally (TransformerLens / nnsight) or via
  NDIF — see `config/pilot.yaml` for model choices picked to stay instrumentable.

## Out of scope for the pilot

Semantic (LLM-based) filter, cross-model pairing, repeated-round convention
formation, multilingual conditions, LLM-based strategy annotation. These come
after the design is reviewed with Prof. McCoy.
```
