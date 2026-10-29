# Human-readable evasion pilot

A tiny behavioral experiment starter: 20 harmless messages, direct-message controls, human-reader sheets, simulated keyword/LLM censors and scoring. This is not a completed study or a novelty claim.

## Start here
Download `bootstrap.py` from this repository, then run:

```sh
python bootstrap.py
cd pilot-starter
python -m unittest discover -s tests -v
```

Python 3.10+; standard library only. The bootstrap extracts the source, tests, data and prompts into a **new** local directory, checking the embedded archive checksum first. It refuses to overwrite an existing directory. It makes no network calls, installs no packages, and calls no paid APIs.

Open the extracted `README.md`. Your first task is to collect one model rewrite for each of the 10 development messages, saving the exact first response. Freeze the protocol before the 10 test messages. Two independent human readers judge meaning; a fresh isolated LLM censor judges the simulated policy. The offline harness prepares sheets and scores their labels. No model outputs or empirical results are included.

## Contents after extraction
- `pilot.py`: prepare reader sheets and score labels.
- `tests/test_pilot.py`: five offline tests.
- `data/items.csv`: 20 toy messages, development/test split and meaning rubrics.
- `data/rewrites.csv`: empty output collection template.
- `prompts/`: writer, censor and reader instructions.
- `RUN_NOTES.md`: settings, raw-output and missing-trial record.
- `README.md`: full protocol, scoring, limitations and related papers.

The bootstrap format keeps the whole tested starter together. Its payload is a ZIP of these plain-text source files, not executable downloaded code. After extraction you can inspect and work with them normally.

Stop after a single 20-message run: one chart, exact counts, five examples including failures, and a short methods/limitations note. Adaptation is a follow-up, not part of the first run. This is behavioral evaluation, not mechanistic interpretability. No public research publication or paid calls have been made.
