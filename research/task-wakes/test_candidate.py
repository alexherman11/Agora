"""Isolated real desk/routing tests; candidate source only, no runtime or sessions."""
import json
import sys
import unittest
import os
import shutil
import uuid
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

from replay import LAB, POLICY, modules, replay
sys.path.insert(0, str(LAB))
import roomworld
import task_flow as legacy
import test_task_flow

CANDIDATE = modules()
flow, house, routes = (CANDIDATE[n] for n in ("task_flow", "house", "rooms"))


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_task_flow.TaskFlowTests()
        self.fixture.setUp()
        self.w, self.d, self.r = self.fixture.w, self.fixture.d, self.fixture.r
        self.card = self.fixture.card
        self.change = self.fixture.change
        self.run_line = self.fixture.run_line
        self.w.subjects["test-policy"] = {"id": "test-policy", "kind": "note",
                                          "props": deepcopy(POLICY), "rev": 0,
                                          "title": "Test policy", "lines": [], "comments": []}
        self.h = object.__new__(house.House)

    def news(self, actor, start, state=None):
        saved = []
        resident = SimpleNamespace(rid=self.r.corner[actor],
                                  state=state if state is not None else {"cursor": start})
        resident.save = lambda: saved.append(deepcopy(resident.state))
        with patch.dict(sys.modules, {"task_flow": flow, "rooms": routes}):
            urgent = self.h.news(self.w, resident, actor)
        return urgent, resident, saved

    def test_same_captured_interval(self):
        rows, result = replay()
        self.assertEqual(len(rows), 718)
        self.assertEqual(sum(len(r["before"]) for r in result), 13)
        self.assertEqual(sum(len(r["after"]) for r in result), 9)
        suppressed = [r["event"] for r in result if r["before"] and not r["after"]]
        self.assertEqual(suppressed, ["e26773", "e26816", "e26856", "e26866", "e27012", "e27042"])

    def test_repeated_waiting_and_checkpoint_text_do_not_wake(self):
        for i in range(3):
            self.change("pike", "commission=working")
            e = self.change("pike", f'commission=waiting worker_milestone=checkpoint worker_summary="Update {i}"')
            self.assertEqual(flow.notices(self.w, e), [])

    def test_question_and_permission_request_while_waiting_reach_lead_not_corner(self):
        self.change("juniper", "commission=waiting lead=sable")
        for actor, text in (("pike", "Need a decision"), ("alex", "Permission needed")):
            start = len(self.w.events)
            self.run_line(actor, f"read {self.card}")
            self.run_line(actor, f'do comment {self.card} line="{text}" mark=ask')
            e = self.w.events[-1]
            with patch.dict(sys.modules, {"task_flow": flow}):
                reached = routes.reached(self.w, e)
            self.assertIn("sable", reached)
            self.assertNotIn("juniper", reached)
            self.assertTrue(self.news("sable", start)[0])

    def test_explicit_recipient_overrides_implicit_lead(self):
        self.change("juniper", "commission=waiting lead=sable")
        start = len(self.w.events)
        self.run_line("alex", f"read {self.card}")
        self.run_line("alex", f'do comment {self.card} line="A direct human question" to=pike mark=ask')
        e = self.w.events[-1]
        with patch.dict(sys.modules, {"task_flow": flow}):
            self.assertEqual(routes.reached(self.w, e), {"pike": "call"})
        self.assertTrue(self.news("pike", start)[0])
        self.assertFalse(self.news("sable", start)[0])

    def test_permission_explicitly_for_alex_does_not_move_to_lead(self):
        self.run_line("juniper", f"look {self.r.DESKTOP} :1")
        self.run_line("juniper", f"do prop {self.r.DESKTOP} person=alex")
        self.change("juniper", "commission=waiting lead=sable")
        start = len(self.w.events)
        self.run_line("pike", f"read {self.card}")
        self.run_line("pike", f'do comment {self.card} line="Permission for Alex" to=alex mark=ask')
        with patch.dict(sys.modules, {"task_flow": flow}):
            reached = routes.reached(self.w, self.w.events[-1])
        self.assertEqual(set(reached), {"alex"})
        self.assertIn("person", reached["alex"])
        self.assertFalse(self.news("sable", start)[0])
        self.assertFalse(self.news("juniper", start)[0])

    def test_material_blocker_and_new_resolver(self):
        e = self.change("pike", 'commission=waiting blocked_on="Copy proof" blocker_owner=sable resume_when="Proof exists"')
        self.assertEqual({n["recipient"] for n in flow.notices(self.w, e)}, {"juniper", "sable"})
        e = self.change("pike", 'worker_milestone=blocked worker_summary="Still waiting"')
        self.assertEqual(flow.notices(self.w, e), [])
        e = self.change("pike", 'blocked_on="New scope"')
        self.assertEqual({n["recipient"] for n in flow.notices(self.w, e)}, {"juniper", "sable"})

    def test_new_resolver_even_when_lead_is_unchanged(self):
        self.change("pike", 'blocked_on="Proof" blocker_owner=sable resume_when="Proof exists"')
        e = self.change("juniper", "blocker_owner=pike")
        self.assertEqual([n["recipient"] for n in flow.notices(self.w, e)], ["pike"])

    def test_ready_landed_failed_and_milestone_not_rewording(self):
        for state in ("ready", "landed", "failed", "done"):
            e = self.change("pike", "commission=" + state)
            self.assertEqual(flow.notices(self.w, e)[0]["recipient"], "juniper")
        self.change("pike", "worker_milestone=completed")
        e = self.change("pike", 'worker_milestone=completed worker_summary="A rephrased completion"')
        self.assertEqual(flow.notices(self.w, e), [])

    def test_duplicate_pass_restart_and_unknown_delivery_are_not_retries(self):
        start = len(self.w.events)
        e = self.change("pike", "commission=ready")
        self.w.events.append(deepcopy(e))  # duplicate stored record
        pending = {"carry": "Already flushed", "delivered": True, "fate": "unknown"}
        urgent, r, saved = self.news("juniper", start,
                                    {"cursor": start, "pending": deepcopy(pending)})
        self.assertTrue(urgent)
        self.assertEqual(len(saved[-1]["inbox"]), 1)
        restart = deepcopy(saved[-1])
        self.assertFalse(self.news("juniper", start, restart)[0])
        self.assertEqual(restart["pending"], pending)
        # Even a replay pass with a rewound cursor uses the saved queue receipt.
        restart["cursor"] = start
        self.assertFalse(self.news("juniper", start, restart)[0])
        self.assertEqual(len(restart["inbox"]), 1)
        self.assertEqual(restart["pending"], pending)

    def test_dependency_clearance_world_rule_is_retained(self):
        for prop, value in (("commission", "landed"), ("status", "done")):
            with self.subTest(prop=prop):
                self.run_line("juniper", f"look {self.r.BOARD} :1")
                self.run_line("juniper", f'do create {self.r.BOARD} kind=task title="Prerequisite {prop}"')
                prerequisite = self.w.events[-1]["undo"]["delete"]
                self.change("juniper", f"commission=waiting lead=sable waiting_on={prerequisite}")
                self.run_line("juniper", f"look {self.r.BOARD} :1")
                text = (f"when kind:task,prop:{prop}={value} do comment prop:waiting_on=$item "
                        'line="Unblocked: $item.title has landed. Your next step is due."')
                # Live rules a10418/a10420, including the native selection traversal.
                self.run_line("juniper", f'do create {self.r.BOARD} kind=note tags=rule '
                              f'title="Dependency rule {prop}" text={json.dumps(text)}')
                start = len(self.w.events)
                self.run_line("juniper", f"read {prerequisite}")
                self.run_line("juniper", f"do prop {prerequisite} {prop}={value}")
                comments = [e for e in self.w.events[start:] if e["verb"] == "comment"]
                self.assertEqual(len(comments), 1)
                with patch.dict(sys.modules, {"task_flow": flow}):
                    self.assertEqual(routes.reached(self.w, comments[0]), {"sable": "call"})
                self.assertTrue(self.news("sable", start)[0])
                self.assertEqual(self.w.subjects[self.w.nodes[self.card]["subject"]]
                                 ["props"]["waiting_on"], prerequisite)

    def test_real_state_save_restart_and_failed_replace(self):
        # Exercise the real Resident.save atomic-replace path, not a fake save.
        # This is process-restart evidence, not a claim of power-loss durability.
        scratch = Path(__file__).parent / (".tmp-state-" + uuid.uuid4().hex)
        os.makedirs(scratch)
        try:
            start = len(self.w.events)
            self.change("pike", "commission=ready")
            resident = object.__new__(house.Resident)
            resident.rid = self.r.corner["juniper"]
            resident.state_path = scratch / "resident.json"
            resident.state = {"cursor": start, "pending": {"fate": "unknown", "delivered": True}}
            resident.save()
            before = resident.state_path.read_bytes()
            with patch.dict(sys.modules, {"task_flow": flow, "rooms": routes}):
                with patch.object(house.os, "replace", side_effect=OSError("fixture replace failure")):
                    with self.assertRaises(OSError):
                        self.h.news(self.w, resident, "juniper")
                self.assertEqual(resident.state_path.read_bytes(), before)
                # Reload durable state after the failed save: no provider was called.
                resident.state = json.loads(resident.state_path.read_text())
                self.assertTrue(self.h.news(self.w, resident, "juniper"))
                resident.state = json.loads(resident.state_path.read_text())
                self.assertEqual(len(resident.state["inbox"]), 1)
                resident.state["cursor"] = start
                self.assertFalse(self.h.news(self.w, resident, "juniper"))
                self.assertEqual(len(resident.state["inbox"]), 1)
                self.assertEqual(resident.state["pending"], {"fate": "unknown", "delivered": True})
        finally:
            shutil.rmtree(scratch)

    def test_incomplete_blocker_is_quiet_but_explicit_question_is_not(self):
        e = self.change("pike", 'commission=blocked blocked_on="Need access"')
        self.assertEqual(flow.notices(self.w, e), [])
        start = len(self.w.events)
        self.run_line("pike", f"read {self.card}")
        self.run_line("pike", f'do comment {self.card} line="Who can grant access?" mark=ask')
        self.assertTrue(self.news("juniper", start)[0])

    def test_event_time_transition_lead_survives_later_reassignment(self):
        self.change("juniper", "lead=sable")
        e = self.change("pike", "commission=ready")
        self.change("juniper", "lead=pike asked_by=pike")
        self.assertEqual(flow.notices(self.w, e)[0]["recipient"], "sable")

    def test_absent_unsupported_or_ambiguous_policy_preserves_legacy(self):
        e = self.change("pike", "commission=waiting")
        for mutation in ("version", "ambiguous"):
            if mutation == "version":
                self.w.subjects["test-policy"]["props"]["version"] = "99"
            else:
                self.w.subjects["test-policy"]["props"]["version"] = "1"
                self.w.subjects["another-policy"] = deepcopy(self.w.subjects["test-policy"])
            before, after = legacy.notices(self.w, e), flow.notices(self.w, e)
            for n in after:
                n.pop("action_keys")
            self.assertEqual(before, after)

    def test_legacy_without_world_opt_in_unchanged(self):
        del self.w.subjects["test-policy"]
        e = self.change("pike", "commission=waiting")
        before, after = legacy.notices(self.w, e), flow.notices(self.w, e)
        for n in after:
            n.pop("action_keys")
        self.assertEqual(before, after)

    def test_undone_and_receipt_recipient_independence(self):
        e = self.change("pike", 'blocked_on="Proof" blocker_owner=sable resume_when="Complete"')
        notices = flow.notices(self.w, e)
        state = {}
        self.assertEqual(len([n for n in notices if flow.accept_notice(state, n)]), 2)
        self.assertTrue(all(flow.accept_notice(state, n) is None for n in notices))
        self.assertEqual(flow.notices(self.w, dict(e, undone=True)), [])


if __name__ == "__main__":
    unittest.main()
