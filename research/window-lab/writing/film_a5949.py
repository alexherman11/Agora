"""film_a5949: the Writing room back in the home base, with its comments and Talk (a5949), filmed headless in a copy of
a world at Alex's size (2560x1440). Nothing on his screen. Uses a5820's Reel (film.py).

    python research/window-lab/writing/film_a5949.py [world] [out dir]     (world: frontier-try, after apply.py lines)

The story, in one copy so each step stands on the one before: the home base with JEFF's chat; the dock's Writing room
opens Writing on the LEFT of the chat; words selected in a page -> a Comment box -> sent: the words stay lit, a note in
the margin says where they stand, and the line is in the page's Talk; a tick answered in the text; the text edited so
the comment says its words changed; a design opened in the viewer with design-review, a tick answered there too.
The keys name ids in frontier-try on 16 Oct (layout f5664, viewer a5482, writer a5914, first page a5916, design f4358).
"""
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from film import FFMPEG, Reel   # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
VIEW = "home/tiles/lens:home-tiling/stage/f5664/body/pinned/lens:home-viewer/viewer/mine/a5482/split/left/open"
PAGE = f"{VIEW}/a5911/run/lens:writing/writing/mine/a5914/workspace/desk/doc/one/a5916/lens:doc-page/page/stood/one/a5916/a5914"
ICON = "home/dock/lens:home-dock/foot/dock/f5565/a5482/apps/a5573/view"
PICK = ("(() => { const want = window.__want; const r = document.querySelector('.md-doc');"
        " const w = document.createTreeWalker(r, NodeFilter.SHOW_TEXT); let n;"
        " while ((n = w.nextNode())) { const i = n.data.indexOf(want); if (i >= 0) {"
        " getSelection().setBaseAndExtent(n, i, n, i + want.length); document.dispatchEvent(new PointerEvent('pointerup'));"
        " return 'selected'; } } return 'not found'; })()")


def select(words):
    return ["js", f"window.__want={words!r}", "js", PICK]


def main():
    world = sys.argv[1] if len(sys.argv) > 1 else "frontier-try"
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("C:/Projects/Agora4/research/window-lab/demos/a5949")
    (out / "frames").mkdir(parents=True, exist_ok=True)
    for f in (out / "frames").glob("*.png"):
        f.unlink()
    reel = Reel(out)
    reel.do("js", "document.body.style.background='#15171b'", "desk", "read a5914", "desk", "do prop a5914 open=a5916",
            "desk", "read a5482", "desk", "do prop a5482 viewing=a5080", "wait", "1500")
    reel.say("The home base: JEFF's chat in the middle", secs=2.5)
    reel.do("click", ICON, "wait", "2500")
    reel.say("The dock's Writing room opens Writing on the LEFT of the chat, in the home base's own look", secs=4)
    reel.do(*select("every note, task and chat that names this page"), "wait", "1800")
    reel.say("Select any words in the page: they stay lit, and a Comment box opens under the page", secs=3.5)
    reel.do("click", f"{PAGE}/work/paper/pending/box", "wait", "300")
    reel.type("Does this include comments too?", every=4, secs=0.08)
    reel.shot(1.2)
    reel.do("key", "Enter", "wait", "2500")
    reel.say("Sent: a margin note on those words (and where they stand), and the line in the page's Talk", secs=4.5)
    reel.do("js", "document.querySelector('.md-check') && document.querySelector('.md-check').scrollIntoView({block:'center'})", "wait", "500")
    reel.say("A tick, answered with a click: [ ] becomes [x] in the text", secs=2)
    reel.do("js", "(() => { const b = [...document.querySelectorAll('.md-task:not(.md-done) .md-check')][0]; if (b) b.click(); return !!b; })()",
            "wait", "2500", secs=3)
    reel.do("desk", "read a5916", "desk", 'do replace a5916 old="every note, task and chat that names" new="every thing that names"',
            "js", "document.querySelector('.md-doc mark, .md-doc') && document.querySelector('.md-doc').scrollIntoView({block:'start'})",
            "wait", "2500")
    reel.say("Someone edits the words: the comment keeps them and says they changed, never a guess", secs=4.5)
    reel.do("desk", "read a5482", "desk", "do prop a5482 viewing=f4358 back=a5911", "wait", "2500")
    reel.say("Any lens opens in the viewer on the thing picked: a design, drawn as a page", secs=3.5)
    reel.do("click", f"{VIEW}/f4358/openwith/review", "wait", "2500")
    reel.say("Open with design-review: Alex's call, ticks, margin notes and its Talk", secs=4)
    reel.do("js", "(() => { const b = [...document.querySelectorAll('[data-key]')].filter(e => e.dataset.key.endsWith('/line/box') && !e.hidden && e.offsetParent)[0]; if (b) { b.scrollIntoView({block:'center'}); b.click(); } return !!b; })()",
            "wait", "2500")
    reel.say("A tick answered on the design: it is the paragraph's own checked=yes", secs=3.5)
    reel.run(world, "home-base")

    lst = out / "frames.txt"
    lst.write_text("".join(f"file '{f.as_posix()}'\nduration {s}\n" for f, s in reel.frames)
                   + f"file '{reel.frames[-1][0].as_posix()}'\n", encoding="utf-8")
    mp4 = out / "writing-in-the-home-base.mp4"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf",
                    "scale=1920:-2:flags=lanczos,format=yuv420p", "-r", "30", "-c:v", "libx264", "-crf", "18", str(mp4)], check=True)
    print(f"film: {mp4} ({len(reel.frames)} frames, {sum(s for _, s in reel.frames):.0f} s)")


if __name__ == "__main__":
    main()
