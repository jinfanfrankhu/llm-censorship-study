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
collateral. In a two-sided arms race the censor stays ahead and dogwhistles
degrade into vagueness.

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

## Still needed (status 2026-11-03 evening)
- [running] arms race completion; Exp S (qwen-72b, gemma-3-27b); 6 runs/item
  for v8n/v9 vs gpt-4o-mini.
- [PI] second blind sheet `ratings/dw_validation2.csv` (30 items; ignore the
  empty `community` column).
- arms race replicate (second seed) if the 'both' arm stays noisy.
- Interp follow-up (separate paper or appendix): v8n vs v9 contrast on an
  open model.
