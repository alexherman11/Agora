"""wallpaper.py's off switch, against a pretend Windows (never the real wallpaper): the old wallpaper is saved once, a
second apply or a theme change cannot lose it, restore puts it back, and a Spotlight picture survives Windows rotating
its cache file away."""
import json
import tempfile
import unittest
from pathlib import Path

import wallpaper


class PretendWindows:
    def __init__(self, path, background_type=0):
        self.now = {"path": str(path), "style": "10", "tile": "0", "background_type": background_type}
        self.sets = []

    def current(self):
        return dict(self.now)

    def set(self, path, style="10", tile="0"):
        self.sets.append(str(path))
        self.now.update(path=str(path), style=str(style), tile=str(tile), background_type=0)


class WallpaperOffSwitch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.saved = (wallpaper.STATE, wallpaper.BEFORE, wallpaper.OFF, wallpaper.current, wallpaper._set)
        wallpaper.STATE = root / "wallpaper"
        wallpaper.BEFORE = wallpaper.STATE / "before.json"
        wallpaper.OFF = wallpaper.STATE / "off"
        self.spot = root / "iris" / "1343.jpg"
        self.spot.parent.mkdir()
        self.spot.write_bytes(b"spotlight picture")
        self.win = PretendWindows(self.spot, wallpaper.SPOTLIGHT)
        wallpaper.current, wallpaper._set = self.win.current, self.win.set
        wallpaper.STATE.mkdir()

    def tearDown(self):
        (wallpaper.STATE, wallpaper.BEFORE, wallpaper.OFF, wallpaper.current, wallpaper._set) = self.saved
        self.tmp.cleanup()

    def theme(self, h):
        png = wallpaper.STATE / f"agora-{h}-3840x2160.png"
        png.write_bytes(b"png " + h.encode())
        return png

    def test_two_themes_then_restore_brings_the_spotlight_picture_back_after_windows_rotated_it(self):
        self.assertEqual(wallpaper.apply(self.theme("aaa")), "set")
        self.assertEqual(wallpaper.apply(self.theme("aaa")), "already")
        second = self.theme("bbb")
        self.assertEqual(wallpaper.apply(second), "set")
        self.assertFalse((wallpaper.STATE / "agora-aaa-3840x2160.png").exists(), "the old theme's picture is pruned")
        saved = json.loads(wallpaper.BEFORE.read_text(encoding="utf-8"))
        self.assertEqual(saved["path"], str(self.spot), "the second apply did not overwrite the original")
        self.spot.unlink()                                   # Windows rotates its Spotlight cache
        said = wallpaper.restore()
        self.assertIn("Spotlight", said)
        self.assertEqual(Path(self.win.now["path"]).read_bytes(), b"spotlight picture")
        self.assertFalse(wallpaper.ours(self.win.now["path"]), "the saved copy is not taken for Agora's picture")
        self.assertFalse(wallpaper.BEFORE.exists())
        self.assertIn("nothing to put back", wallpaper.restore())

    def test_a_restart_with_agoras_picture_up_and_the_save_lost_never_saves_agoras_picture_as_the_original(self):
        png = self.theme("ccc")
        self.win.now["path"] = str(png)
        self.assertIsNone(wallpaper.save_before())
        self.assertFalse(wallpaper.BEFORE.exists())

    def test_keeper_stays_off_after_a_command_line_restore(self):
        wallpaper.apply(self.theme("ddd"))
        wallpaper.OFF.write_text("off")
        wallpaper.restore()
        k = wallpaper.Keeper.__new__(wallpaper.Keeper)
        k.on, k.shown, k.said, k.log = True, None, "", lambda s: None
        k.step()                                             # would render and apply if it ignored the mark
        self.assertEqual(Path(self.win.now["path"]).read_bytes(), b"spotlight picture")
        self.assertIn("wallpaper.py on", k.said)


if __name__ == "__main__":
    unittest.main()
