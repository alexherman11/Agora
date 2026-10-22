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

    def status_fixture(self):
        self.w.apply("create", self.w.root, None, {"kind": "note", "title": lw.STATUS_TITLE}, "jeff")
        nid = self.w.last_created
        self.w.apply("create", self.w.root, None, {"kind": "note", "title": "Evidence",
                                                "role": "log-world-evidence"}, "jeff")
        evidence = self.w.last_created
        self.log.path.unlink()
        store._HEADS.pop(str(self.log.path), None)
        store.genesis(self.d, self.path)
        return nid, evidence, self.checker()

    def test_ordinary_records_and_checks_never_rewrite_unchanged_status(self):
        nid, evidence, checker = self.status_fixture()
        lw.project(self.d, self.path)
        checker.jobs.join()
        status = self.w.subjects[self.w.nodes[nid]["subject"]]
        detail = self.w.subjects[self.w.nodes[evidence]["subject"]]
        self.assertEqual(status["props"]["evidence"], evidence)
        initial = copy.deepcopy(status)
        evidence_text = detail["text"]
        observed = checker.covered_records
        for n in range(12):
            self.change(f"ordinary {n}")
            checker.jobs.join()
            lw.project(self.d, self.path)
            checker.jobs.join()
            self.assertEqual(status, initial)
            self.assertEqual(detail["text"], evidence_text)
        self.assertEqual(checker.covered_records, observed + 12)
        for _ in range(3):
            lw.checkpoint(self.d, self.path, full=True)
            checker.jobs.join()
            lw.project(self.d, self.path)
            checker.jobs.join()
            self.assertEqual(status, initial)
        self.assertEqual(checker.covered_records, observed + 12)
        self.assertEqual(store.flatten(checker.replay.world), store.flatten(self.w))
        for key in ("checked_event", "observed", "unavailable", "at", "capture_ms", "max_capture_ms"):
            self.assertNotIn(key, status["props"])
        self.assertLess(len(status["text"].splitlines()), 8)

    def test_self_records_cannot_advance_time_or_bridge_idle_gaps(self):
        nid, _, checker = self.status_fixture()
        start = checker.last_observation
        count = checker.covered_records
        for seconds in (30, 60, 90):
            checker.clock = lambda seconds=seconds: start[0] + seconds
            checker.monotonic = lambda seconds=seconds: start[1] + seconds
            ctx = store.safe_begin(self.d, self.path)
            self.w.apply("edit", self.w.nodes[nid]["subject"], None, {"text": str(seconds)}, "house")
            store.safe_commit(ctx, self.d, lw.REPORT_WORDS, "house")
            checker.jobs.join()
        self.assertEqual(checker.covered_records, count)
        self.assertEqual(checker.covered_seconds, 0)
        self.change("independent endpoint after idle")
        checker.jobs.join()
        self.assertEqual(checker.covered_records, count + 1)
        self.assertEqual(checker.covered_seconds, 0)
        self.assertTrue(checker.gaps)

    def test_first_divergence_writes_status_once_later_evidence_only(self):
        nid, evidence, checker = self.status_fixture()
        lw.project(self.d, self.path)
        checker.jobs.join()
        sid = self.w.nodes[self.r.CARDS[0]]["subject"]
        self.w.subjects[sid]["props"]["bypass"] = "first"
        self.change("first divergence")
        checker.jobs.join()
        lw.project(self.d, self.path)
        checker.jobs.join()
        status = copy.deepcopy(self.w.subjects[self.w.nodes[nid]["subject"]])
        detail = self.w.subjects[self.w.nodes[evidence]["subject"]]["text"]
        self.w.subjects[sid]["props"]["another"] = "later"
        self.change("first divergence")
        checker.jobs.join()
        lw.project(self.d, self.path)
        checker.jobs.join()
        self.assertEqual(self.w.subjects[self.w.nodes[nid]["subject"]], status)
        self.assertNotEqual(self.w.subjects[self.w.nodes[evidence]["subject"]]["text"], detail)
        events = len(self.w.events)
        lw.project(self.d, self.path)
        self.assertEqual(len(self.w.events), events)

    def test_witness_is_readable_dated_and_never_a_world_fact(self):
        import witnessed
        import importlib.util
        spec = importlib.util.spec_from_file_location("witness_source", Path(lw.__file__).parent / "sources/witnessed.py")
        source = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(source)
        checker = self.checker()
        checker.witness_world = "copy-only"
        with patch.object(witnessed, "ROOT", Path(self.tmp.name) / "witnessed-root"):
            before = store.flatten(self.w)
            checker.witness()
            rows = witnessed.read("copy-only", "log-world")["rows"]
            self.assertTrue(rows)
            self.assertEqual(rows[0]["observed_records"], checker.covered_records)
            self.assertIsInstance(rows[0]["at"], str)
            self.assertIn("T", rows[0]["at"])
            self.assertIsInstance(rows[0]["unavailable"][0]["from"], str)
            projected = source.rows(self.d, "log-world", "copy-only")
            self.assertEqual(projected[0]["observed_records"], checker.covered_records)
            self.assertEqual(projected[0]["state"], "in-step")
            self.assertEqual(store.flatten(self.w), before)
            with patch.object(witnessed, "write", side_effect=PermissionError("synthetic")):
                checker.witness()
                self.change("comparison survives witness output failure")
                checker.jobs.join()
            self.assertFalse(checker.stopped)
            self.assertEqual(checker.snapshot()["state"], "in-step")
            self.assertIn("synthetic", checker.snapshot()["witness_error"])
            checker.unavailable("copy release")
            self.assertEqual(witnessed.read("copy-only", "log-world")["rows"][0]["state"], "unavailable")
            checker.witness_world = None

    def test_moving_props_removed_once_and_unavailable_verdict_is_quiet(self):
        import moo
        nid, _, checker = self.status_fixture()
        ctx = store.safe_begin(self.d, self.path)
        moo.REGISTRY["prop"].run(self.w, nid, dict(checked_event="e1", observed="old counter", unavailable="old gaps",
                                                 at="1770000000", capture_ms="5", _by="house"))
        store.safe_commit(ctx, self.d, lw.REPORT_WORDS, "house")
        checker.jobs.join()
        lw.project(self.d, self.path)
        checker.jobs.join()
        props = self.w.subjects[self.w.nodes[nid]["subject"]]["props"]
        for key in ("checked_event", "observed", "unavailable", "at", "capture_ms"):
            self.assertNotIn(key, props)
        checker.stopped = True
        checker.unavailable("copy-only unavailable")
        lw.project(self.d, self.path)
        checker.jobs.join()
        boundary = self.log.head()[0]
        events = len(self.w.events)
        for _ in range(5):
            lw.project(self.d, self.path)
        self.assertEqual(self.log.head()[0], boundary)
        self.assertEqual(len(self.w.events), events)

    def test_unclassifiable_old_totals_freeze_without_stopping_comparison(self):
        journal = Path(self.tmp.name) / "incomplete.jsonl"
        journal.write_text(json.dumps(dict(kind="report", at=10, records=1,
                                          observed_seconds=300, observed_records=20,
                                          unavailable=[], state="in-step")) + "\n", encoding="utf-8")
        checker = lw.Checker(self.log.path, journal)
        self.checkers.append(checker)
        lw._CHECKERS[str(self.path)] = checker
        lw.checkpoint(self.d, self.path, full=True)
        checker.jobs.join()
        self.change("new record still compared")
        checker.jobs.join()
        self.assertEqual(checker.snapshot()["state"], "in-step")
        self.assertEqual(checker.snapshot()["accounting_state"], "unavailable")
        self.assertEqual((checker.covered_seconds, checker.covered_records), (300, 20))
        self.assertEqual(checker.replay.seq, self.log.head()[0])

    def test_historical_self_correction_survives_restart_exactly_once(self):
        checker = self.checker()
        self.change("independent")
        checker.jobs.join()
        # Use actual log sequence metadata with old-format receipt rows.
        ctx = store.safe_begin(self.d, self.path)
        self.w.apply("edit", self.w.nodes[self.r.CARDS[0]]["subject"], None,
                     {"title": "observer output"}, "house")
        store.safe_commit(ctx, self.d, lw.REPORT_WORDS, "house")
        checker.jobs.join()
        checker.close()
        self.checkers.remove(checker)
        with checker.journal.open("w", encoding="utf-8") as f:
            for seq in (1, 2, 3):
                f.write(json.dumps(dict(kind="report", at=seq * 10, records=seq,
                                       observed_records=seq, observed_seconds=(seq - 1) * 10,
                                       unavailable=[], state="in-step")) + "\n")
        other = lw.Checker(self.log.path, checker.journal)
        self.checkers.append(other)
        other.submit(store.flatten(self.w), self.log.path.stat().st_size, f"e{self.w._eseq}", full=True)
        other.jobs.join()
        self.assertEqual(other.covered_records, 2)
        self.assertEqual(other.covered_seconds, 10)
        self.assertEqual(other.accounting_correction["removed_self_records"], 1)
        self.assertEqual(other.accounting_correction["removed_seconds"], 10)
        other.close()
        self.checkers.remove(other)
        restarted = lw.Checker(self.log.path, checker.journal)
        self.checkers.append(restarted)
        restarted.submit(store.flatten(self.w), self.log.path.stat().st_size, f"e{self.w._eseq}", full=True)
        restarted.jobs.join()
        self.assertEqual(restarted.covered_records, 2)
        self.assertEqual(restarted.covered_seconds, 10)
        self.assertEqual(restarted.accounting_correction, other.accounting_correction)

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

    def test_requested_full_check_has_no_outer_record_and_valid_hash_chain(self):
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
        self.assertEqual(self.log.head()[0], seq)
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
        self.w.apply("create", self.r.BOARD, None, {"kind": "note", "title": "New"}, "jeff")
        store.safe_commit(ctx, self.d, "test create", "jeff")
        checker.jobs.join()
        self.assertEqual(checker.snapshot()["state"], "in-step", checker.snapshot())
        nid = self.w.last_created
        ctx = store.safe_begin(self.d, self.path)
        self.w.apply("remove", nid, None, {}, "jeff")
        store.safe_commit(ctx, self.d, "test remove", "jeff")
        checker.jobs.join()
        self.assertEqual(checker.snapshot()["state"], "in-step", checker.snapshot())

    def historical_gap(self, checker):
        sid = self.w.nodes[self.r.CARDS[0]]["subject"]
        self.w.subjects[sid]["props"]["unlogged"] = "historical gap"
        store._MARKS.pop(self.w, None)
        self.change("logger reconciles its own history")
        checker.jobs.join()
        self.assertEqual(checker.snapshot()["state"], "diverged")
        self.assertEqual(store.flatten(checker.replay.world), store.flatten(self.w))

    def baseline_request(self, checker, request="copy-only-request"):
        return {"request": request, "reason": "Synthetic diagnosed refused write; keep historical evidence.",
                "divergence_hash": checker.snapshot()["retained_divergence_hash"]}

    def test_baseline_matching_full_check_retains_journal_and_evidence_resets_only_epoch(self):
        nid, evidence, checker = self.status_fixture()
        self.historical_gap(checker)
        old = copy.deepcopy(checker.replay.divergences)
        journal_prefix = checker.journal.read_bytes()
        raw_log = self.log.path.read_bytes()
        request = self.baseline_request(checker)
        self.assertTrue(lw.checkpoint(self.d, self.path, full=True, baseline=request))
        checker.jobs.join()
        report = checker.snapshot()
        self.assertEqual(report["state"], "in-step", report)
        self.assertEqual(report["divergences"], old)
        self.assertFalse(report["active_divergences"])
        self.assertEqual((report["observed_seconds"], report["observed_records"]), (0, 0))
        self.assertTrue(checker.journal.read_bytes().startswith(journal_prefix))
        self.assertEqual(self.log.path.read_bytes(), raw_log)
        baseline = report["baselines"][-1]
        self.assertEqual(baseline["set_aside"], old)
        self.assertEqual(baseline["full_differences"], 0)
        self.assertEqual(baseline["event"], report["last_full"])
        lw.project(self.d, self.path)
        checker.jobs.join()
        detail = json.loads(self.w.subjects[self.w.nodes[evidence]["subject"]]["text"].split("\n\n", 1)[1])
        self.assertEqual(detail["divergences"], old)
        self.assertEqual(detail["baselines"][-1], baseline)
        props = self.w.subjects[self.w.nodes[nid]["subject"]]["props"]
        self.assertNotIn("checked_event", props)
        self.assertEqual(props["first_divergence"], store.h([]))
        self.change("independent observation in new epoch")
        checker.jobs.join()
        self.assertEqual(checker.covered_records, 1)

    def test_baseline_full_mismatch_refuses_with_exact_difference_retained(self):
        checker = self.checker()
        self.historical_gap(checker)
        request = self.baseline_request(checker)
        sid = self.w.nodes[self.r.CARDS[1]]["subject"]
        self.w.subjects[sid]["title"] = "Still missing from the log"
        lw.checkpoint(self.d, self.path, full=True, baseline=request)
        checker.jobs.join()
        report = checker.snapshot()
        self.assertEqual(report["state"], "diverged")
        self.assertFalse(report["baselines"])
        self.assertIn("refused", report["baseline_result"])
        self.assertTrue(any(d["thing"] == sid and d["live"] == "Still missing from the log"
                            for d in report["divergences"]))
        rows = [json.loads(s) for s in checker.journal.read_text().splitlines()]
        refusal = next(r for r in rows if r["kind"] == "baseline-refused")
        self.assertGreater(refusal["full_differences"], 0)

    def test_baseline_stale_inventory_cannot_forgive_new_repaired_gap(self):
        checker = self.checker()
        self.historical_gap(checker)
        request = self.baseline_request(checker)
        sid = self.w.nodes[self.r.CARDS[1]]["subject"]
        self.w.subjects[sid]["props"]["new_gap"] = "new discrepancy"
        store._MARKS.pop(self.w, None)
        self.change("second repair")
        checker.jobs.join()
        lw.checkpoint(self.d, self.path, full=True, baseline=request)
        checker.jobs.join()
        self.assertFalse(checker.snapshot()["baselines"])
        self.assertIn("refused", checker.snapshot()["baseline_result"])
        self.assertEqual(store.flatten(checker.replay.world), store.flatten(self.w))

    def test_baseline_retry_and_restart_keep_boundary_counters_and_new_first_divergence(self):
        checker = self.checker()
        self.historical_gap(checker)
        request = self.baseline_request(checker)
        lw.checkpoint(self.d, self.path, full=True, baseline=request)
        checker.jobs.join()
        self.change("new independent observation")
        checker.jobs.join()
        count = checker.covered_records
        lw.checkpoint(self.d, self.path, full=True, baseline=request)
        checker.jobs.join()
        self.assertEqual(checker.covered_records, count)
        self.assertEqual(len(checker.replay.baselines), 1)
        checker.close()
        self.checkers.remove(checker)
        other = lw.Checker(self.log.path, checker.journal)
        self.checkers.append(other)
        lw._CHECKERS[str(self.path)] = other
        lw.checkpoint(self.d, self.path, full=True)
        other.jobs.join()
        self.assertEqual(other.snapshot()["state"], "in-step", other.snapshot())
        self.assertEqual(other.covered_records, count)
        self.assertEqual(other.replay.baselines, checker.replay.baselines)
        sid = self.w.nodes[self.r.CARDS[1]]["subject"]
        self.w.subjects[sid]["props"]["later"] = "new epoch discrepancy"
        store._MARKS.pop(self.w, None)
        self.change("new divergence since baseline")
        other.jobs.join()
        report = other.snapshot()
        self.assertEqual(report["state"], "diverged")
        self.assertGreater(len(report["divergences"]), len(report["active_divergences"]))
        self.assertEqual(report["active_divergences"][0]["aspect"], "prop:later")
        self.assertIn("prop:later", report["line"])

    def test_baseline_receipt_failure_does_not_start_new_epoch(self):
        checker = self.checker()
        self.historical_gap(checker)
        request = self.baseline_request(checker)
        with patch.object(checker, "_write", side_effect=OSError("synthetic failed durable write")):
            lw.checkpoint(self.d, self.path, full=True, baseline=request)
            checker.jobs.join()
        self.assertEqual(checker.snapshot()["state"], "unavailable")
        self.assertFalse(checker.replay.baselines)

    def test_baseline_command_uses_documented_world_request_and_changes_no_world_facts(self):
        checker = self.checker()
        self.historical_gap(checker)
        ctx = store.safe_begin(self.d, self.path)
        self.d._store = ctx
        self.w.apply("create", self.w.root, None, {
            "kind": "note", "title": "Baseline request", "role": "log-world-baseline-request",
            "text": "Diagnosed historical refused write, not lost live state; evidence preserved.",
            "divergence_hash": checker.snapshot()["retained_divergence_hash"]}, "juniper")
        note = self.w.last_created
        store.safe_commit(ctx, self.d, "document baseline request", "juniper")
        checker.jobs.join()
        before = store.flatten(self.w)
        raw_log = self.log.path.read_bytes()
        self.d._store = store.safe_begin(self.d, self.path)
        result = self.d.repl("log-world baseline " + note)
        store.safe_commit(self.d._store, self.d, "log-world baseline " + note, "juniper")
        checker.jobs.join()
        self.assertIn("queued", result)
        self.assertEqual(checker.snapshot()["state"], "in-step", checker.snapshot())
        self.assertEqual(store.flatten(self.w), before)
        self.assertEqual(self.log.path.read_bytes(), raw_log)
        self.d._store = store.safe_begin(self.d, self.path)
        self.assertIn("refused", self.d.repl("log-world baseline " + self.r.CARDS[0]))
        store.safe_commit(self.d._store, self.d, "invalid baseline request", "juniper")

    def test_baseline_duplicate_queued_requests_do_not_reset_observation_epoch_twice(self):
        checker = self.checker()
        self.historical_gap(checker)
        request = self.baseline_request(checker)
        for _ in range(2):
            lw.checkpoint(self.d, self.path, full=True, baseline=request)
        checker.jobs.join()
        rows = [json.loads(s) for s in checker.journal.read_text().splitlines()]
        self.assertEqual(len([r for r in rows if r["kind"] == "baseline"]), 1)
        self.assertEqual(len(checker.replay.baselines), 1)

    def test_baseline_without_full_capture_refuses(self):
        checker = self.checker()
        self.historical_gap(checker)
        checker.submit(store.flatten(self.w), self.log.path.stat().st_size, f"e{self.w._eseq}",
                       baseline=self.baseline_request(checker))
        checker.jobs.join()
        self.assertFalse(checker.replay.baselines)
        self.assertEqual(checker.snapshot()["state"], "diverged")

    def test_baseline_cannot_set_aside_broken_log_integrity_even_with_matching_world(self):
        checker = self.checker()
        rec = {"seq": checker.replay.seq, "eseq": self.w._eseq}
        checker.replay.add(rec, "world", "record digest", "bad", "good", "broken state digest")
        checker.current = checker.replay.report()
        lw.checkpoint(self.d, self.path, full=True, baseline=self.baseline_request(checker))
        checker.jobs.join()
        self.assertFalse(checker.replay.baselines)
        self.assertIn("integrity", checker.snapshot()["baseline_result"])

    def test_baseline_receipt_with_wrong_historical_prefix_fails_closed_on_reload(self):
        checker = self.checker()
        self.historical_gap(checker)
        journal = Path(self.tmp.name) / "bad-baseline.jsonl"
        journal.write_text(checker.journal.read_text() + json.dumps({
            "kind": "baseline", "at": time.time(),
            "detail": {"set_aside_count": 1, "divergence_hash": "wrong"}}) + "\n", encoding="utf-8")
        other = lw.Checker(self.log.path, journal)
        self.checkers.append(other)
        other.submit(store.flatten(self.w), self.log.path.stat().st_size, f"e{self.w._eseq}", full=True)
        other.jobs.join()
        self.assertEqual(other.snapshot()["state"], "unavailable")
        self.assertIn("retained divergence prefix", other.snapshot()["line"])

    def restart_checker(self, checker):
        checker.close()
        self.checkers.remove(checker)
        other = lw.Checker(self.log.path, checker.journal)
        self.checkers.append(other)
        lw._CHECKERS[str(self.path)] = other
        lw.checkpoint(self.d, self.path, full=True)
        other.jobs.join()
        return other

    def public_evidence(self, evidence):
        lw.project(self.d, self.path)
        lw._CHECKERS[str(self.path)].jobs.join()
        text = self.w.subjects[self.w.nodes[evidence]["subject"]]["text"]
        return json.loads(text.split("\n\n", 1)[1])

    def test_refused_attempt_remains_public_after_ordinary_updates_and_restart(self):
        _, evidence, checker = self.status_fixture()
        self.historical_gap(checker)
        request = self.baseline_request(checker)
        request["divergence_hash"] = "stale reviewed inventory"
        lw.checkpoint(self.d, self.path, full=True, baseline=request)
        checker.jobs.join()
        attempt = checker.snapshot()["baseline_attempt"]
        self.assertIn("refused", attempt["result"])
        self.assertEqual(self.public_evidence(evidence)["last_baseline_refusal"], attempt)
        self.change("ordinary update must not erase operator result")
        checker.jobs.join()
        self.assertEqual(checker.snapshot()["baseline_attempt"], attempt)
        other = self.restart_checker(checker)
        self.assertEqual(other.snapshot()["baseline_attempt"], attempt)
        self.assertEqual(other.snapshot()["last_baseline_refusal"], attempt)
        self.assertEqual(self.public_evidence(evidence)["baseline_attempt"], attempt)
        self.d._store = store.safe_begin(self.d, self.path)
        self.assertIn("stale reviewed inventory", self.d.repl("log-world status"))
        store.safe_commit(self.d._store, self.d, "log-world status", "juniper")
        other.jobs.join()

    def test_acceptance_and_duplicate_keep_last_refusal_and_do_not_hide_new_divergence(self):
        _, evidence, checker = self.status_fixture()
        self.historical_gap(checker)
        request = self.baseline_request(checker)
        lw.checkpoint(self.d, self.path, baseline=request)  # no full capture
        checker.jobs.join()
        refused = checker.snapshot()["last_baseline_refusal"]
        lw.checkpoint(self.d, self.path, full=True, baseline=request)
        checker.jobs.join()
        accepted = checker.snapshot()["baseline_attempt"]
        self.assertIn("accepted", accepted["result"])
        self.assertEqual(checker.snapshot()["last_baseline_refusal"], refused)
        self.assertIn("not a claim that history is repaired", checker.replay.baselines[-1]["meaning"])
        self.assertEqual(self.public_evidence(evidence)["baseline_attempt"], accepted)
        self.change("independent observation")
        checker.jobs.join()
        sid = self.w.nodes[self.r.CARDS[1]]["subject"]
        self.w.subjects[sid]["title"] = "New post-baseline fault"
        lw.checkpoint(self.d, self.path, full=True, baseline=request)
        checker.jobs.join()
        self.assertEqual(checker.snapshot()["state"], "diverged")
        self.assertEqual(len(checker.replay.baselines), 1)
        self.assertIn("already recorded", checker.snapshot()["baseline_result"])
        count = checker.covered_records
        self.change("ordinary update cannot resume ended period")
        checker.jobs.join()
        self.assertEqual(checker.covered_records, count)
        other = self.restart_checker(checker)
        self.assertEqual(other.snapshot()["state"], "diverged")
        self.assertEqual(other.snapshot()["last_baseline_refusal"], refused)
        self.assertIn("already recorded", self.public_evidence(evidence)["baseline_attempt"]["result"])
        self.assertEqual(other.covered_records, count)

    def test_durable_acceptance_survives_missing_result_and_failed_world_projection(self):
        _, evidence, checker = self.status_fixture()
        self.historical_gap(checker)
        request = self.baseline_request(checker)
        write = checker._write

        def fail_result(row):
            if row["kind"] == "baseline-result":
                raise OSError("synthetic crash after durable baseline")
            write(row)

        with patch.object(checker, "_write", side_effect=fail_result):
            lw.checkpoint(self.d, self.path, full=True, baseline=request)
            checker.jobs.join()
        self.assertEqual(checker.snapshot()["state"], "unavailable")
        other = self.restart_checker(checker)
        self.assertEqual(other.snapshot()["state"], "in-step", other.snapshot())
        self.assertIn("accepted", other.snapshot()["baseline_result"])
        self.assertEqual((other.covered_records, other.covered_seconds), (0, 0))
        # A world projection failure cannot manufacture or erase journal acceptance.
        with patch.object(store, "safe_begin", side_effect=OSError("projection unavailable")):
            with self.assertRaises(OSError):
                lw.project(self.d, self.path)
        self.assertEqual(self.public_evidence(evidence)["baselines"], other.replay.baselines)
        self.assertEqual(len(other.replay.baselines), 1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    unittest.main()
