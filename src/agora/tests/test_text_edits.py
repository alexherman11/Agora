"""Text with a history (Alex, 4 Nov 2026: "make it a crdt ... make documents work more like a regular document
editor"). `edit` changes a text fact by spans and keeps every change in a Loro body beside the world. These run in a
scratch kernel; no model, no window."""
import json
import shutil
import sys
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))

from kernel.kernel import Kernel, Actor  # noqa: E402
from kernel import scratch  # noqa: E402
from kernel.bodies import fingerprint  # noqa: E402

GENESIS = {"tag": "dk", "name": "Alex's desktop", "steward": {"account": "desktop:alex", "name": "Alex"}}


def quoted(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


class TextEdits(unittest.TestCase):
    def setUp(self):
        self.dir = scratch.mkdtemp(prefix="kernel-edit-")
        self.k = Kernel(self.dir, dict(GENESIS))
        self.alex = self.k.accounts["desktop:alex"]
        self.pike = self.k.join("desktop:pike", "Pike", invite={"admitted": "member"})["person"]
        self.doc = self.run_as(self.alex, 'make kind=document title="Plans" text="Hello world"')["made"][0]

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_as(self, who, line, ok=True):
        out = self.k.run(Actor(who, who, "person"), line)
        self.assertEqual(out["ok"], ok, out["text"])
        return out

    def text(self):
        return self.k.state.get(self.doc, "text")

    def edit(self, changes, base=None, version="", who=None, ok=True):
        base = base or fingerprint(self.text())
        line = f'edit {self.doc} changes={quoted(json.dumps(changes))} base={base}' + (f' version={version}' if version else '')
        return self.run_as(who or self.alex, line, ok)

    def test_spans_change_the_fact(self):
        out = self.edit([[5, 5, ","], [11, 11, "!"]])
        self.assertEqual(self.text(), "Hello, world!")
        self.assertEqual(out["rows"][0]["base"], fingerprint("Hello, world!"))
        self.edit([[0, 5, "Goodbye"]])
        self.assertEqual(self.text(), "Goodbye, world!")

    def test_utf16_positions_count_like_a_browser(self):
        self.run_as(self.alex, f'set {self.doc} text="a😀b"')
        self.edit([[3, 3, "c"]])           # 😀 is two UTF-16 units: a=0, 😀=1..2, b=3
        self.assertEqual(self.text(), "a😀cb")

    def test_stale_without_version_is_refused(self):
        base = fingerprint(self.text())
        self.run_as(self.alex, f'set {self.doc} text="Hello there world"')
        out = self.edit([[0, 0, "Oh. "]], base=base, ok=False)
        self.assertIn("stale", out["text"])
        self.assertEqual(self.text(), "Hello there world")

    def test_a_change_made_meanwhile_merges_with_version(self):
        out = self.edit([[11, 11, "."]])                 # "Hello world."
        base, version = out["rows"][0]["base"], out["rows"][0]["version"]
        self.run_as(self.alex, f'set {self.doc} text="Hello big world."')   # someone writes the whole text
        out = self.edit([[0, 0, "Oh. "]], base=base, version=version)       # made against "Hello world."
        self.assertEqual(self.text(), "Oh. Hello big world.")
        self.assertTrue(out["rows"][0]["merged"])
        self.assertEqual(out["rows"][0]["text"], "Oh. Hello big world.")

    def test_others_need_set_rights(self):
        out = self.edit([[0, 0, "x"]], who=self.pike, ok=False)
        self.assertEqual(self.text(), "Hello world")

    def test_undo_takes_it_back_and_the_body_follows(self):
        self.edit([[11, 11, "!"]])
        self.run_as(self.alex, "undo")
        self.assertEqual(self.text(), "Hello world")
        self.edit([[0, 0, ">"]])
        self.assertEqual(self.text(), ">Hello world")

    def test_history_survives_a_restart(self):
        for i in range(5):
            self.edit([[len(self.text()), len(self.text()), f" {i}"]])
        body = Path(self.dir) / "bodies" / f"{self.doc}.text.loro"
        self.assertTrue(body.exists())
        k2 = Kernel(self.dir, dict(GENESIS))
        out = k2.run(Actor(self.alex, self.alex, "person"), f"edits {self.doc}")
        self.assertTrue(out["ok"], out["text"])
        self.assertGreaterEqual(len(out["rows"]), 1)
        import loro
        d = loro.LoroDoc()
        raw, i, blobs = body.read_bytes(), 0, []
        while i < len(raw):
            n = int.from_bytes(raw[i:i + 4], "big"); blobs.append(raw[i + 4:i + 4 + n]); i += 4 + n
        d.import_batch(blobs)
        self.assertEqual(d.get_text("text").to_string(), "Hello world 0 1 2 3 4")

    def test_bad_changes_are_refused(self):
        self.edit([[3, 99, ""]], ok=False)
        self.edit([[5, 5, "a"], [2, 2, "b"]], ok=False)
        self.assertEqual(self.text(), "Hello world")


if __name__ == "__main__":
    unittest.main()
