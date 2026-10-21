"""A short film of the map for Alex and the leads, made on the hidden desktop under the guard (nothing on his screen).

  python research/map-lab/ground/demo.py     -> research/window-lab/demos/map-ground-a7946.mp4 (main checkout) and -last.png

The stand-in host holding the isolated frame at 1280x720: turn the view with the mouse, curve on and off, show which
heights are estimated, drag a pin (the host accepts the move and redraws), and the flat plan without 3D.
"""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import measure as m  # noqa: E402

sw = m.sw


class Reel:
    def __init__(self, c):
        self.c, self.n = c, 0
        self.dir = HERE / "results" / f"reel-{os.getpid()}"
        self.dir.mkdir(parents=True)

    def shot(self, hold=1):
        im = sw.page_shot(self.c).convert("RGB")
        for _ in range(hold):
            im.save(self.dir / f"{self.n:05d}.png")
            self.n += 1

    def make(self, out):
        subprocess.run([sw.screen_tools.ffmpeg(), "-y", "-loglevel", "error", "-framerate", "10", "-i",
                        str(self.dir / "%05d.png"), "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264",
                        "-preset", "veryfast", "-pix_fmt", "yuv420p", str(out)], check=True)
        shutil.copy(self.dir / f"{self.n - 1:05d}.png", out.with_name(out.stem + "-last.png"))
        shutil.rmtree(self.dir, ignore_errors=True)


def main():
    srv, base = m.serve()
    name = f"mapdemo-{os.getpid()}"
    out = sw.screen_tools.place("map-ground-a7946.mp4")
    guard = sw.Guard(name, "Map: Bloomsbury")
    try:
        with guard:
            st = sw.open_edge(name, base + "/host.html", size="1280x720")
            c = sw.Cdp(st["port"])
            try:
                f = m.FrameCdp(st["port"])
                f.js("new Promise(r => { const t = () => __map.drawn().pins.length ? r() : setTimeout(t, 50); t(); })")
                reel = Reel(c)
                reel.shot(20)
                box = lambda sel: f.js(f"(() => {{ const b = document.querySelector('{sel}').getBoundingClientRect(); "
                                       "return [b.x + b.width / 2, b.y + b.height / 2]; })()")
                click = lambda xy: (m.mouse(c, "mouseMoved", *xy), m.mouse(c, "mousePressed", *xy, 1, "left"),
                                    m.mouse(c, "mouseReleased", *xy, 0, "left"))

                def orbit(dx, dy, steps=24):
                    x, y = 420, 520
                    m.mouse(c, "mouseMoved", x, y)
                    m.mouse(c, "mousePressed", x, y, 1, "left")
                    for k in range(1, steps + 1):
                        m.mouse(c, "mouseMoved", x + dx * k / steps, y + dy * k / steps, 1, "left")
                        if k % 2 == 0:
                            reel.shot()
                    m.mouse(c, "mouseReleased", x + dx, y + dy, 0, "left")
                orbit(260, -40)
                reel.shot(8)
                click(box("#curve"))
                time.sleep(0.2)
                reel.shot(20)
                orbit(-260, 40)
                reel.shot(10)
                click(box("#curve"))
                click(box("#mark"))
                time.sleep(0.2)
                reel.shot(20)
                click(box("#mark"))
                tip = f.js("(() => { const p = __map.drawn().pins[1]; return __map.project(p.lat, p.lon, 0); })()")
                x, y = tip[0], tip[1] - 14
                m.mouse(c, "mouseMoved", x, y)
                m.mouse(c, "mousePressed", x, y, 1, "left")
                for k in range(1, 13):
                    m.mouse(c, "mouseMoved", x + 6 * k, y + 2 * k, 1, "left")
                    reel.shot()
                m.mouse(c, "mouseReleased", x + 72, y + 24, 0, "left")
                time.sleep(0.4)
                reel.shot(20)
                click(box("#flat2d"))
                time.sleep(0.3)
                reel.shot(25)
                reel.make(out)
                f.close()
            finally:
                c.close()
                sw.close(name, quiet=True)
        print("wrote", out.as_posix())
        print(guard.verdict()[1])
    finally:
        srv.shutdown()


if __name__ == "__main__":
    main()
