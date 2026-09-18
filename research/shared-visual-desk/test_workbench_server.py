import json
import pickle
import tempfile
import unittest
from unittest.mock import patch

from team_desk import run
from workbench_server import Conflict, InvalidDocument, Store

DOC = {
    "state": {
        "content": {"title": 'A "quoted" title; $today \\n literal', "body": "line one\nline two"}
    },
    "program": {"version": 1, "rules": []},
}


class WorkbenchChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.store = Store(self.temporary.name)

    def test_read_is_not_a_save_and_roundtrip_preserves_literal_source(self):
        self.assertIsNone(self.store.read()["document"])
        self.assertFalse(self.store.path.exists())
        result = self.store.save(None, DOC)
        self.assertEqual(result["document"], DOC)
        self.assertEqual(self.store.read()["document"], DOC)
        desk = pickle.loads(self.store.path.read_bytes())
        self.assertEqual(desk.world.events[-1]["by"], "visual-editor")
        output, refused = run(
            self.temporary.name, "visual", "text-reader", [f"read {result['subject']}"]
        )
        self.assertFalse(refused, output)
        self.assertIn("line one", output[0])

    def test_text_edit_blocks_old_browser_and_is_returned_by_next_read(self):
        first = self.store.save(None, DOC)
        changed = {
            "state": {"content": {"title": "Changed from text"}},
            "program": {"version": 1, "rules": []},
        }
        # A normal textual rewrite; no mutation of the backing object tables.
        source = json.dumps(changed).replace('"', '\\"')
        output, refused = run(
            self.temporary.name,
            "visual",
            "text-author",
            [f"read {first['subject']}", f'do rewrite {first["subject"]} text="{source}"'],
        )
        self.assertFalse(refused, output)
        with self.assertRaises(Conflict):
            self.store.save(first["revision"], DOC)
        self.assertEqual(self.store.read()["document"], changed)
        desk = pickle.loads(self.store.path.read_bytes())
        self.assertEqual(desk.world.events[-1]["by"], "text-author")

    def test_failure_does_not_replace_last_saved_source(self):
        first = self.store.save(None, DOC)
        before = self.store.path.read_bytes()
        with patch("workbench_server.pickle.dumps", side_effect=RuntimeError("injected")):
            with self.assertRaises(RuntimeError):
                self.store.save(first["revision"], DOC)
        self.assertEqual(self.store.path.read_bytes(), before)

    def test_invalid_shape_cannot_replace_document(self):
        first = self.store.save(None, DOC)
        with self.assertRaises(InvalidDocument):
            self.store.save(first["revision"], {"state": {}})
        self.assertEqual(self.store.read()["document"], DOC)

    def test_stale_second_writer_rejected(self):
        first = self.store.save(None, DOC)
        second = Store(self.temporary.name)
        next_save = self.store.save(first["revision"], DOC)
        self.assertNotEqual(first["revision"], next_save["revision"])
        with self.assertRaises(Conflict):
            second.save(first["revision"], DOC)


if __name__ == "__main__":
    unittest.main(verbosity=2)
