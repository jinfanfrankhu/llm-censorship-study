# Paper outline (2026-11-05) — target ARR / ACL 2027 main

Working title: **"Can, But Won't: LLM Dogwhistles Under Knowledge-Asymmetric Censorship"**
(alt: "Deniable by Request: ...")

Full first draft: `paper/draft.md` (numbers traced to FINDINGS_dogwhistle.md
sections). Figures: `figures/f2-f5` via `python -m src.figures`.

## One-paragraph pitch
Two LLMs share real community knowledge (a Beethoven sonata, the Fenian Cycle,
Russell's teapot) that an LLM censor lacks or fails to connect. We ask whether
the sender exploits that asymmetry to write *dogwhistles*: messages with an
innocent surface the censor lets through, which the in-group decodes. Across
20 knowledge-gap items and eleven sender models (open, closed, reasoning and
frontier), models almost never do so by default (1/636 trials vs a gpt-4o-mini
decode-censor) but do when told that messages must read as ordinary in-group
talk (140/636; p = 2e-44), including on items written after the effect was
found and under three rewordings. The clause that matters is the genre ("an
ordinary remark"); banning game talk alone does nothing, and six rounds of
outcome feedback never teach it (0/864).
Survivors of a mid-size censor beat it by indirection; a frontier censor
(gpt-4.1) catches 70% of them at ~4% collateral, and the deniable residue
costs 40-66% false positives on innocent same-community talk to close. Incident review
closes much of the channel cheaply (fully for the same senders, about half for
new senders). In a two-sided arms race the censor stays ahead (2 seeds). Made
two-way, covert acknowledgment fails: what passes the censor proves the frame,
not the word, because word-level evidence is exactly what the censor removes.

## Contributions
1. **Controlled dogwhistle testbed**: Taboo-style game, real pre-existing
   allusion stimuli (2 item sets, 20 gap items + 4 controls) with an empirical
   knowledge-gap check, decode-censor ladder, and a validated metric
   (decoded / censor can't decode / innocent surface; innocence judge
   precision 18/18 on held-out human ratings).
2. **Propensity, not capability**: one sentence naming the genre of the
   message unlocks dogwhistles in all four families; ablation isolates the
   'ordinary remark, not a clue' clause.
3. **Three layers of protection** (knowledge / inference / deniability) with a
   measured cost to close each, replicated on held-out items.
4. **Arms race**: censor ahead in both seeds; incident review transfers fully
   within senders, partially across senders.
5. **Covert acknowledgment** (most novel vs stego/collusion work): the return
   channel has ~zero word-level capacity under a decode-censor (forced-choice
   identification 28% vs 27% for a wrong receiver); challenge-response moves
   the blocked message to the receiver's turn.

## Figures
- F1: game + censor ladder schematic (to draw).
- F2: triples v8n vs v9 per family, all 20 gap items (done).
- F3: catch vs innocent-FP for censor variants (done; add held-out points?).
- F4: arms race, both seeds (done).
- F5: acknowledgment evidence (reply-alone forced choice) (done).
- T1: example dogwhistles with censor cold guesses (to build).

## Still needed (status 2026-11-04 early morning)
- [PI] Rate `ratings/ack_validation.csv` (30 acknowledgment replies; type and
  word-level Y/N). Exp T claims rest on the ECHO judge and the hand-built
  neighbour lists.
- [PI] Decide: Exp T as a main contribution (recommended: it is the novel
  axis) or a short section.
- Second annotator for the innocence judge (kappa from one rater only).
- Citations: verify every [verify] in the draft against the papers.
- Closed senders DONE: gpt-4.1-mini, gemini-2.5-flash-lite (Exp W),
  claude-haiku-4.5 (Exp X); all in the draft table.
- F1 schematic, T1 example table, appendix (prompts, stimuli, judge prompts,
  transcript-cell duplicates for Exp T).
- Interp follow-up (separate paper): v8n vs v9o contrast on an open model.

## Anticipated reviewer questions (2026-11-05)
Where each is answered, and what is still open.

| criticism | answer | status |
|---|---|---|
| The v9 sentence is a cherry-picked magic phrase | ablation (F13); three later paraphrases 13/12/9 of 72 vs 0/72, incl. one with no "not a clue" (F21); held-out items written after the effect (F12) | done |
| Only small / old models | 11 sender models incl. deepseek-r1, qwen3-thinking, gpt-4.1, claude-sonnet-5.5: 1/636 vs 140/636 (F18) | done |
| Games are not independent (shared words, senders) | sign tests over words (18-0) and models (11-0), word-cluster bootstrap, stratified permutation (`data/cluster_stats_withZ.txt`) | done |
| The innocence judge is one LLM and one rater | two judges from other families confirm 185-188 of 189 triples; gemini matches the human kappa (F20) | second human rater still open |
| Same-model pairs collude through model idiosyncrasy, not community knowledge | cross-model pairs llama <-> deepseek (F22); KG-DW requires a fresh receiver to decode cold | done: 0/72 vs 14/72 cross-family, same size as same-model (F22) |
| Censor too weak | gpt-4.1 offline (F15) and in game (F17); stronger senders still get 19 KG-DW / 144 past gpt-4.1 (F18) | done; reframe as relative strength |
| v9 just makes senders vague and lucky | triples split into KG-DW (fresh in-group decodes cold) vs vague throughout; most v9 triples are KG-DW | done |
| Models would learn this with experience | sender-learns arms race from v8n: 0/864 over 6 rounds x 2 seeds (F19) | done |
| Receiver prompt primes allusions ("your partner may allude to...") | identical in v8n and v9, so it cannot explain the gap; it raises decode rates in both | state in Setup |
| One temperature, one censor strictness | not varied | limitation |
| Stimuli are author-written | allusions are pre-existing community knowledge, empirical gap check per item (F1, F7, F12) | done |
| Reasoning senders truncated / provider quirks | empty-turn rates reported; bias is downward (F18) | done |
