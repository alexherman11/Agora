# health: room test
"""Real explore/Session/store and parent dispatch, using disposable synthetic worlds."""
# ruff: noqa: E402
import contextlib
import atexit
import io
import json
import os
from pathlib import Path
import queue
import shutil
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "window-lab"))
sys.path.insert(0, str(HERE.parents[1] / "codex-residents"))
os.environ.setdefault("HOUSE_CLAUDE", "claude")
import agora_tmp
import charter
import codex_resident
import deskd
import explore
import export_docs
import house
import roomworld
import store
import workshop


class WriterAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(agora_tmp.directory("admission-"))
        self.path = self.root / "copy.pickle"
        self.owner, rooms = roomworld.build(say=False)
        self.target = rooms.CARDS[0]
        self.owner.world.apply("create", self.owner.world.root, None,
                               dict(kind="note", title=charter.DEFAULT_TITLE, role=charter.ROLE,
                                    text="- Tests stay on a copy."), "jeff")
        self.patches = [
            patch.object(explore, "SESSIONS", self.root),
            patch.object(export_docs, "SESSIONS", self.root),
            patch.object(deskd, "SESSIONS", self.root),
            patch.dict(os.environ, {"DESKD": "off", "DESKD_HOLD": "off", "DESKD_TRACE": "off"}),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)
        with patch.object(explore, "holder_of", return_value=None):
            store.genesis(self.owner, self.path)
            explore.save_desk(self.path, self.owner)
        self.before_events = list(self.owner.world.events)
        self.before_files = self.files()
        self.before_stamps = {name: (self.root / name).stat().st_mtime_ns
                              for name in self.before_files}
        self.addCleanup(self.cleanup)

    def cleanup(self):
        deskd._DESKS.pop(str(self.path), None)
        shutil.rmtree(self.root, ignore_errors=True)

    def files(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes()
                for p in self.root.rglob("*") if p.is_file()}

    def cli(self, line="", flags=()):
        out = io.StringIO()
        with patch.object(sys, "argv", ["explore.py", "copy", *flags]), \
                patch.object(sys, "stdin", io.StringIO(line)), \
                patch.object(explore, "away_in", return_value=None), \
                patch.object(atexit, "register"), contextlib.redirect_stdout(out):
            try:
                explore.main()
            finally:
                explore.release_lock(self.root / "copy.lock")
        return out.getvalue()

    def assert_intact(self):
        self.assertEqual(self.before_files, self.files())
        self.assertEqual(self.before_stamps,
                         {name: (self.root / name).stat().st_mtime_ns for name in self.before_files})
        self.assertEqual(self.before_events, self.owner.world.events)
        ok, lines = store.check(self.owner.world, store.Log(store.log_path(self.path)))
        self.assertTrue(ok, lines)

    def test_refused_explore_has_no_event_record_file_or_execution(self):
        with patch.object(explore, "holder_of", return_value=os.getpid() + 100000), \
                patch.object(explore, "load_desk") as load, \
                patch.object(store, "safe_begin") as begin, \
                patch.object(store, "safe_commit") as commit, \
                patch.object(deskd, "_take_lease") as lease:
            with self.assertRaisesRegex(RuntimeError, "held by its world server"):
                self.cli(f'look {self.target}; do comment {self.target} line="must not exist"\n')
            for fn in (load, begin, commit, lease):
                fn.assert_not_called()
        self.assert_intact()

    def test_refused_lease_free_session_has_no_event_record_file_or_execution(self):
        for released in (False, True):
            with self.subTest(released=released), \
                    patch.object(explore, "holder_of", return_value=os.getpid() + 100000), \
                    patch.object(explore, "load_desk") as load, \
                    patch.object(store, "safe_begin") as begin, \
                    patch.object(store, "safe_commit") as commit, \
                    patch.object(deskd, "_take_lease") as lease, \
                    patch.object(deskd, "RELEASED", {"copy"} if released else set()):
                with self.assertRaisesRegex(deskd.BadRequest, "held by its world server"):
                    with deskd.Session("copy", "house"):
                        self.fail("foreign request admitted")
                for fn in (load, begin, commit, lease):
                    fn.assert_not_called()
            self.assert_intact()

    def test_owner_and_genuinely_offline_writer_still_work(self):
        for holder in (os.getpid(), None):
            with self.subTest(holder=holder), patch.object(explore, "holder_of", return_value=holder):
                out = self.cli(f'look {self.target}; do comment {self.target} line="allowed"\n')
                self.assertNotIn("ERR", out)
                latest = explore.load_desk(self.path)
                ok, lines = store.check(latest.world, store.Log(store.log_path(self.path)))
                self.assertTrue(ok, lines)
        sid = latest.world.nodes[self.target]["subject"]
        self.assertEqual(2, sum(c["text"] == "allowed" for c in latest.world.subjects[sid]["comments"]))

    def test_offline_read_and_charter_read_do_not_write(self):
        with patch.object(explore, "holder_of", return_value=os.getpid() + 100000), \
                patch.object(store, "safe_begin") as begin, \
                patch.object(store, "safe_commit") as commit:
            reading = charter.live_reading("copy")
            self.assertIn("Tests stay on a copy", reading.text)
            self.cli(flags=("--dump",))
            with deskd.Session("copy", "reader", read=True) as d:
                self.assertIn("Tests stay on a copy", charter.read(d.world).text)
            begin.assert_not_called()
            commit.assert_not_called()
        self.assert_intact()

    def test_admission_is_under_lock_and_final_save_guard_remains(self):
        def foreign(path):
            self.assertTrue(path.with_suffix(".lock").exists())
            return os.getpid() + 100000
        with patch.object(explore, "holder_of", side_effect=foreign):
            with self.assertRaises(RuntimeError):
                self.cli("look\n")
            with self.assertRaises(deskd.BadRequest):
                with deskd.Session("copy", "house"):
                    self.fail("admitted")
        with patch.object(explore, "holder_of", return_value=os.getpid() + 100000):
            with self.assertRaises(RuntimeError):
                explore.save_desk(self.path, self.owner)
        self.assert_intact()

    def parent(self):
        h = SimpleNamespace(world="copy", dir=self.root / "house", fake=True)
        h.dir.mkdir()
        # Real House.act with only its HTTP transport replaced by an in-process
        # owner Session; no public endpoint or live world is contacted.
        h.act = lambda who, line: house.House.act(h, who, line)
        worker = workshop.Worker(h, self.target, self.root, "worker/test", "jeff")
        worker.events = queue.Queue()
        worker.state["session_provider"] = "codex"
        worker.log = MagicMock()
        return worker

    def owner_do(self, world, who, line, *args):
        self.assertEqual("copy", world)
        self.assertEqual("house", who)
        from desk import split_batch
        with deskd.Session(world, who) as d:
            out = []
            for part in split_batch(line):
                ctx = store.safe_begin(d, self.path)
                out.append(d.repl(part))
                store.safe_commit(ctx, d, part, who)
            return "\n".join(out)

    def assert_one_receipt_and_matching_log(self, expected):
        latest = explore.load_desk(self.path)
        sid = latest.world.nodes[self.target]["subject"]
        receipts = [c for c in latest.world.subjects[sid]["comments"]
                    if "charter read (reason: compaction)" in c["text"]]
        self.assertEqual(1, len(receipts))
        self.assertIn(f"as of event {expected.event}", receipts[0]["text"])
        ok, lines = store.check(latest.world, store.Log(store.log_path(self.path)))
        self.assertTrue(ok, lines)

    def test_codex_compaction_parent_once_actual_read_provenance_and_log(self):
        worker = self.parent()
        args = SimpleNamespace(world="copy", target=self.target, actor="worker-copy")
        emitted = []
        expected = charter.live_reading("copy")
        with patch.object(charter, "report", wraps=charter.report) as report:
            codex_resident.refresh_charter(MagicMock(), "thread", args, emitted.append)
            report.assert_not_called()  # helper reads/injects only
        self.assert_intact()
        event = emitted[-1]
        # The read occurred before a subsequent owner event: parent must not
        # manufacture provenance by reading the newer world at receipt time.
        with patch.object(explore, "holder_of", return_value=os.getpid()):
            self.owner_do("copy", "house",
                          f'look {self.target}; do prop {self.target} after_read=yes')
        worker.events.put(event)
        worker.events.put(event)
        with patch.object(explore, "holder_of", return_value=os.getpid()), \
                patch.object(house, "deskd_do", side_effect=self.owner_do) as owner:
            worker.turns_ended()
            worker.turns_ended()
            self.assertEqual(1, owner.call_count)
        self.assert_one_receipt_and_matching_log(expected)
        self.assertEqual("written", worker.state["charter_receipts"][event["receipt_id"]])

    def test_claude_hook_parent_once_actual_read_provenance_and_log(self):
        worker = self.parent()
        channel = worker._charter_channel()
        expected = charter.live_reading("copy")
        argv = ["charter.py", "--world", "copy", "--target", self.target,
                "--actor", "worker-copy", "--hook", "--receipt-channel", str(channel)]
        with patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()) as out, \
                patch.object(charter, "report", wraps=charter.report) as report:
            charter.main()
            report.assert_not_called()
        context = json.loads(out.getvalue())["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(expected.text, context)
        # Only helper bookkeeping has changed; the snapshot and journal have not.
        for name, data in self.before_files.items():
            self.assertEqual(data, (self.root / name).read_bytes())
            self.assertEqual(self.before_stamps[name], (self.root / name).stat().st_mtime_ns)
        with patch.object(explore, "holder_of", return_value=os.getpid()), \
                patch.object(house, "deskd_do", side_effect=self.owner_do) as owner:
            worker.turns_ended()
            worker.turns_ended()
            self.assertEqual(1, owner.call_count)
        self.assert_one_receipt_and_matching_log(expected)

    def test_claude_handoff_survives_parent_reload(self):
        worker = self.parent()
        channel = worker._charter_channel()
        event = charter.read_event(charter.live_reading("copy"))
        charter.write_read_event(channel, event)
        restored = workshop.Worker(worker.house, self.target, self.root, "worker/test", "jeff")
        restored.log = MagicMock()
        with patch.object(explore, "holder_of", return_value=os.getpid()), \
                patch.object(house, "deskd_do", side_effect=self.owner_do) as owner:
            restored.turns_ended()
            restored.turns_ended()
            self.assertEqual(1, owner.call_count)
        self.assertEqual("written", restored.state["charter_receipts"][event["receipt_id"]])

    def test_failed_injection_goes_to_parent_without_helper_world_write(self):
        worker = self.parent()
        client = MagicMock()
        client.request.side_effect = RuntimeError("stand-in transport unavailable")
        args = SimpleNamespace(world="copy", target=self.target, actor="worker-copy")
        emitted = []
        with patch.object(charter, "report", wraps=charter.report) as report:
            codex_resident.refresh_charter(client, "thread", args, emitted.append)
            report.assert_not_called()
        self.assert_intact()
        self.assertEqual("charter_unavailable", emitted[-1]["subtype"])
        worker.events.put(emitted[-1])
        with patch.object(explore, "holder_of", return_value=os.getpid()), \
                patch.object(house, "deskd_do", side_effect=self.owner_do) as owner:
            worker.turns_ended()
            self.assertEqual(1, owner.call_count)
        latest = explore.load_desk(self.path)
        sid = latest.world.nodes[self.target]["subject"]
        self.assertIn("reinjection unavailable", latest.world.subjects[sid]["comments"][-1]["text"])
        ok, lines = store.check(latest.world, store.Log(store.log_path(self.path)))
        self.assertTrue(ok, lines)

    def test_failed_parent_receipt_recorded_and_not_retried(self):
        worker = self.parent()
        event = charter.read_event(charter.live_reading("copy"))
        worker.events.put(event)
        worker.events.put(event)
        with patch.object(house, "deskd_do", return_value="ERR owner refused") as owner:
            worker.turns_ended()
            self.assertEqual(1, owner.call_count)
        self.assertEqual("failed", worker.state["charter_receipts"][event["receipt_id"]])
        worker.log.assert_any_call("charter_receipt_failed",
                                  {"read": event["receipt_id"], "reason": "RuntimeError"})

    def test_ambiguous_parent_write_is_not_replayed_after_state_reload(self):
        worker = self.parent()
        event = charter.read_event(charter.live_reading("copy"))
        worker.state["charter_receipts"] = {event["receipt_id"]: "unknown"}
        worker.save()  # simulates a crash after admission, before acknowledgement
        restored = workshop.Worker(worker.house, self.target, self.root, "worker/test", "jeff")
        restored.events = queue.Queue()
        restored.events.put(event)
        with patch.object(house, "deskd_do") as owner:
            restored.turns_ended()
            owner.assert_not_called()
        self.assertEqual("unknown", restored.state["charter_receipts"][event["receipt_id"]])


if __name__ == "__main__":
    unittest.main()
