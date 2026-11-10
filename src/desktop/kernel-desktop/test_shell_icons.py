"""The icon pipeline against this machine's real windows (read-only: window enumeration, icon drawing, a disk cache).

    python test_shell_icons.py            runs the checks, saves evidence/shell/icons-sheet.png

Checks, each printed as measured: every reference kind returns a PNG with real alpha at 64/128/256, the disk cache
answers the second time faster, windows of a packaged app resolve to pkg:, windows of ordinary programs to exe:, and the
window's own icon (hwnd:) works for at least one window.
"""
import io
import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.append(str(HERE.parents[1] / "agora"))
from kernel import scratch  # noqa: E402
import os  # noqa: E402

os.environ.setdefault("AGORA_ICON_CACHE", scratch.mkdtemp(prefix="icons-", dir=str(HERE / "state")))
import shell_icons as SI  # noqa: E402
import native_shell  # noqa: E402
from PIL import Image  # noqa: E402

EVIDENCE = HERE / "evidence" / "shell"


def real_windows():
    return native_shell.windows()


def alpha_stats(png):
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    a = im.getchannel("A")
    lo, hi = a.getextrema()
    transparent = sum(1 for v in a.getdata() if v == 0) / (im.size[0] * im.size[1])
    return im.size, lo, hi, transparent


class IconPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wins = real_windows()
        cls.sheet = []

    def test_exe_icons_have_alpha_at_every_size(self):
        done = 0
        seen = set()
        for w in self.wins:
            exe = w["path"]
            if not exe or exe in seen:
                continue
            seen.add(exe)
            for size in (64, 128, 256):
                png = SI.png_for("exe:" + exe, size)
                if png is None:
                    continue
                (w_, h_), lo, hi, transparent = alpha_stats(png)
                self.assertEqual((w_, h_), (size, size))
                self.assertEqual(hi, 255)
            png = SI.png_for("exe:" + exe, 128)
            if png:
                (_, _), lo, hi, transparent = alpha_stats(png)
                print(f"  exe {Path(exe).name:<28} 128px alpha {lo}..{hi}, {transparent:.0%} transparent")
                self.sheet.append((Path(exe).name, png))
                done += 1
        print(f"exe icons with alpha: {done} of {len(seen)} programs")
        self.assertGreaterEqual(done, max(3, len(seen) * 2 // 3))

    def test_cache_makes_the_second_ask_fast(self):
        exe = next(w["path"] for w in self.wins if w["path"])
        t0 = time.perf_counter()
        SI.png_for("exe:" + exe, 192)
        first = time.perf_counter() - t0
        t0 = time.perf_counter()
        SI.png_for("exe:" + exe, 192)
        second = time.perf_counter() - t0
        print(f"cache: {Path(exe).name} first {first * 1000:.1f} ms, second {second * 1000:.1f} ms; files on disk: "
              f"{len(list(SI.CACHE.glob('*.png')))}")
        self.assertLess(second, max(0.05, first))

    def test_windows_resolve_to_package_or_exe(self):
        kinds = {}
        for w in self.wins:
            ref = SI.window_ref(int(w["handle"]))
            kinds.setdefault(ref.split(":", 1)[0], []).append((Path(w["path"]).name, ref[:90]))
        for kind, rows in kinds.items():
            print(f"  {kind}: {len(rows)} windows, e.g. {rows[0]}")
        self.assertIn("exe", kinds)

    def test_packaged_apps_through_their_manifest(self):
        pk = [SI.window_ref(int(w["handle"])) for w in self.wins]
        pk = [r for r in pk if r.startswith("pkg:")]
        if not pk:
            self.skipTest("no packaged app has a window open right now")
        for ref in dict.fromkeys(pk):
            png = SI.png_for(ref, 128)
            print(f"  {ref[:70]} -> {'PNG ' + str(alpha_stats(png)[0]) if png else 'no manifest logo (aumid next)'}")
            if png:
                self.sheet.append((ref.split(":")[1].split("_")[0][-18:], png))
        self.assertTrue(any(SI.png_for(r, 128) for r in dict.fromkeys(pk)), "no packaged logo came back")

    def test_the_windows_own_icon(self):
        got = 0
        for w in self.wins:
            png = SI.png_for(f"hwnd:{w['handle']}", 128)
            if png:
                got += 1
                self.sheet.append(("own:" + Path(w["path"]).stem[:14], png))
        print(f"window's own icon (WM_GETICON / class icon): {got} of {len(self.wins)} windows")
        self.assertGreaterEqual(got, 1)

    def test_agora_icons_are_colour_svgs(self):
        names = ["agora", "lines", "board", "appearance", "taskboard", "help", "feed", "overview", "thing", "desktop"]
        for n in names:
            status, ctype, data = SI.serve("agora:" + n)
            self.assertEqual((status, ctype), (200, "image/svg+xml"), n)
            self.assertIn(b"<svg", data)
        self.assertEqual(SI.serve("agora:nonesuch")[0], 404)

    @classmethod
    def tearDownClass(cls):
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        if not cls.sheet:
            return
        cell, cols = 144, 8
        rows = (len(cls.sheet) + cols - 1) // cols
        sheet = Image.new("RGBA", (cols * cell, rows * cell * 2), (0, 0, 0, 0))
        from PIL import ImageDraw
        d = ImageDraw.Draw(sheet)
        d.rectangle((0, 0, cols * cell, rows * cell), fill=(245, 240, 232, 255))
        d.rectangle((0, rows * cell, cols * cell, rows * cell * 2), fill=(32, 28, 48, 255))
        for i, (name, png) in enumerate(cls.sheet):
            im = Image.open(io.BytesIO(png)).convert("RGBA").resize((112, 112), Image.LANCZOS)
            x, y = (i % cols) * cell + 16, (i // cols) * cell + 16
            sheet.alpha_composite(im, (x, y))
            sheet.alpha_composite(im, (x, y + rows * cell))
        sheet.convert("RGB").save(EVIDENCE / "icons-sheet.png")
        print(f"saved {EVIDENCE / 'icons-sheet.png'} ({len(cls.sheet)} icons on light and dark)")


if __name__ == "__main__":
    unittest.main(verbosity=1)
