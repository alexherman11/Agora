# health: room test
"""a10526: a repeat ordered by when things were made or last changed. In-memory worlds only (roomworld): nothing is
saved, no window opens. A thing 'from before the log' is made by clearing its create event's record in memory, so no
event says it made the thing, as for the things the world held before it had a log."""
import re
import unittest

import lens_ir
import roomworld
import scene


def lens(sort):
    return f'list : column, of prop:fixture=yes as t, each row\n  by {sort}\nrow : text "$t.title"'


class LensTime(unittest.TestCase):
    def setUp(self):
        self.d, self.r = roomworld.build(say=False)
        self.w = self.d.world
        self.ids = {t: self.make(t) for t in ("first", "second", "third")}

    def run_line(self, line, who="jeff"):
        self.w.me = who
        self.d._window = ""
        r = self.d.dispatch("desk", {"line": line, "whole": True})
        self.assertFalse(r.get("error"), r)
        return r.get("text", "")

    def make(self, title):
        self.run_line(f"look {self.r.HOME}")
        return re.search(r"created (a\d+)", self.run_line(f"do create {self.r.HOME} kind=note title={title} fixture=yes"))[1]

    def touch(self, title, **props):
        aid = self.ids[title]
        self.run_line(f"look {aid}")
        self.run_line(f"do prop {aid} " + " ".join(f"{k}={v}" for k, v in props.items()))

    def before_the_log(self, title):
        """No event says it made this thing any more (its create's record is cleared, in memory only)."""
        sid = self.w.nodes[self.ids[title]]["subject"]
        for e in self.w.events:
            if (e.get("undo") or {}).get("delete_subject") == sid:
                e["undo"] = {}

    def order(self, sort):
        sc = lens_ir.evaluate(self.d, lens(sort))
        return [k["text"] for k in sc["kids"]], sc

    def test_newest_first_and_oldest_first_by_created(self):
        self.assertEqual(self.order("-created")[0], ["third", "second", "first"])
        self.assertEqual(self.order("created")[0], ["first", "second", "third"])

    def test_changed_and_changed_field(self):
        self.touch("first", mood="up")                          # first is now the latest changed
        self.touch("second", colour="red")
        self.assertEqual(self.order("-changed")[0], ["second", "first", "third"])
        self.assertEqual(self.order("-created")[0], ["third", "second", "first"])      # created is not moved by an edit
        got, sc = self.order("-changed.mood")
        self.assertEqual(got, ["first", "second", "third"])      # only first's mood changed; the others tie, kept in order
        self.assertIn(f"{self.ids['second']} changed.mood=none (no event changed its mood)", scene.to_text(sc, "t", "jeff", 0))

    def test_pre_log_things_sort_last_with_the_reason_printed(self):
        self.before_the_log("second")
        for sort in ("-created", "created"):
            got, sc = self.order(sort)
            self.assertEqual(got[-1], "second", sort)
            text = scene.to_text(sc, "t", "jeff", 0)
            self.assertIn(f"{self.ids['second']} created=none (made before the log)", text)

    def test_ties_keep_their_current_order(self):
        self.before_the_log("first")
        self.before_the_log("third")                            # two with no time: a tie, kept as the selection gives it
        base = [k["text"] for k in lens_ir.evaluate(self.d, 'list : column, of prop:fixture=yes as t, each row\nrow : text "$t.title"')["kids"]]
        ties = [t for t in base if t in ("first", "third")]
        for sort in ("-created", "created"):
            got = self.order(sort)[0]
            self.assertEqual(got[0], "second")
            self.assertEqual(got[1:], ties, sort)

    def test_the_scene_prints_the_order_and_each_value(self):
        got, sc = self.order("-created")
        text = scene.to_text(sc, "t", "jeff", 0)
        self.assertIn("by -created", text)
        line = next(l for l in text.splitlines() if "· sorted" in l)
        self.assertEqual([m for m in re.findall(r"(a\d+) created=", line)],
                         [self.ids[t] for t in got])            # the printed values are in the order shown

    def test_created_and_changed_print_and_an_old_lens_is_unchanged(self):
        sc = lens_ir.evaluate(self.d, 'list : column, of prop:fixture=yes as t, each row\nrow : text "$t.title $created | $changed"')
        texts = [k["text"] for k in sc["kids"]]
        self.assertTrue(all(re.search(r"\| \S", t) for t in texts), texts)
        self.assertTrue(all("none" not in t for t in texts), texts)
        old = lens_ir.evaluate(self.d, lens("title"))           # a lens that does not ask: no time read, no new line
        self.assertNotIn("· sorted", scene.to_text(old, "t", "jeff", 0))

    def test_reading_writes_nothing(self):
        n = len(self.w.events)
        self.order("-created")
        self.order("-changed")
        self.assertEqual(len(self.w.events), n)


if __name__ == "__main__":
    unittest.main()
