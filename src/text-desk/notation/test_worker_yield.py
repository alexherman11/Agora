# health: room test
"""Capacity yield scenarios; no processes, models, live worlds or worktrees are started."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ.setdefault("HOUSE_CLAUDE", "claude")
import workshop  # noqa: E402

CFG = {"workers": "4", "model": "claude-opus-5-5"}


class Worker:
    def __init__(self, cid, busy=False, alive=True):
        self.cid, self.busy, self.is_alive = cid, busy, alive
        self.state = {"session": "kept-session", "cursor": 19, "turns": 1}
        self.sent = []
        self.save = Mock()
        self.ends = []
        self.actor = "worker-" + cid

    def alive(self):
        return self.is_alive

    def turns_ended(self):
        if self.ends:
            self.busy = False
        ended, self.ends = self.ends, []
        return ended

    def send(self, text):
        self.sent.append(text)
        self.busy = True


class YieldTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cards = {}
        self.world = SimpleNamespace(events=[])
        self.house = SimpleNamespace(dir=Path(self.tmp.name), load=lambda: self.world)
        self.ws = workshop.Workshop(self.house)
        self.ws.commissions = lambda w: self.cards
        self.ws.compare_lived = Mock()
        self.ws.keeper_reverts = lambda w: False
        self.ws.limit_handoffs = lambda w, cfg: False
        self.ws.selection_allowed = Mock(return_value=True)
        self.ws.provider_of = lambda cid, s: "codex"
        self.ws.provider_wait = lambda provider: 0
        self.ws.heard = Mock(return_value=["lead: continue with the new test"])
        self.ws.set_state = self.set_state
        self.ws.failed = Mock()
        self.ws.real_tree = lambda tree: True
        self.ws.pool = lambda cfg: []

    def add(self, cid, state, **props):
        self.cards[cid] = ({"id": cid, "props": {"commission": state, **props}}, state)

    def set_state(self, cid, state, **props):
        old = self.cards[cid][0]
        self.cards[cid] = ({**old, "props": {**old["props"], "commission": state, **props}}, state)

    def test_busy_yield_finishes_then_waits_for_capacity_and_resumes_same_session(self):
        self.add("a1", "yielded")
        wk = Worker("a1", busy=True)
        self.ws.workers["a1"] = wk
        for n in range(2, 6):
            self.add(f"a{n}", "paused")
            self.ws.workers[f"a{n}"] = Worker(f"a{n}", busy=True)
        self.ws.step(self.world, CFG)
        self.assertFalse(wk.sent)
        wk.ends = ["checkpoint saved"]
        self.ws.step(self.world, CFG)
        self.assertFalse(wk.sent)
        self.ws.heard.assert_not_called()
        self.assertEqual(wk.state["cursor"], 19)
        self.ws.workers["a2"].busy = False
        self.ws.step(self.world, CFG)
        self.assertEqual(len(wk.sent), 1)
        self.assertIn("lead: continue", wk.sent[0])
        self.assertEqual(wk.state["session"], "kept-session")
        self.assertEqual(self.cards["a1"][1], "working")

    def test_paused_and_blocked_yield_do_not_resume_with_free_slots(self):
        for cid, props in [("a1", {}), ("a2", {"blocked_on": "approval"}),
                           ("a3", {"approval_required": "yes"})]:
            self.add(cid, "paused" if cid == "a1" else "yielded", **props)
            self.ws.workers[cid] = Worker(cid)
        self.ws.step(self.world, CFG)
        self.assertTrue(all(not wk.sent for wk in self.ws.workers.values()))
        self.ws.heard.assert_not_called()

    def test_yield_keeps_model_and_usage_fences(self):
        self.add("a1", "yielded")
        wk = Worker("a1")
        self.ws.workers["a1"] = wk
        self.ws.selection_allowed.return_value = False
        self.ws.step(self.world, CFG)
        self.assertFalse(wk.sent)
        self.ws.selection_allowed.return_value = True
        self.ws.provider_wait = lambda provider: float("inf")
        self.ws.step(self.world, CFG)
        self.assertFalse(wk.sent)
        self.ws.provider_wait = lambda provider: 0
        wk.state["retry_at"] = float("inf")
        self.ws.step(self.world, CFG)
        self.assertFalse(wk.sent)
        self.assertEqual(self.cards["a1"][1], "yielded")

    def test_plan_fuel_hold_preserves_alive_yielded_worker_and_unheard_messages(self):
        self.add("a1", "yielded")
        wk = Worker("a1")
        self.ws.workers["a1"] = wk
        self.ws.provider_of = lambda cid, s: "claude"
        plans = Mock()
        plans.queue_reason.return_value = "Fuel held"
        self.house.plans = plans
        self.ws.step(self.world, CFG)
        plans.queue_reason.assert_called_once_with("claude", CFG)
        plans.target.assert_called_once_with("a1", "Fuel held")
        self.assertEqual(self.cards["a1"][1], "yielded")
        self.assertEqual(wk.state["cursor"], 19)
        self.assertEqual(wk.state["session"], "kept-session")
        self.assertFalse(wk.sent)
        self.ws.heard.assert_not_called()
        plans.queue_reason.return_value = ""
        self.ws.step(self.world, CFG)
        self.assertEqual(self.cards["a1"][1], "working")
        self.assertEqual(len(wk.sent), 1)

    def test_urgent_asked_work_goes_before_normal_yield(self):
        self.add("a1", "yielded", priority="normal")
        self.add("a2", "asked", priority="urgent")
        self.assertEqual([cid for cid, _ in self.ws.ordered(self.cards, CFG)], ["a2", "a1"])

    def test_restart_resumes_saved_worker_without_begin_or_recreating_worktree(self):
        self.add("a1", "yielded")
        wk = Worker("a1")
        self.ws.card_state = lambda cid: wk.state
        self.ws.begin = Mock(side_effect=AssertionError("must not begin fresh work"))
        self.ws.resume = Mock(return_value=wk)
        self.ws.step(self.world, CFG)
        self.ws.resume.assert_called_once()
        self.assertEqual(wk.state["session"], "kept-session")
        self.assertEqual(len(wk.sent), 1)

    def test_restart_does_not_add_second_message_when_pending_turn_resumed(self):
        self.add("a1", "yielded")
        wk = Worker("a1", busy=True)
        self.ws.card_state = lambda cid: wk.state
        self.ws.resume = Mock(return_value=wk)
        self.ws.step(self.world, CFG)
        self.assertFalse(wk.sent)
        self.ws.heard.assert_not_called()

    def test_lead_manual_hold_during_finished_turn_wins_over_old_yield(self):
        self.add("a1", "yielded")
        wk = Worker("a1")
        self.ws.workers["a1"] = wk

        def finished():
            self.set_state("a1", "paused")
            return ["checkpoint saved"]

        wk.turns_ended = finished
        self.ws.step(self.world, CFG)
        self.assertEqual(self.cards["a1"][1], "paused")
        self.assertFalse(wk.sent)
        self.ws.heard.assert_not_called()

    def test_lost_worktree_never_creates_fresh_job_implicitly(self):
        self.add("a1", "yielded")
        self.ws.real_tree = lambda tree: False
        self.ws.resume = Mock()
        self.ws.step(self.world, CFG)
        self.ws.resume.assert_not_called()
        self.assertEqual(self.cards["a1"][1], "yielded")


if __name__ == "__main__":
    unittest.main()
