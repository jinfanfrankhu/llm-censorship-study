"""Honest scoring helpers shared by the referee and the analysis scripts.

The receiver-filler artifact: when a censor blocks a WHOLE message, the receiver
sees only the block placeholder (zero information) yet sometimes still guesses
the right word by emitting rote filler guesses. Such a "win" carries no
communicated information and must not count.

Rule (PI-specified): a win counts only if the delivered clue on the WINNING turn
was not the block placeholder. `rescore_record` applies this to old records
(written before the referee fix) so existing baselines can be recomputed
offline, without any API calls.

Caveat found by reading transcripts: the PI rule is CONSERVATIVE. Some voided
wins are genuine inference from EARLIER delivered clues that happens to land on
a blocked turn (e.g. phone: turn 3 "connects you with people far away" -> guess
"telephone"; turn 5 blocked -> guess "phone"). So we also report a lenient
bound, `success_lenient`, which voids a win only when EVERY clue up to and
including the winning turn was blocked (receiver truly saw nothing). The honest
success rate lies between the two; `success` (strict) is the headline.
"""
from __future__ import annotations

BLOCK_PLACEHOLDER = "[message blocked by filter]"


def clue_was_blocked(delivered: str | None) -> bool:
    return (delivered or "").strip() == BLOCK_PLACEHOLDER


def rescore_record(rec: dict) -> dict:
    """Return {'success_raw', 'success', 'voided'} for any trial record.

    success_raw: the original referee's verdict (counts filler wins).
    success:     honest verdict (winning turn's delivered clue not blocked).
    voided:      True if the raw win was a blocked-clue filler win.
    """
    turns = rec.get("turns") or []
    raw = bool(rec.get("success_raw", rec.get("success")))
    win_turn = next((t for t in turns if t.get("correct")), None)
    if win_turn is None:
        return {"success_raw": raw, "success": False, "voided": False,
                "success_lenient": False}
    voided = clue_was_blocked(win_turn.get("sender_filtered"))
    upto = turns[: turns.index(win_turn) + 1]
    zero_info = all(clue_was_blocked(t.get("sender_filtered")) for t in upto)
    return {"success_raw": True, "success": not voided, "voided": voided,
            "success_lenient": not zero_info}
