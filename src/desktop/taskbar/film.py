"""film (a6271): the one bar at the foot of the home base, filmed headless in a copy. Nothing on Alex's screen.

    python src/desktop/taskbar/film.py [out.mp4]

Run apply.py try first (the bar in frontier-try; a landing recopies it). The story, as Alex at his 3840x2160 at 150 %:
the home base at rest with the bar along its foot; the pointer rests on three icons in turn (an app, a panel put away, a
widget) and each says what it is; he presses the board's icon and the board comes back into its column; the pointer
rests on it again and it says it is out. A drawn ring shows where the pointer is (headless Chrome draws none). Each frame
is a screen.py shot; between the first and last (the whole screen) it is the middle of the screen's foot at its own
pixels, where the bar and its tips are; ffmpeg
holds each for its own time (the story's pace, not measured times). Writes <out>.mp4 and keeps the frames beside it.
"""
import pathlib
import subprocess
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
LAB = HERE.parents[1] / "text-desk" / "notation"
FFMPEG = ("C:/Users/Alex/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/"
          "ffmpeg-8.1.1-full_build/bin/ffmpeg.exe")
BAR = "home/dock/lens:home-dock/foot/bar/a5482"
POINTER = ("(() => {{ let p = document.getElementById('fake-pointer'); if (!p) {{ p = document.createElement('div');"
           " p.id = 'fake-pointer'; p.style.cssText = 'position:fixed;z-index:99;width:16px;height:16px;border-radius:50%;"
           "border:2px solid #fff;background:#ffffff40;pointer-events:none;transform:translate(-50%,-50%)';"
           " document.body.append(p); }} const t = document.querySelector('[data-key=\"{0}\"]'); if (!t) return 'none';"
           " const r = t.getBoundingClientRect(); p.style.left = (r.left + r.width / 2) + 'px'; p.style.top = (r.top + r.height / 2) + 'px';"
           " return 'at ' + Math.round(r.left) + ',' + Math.round(r.top); }})()")


def main():
    out = pathlib.Path(next((x for x in sys.argv[1:] if x.endswith(".mp4")),
                            "C:/Projects/Agora4/src/desktop/demos/a6271/bar.mp4"))
    frames = out.with_suffix("")
    frames.mkdir(parents=True, exist_ok=True)
    beats = [  # (name, part the pointer rests on or None, press it?, seconds held)
        ("rest", None, False, 2.5),
        ("conversation", f"{BAR}/apps/f5565/a5571/view", False, 2.5),
        ("board-away", f"{BAR}/panels/f5664/a5674", False, 2.5),
        ("notices", f"{BAR}/widgets/a5715", False, 2.5),
        ("board-pressed", f"{BAR}/panels/f5664/a5674", True, 1.5),
        ("board-out", f"{BAR}/panels/f5664/a5674", False, 3.0),
    ]
    steps = ["js", "document.body.style.background='#1a1d24'"]
    for name, part, press, _ in beats:
        if part:
            steps += ["hover", part, "js", POINTER.format(part)]
        if press:
            steps += ["click", part, "wait", "1500", "hover", part, "wait", "600"]
        steps += ["shot", str(frames / f"{name}.png")]
    subprocess.run([sys.executable, str(LAB / "screen.py"), "frontier-try", "--as", "alex", "--lens", "home-base",
                    "--size", "2560x1440", "--scale", "1.5", *steps], check=True)
    # the bar's beats cropped to the screen's lower half (the bar and what it restores), the first and last whole
    lst = []
    for i, (name, _, _, hold) in enumerate(beats):
        im = Image.open(frames / f"{name}.png").convert("RGB")
        if 0 < i < len(beats) - 1:          # the bar and its tips at the screen's own pixels: the middle of the foot
            im = im.crop((960, 1080, 2880, 2160))
        p = frames / f"{i:02d}-{name}.png"
        im.resize((1920, 1080)).save(p)
        lst.append(f"file '{p.as_posix()}'\nduration {hold}")
    lst.append(f"file '{(frames / f'{len(beats) - 1:02d}-{beats[-1][0]}.png').as_posix()}'")
    (frames / "list.txt").write_text("\n".join(lst) + "\n", encoding="utf-8")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(frames / "list.txt"),
                    "-vf", "fps=30,format=yuv420p", str(out)], check=True)
    print(f"film: {out}")


if __name__ == "__main__":
    main()
