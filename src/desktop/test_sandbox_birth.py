"""Offline birth/order/cleanup tests. No OS query, launch, input or termination."""
import copy
import ast
import json
import os
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import uuid

import sandbox_birth as birth
import sandbox_owned
import sandbox_receipts
from test_sandbox_receipts import Native, Backend


class BirthTests(unittest.TestCase):
    def facts(self):
        return birth.intent([r"C:\fixture\engine.exe", "--sandbox-profile=C:\\fixture\\profile"],
                            {"pid": 1, "created": 100, "exe": r"c:\fixture\parent.exe"},
                            "WinSta0\\agora-sandbox-fixture")

    def owner(self):
        return birth.capture(self.facts(), 10, (1000, r"c:\fixture\engine.exe"))

    def test_complete_before_resume(self):
        state, launch, saved = {}, {}, []
        def resume():
            self.assertEqual(saved[-1]["launches"][0]["status"], "resume-pending")
            self.assertTrue(birth.valid(saved[-1]["owners"][0]))
            return 1
        state["launches"] = [launch]
        birth.persist_then_resume(state, launch, self.owner(),
                                 lambda s: saved.append(copy.deepcopy(s)), resume)
        self.assertEqual(launch["status"], "running")
        self.assertEqual(len(saved), 2)

    def test_failed_persistence_never_resumes(self):
        calls = []
        with self.assertRaises(OSError):
            birth.persist_then_resume({}, {}, self.owner(),
                                      lambda _: (_ for _ in ()).throw(OSError("denied")),
                                      lambda: calls.append(True))
        self.assertEqual(calls, [])

    def test_unknown_resume_not_repeated(self):
        calls, launch = [], {}
        with self.assertRaises(RuntimeError):
            birth.persist_then_resume({}, launch, self.owner(), lambda _: None,
                                      lambda: calls.append(True) or 0xffffffff)
        self.assertEqual(calls, [True])
        self.assertEqual(launch["status"], "resume-unknown")

    def test_launch_arguments_fail_before_create(self):
        parent = self.facts()["parent"]
        for args in ([], ["relative.exe"], [r"C:\x.exe", "--sandbox-profile=relative"],
                     [r"C:\x.exe", "--sandbox-profile=C:\\a", "--user-data-dir=C:\\b"],
                     [r"C:\x.exe", "--sandbox-profile"]):
            with self.subTest(args=args), self.assertRaises(ValueError):
                birth.intent(args, parent, "WinSta0\\agora-sandbox-fixture")
        with self.assertRaises(ValueError):
            birth.intent([r"C:\x.exe"], parent, "WinSta0\\Default")

    def test_capture_missing_or_different_identity_refuses(self):
        for identity in (None, (1000, r"c:\other.exe"), (99, r"c:\fixture\engine.exe")):
            with self.assertRaises(ValueError):
                birth.capture(self.facts(), 10, identity)

    def test_cleanup_uses_same_birth_handle_without_metadata_fallback(self):
        native = Native()
        backend = sandbox_owned.OwnedProcesses(native, run=lambda *a, **k: self.fail("WMI"))
        result = backend.finish(self.owner())
        self.assertEqual(result["status"], "ended")
        self.assertEqual(result["scope"], "recorded direct child only")
        self.assertEqual(native.ended, [700])
        self.assertEqual(native.closed, [700])

    def test_reused_birth_refuses_and_never_terminates(self):
        for identity in ((9999, r"c:\fixture\engine.exe"), (1000, r"c:\other.exe"), None):
            native = Native()
            native.ident = identity
            result = sandbox_owned.OwnedProcesses(native).finish(self.owner())
            self.assertEqual(result["status"], "refused")
            self.assertEqual(native.ended, [])

    def test_denial_remains_unknown_without_alternate_query(self):
        native = Native()
        native.handle, native.err = 0, 5
        backend = sandbox_owned.OwnedProcesses(native, run=lambda *a, **k: self.fail("WMI"))
        self.assertEqual(backend.finish(self.owner())["winerror"], 5)
        with self.assertRaises(OSError):
            backend.gone(self.owner())
        self.assertEqual(native.ended, [])

    def test_incomplete_birth_never_opens_or_terminates(self):
        for field in ("desktop", "parent", "created", "profile", "profile_scope"):
            item = self.owner()
            del item[field]
            native = Native()
            self.assertEqual(sandbox_owned.OwnedProcesses(native).finish(item)["status"], "refused")
            self.assertEqual(native.opened, [])

    def test_no_profile_is_only_launch_absence_not_engine_profile_proof(self):
        item = birth.capture(birth.intent([r"C:\fixture\engine.exe"], self.facts()["parent"],
                                         self.facts()["desktop"]), 10,
                             (1000, r"c:\fixture\engine.exe"))
        self.assertEqual(item["profile"], "")
        self.assertEqual(item["profile_scope"], "launch argument only")
        self.assertTrue(birth.valid(item))

    def test_cleanup_refuses_changed_launch_fields_before_any_effect(self):
        item = self.owner()
        for field, replacement in (("parent", {**item["parent"], "created": 99}),
                                   ("desktop", "WinSta0\\agora-sandbox-other"),
                                   ("profile", r"c:\other"), ("exe", r"c:\other.exe"),
                                   ("created", 1001)):
            state = {"owners": [copy.deepcopy(item)], "pids": [10],
                     "launches": [{"pid": 10, "owner": copy.deepcopy(item),
                                   "intent": self.facts(), "status": "running"}]}
            state["owners"][0][field] = replacement
            backend = Backend()
            result = sandbox_receipts.cleanup(state, backend, lambda _: None, lambda: [])
            self.assertFalse(result["ok"])
            self.assertEqual(backend.calls, [])

    def test_real_launcher_suspends_and_persists_before_child_code(self):
        here = Path(__file__).resolve().parent
        scratch = here / ".tmp-agora" / ("birth-test-" + uuid.uuid4().hex)
        os.makedirs(scratch)
        self.addCleanup(shutil.rmtree, scratch)
        path = scratch / "fake.json"
        node = next(n for n in ast.parse((here / "sandbox_window.py").read_text(encoding="utf-8")).body
                    if isinstance(n, ast.FunctionDef) and n.name == "_start_locked")
        calls = []
        native = Native()
        class Resume:
            def __call__(self, handle):
                data = json.loads(path.read_text())
                self_test.assertTrue(birth.valid(data["owners"][0]))
                self_test.assertEqual(data["launches"][0]["status"], "resume-pending")
                calls.append("resume")
                return 1
        def create(executable, line, sa, ta, inherit, flags, env, cwd, si, pi):
            self.assertTrue(flags & 4)
            self.assertEqual(executable, r"C:\fixture\engine.exe")
            self.assertEqual(json.loads(path.read_text())["launches"][0]["status"], "pending")
            pi.dwProcessId, pi.hProcess, pi.hThread = 10, 700, 701
            calls.append("create-suspended")
            return True
        self_test = self
        k = SimpleNamespace(CreateProcessW=create, ResumeThread=Resume(), CloseHandle=lambda _: None)
        ns = {"state_file": lambda _: path, "os": os, "json": json,
              "time": SimpleNamespace(time=lambda: 1), "desktop": lambda *a, **k: (99, "agora-sandbox-fixture"),
              "STARTUPINFOW": SimpleNamespace, "PROCESS_INFORMATION": SimpleNamespace,
              "subprocess": subprocess, "sys": SimpleNamespace(exit=lambda _: self.fail("exit")),
              "k32": k, "wt": SimpleNamespace(HANDLE=int, DWORD=int),
              "ctypes": SimpleNamespace(sizeof=lambda _: 1, create_unicode_buffer=lambda s: s,
                                         byref=lambda v: v)}
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(here / "sandbox_window.py"), "exec"), ns)
        with patch.object(sandbox_owned, "OwnedProcesses", return_value=SimpleNamespace(native=native)):
            self.assertEqual(ns["_start_locked"]("fixture", [r"C:\fixture\engine.exe"]), 10)
        self.assertEqual(calls, ["create-suspended", "resume"])
        self.assertEqual(json.loads(path.read_text())["launches"][0]["status"], "running")


if __name__ == "__main__":
    unittest.main()
