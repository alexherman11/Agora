# health: room test
"""Real in-memory rules and native threads; no live notices, wake or persistence."""
import copy
import re
import unittest
from pathlib import Path

import roomworld
import scene
from plan_usage import q

VERB = (Path(__file__).resolve().parents[2] / "window-lab" /
        "notice-routing" / "notify-question-owner.verb").read_text(encoding="utf-8")


class Routing(unittest.TestCase):
    def setUp(self):
        self.d, self.r = roomworld.build(say=False)
        self.w = self.d.world
        self.run_line(f'do append {self.r.TALK[self.r.BOARD]} line="Fixture actor registered."', "alex")
        self.box = self.make("kind=surface title=\"Alex's notices\"")
        self.old = self.make('kind=note title=historical role=notice to=alex topic=asking', self.box)
        self.old_subject = copy.deepcopy(self.w.subjects[self.w.nodes[self.old]["subject"]])
        self.old_events = copy.deepcopy(self.w.events)
        self.make("kind=note title=notify-question-owner tags=verb on=house text=" + q(VERB))
        self.make("kind=note title=waiting-rule tags=rule text=" + q(
            "when prop:commission=waiting do notify-question-owner $item"))

    def run_line(self, line, who="jeff"):
        self.w.me = who
        self.d._window = ""
        r = self.d.dispatch("desk", {"line": line, "whole": True})
        text = r.get("text", "")
        self.assertFalse(r.get("error"), r)
        self.assertFalse(text.startswith(("ERR", "MISS")), text)
        return text

    def make(self, fields, parent=None):
        parent = parent or self.r.HOME
        self.run_line("look " + parent)
        text = self.run_line(f"do create {parent} {fields}")
        return re.search(r"created ([af]\d+)", text)[1]

    def card(self, asker):
        return self.make(f'kind=task title="Fixture {asker}" asked_by={asker} commission=working')

    def comment(self, card, text="Question?", to="", mark="ask", who="worker-fixture"):
        self.run_line("look " + card, who)
        self.run_line(f"do comment {card} line={q(text)}" +
                      (f" to={to}" if to else "") + (f" mark={mark}" if mark else ""), who)
        return self.w.subjects[self.w.nodes[card]["subject"]]["comments"][-1]["id"]

    def wait(self, card):
        self.run_line("look " + card, "house")
        self.run_line(f"do prop {card} commission=waiting", "house")

    def recipients(self, card):
        return [s["props"]["to"] for s in self.w.subjects.values()
                if s.get("props", {}).get("about") == card and s["props"].get("topic") == "asking"]

    def test_asker_jeff_alex_and_resident(self):
        for asker in ("jeff", "alex", "juniper"):
            card = self.card(asker)
            self.comment(card)
            self.wait(card)
            self.assertEqual(self.recipients(card), [asker])
        self.assertEqual(self.w.subjects[self.w.nodes[self.old]["subject"]], self.old_subject)
        self.assertEqual(self.w.events[:len(self.old_events)], self.old_events)

    def test_explicit_alex_permission_survives_unrelated_activity(self):
        card = self.card("jeff")
        cid = self.comment(card, "Alex, may this program be ended?", to="alex")
        self.comment(card, "Unrelated progress", who="alex", mark="")
        rows = scene.rows(self.d, f"sayings for:alex in:{card} mark=ask awaiting=yes")
        self.assertEqual([r["thread"] for r in rows], [cid])
        self.wait(card)
        self.assertEqual(self.recipients(card), ["alex"])
        self.run_line("look " + card, "alex")
        self.run_line(f"do comment {card} id={cid} line=\"No, leave it running.\"", "alex")
        self.assertEqual(scene.rows(self.d, f"sayings for:alex in:{card} mark=ask awaiting=yes"), [])
        # No unrelated activity readdresses or deletes the already-created notice.
        self.assertEqual(self.recipients(card), ["alex"])

    def test_explicit_header_and_reply_question(self):
        card = self.card("jeff")
        self.comment(card, "@alex: May I proceed?")
        self.wait(card)
        self.assertEqual(self.recipients(card), ["alex"])
        other = self.card("juniper")
        cid = self.comment(other, "Initial question", to="juniper")
        self.run_line(f"do comment {other} id={cid} line=\"@alex: May I proceed?\" mark=ask", "worker-fixture")
        self.wait(other)
        self.assertEqual(self.recipients(other), ["alex"])

    def test_explicit_unmarked_progress_is_not_an_alex_question(self):
        card = self.card("jeff")
        self.comment(card, "@alex: FYI only.", mark="")
        self.wait(card)
        self.assertEqual(self.recipients(card), ["jeff"])

    def test_answered_alex_question_does_not_capture_later_question(self):
        card = self.card("jeff")
        cid = self.comment(card, "@alex: Permission?")
        self.run_line("look " + card, "alex")
        self.run_line(f'do comment {card} id={cid} line="Declined."', "alex")
        self.comment(card, "Juniper? No, this card belongs to JEFF.")
        self.wait(card)
        self.assertEqual(self.recipients(card), ["jeff"])


if __name__ == "__main__":
    unittest.main()
