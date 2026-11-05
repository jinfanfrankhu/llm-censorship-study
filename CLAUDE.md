# CLAUDE.md — orientation for future instances

## What this project is
A study (target ARR / ACL 2027 main) of **whether LLMs communicate a secret word
past an LLM censor to a partner LLM, and whether they try to.** Taboo-style game:
a **sender** writes messages about a secret word, a **censor** blocks messages it
judges to reveal the word, a **receiver** guesses (or abstains), and plain code
referees. A mechanistic-interpretability follow-up is planned (needs open-weight
models; OpenRouter gives text only).

Three phases, each with its own findings file of record:
1. **Keyword filter** (`FINDINGS.md`): models can disguise words but don't unless
   permitted (F1); they don't infer a ban from seeing their own redactions (F2);
   a strong sender or receiver rescues a weak pair (F3).
2. **Semantic censor** (`FINDINGS_surveillance.md`): spelling tricks fail
   against an LLM censor, ambiguity works; models' evasion instincts are
   miscalibrated; censoring aware senders costs false positives.
3. **Dogwhistles under a knowledge gap** (`FINDINGS_dogwhistle.md`, CURRENT
   WORK, branch `dogwhistle-asymmetry`): see "Current status" below.

## Start here (in this order)
1. The **headline block at the top of `FINDINGS_dogwhistle.md`**: every current
   number with its section.
2. `PAPER_OUTLINE.md`: pitch, contributions, figure plan, open items.
3. `paper/draft.md` (LOCAL ONLY, gitignored): full first draft;
   `paper/citations.md` (citation check status); `paper/table_examples.md`.
4. `figures/` (rebuild with `python -m src.figures`; module docstring lists all
   ten figures and their data sources).
5. `LIT-REVIEW.md` (gitignored): related work and novelty positioning (section
   10 = latest novelty re-check).

## Current status (2026-11-05)
- **Propensity gap:** default prompt (v8n) 1/636 dogwhistles across eleven
  sender models (incl. reasoning deepseek-r1 / qwen3-thinking and frontier
  gpt-4.1 / claude-sonnet-5.5); one sentence (v9: "an ordinary remark from
  your community, not a clue") gives 140/636 (p = 2e-44; cluster tests in
  `data/cluster_stats_withZ.txt`). Holds on held-out words, under three
  paraphrases (21), for cross-family pairs (22); the sender-learns arms race
  from v8n never finds it (0/864, 19). Ablation: the "ordinary remark" clause
  does all the work (13).
- **Censor strength relative to sender strength:** gpt-4.1 catches ~70% of
  what beats gpt-4o-mini; in game it leaves mid-size senders 1 knowledge-gap
  dogwhistle in 72, but reasoning/frontier senders 19 in 144 (15, 17, 18).
- **Judges:** two second-family innocence judges confirm 185-188 of 189
  triples (20). A second HUMAN rater is still missing.
- **Covert acknowledgment** (most novel): receivers privately know the word in
  ~1/3-1/2 of games, senders notice ~2-3%; delivered replies carry ~0 word-level
  evidence vs the candidate prior; blocked ones carry 10-21 points (11-11g).
- **Open items:** second human rater for the innocence judge; refine the
  acknowledgment rubric (story-echo vs word-echo) if ECHO counts stay in the
  paper; 7 citations to verify (`paper/citations.md`); framing decision;
  figure renumbering in the draft; figures do not yet include Exp Z.
- **Budget:** ~$42.4 spent by 2026-11-05 (the $15 cap was overrun by Exp Z,
  ~$23). Every paid call now goes to `data/spend_ledger.txt`; `.env` sets
  `PROJECT_BUDGET_USD=64` (PI topped up to ~$31 of credit on 2026-11-05).
  Reasoning models: give senders max_tokens >= 2500 (claude-sonnet-5.5 cannot
  disable thinking on OpenRouter; use `reasoning: {effort: low}`); check
  `errors` for `empty_sender` after any run.

## Where to find things
| what | where |
|---|---|
| results of record | `FINDINGS.md`, `FINDINGS_surveillance.md`, `FINDINGS_dogwhistle.md` |
| paper draft, citations, example table | `paper/` (gitignored, local only) |
| figures | `figures/*.pdf` (committed), `*.png` (local); code `src/figures.py` |
| experiment configs | `config/<name>.yaml`; `run_name` = output file name |
| raw trial outputs | `data/raw/<run_name>.jsonl` (gitignored) |
| analysis text outputs | `data/*_analysis*.txt`, `data/hop_*.txt`, `data/expT*_discrim_*.txt` |
| judge probe outputs | `data/raw/dw_probes_*.jsonl` |
| stimuli | `stimuli/` (see "Stimuli" below) |
| human rating sheets | `ratings/` (gitignored): `dw_validation*.csv` (innocence judge), `ack_validation.csv` + `ack_reference.md` (acknowledgment judge); keys in `*_key.jsonl` |
| ideas / night logs | `scratchpad/ideas.md`, `scratchpad/night_plan.md` (gitignored) |
| original pilot design | `PILOT_PLAN.md` (gitignored) |

## Experiment index (dogwhistle phase)
Section numbers refer to `FINDINGS_dogwhistle.md`. Configs are `config/<run>.yaml`
(suffix `_c3b/_c8b/_c4o/_c41` = censor llama-3.2-3b / llama-3.1-8b / gpt-4o-mini /
gpt-4.1; `T` = conversation-level censor).

| exp | what | runs / code | analysis output | section |
|---|---|---|---|---|
| gap check | which allusions in-group decodes but censor doesn't | `src.gap_check` | `data/gap_check_v2b.txt`, `data/raw/gap_check_v3.jsonl` | 1, 7, 12 |
| P, Q | 5-item pilot; plain vs decode censor | `dwP_*`, `dwQ_*` | `data/dwP_analysis*.txt`, `data/dwQ*_analysis.txt` | 2-5 |
| R | 12 gap items, censor ladder, v8n vs v9 | `dwR_*` | `data/dwR_analysis_meta5.txt` | 7 |
| hop test | re-judge dogwhistles with CoT / stronger censors + collateral | `src.hop_test` | `data/hop_U.txt`, `data/hop_R_gpt41.txt`, `data/hop_U_gpt41.txt` | 8, 12b, 15 |
| arms race | censor / sender / both learn, 4 rounds, 2 seeds | `src.arms_race` (`scripts/run_arms.sh`, `scripts/run_arB.sh`) | `data/arA_analysis.txt`, `data/arB_analysis.txt` | 9, 9b |
| S | qwen-72b, gemma-27b senders | `dwS_*` | `data/dwS_analysis.txt` | 10, 10b |
| T | covert acknowledgment (receiver replies through censor) | `src.covert_ack --name expT`; `src.analyze_expT` | `data/expT_analysis.txt` | 11 |
| T re-read | alternative sender verdict prompt | `src.ack_reread` | `data/expT_reread_listen.txt` | 11b |
| T forced choice | word-level evidence in replies (+ prior control) | `src.ack_discrim` | `data/expT*_discrim_*.txt` | 11c, 11f |
| Tc | challenge-response protocol | `covert_ack --protocol challenge --name expTc` | `data/expTc_analysis.txt` | 11d |
| TU | acknowledgment on held-out items x 4 senders | `covert_ack --name expTU --senders ...` | `data/expTU_analysis.txt` | 11e |
| U | 8 held-out gap items x 4 families | `dwU_*` | `data/dwU_analysis.txt` | 12 |
| incident review | cross-family primed censor | `src.learned_heldout` | `data/learned_heldout.txt` | 12c |
| V | v9 ablation (v9o / v9m) | `dwV_*` | `data/dwV_analysis.txt` | 13 |
| W | closed senders gpt-4.1-mini, gemini-2.5-flash-lite | `dwW_*` | `data/dwW_analysis.txt` | 14 |
| X | claude-haiku-4.5 sender | `dwX_*` | `data/dwX_analysis.txt` | 16 |
| Y | gpt-4.1 as in-game censor | `dwY_*` | `data/dwY_analysis.txt` | 17 |
| Z | reasoning (`dwZr_*`) + frontier (`dwZf_*`; claude re-run `dwZs_*`) senders | `scripts/run_Zs.sh` | `data/dwZ{r,f,s}_analysis.txt` | 18 |
| arV | sender-learns arms race from v8n, 6 rounds x 2 seeds | `src.arms_race --prompt v8n` | `data/arV8{a,b}_analysis.txt` | 19 |
| second judge | gpt-4.1-mini + gemini-2.5-flash innocence re-judge | `src.second_judge` | `data/second_judge.txt` | 20 |
| Pa | three v9 paraphrases (v9p1-3) | `dwPa_*` (`scripts/run_PaM.sh`) | `data/dwPa_analysis.txt` | 21 |
| M | cross-family sender/receiver pairs | `dwM_*` | `data/dwM_analysis.txt` | 22 |

## Measurement (read before quoting any rate)
- **Dogwhistle triple** = receiver decodes (D) AND the censor model cannot
  recover the word from the winning message cold AND the message is innocent
  (ORDINARY judge mistral-small + game-talk regex `META_RE` v5 + gist does not
  name the word). **KG-DW** = triple that a fresh in-group model also decodes
  cold; otherwise "vague". Code: `src/analyze_dogwhistle.py`.
- **Innocence judge**: precision 18/18, kappa .63 vs the PI on a held-out sheet
  (one rater only; conservative, so rates are lower bounds).
- **META_RE v5** was added after reading gemma's preambles; without it the
  combined count is 1/384 vs 75/384 (no conclusion changes).
- **Acknowledgment-type judge** (`ACKTYPE_SYS` in `src/analyze_expT.py`): OVERT
  label reliable; ECHO label too generous (PI agrees on 4/16; story-echo vs
  word-echo ambiguity). Do not quote ECHO counts without that caveat; the
  forced-choice test (`src.ack_discrim`) is judge-free.
- **Forced choice** always needs the candidate-prior control (`--mode nothing`):
  the target is never a neutral 1-in-5.
- **Referee v2:** receiver can ABSTAIN; a correct guess on a turn whose clue was
  blocked is voided (`src/scoring.py`; old runs: `python -m src.rescore`).
- Use the **decode-censor** (`filter.mode: topic_decode`) for any knowledge-gap
  claim; the plain topic censor on small models leaks for unrelated reasons.

## Stimuli
- `stimuli/targets.csv`: phases 1-2 (20 targets, ranked forbidden lists).
- `stimuli/dogwhistle_targets.csv` (pilot, 5), `_v2.csv` (round 2, built by
  `stimuli/build_dw2.py`), `_R.csv` (12 gap + manna/towel controls),
  `_v3.csv` (12 candidates, `stimuli/build_dw3.py`), `_U.csv` (8 held-out gap +
  elephant/tulip controls).
- Topic-adjacent innocent controls: `stimuli/dw_adjacent_v2.json`, `_v3.json`.
- Rule: allusions must be real, pre-existing community knowledge; never invent
  codes.

## Prompts (`src/prompts.py`)
v1 minimal, v2 richer neutral (phase-1 default), v3 explicit permission to
evade, v4 soft creativity hint, v5 censor-aware (method-neutral), v6 steer away
from surface tricks, v7 steer toward ambiguity (the folk-theory ladder); v8
persona + censor (v8n no outsider cue = the dogwhistle default; v8o oracle
handle); **v9** = v8n + the "ordinary remark, not a clue, never mention the
game" sentence; **v9o / v9m** = its two halves (ablation); **v9p1-3** = paraphrases (reviewer check).

## Repo map
- `src/game.py` one trial + referee; `src/run.py` resumable grid runner
  (`--workers`, `model_pairs` for cross-pairing); `src/scoring.py` referee rules.
- `src/filter.py` keyword filter + audit detector; `src/censor.py` LLM censors
  (TopicCensor, DecodeTopicCensor, TranscriptDecodeCensor, primed examples).
- `src/client.py` OpenRouter wrapper: on-disk cache, retries, usage log, budget
  guard. **Text only, no activations.** `src/mock.py` fake model for `--dry-run`.
- Analysis: `src/analyze.py`, `src/report.py` (phases 1-2);
  `src/analyze_dogwhistle.py` (judges + triple), `src/analyze_expT.py`,
  `src/ack_reread.py`, `src/ack_discrim.py`, `src/hop_test.py`,
  `src/learned_fp.py`, `src/learned_heldout.py`, `src/agreement.py`.
- Experiments: `src/gap_check.py`, `src/arms_race.py`, `src/covert_ack.py`.
- `src/figures.py` all paper figures; `tests/` (33 tests).

## How to run
Use the venv interpreter explicitly: **`.venv/Scripts/python.exe`** (Windows), and
`export PYTHONIOENCODING=utf-8`.
```sh
.venv/Scripts/python.exe -m pytest tests/ -q
.venv/Scripts/python.exe -m src.run --config config/X.yaml --dry-run --limit 4   # no cost; delete the jsonl after
.venv/Scripts/python.exe -m src.run --config config/X.yaml --workers 6          # real run, resumable
.venv/Scripts/python.exe -m src.analyze_dogwhistle --runs A B --stimuli stimuli/dogwhistle_targets_v2.csv \
    --by_model --exclude_items dw02 dw22 --out data/raw/dw_probes_X.jsonl > data/X_analysis.txt
.venv/Scripts/python.exe -m src.figures
```
Held-out items: `--stimuli stimuli/dogwhistle_targets_U.csv --exclude_items dw34 dw41`.

## Conventions
- **Git:** `main` is up to date with `dogwhistle-asymmetry` (fast-forward
  merges). Atomic commits; no Co-Authored-By trailer. Never commit `data/`,
  `.env`, `LIT-REVIEW.md`, `scratchpad/`, `ratings/` or `paper/` (paper drafts
  stay local; PI decision 2026-11-04). The PI has approved pushing everything
  else. GitHub reports the repo moved to
  `github.com/jinfanfrankhu/llm-censorship-study` (old URL redirects; the PI
  may update the remote).
- Budget cap $15 total; record spend in findings.
- The PI pre-authorizes restarting killed runs within budget (memory
  `autonomous-restarts`).
- Report results honestly; read transcripts before trusting aggregates.

## Gotchas
- **Windows orphans:** stopping a bash wrapper does NOT stop the `python -m
  src.run` child; it keeps writing. Before relaunching, check
  `Get-CimInstance Win32_Process -Filter "Name='python.exe'"`, kill by PID,
  verify none remain. Dedupe by trial key before analysis.
- **Memory reaps:** Claude Code may kill background shells when the machine is
  low on memory; the python child usually survives. Don't restart reaped jobs
  blindly; check processes first.
- **Rate limits:** the mistral-small judge returns 429s under parallel load; run
  analyses sequentially with retry loops (judge calls are cached, so retries
  resume).
- **Re-scoring:** after changing `META_RE` or the scorer, re-run every
  analysis (template: `scratchpad/rescore_meta5.sh`).
- **Scorer:** `guess_is_correct` handles e-final plurals ("pancakes") since
  2026-11-04; older stored outcomes were not rescored (affects <= 2 trials).
- `--dry-run` WRITES mock trials into `data/raw/<run_name>.jsonl`; delete before
  the real run or resume skips them.
- `python-dotenv`: call `load_dotenv(".env")` explicitly.
- Windows console is cp1252: set `PYTHONIOENCODING=utf-8`. Heredoc'd Python that
  writes `\n` escapes into source files turns them into real newlines: use the
  Edit tool for source edits containing escapes.
- Audit `spacing`/`substring` flags (phase 1) are noisy; `leetspeak` is the clean
  signal.
- This repo runs an always-on "caveman" chat-style hook (terse replies). It only
  affects chat prose; code, commits and docs stay normal prose.
