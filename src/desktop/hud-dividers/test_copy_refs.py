"""Typed-reference copy integration, real in-memory commands; no world files."""
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "text-desk" / "notation"))
import explore


def q(value):
    return json.dumps(value).replace("$", r"\$")


class CopyRefs(unittest.TestCase):
    def setUp(self):
        self.d = explore.fresh()
        self.w = self.d.world
        self.w.me = "jeff"
        self.root = self.w.root
        self.layout = self.create(self.root, "surface", "Layout")
        self.col = self.create(self.layout, "surface", "Column")
        self.a = self.create(self.col, "note", "Music")
        self.b = self.create(self.col, "note", "Chat")
        self.outside = self.create(self.root, "note", "Outside")
        self.holder = self.create(self.root, "surface", "Saved")
        self.line(f"do prop {self.a} pin=yes shelf=no filled=home-music-full lens=home-music")
        self.line(f"do prop {self.b} shelf=yes")
        self.tree = {"v": 1, "root": {"axis": "y", "kids": [
            {"id": {"$ref": self.a}}, {"axis": "tabs", "kids": [
                {"id": {"$ref": self.b}}, {"id": {"$ref": self.outside}}
            ], "active": {"$ref": self.b}}], "weights": [2, 1]},
            "literal": self.a, self.a: "literal key",
            "focus_weights": [{"panel": {"$ref": self.a},
                              "members": [{"panel": {"$ref": self.b}, "weight": 6}]}]}
        self.set_tree(self.tree)

    def line(self, line, okay=True):
        result = self.d.dispatch("desk", {"line": line, "reply": "put", "whole": True})
        text = ("ERR " + str(result["error"])) if result.get("error") else result.get("text", "")
        if okay:
            self.assertNotIn("ERR", text, text)
        return text

    def create(self, parent, kind, title):
        self.line(f"look {parent}")
        return re.search(r"created (\w+)", self.line(
            f"do create {parent} kind={kind} title={title}"))[1]

    def set_tree(self, value):
        raw = value if isinstance(value, str) else json.dumps(value)
        self.line(f"look {self.layout}")
        self.line(f"do prop {self.layout} copy_json=tree full={self.a} tree={q(raw)}")

    def copy(self, source, dest):
        self.line(f"look {source} :3")
        self.line(f"look {dest}")
        return re.search(r"copied \w+ as (\w+)", self.line(f"do copy {source} into={dest}"))[1]

    def test_nested_save_use_roundtrip(self):
        first = self.copy(self.layout, self.holder)
        second = self.copy(first, self.root)
        for copied in [first, second]:
            col = self.w.children(copied)[0]["id"]
            a, b = [n["id"] for n in self.w.children(col)]
            props = self.w.nodes[copied]["props"]
            tree = json.loads(props["tree"])
            self.assertNotEqual(a, self.a)
            self.assertEqual(tree["root"]["kids"][0]["id"], {"$ref": a})
            tabs = tree["root"]["kids"][1]
            self.assertEqual(tabs["kids"][0]["id"], {"$ref": b})
            self.assertEqual(tabs["active"], {"$ref": b})
            self.assertEqual(tabs["kids"][1]["id"], {"$ref": self.outside})
            self.assertEqual(tree["literal"], self.a)
            self.assertEqual(tree[self.a], "literal key")
            self.assertEqual(tree["focus_weights"][0]["panel"], {"$ref": a})
            self.assertEqual(tree["focus_weights"][0]["members"][0]["panel"], {"$ref": b})
            self.assertEqual(props["full"], a)
            music = self.w.subjects[self.w.nodes[a]["subject"]]["props"]
            self.assertEqual(music, {"pin": "yes", "shelf": "no",
                                    "filled": "home-music-full", "lens": "home-music"})
            self.assertEqual(self.w.subjects[self.w.nodes[b]["subject"]]["props"]["shelf"], "yes")

    def test_invalid_refuses_before_any_creation(self):
        for raw in ['{', '{"v":2,"root":null}', '{"v":1,"v":1}',
                    '{"v":1,"x":{"$ref":"a","literal":1}}',
                    '{"v":1,"x":{"$ref":12}}', '{"v":1,"x":NaN}', '{"v":1,"x":1e999}']:
            with self.subTest(raw=raw):
                self.set_tree(raw)
                self.line(f"look {self.layout} :3")
                self.line(f"look {self.holder}")
                events, nodes = len(self.w.events), set(self.w.nodes)
                self.assertIn("ERR", self.line(f"do copy {self.layout} into={self.holder}", okay=False))
                self.assertEqual(len(self.w.events), events)
                self.assertEqual(set(self.w.nodes), nodes)

    def test_opt_in_only(self):
        self.line(f"look {self.layout}")
        self.line(f"do prop {self.layout} remove=copy_json")
        copied = self.copy(self.layout, self.holder)
        self.assertEqual(json.loads(self.w.nodes[copied]["props"]["tree"]), self.tree)

    def test_actual_workspace_save_use(self):
        going = self.create(self.root, "surface", "Going")
        self.line(f"look {self.layout}")
        self.line(f"do prop {self.layout} role=home-layout actor=alex")
        verbs = Path(__file__).resolve().parents[1] / "workspaces"
        for name in ("workspace-keep", "workspace-use", "workspace"):
            body = (verbs / f"{name}.verb").read_text(encoding="utf-8")
            body = body.replace("{WS}", self.holder).replace("{R}", going).replace("f5204", self.root)
            self.line(f"look {self.root}")
            self.line(f"do create {self.root} kind=note title={name} tags=verb on=house text={q(body)}")
        self.line("workspace save mine")
        saved = next(n["id"] for n in self.w.children(self.holder)
                     if (n.get("props") or {}).get("name") == "mine")
        self.line("workspace mine")
        live = next(n for n in self.w.nodes.values()
                    if (n.get("props") or {}).get("role") == "home-layout")
        self.assertNotIn(live["id"], [self.layout, saved])
        col = self.w.children(live["id"])[0]["id"]
        a, b = [n["id"] for n in self.w.children(col)]
        tree = json.loads(live["props"]["tree"])
        self.assertEqual(tree["root"]["kids"][0]["id"], {"$ref": a})
        self.assertEqual(tree["root"]["kids"][1]["active"], {"$ref": b})
        self.assertEqual(tree["literal"], self.a)
        self.assertEqual(live["props"]["full"], a)


if __name__ == "__main__":
    unittest.main()
