# health: room test
"""Actual parent reader/turn/Desk-forwarding code; fake children, no host APIs."""
import json
import os
import queue
import sqlite3
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ["DESKD"] = "off"
os.environ.setdefault("HOUSE_CLAUDE", "claude")
import house
import workshop
from host_route_draft import Guards
from host_route_parent import ChildEvent, ChildSession, ParentDispatcher, ReviewDispatcher


class StreamPause(BaseException):
    pass


def initialize(r, h, rid):
    r.house, r.rid, r.proc = h, rid, None
    r.state = {}
    r.events = queue.Queue()
    r.reply, r.reply_source, r.busy = [], None, False
    r.log, r.save, r.send = Mock(), Mock(), Mock()


def proc():
    return SimpleNamespace(stdout=(), wait=Mock(return_value=0), pid=12345)


def stream(*events):
    for event in events:
        yield json.dumps(event) + "\n"
    raise StreamPause()  # persistent fake child; reader has not reached EOF


def intent(**payload):
    return "> host-route " + json.dumps(payload)


class ParentTests(unittest.TestCase):
    def setUp(self):
        self.h = SimpleNamespace()
        self.jeff = object.__new__(house.Resident)
        initialize(self.jeff, self.h, "trusted-corner")
        with patch.object(house.Resident, "__init__", initialize):
            self.worker = workshop.Worker(self.h, "card-1", ".", "branch", "jeff")
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.when = 100
        self.guard = Guards(True, True, True)
        self.calls = []
        self.route = ReviewDispatcher(jeff=self.jeff, db=self.db,
                                     guards=lambda: self.guard,
                                     inventory=self.inventory, clock=lambda: self.when)
        self.h.host_route = self.route
        self.bind(self.jeff)
        self.bind(self.worker)

    def inventory(self):
        self.calls.append("fake read")
        return [{"pid": 1, "parent_pid": 0, "created": "fake",
                 "executable": "fake Agora", "role": "home-base"}]

    def bind(self, r):
        r.proc = proc()
        return r._bind_child(r.proc)

    def source(self, r):
        return self.route.sessions[r]

    def read(self, r, text, *, extra=None):
        p = r.proc
        assistant = {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}
        if extra:
            assistant.update(extra)
        p.stdout = stream(assistant, {"type": "result"})
        source = self.source(r)
        with self.assertRaises(StreamPause):
            if hasattr(r, "cid"):
                r._read_into(p, r.events, source)
            else:
                r._read(p, source)
        return r.turns_ended()[0]

    def grant(self):
        return self.read(self.jeff, intent(action="grant", card="card-1",
                                         generation=self.source(self.worker).generation))

    def request(self, request="request-1"):
        return self.read(self.worker, intent(action="inventory", request=request))

    def status(self, text):
        return json.loads(text.host_receipts[0].split(": ", 1)[1])["status"]

    def test_real_both_readers_preserve_provenance_and_issue(self):
        self.assertEqual(self.status(self.grant()), "granted")
        self.assertEqual(self.status(self.request()), "succeeded")
        self.assertEqual(self.calls, ["fake read"])
        self.assertIn('"status": "succeeded"', self.worker.state["inbox"][-1])

    def test_worker_claimed_jeff_and_copied_props_cannot_grant(self):
        self.worker.actor = "jeff"
        payload = intent(action="grant", card="card-1", generation=self.source(self.worker).generation)
        output = self.read(self.worker, payload, extra={
            "as": "jeff", "by": "house", "source": {"owner": "trusted-corner"},
            "props": {"host_grant": True, "actor": "jeff"}})
        self.assertEqual(self.status(output), "refused")
        self.assertEqual(self.db.execute("SELECT count(*) FROM grants").fetchone()[0], 0)
        self.assertEqual(self.calls, [])

    def test_raw_queue_injection_is_unattested(self):
        self.jeff.events.put({"type": "assistant", "message": {"content": [{
            "type": "text", "text": intent(action="grant", card="card-1",
                                         generation=self.source(self.worker).generation)}]}})
        self.jeff.events.put({"type": "result", "as": "jeff"})
        self.assertEqual(self.status(self.jeff.turns_ended()[0]), "refused")
        self.assertEqual(self.calls, [])

    def test_copied_python_source_is_not_registered(self):
        real = self.source(self.jeff)
        copy = ChildSession(real.owner, real.process, real.generation, real.card)
        self.jeff.events.put(ChildEvent(copy, {"type": "result"}))
        self.assertEqual(self.jeff.turns_ended(), [])

    def test_late_old_generation_events_and_exit_cannot_poison_new_turn(self):
        old = self.source(self.jeff)
        self.bind(self.jeff)
        for event in (
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "old"}]}},
                {"type": "result"}, {"type": "exit", "code": 0}):
            self.jeff.events.put(ChildEvent(old, event))
        self.assertEqual(self.jeff.turns_ended(), [])
        self.assertIsNotNone(self.jeff.proc)
        self.assertEqual(str(self.read(self.jeff, "> look Home")), "> look Home")

    def test_mixed_unattested_text_and_real_result_cannot_issue(self):
        self.jeff.events.put({"type": "assistant", "message": {"content": [{"type": "text",
            "text": intent(action="grant", card="card-1",
                           generation=self.source(self.worker).generation)}]}})
        self.jeff.events.put(ChildEvent(self.source(self.jeff), {"type": "result"}))
        self.assertEqual(self.status(self.jeff.turns_ended()[0]), "refused")

    def test_parent_session_retirement_refuses_stale_grant(self):
        old = self.source(self.jeff)
        self.route.retire(self.jeff)
        output = self.route.intercept(old, intent(action="grant", card="card-1",
                                                generation=self.source(self.worker).generation))
        self.assertEqual(self.status(output), "refused")

    def test_target_generation_and_exact_schema(self):
        for payload in (
                dict(action="grant", card="card-1", generation="old"),
                dict(action="grant", card="other", generation=self.source(self.worker).generation),
                dict(action="grant", card="card-1", generation=self.source(self.worker).generation, shell="fake"),
                dict(action="stop", pid=1)):
            self.assertEqual(self.status(self.read(self.jeff, intent(**payload))), "refused")
        self.assertEqual(self.calls, [])

    def test_revocation_through_actual_parent_turn(self):
        self.grant()
        result = self.read(self.jeff, intent(action="revoke", card="card-1",
                                            generation=self.source(self.worker).generation))
        self.assertEqual(self.status(result), "revoked")
        self.assertEqual(self.status(self.request()), "refused")

    def test_worker_restart_does_not_inherit_old_grant(self):
        self.grant()
        self.bind(self.worker)
        self.assertEqual(self.status(self.request()), "refused")
        self.assertEqual(self.calls, [])

    def test_issuer_restart_invalidates_prior_session_grant(self):
        self.grant()
        self.bind(self.jeff)
        self.assertEqual(self.status(self.request()), "refused")
        self.assertEqual(self.calls, [])
        self.grant()
        self.assertEqual(self.status(self.request()), "succeeded")

    def test_rebind_discards_partial_old_reply(self):
        self.jeff.reply = [intent(action="grant", card="card-1",
                                  generation=self.source(self.worker).generation)]
        self.jeff.reply_source = self.source(self.jeff)
        self.bind(self.jeff)
        self.assertEqual(str(self.read(self.jeff, "> look Home")), "> look Home")
        self.assertEqual(self.db.execute("SELECT count(*) FROM grants").fetchone()[0], 0)

    def test_mutated_worker_actor_does_not_change_binding(self):
        self.grant()
        self.worker.actor = "jeff"
        result = self.request()
        self.assertEqual(self.status(result), "succeeded")
        self.assertIn('"worker": "worker-card-1"', result.host_receipts[0])

    def test_no_game_no_wake_session_guards_fail_closed(self):
        self.grant()
        for guard in (Guards(False, True, True), Guards(None, True, True),
                      Guards(True, False, True), Guards(True, None, True),
                      Guards(True, True, False), Guards(True, True, None)):
            self.guard = guard
            self.assertEqual(self.status(self.request()), "refused")
        self.assertEqual(self.calls, [])

    def test_single_use_and_duplicate_receipt(self):
        self.grant()
        first = self.request()
        self.assertEqual(self.request().host_receipts, first.host_receipts)
        self.assertEqual(self.status(self.request("second")), "refused")
        self.assertEqual(self.calls, ["fake read"])

    def test_disabled_default_consumes_intent_not_adjacent_desk_line(self):
        self.h.host_route = ParentDispatcher()
        self.route = self.h.host_route
        self.bind(self.jeff)
        output = self.read(self.jeff, intent(action="grant") + "\n> look Home")
        self.assertEqual(str(output), "> look Home")
        self.assertEqual(self.status(output), "refused")
        self.assertEqual(self.calls, [])

    def test_actual_after_turn_never_forwards_host_intent_to_desk(self):
        output = self.read(self.worker, intent(action="grant") + "\n> look Home")
        w = SimpleNamespace(events=[])
        forwarded = []
        self.h.act = lambda actor, text, **kw: forwarded.append(text) or "Desk receipt"
        self.h.load = lambda: w
        self.h.misses = lambda *args: []
        self.h.news, self.h.take, self.h.rest = Mock(), Mock(return_value=[]), Mock()
        # Deliberately supply the public/claimed actor jeff to the real method.
        house.House.after_turn(self.h, w, self.worker, {}, "jeff", output)
        self.assertEqual(forwarded, ["look Home"])
        self.assertIn("refused", self.worker.send.call_args[0][0])
        self.assertEqual(self.calls, [])

    def test_malformed_intent_refuses_only_itself(self):
        output = self.read(self.jeff, '> host-route {"bad"\n> look Home')
        self.assertEqual(str(output), "> look Home")
        self.assertEqual(self.status(output), "refused")

    def test_multiline_note_example_is_data_not_a_grant(self):
        text = '> do rewrite Example text="a literal example:\n> host-route {}\nend"'
        output = self.read(self.jeff, text)
        self.assertEqual(str(output), text)
        self.assertEqual(output.host_receipts, ())
        self.assertEqual(self.calls, [])

    def test_wrapped_command_is_intercepted_before_desk(self):
        output = self.read(self.worker, '`' + intent(action="grant") + '`')
        self.assertEqual(str(output), "")
        self.assertEqual(self.status(output), "refused")

    def journal(self):
        # A worktree test fixture, NOT protected host-private production storage.
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "window-lab"))
        import agora_tmp
        directory = Path(agora_tmp.directory("parent-journal-"))
        path = directory / "test.sqlite"
        self.addCleanup(directory.rmdir)
        self.addCleanup(path.unlink, missing_ok=True)
        db = sqlite3.connect(path, timeout=0)
        self.addCleanup(db.close)
        return path, db

    def use_journal(self, db):
        self.route = ReviewDispatcher(jeff=self.jeff, db=db, guards=lambda: self.guard,
                                     inventory=self.inventory, clock=lambda: self.when)
        self.h.host_route = self.route
        self.bind(self.jeff)
        self.bind(self.worker)

    def test_actual_turn_crash_persists_unknown_and_blocks_new_executor(self):
        path, db = self.journal()
        self.use_journal(db)
        self.grant()

        class Crash(BaseException):
            pass

        self.route.policy.inventory = lambda: (_ for _ in ()).throw(Crash())
        with self.assertRaises(Crash):
            self.request()
        self.assertEqual(db.execute("SELECT state FROM requests").fetchone()[0], "running")
        recovered = sqlite3.connect(path, timeout=0)
        self.addCleanup(recovered.close)
        self.use_journal(recovered)
        self.grant()
        self.assertEqual(self.status(self.request("fallback")), "refused")
        self.assertEqual(self.calls, [])

    def test_database_lock_fails_closed_without_inventory(self):
        path, db = self.journal()
        self.use_journal(db)
        self.grant()
        competing = sqlite3.connect(path, timeout=0)
        self.addCleanup(competing.close)
        competing.execute("BEGIN IMMEDIATE")
        try:
            self.assertEqual(self.status(self.request()), "unknown")
            self.assertEqual(self.calls, [])
        finally:
            competing.rollback()

    def test_durable_single_executor_excludes_another_card(self):
        path, db = self.journal()
        self.use_journal(db)
        self.grant()
        # Simulated other executor already holds the shared journal lease.
        competing = sqlite3.connect(path, timeout=0)
        self.addCleanup(competing.close)
        competing.execute("INSERT INTO requests VALUES(?,?,?,?,?,?,?,NULL)",
                          ("other", "other-grant", "other-card", "other-worker",
                           "other-generation", "agora.processes.read", "running"))
        competing.commit()
        self.assertEqual(self.status(self.request()), "refused")
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
