# health: room test
"""Final-candidate session fence, including contamination outside worker ancestry."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "desktop"))
import agora_tmp
import landing
from fixture_cleanup import remove_tree


class CandidateFence(unittest.TestCase):
    def setUp(self):
        self.root = Path(agora_tmp.directory("landing-state-guard-"))
        self.addCleanup(self.cleanup)
        self.env = {
            "GIT_AUTHOR_NAME": "Isolated fixture",
            "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
            "GIT_COMMITTER_NAME": "Isolated fixture",
            "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        }
        self.g("init", "-q", "-b", "main")
        self.put("source.txt", "base\n")
        self.commit("base")
        self.base = self.g("rev-parse", "HEAD")

    def cleanup(self):
        self.assertEqual(remove_tree(self.root, readonly=True), [])

    def g(self, *args):
        return landing.git(*args, cwd=self.root, env=self.env, check=True).stdout.strip()

    def put(self, name, text):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def commit(self, message):
        self.g("add", "-A")
        self.g("commit", "-qm", message)
        return self.g("rev-parse", "HEAD")

    def refuse(self, candidate, names, base=None):
        # No live file/index inspection, parking or merge may follow the fence.
        with patch.object(landing, "LIVE", self.root), \
                patch.object(landing, "dirty_in_live", side_effect=AssertionError("no live state reads")), \
                patch.object(landing, "park", side_effect=AssertionError("no parking")):
            result = landing.advance(candidate, base or self.base, "fixture")
        self.assertFalse(result[0])
        self.assertIsNone(result[1])
        for name in names:
            self.assertIn(name, result[2])
        self.assertEqual(self.g("rev-parse", "HEAD"), base or self.base)

    def test_fixture_parent_contamination_refuses_before_touching_live_files(self):
        self.g("switch", "-qc", "worker")
        self.put("source.txt", "worker change\n")
        worker = self.commit("source work")
        self.g("switch", "-qc", "room", self.base)
        names = [landing.NOTATION + "/sessions/frontier.log.jsonl",
                 landing.NOTATION + "/sessions/frontier.undo.sqlite"]
        for name in names:
            self.put(name, "synthetic state, never live data\n")
        self.commit("fixture")
        self.g("merge", "--no-ff", "-qm", "candidate", worker)
        candidate = self.g("rev-parse", "HEAD")
        self.g("switch", "-q", "main")
        for name in names:
            self.put(name, "untracked live stand-in\n")
        self.refuse(candidate, names)
        for name in names:
            self.assertEqual((self.root / name).read_text(), "untracked live stand-in\n")
        self.assertEqual(self.g("diff", "--cached", "--name-only"), "")

    def test_modification_and_deletion_of_existing_session_fixture_refuse(self):
        name = landing.NOTATION + "/sessions/fixture.txt"
        self.put(name, "old tracked fixture")
        base = self.commit("legacy tracked fixture")
        self.g("switch", "-qc", "worker")
        self.put(name, "changed fixture")
        changed = self.commit("modify")
        (self.root / name).unlink()  # this test's own fixture, not a world
        deleted = self.commit("delete")
        self.g("switch", "-q", "main")
        self.refuse(changed, [name], base)
        self.refuse(deleted, [name], base)

    def test_clean_source_candidate_can_advance(self):
        self.g("switch", "-qc", "worker")
        self.put("source.txt", "source change\n")
        candidate = self.commit("source")
        self.g("switch", "-q", "main")
        with patch.object(landing, "LIVE", self.root):
            moved, parked, reason = landing.advance(candidate, self.base, "fixture")
        self.assertTrue(moved, reason)
        self.assertIsNone(parked)
        self.assertEqual(self.g("rev-parse", "HEAD"), candidate)

    def test_health_head_mutation_aborts_before_caching_judgment(self):
        kept = {}

        def contaminated_health(*args, **kwargs):
            self.put("unexpected.txt", "stand-in for an escaped fixture commit")
            self.commit("fixture")
            return {"ok": True}

        with patch.object(landing, "ROOM", self.root), \
                patch.object(landing, "copy_world"), \
                patch.object(landing, "health", side_effect=contaminated_health):
            with self.assertRaisesRegex(RuntimeError, "health changed landing-room HEAD"):
                landing.judged("synthetic", self.base, kept)
        self.assertEqual(kept, {})

    def test_unchanged_health_head_keeps_normal_judgment(self):
        kept = {}
        with patch.object(landing, "ROOM", self.root), \
                patch.object(landing, "copy_world"), \
                patch.object(landing, "health", return_value={"ok": True}), \
                patch.object(landing, "log"):
            result = landing.judged("synthetic", self.base, kept)
        self.assertTrue(result["ok"])
        self.assertTrue(kept["health"]["synthetic:" + self.base]["ok"])


if __name__ == "__main__":
    unittest.main()
