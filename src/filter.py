"""Blocking filter + audit detector for the censorship pilot.

Two independent components:

1. ``BlockingFilter`` -- redacts forbidden words before the receiver sees a
   message. This affects the game. Whole-word, case-insensitive matching
   against an explicit, reviewable variant list (NOT a stemmer), so behavior
   is predictable.

2. ``audit_flags`` -- a read-only detector that flags likely evasion attempts
   (leetspeak, inserted spacing/punctuation, substring smuggling, near-miss
   spellings). It NEVER blocks; it only logs for later analysis.

Policy decisions (documented, see tests):
- Whole-word matching only. We do NOT block a forbidden word that appears as a
  substring of an unrelated longer word (``keys`` does not fire on ``monkeys``).
  Substring smuggling is instead surfaced by the audit detector.
- Inflections are enumerated explicitly per word (plural/possessive, -ed, -ing,
  -er) so a reviewer can read exactly what is blocked.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


# --------------------------------------------------------------------------- #
# Variant generation (blocking)
# --------------------------------------------------------------------------- #
def word_variants(word: str) -> set[str]:
    """Return the explicit set of surface forms blocked for one word.

    Covers: the word itself, plural/possessive (-s, -es, 's), -ed, -ing, -er,
    plus the usual spelling adjustments for words ending in ``e`` or ``y``.
    Deliberately NOT a stemmer -- the returned set is meant to be eyeballed.
    """
    w = word.lower().strip()
    variants = {w}
    variants.update({w + suf for suf in ("s", "es", "'s", "ed", "ing", "er")})
    if w.endswith("e"):
        stem = w[:-1]
        variants.update({stem + suf for suf in ("ed", "ing", "er")})
    if w.endswith("y") and len(w) > 1 and w[-2] not in "aeiou":
        stem = w[:-1]
        variants.update({stem + suf for suf in ("ies", "ied", "ier")})
    return variants


def build_blocklist(target: str, forbidden: list[str]) -> dict[str, str]:
    """Map every blocked surface form -> its canonical word (lowercased)."""
    blocklist: dict[str, str] = {}
    for word in [target, *forbidden]:
        canonical = word.lower().strip()
        for variant in word_variants(word):
            # First writer wins; canonical words are distinct enough that
            # collisions are rare and harmless for logging.
            blocklist.setdefault(variant, canonical)
    return blocklist


@dataclass
class FilterResult:
    filtered: str
    hits: list[str]  # canonical words that were redacted, in order of appearance


class BlockingFilter:
    """Redacts forbidden surface forms from a message."""

    def __init__(self, target: str, forbidden: list[str], redaction: str = "per_char"):
        if redaction not in ("per_char", "fixed"):
            raise ValueError(f"unknown redaction mode: {redaction!r}")
        self.redaction = redaction
        self.blocklist = build_blocklist(target, forbidden)
        # Longest variants first so "piano's" wins over "piano" at the same spot.
        variants = sorted(self.blocklist, key=len, reverse=True)
        # Boundaries: not preceded by a word char or apostrophe; not followed by
        # a word char. This keeps possessives intact and avoids substring hits.
        self._pattern = re.compile(
            r"(?<![\w'])(" + "|".join(re.escape(v) for v in variants) + r")(?![\w])",
            re.IGNORECASE,
        )

    def apply(self, text: str) -> FilterResult:
        hits: list[str] = []

        def _replace(m: re.Match) -> str:
            token = m.group(0)
            hits.append(self.blocklist[token.lower()])
            if self.redaction == "per_char":
                return "#" * len(token)
            return "[REDACTED]"

        filtered = self._pattern.sub(_replace, text)
        return FilterResult(filtered=filtered, hits=hits)


# --------------------------------------------------------------------------- #
# Audit detector (logs only, never blocks)
# --------------------------------------------------------------------------- #
_LEET = str.maketrans({"0": "o", "3": "e", "4": "a", "1": "i", "5": "s", "@": "a"})


def _normalize_leet(s: str) -> str:
    return s.lower().translate(_LEET)


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if abs(len(a) - len(b)) > 1:
        return 2  # we only care about <= 1, so short-circuit
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def audit_flags(text: str, target: str, forbidden: list[str]) -> list[dict]:
    """Return evasion flags for a *raw* message. Never mutates game state.

    Each flag: ``{"type", "word", "evidence"}`` where ``type`` is one of
    ``leetspeak``, ``spacing``, ``substring``, ``near_miss``.
    """
    words = [w.lower().strip() for w in [target, *forbidden]]
    blocked_surface = set()
    for w in words:
        blocked_surface |= word_variants(w)

    flags: list[dict] = []
    lower = text.lower()
    tokens = re.findall(r"\S+", lower)

    # --- leetspeak: a token normalizes onto a blocked surface form ---------- #
    for tok in tokens:
        stripped = tok.strip(".,!?;:'\"()[]{}")
        norm = _normalize_leet(stripped)
        if norm != stripped and norm in blocked_surface:
            flags.append({"type": "leetspeak", "word": norm, "evidence": tok})

    # --- spacing/punctuation insertion: "p i a n o", "p.i.a.n.o" ------------ #
    # Collapse runs of single letters separated by spaces/punctuation.
    for w in words:
        if len(w) < 4:
            continue
        # letters of w separated by one or more non-word chars
        sep = r"[\s\.\-_,]*".join(re.escape(c) for c in w)
        for m in re.finditer(sep, lower):
            if m.group(0) != w:  # it was actually spaced/punctuated out
                flags.append({"type": "spacing", "word": w, "evidence": m.group(0).strip()})

    # --- substring smuggling: blocked word inside a longer alpha token ------ #
    for tok in tokens:
        stripped = re.sub(r"[^a-z]", "", tok)
        if not stripped:
            continue
        for w in words:
            if len(w) >= 4 and w in stripped and w != stripped:
                flags.append({"type": "substring", "word": w, "evidence": tok})

    # --- near-miss: edit distance <= 1 from a blocked surface form ---------- #
    seen_near = set()
    for tok in tokens:
        stripped = re.sub(r"[^a-z]", "", tok)
        if not stripped or stripped in blocked_surface:
            continue  # exact forms are caught by the blocking filter already
        for surface in blocked_surface:
            if len(surface) >= 4 and _levenshtein(stripped, surface) == 1:
                keypair = (stripped, surface)
                if keypair not in seen_near:
                    seen_near.add(keypair)
                    flags.append({"type": "near_miss", "word": surface, "evidence": tok})
                break

    return flags
