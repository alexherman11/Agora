"""Offline regression journeys for a9369; no saved world, provider or Conversation."""
# health: room test
import unittest
import pickle

import roomworld


class ChatCrossings(unittest.TestCase):
    def setUp(self):
        self.d, self.refs = roomworld.build()
        self.w = self.d.world
        self.slots = {}
        self.ok("worker-a", f"look {self.w.root} :3")
        self.ok("worker-a", f'do create {self.w.root} kind=chat title="Crossing fixture" text="Start"')
        self.s = next(s for s in self.w.subjects.values() if s["title"] == "Crossing fixture")
        self.chat = next(iter(self.w.appearances_of(self.s["id"])))

    def run_as(self, actor, line, at=None, window=""):
        key = (actor, window)
        self.w.me = actor
        self.d._window = window
        self.d.seen, self.d.open, self.d.last_event_seen = self.slots.get(key, ({}, {self.w.root}, 0))
        self.d._as_of = at
        try:
            return self.d.dispatch("desk", {"line": line})
        finally:
            self.slots[key] = self.d.seen, self.d.open, self.d.last_event_seen
            self.d._as_of = None

    def ok(self, actor, line, **kwargs):
        result = self.run_as(actor, line, **kwargs)
        self.assertNotIn("error", result, result)
        return result["text"]

    def test_resident_receipts_do_not_repeat_or_double_hold_in_one_turn(self):
        self.ok("pike", f"read {self.chat}")
        turn = len(self.w.events)
        self.ok("worker-b", f'do append {self.chat} line="First missed message"')
        mid, ev = self.s["lines"][-1]["id"], self.s["lines"][-1]["ev"]
        before = len(self.w.events)
        sent = self.ok("pike", f'do append {self.chat} line="Reply one"', at=turn)
        self.assertEqual(len(self.w.events), before + 1)  # read bookkeeping makes no events
        for words in (mid, ev, "Worker-b", "First missed message", "marked read"):
            self.assertIn(words, sent)
        self.ok("worker-b", f'do append {self.chat} line="Second missed message"')
        second = self.ok("pike", f'do append {self.chat} line="Reply two"', at=turn)
        self.assertIn("Second missed message", second)
        self.assertNotIn("First missed message", second)
        third = self.ok("pike", f'do append {self.chat} line="Reply three"', at=turn)
        self.assertNotIn("new line", third)
        self.assertEqual(sum(l["text"] == "Pike: Reply one" for l in self.s["lines"]), 1)

    def test_failed_append_does_not_consume_crossing_receipt(self):
        self.ok("worker-a", f"read {self.chat}")
        self.ok("worker-b", f'do append {self.chat} line="Still unread"')
        reads = dict(self.d._chat_reads)
        before = len(self.w.events)
        failed = self.run_as("worker-a", f'do append {self.chat} line="Bad" about=zz99999')
        self.assertIn("error", failed)
        self.assertEqual(len(self.w.events), before)
        self.assertEqual(self.d._chat_reads, reads)
        self.assertIn("Still unread", self.ok("worker-a", f'do append {self.chat} line="Valid"'))

    def test_all_crossings_have_bounded_snippets_including_multiline(self):
        self.ok("worker-a", f"read {self.chat}")
        ids = []
        for n in range(12):
            self.ok("worker-b", f'do append {self.chat} line="Message {n}\\n' + "x" * 400 + '"')
            ids.append(self.s["lines"][-1]["id"])
        sent = self.ok("worker-a", f'do append {self.chat} line="Received"')
        self.assertIn("12 new lines", sent)
        for mid in ids:
            row = next(row for row in sent.splitlines() if row.strip().startswith(mid + " "))
            self.assertLessEqual(len(row.split("): ", 1)[1]), 240)
        self.assertNotIn("haven't seen", sent)
        self.assertNotIn("new line", self.ok("worker-a", f'do append {self.chat} line="Next"'))
        self.assertIn("x" * 400, self.ok("worker-a", f"read {self.chat}"))

    def test_chat_comment_and_thread_reply_land_without_prior_look(self):
        self.ok("worker-a", f"read {self.chat}")
        self.ok("worker-b", f'do append {self.chat} line="Before comment"')
        sent = self.ok("worker-a", f'do comment {self.chat} line="Question"')
        self.assertIn("Before comment", sent)
        cid = self.s["comments"][-1]["id"]
        self.ok("worker-a", f"read {self.chat}")
        self.ok("worker-b", f'do comment {self.chat} id={cid} line="Thread crossed"')
        turn = len(self.w.events) - 1
        sent = self.ok("pike", f'do comment {self.chat} id={cid} line="Reply"', at=turn)
        self.assertIn("Thread crossed", sent)
        again = self.ok("pike", f'do comment {self.chat} id={cid} line="Another"', at=turn)
        self.assertNotIn("Thread crossed", again)

    def test_receipts_do_not_unlock_overwriting_edits(self):
        self.ok("worker-a", f"read {self.chat} :3")
        self.ok("worker-b", f'do append {self.chat} line="Crossed"')
        self.ok("worker-a", f'do append {self.chat} line="Mine"')
        for command in (
            f'do rewrite {self.chat} text="Destroy chat"',
            f'do replace {self.chat} old="Crossed" new="Gone"',
            f'do edit {self.chat} text="Destroy chat"',
        ):
            result = self.run_as("worker-a", command)
            self.assertIn("stale", result.get("error", ""), result)
        self.ok("worker-a", f"read {self.chat}")
        self.ok("worker-a", f"do prop {self.chat} custom=before")
        self.ok("worker-b", f"look {self.chat} :3")
        self.ok("worker-b", f"do prop {self.chat} custom=theirs")
        self.ok("worker-a", f'do append {self.chat} line="Does not acknowledge props"')
        result = self.run_as("worker-a", f"do prop {self.chat} custom=mine")
        self.assertIn("stale", result.get("error", ""), result)

    def test_queued_human_lines_stay_unread_when_worker_line_crosses_too(self):
        self.ok("alex", f"look {self.refs.DESKTOP} :1")
        self.ok("alex", f"do prop {self.refs.DESKTOP} person=alex")
        self.ok("alex", f"look {self.chat} :1")
        self.ok("alex", f"do prop {self.chat} members=alex,pike reply_policy=queue")
        self.ok("pike", f"read {self.chat} :3")
        turn = len(self.w.events)
        self.ok("alex", f'do append {self.chat} line="Human next turn"')
        self.ok("worker-b", f'do append {self.chat} line="Worker crossing"')
        sent = self.ok("pike", f'do append {self.chat} line="Current answer"', at=turn)
        self.assertIn("Worker crossing", sent)
        self.assertNotIn("Human next turn", sent)
        self.assertIn("1 human follow-up message(s) queued", sent)
        read = self.ok("pike", f"read {self.chat}")
        self.assertIn("Human next turn", read)

    def test_other_window_has_its_own_receipt(self):
        for window in ("one", "two"):
            self.ok("worker-a", f"read {self.chat}", window=window)
        self.ok("worker-b", f'do append {self.chat} line="For both windows"')
        for window in ("one", "two"):
            self.assertIn("For both windows", self.ok(
                "worker-a", f'do append {self.chat} line="From {window}"', window=window))

    def test_receipt_acknowledgement_survives_session_roundtrip(self):
        self.ok("pike", f"read {self.chat}")
        turn = len(self.w.events)
        self.ok("worker-b", f'do append {self.chat} line="Already acknowledged"')
        self.assertIn("Already acknowledged", self.ok("pike", f'do append {self.chat} line="First"', at=turn))
        self.d = pickle.loads(pickle.dumps(self.d))  # synthetic desk only, never a supplied session
        self.w = self.d.world
        sent = self.ok("pike", f'do append {self.chat} line="After reload"', at=turn)
        self.assertNotIn("Already acknowledged", sent)

    def test_note_appends_and_nonchat_thread_holds_are_unchanged(self):
        self.ok("worker-a", f"look {self.w.root} :1")
        self.ok("worker-a", f'do create {self.w.root} kind=note title="Note fixture" text="Before"')
        note = next(s for s in self.w.subjects.values() if s["title"] == "Note fixture")
        nid = next(iter(self.w.appearances_of(note["id"])))
        self.ok("worker-a", f"read {nid}")
        self.ok("worker-b", f"read {nid}")
        self.ok("worker-b", f'do append {nid} line="Note change"')
        self.assertIn("stale", self.run_as("worker-a", f'do append {nid} line="Still fenced"').get("error", ""))
        self.ok("worker-a", f"read {nid}")
        self.ok("worker-a", f'do comment {nid} line="Question"')
        cid = note["comments"][-1]["id"]
        self.ok("worker-a", f"read {nid}")
        self.ok("worker-b", f"read {nid}")
        self.ok("worker-b", f'do comment {nid} id={cid} line="Nonchat thread"')
        result = self.run_as("worker-a", f'do comment {nid} id={cid} line="Unchanged hold"')
        self.assertIn("held, not sent", result.get("error", ""), result)


if __name__ == "__main__":
    unittest.main()
