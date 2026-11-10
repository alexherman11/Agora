# health: room test
"""Real in-memory rules and native threads; no live notices, wake or persistence."""
import copy
import re
import unittest
from pathlib import Path

import roomworld
import rooms
import scene
import task_flow
from plan_usage import q

VERB = (Path(__file__).resolve().parents[2] / "desktop" /
        "notice-routing" / "notify-question-owner.verb").read_text(encoding="utf-8")


class Routing(unittest.TestCase):
    def setUp(self):
        self.d, self.r = roomworld.build(say=False)
        self.w = self.d.world
        self.run_line(f'do append {self.r.TALK[self.r.BOARD]} line="Fixture actor registered."', "alex")
        # JEFF is a resident in the live world (a corner with role=resident actor=jeff); Alex is a person, with none
        corner = self.make('kind=surface title="JEFF\'s corner"')
        self.run_line(f"look {corner}")
        self.run_line(f"do prop {corner} role=resident actor=jeff")
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

    def last(self, verb, by):
        return next(e for e in reversed(self.w.events) if e.get("verb") == verb and e.get("by") == by)

    def heard(self, card, asker):
        """How the asker hears a waiting card's question, by the house's own readings: the task notice the house
        queues for the commission=waiting event (task_flow.notices), and the knock of the mark=ask comment
        (rooms.reached). -> (recipients of the task notice, how the comment reached the asker)."""
        comment = self.last("comment", "worker-fixture")
        self.wait(card)
        waiting = self.last("prop", "house")
        return ([n["recipient"] for n in task_flow.notices(self.w, waiting)],
                rooms.reached(self.w, comment).get(asker))

    def test_asker_jeff_alex_and_resident(self):
        # a resident asker hears it from the house, twice over, so no notice note is made for them; Alex (a person,
        # no corner) gets the note his notices bell shows
        for asker in ("jeff", "juniper"):
            card = self.card(asker)
            self.comment(card)
            self.assertEqual(self.heard(card, asker), ([asker], "call"))
            self.assertEqual(self.recipients(card), [])
        card = self.card("alex")
        self.comment(card)
        self.wait(card)
        self.assertEqual(self.recipients(card), ["alex"])
        self.assertEqual(self.w.subjects[self.w.nodes[self.old]["subject"]], self.old_subject)
        self.assertEqual(self.w.events[:len(self.old_events)], self.old_events)

    def test_lead_differs_from_asker_the_asker_gets_the_question(self):
        # Ibis e23839: the waiting transition goes to the lead; the worker's question itself must reach the asker
        card = self.make('kind=task title="Fixture led" asked_by=juniper lead=jeff commission=working')
        self.comment(card, "Which way, A or B?")
        question = self.last("comment", "worker-fixture")
        self.wait(card)
        waiting = self.last("prop", "house")
        self.assertEqual([n["recipient"] for n in task_flow.notices(self.w, waiting)], ["jeff"])
        self.assertEqual(rooms.reached(self.w, question).get("juniper"), "call")
        self.assertEqual(self.recipients(card), [])

    def test_unsupported_asker_is_unresolved(self):
        # an asker with no resident corner who is not alex: no knock, no task notice, no note. Reported, not routed
        card = self.card("codex")
        self.comment(card)
        question = self.last("comment", "worker-fixture")
        self.wait(card)
        waiting = self.last("prop", "house")
        self.assertNotIn("codex", rooms.reached(self.w, question))
        self.assertEqual(task_flow.notices(self.w, waiting), [])
        self.assertEqual(self.recipients(card), [])

    def test_a_notice_note_to_a_resident_reaches_no_one(self):
        # why the note is not made for a resident: the house reads a created note with to= as reaching no one, and
        # makes no task notice of it; only Alex's bell (home-notices, to=$me on a person's home base) shows one
        self.run_line(f"look {self.box}", "house")
        self.run_line(f"do create {self.box} kind=note title=asking role=notice to=jeff topic=asking", "house")
        made = self.last("create", "house")
        self.assertEqual(rooms.reached(self.w, made), {})
        self.assertEqual(task_flow.notices(self.w, made), [])

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
        self.assertEqual(self.recipients(card), [])          # JEFF's, through the house; nothing in Alex's bell

    def test_answered_alex_question_does_not_capture_later_question(self):
        card = self.card("jeff")
        cid = self.comment(card, "@alex: Permission?")
        self.run_line("look " + card, "alex")
        self.run_line(f'do comment {card} id={cid} line="Declined."', "alex")
        self.comment(card, "Juniper? No, this card belongs to JEFF.")
        self.wait(card)
        self.assertEqual(self.recipients(card), [])


if __name__ == "__main__":
    unittest.main()
