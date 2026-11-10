"""Viewer state from the person's side: the everyday moments where a choice that is not a world fact shapes what is
shown. The case is the instrument a viewer frame is built against, the way the workspace case was for tracks and fold.

The rule this case sorts by (Juniper; a475, juniper-8, and here):
    A viewer choice is paint until something bound or written depends on it; then it is a printed read. The lens
    decides, by naming it: a choice the lens reads ($viewer.open, $viewer.query) enters evaluation, is printed, and is
    recorded in every act's reads; a choice no lens names can shape pixels only, and so can never change what an act
    writes. The sort is by consumer, not by kind: scroll is paint in a note and a read in a chat that marks
    "read up to here".

    enters evaluation (printed read): the open note, a search, a filter (and a chosen sort, if an act reads order)
    stays paint: fold, scroll, a draft, caret and focus (Pike's viewer store; the text side judges only that the
    authored word prints and that nothing is written)

Two solutions, one world:
    today.sol   navigation in today's words: a shared tag `open`, lens props for the search and the filter.
                This is what a person reaches for without a frame; the probes measure what it costs.
    frame.sol   the proposed words (a475 `view open=`, the codex contract, sable-10's declared frame): `on click
                view open=$item`, `$viewer.open`, `?$viewer.query`. Today the lens is refused, and its probes are n/e
                until the words land. The words are proposals; if the frame arrives with other words, rewrite
                frame.sol, not the probes.

The probes act as a person does: they run the click or edit line the scene prints for a row, so the gesture comes
from the lens, not from the probe. The person is run.me; JEFF is "jeff".
"""
import importlib
import pickle
import re
import tempfile
from pathlib import Path

SEED = ["look", "clock 2026-09-25"]
STEPS = {
    "set": ("My notes in three panes: the list, the note I have open, and a search; my tasks, with done ones hidden "
            "when I ask; the projects bar collapsed; my chat with JEFF, staying at the newest line.", None),
    "live": ("I open notes, search, hide what's done, and keep a draft, while JEFF works in the same notes and "
             "opens his own. Later I sketch in a worktree and bring it home.", None),
}
M4_FACTS = {"alias-after-merge"}


def plan():
    return {}


def read_scene(tree, p):
    return {}


def read_view(rows, p):
    return {}


def judge(key, value, p):
    return "holds"


# ---------------------------------------------------------------- helpers

def _as(run, who, line, window=""):
    me, run.me = run.me, who
    try:
        return run.line(line, window)
    finally:
        run.me = me


def _scene(run, lens, who=None):
    return _as(run, who or run.me, f"scene {lens}")


def _under(out, part):
    """The printed lines of a part and its children (by indentation)."""
    lines = out.splitlines()
    at = next((i for i, l in enumerate(lines) if l.strip().startswith(part + " ") or l.strip() == part), None)
    if at is None:
        return []
    ind = len(lines[at]) - len(lines[at].lstrip())
    out = [lines[at]]
    for l in lines[at + 1:]:
        if len(l) - len(l.lstrip()) <= ind:
            break
        out.append(l)
    return out


def _gesture(line, kind):
    seg = next((s for s in line.split(" · ") if s.startswith(kind + ": ")), None)
    return seg[len(kind) + 2:] if seg else None


def _row_click(out, title, part="list"):
    row = next((l for l in _under(out, part) if f'"{title}"' in l), None)
    return _gesture(row, "click") if row else None


def _open(run, who, title):
    """-> (did, why). Open `title` by clicking its row in the notes list, as `who` sees it."""
    out, refused = _scene(run, "notes", who)
    if refused:
        return False, "the notes lens is refused: " + out.strip().splitlines()[-1][:200]
    click = _row_click(out, title)
    if not click:
        return False, f"no click on {title!r} in the list"
    got, refused = _as(run, who, click)
    return (not refused), (got.strip().splitlines()[-1][:200] if refused else "")


def _page(run, who=None):
    """-> (title bound on the page or None, the page's own printed line)."""
    out, refused = _scene(run, "notes", who)
    if refused:
        return None, ""
    block = _under(out, "page")
    if not block:
        return None, ""
    t = next((l for l in block[1:] if l.strip().startswith("t ")), "")
    m = re.search(r'"([^"]*)"', t)
    return (m.group(1) if m else None), block[0].strip()


def _item_of(run, title):
    for i, n in run.desk.world.nodes.items():
        s = run.desk.world.subjects.get(n.get("subject") or "")
        if s and s["title"] == title and i.startswith("a"):
            return i
    return None


def _nodes(n):
    yield n
    for k in n.get("kids", []):
        yield from _nodes(k)


def _page_body_key(run):
    import scene
    _scene(run, "notes")
    sc, _ = scene.scene_for(run.desk, "notes")
    root = sc.get("root", sc)
    b = next((n for n in _nodes(root) if n.get("part") == "b" and "/page/" in n["key"]), None)
    return (b["key"], b.get("item")) if b else (None, None)


NE_FRAME = "no viewer frame: `on click` takes only desk commands and `view` is not a word"


# ---------------------------------------------------------------- probes

def probe(name, run):
    """-> (verdict, note). holds | silent | visible | n/e."""

    if name == "open-binds-the-page":
        # judges: clicking a row binds the page to that note, and the print says which choice bound it
        did, why = _open(run, run.me, "Fence notes")
        if not did:
            return "n/e", why or NE_FRAME
        title, line = _page(run)
        if title != "Fence notes":
            return "silent", f"the page shows {title!r} after opening 'Fence notes'"
        if not re.search(r"viewer|tag:open", line):
            return "silent", "the page is bound, but its line does not say what chose it"
        return "holds", ""

    if name == "open-makes-no-event":
        # judges: opening a note is not history; the world's event count does not move
        n0 = len(run.desk.world.events)
        did, why = _open(run, run.me, "Charter")
        if not did:
            return "n/e", why or NE_FRAME
        k = len(run.desk.world.events) - n0
        return ("holds", "") if k == 0 else ("visible", f"opening a note wrote {k} event(s) to the shared world, "
                                                          "where JEFF's `since your last look` reports them")

    if name == "open-is-mine":
        # judges: my choice does not move JEFF's page, and his does not move mine (per observer: actor + window)
        did, why = _open(run, run.me, "Fence notes")
        if not did:
            return "n/e", why or NE_FRAME
        _open(run, "jeff", "Groceries")
        mine, _ = _page(run)
        _open(run, run.me, "Charter")
        his, _ = _page(run, "jeff")
        wrong = []
        if mine != "Fence notes":
            wrong.append(f"JEFF opening Groceries moved my page to {mine!r}")
        if his != "Groceries":
            wrong.append(f"my opening Charter moved JEFF's page to {his!r}")
        return ("holds", "") if not wrong else ("silent", "; ".join(wrong) + ": navigation is one shared fact")

    if name == "open-survives-rename":
        # judges: the choice names the thing, not its title
        if not _open(run, run.me, "Fence notes")[0]:
            return "n/e", NE_FRAME
        a = _item_of(run, "Fence notes")
        _as(run, "jeff", "look")
        _as(run, "jeff", f"read {a}")
        _as(run, "jeff", f'do retitle {a} title="Fence: why it refuses"')
        title, _ = _page(run)
        return ("holds", "") if title == "Fence: why it refuses" else ("silent", f"after a rename the page shows {title!r}")

    if name == "open-survives-new-rows":
        # judges: the choice names the thing, not its place in the list (new rows land around it)
        if not _open(run, run.me, "Groceries")[0]:
            return "n/e", NE_FRAME
        _as(run, "jeff", "look")
        _as(run, "jeff", 'do create f01 kind=note title="Aardvark" text="a new first row"')
        title, _ = _page(run)
        return ("holds", "") if title == "Groceries" else ("silent", f"after a new row the page shows {title!r}")

    if name == "open-survives-edit":
        # judges: another person's edit to the open note repaints it; it does not unbind or rebind
        if not _open(run, run.me, "Groceries")[0]:
            return "n/e", NE_FRAME
        a = _item_of(run, "Groceries")
        _as(run, "jeff", f"read {a}")
        _as(run, "jeff", f'do append {a} line="oat milk (JEFF)"')
        out, _ = _scene(run, "notes")
        title, _ = _page(run)
        return ("holds", "") if title == "Groceries" and "oat milk" in "\n".join(_under(out, "page")) else \
            ("silent", f"after JEFF's edit the page shows {title!r} without his line")

    if name == "open-thing-gone":
        # judges: when the open thing is deleted, the page says so; it never binds another thing or goes quietly empty
        if not _open(run, run.me, "Groceries")[0]:
            return "n/e", NE_FRAME
        a = _item_of(run, "Groceries")
        _as(run, "jeff", "look")
        _as(run, "jeff", f"do delete {a}")
        title, line = _page(run)
        if title and title != "Groceries":
            return "silent", f"the open note was deleted and the page now shows {title!r}"
        if re.search(r"gone|deleted|removed", line):
            return "holds", ""
        return "visible", f"the page went empty without saying why: {line[:120]}"

    if name == "open-carries-its-read":
        # judges: a click on a row that went stale (JEFF deleted it after my print) is refused whole, and leaves my
        # page as it was: a refusal changes nothing
        if not _open(run, run.me, "Charter")[0]:
            return "n/e", NE_FRAME
        out, _ = _scene(run, "notes")
        click = _row_click(out, "Aardvark")
        if not click:
            return "n/e", "no row for 'Aardvark'"
        _as(run, "jeff", "look")
        _as(run, "jeff", f"do delete {_item_of(run, 'Aardvark')}")
        got, refused = _as(run, run.me, click)
        title, _ = _page(run)
        if not refused:
            return "silent", f"the stale click went through; the page shows {title!r}"
        if title != "Charter":
            return "visible", (f"the click was refused, but half of it landed: the page shows {title!r}, not Charter "
                               "(a two-command gesture is not one act; the transaction, jeff-1)")
        return "holds", ""

    if name == "draft-follows-its-thing":
        # judges: the part a draft is kept under changes when the page binds another note, so words typed on one note
        # are never drawn on another (viewer.js keeps drafts by the part key)
        if not _open(run, run.me, "Charter")[0]:
            return "n/e", NE_FRAME
        k1, i1 = _page_body_key(run)
        _open(run, run.me, "Groceries")
        k2, i2 = _page_body_key(run)
        if not (k1 and k2) or i1 == i2:
            return "n/e", "the page did not rebind"
        if k1 == k2:
            return "visible", (f"the body is keyed by its slot ({k1}) for both {i1} and {i2}: a draft typed on {i1} is "
                               f"drawn over {i2}; its send is refused by the bind's select read, so the world is safe "
                               "and the words sit on the wrong note, where Escape drops them")
        return "holds", ""

    if name == "search-binds-the-list":
        # judges: typing in the search binds the results to what matches, says the query, and is mine alone
        out, refused = _scene(run, "notes")
        if refused:
            return "n/e", NE_FRAME
        box = next((l for l in _under(out, "side") if l.strip().startswith("search ")), None)
        edit = _gesture(box, "edit") if box else None
        if not edit:
            return "n/e", "no search box with an edit"
        his0 = _under(_scene(run, "notes", "jeff")[0], "found")
        _as(run, run.me, edit.replace("$value", "fence"))
        found = _under(_scene(run, "notes")[0], "found")
        titles = set(re.findall(r'entry \S+ "([^"]*)"', "\n".join(found)))
        want = {"Charter", "Fence notes"}
        if titles != want:
            return "silent", (f"I searched 'fence' and the results show {sorted(titles) or 'nothing'}"
                              + (f"; the results line reads: {found[0].strip()[:90]}" if found else ""))
        his1 = _under(_scene(run, "notes", "jeff")[0], "found")
        if [l.split(" · read")[0] for l in his0] != [l.split(" · read")[0] for l in his1]:
            return "silent", "my search changed JEFF's results"
        return "holds", ""

    if name == "filter-says-what-it-hides":
        # judges: "hide done" leaves done tasks out, and the print says what it left out (else it is a 0-of)
        out, refused = _scene(run, "tasks")
        if refused:
            return "n/e", NE_FRAME
        row = next((l for l in out.splitlines() if l.strip().startswith("hide ")), None)
        click = _gesture(row, "click") if row else None
        if not click:
            return "n/e", "no hide control"
        _as(run, run.me, click)
        out, _ = _scene(run, "tasks")
        lst = _under(out, "list")
        if any('"done"' in l for l in lst):
            return "visible", "I asked to hide done tasks and they still show: " + (lst[0].strip()[:100] if lst else "")
        if not re.search(r"status=done|hidden", lst[0] if lst else ""):
            return "silent", "done tasks are gone, and nothing says they were left out"
        return "holds", ""

    if name == "fold-is-paint":
        # judges (text side): the authored fold prints, its rows stay bound, and printing makes no event; the
        # viewer's own unfold (no event, not in JEFF's view) is Pike's reader
        n0 = len(run.desk.world.events)
        out, refused = _scene(run, "bar")
        if refused:
            return "n/e", out.strip().splitlines()[-1][:160]
        blk = _under(out, "bar")
        if not blk or "fold" not in blk[0]:
            return "n/e", "no fold word"
        rows = [l for l in blk if l.strip().startswith("proj ")]
        if len(rows) < 2:
            return "silent", "folding unbound the bar's rows"
        return ("holds", "") if len(run.desk.world.events) == n0 else ("visible", "printing the bar wrote an event")

    if name == "scroll-end-is-paint":
        # judges (text side): the chat says it stays at the newest line, and a new line from JEFF makes his event
        # only; where the person's scroll is, and whether it jumps, is Pike's reader
        out, refused = _scene(run, "chat")
        if refused or "scroll end" not in out:
            return "n/e", "no scroll end"
        _as(run, "jeff", "look")
        n0 = len(run.desk.world.events)
        _as(run, "jeff", 'do append "With JEFF" line="Jeff: the suite is green."')
        _scene(run, "chat")
        k = len(run.desk.world.events) - n0
        return ("holds", "") if k == 1 else ("visible", f"one new line made {k} events")

    if name == "alias-after-merge":
        # judges: a choice made in a worktree, on a thing made there, names that thing after the merge renames its
        # id; it never binds whatever the old id names at home (journal.Aliases.resolve(short, was) is the design)
        import explore  # noqa: F401  (the desk modules are loaded)
        worktree = importlib.import_module("worktree")
        saved = worktree.SESSIONS
        tmp = Path(tempfile.mkdtemp(prefix="viewer-alias-"))
        worktree.SESSIONS = tmp
        try:
            me = run.me
            if _scene(run, "notes")[1]:
                return "n/e", NE_FRAME
            home, _ = _page(run)
            text, run.desk = worktree.handle("worktree fork sketch", "suite", run.desk, me)
            wt = pickle.loads((tmp / "suite@sketch.pickle").read_bytes())
            W = type(run)(me)
            W.desk = wt
            W.desk._session = "suite@sketch"

            def wline(line, who=me):
                before, n0 = worktree.ids_of(W.desk), len(W.desk.world.events)
                W.me = who
                out = W.line(line)
                worktree.record(W.desk, line, who, before, n0)
                return out
            wline("look")
            wline('do create f01 kind=note title="Sketch: viewer frame" text="written in the worktree"')
            made = _item_of(W, "Sketch: viewer frame")
            did, why = _open(W, me, "Sketch: viewer frame")
            if not did:
                return "n/e", why or NE_FRAME
            # the gesture the frame would keep, if it keeps ids: the click that opened it names `made`
            (tmp / "suite@sketch.pickle").write_bytes(pickle.dumps(W.desk))
            _as(run, "jeff", "look")
            _as(run, "jeff", 'do create f01 kind=note title="JEFF: suite log" text="82 same"')
            text, run.desk = worktree.handle("worktree merge sketch", "suite", run.desk, me)
            if not text.startswith("ok"):
                return "n/e", "the merge was refused: " + text.splitlines()[0][:160]
            title, _ = _page(run)
            stranger = run.desk.world.nodes.get(made)
            stranger_t = stranger and run.desk.world.subjects[stranger["subject"]]["title"]
            if title == "Sketch: viewer frame" or (title == home and title != stranger_t):
                return "holds", ""          # it followed its thing home, or home kept its own choice; both are honest
            if title and title == stranger_t:
                return "silent", f"the merge renamed {made}; my choice kept the id and opened {title!r}"
            return "visible", f"after the merge the page shows {title!r}, not the sketch I opened"
        finally:
            worktree.SESSIONS = saved

    raise KeyError(name)
