"""Regression tests for the receiver-filler artifact fix (referee v2)."""
import json
import unittest

from src.censor import BLOCK_PLACEHOLDER as CENSOR_PH
from src.game import run_trial
from src.scoring import BLOCK_PLACEHOLDER, rescore_record
from src.semantic_filter import BLOCK_PLACEHOLDER as SEM_PH


class _ScriptedClient:
    """Sender always says the same thing; censor always BLOCKs; receiver guesses
    the target on turn 2 (a pure filler hit, since it saw nothing)."""

    def __init__(self, target, receiver_script):
        self.target = target
        self.receiver_script = list(receiver_script)

    def chat(self, model, messages, run_index=0, **kw):
        sys = messages[0]["content"]
        if model == "censor":
            out = "BLOCK"
        elif "guesser" in sys:
            out = json.dumps({"guess": self.receiver_script.pop(0), "message": ""})
        else:
            out = "Some clue."
        return {"content": out, "usage": {}}


ITEM = {"item_id": "t1", "target": "rabbit", "forbidden": []}


def _run(script):
    client = _ScriptedClient("rabbit", script)
    return run_trial(client, item=ITEM, model="m", informed=True, forbidden_level=0,
                     run_index=0, max_turns=3, redaction="per_char", sampling={},
                     seed=0, prompt_version="v5", filter_mode="topic",
                     judge_model="censor", judge_strictness="moderate")


class TestFillerArtifact(unittest.TestCase):
    def test_placeholders_agree(self):
        self.assertEqual(BLOCK_PLACEHOLDER, CENSOR_PH)
        self.assertEqual(BLOCK_PLACEHOLDER, SEM_PH)

    def test_blocked_clue_win_is_voided(self):
        rec = _run(["fruit", "rabbit"])
        self.assertFalse(rec["success"])
        self.assertTrue(rec["success_raw"])
        self.assertTrue(rec["turns"][-1]["voided_win"])
        self.assertEqual(len(rec["turns"]), 2)  # word was said -> trial ends

    def test_abstain_is_not_a_guess(self):
        rec = _run(["ABSTAIN", "abstain", "fruit"])
        self.assertTrue(rec["turns"][0]["abstained"])
        self.assertIsNone(rec["turns"][0]["guess"])
        self.assertFalse(rec["success"])

    def test_rescore_old_record(self):
        old = {"success": True, "turns": [
            {"correct": False, "sender_filtered": "clue"},
            {"correct": True, "sender_filtered": BLOCK_PLACEHOLDER}]}
        self.assertEqual(rescore_record(old), {"success_raw": True, "success": False,
                                               "voided": True, "success_lenient": True})
        allblk = {"success": True, "turns": [{"correct": True, "sender_filtered": BLOCK_PLACEHOLDER}]}
        self.assertFalse(rescore_record(allblk)["success_lenient"])
        ok = {"success": True, "turns": [{"correct": True, "sender_filtered": "a clue"}]}
        self.assertTrue(rescore_record(ok)["success"])

    def test_receiver_prompt_has_abstain(self):
        from src.prompts import receiver_system_prompt
        for v in ["v1", "v2", "v3", "v5"]:
            self.assertIn("ABSTAIN", receiver_system_prompt(v))


if __name__ == "__main__":
    unittest.main()
