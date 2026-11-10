"""No HUD, desktop input, real inventory, or live process termination.

Run normally for tests; --demo prints the fake-copy lifecycle evidence too.
Only the mutex tests call Windows (one private name, also tried by a hidden
Python child). Every process inventory and termination in these tests is fake.
"""
from dataclasses import replace
import argparse
import ast
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from unittest.mock import Mock
import uuid

import hud_lifecycle as life

HERE = Path(__file__).resolve().parent
HUD = r"C:\Projects\Agora4\src\desktop\hud.py"
KEEPER = r"C:\Projects\Agora4\src\text-desk\notation\keeper.py"
EXE = r"C:\Python\pythonw.exe"
SCOPE = life.Scope(HUD, KEEPER)
KEEP = life.Process(10, 1, 100, EXE, (EXE, KEEPER, "frontier", "--port", "8794"))


def host(pid=20, created=200, healthy=True, **changes):
    return replace(life.Process(pid, 1, created, EXE, (EXE, HUD), healthy), **changes)


class Copy:
    def __init__(self):
        self.path = HERE / "state" / ("lifecycle-test-" + uuid.uuid4().hex)
        self.path.mkdir(parents=True)
        self.pid = self.path / "hud.pid"
        self.processes = [KEEP]
        self.monitor = life.Monitor(SCOPE)
        self.starts, self.ends, self.logs = [], [], []

    def close(self):
        self.pid.unlink(missing_ok=True)
        self.path.rmdir()

    def end(self, proc):
        if not self.healthy_identity(proc):
            return "refused: process identity changed"
        self.ends.append((proc.pid, proc.created))
        self.processes = [p for p in self.processes if p.pid != proc.pid]
        return "ended"

    def healthy_identity(self, proc):
        return any((p.pid, p.created, p.exe) == (proc.pid, proc.created, proc.exe) for p in self.processes or [])

    def healthy(self, proc):
        return proc.healthy and self.healthy_identity(proc)

    def tick(self, now, door=True, observed=...):
        return self.monitor.tick(self.processes if observed is ... else observed, life.read_pid(self.pid), door, now,
                                 start=self.starts.append, end=self.end, healthy=self.healthy, log=self.logs.append)


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.copy = Copy()

    def tearDown(self):
        self.copy.close()

    def test_clean_start_requires_two_misses_five_seconds_apart(self):
        c = self.copy
        c.tick(0)
        c.tick(4)
        self.assertEqual(c.starts, [])
        c.tick(5)
        self.assertEqual(c.starts, ["hud"])
        c.tick(10)
        self.assertEqual(c.starts, ["hud"], "startup grace must prevent a second launch")

    def test_process_listing_failure_never_starts_or_deletes_pid(self):
        c = self.copy
        c.pid.write_text("20")
        c.tick(0, observed=None)
        c.tick(100, observed=None)
        self.assertEqual((c.starts, c.ends, c.pid.read_text()), ([], [], "20"))
        self.assertIn("unknown", c.logs[-1])

    def test_unknown_breaks_consecutive_misses(self):
        c = self.copy
        c.tick(0)
        c.tick(6, observed=None)
        c.tick(7)
        self.assertEqual(c.starts, [])
        c.tick(12)
        self.assertEqual(c.starts, ["hud"])

    def test_stale_pid_preserved_when_starting_after_two_misses(self):
        c = self.copy
        c.pid.write_text("99999")
        c.tick(0)
        c.tick(5)
        self.assertEqual(c.starts, ["hud"])
        self.assertEqual(c.pid.read_text(), "99999")

    def test_reused_pid_for_unrelated_python_does_not_block_recovery(self):
        c = self.copy
        c.pid.write_text("20")
        c.processes.append(replace(host(), argv=(EXE, "-c", "print('hud.py')")))
        c.tick(0)
        c.tick(5)
        self.assertEqual(c.starts, ["hud"])
        self.assertEqual(c.ends, [])

    def test_live_process_blocks_start_when_pid_missing_or_stale(self):
        c = self.copy
        c.processes.append(host())
        c.tick(0)
        c.pid.write_text("99999")
        c.tick(100)
        self.assertEqual(c.starts, [])
        self.assertEqual(c.pid.read_text(), "99999")

    def test_malformed_pid_is_unknown(self):
        c = self.copy
        c.pid.write_text("incomplete write")
        c.tick(0)
        c.tick(100)
        self.assertEqual(c.starts, [])

    def test_keeper_restart_gap_never_starts_hud(self):
        c = self.copy
        c.tick(0)
        c.processes = []
        c.tick(3, door=False)
        c.tick(6, door=False)
        self.assertEqual(c.starts, [])
        c.processes = [KEEP]
        c.tick(7, door=False)
        c.tick(20)
        self.assertEqual(c.starts, [])
        c.tick(25)
        self.assertEqual(c.starts, ["hud"])

    def test_clean_machine_starts_keeper_before_hud(self):
        c = self.copy
        c.processes = []
        c.tick(0, door=False)
        c.tick(5, door=False)
        self.assertEqual(c.starts, ["keeper"])
        c.processes = [KEEP]
        c.tick(6)
        c.tick(11)
        self.assertEqual(c.starts, ["keeper", "hud"])

    def test_door_answering_without_keeper_is_unknown(self):
        c = self.copy
        c.processes = []
        c.tick(0)
        c.tick(100)
        self.assertEqual(c.starts, [])

    def test_two_live_hosts_keeps_newest_healthy(self):
        c = self.copy
        c.pid.write_text("20")
        c.processes += [host(), host(30, 300)]
        c.tick(0)
        self.assertEqual(c.ends, [(20, 200)])
        self.assertEqual(c.starts, [])
        self.assertEqual(c.pid.read_text(), "20", "supervisor must never unlink hud.pid")
        self.assertIn("keep 30 created=300; end 20 created=200: ended", "\n".join(c.logs))

    def test_newest_unhealthy_does_not_displace_healthy_host(self):
        c = self.copy
        c.processes += [host(), host(30, 300, healthy=False)]
        c.tick(0)
        self.assertEqual(c.ends, [(30, 300)])

    def test_no_healthy_survivor_or_keeper_gap_does_not_kill(self):
        c = self.copy
        c.processes += [host(healthy=False), host(30, 300, healthy=False)]
        c.tick(0)
        self.assertEqual(c.ends, [])
        c.processes = [KEEP, host(), host(30, 300)]
        c.tick(5, door=False)
        self.assertEqual(c.ends, [])

    def test_survivor_dies_during_cleanup_no_further_victims(self):
        c = self.copy
        c.processes += [host(), host(30, 300), host(40, 400)]
        original = c.end
        def end(proc):
            result = original(proc)
            c.processes = [p for p in c.processes if p.pid != 40]
            return result
        c.end = end
        c.tick(0)
        self.assertEqual(c.ends, [(20, 200)])
        self.assertTrue(any(p.pid == 30 for p in c.processes))

    def test_pid_reused_after_inventory_is_not_terminated(self):
        c = self.copy
        observed = [KEEP, host(), host(30, 300)]
        c.processes = [KEEP, host(created=999), host(30, 300)]
        c.tick(0, observed=observed)
        self.assertEqual(c.ends, [])
        self.assertIn("identity changed", "\n".join(c.logs))

    def test_venv_launcher_and_interpreter_are_one_host(self):
        c = self.copy
        c.processes += [host(exe=r"C:\venv\pythonw.exe"), host(21, 201, parent=20)]
        c.tick(0)
        self.assertEqual((c.starts, c.ends), ([], []))


class MatchingTests(unittest.TestCase):
    def test_other_world_port_script_and_command_mentions_are_not_hosts(self):
        cases = [
            (EXE, HUD, "--world", "other"),
            (EXE, HUD, "--door", "http://127.0.0.1:8795"),
            (EXE, r"C:\Other\hud.py"),
            (EXE, "-c", HUD),
            (EXE, "-m", "hud", HUD),
            (EXE, HUD, "--stop"),
        ]
        for argv in cases:
            with self.subTest(argv=argv):
                self.assertEqual(SCOPE.hosts([host(argv=argv)]), [])
        self.assertEqual(len(SCOPE.hosts([host(argv=(EXE, "-u", HUD))])), 1)

    def test_sibling_worktrees_and_loopback_aliases_share_scope(self):
        argv = (EXE, r"C:\Projects\Agora4\.worktrees\a123\src\desktop\hud.py",
                "--door", "http://localhost:8794/")
        self.assertEqual(len(SCOPE.hosts([host(argv=argv)])), 1)
        self.assertEqual(life.mutex_name("frontier", "http://localhost:8794/"),
                         life.mutex_name("frontier", "http://127.0.0.1:8794"))
        self.assertNotEqual(life.mutex_name("frontier-try", SCOPE.door), life.mutex_name("frontier", SCOPE.door))

    def test_only_own_launcher_is_excluded_at_start(self):
        launcher = host(exe=r"C:\venv\pythonw.exe")
        me = host(21, 201, parent=20)
        self.assertEqual(life.other_hosts([launcher, me], SCOPE, 21, 20), [])
        old_interpreter = host()
        self.assertEqual(life.other_hosts([old_interpreter, me], SCOPE, 21, 20), [old_interpreter])

    def test_pid_cleanup_only_removes_owners_record(self):
        c = Copy()
        try:
            c.pid.write_text("30")
            life.remove_own_pid(c.pid, 20)
            self.assertEqual(c.pid.read_text(), "30")
            life.remove_own_pid(c.pid, 30)
            self.assertFalse(c.pid.exists())
        finally:
            c.close()


class InventoryTests(unittest.TestCase):
    def native(self, created=200):
        return SimpleNamespace(identity=lambda pid: (created, life.path_key(EXE)), argv=lambda cmd: (EXE, HUD))

    def run_result(self, stdout, code=0):
        return lambda *a, **kw: SimpleNamespace(returncode=code, stdout=stdout)

    def test_failed_empty_malformed_and_incomplete_responses_are_unknown(self):
        for text, code in [("", 0), ("[]", 1), ("broken", 0), ("null", 0), ("{}", 0), ('[{"pid":20}]', 0)]:
            with self.subTest(text=text, code=code):
                self.assertIsNone(life.inventory(self.native(), self.run_result(text, code)))
        def failed(*args, **kwargs):
            raise subprocess.TimeoutExpired("powershell", 30)
        self.assertIsNone(life.inventory(self.native(), failed))
        self.assertEqual(life.inventory(self.native(), self.run_result("[]")), [])

    def test_verified_native_identity_keeps_full_creation_time(self):
        row = dict(pid=20, parent=1, created=200, exe=EXE, command="fake")
        got = life.inventory(self.native(209), self.run_result(json.dumps([row])))
        self.assertEqual(got[0].created, 209)
        self.assertIsNone(life.inventory(self.native(999), self.run_result(json.dumps([row]))))

    def test_supervisor_requires_live_backend_not_just_http_200(self):
        import agora_start
        def response(value):
            from io import StringIO
            data = StringIO(json.dumps(value))
            data.status = 200
            return data
        with patch.object(agora_start.urllib.request, "urlopen", return_value=response({"up": False})):
            self.assertFalse(agora_start.door_up())
        with patch.object(agora_start.urllib.request, "urlopen", return_value=response({"up": True})):
            self.assertTrue(agora_start.door_up())

    def test_supervisor_copy_preserves_stale_pid_and_only_launches_after_two_checks(self):
        import agora_start
        c = Copy()
        try:
            c.pid.write_text("999")
            native = SimpleNamespace(end=c.end, healthy=c.healthy)
            monitor = life.Monitor(SCOPE)
            with (patch.object(agora_start, "STATE", c.path),
                  patch.object(agora_start, "SCOPE", SCOPE),
                  patch.object(agora_start, "inventory", return_value=[KEEP]),
                  patch.object(agora_start, "door_up", return_value=True),
                  patch.object(agora_start, "log", side_effect=c.logs.append),
                  patch.object(agora_start, "start") as start,
                  patch.object(agora_start.time, "monotonic", side_effect=[0, 5])):
                agora_start.tend(monitor, native)
                start.assert_not_called()
                agora_start.tend(monitor, native)
                self.assertEqual(start.call_count, 1)
            self.assertEqual(c.pid.read_text(), "999")
        finally:
            c.close()


class NativeContractTests(unittest.TestCase):
    def adapter(self, identity, terminate=True):
        calls = []
        k = SimpleNamespace(
            OpenProcess=lambda *args: calls.append(("open", args)) or 123,
            CloseHandle=lambda handle: calls.append(("close", handle)),
            TerminateProcess=lambda handle, code: calls.append(("terminate", handle)) or terminate,
            WaitForSingleObject=lambda handle, timeout: calls.append(("wait", handle)) or 0)
        native = object.__new__(life.Windows)
        native.k = k
        native.of_handle = lambda handle: calls.append(("identity", handle)) or identity
        return native, calls

    def test_identity_and_termination_use_same_handle(self):
        native, calls = self.adapter((200, life.path_key(EXE)))
        self.assertEqual(native.end(host()), "ended")
        self.assertEqual([c for c in calls if c[0] != "open"],
                         [("identity", 123), ("terminate", 123), ("wait", 123), ("close", 123)])

    def test_creation_or_executable_mismatch_never_calls_terminate(self):
        for identity in [(999, life.path_key(EXE)), (200, r"c:\other.exe"), None]:
            native, calls = self.adapter(identity)
            self.assertIn("refused", native.end(host()))
            self.assertFalse(any(c[0] == "terminate" for c in calls))
            self.assertEqual(calls[-1], ("close", 123))

    def test_failed_termination_is_logged_as_failure(self):
        native, calls = self.adapter((200, life.path_key(EXE)), terminate=False)
        self.assertIn("failed", native.end(host()))
        self.assertFalse(any(c[0] == "wait" for c in calls))

    @unittest.skipUnless(os.name == "nt", "Windows mutex")
    def test_real_named_mutex_blocks_a_second_process_and_releases(self):
        native = life.Windows()
        name = "Local\\Agora.HudLifecycle.Test." + uuid.uuid4().hex
        first, second = life.Mutex(native, name), life.Mutex(native, name)
        self.assertTrue(first.acquire())
        try:
            self.assertFalse(second.acquire())
            code = ("from hud_lifecycle import Windows, Mutex; import sys; "
                    "m=Mutex(Windows(),sys.argv[1]); print(m.acquire()); m.close()")
            result = subprocess.run([sys.executable, "-c", code, name], cwd=HERE, capture_output=True,
                                    text=True, timeout=15, creationflags=0x08000000)
            self.assertEqual((result.returncode, result.stdout.strip()), (0, "False"), result.stderr)
        finally:
            second.close()
            first.close()
        self.assertTrue(second.acquire())
        second.close()

    @unittest.skipUnless(os.name == "nt", "Windows argv")
    def test_real_windows_argv_keeps_a_quoted_script_path(self):
        self.assertEqual(life.Windows().argv('"C:\\Program Files\\Python\\pythonw.exe" -u '
                                           '"C:\\My Desk\\hud.py" --world frontier'),
                         (r"C:\Program Files\Python\pythonw.exe", "-u", r"C:\My Desk\hud.py", "--world", "frontier"))


def hud_function(name):
    """Execute the real entry function with fake dependencies, without importing
    HUD's GUI/input modules or creating a native window."""
    tree = ast.parse((HERE / "hud.py").read_text(encoding="utf-8"))
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


class HudEntryTests(unittest.TestCase):
    def setUp(self):
        self.copy = Copy()
        self.guard = SimpleNamespace(acquire=Mock(return_value=True), close=Mock())
        self.native = SimpleNamespace(end=Mock(return_value="ended"))
        self.ns = dict(vars(life), argparse=argparse, os=os,
                       sys=SimpleNamespace(argv=["hud.py"]), STATE=self.copy.path,
                       HERE=Path(HUD).parent, NOTATION=Path(KEEPER).parent,
                       Windows=lambda: self.native, Mutex=lambda *args: self.guard,
                       inventory=Mock(return_value=[]), Hud=Mock(),
                       wm_switch=SimpleNamespace(release_left=Mock()),
                       witnessed=SimpleNamespace(clear=Mock()))
        exec(compile(ast.Module(body=[hud_function("main")], type_ignores=[]), str(HERE / "hud.py"), "exec"), self.ns)

    def tearDown(self):
        self.copy.close()

    def run_main(self, *args):
        self.ns["sys"].argv = ["hud.py", *args]
        with patch.object(sys, "argv", ["hud.py", *args]), contextlib.redirect_stdout(io.StringIO()) as out:
            result = self.ns["main"]()
        return result, out.getvalue()

    def test_mutex_refusal_happens_before_inventory_or_any_gui_effect(self):
        self.guard.acquire.return_value = False
        self.copy.pid.write_text("20")
        code, said = self.run_main()
        self.assertEqual(code, 76)
        self.assertIn("OS mutex", said)
        self.ns["inventory"].assert_not_called()
        self.ns["Hud"].assert_not_called()
        self.ns["witnessed"].clear.assert_not_called()
        self.assertEqual(self.copy.pid.read_text(), "20")

    def test_legacy_process_blocks_start_even_with_missing_pid(self):
        self.ns["inventory"].return_value = [host()]
        code, said = self.run_main()
        self.assertEqual(code, 76)
        self.ns["Hud"].assert_not_called()
        self.guard.close.assert_called_once()
        self.assertFalse(self.copy.pid.exists())

    def test_unknown_inventory_preserves_unclaimed_pid_even_if_number_matches_us(self):
        self.copy.pid.write_text(str(os.getpid()))
        self.ns["inventory"].return_value = None
        code, said = self.run_main()
        self.assertEqual(code, 75)
        self.ns["Hud"].assert_not_called()
        self.assertEqual(self.copy.pid.read_text(), str(os.getpid()))

    def test_successful_start_holds_mutex_until_app_returns_and_owns_its_pid(self):
        def run():
            self.assertEqual(self.copy.pid.read_text(), str(os.getpid()))
            self.guard.close.assert_not_called()
        self.ns["Hud"].return_value.run.side_effect = run
        self.copy.pid.write_text("999")
        code, said = self.run_main()
        self.assertEqual(code, 0)
        self.ns["Hud"].return_value.run.assert_called_once()
        self.guard.close.assert_called_once()
        self.assertFalse(self.copy.pid.exists())

    def test_stop_with_unknown_inventory_never_ends_a_bare_pid(self):
        self.copy.pid.write_text("999")
        self.ns["inventory"].return_value = None
        code, said = self.run_main("--stop")
        self.assertEqual(code, 75)
        self.native.end.assert_not_called()
        self.ns["wm_switch"].release_left.assert_not_called()
        self.assertEqual(self.copy.pid.read_text(), "999")

    def test_stop_does_not_kill_unrelated_reused_pid(self):
        self.copy.pid.write_text("20")
        self.ns["inventory"].return_value = [replace(host(), argv=(EXE, "-c", "pass"))]
        code, said = self.run_main("--stop")
        self.assertEqual(code, 0)
        self.native.end.assert_not_called()
        self.assertEqual(self.copy.pid.read_text(), "20")


class HotkeyRecoveryTests(unittest.TestCase):
    def test_survivor_retries_hotkey_after_old_host_releases_it(self):
        import ctypes
        from ctypes import wintypes as wt
        tree = ast.parse((HERE / "hud.py").read_text(encoding="utf-8"))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Hud")
        keys = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "keys")
        # The duplicate initially owns Ctrl+Alt+J. It ends, a retry arrives, and
        # a further retry must not register the same hotkey twice.
        messages = iter([0x8003, 0x8003])
        def message(pointer, *args):
            try:
                pointer._obj.message = next(messages)
                return 1
            except StopIteration:
                return 0
        user = SimpleNamespace(RegisterHotKey=Mock(side_effect=[False, True]),
                               GetMessageW=message, UnregisterHotKey=Mock())
        ns = dict(ctypes=ctypes, wt=wt, user32=user,
                  kernel32=SimpleNamespace(GetCurrentThreadId=lambda: 1),
                  host_verbs=SimpleNamespace(hotkey=lambda s: (3, 74)),
                  MOD_CONTROL=2, MOD_ALT=1, VK_J=74, MOD_NOREPEAT=0x4000,
                  HK_TOGGLE=1, HK_ESC=2, WM_HOTKEY=0x312, WM_APP=0x8000, VK_ESCAPE=27)
        exec(compile(ast.Module(body=[keys], type_ignores=[]), str(HERE / "hud.py"), "exec"), ns)
        self_stub = SimpleNamespace(settings={"hotkey": "Ctrl+Alt+J"}, toggle=Mock(), hide=Mock())
        with contextlib.redirect_stdout(io.StringIO()) as out:
            ns["keys"](self_stub)
        self.assertEqual(user.RegisterHotKey.call_count, 2)
        self.assertIn("available again", out.getvalue())
        self_stub.toggle.assert_not_called()
        self_stub.hide.assert_not_called()


def demo():
    c = Copy()
    try:
        print("COPY DEMO: fake inventory and fake termination; no live hosts queried")
        c.pid.write_text("999")
        for now, rows, ready in [(0, [KEEP], True), (2, None, True), (4, [], False),
                                 (6, [KEEP], True), (11, [KEEP], True),
                                 (12, [KEEP, host(), host(30, 300)], True)]:
            c.processes = rows
            before = len(c.logs)
            c.tick(now, ready)
            print(f"t={now:02}: " + " | ".join(c.logs[before:]))
        print(f"starts={c.starts}; verified fake ends={c.ends}; hud.pid={c.pid.read_text()} (preserved)")
    finally:
        c.close()


if __name__ == "__main__":
    if "--demo" in sys.argv:
        sys.argv.remove("--demo")
        demo()
    unittest.main(verbosity=2)
