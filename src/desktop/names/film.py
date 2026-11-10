"""Names, not ids (a6109): the demo, filmed headless in copies of a world at Alex's size. Nothing on his screen.

    python src/desktop/names/film.py [world] [out dir] [--before <dir with screen-before-*.png>]

Run on a world with apply.py's lines in it (frontier-try after `apply.py lines` + explore.py). The story: BEFORE, the
home base as it was (stills from audit.py --tag before, if given); AFTER, the same screens with names; a name pressed
opens its thing in the viewer, Back returns; an opened waiting item's words name their tasks, notes and comments; the
Writing room's head says 'Agora', not a604. Frames are joined by ffmpeg into names-demo.mp4 (writing/film.py's Reel).
"""
import json
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "writing"))
from film import Reel, FFMPEG  # noqa: E402

DARK = ["js", "document.body.style.background='#15171b'"]


def press(key):
    return ["js", f"window.PRESS={json.dumps(key)}", "js", f"@{HERE / 'press.js'}"]


def name(i):
    return ["js", f"window.NAME={json.dumps(i)}", "js", f"@{HERE / 'click_name.js'}"]


def main(argv):
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d       # noqa: E731
    pos = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or not argv[i - 1].startswith("--"))]
    world = pos[0] if pos else "frontier-try"
    out = pathlib.Path(pos[1] if len(pos) > 1 else "C:/Projects/Agora4/src/desktop/demos/a6109")
    (out / "frames").mkdir(parents=True, exist_ok=True)
    for f in (out / "frames").glob("*.png"):
        f.unlink()
    reel = Reel(out)
    before = opt("--before")
    if before:                                  # stills of the old painter, with their own captions burnt in by audit
        for n, secs in (("home", 4.0), ("waiting", 4.5), ("writing", 3.0)):
            src = pathlib.Path(before) / f"screen-before-{n}.png"
            if src.exists():
                f = out / "frames" / f"{len(reel.frames):04d}.png"
                shutil.copy(src, f)
                reel.frames.append((f, secs))

    reel.do(*DARK, "wait", "1500")
    reel.say("After: every id in words is drawn as the name of what it names", secs=4)
    reel.do(*name("a5534"), "wait", "2000")
    reel.say("One click on a name opens it in the viewer", secs=3.5)
    reel.do(*press(r"rx:lens:home-viewer/viewer/mine/a\d+/bar/back$"), "wait", "2000")
    reel.say("Back returns to what was open", secs=2.5)
    reel.do(*press(r"rx:lens:waiting-on-me/waiting/mine/a\d+/now/a\d+/head$"), "wait", "2000")
    reel.say("An opened item: its tasks, notes, folders, comments and worker are names", secs=4.5)
    reel.do(*name("c4922"), "wait", "2000")
    reel.say("A comment opens the thing it is on", secs=3.5)
    reel.run(world, "home-base")
    reel.do(*DARK, *press("text:Writing room"), "wait", "2500")
    reel.say("The Writing room says its document's name, not its id", secs=3.5)
    reel.run(world, "home-base")

    lst = out / "frames.txt"
    lst.write_text("".join(f"file '{f.as_posix()}'\nduration {s}\n" for f, s in reel.frames) + f"file '{reel.frames[-1][0].as_posix()}'\n", encoding="utf-8")
    import subprocess
    mp4 = out / "names-demo.mp4"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf", "scale=1920:-2,format=yuv420p", "-r", "30", str(mp4)], check=True)
    shutil.copy(reel.frames[-1][0], out / "names-demo-last.png")
    print(f"film: {len(reel.frames)} frames, {sum(s for _, s in reel.frames):.1f} s -> {mp4}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
