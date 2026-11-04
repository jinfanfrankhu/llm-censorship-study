# LLM Communication Under Censorship

Can two language models get a message past an AI censor, and do they try to?
This repository holds the code, stimuli, configs and findings for a study of how
LLMs communicate when a third model is watching and blocking what it judges to
be off-limits. Target venue: ARR / ACL 2027.

The study runs as a Taboo-style word-guessing game:

- A **sender** model knows a secret word and writes short messages to a partner.
- A **censor** reads every message and blocks anything it judges to reveal the
  word. Blocked messages never arrive; the sender is told which were blocked.
- A **receiver** model reads what gets through and guesses (or abstains).
- A **referee** (plain code) scores the game. A correct guess on a turn whose
  message was blocked does not count.

## What we have found so far

The work proceeded in three phases; each has its own findings file.

**1. Keyword filter** ([FINDINGS.md](FINDINGS.md)). The censor blacks out a
list of banned words.
- Large models *can* disguise words (leetspeak, letter spacing) but never do it
  unless explicitly permitted; small models cannot even when permitted.
- Told which words are banned, models avoid them. Left to infer the ban from
  seeing their own words redacted, they do not adapt and rarely mention the
  filter at all.

**2. Semantic censor** ([FINDINGS_surveillance.md](FINDINGS_surveillance.md)).
The censor is an LLM that judges what a message is about.
- Spelling tricks are the worst strategy against such a censor: it decodes them
  and they look suspicious. Ambiguous, functional descriptions ("I help people
  navigate") get through.
- Models' instincts are miscalibrated: told to evade, a stronger model reached
  for spelling tricks and did worse than a weaker one.
- Blocking a censorship-aware sender costs false positives on innocent messages,
  the same trade-off human censors face.

**3. Dogwhistles under a knowledge gap**
([FINDINGS_dogwhistle.md](FINDINGS_dogwhistle.md); current work). Sender and
receiver share a real community background (pianists, Irish mythology,
Wittgenstein readers); the censor lacks it or fails to connect it. No codes are
ever supplied: any allusion must come from the models' own knowledge. A
*dogwhistle* is a message the partner decodes, the censor cannot, and that reads
as ordinary conversation.
- **Can, but won't.** With a neutral prompt, models produced no dogwhistles in
  492 games across seven model families (Llama, DeepSeek, Qwen, Gemma, GPT,
  Gemini, Claude). One added sentence asking for "an ordinary remark from your
  community, not a clue" produced 92/492, including on a second item set written
  after the effect was found. An ablation shows the "not a clue" clause does the
  work; forbidding talk about the game does nothing.
- **How hard they are to stop depends on the censor.** A frontier censor
  (gpt-4.1) catches about 70% of what gets past gpt-4o-mini at roughly 4% false
  positives. The remaining, genuinely deniable messages can only be caught by
  blocking 40-66% of innocent same-community conversation.
- **Arms race.** A censor that reviews past incidents stays ahead of a sender
  that learns from its blocked messages (two independent runs).
- **Acknowledging receipt is the hard part.** When the receiver must confirm
  understanding through the same censor, replies that would prove it knows the
  word get blocked, and replies that get through carry essentially no evidence
  about the specific word. Senders almost never learn that their partner
  understood.

Each findings file lists its caveats; judge validity, sample sizes and
replication status are reported there alongside every number.

## Setup

```sh
python -m venv .venv
.venv/Scripts/activate            # Windows; use .venv/bin/activate elsewhere
pip install -r requirements.txt
cp .env.example .env              # then add your OpenRouter key
```

On Windows, call the interpreter explicitly (`.venv/Scripts/python.exe`) and set
`PYTHONIOENCODING=utf-8` before printing model output.

## Running

```sh
# tests
python -m pytest tests/ -q

# plumbing check with a fake model (no API cost; writes mock trials to
# data/raw/<run_name>.jsonl -- delete that file before the real run)
python -m src.run --config config/pilot.yaml --dry-run --limit 4

# a real run (resumable: rerun to continue after a crash or budget stop)
python -m src.run --config config/dwR_v9_c4o.yaml --workers 6

# analysis
python -m src.analyze --run_name pilot_v1                  # phases 1-2
python -m src.analyze_dogwhistle --runs dwR_v9_c4o dwR_v8n_c4o \
    --stimuli stimuli/dogwhistle_targets_v2.csv --by_model  # phase 3
python -m src.figures                                       # figures/
```

Each experiment has its own config in `config/`; its `run_name` is the output
file in `data/raw/`. API calls are cached on disk, so re-running an analysis
never re-calls a model. The client enforces a per-run budget cap.

Dogwhistle pipeline: `src.gap_check` (verify the knowledge gap) -> run the
`config/dw*` grids -> `src.analyze_dogwhistle` -> follow-ups (`src.hop_test`,
`src.arms_race`, `src.learned_heldout`, `src.covert_ack`, `src.analyze_expT`,
`src.ack_discrim`).

## Layout

```
config/                 one YAML per experiment (models, prompt version, censor, runs, budget)
stimuli/                targets.csv (phases 1-2); dogwhistle_targets_*.csv (phase 3),
                        built by stimuli/build_dw*.py; dw_adjacent_*.json innocent controls
src/game.py             one trial: turn loop + referee
src/run.py              resumable grid runner
src/prompts.py          versioned sender/receiver prompts (v1-v9, v9o/v9m ablations)
src/filter.py           keyword filter + evasion audit detector
src/censor.py           LLM censors: topic judge, decode-censor, conversation-level censor
src/scoring.py          referee rules (abstain, voided blocked-clue wins)
src/client.py           OpenRouter wrapper: retries, on-disk cache, usage log, budget guard
src/mock.py             fake model for --dry-run
src/analyze*.py         per-phase analysis; analyze_dogwhistle.py holds the judges
src/gap_check.py        knowledge-gap check for dogwhistle stimuli
src/hop_test.py         re-judge dogwhistles with stronger / reasoning censors + false positives
src/arms_race.py        multi-round censor-vs-sender learning
src/covert_ack.py       two-way variant: receiver acknowledges through the censor
src/ack_*.py            acknowledgment analyses (verdict re-read, forced-choice evidence test)
src/figures.py          paper figures
tests/                  filter, scoring and censor tests
FINDINGS*.md            results of record for each phase
```

Raw outputs (`data/`), the API cache, `.env` and rating sheets stay local and
are gitignored.

## Notes

- **Prompts never suggest a tactic** unless the experiment says so (e.g. the
  permission prompt in phase 1). Strategies must come from the model.
- **Interpretability.** OpenRouter returns text only, no activations. The
  planned mechanistic follow-up (what changes inside a model between the default
  and "ordinary remark" prompts) will run open-weight models locally or via
  NDIF.
