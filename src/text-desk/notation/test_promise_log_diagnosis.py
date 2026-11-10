"""Promise-hook recording regressions: synthetic worlds; no live/session input."""
# health: room test
import copy
import os
import pickle
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch
from uuid import uuid4

import log_world as lw
import moo
import promises
import roomworld
import store
from world import Refusal


class PromiseLogDiagnosis(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(__file__).resolve().parents[3] / ".agora-tmp" / (
            "promise-log-diagnosis-" + uuid4().hex)
        self.tmp.mkdir(parents=True)
        self.path = self.tmp / "synthetic.pickle"  # never created/read
        self.addCleanup(shutil.rmtree, self.tmp)
        self.d, self.r = roomworld.build(say=False)
        self.w = self.d.world
        self.w.me = "juniper"
        self.card = self.r.CARDS[0]
        self.aid, _ = promises.make(
            self.w, "promise", "Finish the synthetic card", "juniper",
            about=self.card, actor="juniper")
        self.sid = self.w.subject_of(self.aid)
        self.key = (self.sid, "x:promise")
        self.addCleanup(patch.stopall)
        patch.dict(os.environ, DESK_LOG_VERIFY="0", DESK_LOG_WORLD="on").start()
        patch.object(store, "_QUICK", [1]).start()
        store.genesis(self.d, self.path)
        # Prime the exact cached-world quick path, without changing the promise.
        self.edit("title", "Synthetic card primed", observe=False)
        self.checker = lw.Checker(store.log_path(self.path), self.tmp / "receipts.jsonl")
        lw._CHECKERS[str(self.path)] = self.checker
        self.addCleanup(lw._CHECKERS.pop, str(self.path), None)
        self.addCleanup(self.checker.close)
        lw.checkpoint(self.d, self.path, full=True)
        self.checker.jobs.join()
        self.assertEqual(self.checker.snapshot()["state"], "in-step")

    def edit(self, field, value, observe=True):
        ctx = (store.safe_begin if observe else store.begin)(self.d, self.path)
        self.w.apply("edit", self.w.subject_of(self.card),
                     None, {field: value}, "juniper")
        (store.safe_commit if observe else store.commit)(
            ctx, self.d, f"synthetic {field}={value}", "juniper")

    def close_card(self, full=False):
        if full:
            store._MARKS.pop(self.w, None)
        ctx = store.safe_begin(self.d, self.path)
        if not full:
            self.assertIsNotNone(ctx.quick, "exercise incremental recording, not the full fallback")
        n0 = len(self.w.events)
        moo.v_prop(self.w, self.card, {"status": "done"})
        notes = promises.after_act(self.d, n0)
        self.assertTrue(notes, "the actual promise hook must run")
        asked = [a for a in self.w.subjects[self.sid]["promise"]["acts"]
                 if a[1] == "asked-end"]
        self.assertEqual(len(asked), 1)
        self.question_event = self.w.event_by_id(asked[0][0])
        store.safe_commit(ctx, self.d, "synthetic close card", "juniper")
        self.checker.jobs.join()
        return store.Log(store.log_path(self.path)).flat()[0]

    def test_quick_path_captures_asked_end_without_later_repair(self):
        flat = self.close_card()
        live = copy.deepcopy(store.flatten(self.w)[self.key])
        self.assertEqual(flat[self.key], live)
        self.assertIn(self.sid, self.question_event["changed"])
        self.assertEqual(self.checker.snapshot()["state"], "in-step")
        store._QUICK[0] = store.VERIFY_EVERY - 1
        self.edit("title", "Unrelated later detection context")
        self.checker.jobs.join()
        self.assertEqual(self.checker.snapshot()["divergences"], [])
        self.assertEqual(self.checker.snapshot()["state"], "in-step")
        self.assertEqual(store.Log(store.log_path(self.path)).flat()[0][self.key], live)
        self.assertEqual(len([a for a in self.w.subjects[self.sid]["promise"]["acts"]
                              if a[1] == "asked-end"]), 1)

    def test_regression_quick_record_must_include_asked_end_in_original_command(self):
        flat = self.close_card()
        self.assertEqual(flat[self.key], store.flatten(self.w)[self.key])

    def test_whole_world_recording_control_captures_the_hook(self):
        flat = self.close_card(full=True)
        self.assertEqual(flat[self.key], store.flatten(self.w)[self.key])
        self.assertEqual(self.checker.snapshot()["state"], "in-step")

    def test_revision_cause_and_one_question_guard(self):
        before = copy.deepcopy(self.w.subjects[self.sid])
        apps = {a: self.w.nodes[a]["rev"] for a in self.w.appearances_of(self.sid)}
        self.close_card()
        self.assertEqual(self.w.subjects[self.sid]["rev"], before["rev"] + 1)
        for a, rev in apps.items():
            self.assertEqual(self.w.nodes[a]["rev"], rev + 1)
        self.assertEqual(self.question_event["undo"]["restore_subjects"], [before])
        self.assertEqual(self.question_event["via"], promises.VIA)
        cause = self.w.event_by_id(self.question_event["cause"])
        self.assertEqual(cause["args"]["status"], "done")
        question_count = len(self.w.subjects)
        ctx = store.safe_begin(self.d, self.path)
        n0 = len(self.w.events)
        moo.v_prop(self.w, self.card, {"next": "Still finished"})
        self.assertEqual(promises.after_act(self.d, n0), [])
        store.safe_commit(ctx, self.d, "synthetic repeated closed card", "juniper")
        self.checker.jobs.join()
        self.assertEqual(len(self.w.subjects), question_count)

    def test_primitive_undo_removes_question_and_restores_promise(self):
        before = copy.deepcopy(self.w.subjects[self.sid]["promise"])
        self.close_card()
        self.assertIn("restore_subjects", self.question_event["undo"])
        self.assertIn("delete", self.question_event["undo"])
        self.assertIn("delete_subject", self.question_event["undo"])
        aid = self.question_event["undo"]["delete"]
        qsid = self.question_event["undo"]["delete_subject"]
        rev = self.w.subjects[self.sid]["rev"]
        self.w.undo(self.question_event["id"])
        self.assertNotIn(aid, self.w.nodes)
        self.assertNotIn(qsid, self.w.subjects)
        self.assertEqual(self.w.subjects[self.sid]["promise"], before)
        self.assertGreater(self.w.subjects[self.sid]["rev"], rev)
        self.assertFalse(promises.state(self.w, self.sid)["asked_end"])

    def test_later_promise_change_fences_primitive_undo(self):
        self.close_card()
        promises.add_act(self.w, self.sid, "release", actor="juniper")
        before = copy.deepcopy(self.w.__dict__)
        with self.assertRaises(Refusal):
            self.w.undo(self.question_event["id"])
        # Refusal must precede both restoration and removal, including revision,
        # event/counter and appearance changes, not just leave the promise alone.
        self.assertEqual(self.w.__dict__, before)
        self.assertIn(self.question_event["undo"]["delete"], self.w.nodes)
        self.assertIn(self.question_event["undo"]["delete_subject"], self.w.subjects)

    def test_replay_and_snapshot_reload_keep_question_marker_and_undo(self):
        self.close_card()
        replay = store.Log(store.log_path(self.path)).flat()[0]
        self.assertEqual(replay, store.flatten(self.w))
        # Only our synthetic fixture is serialized; no session file is read.
        restored = pickle.loads(pickle.dumps(self.d))
        self.assertTrue(promises.state(restored.world, self.sid)["asked_end"])
        restored.world.undo(self.question_event["id"])
        self.assertFalse(promises.state(restored.world, self.sid)["asked_end"])
        self.assertNotIn(self.question_event["undo"]["delete"], restored.world.nodes)

    def test_older_snapshot_catches_up_then_journal_undo_restores_whole_command(self):
        store.mark_snapshot(self.d, self.path)
        saved = pickle.dumps(self.d)
        self.close_card()
        restored = pickle.loads(saved)
        store.catch_up(restored, self.path)
        self.assertEqual(store.flatten(restored.world), store.flatten(self.w))
        self.assertTrue(promises.state(restored.world, self.sid)["asked_end"])
        ctx = store.begin(restored, self.path)
        receipt = restored.cmd_undo(self.question_event["cause"])
        self.assertIn("reverted", receipt)
        store.commit(ctx, restored, "synthetic journal undo", "juniper")
        self.assertFalse(promises.state(restored.world, self.sid)["asked_end"])
        self.assertNotEqual(restored.world.subjects[restored.world.subject_of(self.card)]
                            ["props"].get("status"), "done")
        self.assertNotIn(self.question_event["undo"]["delete"], restored.world.nodes)
        self.assertEqual(store.Log(store.log_path(self.path)).flat()[0],
                         store.flatten(restored.world))


class PrimitiveUndoControls(unittest.TestCase):
    """Unhooked mutations must retain the ordinary primitive undo behavior."""

    def setUp(self):
        self.d, _ = roomworld.build(say=False)
        self.w = self.d.world
        self.w.me = "juniper"

    def create(self):
        return self.w.apply("create", self.w.root, None,
                            {"kind": "note", "title": "Undo control", "text": "before"},
                            "juniper")

    def test_create_only_removes_only_the_created_note(self):
        subjects = copy.deepcopy(self.w.subjects)
        nodes = set(self.w.nodes)
        result = self.create()
        event = self.w.event_by_id(result["event"])
        self.assertEqual(set(event["undo"]), {"delete", "delete_subject"})
        self.w.undo(event["id"])
        self.assertEqual(self.w.subjects, subjects)
        self.assertEqual(set(self.w.nodes), nodes)
        self.assertTrue(event["undone"])
        self.assertEqual(self.w.events[-1]["verb"], "undo")
        with self.assertRaises(Refusal):
            self.w.undo(event["id"])

    def test_restore_only_keeps_the_note_and_restores_its_text(self):
        result = self.create()
        aid = result["created"]
        sid = self.w.subject_of(aid)
        subjects = copy.deepcopy(self.w.subjects)
        nodes = set(self.w.nodes)
        edit = self.w.apply("edit", sid, None, {"text": "after"}, "juniper")
        event = self.w.event_by_id(edit["event"])
        self.assertEqual(set(event["undo"]), {"restore_subject"})
        rev = self.w.subjects[sid]["rev"]
        self.w.undo(event["id"])
        self.assertEqual(set(self.w.nodes), nodes)
        self.assertEqual(set(self.w.subjects), set(subjects))
        self.assertEqual(self.w.subjects[sid]["text"], "before")
        self.assertGreater(self.w.subjects[sid]["rev"], rev)
        for other in set(subjects) - {sid}:
            self.assertEqual(self.w.subjects[other], subjects[other])
        self.assertTrue(event["undone"])

    def test_restore_only_later_write_refuses_without_any_mutation(self):
        result = self.create()
        sid = self.w.subject_of(result["created"])
        edit = self.w.apply("edit", sid, None, {"text": "after"}, "juniper")
        self.w.apply("edit", sid, None, {"text": "later"}, "juniper")
        before = copy.deepcopy(self.w.__dict__)
        with self.assertRaises(Refusal):
            self.w.undo(edit["event"])
        self.assertEqual(self.w.__dict__, before)


if __name__ == "__main__":
    unittest.main()
