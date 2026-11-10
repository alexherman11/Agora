"""Review recipe preflight and commands, in memory; never starts the runner."""
import json
import re
import unittest
from unittest.mock import patch

import review_copy as review
import explore


class Review(unittest.TestCase):
    def setUp(self):
        self.d = explore.fresh()
        self.d.world.me = "hud-playtest"
        self.root = self.d.world.root
        self.lay = self.create(self.root, "surface", "Layout", "role=home-layout actor=alex")
        self.col = self.create(self.lay, "surface", "Column", "span=2")
        self.panel = self.create(self.col, "note", "Music",
                                 "role=home-panel shelf=yes sizing=content chrome=none")
        # The recipe preserves stored gesture names; harmless local definitions
        # let the fixture admit them without invoking either gesture.
        for name in ("drop-panel", "close-panel"):
            self.create(self.root, "note", name,
                        "tags=verb on=" + self.root + " text=" + review.pt.q("do prop $1 touched=yes"))
        text = (review.HERE / "home-tiling.current").read_text(encoding="utf-8")
        self.lens = self.create(self.root, "note", "home-tiling", "tags=lens text=" + review.pt.q(text))

    def do(self, line):
        result = self.d.dispatch("desk", {"line": line, "whole": True, "reply": "put"})
        self.assertFalse(result.get("error"), result)
        self.assertNotIn("ERR", result.get("text", ""))
        return result["text"]

    def create(self, parent, kind, title, more):
        self.do("look " + parent)
        nid = re.search(r"created (\w+)", self.do(
            f"do create {parent} kind={kind} title={review.pt.q(title)} "
            + (more if kind != "surface" else "")))[1]
        if kind == "surface":
            self.do("look " + nid)
            self.do(f"do prop {nid} {more}")
        return nid

    def test_recipe_migrates_copy_without_membership_changes(self):
        before = {i: n["parent"] for i, n in self.d.world.nodes.items()}
        for command in review.prepare_navigation(self.d.snapshot()):
            self.do(command)
        props = self.d.world.nodes[self.lay]["props"]
        self.assertEqual(props["copy_json"], "tree")
        leaf = json.loads(props["tree"])["root"]
        self.assertEqual(leaf, {"id": {"$ref": self.panel}, "size": "content"})
        self.assertEqual(before, {i: n["parent"] for i, n in self.d.world.nodes.items()})
        self.assertIn("partition tree", self.d.world.subjects[
            self.d.world.nodes[self.lens]["subject"]]["text"])

    def test_existing_tree_and_copy_declarations_preserved(self):
        raw = '{"v":1,"root":null,"literal":"keep me"}'
        self.do("look " + self.lay)
        self.do(f"do prop {self.lay} tree={review.pt.q(raw)} copy_json=other")
        for command in review.prepare_navigation(self.d.snapshot()):
            self.do(command)
        props = self.d.world.nodes[self.lay]["props"]
        self.assertEqual(props["tree"], raw)
        self.assertEqual(props["copy_json"], "other,tree")

    def test_preflight_stops_before_mutating(self):
        snap = self.d.snapshot()
        snap["subjects"][snap["nodes"][self.lens]["subject"]]["text"] = "changed"
        at = len(self.d.world.events)
        with self.assertRaises(ValueError):
            review.prepare_navigation(snap)
        self.assertEqual(len(self.d.world.events), at)
        with self.assertRaisesRegex(ValueError, "disposable"):
            review.stage_copy(type("NotCopy", (), {"session": "frontier"})())

    def combined_snapshot(self, applied=False):
        snap = self.d.snapshot()
        snap["nodes"]["f5189"] = {"id": "f5189", "type": "surface", "props": {},
                                "parent": self.root}
        for ident, old, new in review.dock_stage.passages():
            sid = "dock-fixture-" + ident
            snap["nodes"][ident] = {"id": ident, "type": "note", "subject": sid,
                                    "parent": "f5189"}
            snap["subjects"][sid] = {"text": new if applied else old}
        if applied:
            for path in review.dock_stage.HERE.glob("*.verb"):
                snap["subjects"]["verb-" + path.stem] = {
                    "title": path.stem, "tags": ["verb"], "props": {"on": "f5189"},
                    "text": path.read_text(encoding="utf-8").rstrip()}
        return snap

    def test_combined_recipe_plans_both_halves(self):
        commands = review.prepare(self.combined_snapshot())
        self.assertEqual(sum("do create f5189" in c for c in commands), 4)
        self.assertEqual(sum(c.startswith("do replace ") for c in commands), 8)
        self.assertTrue(any("on drop any" in c for c in commands))
        self.assertTrue(any("partition tree" in c for c in commands))

    def test_existing_dock_is_not_duplicated_or_overwritten(self):
        snap = self.combined_snapshot(applied=True)
        self.assertEqual(review.prepare_dock(snap), [])
        self.assertEqual(review.prepare(snap), review.prepare_navigation(snap))

    def test_late_dock_preflight_failure_makes_zero_copy_writes(self):
        snap = self.combined_snapshot()
        # Fail the last passage, after earlier passages and navigation preflight.
        node = snap["nodes"]["a5564"]
        snap["subjects"][node["subject"]]["text"] = "newer dock"
        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def read(self):
                return json.dumps(snap).encode()
        writes = []
        copy = type("Copy", (), {"session": "frontier-playtest-fixture",
                                "base": "http://unused.invalid",
                                "do": lambda self, *args: writes.append(args)})()
        with patch.object(review.urllib.request, "urlopen", return_value=Response()):
            with self.assertRaisesRegex(ValueError, "dock passage"):
                review.stage_copy(copy)
        self.assertEqual(writes, [])

    def test_newer_or_duplicate_verb_refuses_instead_of_replacing(self):
        snap = self.combined_snapshot(applied=True)
        key = next(k for k in snap["subjects"] if k.startswith("verb-"))
        original = dict(snap["subjects"][key])
        snap["subjects"][key]["text"] = "new implementation"
        with self.assertRaisesRegex(ValueError, "verb changed"):
            review.prepare(snap)
        snap["subjects"][key] = original
        snap["subjects"]["duplicate"] = dict(original)
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            review.prepare(snap)

    def test_partial_dock_style_refuses(self):
        snap = self.combined_snapshot()
        sid = snap["nodes"]["a5206"]["subject"]
        snap["subjects"][sid]["text"] += "\n# a7223 slim dock begin\npartial"
        with self.assertRaisesRegex(ValueError, "partly applied"):
            review.prepare(snap)


if __name__ == "__main__":
    unittest.main()
