"""film: the Scripts demo (a6249), filmed headless in a copy of a world at Alex's size. Nothing on his screen.

    python src/desktop/scripts/film.py [world] [out dir]     (world: frontier-try, after apply.py's lines)

The story: the Scripts page as Alex would open it (names and sentences, no paths), the Rocket League timer's two
settings, the script itself folded at the foot; BEFORE and AFTER of its text (the real diff of the two files here);
the weekend rule dry-run for all seven days (the real output of the new script's -DryRun, which watches and closes
nothing); a setting changed on the page (in the copy: on the live world the house then writes it to the file).
"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "writing"))
from film import Reel, FFMPEG, caption  # noqa: E402

ORIGINAL = HERE / "originals" / "RocketLeagueTimer.2026-10-17.original.ps1"
NEW = HERE / "RocketLeagueTimer.ps1"
DARK = ["js", "document.body.style.background='#0E1211'"]


def board(title, text):
    """A panel over the page holding real output (a diff, a dry run), as words; empty title takes it away."""
    import json
    css = ("position:fixed;left:6%;right:6%;top:7%;bottom:14%;background:#0b0e0d;color:#e9eeea;border:1px solid #2a312e;"
           "border-radius:16px;padding:28px 36px;z-index:9998;overflow:hidden;font:12px/1.35 'Cascadia Code',monospace;"
           "white-space:pre")
    lines = []
    for line in text.splitlines():
        colour = "#8DCDB4" if line.startswith("+") else "#F28B8B" if line.startswith("-") else "#9aa5a0"
        lines.append(f"<span style='color:{colour}'>{line.replace('&', '&amp;').replace('<', '&lt;')}</span>")
    html = (f"<div style=\"font:600 24px system-ui;color:#fff;margin-bottom:16px;white-space:normal\">{title}</div>"
            + "\n".join(lines))
    js = ("(() => { let b = document.getElementById('film-board'); if (!b) { b = document.createElement('div');"
          " b.id = 'film-board'; document.body.appendChild(b); } b.style.cssText = %s; b.innerHTML = %s; b.hidden = !%s;"
          " return 1; })()" % (json.dumps(css), json.dumps(html), json.dumps(bool(title))))
    return ["js", js]


def diff():
    p = subprocess.run(["git", "diff", "--no-index", "-U1", str(ORIGINAL), str(NEW)], capture_output=True, text=True,
                       encoding="utf-8")
    return "\n".join(l for l in p.stdout.splitlines()[4:])          # past git's own header


def dry():
    p = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                        str(NEW), "-DryRun", "-Clock", "2026-10-12", "-SettingsFile", str(HERE / "no-such.json")],
                       capture_output=True, text=True, timeout=60)
    return p.stdout.rstrip()


def main():
    world = sys.argv[1] if len(sys.argv) > 1 else "frontier-try"
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path(
        "C:/Projects/Agora4/src/desktop/demos/a6249")
    (out / "frames").mkdir(parents=True, exist_ok=True)
    card = "scripts/list/" + (sys.argv[3] if len(sys.argv) > 3 else "a6263")
    reel = Reel(out)
    reel.do(*DARK)
    reel.say("Scripts: Alex's own scripts, in the world. Names and plain sentences; no file paths", secs=3.5)
    reel.say("The Rocket League timer: what it does, how it runs, and why it is never run from here", secs=3.5)
    reel.say("Its two numbers are settings now: weekdays 30 minutes, Saturday and Sunday 60", secs=3.5)
    reel.do("click", f"{card}/words/handle")
    reel.say("The script itself, folded at the foot, editable: an edit is checked and written to the file", secs=3.5)
    reel.do(*caption(""), *board("Before and after: the timer's text (green added, red taken away)", diff()), secs=9)
    reel.do(*board("The weekend rule, dry run (-DryRun watches and closes nothing): one week from a Monday", dry()),
            secs=5)
    reel.do(*board("", ""), "click", f"{card}/words/handle")
    num = f"{card}/panel/lens:rocket-settings/settings/on/one/{card.rsplit('/', 1)[1]}/weekend/n"
    reel.say("A setting changed here: Saturday and Sunday to 75", secs=1.5)
    reel.do("click", num, "key", "Ctrl+a", "type", "75", "key", "Enter", "wait", "600", secs=2.5)
    reel.say("Saved on the note; on the live world the house writes it to the timer's settings file, keeping the old one",
             secs=4)
    reel.run(world, "scripts-page")
    lst = out / "frames.txt"
    lst.write_text("".join(f"file '{f.as_posix()}'\nduration {s}\n" for f, s in reel.frames)
                   + f"file '{reel.frames[-1][0].as_posix()}'\n", encoding="utf-8")
    mp4 = out / "scripts-demo.mp4"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf",
                    "scale=1920:-2:flags=lanczos,format=yuv420p", "-r", "30", "-c:v", "libx264", "-crf", "18", str(mp4)],
                   check=True)
    print(f"film: {mp4} ({len(reel.frames)} frames, {sum(s for _, s in reel.frames):.0f} s)")


if __name__ == "__main__":
    main()
