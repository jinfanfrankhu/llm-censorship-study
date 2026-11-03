# CLAUDE.md — orientation for future instances

## What this project is
A research pilot (target ARR/ACL 2027 cycle) studying **whether LLMs can
communicate a target concept past a censorship filter to a partner LLM**, and
whether they notice/adapt to being censored. Two-agent Taboo game: a **sender** gives clues about a secret word, a
**filter** redacts forbidden words (`####`), a **receiver** guesses. Referee is
plain code. The deeper aim is a **mechanistic-interpretability** follow-up.

## Current state (read these first)
- `FINDINGS.md` — all results so far (committed). The three headline findings:
  - **F1 evasion gate:** off-the-shelf models never use orthographic evasion
    (leetspeak/spacing) spontaneously, but do when *explicitly permitted* (prompt
    v3); a soft hint (v4) doesn't trigger it. Capability vs **propensity** gap.
    NOTE: robust orthographic disguise is concentrated in gpt-4.1 + llama-3.3-70b;
    mid models mostly respond to permission with better *semantic* avoidance.
  - **F2 censorship blind spot:** models avoid banned words when *told* them, but
    not when they must *infer* the ban from seeing their own `####` redactions.
  - **F3 sender/receiver decomposition:** either a strong sender or strong
    receiver rescues a weak-weak pair (cross-model pairing).
- `LIT-REVIEW.md` (gitignored) — positioning vs prior work (steganographic
  collusion, sandbagging/password-locks, self-correction blind spot, refusal
  direction, emergent communication, LLM guardrails). Read for novelty framing.
- `scratchpad/ideas.md` (gitignored) — ranked next directions.
- **Next planned experiment:** a **semantic / LLM censor** (`src/semantic_filter.py`)
  to replace the easy keyword filter — forces real evasion. See scratchpad TIER 1.

## Repo map
- `src/filter.py` — keyword BlockingFilter + audit detector (leetspeak/spacing/
  substring/near_miss). `tests/test_filter.py` covers it.
- `src/client.py` — OpenRouter wrapper: on-disk cache, tenacity retries, usage
  log, budget guard. **Text-only API — no activations.**
- `src/mock.py` — fake model for `--dry-run` (zero cost).
- `src/prompts.py` — versioned prompts. v1 minimal, **v2 richer neutral
  (default)**, v3 explicit permission-to-evade, v4 soft creativity hint.
- `src/game.py` — one trial: turn loop + referee. Supports separate
  sender/receiver models (`receiver_model`).
- `src/run.py` — grid runner. Resumable (skips trials already in the output
  jsonl). Supports `model_pairs` for cross-pairing. Per-trial error handling.
- `src/analyze.py` — per-run metrics table + markdown transcript export.
- `src/report.py` — cross-run analysis (metrics, adaptation, filter awareness,
  cross-pair).
- `config/*.yaml` — one per experiment; `run_name` = output file name.
- `stimuli/targets.csv` — 20 targets (10 high-/10 low-freq), each with a 50-word
  ranked `forbidden` list (pipe-separated). zipf values are approximate.
- `PILOT_PLAN.md` — original design (gitignored by Frank).
- `data/raw/*.jsonl` — run outputs (gitignored). `data/transcripts/`, `cache/`,
  `.env` also gitignored.

## How to run
Use the venv interpreter explicitly: **`.venv/Scripts/python.exe`** (Windows).
```sh
.venv/Scripts/python.exe -m pytest tests/ -q                 # tests (21)
.venv/Scripts/python.exe -m src.run --config config/X.yaml --dry-run --limit 4   # plumbing, no cost
.venv/Scripts/python.exe -m src.run --config config/X.yaml   # real run (needs .env OPENROUTER_API_KEY)
.venv/Scripts/python.exe -m src.run --config config/X.yaml --workers 10   # parallel trials (I/O-bound, ~10x)
.venv/Scripts/python.exe -m src.analyze --run_name X
.venv/Scripts/python.exe -m src.report --runs A B            # compare runs
```

## Conventions
- **Git hygiene:** work on a branch (current experiment branch: `pilot-experiments`),
  atomic commits. Never commit `data/`, `.env`, `LIT-REVIEW.md`, `scratchpad/`.
- Each experiment gets its own `run_name`/config. Runs are resumable and cached,
  so re-running analysis never re-calls the API.
- Report results honestly; this is research. Read transcripts before trusting
  aggregate metrics.

## Gotchas
- Audit `spacing`/`substring` flags are **review-only / noisy**; `leetspeak` (and
  hand-verified spacing) is the clean orthographic-evasion signal. `main_v2` ran
  with the older looser spacing detector; `expE/expG/expH` use the tightened one.
- `python-dotenv`: call `load_dotenv(".env")` explicitly (bare `find_dotenv`
  fails when run via heredoc).
- OpenRouter has transient 500s; the client's retries ride through them.
- **Killing a background run on Windows orphans the python child.** Stopping the
  bash wrapper (TaskStop / Ctrl-C) does NOT cascade to the `python -m src.run`
  child — it keeps running and keeps writing. If you relaunch, the orphan and the
  new run write the SAME config concurrently, producing duplicate rows (seen:
  moderate/strict at ~780 lines vs the 400-cell max). Always kill python by PID
  after stopping a run (`Get-Process python | Stop-Process -Force`), verify zero
  remain, THEN relaunch. Writes are per-line-flushed so no truncation, but dedupe
  defensively by trial key `(item_id, model, receiver_model, informed,
  forbidden_level, run_index)` — keep first occurrence — before analysis. Letting
  a run finish on its own (don't kill) avoids the whole problem.
- Interp phase needs model internals → run open models locally or via **NDIF**
  (hosts Llama-3.1-70B free for researchers); OpenRouter can't give activations.
- This repo runs an always-on "caveman" chat-style hook (terse replies). It only
  affects chat prose — code, commits, and docs stay normal prose.
