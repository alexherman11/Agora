"""Offline tests: real orchestration + real shared Job/birth receipt logic.

All process/Job calls are fakes. No native containment or cleanup certification.
"""
import copy
import json
import os
import sys
import threading
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sandbox_job
from admission_job import (
    EngineFence,
    GuardRefused,
    engine_report,
    guard_details,
    read,
    require_guard,
    run,
    write,
)
from sandbox_birth import capture, intent, persist_then_resume


class GuardDiagnostics(unittest.TestCase):
    def test_empty_reviewed_inventory_refuses_before_native_import(self):
        import io

        import run_admission
        output = io.StringIO()
        with patch.dict(sys.modules, {"guard_context": NS(read=lambda: {"admitted": True}),
                                      "sandbox_window": None}), \
                patch.object(sys, "argv", ["run_admission.py"]), \
                patch.object(run_admission, "REVIEWED_HOST_IMAGES", {}), \
                patch("sys.stdout", output):
            self.assertEqual(run_admission.main(), 2)
        self.assertIn("no native initialization", output.getvalue())

    def test_missing_stale_unknown_unsafe_reasons_retained_without_admission(self):
        for reason in ("house observation missing/unreadable",
                       "house observation stale/unknown/unsafe"):
            for observed, game, exe in ((0, False, "editor.exe"),
                                        (100, None, "unknown"),
                                        (100, True, "game.exe")):
                source = {"admitted": False, "reason": reason, "observation": {
                    "observed_at": observed, "game": game, "foreground_exe": exe}}
                with self.subTest(reason=reason, game=game), \
                        self.assertRaises(GuardRefused) as caught:
                    require_guard(lambda source=source: source)
                details = caught.exception.guard
                self.assertEqual(details["reason"], reason)
                self.assertEqual(details["game"], game)
                self.assertEqual(details["foreground_exe"], exe)

    def test_projection_is_bounded_metadata_not_host_or_private_content(self):
        result = guard_details({"admitted": False, "reason": "x" * 300,
                                "observation": {
                                    "observed_at": 90, "game": "false",
                                    "foreground_exe": r"C:\private\thing.exe",
                                    "title": "never retain", "command": "never retain"}},
                               now=100)
        self.assertEqual(result["observation_age_seconds"], 10)
        self.assertEqual(result["foreground_exe"], "unknown")
        self.assertIsNone(result["game"])
        self.assertEqual(len(result["reason"]), 200)
        self.assertNotIn("never retain", json.dumps(result))
        self.assertIsNone(guard_details({"observation": {"observed_at": float("nan")}},
                                        now=100)["observation_age_seconds"])
        self.assertFalse(guard_details({"admitted": 1})["admitted"])

    def test_status_cli_reads_once_without_importing_launcher(self):
        import io

        import run_admission
        calls = []
        def reader():
            calls.append("read")
            return {"admitted": False, "reason": "house observation missing/unreadable"}
        output = io.StringIO()
        with patch.dict(sys.modules, {"guard_context": NS(read=reader),
                                      "sandbox_window": None}), \
                patch.object(sys, "argv", ["run_admission.py", "--guard-status"]), \
                patch("sys.stdout", output):
            self.assertEqual(run_admission.main(), 0)
        self.assertEqual(calls, ["read"])
        self.assertFalse(json.loads(output.getvalue())["admitted"])

    def test_initial_refusal_keeps_details_before_importing_launcher(self):
        import run_admission
        source = {"admitted": False, "reason": "house observation stale/unknown/unsafe",
                  "observation": {"game": None, "foreground_exe": "pythonw.exe"}}
        with patch.dict(sys.modules, {"guard_context": NS(read=lambda: source),
                                      "sandbox_window": None}), \
                patch.object(sys, "argv", ["run_admission.py"]), \
                self.assertRaises(GuardRefused) as caught:
            run_admission.main()
        self.assertEqual(caught.exception.guard["foreground_exe"], "pythonw.exe")
        self.assertIsNone(caught.exception.guard["game"])


class Verifier:
    """Injected observer, never evidence of native containment."""
    def __init__(self, events):
        self.events = events
        self.allow = True

    def before(self):
        self.events.append("verify_before")

    def add_birth(self, birth):
        assert set(birth) == {"pid", "created", "exe"}
        self.events.append("verify_birth")

    def start_sampling(self, interval):
        self.events.append("verify_start")

    def gate(self):
        self.events.append("verify_gate")
        return {"allow_interaction": self.allow}

    def stop_sampling(self):
        self.events.append("verify_stop")

    def after(self):
        self.events.append("verify_after")

    def verdict(self):
        return {"allow_interaction": self.allow}


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
        if handle == 10:
            return (100, r"c:\fixture\python.exe")
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
        write(self.folder / "receipt.json",
              {"request": "token", "pid": 10, "phase": "importing",
               "desktop": "agora-sandbox-" + name, "profile": str(self.folder / "profile"),
               "binding": None})
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
        self.verifier = Verifier(self.api.events)
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
        return {"admitted": self.block_at is None or self.guards < self.block_at,
                "reason": "house observation stale/unknown/unsafe",
                "observation": {"foreground_exe": "unknown", "game": None}}

    def pause(self, seconds):
        self.now += seconds
        self.bound_receipt("host_bound")
        if (self.folder / "engine-admission.json").exists():
            self.bound_receipt("child_exit")

    def bound_receipt(self, phase):
        path = self.folder / "host-binding.json"
        if not path.exists():
            return
        binding = read(path)
        envelope = {"request": "token", "desktop": binding["desktop"],
                    "profile": str(self.folder / "profile"), "binding": binding}
        pid = binding["host"]["pid"]
        write(self.folder / "receipt.json", {**envelope, "phase": phase, "pid": pid})
        request = self.folder / "engine-request.json"
        if not request.exists():
            write(request, {**envelope, "host_pid": pid, "engine_pid": 20,
                            "engine_report": {"browser_pid": 20}})

    def execute(self, **kwargs):
        kwargs.setdefault("verifier_factory", lambda scope: self.verifier)
        kwargs.setdefault("host_images", {r"c:\fixture\python.exe": "fake-hash"})
        kwargs.setdefault("digest", lambda _: "fake-hash")
        kwargs.setdefault("processes", lambda: [(10, os.getpid(), "python.exe"),
                                               (20, 10, "msedgewebview2.exe")])
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
        self.assertEqual(self.native.closed, [20, 10])
        for first, second in (
                ("verify_before", "start_suspended"), ("resume", "verify_birth"),
                ("verify_birth", "verify_start"), ("verify_gate", "verify_stop"),
                ("verify_stop", "cleanup"), ("cleanup", "verify_after"),
                ("verify_after", "close_job")):
            self.assertLess(events.index(first), events.index(second))

    def test_missing_verifier_prevents_any_native_scope(self):
        result = self.execute(verifier_factory=None)
        self.assertEqual(result["phase"], "refused")
        self.assertEqual(self.api.events, [])

    def test_missing_host_configuration_prevents_job_or_start(self):
        result = self.execute(host_images={})
        self.assertEqual(result["phase"], "refused")
        self.assertEqual(self.api.events, [])

    def test_measured_descendant_actual_orchestration(self):
        original_start = self.api.start
        def start(name, argv, **kwargs):
            root = original_start(name, argv, **kwargs)
            self.api.job.pids.append(11)
            value = read(self.folder / "receipt.json")
            write(self.folder / "receipt.json", {**value, "pid": 11})
            return root
        self.api.start = start
        self.native.ident = (120, r"c:\fixture\msedgewebview2.exe")
        original_identity = self.native.of_handle
        self.native.of_handle = lambda h: ((110, r"c:\fixture\python.exe")
                                           if h == 11 else original_identity(h))
        result = self.execute(processes=lambda: [(10, os.getpid(), "python.exe"),
                                                (11, 10, "python.exe"),
                                                (20, 11, "msedgewebview2.exe")])
        self.assertEqual(result["phase"], "child_exit")
        self.assertEqual(result["host_binding"]["host"]["pid"], 11)
        self.assertEqual(result["host_binding"]["root"]["pid"], 10)
        self.assertEqual(result["job_closure"], "proven empty")
        self.assertEqual(sorted(self.native.closed), [10, 11, 20])

    def test_actual_host_bound_engine_report_callback(self):
        original = self.verifier.gate
        def gate():
            self.assertEqual(self.verifier.engine_report()["browser_pid"], 20)
            return original()
        self.verifier.gate = gate
        self.assertEqual(self.execute()["phase"], "child_exit")

    def test_forged_receipt_cannot_supply_report_provenance(self):
        original = self.verifier.gate
        def gate():
            value = read(self.folder / "receipt.json")
            write(self.folder / "receipt.json", {**value, "pid": 999})
            self.verifier.engine_report()
            return original()
        self.verifier.gate = gate
        result = self.execute()
        self.assertEqual(result["phase"], "refused")
        self.assertFalse(result["engine_admitted"])
        self.assertEqual(result["job_closure"], "proven empty")

    def test_engine_envelope_wrong_profile_refuses(self):
        original = self.pause
        def changed(seconds):
            original(seconds)
            path = self.folder / "engine-request.json"
            if path.exists():
                value = read(path)
                write(path, {**value, "profile": r"C:\wrong"})
        self.pause = changed
        result = self.execute()
        self.assertEqual(result["phase"], "refused")
        self.assertFalse(result["engine_admitted"])

    def test_engine_report_read_race_refuses(self):
        original = self.verifier.gate
        def gate():
            original_read = read
            calls = []
            def raced(path):
                value = original_read(path)
                if Path(path).name == "engine-request.json":
                    calls.append(1)
                    if len(calls) == 2:
                        return {**value, "request": "changed"}
                return value
            with patch("admission_job.read", side_effect=raced):
                self.verifier.engine_report()
            return original()
        self.verifier.gate = gate
        result = self.execute()
        self.assertEqual(result["phase"], "refused")
        self.assertFalse(result["engine_admitted"])

    def test_unknown_verifier_gate_blocks_content_but_cleans_job(self):
        self.verifier.allow = False
        result = self.execute()
        self.assertFalse(result["engine_admitted"])
        self.assertFalse((self.folder / "engine-admission.json").exists())
        self.assertEqual(result["job_closure"], "proven empty")
        self.assertFalse(result["native_verification"]["allow_interaction"])

    def test_verifier_before_failure_never_launches(self):
        self.verifier.before = lambda: (_ for _ in ()).throw(OSError("snapshot"))
        self.assertEqual(self.execute()["phase"], "refused")
        self.assertNotIn("start_suspended", self.api.events)

    def test_verifier_after_failure_cannot_claim_success(self):
        self.verifier.after = lambda: (_ for _ in ()).throw(OSError("snapshot"))
        result = self.execute()
        self.assertEqual(result["job_closure"], "proven empty")
        self.assertEqual(result["native_verification"]["status"], "unknown")

    def test_report_envelope_binding(self):
        self.assertIsNone(engine_report(self.folder, "token"))
        report = {"browser_pid": 20, "user_data_folder": "fixture", "processes": []}
        write(self.folder / "receipt.json", {"pid": 10})
        request = {"request": "token", "host_pid": 10, "engine_pid": 20,
                   "engine_report": report}
        write(self.folder / "engine-request.json", request)
        host = NS(envelope=lambda *a, **k: None, check=lambda: None,
                  lock=threading.RLock())
        engine = NS(check=lambda *a, **k: None)
        with self.assertRaisesRegex(RuntimeError, "measured host"):
            engine_report(self.folder, "token")
        self.assertEqual(engine_report(self.folder, "token", host, engine), report)
        for field, value in (("request", "forged"), ("host_pid", 99),
                             ("engine_pid", 99), ("engine_report", None)):
            write(self.folder / "engine-request.json", {**request, field: value})
            with self.assertRaises(RuntimeError):
                engine_report(self.folder, "token", host, engine)

    def test_real_shared_verdict_cannot_prove_required_snapshot_limits(self):
        import native_run_verify as shared
        verifier = shared.Verifier(
            {"name": "offline", "must_prove": ["family.brokered", "writes.unscanned"]},
            object(), native=object())
        # Supply ideal observations, not native evidence. Exercise the delivered
        # verdict implementation, including its immutable observational limits.
        verifier._family = lambda final: shared.check(
            shared.OBSERVED, "fixture", {}, [], shared.NOT_PROVEN["family"])
        verifier._windows = lambda: shared.check(
            shared.OBSERVED, "fixture", {}, [], shared.NOT_PROVEN["windows"])
        verifier._network = lambda: shared.check(
            shared.OBSERVED, "fixture", {}, [], shared.NOT_PROVEN["network"])
        verifier._writes = lambda: shared.check(
            shared.OBSERVED, "fixture", {}, [], shared.NOT_PROVEN["writes"])
        gate = verifier.verdict(final=False)
        self.assertFalse(gate["allow_interaction"])
        self.assertIn("family.brokered", gate["blocking_limits"])
        final = verifier.verdict()
        self.assertFalse(final["allow_interaction"])
        self.assertIn("writes.unscanned", final["blocking_limits"])

    def test_preflight_guard_refuses_without_job_or_start(self):
        self.block_at = 1
        result = self.execute()
        self.assertEqual(result["phase"], "refused")
        self.assertEqual(result["guard_admission"]["reason"],
                         "house observation stale/unknown/unsafe")
        self.assertEqual(read(self.folder / "launch.json")["guard_admission"],
                         result["guard_admission"])
        self.assertEqual(self.api.events, [])

    def test_guard_rechecked_before_birth(self):
        self.block_at = 2
        result = self.execute()
        self.assertEqual(result["phase"], "refused")
        self.assertEqual(read(self.folder / "launch.json")["guard_admission"]["reason"],
                         "house observation stale/unknown/unsafe")
        self.assertNotIn("start_suspended", self.api.events)

    def test_guard_lost_during_run_cleans_only_retained_job(self):
        self.block_at = 3
        result = self.execute()
        self.assertEqual(result["phase"], "refused")
        self.assertFalse(result["guard_admission"]["admitted"])
        self.assertEqual(read(self.folder / "launch.json")["guard_admission"],
                         result["guard_admission"])
        self.assertEqual(self.api.job.pids, [])

    def test_out_of_job_engine_refuses(self):
        self.api.job.member = False
        self.api.job.pids = [10]
        result = self.execute()
        self.assertFalse(result["engine_admitted"])
        self.assertFalse((self.folder / "engine-admission.json").exists())
        self.assertEqual(result["job_closure"], "proven empty")
        # The external engine handle was inspected/closed, never terminated.
        self.assertIn(10, self.native.closed)

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
            self.bound_receipt("host_bound")
            if (self.folder / "engine-admission.json").exists():
                ticks.append(1)
                self.api.job.pids = [10]  # engine exited, host still flushing
                self.bound_receipt("form_closed" if len(ticks) == 1 else "child_exit")
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
        with self.assertRaisesRegex(RuntimeError, "closed"):
            fence.check(good)

    def test_birth_race_on_same_handle(self):
        identities = iter([(101, r"c:\fixture\msedgewebview2.exe"),
                           (102, r"c:\fixture\msedgewebview2.exe")])
        self.native.of_handle = lambda h: ((100, r"c:\fixture\python.exe")
                                           if h == 10 else next(identities))
        self.assertFalse(self.execute()["engine_admitted"])


if __name__ == "__main__":
    unittest.main()
