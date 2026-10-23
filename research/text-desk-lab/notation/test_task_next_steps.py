# health: room test
"""Private native-world fixture: no model, live world, network or windows."""

import json
import unittest
from datetime import UTC, datetime
from types import SimpleNamespace

import house
import task_next_steps as ns
import task_next_steps_verbs
import test_task_flow

pytest_plugins = ["test_resident_portable"]  # shared fake transport fixture


class NextStepsTests(unittest.TestCase):
    run_line = test_task_flow.TaskFlowTests.run_line
    change = test_task_flow.TaskFlowTests.change

    def setUp(self):
        test_task_flow.TaskFlowTests.setUp(self)
        self.rid = self.r.corner["juniper"]
        self.w.nodes[self.rid]["props"]["next_steps"] = "on"
        for line in task_next_steps_verbs.lines(self.r.BOARD):
            self.run_line("juniper", line)
        self.change(
            "juniper",
            'lead=juniper priority=urgent next_action="Review blocked worker" '
            'acceptance="Corrected fixture passes"',
        )

    def record(self):
        return next(r for r in ns.rows(self.w, "juniper") if r["target"] == self.card)

    def test_native_block_correction_completion_review_verification(self):
        self.change(
            "pike",
            'status=blocked blocked_on="Need fixture" blocker_owner=juniper '
            'resume_when="Fixture supplied"',
        )
        self.assertEqual(self.record()["state"], "blocked")
        old = self.record()["basis"]
        self.run_line(
            "juniper",
            f'task-revise {self.card} "Preserve interruptions" "Corrected fixture passes" '
            f'{self.card} "Supply fixture"',
        )
        self.assertNotEqual(old, self.record()["basis"])
        self.change(
            "pike",
            "status=doing remove=blocked_on,blocker_owner,resume_when "
            'worker_milestone=completed worker_summary="Fixture passed" worker_evidence="evidence"',
        )
        self.assertEqual(self.record()["state"], "result awaiting owner review")
        token = self.record()["basis"]
        self.run_line("pike", f'task-review {self.card} {token} "Done"')
        self.assertEqual(self.record()["reviewed"], "no")  # child cannot review itself for lead
        self.run_line("juniper", f'task-review {self.card} {token} "Check acceptance"')
        self.assertEqual(self.record()["reviewed"], "yes")
        self.assertEqual(self.record()["verified"], "no")
        self.run_line(
            "juniper",
            f'do create {self.r.BOARD} kind=note title="Fixture evidence" '
            'text="RAN corrected fixture passed"',
        )
        evidence = self.w.events[-1]["undo"]["delete"]
        self.run_line("juniper", f"task-verify {self.card} {token} {evidence}")
        self.assertEqual(self.record()["verified"], "yes")
        self.assertEqual(ns.props(self.w, self.card)["status"], "doing")
        self.run_line(
            "juniper", f'task-revise {self.card} "New goal" "New acceptance" {self.card} "Recheck"'
        )
        self.assertEqual(self.record()["verified"], "no")
        self.assertEqual(self.record()["reviewed"], "no")

    def test_parent_stays_open_and_explicit_priority_beats_noisy_dashboard(self):
        self.run_line(
            "juniper",
            f'do create {self.r.BOARD} kind=task title="Dashboard integration" '
            "owner=pike lead=juniper priority=normal status=doing",
        )
        dashboard = self.w.events[-1]["undo"]["delete"]
        for i in range(12):
            self.run_line("pike", f"read {dashboard}")
            self.run_line(
                "pike",
                f'do prop {dashboard} worker_milestone=failed worker_summary="Urgent detail {i}"',
            )
        self.run_line(
            "juniper",
            f'do create {self.r.BOARD} kind=task title="Delegated harness check" '
            f"owner=pike lead=juniper parent_task={self.card} status=doing",
        )
        child = self.w.events[-1]["undo"]["delete"]
        old = self.record()["basis"]
        self.run_line("pike", f"read {child}")
        self.run_line(
            "pike",
            f'do prop {child} worker_milestone=completed worker_evidence="result" status=done',
        )
        self.assertNotEqual(old, self.record()["basis"])
        self.assertEqual(ns.rows(self.w, "juniper")[0]["target"], self.card)
        result = next(r for r in ns.rows(self.w, "juniper") if r["target"] == child)
        self.assertEqual(result["state"], "result awaiting owner review")
        self.run_line("juniper", f'task-review {child} {result["basis"]} "Check parent acceptance"')
        self.assertFalse(any(r["target"] == child for r in ns.rows(self.w, "juniper")))
        self.assertEqual(self.record()["verified"], "no")
        self.assertNotEqual(ns.props(self.w, self.card)["status"], "done")
        self.assertIn("Dashboard integration", ns.packet(self.w, "juniper"))

    def test_due_review_one_shot_restart_hold_and_rearm(self):
        now = datetime(2026, 10, 23, tzinfo=UTC).timestamp()
        self.run_line("juniper", f"task-followup {self.card} 2026-10-22T23:00:00Z")
        state = {}
        self.assertIn(
            "task review due", ns.collect(self.w, self.rid, state, len(self.w.events), now)
        )
        state = json.loads(json.dumps(state))
        self.assertEqual(ns.collect(self.w, self.rid, state, len(self.w.events), now), "")
        for value in (
            "status=paused",
            "status=doing authority=permission",
            "authority=granted effect_state=unknown",
            "effect_state=known status=cancelled",
        ):
            self.change("juniper", value)
            self.assertEqual(ns.collect(self.w, self.rid, {}, 0, now), "")
        self.change("juniper", 'status=doing review_at="2026-10-22T23:30:00Z"')
        self.assertIn(
            "task review due", ns.collect(self.w, self.rid, state, len(self.w.events), now)
        )

    def test_event_pass_is_durable_and_own_completion_returns_attention(self):
        r = SimpleNamespace(rid=self.rid, state={"cursor": len(self.w.events)}, save=lambda: None)
        self.change("juniper", "status=done")
        h = house.House.__new__(house.House)
        self.assertTrue(h.news(self.w, r, "juniper"))
        self.assertIn("Next-steps review", r.state["inbox"][-1])
        saved = json.loads(json.dumps(r.state))
        self.assertFalse(h.news(self.w, r, "juniper"))
        self.assertEqual(r.state, saved)
        # Even an earlier cursor supplied again cannot duplicate the review event.
        self.assertEqual(ns.collect(self.w, self.rid, r.state, 0, 0), "")

    def test_workshop_approval_holds_suppress_due_review_until_released(self):
        now = datetime(2026, 10, 23, tzinfo=UTC).timestamp()
        for value in (True, "true", "yes"):
            self.assertTrue(ns.held({"approval_required": value}))
        for value in (False, "false", "no", ""):
            self.assertFalse(ns.held({"approval_required": value}))
        self.run_line("juniper", f"task-followup {self.card} 2026-10-22T23:00:00Z")
        for value in ("true", "yes"):
            self.change("juniper", f"approval_required={value}")
            state = {}
            self.assertEqual(ns.collect(self.w, self.rid, state, 0, now), "")
            self.assertEqual(state["next_steps_due"], {})
            self.assertTrue(self.record()["state"].startswith("held:"))
        self.change("juniper", "approval_required=no")
        state = {}
        self.assertIn(
            "task review due", ns.collect(self.w, self.rid, state, len(self.w.events), now)
        )
        self.assertEqual(ns.collect(self.w, self.rid, state, len(self.w.events), now), "")

    def test_context_opt_in_bounded_fresh_and_cosmetic_noise(self):
        state = {}
        text = ns.context(self.w, self.rid, state)
        self.assertIn("Repair", text)
        self.assertEqual(ns.context(self.w, self.rid, state), "")
        self.assertTrue(ns.context(self.w, self.rid, state, force=True))
        token = self.record()["basis"]
        self.change("pike", 'colour=red worker_log="Routine log"')
        self.assertEqual(token, self.record()["basis"])
        self.w.nodes[self.rid]["props"]["next_steps"] = "off"
        self.assertEqual(ns.context(self.w, self.rid, state, force=True), "")

    def test_closed_task_does_not_discard_open_promise(self):
        self.run_line("juniper", f'promise to=pike "Check final outcome" about={self.card}')
        self.change("juniper", "status=cancelled")
        row = self.record()
        self.assertTrue(row["promises"])
        self.assertTrue(row["state"].startswith("held:"))

    def test_evidence_change_and_false_basis_do_not_verify(self):
        self.run_line(
            "juniper", f'do create {self.r.BOARD} kind=note title="Evidence" text="Result"'
        )
        evidence = self.w.events[-1]["undo"]["delete"]
        self.run_line("juniper", f"task-verify {self.card} invented {evidence}")
        self.assertEqual(self.record()["verified"], "no")
        token = self.record()["basis"]
        self.run_line("juniper", f"task-verify {self.card} {token} {evidence}")
        self.assertEqual(self.record()["verified"], "yes")
        self.run_line("juniper", f"read {evidence}")
        self.run_line("juniper", f'do prop {evidence} conclusion="Withdrawn result"')
        self.assertEqual(self.record()["verified"], "no")

    def test_packet_limit_preserves_inspection_and_high_priority(self):
        for i in range(12):
            self.run_line("juniper", f"look {self.r.BOARD} :1")
            self.run_line(
                "juniper",
                f'do create {self.r.BOARD} kind=task title="Sibling {i}" '
                f'owner=juniper priority=normal next_action="{"x" * 800}" '
                f'acceptance="{"y" * 800}"',
            )
        text = ns.packet(self.w, "juniper")
        self.assertLess(len(text), 6000)
        self.assertIn("Repair", text)
        self.assertIn("more. Inspect rows nextsteps:juniper", text)
        self.assertGreater(len(ns.rows(self.w, "juniper")), 8)

    def test_evidence_reference_swap_cannot_borrow_owners_verification(self):
        evidence = []
        for title in ("Evidence A", "Older unchanged evidence B"):
            self.run_line("juniper", f"look {self.r.BOARD} :1")
            self.run_line(
                "juniper", f'do create {self.r.BOARD} kind=note title="{title}" text="Result"'
            )
            evidence.append(self.w.events[-1]["undo"]["delete"])
        token = self.record()["basis"]
        self.run_line("juniper", f"task-verify {self.card} {token} {evidence[0]}")
        self.assertEqual(self.record()["verified"], "yes")
        self.change("pike", f"verified_evidence={evidence[1]}")
        self.assertEqual(self.record()["basis"], token)
        self.assertEqual(self.record()["verified"], "no")
        # Even the lead must attest the evidence/token pair, not only swap a pointer.
        self.change("juniper", f"verified_evidence={evidence[0]}")
        self.assertEqual(self.record()["verified"], "yes")
        self.change("juniper", f"verified_evidence={evidence[1]}")
        self.assertEqual(self.record()["verified"], "no")
        self.run_line("juniper", f"task-verify {self.card} {token} {evidence[1]}")
        self.assertEqual(self.record()["verified"], "yes")
        self.run_line("juniper", f"task-verify {self.card} {token} {evidence[1]}")
        self.assertEqual(self.record()["verified"], "yes")

    def test_bad_deadline_is_not_a_clock_or_permission_guess(self):
        self.change("juniper", 'review_at="tomorrow"')
        self.assertEqual(ns.collect(self.w, self.rid, {}, len(self.w.events), 9999999999), "")
        self.change("juniper", 'review_at="2026-10-22T23:00:00"')
        self.assertEqual(ns.collect(self.w, self.rid, {}, len(self.w.events), 9999999999), "")

    def test_inspectable_source_and_undone_result(self):
        import scene

        before = self.record()["basis"]
        event = self.change("pike", 'worker_milestone=completed worker_summary="Changed"')
        self.assertNotEqual(before, self.record()["basis"])
        self.run_line("pike", f"undo {event['id']}")
        self.assertEqual(before, self.record()["basis"])
        self.assertTrue(
            any(r["target"] == self.card for r in scene.rows(self.d, "nextsteps:juniper"))
        )


def test_actual_restart_handoff_delivers_current_tasks_with_identity(portable):
    h, r, corner, spawned = portable
    corner["next_steps"] = "on"
    w = h.load()
    # Reuse the real native command path, with no live server or transport.
    from desk_knife import DeskKnife

    d = DeskKnife(w)
    # Native fixture writes use a tiny adapter to the same tested dispatch helper.
    f = NextStepsTests()
    f.d, f.w = d, w
    board = next(n["id"] for n in w.nodes.values() if n.get("title") == "Board")
    f.run_line("pike", f"look {board} :1")
    f.run_line(
        "pike",
        f'do create {board} kind=task title="Harness top priority" owner=pike priority=urgent '
        'next_action="Verify corrected child" acceptance="Private fixture passes" '
        'worker_milestone=completed worker_summary="Child report received"',
    )
    r.state.update(
        next_steps_context="old-digest",
        next_steps_due={"task": "old-deadline"},
        pending={"carry": "Current user correction", "delivered": True},
    )
    r.save()
    # Actual Resident disk reload then actual House.step -> provider prepare -> send.
    restored = house.Resident(h, r.rid)
    h.residents[r.rid] = restored
    h.step()
    content = json.loads(restored.proc.stdin.getvalue())["message"]["content"][0]["text"]
    assert "Harness top priority" in content and "Verify corrected child" in content
    assert "Current user correction" in content and "unchanged identity" in content
    assert "Provider handover: codex -> claude" in content
    assert restored.state["next_steps_due"] == {"task": "old-deadline"}
    assert "--resume" not in spawned[0][0]
    restored.events.put({"type": "result", "is_error": False})
    restored.turns_ended()
    row = next(row for row in ns.rows(w, "pike") if row["title"] == "Harness top priority")
    assert row["reviewed"] == "no" and row["verified"] == "no"
    assert row["state"] == "result awaiting owner review"


def test_failed_send_reincludes_context_without_changing_quota_or_replaying_effect(portable):
    from unittest.mock import Mock

    h, r, corner, _ = portable
    corner.update(next_steps="on", provider="codex", model="gpt-6.1-sol")
    r.proc = Mock()
    r.proc.stdin.write.side_effect = OSError("disconnected")
    r.state.update(retry_kind="limit", retry_at=9999999999)
    r.send("Current correction", "news")
    assert not r.state["pending"].get("delivered")
    r.proc.stdin.write.side_effect = None
    r.send("Reconnect", "receipt")
    sent = r.proc.stdin.write.call_args[0][0]
    assert "Next steps (canonical" in sent and "Current correction" in sent
    assert r.state["retry_kind"] == "limit" and r.state["retry_at"] == 9999999999
    h.act.assert_not_called()


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q", "-p", "no:cacheprovider"]))
