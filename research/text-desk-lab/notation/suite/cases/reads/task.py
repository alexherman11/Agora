"""What counts as a read (Jeff's 1758e14, "a print reads only what it printed whole"), in everyday moments.

Each probe is a person who reads a value through one printer and then acts. Two ways to be wrong:
- over-refusal: the person saw the value printed, acts, and is told "you have not looked at it yet" (visible);
- over-grant: the person never saw the value they overwrite (or saw only its title), and the write is accepted,
  dropping someone else's words (silent: the receipt says "dropped" after the loss).
The other person always acts through `read`, so their own act is well founded.
"""
SEED = ["look"]
STEPS = {
    "shown": ("I read my tasks in a view, in my day lens, or in a table, and tick one off.", None),
    "unseen": ("I see a note's title in the outline or in a search, and write over its text without reading it.", None),
}
M4_FACTS = {"blind-after-look", "blind-after-find"}


def plan():
    return {}


def read_scene(tree, p):
    return {}


def read_view(rows, p):
    return {}


def judge(key, value, p):
    return "holds"


def _as(run, who, line):
    me, run.me = run.me, who
    try:
        return run.line(line)
    finally:
        run.me = me


def _tick_after(run, printer, title):
    """jeff owns a task; alex reads it only through `printer`, then ticks it off."""
    _as(run, "jeff", "look")
    _as(run, "jeff", f'do create f01 kind=task title="{title}" status=doing owner=jeff')
    out, refused = _as(run, "alex", printer)
    if refused:
        return "visible", f"the print itself was refused: {out.splitlines()[0][:80]}"
    out, refused = _as(run, "alex", f'do prop "{title}" status=done')
    if refused:
        return "visible", f"'{printer}' printed the status, yet ticking it off was refused: {out.splitlines()[-1][:70]}"
    return "holds", ""


def _blind(run, printer, title):
    """sable writes a two-line note; juniper sees it only through `printer`, then rewrites its text."""
    _as(run, "sable", "look")
    _as(run, "sable", f'do create f01 kind=note title="{title}" text="Rent split by days here.\\nCleaning from November, 90 a month, agreed with Ben."')
    _as(run, "juniper", printer)
    out, refused = _as(run, "juniper", f'do rewrite "{title}" text="Rent split by the nights each of us sleeps here."')
    if refused:
        return "holds", ""
    return "silent", f"after '{printer}', which printed no text, the rewrite was accepted and dropped Sable's two lines"


def probe(name, run):
    if name == "view-is-a-read":
        _as(run, "jeff", "look")
        out, _ = _as(run, "jeff", 'do create f01 kind=view title="Jeff tasks" query=kind:task,prop:owner=jeff cols=title,status')
        vid = out.split("created ")[1].split()[0]
        return _tick_after(run, f"look {vid} :3", "Index the photos")
    if name == "lens-is-a-read":
        _as(run, "jeff", "look")
        _as(run, "jeff", 'do create f01 kind=note title="my day" tags=lens text="t : column, of kind:task, each r\\nr : row\\n  a : text \\"$title\\"\\n  b : text \\"$status\\""')
        return _tick_after(run, "scene my day", "Run the suite")
    if name == "table-is-a-read":
        return _tick_after(run, "table kind:task cols=title,status", "Book the campsite")
    if name == "blind-after-look":
        return _blind(run, "look", "Bills")
    if name == "blind-after-find":
        return _blind(run, "find ?Rules", "House rules")
    raise KeyError(name)
