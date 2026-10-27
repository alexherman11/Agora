"""Offline only: fake handles, processes, clocks and receipts. No native calls."""
import ast
import copy
import json
import os
from pathlib import Path
import shutil
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import uuid

import sandbox_owned as owned
import sandbox_receipts as receipts

HERE = Path(__file__).resolve().parent


def owner(pid=10, parent=1):
    return {"pid": pid, "created": pid * 100, "exe": r"c:\fixture\engine.exe",
            "parent": {"pid": parent, "created": parent * 100,
                       "exe": r"c:\fixture\engine.exe" if parent >= 10 else r"c:\fixture\parent.exe"},
            "profile": r"c:\fixture\profile"}


class Backend:
    def __init__(self, result=None):
        self.dead, self.calls = set(), []
        self.result = result or {"status": "ended"}

    def gone(self, item):
        return item["pid"] in self.dead

    def finish(self, item):
        self.calls.append(item["pid"])
        if self.result["status"] == "ended":
            self.dead.add(item["pid"])
        return self.result


class CleanupTests(unittest.TestCase):
    def run_cleanup(self, state, backend=None, remaining=lambda: []):
        backend = backend or Backend()
        snapshots = []
        result = receipts.cleanup(state, backend, lambda s: snapshots.append(copy.deepcopy(s)), remaining)
        return result, backend, snapshots

    def test_legacy_and_incomplete_refuse_before_effect(self):
        for state in ({}, {"owners": [None]}, {"pids": [20], "owners": [owner()]},
                      {"owners": [owner(), owner()]},
                      {"owners": [{**owner(), "profile": None}]}):
            with self.subTest(state=state):
                result, backend, snapshots = self.run_cleanup(state)
                self.assertFalse(result["ok"])
                self.assertEqual(backend.calls, [])
                self.assertEqual(snapshots[-1]["cleanup"][-1]["status"], "refused")

    def test_pending_is_durable_before_effect(self):
        state = {"owners": [owner()]}
        saved = []
        backend = Backend()
        finish = backend.finish

        def effect(item):
            self.assertEqual(saved[-1]["cleanup"][-1]["status"], "pending")
            return finish(item)
        backend.finish = effect
        self.assertTrue(receipts.cleanup(state, backend, lambda s: saved.append(copy.deepcopy(s)),
                                         lambda: [])["ok"])
        self.assertEqual(saved[-1]["cleanup"][-1]["status"], "ended")

    def test_persistence_failure_prevents_effect(self):
        backend = Backend()
        with self.assertRaises(OSError):
            receipts.cleanup({"owners": [owner()]}, backend,
                             lambda _: (_ for _ in ()).throw(OSError("write denied")), lambda: [])
        self.assertEqual(backend.calls, [])

    def test_failure_keeps_old_taskkill_receipt_and_owner(self):
        old = {"status": "failed", "taskkill": {"returncode": 1, "stderr": "Access denied"}}
        state = {"owners": [owner()], "cleanup": [copy.deepcopy(old)]}
        result, backend, saved = self.run_cleanup(
            state, Backend({"status": "failed", "winerror": 5, "reason": "owned termination failed"}))
        self.assertFalse(result["ok"])
        self.assertEqual(saved[-1]["cleanup"][0], old)
        self.assertEqual(saved[-1]["owners"], [owner()])
        self.assertEqual(saved[-1]["cleanup"][-1]["winerror"], 5)

    def test_crash_unknown_never_replays_live_effect(self):
        state = {"owners": [owner()],
                 "cleanup": [{"pid": 10, "created": 1000, "status": "pending"}]}
        result, backend, _ = self.run_cleanup(state)
        self.assertFalse(result["ok"])
        self.assertEqual(backend.calls, [])
        backend.dead.add(10)
        result, backend, _ = self.run_cleanup(state, backend)
        self.assertTrue(result["ok"])
        self.assertEqual(backend.calls, [])

    def test_children_before_parents_and_cycle_refusal(self):
        result, backend, _ = self.run_cleanup({"owners": [owner(), owner(20, 10)]})
        self.assertTrue(result["ok"])
        self.assertEqual(backend.calls, [20, 10])
        result, backend, _ = self.run_cleanup({"owners": [owner(10, 20), owner(20, 10)]})
        self.assertFalse(result["ok"])
        self.assertEqual(backend.calls, [])

    def test_unknown_or_remaining_is_not_success(self):
        for left in (None, [40]):
            result, _, saved = self.run_cleanup({"owners": [owner()]}, remaining=lambda: left)
            self.assertFalse(result["ok"])
            self.assertFalse(saved[-1]["cleanup_complete"])

    def test_inconsistent_owned_parent_refuses_before_any_effect(self):
        child = owner(20, 10)
        child["parent"]["created"] += 1
        result, backend, _ = self.run_cleanup({"owners": [owner(), child]})
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "parent ownership inconsistent")
        self.assertEqual(backend.calls, [])

    def test_all_identity_fields_matter(self):
        self.assertTrue(receipts.same(owner(), copy.deepcopy(owner())))
        for key, value in (("pid", 11), ("created", 1001), ("exe", r"c:\other.exe"),
                           ("profile", r"c:\other"), ("profile", None)):
            self.assertFalse(receipts.same(owner(), {**owner(), key: value}))
        for key, value in (("pid", 2), ("created", 101), ("exe", r"c:\other.exe")):
            other = owner()
            other["parent"][key] = value
            self.assertFalse(receipts.same(owner(), other))

    def test_actual_close_keeps_manifest_and_does_not_adopt_windows(self):
        # Compile the real function with fake dependencies; no sandbox_window
        # import, DPI change, desktop enumeration, WMI or process call.
        tree = ast.parse((HERE / "sandbox_window.py").read_text(encoding="utf-8"))
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "close")
        scratch = HERE / ".tmp-agora" / ("receipt-test-" + uuid.uuid4().hex)
        os.makedirs(scratch)
        path = scratch / "fake.json"
        receipts.write(path, {"pids": [10], "owners": [owner()]})
        backend = Backend({"status": "failed", "winerror": 5})
        namespace = {"state_file": lambda _: path, "json": json,
                     "top_windows_quiet": lambda _: [(100, 99)], "time": SimpleNamespace(time_ns=lambda: 123)}
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(HERE / "sandbox_window.py"), "exec"), namespace)
        try:
            with patch.object(owned, "OwnedProcesses", return_value=backend):
                result = namespace["close"]("fixture", quiet=True)
                self.assertFalse(result["ok"])
                data = json.loads(path.read_text())
                self.assertEqual(data["remaining_window_pids"], [99])
                self.assertEqual(backend.calls, [10])  # never 99
                self.assertEqual(data["cleanup"][-1]["winerror"], 5)
                # Even empty windows cannot certify headless children.
                namespace["top_windows_quiet"] = lambda _: []
                backend.result = {"status": "ended"}
                self.assertFalse(namespace["close"]("fixture", quiet=True)["ok"])
                self.assertTrue(path.exists())
                lock = path.with_suffix(".cleanup-lock")
                lock.write_text("")
                self.assertFalse(namespace["close"]("fixture", quiet=True)["ok"])
                self.assertEqual(backend.calls, [10, 10])
        finally:
            shutil.rmtree(scratch)

    def test_metadata_updates_preserve_receipts_and_obey_same_lock(self):
        scratch = HERE / ".tmp-agora" / ("receipt-test-" + uuid.uuid4().hex)
        os.makedirs(scratch)
        path = scratch / "fake.json"
        state = {"owners": [owner()], "pids": [10], "launches": [{"status": "created"}]}
        try:
            receipts.write(path, state)
            updated = receipts.update_manifest(path, {"viewport": [320, 400, 1.5]})
            self.assertEqual(updated["owners"], state["owners"])
            self.assertEqual(updated["launches"], state["launches"])
            state["cleanup"] = [{"status": "pending", "pid": 10}]
            receipts.write(path, state)
            with self.assertRaises(RuntimeError):
                receipts.update_manifest(path, {"port": 9})
            self.assertEqual(json.loads(path.read_text()), state)
            with self.assertRaises(ValueError):
                receipts.update_manifest(path, {"owners": []})
            path.with_suffix(".cleanup-lock").write_text("")
            with self.assertRaises(FileExistsError):
                receipts.update_manifest(path, {})
        finally:
            shutil.rmtree(scratch)

    def test_local_paint_switches_is_a_presentation_update_other_unknown_keys_still_refuse(self):
        scratch = HERE / ".tmp-agora" / ("receipt-test-" + uuid.uuid4().hex)
        os.makedirs(scratch)
        path = scratch / "fake.json"
        state = {"owners": [owner()], "pids": [10], "launches": [{"status": "created"}]}
        try:
            receipts.write(path, state)
            updated = receipts.update_manifest(path, {"local_paint_switches": ["--disable-quic"]})
            self.assertEqual(updated["local_paint_switches"], ["--disable-quic"])
            self.assertEqual(updated["owners"], state["owners"])
            updated = receipts.update_manifest(path, {"pid": 11, "local_paint_switches": []})
            self.assertEqual(updated["pid"], 11)
            self.assertEqual(updated["local_paint_switches"], [])
            with self.assertRaises(ValueError):
                receipts.update_manifest(path, {"arbitrary": 1})
            with self.assertRaises(ValueError):
                receipts.update_manifest(path, {"local_paint_switches": [], "owners": []})
        finally:
            shutil.rmtree(scratch)

    def test_actual_launch_obeys_cleanup_lease_without_launching(self):
        tree = ast.parse((HERE / "sandbox_window.py").read_text(encoding="utf-8"))
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "start")
        scratch = HERE / ".tmp-agora" / ("receipt-test-" + uuid.uuid4().hex)
        os.makedirs(scratch)
        path = scratch / "fake.json"
        launches = []
        namespace = {"state_file": lambda _: path, "os": os,
                     "_start_locked": lambda *args, **kwargs: launches.append((args, kwargs)) or 10}
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(HERE / "sandbox_window.py"), "exec"), namespace)
        try:
            path.with_suffix(".cleanup-lock").write_text("")
            with self.assertRaises(FileExistsError):
                namespace["start"]("fixture", ["fake"])
            self.assertEqual(launches, [])
            path.with_suffix(".cleanup-lock").unlink()
            self.assertEqual(namespace["start"]("fixture", ["fake"]), 10)
            self.assertEqual(launches[-1][1], {"job": None})
            self.assertFalse(path.with_suffix(".cleanup-lock").exists())
        finally:
            shutil.rmtree(scratch)


class Native:
    """The existing Windows handle API, entirely fake."""
    def __init__(self):
        self.handle, self.err, self.code = 700, 0, 259
        self.ident = (1000, r"c:\fixture\engine.exe")
        self.closed, self.ended, self.opened = [], [], []
        self.c = SimpleNamespace(get_last_error=lambda: self.err, byref=lambda x: x)
        self.w = SimpleNamespace(DWORD=lambda: SimpleNamespace(value=0))
        self.k = self
        self.wait, self.end_ok = 0, True

    def OpenProcess(self, access, inherit, pid):
        self.opened.append((access, pid))
        return self.handle

    def CloseHandle(self, handle):
        self.closed.append(handle)

    def of_handle(self, handle):
        return self.ident

    def GetExitCodeProcess(self, handle, code):
        code.value = self.code
        return True

    def TerminateProcess(self, handle, code):
        self.ended.append(handle)
        return self.end_ok

    def WaitForSingleObject(self, handle, ms):
        return self.wait

    def identity(self, pid):
        return (100, r"c:\fixture\parent.exe")

    def argv(self, text):
        return json.loads(text)  # test-only parser, no native CommandLineToArgvW


class OwnedTests(unittest.TestCase):
    def backend(self, row=None, code=0, stderr=""):
        native = Native()
        row = row or {"ProcessId": 10, "ParentProcessId": 1,
                      "CommandLine": json.dumps(["engine.exe", "--user-data-dir=C:\\fixture\\profile"])}
        calls = []

        def run(argv, **kw):
            calls.append((argv, kw))
            return SimpleNamespace(returncode=code, stderr=stderr, stdout=json.dumps(row))
        return owned.OwnedProcesses(native, run=run), native, calls

    def test_same_handle_verified_then_ended(self):
        backend, native, calls = self.backend()
        self.assertEqual(backend.capture(10), owner())
        self.assertEqual(backend.finish(owner())["status"], "ended")
        self.assertEqual(native.ended, [700])
        self.assertEqual(native.closed, [700, 700])
        self.assertIn("ProcessId=10", calls[-1][0][-1])
        self.assertEqual(calls[-1][1]["timeout"], 3)

    def test_changed_creation_parent_executable_profile_refused(self):
        for field, val in (("created", 1001), ("exe", r"c:\wrong.exe"),
                           ("profile", r"c:\wrong")):
            backend, native, _ = self.backend()
            self.assertEqual(backend.finish({**owner(), field: val})["status"], "refused")
            self.assertEqual(native.ended, [])
        backend, native, _ = self.backend()
        other = owner()
        other["parent"]["created"] += 1
        self.assertEqual(backend.finish(other)["status"], "refused")
        self.assertEqual(native.ended, [])

    def test_access_denial_is_unknown_not_absent(self):
        backend, native, _ = self.backend()
        native.handle, native.err = 0, 5
        with self.assertRaises(OSError):
            backend.gone(owner())
        self.assertEqual(backend.finish(owner())["winerror"], 5)
        native.err = 87
        self.assertTrue(backend.gone(owner()))
        self.assertEqual(native.ended, [])

    def test_reused_pid_is_old_identity_gone_not_a_kill(self):
        backend, native, _ = self.backend()
        native.ident = (9999, r"c:\fixture\engine.exe")
        self.assertTrue(backend.gone(owner()))
        self.assertEqual(backend.finish(owner())["status"], "refused")
        self.assertEqual(native.ended, [])

    def test_denied_metadata_redacted_and_no_alternate_query(self):
        backend, native, calls = self.backend(code=1, stderr="Access is denied: SECRET https://private")
        result = backend.finish(owner())
        self.assertEqual(result["metadata_receipt"], {"returncode": 1, "stderr": "Access denied"})
        self.assertEqual(len(calls), 1)
        self.assertEqual(native.ended, [])
        self.assertNotIn("SECRET", json.dumps(result))

    def test_ambiguous_relative_and_unknown_parent_refused(self):
        for args in (["x", "--user-data-dir=C:\\one", "--sandbox-profile=C:\\two"],
                     ["x", "--user-data-dir"], ["x", "--user-data-dir=relative"]):
            backend, native, _ = self.backend(row={
                "ProcessId": 10, "ParentProcessId": 1, "CommandLine": json.dumps(args)})
            self.assertEqual(backend.finish(owner())["status"], "refused")
            self.assertEqual(native.ended, [])
        backend, native, _ = self.backend()
        native.identity = lambda pid: None
        self.assertEqual(backend.finish(owner())["status"], "refused")
        self.assertEqual(native.ended, [])

    def test_handle_change_during_metadata_refuses(self):
        backend, native, _ = self.backend()
        identities = iter([native.ident, (9999, native.ident[1])])
        native.of_handle = lambda _: next(identities)
        self.assertEqual(backend.finish(owner())["status"], "refused")
        self.assertEqual(native.ended, [])

    def test_no_profile_argument_does_not_certify_in_process_engine_profile(self):
        backend, native, _ = self.backend(row={
            "ProcessId": 10, "ParentProcessId": 1, "CommandLine": json.dumps(["python.exe", "fixture.py"])})
        captured = backend.capture(10)
        self.assertEqual(captured["profile"], "")
        self.assertEqual(backend.finish(captured),
                         {"status": "refused", "reason": "profile identity unknown"})
        self.assertEqual(native.ended, [])

    def test_parent_pid_reused_after_child_started_is_not_its_parent_identity(self):
        backend, native, _ = self.backend()
        native.identity = lambda _: (2000, r"c:\fixture\parent.exe")
        result = backend.finish(owner())
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["reason"], "owned metadata unavailable")
        self.assertEqual(native.ended, [])

    def test_termination_failure_and_wait_timeout_are_receipts(self):
        backend, native, _ = self.backend()
        native.end_ok, native.err = False, 5
        self.assertEqual(backend.finish(owner())["winerror"], 5)
        native.end_ok, native.wait = True, 258
        self.assertEqual(backend.finish(owner()), {"status": "pending", "wait": 258})


class DiagnosticTests(unittest.TestCase):
    def recorder(self):
        saved, clock = [], [0.]
        diag = receipts.Diagnostics(lambda x: saved.append(copy.deepcopy(x)),
                                    clock=lambda: clock[0], child_id="fixture-child")
        return diag, saved, clock

    def handshake(self, diag, child="fixture-child", nav=7, **kw):
        return diag.child_ready(child, nav, top_channel=kw.get("top", False),
                                child_channel=False, messages_enabled=False, host_objects_allowed=False)

    def test_timing_deadline_persisted_before_caller_closes(self):
        diag, saved, clock = self.recorder()
        diag.event("initializing")
        clock[0] = 15
        diag.deadline()
        self.assertEqual(saved[-1]["events"][-1], {"phase": "deadline_fired", "elapsed_ms": 15000.0})
        self.assertTrue(saved[-1]["deadline_fired"])
        exc = RuntimeError("Operation aborted SECRET")
        exc.HResult = -2147467260
        diag.exception("initialization_failed", exc)
        self.assertEqual(saved[-1]["events"][-1]["error"]["hresult"], -2147467260)
        self.assertNotIn("SECRET", json.dumps(saved))
        self.assertFalse(diag.passed)

    def test_navigation_is_not_child_ready(self):
        diag, _, _ = self.recorder()
        diag.navigation(7, True)
        self.assertFalse(diag.passed)
        self.assertFalse(self.handshake(diag, child="stale"))
        self.assertFalse(self.handshake(diag, nav=6))
        self.assertFalse(self.handshake(diag, top=True))
        self.assertTrue(self.handshake(diag))
        self.assertTrue(diag.passed)
        diag.navigation(8, False)
        self.assertFalse(self.handshake(diag, nav=8))
        self.assertFalse(diag.passed)

    def test_native_failure_events_invalidate_success(self):
        for phase in ("browser_process_exited", "process_failed"):
            diag, saved, _ = self.recorder()
            diag.navigation(7, True)
            self.assertTrue(self.handshake(diag))
            diag.event(phase, kind="BrowserProcessExited", exit_code=1)
            self.assertFalse(diag.passed)
            self.assertFalse(self.handshake(diag))
            self.assertTrue(saved[-1]["process_failure"])

    def test_expected_disposal_exit_is_recorded_without_inventing_crash(self):
        diag, saved, _ = self.recorder()
        diag.navigation(7, True)
        self.assertTrue(self.handshake(diag))
        diag.event("disposing")
        diag.event("browser_process_exited", kind="Normal")
        self.assertTrue(diag.passed)
        self.assertEqual(saved[-1]["events"][-1]["phase"], "browser_process_exited")

    def test_deadline_and_truncation_refuse_late_success(self):
        diag, saved, _ = self.recorder()
        diag.navigation(7, True)
        diag.deadline()
        self.assertFalse(self.handshake(diag))
        diag, saved, _ = self.recorder()
        diag.navigation(7, True)
        for _ in range(130):
            diag.event("handshake_wait")
        self.assertEqual(len(saved[-1]["events"]), 128)
        self.assertFalse(self.handshake(diag))

    def test_unreviewed_data_and_exception_messages_do_not_escape(self):
        diag, saved, _ = self.recorder()
        for values in ({"url": "https://private"}, {"error": {"raw": "secret"}},
                       {"kind": "unbounded private text"}, {"exit_code": "secret"}):
            with self.assertRaises(ValueError):
                diag.event("native_failed", **values)
        with self.assertRaises(ValueError):
            diag.navigation("secret", True)
        self.assertFalse(diag.data["navigation_success"])
        exc = owned.MetadataUnavailable({"stderr": "SECRET", "reason": "SECRET", "returncode": 7})
        diag.exception("native_failed", exc)
        self.assertNotIn("SECRET", json.dumps(saved))
        self.assertEqual(saved[-1]["events"][-1]["error"]["metadata_receipt"]["returncode"], 7)

    def test_retained_e_abort_has_no_deadline_evidence(self):
        old = json.loads((HERE / "browsing" / "diagnostics" / "retained-failure.json").read_text())
        self.assertEqual(old["hresult"], -2147467260)
        self.assertEqual(old["stage"], "initialization_failed")
        self.assertNotIn("deadline_fired", old)
        self.assertNotIn("events", old)
        # No reconstruction of timing or cause from HRESULT alone.


if __name__ == "__main__":
    unittest.main()
