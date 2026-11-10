"""In-memory compiler, world persistence, fences and exact-patch checks. No window."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "text-desk" / "notation"))
import explore
import lens_ir
import scene
import stage


class Dividers(unittest.TestCase):
    def setUp(self):
        self.d = explore.fresh()
        self.d.world.me = "jeff"
        self.root = self.d.world.root
        self.do(f"look {self.root}")
        self.do(f'do create {self.root} kind=note title=Left weight=1')
        self.do(f'do create {self.root} kind=note title=Right weight=2')
        self.src = (f"root : row, of kind:note,in:{self.root} as p, each panel\n"
                    "panel : column, share $($p.weight or 1), resize weight min 240\n"
                    '  title : text "$title"')

    def do(self, line):
        r = self.d.dispatch("desk", {"line": line, "reply": "put"})
        self.assertFalse(r.get("error"), r)
        text = r.get("text") or str(r)
        self.assertNotIn("ERR", text)
        return text

    def painted(self, src=None):
        sc = lens_ir.evaluate(self.d, src or self.src)
        scene.emit(sc)
        return sc, scene.painter_view(sc)

    def test_compile_and_text_show_gesture(self):
        sc, pv = self.painted()
        self.assertEqual([k["paint"]["share"] for k in pv["kids"]], [1, 2])
        self.assertEqual(pv["kids"][0]["paint"]["resize"], ["weight", 240])
        self.assertEqual(pv["kids"][0]["acts"][0]["on"], "resize")
        self.assertIn("resize", scene.to_text(sc, "divider-test", "jeff", 0))

    def test_two_props_persist_and_repaint(self):
        _, pv = self.painted()
        lines = []
        for kid, value in zip(pv["kids"], [1.7, 1.3]):
            self.do(f'read {kid["fence"]["item"]}')
            lines.append(kid["acts"][0]["line"].replace("$value", str(value)))
        self.do("; ".join(lines))
        _, again = self.painted()
        self.assertEqual([k["paint"]["share"] for k in again["kids"]], [1.7, 1.3],
                         self.do("find kind:note") + repr(self.d.world.events[-2:]))

    def test_missing_prop_is_fenced(self):
        src = self.src.replace("resize weight", "resize new_weight")
        _, pv = self.painted(src)
        self.assertTrue(any("prop:new_weight" in (r[2] or []) for r in pv["kids"][0]["fence"]["reads"] if r[0] != "select"))

    def test_admission(self):
        for word in ["resize weight min 0", "resize x", "resize x min -1", "resize x min 3.2"]:
            with self.assertRaises(scene.LensRefusal):
                scene.parse("root : column, " + word)
        with self.assertRaises(scene.LensRefusal):
            self.painted("root : column, resize weight min 240")

    def test_stage_preserves_music_scroll_and_foot(self):
        before = (HERE / "home-tiling.before").read_text(encoding="utf-8")
        after = stage.staged(before)
        self.assertEqual(after.count("\n  resize "), 3)
        self.assertEqual(after.count("scroll scroll"), before.count("scroll scroll"))
        self.assertIn("lens $p.filled", after)
        self.assertEqual(stage.staged(after), after)
        with self.assertRaises(ValueError):
            stage.staged(before.replace("  share $span", "  share 3"))
        # A concurrent unrelated edit survives the exact patches.
        self.assertIn("# music changed", stage.staged(before + "\n# music changed"))


if __name__ == "__main__":
    unittest.main()
