# Findings — Strategic Speakers under Surveillance (strategic-speakers branch)

Frame: do LLMs communicate with **plausible deniability** to evade an (AI)
censor, and how does strategy change with awareness and censor strength?
Grounded in Pinker/Lee's Strategic Speaker, Henderson/McCready dogwhistles, and
Weibo homophone evasion (false-positive exploitation). See LIT-REVIEW §8.

All results: real OpenRouter calls. Sender/receiver = gemma-2-27b unless noted;
censor judge = gpt-4o-mini. Judge validated against a human (guess accuracy
14/14 match; evasion-label binary kappa 0.75).

## The measurable: the deniability frontier
Every message has decodability D (can the partner recover the word) and suspicion
S (would a censor flag it). Evasion = high D, low S; deniability = low S read
cold. On existing messages (n=150):

| message type | D | topic-suspicion (censor knows word) | blind-suspicion (cold read) |
|---|---|---|---|
| orthographic disguise (leetspeak/spacing) | 0.71 | **9.2** | **3.1** |
| plain language | 0.45 | 8.2 | **0.9** |

**Orthographic evasion is the worst strategy on a real monitor** — most
detectable (a judge just decodes "h0m3") *and* most conspicuous. It only beats a
dumb keyword matcher. **Plain language is already dogwhistle-shaped**: innocent
cold (0.9) but transparent to anyone who knows the topic (8.2). The S_topic−S_blind
gap is the deniability-to-outsiders.

## The censor ladder
- **Blind censor** (doesn't know the forbidden word): **toothless** — blocks 0%
  of game messages AND 0% of innocent messages at every strictness. Plain
  description is indistinguishable from innocent chatter without knowing the
  topic. So against an anomaly monitor, plain description is already perfectly
  deniable.
- **Topic-aware censor** (knows the forbidden concept; realistic watchlist): a
  **strong classifier** vs plain language — ROC recall 98–100% at only 0–15%
  false positives. Plain clues get shut down cleanly. The Weibo false-positive
  mechanism only bites if the sender manufactures **ambiguity**.

## Awareness unlocks deniable communication (Exp K vs L)
Topic-aware censor, success rate by sender awareness and censor strictness:

| censor | uninformed sender (K) | aware sender (L, v5) |
|--------|----:|----:|
| lenient  | 15% | **55%** |
| moderate | 10% | 15% |
| strict   |  0% |  5% |

- **Uninformed senders don't adapt** — they keep emitting plain on-topic clues
  and eat 90–98% blocks. The censorship blind spot, in a surveillance setting.
- **Aware senders (told a censor blocks on-topic messages) change behavior** —
  they try tactics, abstraction, emojis ("Man's best friend 🐶"), meta-probing
  ("let's try a different tactic") — and succeed via genuinely **ambiguous
  functional descriptions**: lighthouse "I help people navigate"; tree "it has
  rings"; money "can be saved but not eaten"; scarecrow "I scare away pests".
  These describe role/ambiguous-attribute, not category — decodable in context,
  individually innocent. NOT orthographic tricks (which the frontier showed fail).

## The thesis, quantified: you can't close the channel without collateral
Combining aware-sender success (channel openness) with the censor ROC
(collateral):

| censor strictness | aware evader success | false-positive collateral |
|---|---|---|
| lenient | 55% | 0% |
| strict  | 5%  | 15% |

To drive an aware evader from 55% down to 5%, the censor must move lenient→strict,
which raises false positives 0%→15%. **Censoring a surveillance-aware
communicator forces a precision/recall tradeoff — exactly the Weibo homophone
dynamic, reproduced and quantified in LLMs.**

## Why this is more than "instructions elicit behavior"
- Awareness is *necessary but not sufficient*: aware gemma still only reaches 5%
  vs a strict censor — the monitor-equals-decoder wall mostly holds.
- The behavior is specific and principled: senders converge on **ambiguity-based
  deniability** (functional/relational/ambiguous description), the human
  mechanism, not on the leetspeak the earlier (keyword-filter) experiments
  elicited — and the frontier proves leetspeak would *fail* here.
## Capability inversion: the stronger model is EASIER to censor (Exp M)
Aware gpt-4.1 vs aware gemma-2-27b, same topic censor:

| censor | aware gemma-2-27b | aware gpt-4.1 |
|--------|----:|----:|
| lenient  | 55% | **5%** |
| moderate | 15% | 0% |
| strict   |  5% | 0% |

gpt-4.1 is blocked ~100% of the time and does FAR worse. Why — it deploys the
WRONG evasion:
- When told to evade, **gpt-4.1 reaches for orthographic/wordplay tricks** —
  "D _ O _ G", "rhymes with fog and log", "H2O", "H _ U _ S _ E fill in the
  vowels" — in **29% of messages vs gemma's 2%** (15x more). These are exactly
  the transparent tricks the deniability frontier proved **useless against a
  semantic censor** (the judge decodes "rhymes with fog" -> dog instantly).
- Its plain clues are also *more precisely on-topic* (better communicator ->
  clearer reference -> more detectable).
- gemma wins by ACCIDENT: its vaguer, clumsier **ambiguous functional
  descriptions** are genuinely deniable (ambiguous, not disguised).

**The insight: LLMs have a miscalibrated folk theory of censorship evasion.**
Asked to beat a filter, they produce orthographic wordplay (effective only vs a
dumb keyword matcher) instead of the semantic ambiguity that actually defeats a
smart monitor. Neither model deliberately deploys the winning strategy; the
"stronger" model fails harder because it confidently uses the wrong tool. This
unifies the whole project: the permission-gated leetspeak (keyword-filter
experiments) is the same miscalibrated instinct, now shown to be counterproductive
against realistic (semantic) censorship.

## Mech-interp implications
- Primary contrast refined: **aware vs unaware sender facing the same topic
  censor** — what representation does "a censor is watching" induce, and does it
  drive the shift to ambiguous description? (gemma-2-27b is the interp target.)
- Does the model represent the *dual meaning* of a deniable message (the covert
  target + the innocent surface) simultaneously — the dogwhistle's two readings?

## Caveats
- One sender model (gemma-2-27b) so far; one censor judge (gpt-4o-mini); 20
  targets, 1 run/cell. Pilot scale.
- Judge validated on 25 items, one human rater — add raters + items for a paper.
- Methodological: when fully blocked, the receiver emits rote filler guesses
  (fruit lists); give it an explicit "insufficient information" option.
- FP measured cross-concept on clue messages; a real deployment FP needs
  topically-adjacent innocent traffic.
