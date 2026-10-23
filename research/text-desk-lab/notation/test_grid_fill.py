# health: room test
"""a10637: `grid fill <min>`, a grid that fits as many columns as its width holds. Compiler side: the word, its forms,
its refusals and what the scene sends the painter. The painter side is checked by eye in screen.py at 1280 and 2560."""
import unittest

import lens_ir
import roomworld
import scene

TILES = """tiles : grid fill {m}
  of prop:fixture=yes as c
  each tile
tile : text "$c.title"
  role card
"""


class GridFill(unittest.TestCase):
    def test_forms(self):
        for said, track in (("18ch", "fill 18ch"), ("12gap", "fill 12gap"), ("240", "fill 240px"), ("240px", "fill 240px"), ("17.5ch", "fill 17.5ch")):
            _, parts = scene.parse(TILES.format(m=said))
            self.assertEqual((parts["tiles"]["layout"], parts["tiles"]["tracks"]), ("grid", [track]), said)

    def test_refusals(self):
        for bad in ("", "0", "wide", "18em", "18ch 2"):
            with self.assertRaises(scene.LensRefusal, msg=bad):
                scene.parse(TILES.format(m=bad))

    def test_fixed_tracks_are_unchanged(self):
        _, parts = scene.parse("ws : grid 1 3fr fit 12gap\n")
        self.assertEqual(parts["ws"]["tracks"], ["1fr", "3fr", "fit", "12gap"])

    def test_pack_forms_and_refusals(self):
        for unit in ("18ch", "12gap", "240px", "240", "17.5ch"):
            _, p = scene.parse(TILES.format(m=unit + " pack"))
            minimum = unit + "px" if unit == "240" else unit
            self.assertEqual(p["tiles"]["tracks"], ["fill " + minimum + " pack"])
        invalid = ("pack", "0 pack", "18em pack", "18ch pack pack",
                   "18ch dense", "18ch pack extra")
        for bad in invalid:
            with self.assertRaises(scene.LensRefusal, msg=bad):
                scene.parse(TILES.format(m=bad))

    def test_pack_roundtrip_is_read_only(self):
        d, _ = roomworld.build(say=False)
        before = list(d.events)
        sc = lens_ir.evaluate(d, TILES.format(m="18ch pack"))
        self.assertEqual(sc["tracks"], ["fill 18ch pack"])
        self.assertIn("grid fill 18ch pack", scene.to_text(sc, "t", "jeff", 0))
        self.assertIn("grid fill 18ch pack", scene.to_lines(TILES.format(m="18ch pack")))
        self.assertEqual(d.events, before)

    def test_scene_prints_and_sends_it(self):
        d, r = roomworld.build(say=False)
        sc = lens_ir.evaluate(d, TILES.format(m="18ch"))
        self.assertEqual(sc["tracks"], ["fill 18ch"])
        self.assertIn("grid fill 18ch", scene.to_text(sc, "t", "jeff", 0))
        self.assertIn("grid fill 18ch", scene.to_lines(TILES.format(m="18ch")))


if __name__ == "__main__":
    unittest.main()
