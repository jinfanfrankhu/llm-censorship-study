"""Offline tests for the blocking filter and audit detector (stdlib only).

Run with either:
    python -m unittest discover -s tests -v
    python -m pytest tests/ -v
"""
import unittest

from src.filter import BlockingFilter, audit_flags, build_blocklist, word_variants


TARGET = "piano"
FORBIDDEN = ["music", "keys", "instrument", "play", "notes"]


def filt(text, redaction="per_char"):
    return BlockingFilter(TARGET, FORBIDDEN, redaction=redaction).apply(text)


class TestBlockingFilter(unittest.TestCase):
    def test_exact_match(self):
        r = filt("I love the piano")
        self.assertEqual(r.filtered, "I love the #####")
        self.assertEqual(r.hits, ["piano"])

    def test_case_insensitive(self):
        r = filt("PIANO and Music")
        self.assertIn("#####", r.filtered)
        self.assertEqual(sorted(r.hits), ["music", "piano"])

    def test_inflections(self):
        # plural, -ing, -s on forbidden words
        r = filt("keys playing notes")
        self.assertEqual(r.hits, ["keys", "play", "notes"])
        self.assertNotIn("keys", r.filtered.lower())
        self.assertNotIn("playing", r.filtered.lower())

    def test_possessive(self):
        r = filt("the piano's lid")
        self.assertEqual(r.hits, ["piano"])
        self.assertIn("lid", r.filtered)
        self.assertNotIn("piano", r.filtered.lower())

    def test_punctuation_adjacency(self):
        r = filt('He said "piano," loudly.')
        self.assertEqual(r.hits, ["piano"])
        self.assertIn('"', r.filtered)
        self.assertIn(",", r.filtered)

    def test_no_substring_false_positive(self):
        # "keys" must not fire inside "monkeys"; "notes" not inside "notebook"
        r = filt("the monkeys read a notebook")
        self.assertEqual(r.hits, [])
        self.assertEqual(r.filtered, "the monkeys read a notebook")

    def test_per_char_length_matches(self):
        r = filt("piano", redaction="per_char")
        self.assertEqual(r.filtered, "#" * len("piano"))

    def test_fixed_redaction(self):
        r = filt("piano", redaction="fixed")
        self.assertEqual(r.filtered, "[REDACTED]")

    def test_longest_variant_wins(self):
        # "piano's" should be redacted as one 7-char token, not "piano" + "'s"
        r = filt("piano's")
        self.assertEqual(r.filtered, "#" * len("piano's"))
        self.assertEqual(r.hits, ["piano"])


class TestVariants(unittest.TestCase):
    def test_e_ending(self):
        v = word_variants("dance")
        self.assertIn("dancing", v)
        self.assertIn("danced", v)

    def test_y_ending(self):
        v = word_variants("city")
        self.assertIn("cities", v)

    def test_blocklist_maps_to_canonical(self):
        bl = build_blocklist(TARGET, FORBIDDEN)
        self.assertEqual(bl["keys"], "keys")
        self.assertEqual(bl["playing"], "play")


class TestAuditDetector(unittest.TestCase):
    def test_leetspeak(self):
        flags = audit_flags("try p14n0 instead", TARGET, FORBIDDEN)
        types = {f["type"] for f in flags}
        self.assertIn("leetspeak", types)

    def test_spacing(self):
        flags = audit_flags("the p i a n o is big", TARGET, FORBIDDEN)
        self.assertTrue(any(f["type"] == "spacing" and f["word"] == "piano" for f in flags))

    def test_substring(self):
        flags = audit_flags("I love pianoforte", TARGET, FORBIDDEN)
        self.assertTrue(any(f["type"] == "substring" and f["word"] == "piano" for f in flags))

    def test_near_miss(self):
        flags = audit_flags("a pianno maybe", TARGET, FORBIDDEN)
        self.assertTrue(any(f["type"] == "near_miss" for f in flags))

    def test_clean_message_no_flags(self):
        flags = audit_flags("a large keyboard contraption with black and white levers", TARGET, FORBIDDEN)
        self.assertEqual(flags, [])

    def test_audit_never_blocks(self):
        # Audit runs on raw text and does not alter the blocking result.
        r = filt("p14n0")  # leetspeak is NOT blocked in v1
        self.assertEqual(r.hits, [])
        self.assertEqual(r.filtered, "p14n0")


if __name__ == "__main__":
    unittest.main()
