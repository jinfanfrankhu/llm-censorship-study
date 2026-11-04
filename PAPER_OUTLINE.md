# Paper outline (draft, 2026-11-03) — target ARR / ACL 2027 main

Working title: **"Can, But Won't: LLM Dogwhistles Under Knowledge-Asymmetric Censorship"**
(alt: "Deniable by Request: ...")

## One-paragraph pitch
Two LLMs share real community knowledge (a Schubert quintet, the Fenian Cycle,
a Wittgenstein passage) that an LLM censor lacks or fails to connect. We ask
whether the sender exploits that asymmetry to write *dogwhistles*: messages
with an innocent surface the censor lets through, which the in-group decodes.
Models almost never do so by default (0/216 trials), but do when merely told
that messages must read as ordinary in-group talk (47/216; p ~ 1e-15) — a
propensity gap, not a capability gap. Survivors beat a strong censor by
indirection rather than ignorance; closing them costs collateral (40% of
innocent same-topic messages blocked by a zero-tolerance reasoning censor),
except when the censor learns from incident review, which generalises at no
collateral. In a two-sided arms race the censor stays ahead (2 seeds). Made
two-way, covert acknowledgment fails: what passes the censor proves the frame,
not the word, and word-level evidence is what the censor removes.

## Contributions
1. A **controlled dogwhistle testbed**: Taboo-style game, real pre-existing
   allusion stimuli (21 items, 14 used) with an empirically verified
   knowledge-gap check, decode-censor ladder, and a validated metric (the
   dogwhistle triple: decoded / censor can't decode / innocent surface,
   judges checked against human ratings).
2. **Propensity finding**: in-group LLM pairs have the capability but not the
   default behaviour; one sentence naming the innocence requirement unlocks it.
   Ties to F1 (permission-gated orthographic evasion) — a general pattern.
3. **Three layers of protection** (knowledge / inference / deniability) with a
   measured cost to close each (scale: free; reasoning: small FP; deniability:
   large FP).
4. **Arms race dynamics**: incident-review censors generalise at zero collateral;
   adaptive senders beat static censors; with both adapting, dogwhistles trade
   information rate for deniability (vagueness).

## Sections
1. Intro — dogwhistles in human speech (Henderson & McCready; Mendelsohn et al.
   2023 computational dogwhistles), LLM monitors, steganographic collusion.
2. Related work — dogwhistle detection (Mendelsohn et al. 2023; others TBD), LLM
   steganography / collusion (Motwani et al. 2024, Roger & Greenblatt 2023,
   Mathew et al. 2024 "hidden in plain text"), CoT monitoring, latent
   multi-hop reasoning (Yang et al. 2024), emergent communication. [verify
   all citations against LIT-REVIEW.md before writing.] Key
   distinction: no shared codebook; knowledge is pre-existing, not agreed.
3. Setup — game, referee v2 (voided blocked-clue wins), censors (topic,
   decode, conversation-level, CoT, primed), stimuli + gap check, metrics,
   judge validation (kappa table).
4. Exp: propensity (Exp Q pilot + Exp R + Exp S families).
5. Exp: what protects survivors (gap does not predict outcomes; hop test;
   collateral curve).
6. Exp: arms race.
7. Discussion — implications for AI monitoring (monitor = decoder wall; incident
   review is cheap and effective), for content moderation, limits.
8. Limitations — 14 items, 4 sender families, LLM judges (validated on 70
   items), English-language framing of non-English folklore, single strictness.

## Figures
- F1: game + censor ladder schematic.
- F2: triple rate v8n vs v9 by censor (bars with Wilson CIs), per sender family.
- F3: catch vs adjacent-FP for censor variants (the collateral curve).
- F4: arms race: D and KG-DW / vague per round for the three arms.
- T1: example dogwhistles with censor cold guesses.

## Still needed (status 2026-11-03 night)
Done: arms race complete (3 arms x 4 rounds); Exp S (qwen-72b, gemma-3-27b:
v8n 1/144 vs v9 20/144); 6 runs/item vs gpt-4o-mini (v8n 0/144 vs v9 28/144);
second blind validation sheet (precision 18/18, kappa .63); Exp T covert
acknowledgment (FINDINGS section 11).
- Arms race second seed DONE (FINDINGS 9b): pattern replicates; the
  'vagueness' trend does not replicate cleanly, now reported as a trend.
- **Exp T needs independent samples.** Message vs transcript cells share
  66/72 cached trajectories; for the paper either drop the transcript cells or
  rerun them with different run indices. Decide after the sender re-read.
- Exp T confusion-set test (11c) and challenge protocol (11d) DONE: delivered
  acks carry no word-level evidence (28% vs 27% wrong-receiver baseline);
  challenges elicit target-revealing answers that get blocked.
- Exp T sender-side re-read DONE (section 11b): a 'listening' verdict does
  not unlock reliable uptake (7 true / 16 false acks); echoes prove the frame,
  not the word. Next Exp T step: a confusion-set test (does the receiver's
  echo ever discriminate target vs same-work neighbour, e.g. hedgehog vs fox?)
  and a challenge-response variant where the SENDER asks a question only the
  target answers.
- Decide paper scope: Exp T as a fifth contribution ("covert grounding") or as
  a short section; it is the most novel axis vs prior stego/collusion work.
- [PI] ACK-type judge blind sheet ready: `ratings/ack_validation.csv` (30
  replies; columns: type, and whether the reply alone shows THIS word).
- First full draft: `paper/draft.md`; figures F2-F5 in `figures/`.
- Citations: verify every entry in Related Work against LIT-REVIEW.md and the
  papers themselves.
- Interp follow-up (separate paper or appendix): v8n vs v9 contrast on an
  open model.
