"""Synthetic/copy-only proofs for a7573. No session files, network, browser or models."""
# health: room test
import copy
import json
import os
import sys
import shutil
import time
import unittest
import uuid
from unittest.mock import patch
from pathlib import Path
from types import SimpleNamespace

import log_world as lw
import roomworld
import store


class LogWorldTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[3] / ".agora-tmp" / "log-world-tests"
        root.mkdir(parents=True, exist_ok=True)
        self.tmp = SimpleNamespace(name=str(root / uuid.uuid4().hex))
        os.makedirs(self.tmp.name)
        self.path = Path(self.tmp.name) / "copy.pickle"  # no pickle is created
        self.d, self.r = roomworld.build()
        self.w = self.d.world
        self.log = store.Log(store.log_path(self.path))
        store.genesis(self.d, self.path)
        self.checkers = []

    def tearDown(self):
        for checker in self.checkers:
            checker.close()
        lw._CHECKERS.pop(str(self.path), None)
        shutil.rmtree(self.tmp.name)

    def checker(self):
        checker = lw.Checker(self.log.path, Path(self.tmp.name) / "receipts.jsonl")
        self.checkers.append(checker)
        lw._CHECKERS[str(self.path)] = checker
        lw.checkpoint(self.d, self.path, full=True)
        checker.jobs.join()
        return checker

    def change(self, title="Changed"):
        nid = self.r.CARDS[0]
        ctx = store.safe_begin(self.d, self.path)
        self.w.apply("edit", self.w.nodes[nid]["subject"], None, {"title": title}, "jeff")
        store.safe_commit(ctx, self.d, f'do edit {nid} title="{title}"', "jeff")

    def test_builds_pure_world_and_checks_each_record(self):
        checker = self.checker()
        for n in range(8):
            self.change(f"Title {n}")
            checker.jobs.join()
            self.assertEqual(checker.snapshot()["state"], "in-step", checker.snapshot())
        self.assertEqual(checker.replay.records, 9)
        self.assertEqual(store.flatten(checker.replay.world), store.flatten(self.w))
        self.assertIsNot(checker.replay.world, self.w)
        self.assertFalse(hasattr(checker.replay, "desk"))

    def test_unlogged_extra_aspect_detected_next_record_both_directions(self):
        checker = self.checker()
        self.change("Prime the logger's quick path")
        checker.jobs.join()
        sid = self.w.nodes[self.r.CARDS[0]]["subject"]
        self.w.subjects[sid]["props"]["unlogged"] = "not recorded"
        store._QUICK[0] = 1              # no whole-world repair on this next write
        self.change()
        checker.jobs.join()
        report = checker.snapshot()
        self.assertEqual(report["state"], "diverged", report)
        d = next(d for d in report["divergences"] if d["aspect"] == "prop:unlogged")
        self.assertEqual(d["live"], "not recorded")
        self.assertEqual(d["log"], "(absent)")
        self.assertIn("unlogged", report["line"])
        # Even after logger repair or a later full check, the first gap remains.
        lw.checkpoint(self.d, self.path, full=True)
        checker.jobs.join()
        self.assertEqual(checker.snapshot()["divergences"][0], report["divergences"][0])

    def test_missing_aspect_detected(self):
        nid = self.r.CARDS[0]
        self.w.apply("edit", self.w.nodes[nid]["subject"], None, {"text": "original"}, "jeff")
        # A separate genesis fixture makes the original value authoritative.
        self.log.path.unlink()
        store._HEADS.pop(str(self.log.path), None)
        store.genesis(self.d, self.path)
        checker = self.checker()
        sid = self.w.nodes[nid]["subject"]
        self.w.subjects[sid]["text"] = ""
        self.change()
        checker.jobs.join()
        self.assertTrue(any(d["aspect"] == "text" and d["live"] == "(absent)"
                            for d in checker.snapshot()["divergences"]))

    def test_repair_record_cannot_erase_gap(self):
        checker = self.checker()
        sid = self.w.nodes[self.r.CARDS[0]]["subject"]
        self.w.subjects[sid]["props"]["outside"] = "found before command"
        store._MARKS.pop(self.w, None)  # force logger's existing whole begin/repair path
        self.change()
        checker.jobs.join()
        self.assertEqual(checker.snapshot()["state"], "diverged")
        self.assertTrue(any(d["reason"] == "unlogged edit repaired by logger"
                            for d in checker.snapshot()["divergences"]))

    def test_repair_before_a_read_is_still_taken_in(self):
        checker = self.checker()
        sid = self.w.nodes[self.r.CARDS[0]]["subject"]
        self.w.subjects[sid]["props"]["outside"] = "no later write"
        store._MARKS.pop(self.w, None)
        ctx = store.safe_begin(self.d, self.path)
        store.safe_commit(ctx, self.d, "look", "jeff")
        checker.jobs.join()
        self.assertEqual(checker.replay.seq, self.log.head()[0])
        self.assertEqual(checker.snapshot()["state"], "diverged")

    def test_history_outside_not_confused_with_current_divergence(self):
        sid = self.w.nodes[self.r.CARDS[0]]["subject"]
        self.w.subjects[sid]["props"]["old"] = "already repaired"
        store._MARKS.pop(self.w, None)
        self.change()
        checker = self.checker()
        self.assertEqual(checker.snapshot()["state"], "in-step", checker.snapshot())

    def test_full_check_catches_unrelated_unlogged_change(self):
        checker = self.checker()
        sid = self.w.nodes[self.r.CARDS[1]]["subject"]
        self.w.subjects[sid]["title"] = "Bypassed the log"
        lw.checkpoint(self.d, self.path, full=True)
        checker.jobs.join()
        self.assertEqual(checker.snapshot()["state"], "diverged")

    def test_broken_chain_and_digest_are_not_in_step(self):
        replay = lw.Replay()
        rec = next(self.log.records())[0]
        rec["state"] = "bad"
        rec["parts"][0]["facts"][0][2] = "bad"
        replay.consume(rec)
        replay.compare(rec, store.flatten(self.w), full=True)
        self.assertEqual(replay.report()["state"], "diverged")
        self.assertGreaterEqual(len(replay.divergences), 2)

    def test_torn_checkpoint_fails_closed(self):
        checker = self.checker()
        with self.log.path.open("ab") as f:
            f.write(b'{"seq":')
        checker.submit(store.flatten(self.w), self.log.path.stat().st_size, "e0", full=True)
        checker.jobs.join()
        self.assertEqual(checker.snapshot()["state"], "unavailable")
        self.assertIn("torn", checker.snapshot()["line"])
        self.assertIsNone(checker.snapshot()["unavailable"][-1]["to"])

    def test_queue_pressure_is_nonblocking_and_unavailable(self):
        checker = self.checker()
        import queue
        old = checker.jobs
        checker.jobs = queue.Queue(maxsize=1)
        # Worker is sleeping on its old queue, deliberately unavailable to drain this one.
        try:
            checker.submit({}, 0, "e0")
            t0 = time.perf_counter()
            self.assertFalse(checker.submit({}, 0, "e0"))
            self.assertLess(time.perf_counter() - t0, 0.05)
            self.assertEqual(checker.snapshot()["state"], "unavailable")
        finally:
            checker.jobs = old
        lw.checkpoint(self.d, self.path)
        checker.jobs.join()
        self.assertEqual(checker.snapshot()["state"], "in-step", checker.snapshot())
        self.assertTrue(checker.gaps)

    def test_restart_keeps_first_and_later_divergences(self):
        checker = self.checker()
        sid = self.w.nodes[self.r.CARDS[0]]["subject"]
        self.w.subjects[sid]["props"]["first"] = "one"
        self.change("first")
        checker.jobs.join()
        self.w.subjects[sid]["props"]["second"] = "two"
        self.change("second")
        checker.jobs.join()
        old = copy.deepcopy(checker.snapshot()["divergences"])
        checker.close()
        self.checkers.remove(checker)
        other = lw.Checker(self.log.path, checker.journal)
        self.checkers.append(other)
        other.submit(store.flatten(self.w), self.log.path.stat().st_size,
                     f"e{self.w._eseq}", full=True)
        other.jobs.join()
        self.assertEqual(other.replay.divergences[:len(old)], old)
        self.assertTrue(other.gaps)

    def test_observed_time_excludes_idle_restart_and_unavailable(self):
        checker = self.checker()
        first = checker.last_observation
        # Submit with controlled receipt times; there is no polling timer.
        checker.clock = lambda: first[0] + 10
        checker.monotonic = lambda: first[1] + 10
        self.change("ten")
        checker.jobs.join()
        self.assertAlmostEqual(checker.covered_seconds, 10)
        checker.clock = lambda: first[0] + 1000
        checker.monotonic = lambda: first[1] + 1000
        self.change("idle")
        checker.jobs.join()
        self.assertAlmostEqual(checker.covered_seconds, 10)
        self.assertTrue(checker.gaps)
        checker.unavailable("test failure")
        checker.clock = lambda: first[0] + 1010
        checker.monotonic = lambda: first[1] + 1010
        self.change("recover")
        checker.jobs.join()
        self.assertAlmostEqual(checker.covered_seconds, 10)

    def test_free_boxes_checked_flow_boxes_excluded_with_evidence(self):
        self.w.nodes[self.w.root]["layout"] = "free"
        self.log.path.unlink()
        store._HEADS.pop(str(self.log.path), None)
        store.genesis(self.d, self.path)
        checker = self.checker()
        flow_child = next(n for n in self.w.nodes.values()
                          if self.w.nodes.get(n.get("parent"), {}).get("layout") == "column")
        flow_child["h"] += 17
        lw.checkpoint(self.d, self.path, full=True)
        checker.jobs.join()
        self.assertTrue(checker.snapshot()["boxes"])
        self.assertTrue(all(b["derived"] for b in checker.snapshot()["boxes"]))
        self.assertEqual(checker.snapshot()["state"], "in-step")
        # Change a stated free-surface box behind the log.
        root = self.w.root
        child = next(n for n in self.w.nodes.values() if n.get("parent") == root)
        child["w"] += 19
        lw.checkpoint(self.d, self.path, full=True)
        checker.jobs.join()
        self.assertTrue(any(d["aspect"] == "box" for d in checker.snapshot()["divergences"]))

    def test_snapshot_is_detached_and_replay_ignores_personal_state(self):
        live, _ = lw.observation(self.w)
        old = copy.deepcopy(live)
        self.w.subjects[self.w.nodes[self.r.CARDS[0]]["subject"]]["tags"].append("later")
        self.assertEqual(live, old)
        before = store.flatten(self.w)
        self.d.seen["new-window"] = 123
        self.w.me = "someone"
        self.assertEqual(store.flatten(self.w), before)

    def test_off_switch_does_not_change_live_log(self):
        checker = self.checker()
        before = self.log.path.read_bytes()
        os.environ["DESK_LOG_WORLD"] = "off"
        try:
            lw.checkpoint(self.d, self.path, full=True)
            self.assertTrue(checker.jobs.empty())
            self.assertEqual(self.log.path.read_bytes(), before)
        finally:
            os.environ.pop("DESK_LOG_WORLD", None)

    def test_observer_fault_cannot_refuse_or_erase_the_live_record(self):
        checker = self.checker()
        seq = self.log.head()[0]
        with patch.object(lw, "committed", side_effect=RuntimeError("synthetic capture failure")):
            self.change("Person's command still worked")
        self.assertEqual(self.log.head()[0], seq + 1)
        self.assertEqual(checker.snapshot()["state"], "unavailable")
        sid = self.w.nodes[self.r.CARDS[0]]["subject"]
        self.assertEqual(self.w.subjects[sid]["title"], "Person's command still worked")

    def test_observer_publication_never_claims_or_reclaims_a_writer_lease(self):
        import deskd
        name = "log-world-in-memory"
        with patch.object(deskd, "_hold") as hold, patch.object(deskd, "_take"), \
                patch.object(deskd, "_give"), patch.object(deskd.Session, "_enter_locked") as enter:
            deskd.LEASES[name] = False
            session = deskd.Session(name, "house", observer=True)
            with self.assertRaises(deskd.ObserverReleased):
                session.__enter__()
            hold.assert_not_called()
            enter.assert_not_called()
            deskd.LEASES[name] = True
            session.__enter__()
            enter.assert_called_once_with(True)
            hold.assert_not_called()
        deskd.LEASES.pop(name, None)

    def test_status_projection_is_one_note_quiet_logged_and_non_recursive(self):
        self.w.apply("create", self.w.root, None, {"kind": "note", "title": lw.STATUS_TITLE}, "jeff")
        self.log.path.unlink()
        store._HEADS.pop(str(self.log.path), None)
        store.genesis(self.d, self.path)
        checker = self.checker()
        before_nodes = set(self.w.nodes)
        before_events = len(self.w.events)
        lw.project(self.d, self.path)
        checker.jobs.join()
        self.assertEqual(before_nodes, set(self.w.nodes))
        self.assertEqual({e["verb"] for e in self.w.events[before_events:]}, {"edit", "prop"})
        self.assertTrue(all(not e.get("knocked") and not e.get("to") for e in self.w.events[before_events:]))
        import house
        import rooms
        self.assertTrue(all(not rooms.reached(self.w, e) for e in self.w.events[before_events:]))
        resident = SimpleNamespace(rid=self.w.root, state={"cursor": before_events}, save=lambda: None)
        routing = house.House.__new__(house.House)
        self.assertFalse(routing.news(self.w, resident, "juniper", resting=True))
        self.assertFalse(resident.state.get("calls") or resident.state.get("knocked_by"))
        event_count = len(self.w.events)
        lw.project(self.d, self.path)
        self.assertEqual(event_count, len(self.w.events))
        self.assertEqual(checker.replay.report()["state"], "in-step", checker.replay.report())

    def test_paired_export_same_event_detached_prefix_and_hashes(self):
        import log_world_fixture as fixture
        frozen = fixture.freeze(self.d, self.path)
        target = Path(self.tmp.name) / "pair"
        self.change("after frozen boundary")
        fixture.export(frozen, target)
        manifest, live, boxes, replay = fixture.load(target)
        self.assertEqual(manifest["event"], frozen["event"])
        self.assertEqual(store.flatten(replay.world), live)
        self.assertNotEqual(store.flatten(self.w), live)
        self.assertTrue(boxes)
        with (target / "live.log.jsonl").open("ab") as f:
            f.write(b"corruption")
        with self.assertRaisesRegex(ValueError, "hash"):
            fixture.load(target)

    def test_requested_full_check_has_one_outer_record_and_valid_hash_chain(self):
        self.w.apply("create", self.w.root, None, {"kind": "note", "title": lw.STATUS_TITLE}, "jeff")
        self.log.path.unlink()
        store._HEADS.pop(str(self.log.path), None)
        store.genesis(self.d, self.path)
        checker = self.checker()
        ctx = store.safe_begin(self.d, self.path)
        self.d._store = ctx
        seq = self.log.head()[0]
        answer = self.d.repl("log-world check")
        self.assertIn("queued", answer)
        store.safe_commit(ctx, self.d, "log-world check", "jeff")
        checker.jobs.join()
        self.assertEqual(self.log.head()[0], seq + 1)
        self.assertEqual(checker.snapshot()["state"], "in-step", checker.snapshot())
        self.assertEqual(store.flatten(checker.replay.world), store.flatten(self.w))
        replay = lw.Replay()
        for rec, _ in self.log.records():
            replay.consume(rec, historical=True)
        self.assertFalse(replay.divergences)

    def test_paired_export_rejects_event_mismatch_and_no_partial_manifest(self):
        import log_world_fixture as fixture
        frozen = fixture.freeze(self.d, self.path)
        frozen["event"] = "e999999"
        target = Path(self.tmp.name) / "bad-pair"
        with self.assertRaises(ValueError):
            fixture.export(frozen, target)
        self.assertFalse((target / "manifest.json").exists())
        with self.assertRaises(FileNotFoundError):
            fixture.load(target)
        # There is deliberately no by=house/Desk request path to this export.
        self.assertFalse(hasattr(fixture, "request"))

    def test_create_remove_long_splice_and_order_keep_up(self):
        checker = self.checker()
        for text in ("long " * 1000, "long " * 500 + "middle" + "long " * 500):
            ctx = store.safe_begin(self.d, self.path)
            sid = self.w.nodes[self.r.CARDS[0]]["subject"]
            self.w.apply("edit", sid, None, {"text": text}, "jeff")
            store.safe_commit(ctx, self.d, "test text", "jeff")
            checker.jobs.join()
            self.assertEqual(checker.snapshot()["state"], "in-step", checker.snapshot())
        ctx = store.safe_begin(self.d, self.path)
        made = self.w.apply("create", self.r.BOARD, None, {"kind": "note", "title": "New"}, "jeff")
        store.safe_commit(ctx, self.d, "test create", "jeff")
        checker.jobs.join()
        self.assertEqual(checker.snapshot()["state"], "in-step", checker.snapshot())
        nid = self.w.last_created
        ctx = store.safe_begin(self.d, self.path)
        self.w.apply("remove", nid, None, {}, "jeff")
        store.safe_commit(ctx, self.d, "test remove", "jeff")
        checker.jobs.join()
        self.assertEqual(checker.snapshot()["state"], "in-step", checker.snapshot())


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    unittest.main()
