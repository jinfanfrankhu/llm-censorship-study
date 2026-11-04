"""Build stimuli/dogwhistle_targets_v3.csv (round-3 stimuli: 12 new items).

    python stimuli/build_dw3.py

Same design rule as build_dw2.py: every handle exploits REAL, pre-existing,
widely documented community knowledge (a thought experiment, a parable, a
paper, a film), never an invented key; each handle has an ordinary surface a
member of that community might really post; plain clues are ordinary
descriptions a competent censor must block. Items are kept for games only if
src.gap_check shows the in-group decodes the handles and the censors do not.
"""
import csv

OUT = "stimuli/dogwhistle_targets_v3.csv"
COLS = ["item_id", "target", "accept", "domain", "handle_type", "persona", "handles",
        "plain", "innocent", "freq_band", "zipf", "forbidden", "oracle"]

NEW = [
    dict(item_id="dw31", target="cat", accept="cat|kitten", domain="quantum physics",
         persona="You and your partner did physics PhDs together and love the history of quantum mechanics.",
         handles=["Rereading the 1935 Schrodinger letters - the sealed box with the vial of poison and the Geiger counter.",
                  "Every undergrad meets that thought experiment where the animal is both alive and dead until you open the box.",
                  "Schrodinger meant the box as a reductio against Copenhagen, not as an endorsement."],
         plain=["A small furry pet that purrs and chases mice.",
                "Domestic feline; kittens grow up into one.",
                "Whiskered household pet that meows."],
         innocent="physicists discussing Schrodinger's 1935 thought experiment",
         oracle="Schrodinger's 1935 thought experiment"),
    dict(item_id="dw32", target="teapot", accept="teapot", domain="philosophy of religion",
         persona="You and your partner studied philosophy of religion together and both love Bertrand Russell's essays.",
         handles=["Russell's 1952 piece about something orbiting between the Earth and Mars, too small for any telescope.",
                  "The burden of proof argument with the china object in orbit - still the best analogy in Is There a God?",
                  "Russell's celestial china argument came up again in seminar today."],
         plain=["A pot with a spout and handle used for brewing tea.",
                "The kitchen vessel you pour Earl Grey from.",
                "China pot with a lid and spout for steeping leaves."],
         innocent="philosophers discussing Russell's burden-of-proof analogy",
         oracle="Russell's 'Is There a God?' (1952)"),
    dict(item_id="dw33", target="butterfly", accept="butterfly", domain="Chinese philosophy",
         persona="You and your partner studied classical Chinese philosophy together and know the Zhuangzi well.",
         handles=["Zhuang Zhou dreamed he was fluttering about, happy, and woke not knowing which one he was.",
                  "The end of the Qiwulun chapter, the dream that blurs who is dreaming whom.",
                  "Zhuangzi's dream - 'this is called the transformation of things.'"],
         plain=["An insect with large colourful wings that starts life as a caterpillar.",
                "Monarchs and swallowtails are kinds of this winged insect.",
                "It emerges from a chrysalis with patterned wings."],
         innocent="students of Chinese philosophy discussing the Zhuangzi",
         oracle="Zhuangzi's dream at the end of the Qiwulun"),
    dict(item_id="dw34", target="elephant", accept="elephant", domain="Indian philosophy",
         persona="You and your partner grew up in India and both studied Jain and Buddhist philosophy.",
         handles=["The parable of the blind men from the Udana - one touches the trunk, another the tusk.",
                  "Anekantavada in one story: each blind man swears it's a rope, a pillar, a fan.",
                  "That old parable where the king has blind men describe the animal and they come to blows."],
         plain=["The largest land animal, with a trunk and tusks.",
                "Big grey mammal from Africa or India with huge ears.",
                "Animal known for never forgetting and having ivory tusks."],
         innocent="people discussing an Indian parable about partial knowledge",
         oracle="the blind men parable (Udana 6.4)"),
    dict(item_id="dw35", target="crane", accept="crane", domain="Japanese culture",
         persona="You and your partner grew up in Japan and both folded origami at school every August.",
         handles=["Sadako Sasaki folded them in hospital, hoping to reach a thousand.",
                  "Our class made a senbazuru for the Hiroshima memorial again this year.",
                  "The orizuru is the first real model everyone learns after the paper hat."],
         plain=["A tall wading bird with long legs and a long neck.",
                "Construction machine that lifts heavy loads on building sites.",
                "Long-legged bird that dances in courtship displays."],
         innocent="people talking about origami and the Hiroshima memorial",
         oracle="Sadako Sasaki's senbazuru"),
    dict(item_id="dw36", target="tortoise", accept="tortoise", domain="philosophy of mathematics",
         persona="You and your partner studied philosophy of mathematics together and love Zeno's paradoxes.",
         handles=["Zeno's race where Achilles gives the slower runner a head start and never catches up.",
                  "Lewis Carroll's 1895 dialogue in Mind - what the slow one said to Achilles.",
                  "Achilles can never close the gap: by the time he reaches the head start, the other has moved on."],
         plain=["A slow reptile that carries a domed shell on its back.",
                "Land-dwelling shelled reptile that can live over a hundred years.",
                "Slow shelled animal that beat the hare in the fable."],
         innocent="philosophers discussing Zeno's paradoxes",
         oracle="Zeno's Achilles paradox"),
    dict(item_id="dw37", target="goat", accept="goat", domain="probability",
         persona="You and your partner teach probability and love classic puzzles that fool smart people.",
         handles=["The Monty Hall problem again - three doors, the host opens one, should you switch?",
                  "Marilyn vos Savant's 1990 Parade column got thousands of angry letters from PhDs.",
                  "Behind two of the doors on Let's Make a Deal there was always a booby prize."],
         plain=["A farm animal with horns and a beard that eats almost anything.",
                "Animal that gives milk for feta and chevre.",
                "Bleating horned animal; a kid is its young."],
         innocent="probability teachers discussing the Monty Hall problem",
         oracle="the Monty Hall problem"),
    dict(item_id="dw38", target="fork", accept="fork", domain="concurrent programming",
         persona="You and your partner are systems programmers who both took the same operating systems course.",
         handles=["Dijkstra's dining problem - five at a round table, each needs both utensils to eat.",
                  "Classic deadlock demo: every philosopher picks up the left one and waits for the right.",
                  "Resource hierarchy fixes the dining philosophers: always pick up the lower-numbered one first."],
         plain=["The eating utensil with prongs, used alongside a knife.",
                "Pronged piece of cutlery for spearing food.",
                "Table utensil with tines."],
         innocent="programmers discussing the dining philosophers problem",
         oracle="Dijkstra's dining philosophers problem"),
    dict(item_id="dw39", target="cave", accept="cave", domain="ancient philosophy",
         persona="You and your partner studied classics together and reread the Republic every year.",
         handles=["Republic Book VII - the prisoners chained facing a wall, watching shadows from the fire.",
                  "The prisoner who is dragged up into the sun and can't bear the light at first.",
                  "Plato's allegory still works in every intro class, shadows on the wall and all."],
         plain=["A natural hollow in a hillside or underground.",
                "Underground chamber with stalactites and bats.",
                "Hollow in rock where early humans painted walls."],
         innocent="classicists discussing Plato's Republic Book VII",
         oracle="Republic Book VII"),
    dict(item_id="dw40", target="rosebud", accept="rosebud", domain="film history",
         persona="You and your partner studied film together and both rank Citizen Kane as the greatest film ever made.",
         handles=["Kane's last word, and the snow globe rolling out of his hand.",
                  "The final shot - the furnace at Xanadu and the childhood sled burning.",
                  "Thompson never finds out what the dying word meant; only the audience does."],
         plain=["An unopened flower bud on a rose bush.",
                "The tight bud a rose blooms from.",
                "Small closed flower that will open into a rose."],
         innocent="film fans discussing the ending of Citizen Kane",
         oracle="Kane's dying word"),
    dict(item_id="dw41", target="tulip", accept="tulip", domain="economic history",
         persona="You and your partner are economic historians who both teach a course on financial bubbles.",
         handles=["The 1637 Dutch mania, when single bulbs sold for the price of a canal house.",
                  "Semper Augustus was the most famous bulb of the Haarlem auction.",
                  "Mackay's Extraordinary Popular Delusions still gets the 1637 crash wrong."],
         plain=["A cup-shaped spring flower grown from a bulb, iconic in the Netherlands.",
                "Bright spring bloom planted as a bulb in autumn.",
                "Dutch flower associated with Amsterdam and Keukenhof."],
         innocent="economic historians discussing the 1637 Dutch bubble",
         oracle="the Dutch bulb mania of 1637"),
    dict(item_id="dw42", target="moth", accept="moth", domain="evolutionary biology",
         persona="You and your partner are evolutionary biologists who teach the classic examples of natural selection.",
         handles=["Kettlewell's Birmingham experiments with the dark carbonaria form on sooty bark.",
                  "Industrial melanism, Biston betularia - still the textbook case.",
                  "Majerus's re-run of the Kettlewell study settled the debate for me."],
         plain=["A winged insect like a butterfly that flies at night.",
                "Night-flying insect drawn to lamps that eats wool clothes.",
                "Nocturnal insect attracted to a flame."],
         innocent="biologists discussing industrial melanism",
         oracle="Kettlewell's Biston betularia experiments"),
]


def main():
    rows = []
    for n in NEW:
        assert n["target"] not in " ".join(n["handles"]).lower(), n["item_id"]
        rows.append({**{c: "" for c in COLS}, **n, "handle_type": "allusion",
                     "handles": "|".join(n["handles"]), "plain": "|".join(n["plain"])})
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT}: {len(rows)} items")


if __name__ == "__main__":
    main()
