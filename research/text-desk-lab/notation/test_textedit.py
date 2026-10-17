# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_textedit (a6067): the world's half of the continuous-text module's seam.

    python test_textedit.py

The module (desk-shell/textedit.js) sends a document's whole text fenced by the version it fitted its edits to, and
fits the desk's new words over what it has not sent (its own half is checked in a real page by
test_textedit_paint.py). This checks the desk keeps its side, through deskd's own /api/do, as the painter sends:
Imagined use: Alex writes in a document in the home base while Pike, a resident, fixes a word with `do replace`.
  1. a whole-text rewrite sent against the version before Pike's replace is refused (fenced), never written over it;
  2. sent again against the version that holds Pike's words, it is done, and both edits stand;
  3. Pike replacing words Alex's sent edit already changed is refused in words (nothing guessed);
  4. the world's undo of a sent edit (`undo eN`, the module's second undo) is refused once someone has edited after
     it (saying why), and puts the words back when it is the latest;
  5. `on capture` is a gesture of a text being written, refused on a part with no `on edit`;
  6. the control screen names a passage of one continuous text (part:<key>::<line>) as its document, words and rev.
"""
import importlib
import json
import os
import shutil
import sys
import tempfile
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1200]}"))
    if not ok:
        fails.append(name)


argv = sys.argv
try:
    sys.argv = ["deskd.py"]
    deskd = importlib.import_module("deskd")
finally:
    sys.argv = argv
tmp = Path(tempfile.mkdtemp(prefix="textedit-"))
deskd.SESSIONS = tmp
deskd._DESKS.clear()
deskd._SCENES.clear()
server = ThreadingHTTPServer(("127.0.0.1", 0), deskd.Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
WORLD = "textedit-test"


def do(line, actor, observed=None):
    data = json.dumps({"session": WORLD, "as": actor, "line": line, "observed": observed}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{server.server_port}/api/do", data, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def rev(item):
    with deskd.Session(WORLD, "alex") as desk:
        return desk.world.nodes[item]["rev"]


def text(item):
    with deskd.Session(WORLD, "alex") as desk:
        n = desk.world.nodes[item]
        return desk.world.subjects[n["subject"]].get("text")


esc = lambda s: s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
try:
    with deskd.Session(WORLD, "alex") as desk:
        root = desk.world.root
    do("look", "alex")
    doc = do(f'do create {root} kind=note title="Plan" text="{esc("Intro." + chr(10) + chr(10) + "The plan is to bild it." + chr(10))}"', "alex")["created"][0]
    seen = {"item": doc, "rev": rev(doc)}                 # the version Alex's window was painted at

    # Pike fixes a typo while Alex is typing (his words are unsent, in his window only)
    do(f"read {doc}", "pike")
    r = do(f'do replace {doc} old="bild" new="build"', "pike")
    check("the resident's replace is done", not r.get("error") and text(doc).endswith("build it.\n"), r)

    # 1. the module's first send was typed (and fitted) against the version before Pike's: refused by the fence
    alex = "Intro. Written by Alex.\n\nThe plan is to bild it.\n"
    r = do(f'do rewrite {doc} text="{esc(alex)}"', "alex", seen)
    check("a whole-text rewrite on the old version is refused, not written over Pike's words",
          r.get("error") and "changed since this was painted" in r["error"] and "build it" in text(doc), r)

    # 2. the module fits Pike's edit over its unsent words and sends against the version that holds them
    fitted = "Intro. Written by Alex.\n\nThe plan is to build it.\n"
    r = do(f'do rewrite {doc} text="{esc(fitted)}"', "alex", {"item": doc, "rev": rev(doc)})
    sent = (r.get("events") or [None])[-1]
    check("sent again against the new version: done, and both edits stand", not r.get("error") and text(doc) == fitted and sent, r)

    # 3. Pike's next replace quotes words Alex's sent edit removed: refused in words, nothing guessed
    do(f"read {doc}", "pike")
    r = do(f'do replace {doc} old="Intro." new="Introduction."', "pike")
    check("a replace of words that still stand is done", not r.get("error") and text(doc).startswith("Introduction."), r)
    r = do(f'do replace {doc} old="Intro. Written" new="Hello"', "pike")
    check("a replace of words that are gone is refused, loudly", bool(r.get("error")) and text(doc).startswith("Introduction. Written"), r)

    # 4. the module's second undo: the world's undo of the sent edit
    do(f"look {doc}", "alex")
    r = do(f"undo {sent}", "alex")
    blob = str(r.get("error") or "") + str(r.get("text") or "")
    check("the world's undo of a sent edit someone has edited over is refused, saying why", "not the latest change" in blob and text(doc).startswith("Introduction."), r)
    now = text(doc)
    r = do(f'do rewrite {doc} text="{esc(now + "A last line." + chr(10))}"', "alex", {"item": doc, "rev": rev(doc)})
    last = (r.get("events") or [None])[-1]
    do(f"read {doc}", "alex")
    r = do(f"undo {last}", "alex")
    check("the world's undo of Alex's latest sent edit puts the words back as they were", not r.get("error") and text(doc) == now, r)
finally:
    server.shutdown()
    server.server_close()
    deskd._DESKS.clear()
    deskd._SCENES.clear()
    shutil.rmtree(tmp, ignore_errors=True)

# 5. `on capture` belongs to a text being written
import scene   # noqa: E402
try:
    scene.parse('x : text "a", on capture do prop $item seen=$value')
    check("`on capture` without `on edit` is refused", False, "admitted")
except scene.LensRefusal as e:
    check("`on capture` without `on edit` is refused", "has no `on edit`" in str(e), e)
try:
    scene.parse('x : text "a", markdown, on edit do rewrite $item text="$value", on capture do prop $item seen=$value')
    check("`on capture` on a document being written compiles", True)
except scene.LensRefusal as e:
    check("`on capture` on a document being written compiles", False, e)

# 6. the control screen: a drag over two lines of a document names the document, the words and the revision
sys.path.insert(0, str(HERE.parent.parent / "window-lab" / "capture"))
try:
    import capture   # noqa: E402
    root_node = {"key": "w", "paint": {}, "kids": [{"key": "w/a12/body", "fence": {"item": "a12", "rev": 7, "bind": {"subject": "s11"}},
                                                     "paint": {"text": "# Plan\nWe build it.\nThen we test it.\n", "role": "body"}, "kids": []}]}
    parts = [{"aid": "part:w/a12/body", "rect": [0, 0, 600, 400], "words": "Plan We build it. Then we test it."},
             {"aid": "part:w/a12/body::1", "rect": [0, 40, 600, 20], "words": "We build it."},
             {"aid": "part:w/a12/body::2", "rect": [0, 60, 600, 20], "words": "Then we test it."}]
    refs = capture.refs_from(parts, root_node, 99, ("frontier", "alex", "writing"), rect=[0, 38, 600, 44])
    r0 = refs[0] if refs else {}
    check("a passage is named: its document, its rev, and the words under the drag",
          len(refs) == 1 and r0.get("item") == "a12" and r0.get("rev") == 7 and r0.get("passage") == "We build it.\nThen we test it.", refs)
except ImportError as e:
    check("capture.py imports", False, e)

print("all passed" if not fails else f"{len(fails)} FAILED: " + "; ".join(fails))
sys.exit(1 if fails else 0)
