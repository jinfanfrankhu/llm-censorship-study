from src.game import guess_is_correct, reply_names_target


def test_plural_e_final():
    assert guess_is_correct("pancakes", "pancake")
    assert guess_is_correct("Beetles", "beetle")


def test_plural_es():
    assert guess_is_correct("foxes", "fox")
    assert guess_is_correct("hedgehogs", "hedgehog")


def test_no_false_match():
    assert not guess_is_correct("beet", "beetle")
    assert not reply_names_target("BEET", ["beetle"])


def test_reply_any_word():
    assert reply_names_target("Moonlight Sonata", ["moonlight"])
    assert reply_names_target("pancakes", ["pancake"])
