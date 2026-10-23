# health: room test
"""Transfer lifecycle with real result draining and fake processes; no live effects."""
import copy
import json
import queue
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

import house
import landing
import preserved_work as pw
import workshop


class Process:
    def __init__(self, exits=True):
        self.code = None
        self.exits = exits
        self.stdin = SimpleNamespace(close=lambda: None)

    def poll(self):
        return self.code

    def wait(self, timeout):
        if self.exits:
            self.code = 0
        return self.code


class TransferLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(prefix="transfer-lifecycle-")
        self.addCleanup(self.tmp.cleanup)
        self.world = SimpleNamespace(nodes={})
        self.host = SimpleNamespace(dir=Path(self.tmp.name), load=lambda: self.world)
        self.pool = workshop.Workshop(self.host)
        self.raw = json.dumps({"source": "main", "paths": ["one.py"]})
        self.subject = {"props": {"brings": self.raw}}
        self.cards = {"card": (self.subject, "working")}
        self.pool.commissions = lambda world: self.cards
        self.pool.compare_lived = lambda world: None
        self.pool.keeper_reverts = lambda world: False
        self.pool.limit_handoffs = lambda world, cfg: False
        self.pool.ordered = lambda cards, cfg: cards.items()
        self.pool.bring_props = lambda cid, **props: self.subject["props"].update(props)
        self.pool.say = Mock()
        self.pool.card_state = lambda cid: (
            self.pool.workers[cid].state if cid in self.pool.workers else {})
        self.worker = self.make_worker()
        self.pool.workers["card"] = self.worker
        self.addCleanup(patch.stopall)
        patch.object(house.charter, "drain_channel").start()
        patch.object(house.conversation_policy, "queued_interrupts", return_value=False).start()
        self.lock = patch.object(landing, "_try_lock", return_value=None).start()

    def make_worker(self):
        worker = object.__new__(house.Resident)
        worker.house = self.host
        worker.cid, worker.rid = "card", "worker-card"
        worker.state = dict(session="kept-session", session_provider="codex",
                            pending=dict(delivered=True, carry="keep this input"))
        worker.events = queue.Queue()
        worker.proc = Process()
        worker.busy, worker.reply, worker.reply_source = True, [], None
        worker.save, worker.log = Mock(), Mock()
        return worker

    def complete(self, error=False):
        self.worker.events.put(dict(type="result", turn_id="one", is_error=error,
                                    subtype="uncertain" if error else "success",
                                    result="result"))

    def test_completion_drains_but_ownership_holds_until_process_exits(self):
        self.complete()
        proc = self.worker.proc
        self.pool._step(self.world, {})
        self.assertEqual(self.worker.state["turns"], 1)
        self.assertEqual(self.worker.state["session"], "kept-session")
        self.assertNotIn("pending", self.worker.state)
        self.assertTrue(self.worker.alive())
        self.assertIsNone(proc.poll())
        self.lock.assert_not_called()
        self.assertIn("worker process", self.subject["props"]["brings_status"])
        self.assertEqual(self.subject["props"]["brings"], self.raw)
        self.pool._step(self.world, {})
        self.assertEqual(self.worker.state["turns"], 1)
        self.assertTrue(self.worker.alive())
        # Observed exit through the ordinary event path, never automatic stop.
        proc.code = 0
        self.worker.events.put(dict(type="exit", code=0))
        self.pool._step(self.world, {})
        self.lock.assert_called_once()
        self.assertIn("serialization", self.subject["props"]["brings_status"])

    def test_completed_paused_receiver_also_drains_without_starting_a_turn(self):
        self.cards["card"] = (self.subject, "paused")
        self.complete()
        self.pool._step(self.world, {})
        self.assertTrue(self.worker.alive())
        self.assertFalse(self.worker.busy)
        self.lock.assert_not_called()
        self.assertEqual(self.cards["card"][1], "paused")

    def test_active_recipient_is_not_stopped_or_admitted(self):
        pending = copy.deepcopy(self.worker.state["pending"])
        self.pool._step(self.world, {})
        self.assertTrue(self.worker.busy)
        self.assertTrue(self.worker.alive())
        self.assertEqual(self.worker.state["pending"], pending)
        self.lock.assert_not_called()

    def test_error_result_retains_unresolved_delivery_and_holds(self):
        pending = copy.deepcopy(self.worker.state["pending"])
        self.complete(error=True)
        self.pool._step(self.world, {})
        self.assertFalse(self.worker.busy)
        self.assertTrue(self.worker.alive())
        self.assertEqual(self.worker.state["pending"], pending)
        self.assertEqual(self.worker.state["last_error"], "result")
        self.assertIn("unresolved", self.subject["props"]["brings_status"])
        self.lock.assert_not_called()

    def test_uncertain_relay_and_staged_input_are_never_cleared(self):
        for key in ("pending", "relay_pending", "handoff"):
            with self.subTest(key=key):
                self.worker = self.make_worker()
                self.pool.workers["card"] = self.worker
                self.worker.busy = False
                self.worker.state.pop("pending")
                self.worker.state[key] = {"phase": "applying"}
                state = copy.deepcopy(self.worker.state)
                self.assertFalse(self.pool.bring("card", self.subject))
                self.assertTrue(self.worker.alive())
                self.assertEqual(self.worker.state, state)
        self.lock.assert_not_called()

    def test_source_owner_is_not_drained_or_stopped(self):
        source = self.make_worker()
        source.turns_ended = Mock(return_value=[])
        self.pool.workers["source"] = source
        self.cards["source"] = ({"props": {}}, "working")
        self.raw = json.dumps({"source": "source", "paths": ["one.py"]})
        self.subject["props"]["brings"] = self.raw
        self.complete()
        self.assertFalse(self.pool.bring("card", self.subject))
        source.turns_ended.assert_not_called()
        self.assertTrue(source.alive())
        self.lock.assert_not_called()

    def test_applied_receipt_does_not_drain_or_stop_resumed_receiver(self):
        _, key = pw.request(self.raw, "card")
        receipt = self.host.dir / "brings" / ("card-" + key + ".json")
        receipt.parent.mkdir()
        receipt.write_text(json.dumps(dict(phase="applied", recipient_after="a" * 40)))
        self.worker.turns_ended = Mock(return_value=[])
        with (patch.object(pw, "registered"),
              patch.object(pw, "git", return_value=SimpleNamespace(returncode=0)),
              patch.object(self.pool, "brought")):
            self.assertTrue(self.pool.bring("card", self.subject))
        self.worker.turns_ended.assert_not_called()
        self.assertTrue(self.worker.alive())
        self.assertTrue(self.worker.busy)

    def test_changed_request_during_drain_does_not_release_receiver(self):
        original = self.worker.turns_ended
        def drain():
            result = original()
            self.subject["props"]["brings"] = "changed"
            return result
        self.worker.turns_ended = drain
        self.complete()
        self.assertFalse(self.pool.bring("card", self.subject))
        self.assertTrue(self.worker.alive())
        self.assertIn("changed", self.subject["props"]["brings_status"])
        self.lock.assert_not_called()

    def test_idle_process_is_not_closed_or_assumed_released(self):
        self.worker.proc = Process(exits=False)
        self.complete()
        self.assertFalse(self.pool.bring("card", self.subject))
        self.assertIn("worker process", self.subject["props"]["brings_status"])
        self.assertTrue(self.worker.alive())
        self.assertFalse(self.pool.bring("card", self.subject))
        self.lock.assert_not_called()

    def test_prepare_keeps_priority_over_a_pending_transfer(self):
        self.cards["card"] = (self.subject, "prepare")
        self.complete()
        with (patch.object(self.pool, "prepare") as prepare,
              patch.object(self.pool, "bring") as bring):
            self.pool._step(self.world, {})
        prepare.assert_called_once()
        bring.assert_not_called()
        self.assertEqual(self.worker.state["turns"], 1)
        self.assertFalse(self.worker.alive())


if __name__ == "__main__":
    unittest.main()
