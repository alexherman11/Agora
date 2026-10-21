# health: room test
"""Durable task events route independently of chat syntax; no live world/model."""

import unittest
import uuid
from copy import deepcopy
from types import SimpleNamespace

import rooms
import roomworld
import task_flow


class TaskFlowTests(unittest.TestCase):
    def setUp(self):
        self.d, self.r = roomworld.build()
        self.w = self.d.world
        self.run_line("juniper", f"look {self.r.BOARD} :1")
        self.run_line(
            "juniper",
            f'do create {self.r.BOARD} kind=task title="Repair" '
            "owner=pike asked_by=juniper status=asked",
        )
        self.assignment = self.w.events[-1]
        self.card = self.assignment["undo"]["delete"]

    def run_line(self, actor, line):
        self.w.me = actor
        self.d._window = ""
        reply = self.d.dispatch("desk", {"line": line, "whole": True, "reply": uuid.uuid4().hex})
        self.assertFalse(reply.get("error"), reply)
        return reply

    def change(self, actor, props):
        self.run_line(actor, f"look {self.r.BOARD} :1")
        self.run_line(actor, f"read {self.card}")
        self.run_line(actor, f"do prop {self.card} {props}")
        return self.w.events[-1]

    def test_assignment_and_owner_acceptance_are_distinct(self):
        n = task_flow.notices(self.w, self.assignment)
        self.assertEqual([x["recipient"] for x in n], ["pike"])
        self.assertIn("awaiting", task_flow.delivery_text(n[0]))
        fake = self.change("sable", "status=doing accepted_by=pike")
        self.assertEqual(task_flow.notices(self.w, fake), [])
        self.change("juniper", "status=asked remove=accepted_by")
        accepted = self.change("pike", "status=doing accepted_by=pike")
        self.assertEqual(task_flow.notices(self.w, accepted)[0]["kinds"], ["accepted by pike"])

    def test_event_snapshot_survives_reassignment(self):
        event = self.change("pike", "status=doing")
        self.change("juniper", "owner=sable asked_by=sable")
        self.assertEqual(task_flow.notices(self.w, event)[0]["recipient"], "juniper")
        self.assertEqual(task_flow.notices(self.w, self.assignment)[0]["recipient"], "pike")

    def test_blocker_contract_notifies_lead_and_resolver_once(self):
        event = self.change(
            "pike",
            'status=blocked blocked_on="Browser acceptance" blocker_owner=sable '
            'resume_when="Browser available"',
        )
        notices = task_flow.notices(self.w, event)
        self.assertEqual({n["recipient"] for n in notices}, {"juniper", "sable"})
        self.assertEqual(len({n["id"] for n in notices}), 2)
        self.assertEqual(rooms.reached(self.w, event), {"juniper": "call", "sable": "call"})
        self.assertTrue(all(not n["missing"] for n in notices))

    def test_incomplete_block_is_visible_not_silently_accepted(self):
        event = self.change("pike", "status=blocked")
        self.assertEqual(
            task_flow.notices(self.w, event)[0]["missing"], list(task_flow.BLOCK_FIELDS)
        )

    def test_worker_checkpoint_is_bounded_and_routine_progress_quiet(self):
        event = self.change("pike", 'worker_summary="Routine progress"')
        self.assertEqual(task_flow.notices(self.w, event), [])
        event = self.change(
            "pike", 'worker_milestone=checkpoint worker_summary="' + "x" * 2000 + '"'
        )
        n = task_flow.notices(self.w, event)
        self.assertEqual([x["recipient"] for x in n], ["juniper"])
        self.assertTrue(n[0]["summary"].endswith("[truncated; read task]"))
        self.assertLess(len(task_flow.delivery_text(n[0])), 1000)
        routine = self.change("pike", 'worker_summary="More routine progress"')
        self.assertEqual(task_flow.notices(self.w, routine), [])

    def test_house_delivery_is_saved_once_and_receipt_is_durable(self):
        import house

        h = object.__new__(house.House)
        snapshots = []
        resident = SimpleNamespace(
            rid=self.r.corner["pike"],
            state={"cursor": self.w.events.index(self.assignment)},
        )
        resident.save = lambda: snapshots.append(deepcopy(resident.state))
        self.assertTrue(h.news(self.w, resident, "pike", resting=True))
        self.assertEqual(len(resident.state["inbox"]), 1)
        self.assertEqual(snapshots[-1]["cursor"], len(self.w.events))
        resident.state = deepcopy(snapshots[-1])
        self.assertFalse(h.news(self.w, resident, "pike", resting=True))
        self.assertEqual(len(resident.state["inbox"]), 1)
        eid = self.assignment["id"]
        self.run_line("house", f'knocked {eid} {{"pike": "queued, acceptance pending"}}')
        receipt = rooms.knock_of(self.w, eid)
        self.assertEqual(receipt["args"]["pike"], "queued, acceptance pending")
        count = len(self.w.events)
        self.run_line("house", f'knocked {eid} {{"pike": "queued, acceptance pending"}}')
        self.assertEqual(len(self.w.events), count)

    def test_house_routes_event_time_owner_after_reassignment(self):
        import house

        h = object.__new__(house.House)
        start = self.w.events.index(self.assignment)
        self.change("juniper", "owner=sable")
        for actor in ("pike", "sable"):
            resident = SimpleNamespace(
                rid=self.r.corner[actor], state={"cursor": start}, save=lambda: None
            )
            self.assertTrue(h.news(self.w, resident, actor))
            self.assertEqual(len(resident.state["inbox"]), 1)
            self.assertIn("awaiting your explicit acceptance", resident.state["inbox"][0])

    def test_undone_events_and_replay_have_no_effects(self):
        event = self.change("pike", "commission=yielded")
        before = len(self.w.events)
        self.assertEqual(task_flow.notices(self.w, event), task_flow.notices(self.w, event))
        self.assertEqual(before, len(self.w.events))
        self.assertEqual(task_flow.notices(self.w, dict(event, undone=True)), [])

    def test_sleeping_recipient_is_held_not_enabled(self):
        self.run_line("juniper", f"examine {self.r.corner['pike']}")
        self.run_line("juniper", f"do prop {self.r.corner['pike']} want=rest")
        self.assertEqual(task_flow.notices(self.w, self.assignment)[0]["recipient"], "pike")
        self.assertEqual(self.w.nodes[self.r.corner["pike"]]["props"]["want"], "rest")

    def test_legacy_task_without_lead_notifies_creator(self):
        self.change("juniper", "remove=asked_by")
        event = self.change("pike", "status=doing")
        self.assertEqual(task_flow.notices(self.w, event)[0]["recipient"], "juniper")


if __name__ == "__main__":
    unittest.main()
