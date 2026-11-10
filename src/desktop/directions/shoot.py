"""shoot: the closed, busy and expanded shots of each direction at 1920x1080 and 3840x2160 (a5534, worker-a5534).

    python src/desktop/directions/shoot.py [out dir] [direction ...]

Each run is hud_stage.py (screen.py in a copy of frontier-try, with a stand-in frost and windows):
  closed    nothing open, the house quiet
  expanded  then: a waiting item with a demo opened in place (a5431), and the Board opened in the middle (pin f155)
  busy      a separate run with --busy (JEFF thinking, two residents and three builders at work), and the panel that
            shows the board brought into view
"""
import concurrent.futures as cf
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
STAGE = HERE.parent / "hud_stage.py"
WAIT = "a5441/now/a5431/head"
PIN = "lens:home-viewer/viewer/mine/a5482/pins/f155"
D = {
    "vector": {"waiting": "home/body/left/waiting/lens:waiting-on-me/waiting/mine/", "viewer": "home/body/middle/",
               "busy": ["scroll", "home/body/left", "640"]},
    "halo": {"waiting": "home/body/orbit/waiting/lens:waiting-on-me/waiting/mine/", "viewer": "home/body/stage/",
             "busy": ["click", "home/body/orbit/board/handle"]},
    "signal": {"waiting": "home/body/rack/waiting/lens:waiting-on-me/waiting/mine/", "viewer": "home/body/stage/",
               "busy": []},
}
SIZES = {"1080": "1920x1080", "2160": "3840x2160"}


def runs(out, names):
    for n in names:
        d = D[n]
        for tag, size in SIZES.items():
            base = [sys.executable, str(STAGE)]
            common = ["frontier-try", "--as", "alex", "--lens", f"direction-{n}-base", "--size", size, "wait", "2500"]
            yield base + common + ["shot", str(out / f"{n}-closed-{tag}.png"),
                                   "click", d["waiting"] + WAIT, "wait", "1500", "click", d["viewer"] + PIN, "wait", "2500",
                                   "shot", str(out / f"{n}-expanded-{tag}.png")]
            yield base + ["--busy"] + common + d["busy"] + ["wait", "1800", "shot", str(out / f"{n}-busy-{tag}.png")]


def go(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return " ".join(cmd[-1:]) + "\n" + (r.stdout + r.stderr).strip()


def main():
    a = sys.argv[1:]
    out = pathlib.Path(a[0]) if a and not a[0] in D else pathlib.Path("C:/Projects/Agora4/src/desktop/demos/a5534")
    names = [x for x in a if x in D] or list(D)
    out.mkdir(parents=True, exist_ok=True)
    with cf.ThreadPoolExecutor(3) as ex:
        for r in ex.map(go, list(runs(out, names))):
            print(r, flush=True)


if __name__ == "__main__":
    main()
