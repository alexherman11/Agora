"""Offline tests: real orchestration + real shared Job/birth receipt logic.

All process/Job calls are fakes. No native containment or cleanup certification.
"""
import copy
import os
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sandbox_job
from sandbox_birth import capture, intent, persist_then_resume
from admission_job import EngineFence, read, run, write


class Kernel:
    def __init__(self):
        self.ident = (101, r"c:\fixture\msedgewebview2.exe")
        self.closed = []
        self.denied = False
        self.k = self

    def OpenProcess(self, access, inherit, pid):
        return None if self.denied else pid

    def CloseHandle(self, handle):
        self.closed.append(handle)

    def of_handle(self, handle):
        return self.ident


class Job:
    def __init__(self, events):
        self.events, self.pids = events, [10, 20]
        self.member, self.fail_snapshot = True, False

    def create(self):
        self.events.append("job_create")
        return 900

    def verify(self, handle):
        if handle != 900:
            raise RuntimeError("wrong job")

    def contains(self, handle, process):
        return self.member and process in self.pids

    def snapshot(self, handle):
        self.verify(handle)
        if self.fail_snapshot:
            raise RuntimeError("snapshot unavailable")
        return {"pids": list(self.pids), "active": len(self.pids),
                "total": 2, "terminated": 2 - len(self.pids)}

    def terminate(self, handle):
        self.events.append("terminate_job")
        self.pids.clear()

    def close(self, handle):
        self.events.append("close_job")


class Guard:
    def __init__(self, events):
        self.events = events

    def __enter__(self):
        self.events.append("guard_enter")
        return self

    def __exit__(self, *exc):
        self.events.append("guard_exit")

    def verdict(self):
        return 0, "fake Guard only"


class API:
    def __init__(self, folder):
        self.folder, self.events = folder, []
        self.job = Job(self.events)
        self.parent = {"pid": os.getpid(), "created": 1, "exe": r"c:\fixture\parent.exe"}
        self.state = {}
        self.closed = None

    def Guard(self, *_):
        return Guard(self.events)

    def job_scope(self, name):
        self.scope = sandbox_job.Scope(name, native=self.job, parent=self.parent)
        return self.scope

    def start(self, name, argv, *, job):
        job.admit(name, self.parent, self.state)
        self.events.append("start_suspended")
        facts = intent(argv, self.parent, "WinSta0\\agora-sandbox-" + name)
        birth = capture(facts, 10, (100, r"c:\fixture\python.exe"))
        birth["job_id"] = job.descriptor["id"]
        record = {"intent": facts, "job_id": job.descriptor["id"], "job_assigned": True}
        self.state = {"job": copy.deepcopy(job.descriptor), "pids": [10],
                      "launches": [record], "owners": []}
        self.events.append("assign_before_resume")
        persist_then_resume(self.state, record, birth,
                            lambda _: self.events.append("persist_birth"),
                            lambda: (self.events.append("resume") or 1))
        write(self.folder / "engine-request.json",
              {"request": "token", "host_pid": 10, "engine_pid": 20})
        return 10

    def load(self, name):
        return copy.deepcopy(self.state)

    def close(self, name, quiet):
        self.events.append("cleanup")
        result = sandbox_job.cleanup(
            self.state, self.scope,
            lambda data: write(self.folder / "owned.json", data))
        if result["ok"]:
            result["receipt"] = str(self.folder / "owned.json")
        self.closed = copy.deepcopy(result)
        return result


class Tests(unittest.TestCase):
    def setUp(self):
        # Inherited ACL, inside this worktree. No tempfile owner-only ACL.
        root = Path(__file__).resolve().parents[1] / ".tmp-agora"
        self.folder = root / ("offline-job-" + uuid.uuid4().hex)
        os.makedirs(self.folder)
        self.api = API(self.folder)
        self.native = Kernel()
        self.now = 0
        self.guards = 0
        self.block_at = None
        # Tripwires only, not an OS security boundary.
        self.patches = [patch("subprocess.run", side_effect=AssertionError("host process")),
                        patch("subprocess.Popen", side_effect=AssertionError("host process")),
                        patch("ctypes.WinDLL", side_effect=AssertionError("native query"))]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def guard(self):
        self.guards += 1
        return {"admitted": self.block_at is None or self.guards < self.block_at}

    def pause(self, seconds):
        self.now += seconds
        if (self.folder / "engine-admission.json").exists():
            write(self.folder / "receipt.json", {"phase": "child_exit", "pid": 10})

    def execute(self, **kwargs):
        return run(self.api, self.guard, self.native, "fake-" + uuid.uuid4().hex,
                   self.folder, [r"C:\fixture\python.exe"], "token",
                   clock=lambda: self.now, pause=self.pause, timeout=.1, **kwargs)

    def test_success_actual_shared_birth_cleanup_order(self):
        result = self.execute()
        self.assertEqual(result["phase"], "child_exit")
        self.assertTrue(result["engine_admitted"])
        self.assertEqual(result["job_closure"], "proven empty")
        self.assertEqual(self.api.job.pids, [])
        events = self.api.events
        self.assertLess(events.index("assign_before_resume"), events.index("resume"))
        self.assertLess(events.index("persist_birth"), events.index("resume"))
        self.assertLess(events.index("cleanup"), events.index("close_job"))
        self.assertLess(events.index("terminate_job"), events.index("close_job"))
        self.assertIn("UNKNOWN", result["legacy_runtime_closure"])
        self.assertEqual(self.native.closed, [20])

    def test_preflight_guard_refuses_without_job_or_start(self):
        self.block_at = 1
        self.assertEqual(self.execute()["phase"], "refused")
        self.assertEqual(self.api.events, [])

    def test_guard_rechecked_before_birth(self):
        self.block_at = 2
        self.assertEqual(self.execute()["phase"], "refused")
        self.assertNotIn("start_suspended", self.api.events)

    def test_guard_lost_during_run_cleans_only_retained_job(self):
        self.block_at = 3
        self.assertEqual(self.execute()["phase"], "refused")
        self.assertEqual(self.api.job.pids, [])

    def test_out_of_job_engine_refuses(self):
        self.api.job.member = False
        self.api.job.pids = [10]
        result = self.execute()
        self.assertFalse(result["engine_admitted"])
        self.assertFalse((self.folder / "engine-admission.json").exists())
        self.assertEqual(result["job_closure"], "proven empty")
        # The external engine handle was inspected/closed, never terminated.
        self.assertEqual(self.native.closed, [20])

    def test_unknown_engine_refuses(self):
        self.native.denied = True
        self.assertFalse(self.execute()["engine_admitted"])

    def test_reused_preexisting_engine_refuses(self):
        self.native.ident = (99, r"c:\fixture\msedgewebview2.exe")
        self.assertFalse(self.execute()["engine_admitted"])

    def test_unknown_birth_refuses(self):
        self.native.ident = None
        self.assertFalse(self.execute()["engine_admitted"])

    def test_wrong_executable_refuses(self):
        self.native.ident = (101, r"c:\fixture\other.exe")
        self.assertFalse(self.execute()["engine_admitted"])

    def test_snapshot_denial_leaves_unknown_receipt(self):
        self.api.job.fail_snapshot = True
        result = self.execute()
        self.assertEqual(result["job_closure"], "unknown")
        self.assertFalse(result["cleanup"]["ok"])
        self.assertNotIn("terminate_job", self.api.events)

    def test_explicit_parent_deadline(self):
        self.pause = lambda seconds: setattr(self, "now", self.now + seconds)
        result = self.execute()
        self.assertEqual(result["phase"], "deadline_fired")
        self.assertEqual(result["deadline_seconds"], .1)
        self.assertEqual(result["job_closure"], "proven empty")

    def test_normal_engine_exit_can_precede_child_receipt_flush(self):
        ticks = []
        def finishing(seconds):
            self.now += seconds
            if (self.folder / "engine-admission.json").exists():
                ticks.append(1)
                self.api.job.pids = [10]  # engine exited, host still flushing
                write(self.folder / "receipt.json",
                      {"phase": "form_closed" if len(ticks) == 1 else "child_exit", "pid": 10})
        self.pause = finishing
        self.assertEqual(self.execute()["phase"], "child_exit")

    def test_unknown_job_effect_is_not_replayed(self):
        original = self.api.close
        def unknown(name, quiet):
            self.api.state["cleanup"] = [{"kind": "job", "status": "unknown"}]
            return original(name, quiet)
        self.api.close = unknown
        result = self.execute()
        self.assertEqual(result["job_closure"], "unknown")
        self.assertFalse(result["cleanup"]["ok"])
        self.assertNotIn("terminate_job", self.api.events)

    def test_cleanup_persist_failure_prevents_job_effect(self):
        def failed(name, quiet):
            def fail_write(_):
                raise OSError("disk")
            return sandbox_job.cleanup(self.api.state, self.api.scope, fail_write)
        self.api.close = failed
        result = self.execute()
        self.assertEqual(result["job_closure"], "unknown")
        self.assertNotIn("terminate_job", self.api.events)

    def test_wrong_child_receipt_refuses(self):
        self.pause = lambda seconds: write(self.folder / "receipt.json",
                                           {"phase": "child_exit", "pid": 999})
        self.assertEqual(self.execute()["phase"], "refused")

    def test_start_failure_still_uses_shared_cleanup(self):
        original = self.api.start
        def partial(*args, **kwargs):
            original(*args, **kwargs)
            raise RuntimeError("lost start reply")
        self.api.start = partial
        result = self.execute()
        self.assertEqual(result["phase"], "refused")
        self.assertEqual(result["job_closure"], "proven empty")

    def test_cleanup_exception_not_closed(self):
        def failure(*args, **kwargs):
            raise OSError("receipt failed")
        self.api.close = failure
        result = self.execute()
        self.assertEqual(result["job_closure"], "unknown")
        self.assertEqual(result["cleanup"]["error_type"], "OSError")

    def test_no_cleanup_from_unbound_birth(self):
        original = self.api.load
        def broken(name):
            self.api.state["launches"][0]["owner"]["created"] = 999
            return original(name)
        self.api.load = broken
        result = self.execute()
        self.assertEqual(result["job_closure"], "unknown")
        self.assertNotIn("terminate_job", self.api.events)

    def test_persistence_failure_prevents_launch(self):
        with patch("admission_job.write", side_effect=OSError("disk")):
            with self.assertRaises(OSError):
                self.execute()
        self.assertEqual(self.api.events, [])

    def test_retained_folder_not_overwritten_or_adopted(self):
        write(self.folder / "launch.json", {"legacy": "UNKNOWN"})
        with self.assertRaisesRegex(RuntimeError, "fresh receipt"):
            self.execute()
        self.assertEqual(read(self.folder / "launch.json"), {"legacy": "UNKNOWN"})
        self.assertEqual(self.api.events, [])

    def test_engine_request_change_during_fixture_refused(self):
        def changed(seconds):
            self.now += seconds
            write(self.folder / "engine-request.json",
                  {"request": "other", "host_pid": 10, "engine_pid": 20})
        self.pause = changed
        self.assertEqual(self.execute()["phase"], "refused")

    def test_snapshot_without_engine_is_not_admission(self):
        self.api.job.pids = [10]
        self.assertFalse(self.execute()["engine_admitted"])

    def test_wrong_or_changed_engine_request(self):
        scope = NS(handle=900, native=self.api.job,
                   descriptor={"id": "own"}, snapshot=lambda: self.api.job.snapshot(900))
        fence = EngineFence(scope, self.native, {"pid": 10, "created": 100}, "token")
        good = {"request": "token", "host_pid": 10, "engine_pid": 20}
        for field, value in (("request", "forged"), ("host_pid", 999), ("engine_pid", True)):
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                fence.check({**good, field: value})
        fence.check(good)
        with self.assertRaises(RuntimeError):
            fence.check({**good, "engine_pid": 30})
        fence.close()

    def test_birth_race_on_same_handle(self):
        identities = iter([(101, r"c:\fixture\msedgewebview2.exe"),
                           (102, r"c:\fixture\msedgewebview2.exe")])
        self.native.of_handle = lambda _: next(identities)
        self.assertFalse(self.execute()["engine_admitted"])


if __name__ == "__main__":
    unittest.main()
