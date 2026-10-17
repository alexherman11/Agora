"""film_a6067: the continuous-text module's demo (a6067), filmed headless in a copy of a world at Alex's size (2560x1440).
Nothing on his screen; every press is in the copy.

    python research/window-lab/writing/film_a6067.py [world] [out dir]

The story, in the Writing app as Alex: he types in a document and his words go as he pauses; Pike (a resident, through
the same door) replaces other words while Alex's are still unsent: fitted, both stand; Pike replaces the very words Alex
is changing: a conflict, said, nothing sent until Alex chooses Keep mine, and the document says what was set aside;
Ctrl+Z twice: his unsent typing first, then the world's undo of his sent edit, each said; then the home base's chat
composer, the same keys and undo.
"""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import film   # noqa: E402  (a5820's Reel and caption)

FFMPEG = film.FFMPEG


def caret(word, select=False, after=False):
    """put the caret at (or select) the first place `word` stands in the open document"""
    return ["js", "(() => { const p = document.querySelector('.md-part'), te = p._te, M = window.Markdown, root = p.querySelector('.md-doc');"
                  f" const w = {json.dumps(word)}, i = te.doc.text.indexOf(w); if (i < 0) return 'not found';"
                  f" const a = {'i + w.length' if after else 'i'}, b = {'i + w.length' if select or after else 'i'};"
                  " root.focus(); const [n1, o1] = M.pointAt(root, te.doc.text, a), [n2, o2] = M.pointAt(root, te.doc.text, b);"
                  " getSelection().setBaseAndExtent(n1, o1, n2, o2); root.closest('[data-scroll]') && 0;"
                  " (n1.parentElement || n1).scrollIntoView({block: 'center'}); return a; })()"]


def pike(line):
    """Pike, a resident, acts through the same door, as the page's own requests do"""
    return ["js", "(async () => { const q = new URLSearchParams(location.search), s = q.get('session'), f = document.querySelector('.md-part')._n.fence, tr = (f.reads || []).find(e => (e[2] || []).includes('text')), id = tr ? tr[0] : f.item;"
                  " const go = l => fetch('/api/do', {method: 'POST', body: JSON.stringify({session: s, as: 'pike', line: l})}).then(r => r.json());"
                  f" await go('read ' + id + ' :3'); const r = await go({json.dumps(line)}.replace('$ID', id)); return r.error || 'ok'; }})()"]


def main():
    world = sys.argv[1] if len(sys.argv) > 1 else "frontier-try"
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("C:/Projects/Agora4/research/window-lab/demos/a6067")
    (out / "frames").mkdir(parents=True, exist_ok=True)
    for f in (out / "frames").glob("*.png"):
        f.unlink()
    reel = film.Reel(out)

    reel.do("wait", "1200")
    reel.say("One editing module for every text you type in. Here: a Writing document", secs=3.2)
    reel.do(*caret("social fabric.", after=True), "wait", "300")
    reel.say("You type; the words are yours (this window's) until you pause")
    reel.type(" Typed by Alex.", every=3, secs=0.08)
    reel.shot(1.2)
    reel.say("Meanwhile Pike, a resident, replaces other words: “consumers” → “people”")
    reel.do(*pike('do replace $ID old="turns consumers into" new="turns people into"'), "wait", "2200")
    reel.shot(1.0)
    reel.do(*caret("people into"))
    reel.say("Fitted: Pike's change and yours both stand, sent as one text against the new version", secs=3.6)

    reel.do(*caret("largely static", select=True), "wait", "300")
    reel.say("Now you change words Pike is changing too")
    reel.type("mostly frozen", every=3, secs=0.08)
    reel.do(*pike('do replace $ID old="largely static applications" new="fixed applications"'), "wait", "2200")
    reel.say("Conflict: said loudly; nothing of yours is sent until you choose", secs=3.6)
    reel.do("click", ".te-conflict button", "wait", "2500")
    reel.say("Keep mine: your words go over Pike's, and the document says what was set aside", secs=3.6)

    reel.do(*caret("Typed by Alex.", after=True))
    reel.type(" More", every=5, secs=0.3)
    reel.say("Ctrl+Z: first your unsent typing (this window's own undo)…")
    reel.do("key", "Ctrl+z", "wait", "300", secs=2.6)
    reel.say("…then, nothing unsent left, the world's undo of your last sent edit, said as such")
    reel.do("key", "Ctrl+z", "wait", "2500", secs=3.4)
    reel.run(world, "writing")

    reel.do("js", "document.body.style.background='#15171b'", "wait", "1200")
    reel.say("The chat composer is the same module: same keys, same undo, its own Send", secs=3)
    reel.do("click", ".explicit-composer textarea")
    reel.type("Hello JEFF, this is a test", every=4, secs=0.08)
    reel.say("Ctrl+Z takes back what you typed, as in a document")
    reel.do("key", "Ctrl+z", "wait", "300", secs=2.8)
    reel.say("AltGr characters arrive as text (Ctrl+Alt is never a shortcut here); Enter sends", secs=3.2)
    reel.run(world, "home-base")

    lst = out / "frames.txt"
    lst.write_text("".join(f"file '{f.as_posix()}'\nduration {s}\n" for f, s in reel.frames) + f"file '{reel.frames[-1][0].as_posix()}'\n", encoding="utf-8")
    mp4 = out / "continuous-text.mp4"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf", "scale=1920:-2,format=yuv420p",
                    "-r", "30", str(mp4)], check=True)
    print("film:", mp4, f"({sum(s for _, s in reel.frames):.0f} s, {len(reel.frames)} frames)")


if __name__ == "__main__":
    main()
