# health: room test
"""Offline regressions for visit scratch, vanished paths and landing isolation."""
import errno
import io
import os
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "window-lab"))
import agora_tmp
import door
import fixture_cleanup as cleanup
import landing


class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(agora_tmp.directory("cleanup-test-"))

    def tearDown(self):
        errors = cleanup.remove_tree(self.root, readonly=True)
        self.assertEqual(errors, [])

    def test_nested_git_repository_removed_not_silently_left(self):
        tree = self.root / "trees/a9002"
        tree.mkdir(parents=True)
        for args in (["init", "-q"], ["-c", "user.name=test", "-c", "user.email=test@example.invalid",
                                    "commit", "--allow-empty", "-qm", "fixture"]):
            subprocess.run(["git", *args], cwd=tree, check=True, capture_output=True)
        self.assertTrue((tree / ".git/logs/HEAD").exists())
        if sys.platform == "win32":
            # Reproduce the old finally: Git's read-only objects survive silently.
            cleanup.shutil.rmtree(tree, ignore_errors=True)
            self.assertTrue(tree.exists(), "old cleanup unexpectedly removed readonly Git objects")
        self.assertEqual(cleanup.remove_tree(tree, readonly=True), [])
        self.assertFalse(tree.exists())

    @unittest.skipUnless(sys.platform == "win32", "Windows sharing semantics")
    def test_real_held_output_reports_then_cleans_when_owner_closes(self):
        import ctypes
        from ctypes import wintypes
        path = self.root / "deskd.out"
        path.write_text("private fixture", encoding="utf-8")
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        create = kernel.CreateFileW
        create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                           wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        create.restype = wintypes.HANDLE
        close = kernel.CloseHandle
        close.argtypes = [wintypes.HANDLE]
        close.restype = wintypes.BOOL
        handle = create(str(path), 0x80000000, 0, None, 3, 0x80, None)
        self.assertNotEqual(handle, wintypes.HANDLE(-1).value)
        try:
            errors = cleanup.remove_tree(self.root, attempts=2, pause=0)
            self.assertTrue(errors)
            self.assertIn("deskd.out", "\n".join(errors))
            self.assertTrue(path.exists())
        finally:
            close(handle)
        self.assertEqual(cleanup.remove_tree(self.root), [])

    def test_door_pipe_eof_reaps_owned_backends_before_exit(self):
        stopped, serving, calls = threading.Event(), threading.Event(), []

        class Server:
            daemon_threads = False

            def __init__(self, *args):
                pass

            def shutdown(self):
                stopped.set()

            def serve_forever(self):
                serving.set()
                self.assertion = stopped.wait(2)
                if not self.assertion:
                    raise AssertionError("parent EOF did not stop door")

            def server_close(self):
                calls.append("server closed")

        owned = SimpleNamespace(
            stopping=threading.Event(), entering=threading.Lock(), visiting=threading.RLock(),
            join_retired=lambda: calls.append("retired reaped"), start_first=lambda: None,
            watch=lambda: stopped.wait(2),
            current=SimpleNamespace(stop=lambda *args: calls.append("home reaped")),
            versions={"fixture": SimpleNamespace(stop=lambda: calls.append("visit reaped"))})
        def eof():
            if not serving.wait(2):
                raise AssertionError("door never served")
            return b""
        with patch.object(door, "Door", return_value=owned), \
                patch.object(door, "ThreadingHTTPServer", Server), \
                patch.object(sys, "argv", ["door.py", "--no-git", "--lifetime-stdin"]), \
                patch.object(sys, "stdin", SimpleNamespace(buffer=SimpleNamespace(read=eof))):
            door.main()
        self.assertEqual(calls, ["server closed", "home reaped", "visit reaped", "retired reaped"])
        self.assertTrue(owned.stopping.is_set())

    def test_real_pipe_eof_waits_for_owned_child_and_releases_output(self):
        # Real process/pipe/file lifetime, fake backend: no world, port or model.
        program = """
import pathlib, subprocess, sys, threading
from types import SimpleNamespace
import door
root = pathlib.Path(sys.argv[1])
class Owned:
    def __init__(self):
        self.out = (root / 'deskd.out').open('w')
        self.proc = subprocess.Popen([sys.executable, '-c', 'import sys; sys.stdin.buffer.read()'],
                                     stdin=subprocess.PIPE, stdout=self.out)
    def stop(self, *args):
        self.proc.stdin.close()
        self.proc.wait(timeout=5)
        self.out.close()
        (root / 'reaped').touch()
class TestDoor:
    def __init__(self, *args):
        self.stopping = threading.Event()
        self.entering = threading.Lock()
        self.visiting = threading.RLock()
        self.current, self.versions = None, {}
    def start_first(self):
        self.current = Owned()
    def watch(self):
        self.stopping.wait()
    def join_retired(self):
        pass
class Server:
    def __init__(self, *args):
        self.done = threading.Event()
    def serve_forever(self):
        (root / 'ready').touch()
        self.done.wait()
    def shutdown(self):
        self.done.set()
    def server_close(self):
        pass
door.Door, door.ThreadingHTTPServer = TestDoor, Server
sys.argv = ['door.py', '--no-git', '--lifetime-stdin']
door.main()
"""
        proc = subprocess.Popen([sys.executable, "-c", program, str(self.root)], cwd=HERE,
                                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL)
        try:
            until = time.monotonic() + 5
            while not (self.root / "ready").exists() and time.monotonic() < until:
                time.sleep(0.02)
            self.assertTrue((self.root / "ready").exists())
        finally:
            proc.stdin.close()
            proc.wait(timeout=10)
        self.assertEqual(proc.returncode, 0)
        self.assertTrue((self.root / "reaped").exists())
        self.assertEqual(cleanup.remove_tree(self.root), [])

    def test_retired_visit_cleanup_is_joined_even_after_leaving_version_map(self):
        owner = object.__new__(door.Door)
        owner.retiring, owner.retiring_lock = [], threading.Lock()
        started, release, joined = threading.Event(), threading.Event(), threading.Event()

        def cleanup_visit():
            started.set()
            release.wait(2)

        owner.retire(SimpleNamespace(stop=cleanup_visit))
        self.assertTrue(started.wait(1))

        def join():
            owner.join_retired()
            joined.set()
        waiter = threading.Thread(target=join)
        waiter.start()
        try:
            self.assertFalse(joined.wait(0.02), "returning before visit cleanup finishes recreates the race")
        finally:
            release.set()
            waiter.join(2)
        self.assertTrue(joined.is_set())

    def test_vanished_nested_git_paths_are_success(self):
        tree = self.root / "trees/a9002"
        tree.mkdir(parents=True)
        real = cleanup.shutil.rmtree

        def race(path, onerror):
            real(path)
            for name in (".git/info", ".git/logs"):
                onerror(os.rmdir, str(path / name), (FileNotFoundError,
                        FileNotFoundError(errno.ENOENT, "No such file or directory"), None))
        with patch.object(cleanup.shutil, "rmtree", side_effect=race):
            self.assertEqual(cleanup.remove_tree(tree), [])

    def test_held_output_and_visits_retry_then_remove(self):
        tree = self.root / "state"
        tree.mkdir()
        real = cleanup.shutil.rmtree
        calls = []

        def held(path, onerror):
            calls.append(path)
            if len(calls) == 1:
                for name, error in (("deskd.out", OSError(errno.EINVAL, "Invalid argument")),
                                    ("visits", PermissionError(errno.EACCES, "Permission denied"))):
                    onerror(os.unlink, str(path / name), (type(error), error, None))
            else:
                real(path)
        with patch.object(cleanup.shutil, "rmtree", side_effect=held):
            self.assertEqual(cleanup.remove_tree(tree, pause=0), [])
        self.assertEqual(len(calls), 2)

    def test_held_legacy_scratch_warns_and_does_not_fail_landing(self):
        results = subprocess.CompletedProcess([], 0, "", "")
        with patch.object(landing, "ROOM", self.root), \
                patch.object(landing, "git", return_value=results) as git, \
                patch.object(landing, "log") as log, \
                patch("fixture_cleanup.remove_tree", return_value=["state/deskd.out: Invalid argument",
                      "state/visits: Permission denied"]), \
                patch("sys.stderr", new_callable=io.StringIO) as err:
            landing.clean_room()
        self.assertIn("could not remove", err.getvalue())
        self.assertIn("deskd.out", err.getvalue())
        self.assertIn("Permission denied", err.getvalue())
        log.assert_called_once()
        self.assertEqual(git.call_args.args, ("clean", "-ffdxq", "-e", "/research/window-lab/.tmp-agora/"))

    def test_vanished_git_clean_path_retried(self):
        results = [subprocess.CompletedProcess([], 1, "", "No such file or directory"),
                   subprocess.CompletedProcess([], 0, "", "")]
        with patch.object(landing, "ROOM", self.root), patch.object(landing, "git", side_effect=results) as git:
            landing.clean_room()
        self.assertEqual(git.call_count, 2)

    def test_real_git_clean_excludes_only_rooted_tool_scratch(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)
        scratch = self.root / "research/window-lab/.tmp-agora"
        scratch.mkdir(parents=True)
        (scratch / "held.out").touch()
        source = self.root / "untracked-source.py"
        source.touch()
        with patch.object(landing, "ROOM", self.root), patch.object(landing, "log"), \
                patch("fixture_cleanup.remove_tree", return_value=["held fixture"]), \
                patch("sys.stderr", new_callable=io.StringIO):
            landing.clean_room()
        self.assertFalse(source.exists())
        self.assertTrue((scratch / "held.out").exists())

    def test_non_scratch_failure_still_refuses(self):
        result = subprocess.CompletedProcess([], 1, "", "untracked-source.py: Permission denied")
        with patch.object(landing, "ROOM", self.root), patch.object(landing, "git", return_value=result):
            with self.assertRaisesRegex(RuntimeError, "untracked-source.py: Permission denied"):
                landing.clean_room()

    def test_visit_directory_uses_external_opt_in_without_changing_general_tmp(self):
        external = self.root / "outside-room"
        with patch.dict(os.environ, {"AGORA_VISIT_TMP": str(external)}):
            path = cleanup.visit_directory()
        self.assertEqual(path.parent, external)
        self.assertTrue(path.name.startswith("test-visit-"))

    def test_health_inherits_outside_room_visit_scratch(self):
        lab = self.root / "room/research/text-desk-lab/notation"
        lab.mkdir(parents=True)
        state = self.root / "house-state"
        result = subprocess.CompletedProcess([], 0, '{"ok":true,"failed":[]}\n', "")
        with patch.object(landing, "STATE", state), patch.object(landing.subprocess, "run", return_value=result) as run:
            self.assertTrue(landing.health("fixture", lab)["ok"])
        visits = Path(run.call_args.kwargs["env"]["AGORA_VISIT_TMP"])
        self.assertEqual(visits, (state / "test-visits").resolve())
        self.assertFalse(visits.is_relative_to(self.root / "room"))


if __name__ == "__main__":
    unittest.main()
