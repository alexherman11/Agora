"""Offline job admission/order/closure tests; no native process or job effects."""
import ast
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import uuid

import sandbox_birth as birth
import sandbox_job as job
import sandbox_owned
from test_sandbox_receipts import Native

PARENT = {"pid": os.getpid(), "created": 100, "exe": r"c:\fixture\parent.exe"}


class JobNative:
    def __init__(self):
        self.calls = []
        self.pids = [10, 11]
        self.limits = job.KILL_ON_CLOSE
        self.delay = False
        self.fail_query = False
        self.fail_assign = False

    def create(self):
        self.calls.append("create-job")
        return 888

    def verify(self, handle):
        assert handle == 888
        if self.limits != job.KILL_ON_CLOSE:
            raise RuntimeError("limits changed")

    def assign(self, handle, process):
        self.verify(handle)
        self.calls.append("assign")
        if self.fail_assign:
            raise OSError("denied")

    def snapshot(self, handle):
        self.verify(handle)
        if self.fail_query:
            raise OSError("denied")
        return {"pids": list(self.pids), "active": len(self.pids), "total": 2, "terminated": 0}

    def terminate(self, handle):
        self.verify(handle)
        self.calls.append("terminate-job")
        if not self.delay:
            self.pids = []

    def close(self, handle):
        self.calls.append("close-job")


class JobTests(unittest.TestCase):
    def scope(self, name=None):
        native = JobNative()
        clock = [0]
        scope = job.Scope(name or uuid.uuid4().hex, native=native, parent=PARENT,
                          clock=lambda: clock[0], pause=lambda _: clock.__setitem__(0, clock[0] + 1))
        self.enterContext(scope)
        return scope, native

    def state(self, scope):
        facts = birth.intent([r"C:\fixture\engine.exe"], PARENT,
                             "WinSta0\\agora-sandbox-fixture")
        owner = birth.capture(facts, 10, (1000, r"c:\fixture\engine.exe"))
        owner["job_id"] = scope.descriptor["id"]
        return {"job": copy.deepcopy(scope.descriptor), "pids": [10], "owners": [owner],
                "launches": [{"pid": 10, "owner": copy.deepcopy(owner), "intent": facts,
                              "status": "running", "job_assigned": True,
                              "job_id": scope.descriptor["id"]}]}

    def test_child_and_grandchild_empty_only_after_durable_intent(self):
        scope, native = self.scope()
        state, saved = self.state(scope), []
        def persist(data):
            saved.append(copy.deepcopy(data))
            if len(saved) == 1:
                self.assertNotIn("terminate-job", native.calls)
                self.assertEqual(data["cleanup"][-1]["before"]["pids"], [10, 11])
                self.assertEqual(data["cleanup"][-1]["status"], "pending")
        self.assertTrue(job.cleanup(state, scope, persist)["ok"])
        self.assertEqual(native.calls.count("terminate-job"), 1)
        self.assertEqual(saved[-1]["cleanup"][-1]["after"]["active"], 0)
        self.assertTrue(state["cleanup_complete"])
        self.assertIn("unknown", state["runtime_closure"])

    def test_pending_persistence_failure_has_no_termination(self):
        scope, native = self.scope()
        with self.assertRaises(OSError):
            job.cleanup(self.state(scope), scope, lambda _: (_ for _ in ()).throw(OSError()))
        self.assertNotIn("terminate-job", native.calls)

    def test_result_persistence_failure_is_unknown(self):
        scope, _ = self.scope()
        state, saves = self.state(scope), []
        def persist(data):
            saves.append(copy.deepcopy(data))
            if len(saves) == 2:
                raise OSError("denied")
        self.assertFalse(job.cleanup(state, scope, persist)["ok"])
        self.assertFalse(saves[-1]["cleanup_complete"])
        self.assertEqual(saves[-1]["job_closure"], "unknown")

    def test_deadline_keeps_unknown_and_does_not_repeat_effect(self):
        scope, native = self.scope()
        native.delay = True
        state = self.state(scope)
        self.assertFalse(job.cleanup(state, scope, lambda _: None, timeout=2)["ok"])
        self.assertEqual(state["cleanup"][-1]["status"], "unknown")
        self.assertFalse(job.cleanup(state, scope, lambda _: None)["ok"])
        self.assertEqual(native.calls.count("terminate-job"), 1)
        native.pids = []
        self.assertTrue(job.cleanup(state, scope, lambda _: None)["ok"])
        self.assertEqual(native.calls.count("terminate-job"), 1)

    def test_query_denial_has_no_effect_or_empty_claim(self):
        scope, native = self.scope()
        native.fail_query = True
        state = self.state(scope)
        with self.assertRaises(OSError):
            job.cleanup(state, scope, lambda _: None)
        self.assertFalse(state["cleanup_complete"])
        self.assertNotIn("terminate-job", native.calls)

    def test_post_termination_query_denial_keeps_unknown_receipt(self):
        scope, native = self.scope()
        state, saved = self.state(scope), []
        def terminate(handle):
            native.calls.append("terminate-job")
            native.fail_query = True
        native.terminate = terminate
        self.assertFalse(job.cleanup(state, scope, lambda s: saved.append(copy.deepcopy(s)))["ok"])
        self.assertEqual(saved[-1]["cleanup"][-1]["status"], "unknown")
        self.assertFalse(saved[-1]["cleanup_complete"])
        self.assertEqual(native.calls.count("terminate-job"), 1)

    def test_termination_denial_is_not_closed_or_replayed(self):
        scope, native = self.scope()
        state = self.state(scope)
        def terminate(handle):
            native.calls.append("terminate-job")
            raise OSError("denied")
        native.terminate = terminate
        self.assertFalse(job.cleanup(state, scope, lambda _: None)["ok"])
        self.assertFalse(job.cleanup(state, scope, lambda _: None)["ok"])
        self.assertEqual(native.calls.count("terminate-job"), 1)
        self.assertEqual(state["job_closure"], "unknown")

    def test_receipt_or_scope_mismatch_never_adopts_job(self):
        scope, native = self.scope()
        for changed in ("id", "limits", "creator"):
            state = self.state(scope)
            state["job"][changed] = "forged"
            with self.subTest(changed=changed), self.assertRaises(RuntimeError):
                job.live(scope.name, state)
        with self.assertRaises(RuntimeError):
            job.live("absent", self.state(scope))
        with self.assertRaises(RuntimeError):
            scope.admit("wrong", PARENT, {})
        with self.assertRaises(RuntimeError):
            scope.admit(scope.name, {**PARENT, "created": 999}, {})
        with patch.object(scope, "pid", -1), self.assertRaises(RuntimeError):
            job.live(scope.name, self.state(scope))
        self.assertNotIn("terminate-job", native.calls)

    def test_no_legacy_mixed_adoption(self):
        scope, _ = self.scope()
        for state in ({"pids": [77]}, {"launches": [{}]}, {"job": {"id": "old"}}):
            with self.assertRaises(RuntimeError):
                scope.admit(scope.name, PARENT, state)
        scope.admit(scope.name, PARENT, {})
        scope.admit(scope.name, PARENT, self.state(scope))

    def test_birth_or_membership_receipt_change_refuses_before_effect(self):
        scope, native = self.scope()
        variants = []
        for key in ("owners", "launches", "pids"):
            state = self.state(scope)
            state[key] = []
            variants.append(state)
        for key, value in (("job_assigned", False), ("job_id", "other"), ("status", "pending")):
            state = self.state(scope)
            state["launches"][0][key] = value
            variants.append(state)
        state = self.state(scope)
        state["owners"][0]["created"] = 101
        variants.append(state)
        for state in variants:
            with self.assertRaises(RuntimeError):
                job.cleanup(state, scope, lambda _: None)
        self.assertNotIn("terminate-job", native.calls)

    def test_changed_limits_refuses(self):
        scope, native = self.scope()
        native.limits |= 0x800  # BREAKAWAY_OK
        with self.assertRaises(RuntimeError):
            scope.admit(scope.name, PARENT, {})
        with self.assertRaises(RuntimeError):
            job.cleanup(self.state(scope), scope, lambda _: None)
        self.assertNotIn("terminate-job", native.calls)

    def test_last_handle_close_is_backstop_not_closure_receipt(self):
        native = JobNative()
        scope = job.Scope(uuid.uuid4().hex, native=native, parent=PARENT)
        with scope:
            state = self.state(scope)
        self.assertEqual(native.calls, ["create-job", "close-job"])
        self.assertNotIn("cleanup_complete", state)
        with self.assertRaises(RuntimeError):
            job.live(scope.name, state)
        with self.assertRaises(RuntimeError):
            scope.__enter__()

    def launcher(self, *, fail_assign=False, fail_birth_save=False):
        """Execute actual launcher function, fake only Win32 transport."""
        here = Path(__file__).resolve().parent
        scratch = here / ".tmp-agora" / ("job-test-" + uuid.uuid4().hex)
        os.makedirs(scratch)
        self.addCleanup(shutil.rmtree, scratch)
        path = scratch / "fake.json"
        node = next(n for n in ast.parse((here / "sandbox_window.py").read_text(encoding="utf-8")).body
                    if isinstance(n, ast.FunctionDef) and n.name == "_start_locked")
        scope, native = self.scope()
        native.fail_assign = fail_assign
        direct = Native()
        calls = native.calls
        class Resume:
            def __call__(inner, handle):
                data = json.loads(path.read_text())
                self.assertTrue(data["launches"][0]["job_assigned"])
                self.assertTrue(birth.bound(data, data["owners"][0]))
                self.assertEqual(data["launches"][0]["status"], "resume-pending")
                calls.append("resume")
                return 1
        def create(executable, line, sa, ta, inherit, flags, env, cwd, si, pi):
            self.assertFalse(inherit)
            self.assertTrue(flags & 4)
            self.assertFalse(flags & 0x01000000)  # no CREATE_BREAKAWAY_FROM_JOB
            data = json.loads(path.read_text())
            self.assertEqual(data["job"], scope.descriptor)
            self.assertEqual(data["launches"][0]["status"], "pending")
            pi.dwProcessId, pi.hProcess, pi.hThread = 10, 700, 701
            calls.append("create-suspended")
            return True
        k = NS(CreateProcessW=create, ResumeThread=Resume(), CloseHandle=lambda _: None)
        ns = {"state_file": lambda _: path, "os": os, "json": json,
              "time": NS(time=lambda: 1), "desktop": lambda *a, **k: (99, "agora-sandbox-fixture"),
              "STARTUPINFOW": NS, "PROCESS_INFORMATION": NS, "subprocess": subprocess,
              "sys": NS(exit=lambda _: self.fail("exit")), "k32": k,
              "wt": NS(HANDLE=int, DWORD=int),
              "ctypes": NS(sizeof=lambda _: 1, create_unicode_buffer=lambda s: s, byref=lambda v: v)}
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(here / "sandbox_window.py"), "exec"), ns)
        import sandbox_receipts
        original = sandbox_receipts.write
        def write(path, data):
            if fail_birth_save and data.get("owners"):
                raise OSError("denied")
            original(path, data)
        with patch.object(sandbox_owned, "OwnedProcesses", return_value=NS(native=direct)), \
                patch.object(sandbox_receipts, "write", side_effect=write):
            if fail_assign or fail_birth_save:
                with self.assertRaises(OSError):
                    ns["_start_locked"](scope.name, [r"C:\fixture\engine.exe"], job=scope)
                self.assertNotIn("resume", calls)
                self.assertNotIn("terminate-job", calls)
            else:
                self.assertEqual(ns["_start_locked"](scope.name, [r"C:\fixture\engine.exe"], job=scope), 10)
                self.assertEqual(calls, ["create-job", "create-suspended", "assign", "resume"])

    def test_actual_launcher_assigns_before_durable_resume(self):
        self.launcher()

    def test_assignment_failure_no_resume_or_outside_job_termination(self):
        self.launcher(fail_assign=True)

    def test_birth_save_failure_no_resume(self):
        self.launcher(fail_birth_save=True)

    def test_actual_close_uses_live_job_or_refuses_without_legacy_fallback(self):
        here = Path(__file__).resolve().parent
        scratch = here / ".tmp-agora" / ("job-close-test-" + uuid.uuid4().hex)
        os.makedirs(scratch)
        self.addCleanup(shutil.rmtree, scratch)
        path = scratch / "fake.json"
        node = next(n for n in ast.parse((here / "sandbox_window.py").read_text(encoding="utf-8")).body
                    if isinstance(n, ast.FunctionDef) and n.name == "close")
        ns = {"state_file": lambda _: path, "json": json, "time": NS(time_ns=lambda: 123),
              "top_windows_quiet": lambda _: self.fail("window enumeration is not job ownership")}
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(here / "sandbox_window.py"), "exec"), ns)
        scope, native = self.scope()
        path.write_text(json.dumps(self.state(scope)), encoding="utf-8")
        with patch.object(sandbox_owned, "OwnedProcesses", side_effect=AssertionError("legacy cleanup")):
            with patch.object(scope, "pid", -1):
                self.assertFalse(ns["close"](scope.name, quiet=True)["ok"])
            self.assertTrue(path.exists())
            self.assertNotIn("terminate-job", native.calls)
            result = ns["close"](scope.name, quiet=True)
        self.assertTrue(result["ok"])
        self.assertFalse(path.exists())
        receipt = json.loads(Path(result["receipt"]).read_text())
        self.assertEqual(receipt["cleanup"][-1]["after"]["pids"], [])
        self.assertEqual(receipt["job_closure"], "proven empty")


class KernelTests(unittest.TestCase):
    """Real ctypes layouts/API wrapper with mocked kernel, no OS effects."""
    def native(self, *, incomplete=False, membership=True):
        calls = []
        def create(sa, name):
            self.assertIsNone(sa)
            self.assertIsNone(name)
            calls.append("create")
            return 888
        def set_limits(handle, kind, data, size):
            self.assertEqual(kind, 9)
            self.assertEqual(size, job.c.sizeof(job.ExtendedLimits))
            self.assertEqual(data._obj.basic.flags, job.KILL_ON_CLOSE)
            calls.append("kill-on-close")
            return True
        def query(handle, kind, data, size, returned):
            self.assertEqual(handle, 888)
            if kind == 9:
                data._obj.basic.flags = job.KILL_ON_CLOSE
            elif kind == 3:
                data._obj.assigned = 3 if incomplete else 2
                data._obj.listed = 2
                data._obj.ids[0], data._obj.ids[1] = 10, 11
            elif kind == 1:
                data._obj.active, data._obj.total = 2, 2
            else:
                self.fail("unreviewed information class")
            return True
        def contains(process, handle, result):
            result._obj.value = membership
            return True
        class Fn:
            def __init__(self, fn):
                self.fn = fn
            def __call__(self, *args):
                return self.fn(*args)
        kernel = NS(**{name: Fn(fn) for name, fn in {
            "CreateJobObjectW": create, "SetInformationJobObject": set_limits,
            "QueryInformationJobObject": query, "IsProcessInJob": contains,
            "AssignProcessToJobObject": lambda *args: calls.append("assign") or True,
            "TerminateJobObject": lambda *args: calls.append("terminate") or True,
            "CloseHandle": lambda *args: calls.append("close") or True}.items()})
        with patch.object(job.c, "WinDLL", return_value=kernel):
            native = job.WindowsJob()
        return native, calls

    def test_native_unnamed_no_breakaway_and_pid_accounting(self):
        native, calls = self.native()
        handle = native.create()
        native.assign(handle, 700)
        self.assertEqual(native.snapshot(handle)["pids"], [10, 11])
        native.terminate(handle)
        native.close(handle)
        self.assertEqual(calls, ["create", "kill-on-close", "assign", "terminate", "close"])

    def test_native_incomplete_pid_list_is_unknown(self):
        native, _ = self.native(incomplete=True)
        with self.assertRaises(RuntimeError):
            native.snapshot(888)

    def test_native_unconfirmed_assignment_refuses(self):
        native, _ = self.native(membership=False)
        with self.assertRaises(RuntimeError):
            native.assign(888, 700)


if __name__ == "__main__":
    unittest.main()
