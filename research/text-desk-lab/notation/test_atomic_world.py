# health: room test
"""Real Desk/World, journal and Session writer-lock tests; no supplied worlds.

Only the Session loader is in-memory. Journal and lock fixtures are newly made
below this worktree, outside sessions/. There is no server, host or painter.
"""
from copy import deepcopy
import os
from pathlib import Path
import shutil
import sys
import threading
import unittest
from unittest.mock import patch
import uuid

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "window-lab")]
os.environ["DESKD"] = "off"
os.environ["DESKD_TRACE"] = "off"
import agora_tmp
import atomic_world as atomic
import deskd
import explore
import store
from world import Refusal


def command(desk, line):
    result = desk.dispatch("desk", {"line": line, "whole": True, "reply": uuid.uuid4().hex})
    if result.get("error"):
        raise AssertionError(result)
    return result


class MemorySession(deskd.Session):
    """Use production admission/exit and real locks, with an in-memory loader."""
    def __init__(self, test, actor="jeff", read=False):
        super().__init__(test.name, actor, read=read)
        self.test = test
        self.path, self.lock = test.path, test.path.with_suffix(".lock")

    def _enter_locked(self, hold):
        self.desk = self.test.desk
        self.desk.world.me = self.actor
        self.desk._session = self.name
        self.desk._per = getattr(self.desk, "_per", {})
        self.per = self.desk._per
        self.hold, self.stamp = True, (1, 1)
        self.before, self.pickled = None, {}
        self._facts0 = (len(self.desk.world.events),
                        self.test.log.path.stat().st_size if self.test.log.exists() else 0)
        return self.desk


class AtomicWorldTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(agora_tmp.directory("atomic-world-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.name = "atomic-" + uuid.uuid4().hex
        self.path = self.tmp / "fixture.state"
        self.desk = explore.fresh()
        d, w = self.desk, self.desk.world
        command(d, f"look {w.root} :3")
        command(d, f'do create {w.root} kind=surface title=Receiver')
        self.receiver = w.last_created
        command(d, f"look {w.root} :3")
        self.log = store.Log(store.log_path(self.path))
        store.genesis(d, self.path)
        store.mark_snapshot(d, self.path)
        self.original = deepcopy(d)
        self.operation = uuid.uuid4().hex
        self.steps = [
            {"verb": "create", "target": w.root,
             "args": {"kind": "surface", "title": "Picked-up item"}, "as": "panel"},
            {"verb": "prop", "target": "@panel", "args": {"target": self.receiver}},
            {"verb": "move", "target": "@panel", "args": {"into": self.receiver}},
        ]
        self.observed = atomic.capture(d)

    def session(self, **kwargs):
        return MemorySession(self, **kwargs)

    def submit(self, steps=None, operation=None, observed=None):
        s = self.session()
        with s:
            return s.atomic(operation or self.operation, observed or self.observed,
                            self.steps if steps is None else steps)

    def normal(self, line):
        ctx = store.begin(self.desk, self.path)
        result = command(self.desk, line)
        store.commit(ctx, self.desk, line, self.desk.world.me)
        store.mark_snapshot(self.desk, self.path)
        return result

    def unchanged(self, before, size):
        self.assertEqual(atomic.capture(self.desk), before)
        self.assertEqual(self.log.path.stat().st_size, size)

    def rule(self, text):
        value = '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$") + '"'
        self.normal(f"do create {self.desk.world.root} kind=note tags=rule title=Rule text={value}")
        rule_id = self.desk.world.last_created
        self.desk._rules_sync(say=False)
        self.observed = atomic.capture(self.desk)
        self.original = deepcopy(self.desk)
        return self.desk.world.nodes[rule_id]["subject"]

    def test_success_one_record_and_same_target_restore(self):
        result = self.submit()
        panel = result["aliases"]["panel"]
        self.assertEqual(self.desk.world.nodes[panel]["parent"], self.receiver)
        self.assertEqual(self.desk.world.nodes[panel]["props"]["target"], self.receiver)
        self.assertEqual(result["record"], 2)
        self.assertEqual(len(list(self.log.records())), 2)
        restore = [{"verb": "move", "target": panel,
                    "args": {"into": self.desk.world.root}}]
        r = self.submit(restore, uuid.uuid4().hex, atomic.capture(self.desk))
        self.assertFalse(r["aliases"])
        self.assertEqual(self.desk.world.nodes[panel]["parent"], self.desk.world.root)

    def test_refusal_each_stage_no_orphan_ids_events_or_journal(self):
        for index in range(3):
            with self.subTest(stage=index):
                steps = deepcopy(self.steps)
                if index == 0:
                    steps[0]["args"]["title"] = ""
                elif index == 1:
                    steps[1]["target"] = "f999999"
                else:
                    steps[2]["args"]["into"] = "f999999"
                before, size = atomic.capture(self.desk), self.log.path.stat().st_size
                with self.assertRaises(Refusal):
                    self.submit(steps)
                self.unchanged(before, size)

    def panel_steps(self):
        return [
            {"verb": "create", "target": self.desk.world.root, "as": "panel",
             "args": {"kind": "note", "title": "Picked-up document",
                      "role": "home-panel", "actor": "jeff", "lens": "home-thing",
                      "shows": self.receiver, "shelf": "no"}},
            {"verb": "move", "target": "@panel", "args": {"into": self.receiver}},
        ]

    def test_real_home_panel_note_restore_and_whole_undo(self):
        before = store.flatten(self.desk.world)
        r = self.submit(self.panel_steps())
        panel = r["aliases"]["panel"]
        node = self.desk.world.nodes[panel]
        subject = self.desk.world.subjects[node["subject"]]
        self.assertEqual(subject["kind"], "note")
        self.assertEqual(subject["props"]["role"], "home-panel")
        self.assertEqual(subject["props"]["shows"], self.receiver)
        self.assertEqual(node["parent"], self.receiver)
        restore_id = uuid.uuid4().hex
        restored = self.submit([
            {"verb": "prop", "target": panel, "args": {"shelf": "yes"}},
            {"verb": "move", "target": panel, "args": {"into": self.desk.world.root}},
        ], restore_id, atomic.capture(self.desk))
        self.assertFalse(restored["aliases"])
        s = self.session()
        with s:
            s.atomic_undo(uuid.uuid4().hex, atomic.capture(self.desk), restore_id)
            s.atomic_undo(uuid.uuid4().hex, atomic.capture(self.desk), self.operation)
        self.assertEqual(store.flatten(self.desk.world), before)
        self.assertNotIn(node["subject"], self.desk.world.subjects)

    def test_note_panel_late_refusal_leaks_no_subject_or_appearance(self):
        steps = self.panel_steps()
        steps[-1]["args"]["into"] = "f999999"
        before, size = atomic.capture(self.desk), self.log.path.stat().st_size
        with self.assertRaises(Refusal):
            self.submit(steps)
        self.unchanged(before, size)

    def test_panel_actor_source_and_effect_fields_fail_closed(self):
        for prop, value in (("actor", "alex"), ("shows", "f999999"),
                            ("text", "unreviewed"), ("tags", "rule"),
                            ("wake", "anything"), ("role", "agent")):
            with self.subTest(prop=prop):
                steps = self.panel_steps()
                steps[0]["args"][prop] = value
                before, size = atomic.capture(self.desk), self.log.path.stat().st_size
                with self.assertRaises(Refusal):
                    self.submit(steps)
                self.unchanged(before, size)
        self.desk.seen.pop(self.receiver)
        before, size = atomic.capture(self.desk), self.log.path.stat().st_size
        with self.assertRaisesRegex(Refusal, "source.*looked"):
            self.submit(self.panel_steps())
        self.unchanged(before, size)

    def test_panel_note_cannot_mutate_unrelated_or_other_actors_note(self):
        root = self.desk.world.root
        for extra in ("", "role=home-panel actor=alex lens=home-thing"):
            self.normal(f'do create {root} kind=note title=Unrelated {extra}')
            other = self.desk.world.last_created
            before, size = atomic.capture(self.desk), self.log.path.stat().st_size
            with self.assertRaises(Refusal):
                self.submit([{"verb": "prop", "target": other, "args": {"shelf": "yes"}}],
                            uuid.uuid4().hex, before)
            self.unchanged(before, size)

    def test_budgets_refuse_before_append_or_allocation_publication(self):
        before, size = atomic.capture(self.desk), self.log.path.stat().st_size
        for steps in (self.steps * 6, [
                {"verb": "create", "target": self.receiver,
                 "args": {"kind": "surface", "title": "x" * atomic.MAX_BYTES}}]):
            with self.assertRaises(Refusal):
                self.submit(steps)
            self.unchanged(before, size)
        with patch.object(atomic, "MAX_RECORD_BYTES", 100):
            with self.assertRaisesRegex(Refusal, "record size"):
                self.submit()
        self.unchanged(before, size)

    def test_missing_established_journal_refuses_without_creating_it(self):
        self.log.path.unlink()  # this test's own newly made fixture only
        before = atomic.capture(self.desk)
        with self.assertRaisesRegex(Refusal, "established recoverable journal"):
            self.submit()
        self.assertFalse(self.log.path.exists())
        self.assertEqual(atomic.capture(self.desk), before)

    def test_native_observation_permission_is_not_bypassed(self):
        self.desk.seen.clear()
        before, size = atomic.capture(self.desk), self.log.path.stat().st_size
        with self.assertRaisesRegex(Refusal, "not looked|not seen"):
            self.submit()
        self.unchanged(before, size)

    def test_does_not_accept_subjects_or_executable_commands(self):
        before, size = atomic.capture(self.desk), self.log.path.stat().st_size
        for step in (
            {"verb": "append", "target": self.receiver, "args": {"line": "send"}},
            {"verb": "prop", "target": self.receiver, "args": {"wake": "something"}},
            {"verb": "create", "target": self.receiver,
             "args": {"kind": "note", "title": "Executable", "tags": "verb"}},
        ):
            with self.assertRaises(Refusal):
                self.submit([step])
            self.unchanged(before, size)

    def test_stale_layout_source_membership_and_receiver_fences(self):
        for line in (
            f"do prop {self.receiver} layout_state=changed",
            f"do create {self.receiver} kind=surface title=NewArrival",
        ):
            with self.subTest(line=line):
                self.normal(line)
                before, size = atomic.capture(self.desk), self.log.path.stat().st_size
                with self.assertRaisesRegex(Refusal, "stale"):
                    self.submit()
                self.unchanged(before, size)

    def test_duplicate_reply_reconciles_and_changed_payload_refuses(self):
        first = self.submit()
        before, size = atomic.capture(self.desk), self.log.path.stat().st_size
        self.assertEqual(self.submit(), first)
        self.unchanged(before, size)
        changed = deepcopy(self.steps)
        changed[0]["args"]["title"] = "Different"
        with self.assertRaisesRegex(Refusal, "different request"):
            self.submit(changed)
        self.unchanged(before, size)

    def test_status_only_reconciliation_never_creates(self):
        size = self.log.path.stat().st_size
        s = self.session()
        with s:
            self.assertEqual(s.atomic_status(self.operation)["status"], "absent")
        self.assertEqual(self.log.path.stat().st_size, size)
        first = self.submit()
        size = self.log.path.stat().st_size
        s = self.session()
        with s:
            self.assertEqual(s.atomic_status(self.operation), first)
        self.assertEqual(self.log.path.stat().st_size, size)

    def test_no_candidate_events_or_hooks_visible_before_durable_append(self):
        before = atomic.capture(self.desk)
        append = store.Log.append

        def inspect(log, record, flat_after=None):
            self.assertEqual(atomic.capture(self.desk), before)
            self.assertEqual(record["atomic_world"]["result"]["status"], "committed")
            return append(log, record, flat_after)

        with patch.object(store.Log, "append", inspect):
            self.submit()

    def test_custom_hooks_refuse_instead_of_silently_skipping_validation(self):
        seen = []
        self.desk.hooks.append(lambda d: seen.append(atomic.capture(d)))
        before, size = atomic.capture(self.desk), self.log.path.stat().st_size
        with self.assertRaisesRegex(Refusal, "custom mutation hooks"):
            self.submit()
        self.unchanged(before, size)
        self.assertFalse(seen)

    def test_rules_only_see_final_placement_and_recover_their_cursor(self):
        wrong = self.rule(
            f"when prop:target,-in:{self.receiver} do prop $item lens=intermediate")
        right = self.rule(
            f"when in:{self.receiver},prop:target do prop $item lens=reader")
        pre = deepcopy(self.original)
        result = self.submit()
        panel = result["aliases"]["panel"]
        self.assertEqual(self.desk.world.nodes[panel]["props"]["lens"], "reader")
        self.assertEqual(self.desk._rulestate[wrong]["fired"], 0)
        self.assertEqual(self.desk._rulestate[right]["fired"], 1)
        self.assertTrue(any(p["cause"].startswith("rule ") for p in
                            list(self.log.records())[-1][0]["parts"]))
        state = deepcopy(self.desk._rulestate)
        events = deepcopy(self.desk.world.events)
        self.desk = pre
        retry = self.submit()
        self.assertEqual(retry, result)
        self.assertEqual(self.desk._rulestate, state)
        self.assertEqual(store.plain(self.desk.world.events), store.plain(events))
        self.desk._run_rules()
        self.assertEqual(self.desk._rulestate[right]["fired"], 1)

    def test_unsupported_rule_effect_refuses_all_explicit_steps(self):
        self.rule("on move do prop $item wake=yes")
        before, size = atomic.capture(self.desk), self.log.path.stat().st_size
        with self.assertRaisesRegex(Refusal, "declared panel/layout"):
            self.submit()
        self.unchanged(before, size)

    def test_rule_action_refusal_discards_all_steps(self):
        self.rule("on move do move $item into=f999999")
        before, size = atomic.capture(self.desk), self.log.path.stat().st_size
        with self.assertRaisesRegex(Refusal, "rule action refused"):
            self.submit()
        self.unchanged(before, size)

    def test_full_record_lost_response_recovers_without_recreate(self):
        append = store.Log.append

        def lost(log, record, flat_after=None):
            append(log, record, flat_after)
            raise OSError("simulated response loss after fsync")

        with patch.object(store.Log, "append", lost):
            with self.assertRaises(atomic.UnknownCommit):
                self.submit()
        self.assertEqual(atomic.capture(self.desk), self.observed)
        self.desk = deepcopy(self.original)  # restart from the old in-memory snapshot
        result = self.submit()
        self.assertEqual(result["record"], 2)
        self.assertEqual(len(list(self.log.records())), 2)
        self.assertEqual(self.desk.world.nodes[result["aliases"]["panel"]]["parent"], self.receiver)
        self.assertEqual(self.desk.world.events[-1]["atomic_world"][-1], self.operation)

    def test_missing_or_partial_record_retry_creates_once(self):
        def partial(log, record, flat_after=None):
            with open(log.path, "ab") as stream:
                stream.write(b'{"seq":')
                stream.flush()
            raise OSError("partial write")

        with patch.object(store.Log, "append", partial):
            with self.assertRaises(atomic.UnknownCommit):
                self.submit()
        result = self.submit()
        self.assertEqual(result["record"], 2)
        self.assertEqual(len(list(self.log.records())), 2)

    def test_partial_record_larger_than_tail_scan_is_repaired(self):
        with open(self.log.path, "ab") as stream:
            stream.write(b'{"interrupted":"' + b"x" * 100000)
        result = self.submit()
        self.assertEqual(result["record"], 2)
        self.assertEqual(len(list(self.log.records())), 2)
        self.assertEqual(self.log.flat()[0], store.flatten(self.desk.world))

    def test_mismatched_journal_never_publishes_or_saves_partial_recovery(self):
        self.submit()
        self.desk = deepcopy(self.original)
        # A syntactically valid but inconsistent record cannot be admitted.
        self.log.append({"state": "0000000000000000", "parts": []})
        before = atomic.capture(self.desk)
        with self.assertRaises(atomic.UnknownCommit):
            self.submit()
        self.assertEqual(atomic.capture(self.desk), before)

    def test_native_rule_world_verb_is_refused_without_running_it(self):
        root = self.desk.world.root
        value = '"do prop \\$1 panel_state=executed"'
        self.normal(f"do create {root} kind=note tags=verb on=house title=touch text={value}")
        self.rule("on move do touch $item")
        self.assertTrue(any(r.get("world") for r in self.desk._rulestate.values()))
        before, size = atomic.capture(self.desk), self.log.path.stat().st_size
        with self.assertRaisesRegex(Refusal, "world-verb rules"):
            self.submit()
        self.unchanged(before, size)

    def test_unsettled_rule_chain_is_not_partly_committed(self):
        self.rule(f"when kind:surface do create {self.desk.world.root} kind=surface title=Recursive")
        before, size = atomic.capture(self.desk), self.log.path.stat().st_size
        with self.assertRaisesRegex(Refusal, "did not settle"):
            self.submit()
        self.unchanged(before, size)

    def test_ordinary_refusal_still_leaves_earlier_lines_and_allows_later_lines(self):
        root = self.desk.world.root
        command(self.desk, f"do create {root} kind=surface title=Ordinary")
        panel = self.desk.world.last_created
        failure = self.desk.dispatch("desk", {
            "line": f"do move {panel} into=f999999", "whole": True,
            "reply": uuid.uuid4().hex})
        self.assertTrue(failure.get("error"))
        command(self.desk, f"do prop {self.receiver} panel_state=later")
        self.assertIn(panel, self.desk.world.nodes)
        self.assertEqual(self.desk.world.nodes[self.receiver]["props"]["panel_state"], "later")

    def test_operation_ids_are_actor_and_window_bound(self):
        first = self.submit()
        self.assertIsNone(atomic.receipt(self.desk, self.log, "someone-else", "",
                                         self.operation))
        self.assertIsNone(atomic.receipt(self.desk, self.log, "jeff", "other-window",
                                         self.operation))
        self.assertEqual(atomic.receipt(self.desk, self.log, "jeff", "", self.operation),
                         first)

    def test_alias_collision_no_identity_leak(self):
        steps = deepcopy(self.steps)
        steps.insert(1, deepcopy(steps[0]))
        before, size = atomic.capture(self.desk), self.log.path.stat().st_size
        with self.assertRaisesRegex(Refusal, "alias is already"):
            self.submit(steps)
        self.unchanged(before, size)

    def test_failed_durability_check_poisoned_session_publishes_nothing(self):
        before, size = atomic.capture(self.desk), self.log.path.stat().st_size
        with patch.object(atomic.os, "fsync", side_effect=OSError("fsync denied")):
            s = self.session()
            with s:
                with self.assertRaises(atomic.UnknownCommit):
                    s.atomic(self.operation, self.observed, self.steps)
                self.assertTrue(s._atomic_unknown)
        self.unchanged(before, size)

    def test_unknown_session_and_read_session_cannot_admit(self):
        with self.session(read=True) as d:
            pass
        s = self.session(read=True)
        with s:
            with self.assertRaises(deskd.BadRequest):
                s.atomic(self.operation, self.observed, self.steps)
        with self.assertRaises(deskd.BadRequest):
            s.atomic(self.operation, self.observed, self.steps)
        s = self.session()
        with s:
            s._atomic_unknown = True
            with self.assertRaises(deskd.BadRequest):
                s.atomic(self.operation, self.observed, self.steps)

    def test_whole_undo_and_retry_after_undo_never_recreates(self):
        before = store.flatten(self.desk.world)
        result = self.submit()
        panel = result["aliases"]["panel"]
        with self.assertRaisesRegex(Refusal, "whole-record"):
            self.desk.world.undo(result["events"][-1])
        s = self.session()
        with s:
            undone = s.atomic_undo(uuid.uuid4().hex, atomic.capture(self.desk), self.operation)
        self.assertEqual(undone["status"], "committed")
        self.assertNotIn(panel, self.desk.world.nodes)
        self.assertEqual(store.flatten(self.desk.world), before)
        retry = self.submit()
        self.assertEqual(retry["status"], "undone")
        self.desk = deepcopy(self.original)
        retry_after_recovery = self.submit()
        self.assertEqual(retry_after_recovery["status"], "undone")
        self.assertNotIn(panel, self.desk.world.nodes)

    def test_whole_undo_includes_rule_changes(self):
        self.rule(f"when in:{self.receiver},prop:target do prop $item lens=reader")
        before = store.flatten(self.desk.world)
        result = self.submit()
        self.assertGreater(len(result["events"]), 3)
        s = self.session()
        with s:
            s.atomic_undo(uuid.uuid4().hex, atomic.capture(self.desk), self.operation)
        self.assertEqual(store.flatten(self.desk.world), before)

    def test_ordinary_journal_undo_recovery_does_not_replay_a_create(self):
        result = self.submit()
        before_undo = deepcopy(self.desk)
        self.normal(f"undo {result['events'][0]}")
        self.desk = before_undo
        retry = self.submit()
        self.assertEqual(retry["status"], "undone")
        self.assertNotIn(result["aliases"]["panel"], self.desk.world.nodes)

    def test_undo_refuses_later_changed_fact_without_partial_undo(self):
        result = self.submit()
        panel = result["aliases"]["panel"]
        self.normal(f"do prop {panel} target=different")
        before, size = atomic.capture(self.desk), self.log.path.stat().st_size
        s = self.session()
        with s:
            with self.assertRaisesRegex(Refusal, "changed since"):
                s.atomic_undo(uuid.uuid4().hex, before, self.operation)
        self.unchanged(before, size)

    def test_two_requests_under_real_writer_serialization(self):
        barrier = threading.Barrier(2)
        outcomes = []

        def submit(op):
            barrier.wait()
            try:
                outcomes.append(self.submit(operation=op)["status"])
            except Refusal:
                outcomes.append("stale")

        workers = [threading.Thread(target=submit, args=(uuid.uuid4().hex,)) for _ in range(2)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=10)
            self.assertFalse(worker.is_alive())
        self.assertCountEqual(outcomes, ["committed", "stale"])
        self.assertEqual(len(list(self.log.records())), 2)

    def test_concurrent_identical_retries_get_one_result(self):
        barrier = threading.Barrier(2)
        outcomes = []

        def submit():
            barrier.wait()
            outcomes.append(self.submit())

        workers = [threading.Thread(target=submit) for _ in range(2)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=10)
            self.assertFalse(worker.is_alive())
        self.assertEqual(len(outcomes), 2)
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(len(list(self.log.records())), 2)

    def test_actor_change_is_refused_under_the_writer_lock(self):
        s = self.session()
        with s:
            self.desk.world.me = "different-actor"
            with self.assertRaisesRegex(Refusal, "actor changed"):
                s.atomic(self.operation, self.observed, self.steps)
            self.desk.world.me = s.actor


if __name__ == "__main__":
    unittest.main()
