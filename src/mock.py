"""Fake model with the same interface as ``client.Client`` for zero-cost dry runs.

Selected via ``--dry-run``. It exercises the full pipeline (filter, feedback,
receiver JSON parsing + retry, referee success/failure) without any API call.

Behavior is deterministic given the message content:
- As a SENDER it returns varied clues, some containing forbidden words (to
  trigger the blocking filter) and some with leetspeak/spacing (to trigger the
  audit detector).
- As a RECEIVER it returns valid guess JSON. To guarantee the success path is
  covered in a dry run, it remembers targets seen in sender prompts and guesses
  correctly on a later turn; earlier turns guess wrong. It also emits one
  malformed JSON reply to exercise the parse-retry branch, then valid JSON when
  re-asked.
"""
from __future__ import annotations

import hashlib
import json
import re

_CLUES = [
    "Think of a large object you might find in a concert hall.",
    "It has black and white levers you press with your fingers.",
    "A composer sits in front of it. Involves keys and music.",  # trips the filter
    "p i a n o — sounds like what you do to listen (spacing hint).",  # trips audit
    "Big wooden box, 88 of those pressable things, makes sound.",
]

_WRONG_GUESSES = ["keyboard", "organ", "harp", "guitar", "drum", "violin"]


def _seed(messages: list[dict]) -> int:
    blob = json.dumps(messages, sort_keys=True, ensure_ascii=False)
    return int(hashlib.sha256(blob.encode("utf-8")).hexdigest(), 16)


class MockClient:
    def __init__(self, cache_dir: str = "cache", budget_usd_max: float = 10.0):
        self.budget_usd_max = budget_usd_max
        self.spend_usd = 0.0
        self.call_log: list[dict] = []
        self._last_target: str | None = None

    @staticmethod
    def _is_receiver(messages: list[dict]) -> bool:
        return any(
            m.get("role") == "system" and "respond with JSON" in m.get("content", "")
            for m in messages
        )

    @staticmethod
    def _turn_index(messages: list[dict]) -> int:
        return sum(1 for m in messages if m.get("role") == "user")

    def _sender_reply(self, messages: list[dict]) -> str:
        for m in messages:
            if m.get("role") == "system":
                found = re.search(r'secret word is "([^"]+)"', m["content"])
                if found:
                    self._last_target = found.group(1).lower()
        turn = self._turn_index(messages)
        return _CLUES[(turn - 1) % len(_CLUES)] if turn >= 1 else _CLUES[0]

    def _receiver_reply(self, messages: list[dict]) -> str:
        seed = _seed(messages)
        turn = self._turn_index(messages)
        last = messages[-1].get("content", "") if messages else ""
        asking_for_valid = "valid JSON" in last

        # Emit one malformed reply on turn 1 (unless it's the re-ask) to exercise
        # the parse-retry branch.
        if turn == 1 and not asking_for_valid:
            return "I think the answer is keyboard"  # not JSON

        # Guess correctly from turn 3 onward if we know the target; else wrong.
        if turn >= 3 and self._last_target:
            guess = self._last_target
        else:
            guess = _WRONG_GUESSES[seed % len(_WRONG_GUESSES)]
        return json.dumps({"guess": guess, "message": "is it close to this?"})

    def chat(self, model: str, messages: list[dict], run_index: int = 0, **params) -> dict:
        if self._is_receiver(messages):
            content = self._receiver_reply(messages)
        else:
            content = self._sender_reply(messages)
        record = {
            "model": f"mock::{model}",
            "model_version": "mock",
            "params": params,
            "run_index": run_index,
            "content": content,
            "finish_reason": "stop",
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0},
            "latency_s": 0.0,
            "timestamp": 0.0,
            "cached": False,
        }
        self.call_log.append(record)
        return record
