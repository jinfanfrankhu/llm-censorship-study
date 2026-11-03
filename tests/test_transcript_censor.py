"""TranscriptDecodeCensor: decodes the accumulated delivered history, not one message."""
import unittest

from src.censor import TranscriptDecodeCensor


class _Client:
    """Topic judge always ALLOWs; the decoder names 'rabbit' only once it sees
    both the moon message and the jade message together."""

    def __init__(self):
        self.systems = []

    def chat(self, model, messages, run_index=0, **kw):
        sys, user = messages[0]["content"], messages[1]["content"]
        self.systems.append(sys)
        if "censor" in sys:
            return {"content": "ALLOW"}
        both = "moon" in user and "jade" in user
        return {"content": "rabbit" if both else "lamp"}


class TestTranscriptCensor(unittest.TestCase):
    def test_pieces_add_up(self):
        c = TranscriptDecodeCensor("rabbit", _Client(), "m", accept=["rabbit"])
        self.assertFalse(c.apply("Lovely moon tonight.").hits)
        self.assertEqual(c.history, ["Lovely moon tonight."])
        self.assertTrue(c.apply("Like the jade one in the story.").hits)
        self.assertEqual(len(c.history), 1)  # blocked messages are not delivered

    def test_examples_reach_topic_judge(self):
        cl = _Client()
        c = TranscriptDecodeCensor("rabbit", cl, "m", accept=["rabbit"],
                                   examples=["Chang'e's companion"])
        c.decide_block("hello")
        self.assertIn("Chang'e's companion", cl.systems[0])
        self.assertTrue(cl.systems[0].rstrip().endswith("BLOCK or ALLOW."))


if __name__ == "__main__":
    unittest.main()


class TestReplyMatcher(unittest.TestCase):
    def test_multiword(self):
        from src.game import reply_names_target
        self.assertTrue(reply_names_target("To the Lighthouse", ["lighthouse"]))
        self.assertTrue(reply_names_target("ToTheLighthouse", ["lighthouse"]))
        self.assertTrue(reply_names_target("Moonlight Sonata.", ["moonlight"]))
        self.assertTrue(reply_names_target("Rabbits", ["rabbit", "hare"]))
        self.assertFalse(reply_names_target("Carpet", ["carp"]))
        self.assertFalse(reply_names_target("", ["carp"]))
