"""Real in-memory world/scene tests, with no window or persisted world."""
import json
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "text-desk-lab" / "notation"))
import explore
import lens_ir
import scene
import deskd
import navigation_stage as stage


class Navigation(unittest.TestCase):
    def setUp(self):
        self.d = explore.fresh()
        self.d.world.me = "jeff"
        self.root = self.d.world.root
        self.do(f"look {self.root}")
        r = self.do(f'do create {self.root} kind=surface title=Layout')
        self.layout = re.search(r"created (\w+)", r["text"])[1]
        self.do(f"look {self.layout}")
        self.do(f"do prop {self.layout} role=home-layout actor=jeff")
        r = self.do(f'do create {self.layout} kind=note title=One role=home-panel pin=yes shelf=no')
        self.a = re.search(r"created (\w+)", r["text"])[1]
        r = self.do(f'do create {self.layout} kind=note title=Two role=home-panel shelf=no')
        self.b = re.search(r"created (\w+)", r["text"])[1]
        self.src = (
            f"root : column, the {self.layout} as lay\n"
            "  tiles : column, share 1, partition tree min 240 140 gap 16 focus full\n"
            f"    of kind:note,in:{self.layout} as p\n"
            "    each panel\n"
            'panel : column, companion ($p.pin or "") = "yes", sizing ($p.sizing or ""), chrome ($p.chrome or "")\n'
            '  title : text "$title"\n'
            "    carry\n"
        )

    def do(self, line):
        r = self.d.dispatch("desk", {"line": line, "reply": "put"})
        self.assertFalse(r.get("error"), r)
        self.assertNotIn("ERR", r.get("text") or "", r)
        return r

    def paint(self, src=None):
        sc = lens_ir.evaluate(self.d, src or self.src)
        scene.emit(sc)
        return sc, scene.painter_view(sc)

    def test_word_emission_and_fences(self):
        _, pv = self.paint()
        tiles = pv["kids"][0]
        self.assertEqual(tiles["paint"]["partition"]["tree"], "")
        self.assertEqual(tiles["paint"]["partition"]["minimum"], [240, 140])
        self.assertEqual(tiles["paint"]["partition"]["focus"], "")
        self.assertEqual([k["paint"]["companion"] for k in tiles["kids"]], [True, False])
        self.assertEqual([k["paint"]["partition_item"] for k in tiles["kids"]], [self.a, self.b])
        reads = [r[2] for r in tiles["fence"]["reads"] if r[0] != "select"]
        self.assertTrue(any("prop:tree" in r and "prop:full" in r for r in reads), reads)
        self.assertEqual(tiles["acts"][-1]["on"], "arrange")

    def test_actual_tree_and_focus_write_repaint(self):
        _, pv = self.paint()
        raw = json.dumps(stage.migration([{"panels": [{"id": self.a}, {"id": self.b}]}]))
        act = pv["kids"][0]["acts"][-1]["line"]
        line = act.replace("$value", raw.replace('"', r'\"')).replace("$partition_focus", self.b)
        self.do(line)
        _, again = self.paint()
        spec = again["kids"][0]["paint"]["partition"]
        self.assertEqual(json.loads(spec["tree"]), json.loads(raw))
        self.assertEqual(spec["focus"], self.b)
        self.do(f"look {self.layout}")
        self.do(f'do prop {self.layout} full=""')
        self.assertEqual(self.paint()[1]["kids"][0]["paint"]["partition"]["focus"], "")

    def test_admission(self):
        for bad in ["partition x", "partition x min 0 140 gap 16", "partition x min 240 140 gap -1"]:
            with self.assertRaises(scene.LensRefusal):
                scene.parse("root : column, " + bad)
        with self.assertRaises(scene.LensRefusal):
            self.paint("root : column, partition tree min 240 140 gap 16")
        with self.assertRaises(scene.LensRefusal):
            scene.parse("root : column, companion (")

    def test_policy_expression_changes_repaint(self):
        self.paint()
        self.do(f"read {self.a}")
        self.do(f"do prop {self.a} sizing=content chrome=none")
        child = self.paint()[1]["kids"][0]["kids"][0]["paint"]
        self.assertEqual(child["sizing"], "content")
        self.assertEqual(child["chrome"], "none")

    def test_partition_fences_members_and_their_policies(self):
        def current(fence):
            for entry in fence["reads"]:
                if entry[0] == "select":
                    if not deskd.same_answer(self.d, entry[1], entry[2])[0]:
                        return False
                else:
                    sid, rev, fields = entry
                    cur = self.d.world.subjects.get(sid) or self.d.world.nodes.get(sid)
                    if not cur or (cur["rev"] != rev and
                                   not (fields and not deskd.touched_aspects(
                                       self.d.world, sid, rev, cur["rev"], fields))):
                        return False
            return True
        for prop in ("sizing=content", "chrome=none", "pin=no", "shelf=yes"):
            old = self.paint()[1]["kids"][0]["fence"]
            self.assertTrue(current(old))
            self.do(f"read {self.a}")
            self.do(f"do prop {self.a} {prop}")
            self.assertFalse(current(old), prop)
            self.assertTrue(current(self.paint()[1]["kids"][0]["fence"]))
        old = self.paint()[1]["kids"][0]["fence"]
        self.do(f"look {self.layout}")
        self.do(f"do create {self.layout} kind=note title=Three")
        self.assertFalse(current(old))
        self.assertTrue(current(self.paint()[1]["kids"][0]["fence"]))
        old = self.paint()[1]["kids"][0]["fence"]
        self.do(f"read {self.b}")
        self.do(f"look {self.root}")
        self.do(f"do move {self.b} into={self.root}")
        self.assertFalse(current(old))

    def test_kept_partition_refreshes_extra_reads(self):
        src = (f"root : column, of kind:surface,in:{self.root}, each group\n"
               + self.src.replace(f"root : column, the {self.layout} as lay",
                                  "group : column, the $item as lay"))
        self.paint(src)
        self.do(f"read {self.a}")
        self.do(f"do prop {self.a} shelf=yes")
        _, changed = self.paint(src)
        _, kept = self.paint(src)
        for pv in (changed, kept):
            tiles = pv["kids"][0]["kids"][0]
            for sid, rev, fields in [r for r in tiles["fence"]["reads"] if r[0] != "select"]:
                cur = self.d.world.subjects.get(sid) or self.d.world.nodes.get(sid)
                self.assertEqual(cur["rev"], rev)

    def test_current_bare_chrome_staging(self):
        before = (HERE / "home-tiling.current").read_text(encoding="utf-8")
        after = stage.staged(before)
        roles = set(re.findall(r"^\s+role ([^\s]+)", after, re.M))
        scene.parse(after, roles=roles)
        for passage in ['role pane.bare when ($p.chrome or "") = "none"',
                        'only when ($p.chrome or "") != "none"',
                        'appgrip : row\n    role appgrip\n    carry',
                        'sizing ($p.sizing or "")', 'chrome ($p.chrome or "")',
                        'lens $p.filled']:
            self.assertIn(passage, after)

    def test_world_migration_preserves_order_and_weights(self):
        manifest = [{"span": 2, "panels": [{"id": self.a, "height_share": 3}, {"id": self.b}]},
                    {"span": 1, "panels": [{"id": "shelved"}]}]
        result = stage.migration(manifest)
        self.assertEqual(result["root"]["weights"], [2, 1])
        self.assertEqual(result["root"]["kids"][0]["weights"], [3, 1])
        self.assertEqual(result["root"]["kids"][1]["id"], {"$ref": "shelved"})
        with self.assertRaises(ValueError):
            stage.migration([{"panels": [{"id": self.a}, {"id": self.a}]}])

    def test_staged_lens_compiles_and_keeps_music_and_controls(self):
        before = (HERE / "home-tiling.before").read_text(encoding="utf-8")
        after = stage.staged(before)
        # Parse with its declared roles, independently from the live stylesheet.
        roles = set(re.findall(r"^\s+role ([^\s]+)", after, re.M))
        scene.parse(after, roles=roles)
        self.assertIn("partition tree min 240 140 gap 16 focus full", after)
        self.assertIn("lens $p.filled", after)
        self.assertIn("scroll scroll", after)
        self.assertIn("do close-panel $p $p.in", after)
        self.assertIn('tip "Panels" "Drag dividers to resize.', after)
        self.assertIn("The following\n# column behavior is retained as historical context", after)
        # Top-row controls and their unrelated lenses are unchanged.
        self.assertEqual(after[after.index("  top : row"):after.index("      keys : text")],
                         before[before.index("  top : row"):before.index("      keys : text")])
        self.assertIn("# unrelated music edit", stage.staged(before + "\n# unrelated music edit"))

    def test_staged_headers_and_filled_lens_run_in_a_world(self):
        before = (HERE / "home-tiling.current").read_text(encoding="utf-8")
        # Roles are checked by the preceding parse test. Here stub unrelated
        # app lenses, isolating actual frame/guard/gesture semantics.
        src = re.sub(r"^ *role [^\n]*\n", "", stage.staged(before), flags=re.M)
        for name in ["home-widgets", "home-search", "home-widgets-end", "app-one", "app-two", "full-one"]:
            self.do(f"look {self.root}")
            self.do(f'do create {self.root} kind=note tags=lens title={stage.quoted(name)} text={stage.quoted("root : text " + stage.quoted(name))}')
        self.do(f"read {self.a}")
        self.do(f"do prop {self.a} lens=app-one filled=full-one")
        self.do(f"read {self.b}")
        self.do(f"do prop {self.b} lens=app-two")
        def flattened(n):
            return [n] + [x for k in n.get("kids", []) for x in flattened(k)]
        _, pv = self.paint(src)
        tiles = next(n for n in flattened(pv) if n["paint"].get("partition"))
        self.assertEqual(len(tiles["kids"]), 2)
        first = tiles["kids"][0]
        self.assertIn("app-one", [n["paint"].get("text") for n in flattened(first)])
        grip = next(n for n in flattened(first) if any(a["on"] == "double" for a in n["acts"]))
        self.assertEqual(len([a for a in grip["acts"] if a["on"] == "double"]), 1)
        self.do(next(a["line"] for a in grip["acts"] if a["on"] == "double"))
        _, filled = self.paint(src)
        nodes = flattened(filled)
        self.assertIn("full-one", [n["paint"].get("text") for n in nodes])
        filled_tiles = next(n for n in nodes if n["paint"].get("partition"))
        self.assertEqual(filled_tiles["paint"]["partition"]["focus"], self.a)
        restore = next(n for n in flattened(filled_tiles["kids"][0]) if any(a["on"] == "double" for a in n["acts"]))
        self.do(next(a["line"] for a in restore["acts"] if a["on"] == "double"))
        self.assertEqual(next(n for n in flattened(self.paint(src)[1]) if n["paint"].get("partition"))["paint"]["partition"]["focus"], "")
        self.do(f"read {self.b}")
        self.do(f"do prop {self.b} shelf=yes")
        hidden_tiles = next(n for n in flattened(self.paint(src)[1]) if n["paint"].get("partition"))
        self.assertEqual(hidden_tiles["kids"][1]["paint"]["partition_item"], self.b)
        self.assertTrue(hidden_tiles["kids"][1]["paint"]["absent"])
        self.do(f"read {self.b}")
        self.do(f"do prop {self.b} shelf=no")
        restored = next(n for n in flattened(self.paint(src)[1]) if n["paint"].get("partition"))
        self.assertFalse(restored["kids"][1]["paint"].get("absent"))
        self.do(f"read {self.a}")
        self.do(f"do prop {self.a} chrome=none sizing=content")
        bare = next(n for n in flattened(self.paint(src)[1]) if n["paint"].get("partition"))["kids"][0]
        self.assertEqual(bare["paint"]["sizing"], "content")
        self.assertEqual(bare["paint"]["chrome"], "none")
        regular = next(n for n in bare["kids"] if n["key"].endswith("/grip"))
        appgrip = next(n for n in bare["kids"] if n["key"].endswith("/appgrip"))
        self.assertTrue(regular["paint"]["absent"])
        self.assertFalse(appgrip["paint"].get("absent"))
        self.assertTrue(any(a["on"] == "carry" for a in appgrip["acts"]))
        self.do(next(a["line"] for a in appgrip["acts"] if a["on"] == "double"))
        self.assertIn("full-one", [n["paint"].get("text") for n in flattened(self.paint(src)[1])])


if __name__ == "__main__":
    unittest.main()
