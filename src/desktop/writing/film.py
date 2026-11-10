"""film: the Writing app's demo (a5820), filmed headless in copies of a world at Alex's size. Nothing on his screen.

    python src/desktop/writing/film.py [world] [out dir]       (world: frontier-try, after apply.py try)

screen.py drives a copy as alex at 2560x1440 (his home base's page size) and takes a frame after each step; ffmpeg joins
the frames, each held for its own time, into writing-demo.mp4. A caption at the foot says what is happening.
The story: BEFORE, the dock's Writing room as it opened (a board of old editor cards) and a one-text document shown as
raw Markdown; AFTER, the Writing app: a page drawn as Markdown, a new page written live (marks shown on the line being
written, drawn when the caret leaves), a task ticked, a table, a [[link]] chosen from the documents, a live embed,
the source one key away (Ctrl+E), the link followed and the page found in the other document's live 'Mentioned in'.
The part keys name the ids apply.py try made in frontier-try on 16 Oct (writer a5903, first page a5905, Notes f5901, the
new page a5907); after a recopy, run apply.py try again and change those ids to the ones its receipt prints.
"""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
LAB = HERE.parents[1] / "text-desk" / "notation"
SCREEN = LAB / "screen.py"
FFMPEG = ("C:/Users/Alex/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/"
          "ffmpeg-8.1.1-full_build/bin/ffmpeg.exe")
SIZE = ["--size", "2560x1440"]
WRITER = "Alex's writing (what the Writing app has open)"


def caption(words):
    css = ("position:fixed;left:50%;bottom:36px;transform:translateX(-50%);background:rgba(8,10,12,.86);color:#fff;"
           "font:600 26px Inter,system-ui,sans-serif;padding:14px 28px;border-radius:14px;z-index:9999;pointer-events:none;"
           "box-shadow:0 10px 40px rgba(0,0,0,.4);white-space:nowrap")
    js = ("(() => { let c = document.getElementById('film-cap'); if (!c) { c = document.createElement('div'); c.id = 'film-cap';"
          " document.body.appendChild(c); } c.style.cssText = %s; c.textContent = %s; c.hidden = !%s; return 1; })()"
          % (json.dumps(css), json.dumps(words), json.dumps(bool(words))))
    return ["js", js]


class Reel:
    def __init__(self, out):
        self.out, self.frames, self.steps = out, [], []

    def shot(self, secs):
        f = self.out / "frames" / f"{len(self.frames):04d}.png"
        self.frames.append((f, secs))
        self.steps += ["shot", str(f)]

    def do(self, *steps, secs=None):
        self.steps += list(steps)
        if secs:
            self.shot(secs)

    def say(self, words, secs=None):
        self.do(*caption(words), secs=secs)

    def type(self, words, every=3, secs=0.09):
        """Typed a few characters at a time, a frame after each, so the marks are seen appearing on the line."""
        for i in range(0, len(words), every):
            self.do("type", words[i:i + every], secs=secs)

    def run(self, world, lens):
        cmd = [sys.executable, str(SCREEN), world, "--as", "alex", "--lens", lens, *SIZE, *self.steps]
        r = subprocess.run(cmd, cwd=LAB, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode:
            print(r.stdout[-3000:], r.stderr[-3000:])
            raise SystemExit("film: a screen.py run failed")
        self.steps = []


def main():
    world = sys.argv[1] if len(sys.argv) > 1 else "frontier-try"
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("C:/Projects/Agora4/src/desktop/demos/a5820")
    (out / "frames").mkdir(parents=True, exist_ok=True)
    for f in (out / "frames").glob("*.png"):
        f.unlink()
    reel = Reel(out)

    # BEFORE 1: the dock's Writing room, as it opened in the home base (its viewer on the room f3402)
    reel.do("js", "document.body.style.background='#15171b'", "desk", "look a5482", "desk", "do prop a5482 viewing=f3402", "wait", "1500")
    reel.say("Before: the Writing room opened as a board of old editor cards", secs=3.5)
    reel.run(world, "home-base")
    # BEFORE 2: a one-text document in the old writing window, its Markdown printed raw
    reel.do("desk", "look a4035", "desk", "do prop a4035 reviewing=a4865", "wait", "1500")
    reel.say("Before: a Markdown document printed raw, ## and - as typed", secs=3.5)
    reel.run(world, "design-review")

    # AFTER: the Writing app
    w = WRITER
    reel.do("wait", "800")
    reel.say("After: the Writing app. A page is drawn as Markdown", secs=3.5)
    reel.say("Live on the right: its outline, what mentions it, its props", secs=3)
    reel.do("click", ".md-embed", "wait", "1200")
    reel.say("An embed is the thing itself: here the commission that made this, live", secs=3.2)
    reel.do("desk", f'look "{w}"', "desk", f'do prop "{w}" open=a5905', "wait", "1200")
    reel.say("+ New starts a page", secs=1.2)
    reel.do("click", "writing/mine/a5903/side/top/new/f5901", "wait", "1500", secs=1.0)
    reel.do("click", "writing/mine/a5903/main/open/a5907/title", "key", "Ctrl+a")
    reel.type("Garden plan", every=2, secs=0.08)
    reel.do("key", "Enter", "wait", "1000")
    reel.do("click", ".md-doc", "wait", "200")
    reel.say("The line being written shows its marks; every other line is drawn")
    reel.type("Spring beds along the **south fence**, three of them.", every=3, secs=0.07)
    reel.shot(1.4)
    reel.do("key", "Enter", "key", "Enter", secs=1.4)
    reel.type("## To do", every=2, secs=0.08)
    reel.do("key", "Enter", secs=0.5)
    reel.type("- [ ] order seeds", every=3, secs=0.08)
    reel.do("key", "Enter", secs=0.4)
    reel.say("Enter carries the list on")
    reel.type("turn the compost", every=3, secs=0.08)
    reel.do("key", "Enter", "key", "Enter", secs=0.8)
    reel.say("A table: its rows are text while you write them, a table once you leave")
    reel.type("## Beds", every=2, secs=0.08)
    reel.do("key", "Enter")
    for row in ("| Bed | Crop | Sown |", "| --- | --- | --- |", "| 1 | peas | March |", "| 2 | *beans* | May |"):
        reel.type(row, every=5, secs=0.06)
        reel.do("key", "Enter", secs=0.25)
    reel.do("key", "Enter", secs=1.6)
    reel.say("[[ offers the documents; the link is kept by id, so a rename never breaks it")
    reel.type("Why one text: see [[Contin", every=3, secs=0.08)
    reel.shot(2.0)
    reel.do("key", "Enter", secs=1.0)
    reel.type(".", every=1, secs=0.3)
    reel.do("key", "Enter", "key", "Enter")
    reel.say("![[id]] embeds a live thing")
    reel.type("![[a5820]]", every=2, secs=0.1)
    reel.do("key", "Enter", secs=1.8)
    reel.say("Leaving the page saves it: one Markdown text")
    reel.do("blur", "wait", "1500", secs=2.6)
    reel.say("Tick a task with a click")
    reel.do("click", ".md-check", "wait", "1200", secs=2.0)
    reel.say("Ctrl+E: the source, one key away")
    reel.do("click", "writing/mine/a5903/main/open/a5907/crumbs/raw", "wait", "500", secs=3.2)
    reel.do("click", "writing/mine/a5903/main/open/a5907/crumbs/raw", "wait", "500", secs=1.2)
    reel.say("A link opens the other document")
    reel.do("click", ".md-wl", "wait", "1800", secs=2.2)
    reel.say("…where 'Mentioned in' already lists the new page, live", secs=3.6)
    reel.do("click", "writing/mine/a5903/main/open/a4865/crumbs/back", "wait", "1500")
    reel.say("Back. Same world, one text per document, readable and writable by every resident", secs=3.6)
    reel.run(world, "writing")

    # the reel: each frame held for its time (ffmpeg's concat list), then one H.264 file
    lst = out / "frames.txt"
    lst.write_text("".join(f"file '{f.as_posix()}'\nduration {s}\n" for f, s in reel.frames)
                   + f"file '{reel.frames[-1][0].as_posix()}'\n", encoding="utf-8")
    mp4 = out / "writing-demo.mp4"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf",
                    "scale=1920:-2:flags=lanczos,format=yuv420p", "-r", "30", "-c:v", "libx264", "-crf", "18", str(mp4)], check=True)
    print(f"film: {mp4} ({len(reel.frames)} frames, {sum(s for _, s in reel.frames):.0f} s)")


if __name__ == "__main__":
    main()
