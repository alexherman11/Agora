"""motion_check: does anything move in a recording, and where? (a5816, Alex 16 Oct: 'the hud keeps animating over
and over again'). A video can't be read; this reads it for you.

    python src/desktop/motion_check.py <video.mp4> [--fps 5] [--every]

The video is cut into frames (--fps a second), each compared with the one before on a 16 x 9 grid of cells. A cell
that changes in one frame and then stands still is a state change (a line appeared, a panel reflowed). A cell that
keeps changing for 3 frames or more in a row is MOTION: an animation, typing, a pointer, a playing video. Each run of
motion is printed with its time, its cells and its box in the video's pixels, so you can open the frame and see what it
was (the frames are kept; their folder is printed). --every prints every frame's change as well.
A bare file name is looked for in src/desktop/demos/ of the main checkout, where screen_tools.py records.
"""
import argparse
import glob
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops

sys.path.insert(0, str(Path(__file__).resolve().parent))
from screen_tools import ffmpeg  # noqa: E402

GX, GY = 16, 9
THRESHOLD = 24      # a pixel whose grey moved by more than this changed (video noise stays under it)
MIN_PIXELS = 30     # a cell with fewer changed pixels than this stood still
RUN = 3             # this many changed frames in a row is motion


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("video")
    ap.add_argument("--fps", default="5")
    ap.add_argument("--every", action="store_true")
    a = ap.parse_args()
    src = Path(a.video)
    if not src.exists() and src.parent == Path("."):
        src = Path("C:/Projects/Agora4/src/desktop/demos") / src
    if not src.exists():
        sys.exit(f"no such video: {a.video}")
    fps = float(a.fps)
    d = tempfile.mkdtemp(prefix="motion-")
    subprocess.run([ffmpeg(), "-loglevel", "error", "-i", str(src), "-vf", f"fps={a.fps}", os.path.join(d, "f%04d.png")], check=True)
    frames = sorted(glob.glob(os.path.join(d, "f*.png")))
    if len(frames) < 2:
        sys.exit("fewer than two frames")
    prev = Image.open(frames[0]).convert("L")
    w, h = prev.size
    cell = lambda x, y: (x * w // GX, y * h // GY, (x + 1) * w // GX, (y + 1) * h // GY)
    run = {}            # cell -> (first frame of its current run, run length)
    motions = []        # (start s, end s, cells, box)
    open_runs = {}
    states = 0

    def close(c, upto):
        start, n = run.pop(c)
        if n >= RUN:
            open_runs.setdefault((start, upto), set()).add(c)

    for i, f in enumerate(frames[1:], 1):
        im = Image.open(f).convert("L")
        diff = ImageChops.difference(im, prev).point(lambda v: 255 if v > THRESHOLD else 0)
        changed = set()
        if diff.getbbox():
            for y in range(GY):
                for x in range(GX):
                    hist = diff.crop(cell(x, y)).histogram()
                    if hist[255] >= MIN_PIXELS:
                        changed.add((x, y))
        if a.every and changed:
            print(f"{i / fps:6.1f}s  {len(changed):3d} cells  box={diff.getbbox()}")
        for c in changed:
            s, n = run.get(c, (i, 0))
            run[c] = (s, n + 1)
        for c in [c for c in run if c not in changed]:
            if run[c][1] == 1:
                states += 1
            close(c, i)
        prev = im
    for c in list(run):
        close(c, len(frames))
    for (start, end), cells in sorted(open_runs.items()):
        xs = [c[0] for c in cells]; ys = [c[1] for c in cells]
        box = (min(xs) * w // GX, min(ys) * h // GY, (max(xs) + 1) * w // GX, (max(ys) + 1) * h // GY)
        motions.append((start, end, len(cells), box))
    print(f"{src.name}: {len(frames)} frames over {len(frames) / fps:.1f} s at {a.fps} fps, {w}x{h}")
    print(f"state changes (a cell changed in one frame, then stood still): {states}")
    if not motions:
        print("motion: none (no cell changed in 3 frames running)")
    for s, e, n, box in motions:
        print(f"motion {s / fps:6.1f}s .. {e / fps:6.1f}s  {n:3d} cells  box={box}  (frames f{s:04d}..f{e:04d})")
    print("frames in", d)


if __name__ == "__main__":
    main()
