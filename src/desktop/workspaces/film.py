"""film (a6427): workspaces, filmed headless in a copy of frontier-try at Alex's 2560x1440 at 150 %. Nothing on his screen.

    python src/desktop/workspaces/film.py [out.mp4]

Run apply.py try first (a landing recopies frontier-try). The story: the home base as Alex has it (default); the pointer
rests on the dock's app-dev icon and it says what it is; he presses it and the whole home base is app dev; JEFF's line
`workspace writing` makes it Writing beside the chat; Alex presses ↶ (back) and app dev returns as it was; JEFF's line
`workspace default` gives him his own arrangement again. Each change is ONE verb call: a caption at the top says which.
A drawn ring shows the pointer (headless Chrome draws none). Each frame is a screen.py shot, held for the story's pace
(not measured times). The dock's icons are aimed at by position: their keys carry the layout's id, which every apply
changes. Writes <out>.mp4 and keeps the frames beside it.
"""
import pathlib
import subprocess
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
LAB = HERE.parents[1] / "text-desk" / "notation"
FFMPEG = ("C:/Users/Alex/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/"
          "ffmpeg-8.1.1-full_build/bin/ffmpeg.exe")
ICON = {name: (16 + 113 * i + 52, 1314) for i, name in enumerate(["default", "app-dev", "writing", "review", "quiet", "play", "back"])}
MARK = ("(() => {{ let p = document.getElementById('fake-pointer'); if (!p) {{ p = document.createElement('div');"
        " p.id = 'fake-pointer'; p.style.cssText = 'position:fixed;z-index:99;width:18px;height:18px;border-radius:50%;"
        "border:2px solid #fff;background:#ffffff40;pointer-events:none;transform:translate(-50%,-50%)';"
        " document.body.append(p); }} p.style.display = '{2}'; p.style.left = '{0}px'; p.style.top = '{1}px'; return 'ok'; }})()")
SAY = ("(() => {{ let c = document.getElementById('film-caption'); if (!c) {{ c = document.createElement('div');"
       " c.id = 'film-caption'; c.style.cssText = 'position:fixed;z-index:98;left:50%;top:6px;transform:translateX(-50%);"
       "padding:6px 16px;border-radius:8px;background:#000c;color:#fff;font:600 16px system-ui;pointer-events:none';"
       " document.body.append(c); }} c.textContent = {0!r}; return 'ok'; }})()")


def main():
    out = pathlib.Path(next((x for x in sys.argv[1:] if x.endswith(".mp4")),
                            "C:/Projects/Agora4/src/desktop/demos/a6427/workspaces.mp4"))
    frames = out.with_suffix("")
    frames.mkdir(parents=True, exist_ok=True)
    beats = [  # (name, caption, pointer at (icon name) or None, act: ("click", icon) | ("desk", line) | None, seconds)
        ("default", "default: the home base as Alex has it", None, None, 3.0),
        ("hover-appdev", "the dock: each workspace an icon, its name on hover", "app-dev", None, 2.5),
        ("appdev", "Alex pressed app dev: one call, workspace app-dev", "app-dev", ("click", "app-dev"), 3.5),
        ("writing", "JEFF's one line: workspace writing", None, ("desk", "workspace writing"), 3.5),
        ("hover-back", "↶ back: the arrangement before the last one", "back", None, 2.5),
        ("back", "Alex pressed back: one call, workspace back", "back", ("click", "back"), 3.5),
        ("default-again", "JEFF's one line: workspace default", None, ("desk", "workspace default"), 3.5),
    ]
    steps = ["js", "document.body.style.background='#1b2230'", "wait", "1200"]
    for name, caption, at, act, _ in beats:
        if act and act[0] == "click":
            steps += ["click", "%d,%d" % ICON[act[1]], "wait", "1800"]
        if act and act[0] == "desk":
            steps += ["desk", act[1], "wait", "1800"]
        if at:
            x, y = ICON[at]
            steps += ["hover", f"{x},{y}", "wait", "500", "js", MARK.format(x, y, "block")]
        else:
            steps += ["js", MARK.format(0, 0, "none")]
        steps += ["js", SAY.format(caption), "shot", str(frames / f"{name}.png")]
    subprocess.run([sys.executable, str(LAB / "screen.py"), "frontier-try", "--as", "alex", "--lens", "home-base",
                    "--size", "2560x1440", "--scale", "1.5", *steps], check=True)
    lst = []
    for i, (name, _, _, _, hold) in enumerate(beats):
        p = frames / f"{i:02d}-{name}.png"
        Image.open(frames / f"{name}.png").convert("RGB").resize((1920, 1080)).save(p)
        lst.append(f"file '{p.as_posix()}'\nduration {hold}")
    lst.append(f"file '{(frames / f'{len(beats) - 1:02d}-{beats[-1][0]}.png').as_posix()}'")
    (frames / "list.txt").write_text("\n".join(lst) + "\n", encoding="utf-8")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(frames / "list.txt"),
                    "-vf", "fps=30,format=yuv420p", str(out)], check=True)
    print(f"film: {out}")


if __name__ == "__main__":
    main()
