"""Storage/lifecycle checks on disposable desks, never research conversations."""

import pickle
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import team_desk

HERE = Path(__file__).resolve().parent
FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class TeamDeskChecks(unittest.TestCase):
    def test_three_processes_keep_all_notes_and_attribution(self):
        with TemporaryDirectory() as folder:
            code = """import sys
from team_desk import run
for i in range(4):
    command = f'do create f01 kind=note title="{sys.argv[2]}-{i}"'
    command += ' text="parallel contribution"'
    out, refused = run(sys.argv[1], 'team', sys.argv[2], ['look f01', command])
    assert not refused, out
"""
            jobs = [
                subprocess.Popen(
                    [sys.executable, "-B", "-c", code, folder, actor],
                    cwd=HERE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=FLAGS,
                )
                for actor in ("foundations", "editing", "media")
            ]
            for job in jobs:
                stdout, stderr = job.communicate(timeout=25)
                self.assertEqual(job.returncode, 0, stdout + stderr)
            desk = pickle.loads((Path(folder) / "team.pickle").read_bytes())
            self.assertEqual(len(desk.world.subjects), 12)
            self.assertEqual(
                {s["title"] for s in desk.world.subjects.values()},
                {f"{a}-{i}" for a in ("foundations", "editing", "media") for i in range(4)},
            )
            self.assertEqual(
                {e["by"] for e in desk.world.events}, {"foundations", "editing", "media"}
            )
            self.assertEqual(set(desk._per), {"foundations", "editing", "media"})

    def test_personal_seen_state_is_not_borrowed(self):
        with TemporaryDirectory() as folder:
            team_desk.run(
                folder,
                "team",
                "alice",
                ["look f01", 'do create f01 kind=note title="subject" text="first"'],
            )
            desk = pickle.loads((Path(folder) / "team.pickle").read_bytes())
            appearance = next(n["id"] for n in desk.world.nodes.values() if n["type"] != "surface")
            _, refused = team_desk.run(
                folder, "team", "bob", [f'do rewrite {appearance} text="unseen"']
            )
            self.assertTrue(refused)
            _, refused = team_desk.run(
                folder,
                "team",
                "bob",
                [f"read {appearance}", f'do rewrite {appearance} text="seen"'],
            )
            self.assertFalse(refused)

    def test_snapshot_does_not_rewrite_session(self):
        with TemporaryDirectory() as folder:
            team_desk.run(folder, "team", "alice", ["look"])
            path = Path(folder) / "team.pickle"
            before = path.read_bytes()
            team_desk.run(folder, "team", "observer", [], snapshot=True)
            self.assertEqual(path.read_bytes(), before)

    def test_serialization_failure_preserves_saved_state(self):
        with TemporaryDirectory() as folder:
            team_desk.run(folder, "team", "alice", ["look"])
            path = Path(folder) / "team.pickle"
            before = path.read_bytes()
            with patch.object(
                team_desk.pickle, "dumps", side_effect=RuntimeError("injected failure")
            ):
                with self.assertRaises(RuntimeError):
                    team_desk.run(
                        folder, "team", "alice", ["look", 'do rename f01 title="unsaved"']
                    )
            self.assertEqual(path.read_bytes(), before)
            team_desk.run(folder, "team", "alice", ["look"])

    def test_dead_process_releases_lock_without_deleting_guard(self):
        with TemporaryDirectory() as folder:
            code = """from pathlib import Path
import sys,time
from team_desk import session_lock
with session_lock(Path(sys.argv[1]) / 'team.guard'):
    print('READY', flush=True)
    time.sleep(30)
"""
            child = subprocess.Popen(
                [sys.executable, "-B", "-c", code, folder],
                cwd=HERE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=FLAGS,
            )
            try:
                self.assertEqual(child.stdout.readline().strip(), "READY")
                with self.assertRaises(TimeoutError):
                    with team_desk.session_lock(Path(folder) / "team.guard", timeout=0.1):
                        pass
                child.terminate()
                child.wait(timeout=5)
                with team_desk.session_lock(Path(folder) / "team.guard", timeout=1):
                    pass
                self.assertTrue((Path(folder) / "team.guard").exists())
            finally:
                if child.poll() is None:
                    child.kill()
                child.communicate(timeout=5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
