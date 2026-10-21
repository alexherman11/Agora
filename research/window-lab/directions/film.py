"""film: a short motion demo of one direction, filmed headless in a copy (a5534, worker-a5534). Nothing on Alex's screen.

    python research/window-lab/directions/film.py <vector|halo|signal> [out dir]

screen.py (through hud_stage.py, --busy) takes frames one after another while the page's own animations run SLOW
(every animation's playbackRate is set to 1/SLOW), then ffmpeg puts the frames together at the rate that gives back
real time, so a 520 ms glide is seen as it is. The story: the home base at rest; a working commission is set ready
and its card glides into a Ready lane that opens for it (a desk line in the copy); a waiting item opens in place; the Board opens in the middle.
Frame times come from the clock, so the film's speed is approximate (said in its name: approx).
"""
import pathlib
import shutil
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
STAGE = HERE.parent / "hud_stage.py"
FFMPEG = ("C:/Users/Alex/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/"
          "ffmpeg-8.1.1-full_build/bin/ffmpeg.exe")
SLOW = 6
CARD = "a5534"          # a commission working in the copy (this one); the story sets it ready, so it glides to Ready
WAIT = "a5441/now/a5431/head"
PIN = "lens:home-viewer/viewer/mine/a5482/pins/f155"
D = {
    "vector": {"waiting": "home/body/left/waiting/lens:waiting-on-me/waiting/mine/", "viewer": "home/body/middle/",
               "before": ["scroll", "home/body/left", "560"], "after": ["scroll", "home/body/left", "-560"]},
    "halo": {"waiting": "home/body/orbit/waiting/lens:waiting-on-me/waiting/mine/", "viewer": "home/body/stage/",
             "before": ["click", "home/body/orbit/board/handle"], "after": ["click", "home/body/orbit/waiting/handle"]},
    "signal": {"waiting": "home/body/rack/waiting/lens:waiting-on-me/waiting/mine/", "viewer": "home/body/stage/",
               "before": [], "after": []},
}
SLOWJS = ("(() => { window.__slow = setInterval(() => document.getAnimations().forEach(a => a.playbackRate = 1 / %d), 15);"
          " return 'slow'; })()" % SLOW)


def main():
    n = sys.argv[1]
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("C:/Projects/Agora4/research/window-lab/demos/a5534")
    frames = out / f"frames-{n}"
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir(parents=True)
    k = [0]

    def shots(count):
        s = []
        for _ in range(count):
            k[0] += 1
            s += ["shot", str(frames / f"f{k[0]:04d}.png")]
        return s

    d = D[n]
    steps = ["wait", "2500", "js", SLOWJS] + d["before"] + ["wait", "600"] + shots(14)
    steps += ["desk", f"look {CARD}; do prop {CARD} commission=ready"] + shots(40)
    steps += d["after"] + ["wait", "300", "click", d["waiting"] + WAIT] + shots(30)
    steps += ["click", d["viewer"] + PIN] + shots(24)
    t0 = time.time()
    r = subprocess.run([sys.executable, str(STAGE), "--busy", "frontier-try", "--as", "alex", "--lens",
                        f"direction-{n}-base", "--size", "1920x1080"] + steps, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    took = time.time() - t0
    print("\n".join(l for l in (r.stdout + r.stderr).splitlines() if not l.startswith("shot:"))[-2500:])
    got = sorted(frames.glob("f*.png"))
    # the frames span the run less its start (about 12 s to start the copy and wait); at SLOW, each real second of the
    # page is SLOW seconds of the clock
    span = max(1.0, took - 12.0)
    fps = max(2.0, min(30.0, len(got) / (span / SLOW)))
    film = out / f"{n}-motion-approx.mp4"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-framerate", f"{fps:.2f}", "-i", str(frames / "f%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-vf", "scale=1920:-2", str(film)], check=True)
    print(f"film: {film} ({len(got)} frames, {took:.0f} s of clock, {fps:.1f} fps)")


if __name__ == "__main__":
    main()
