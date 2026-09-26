"""Alex's workspace (a319, his first ordinary thing), as he says it, with the facts that must hold.

"Keep this workspace, with its bar collapsed, while a document is being edited and background tasks finish."
Four regions: a collapsed project bar; a chat with JEFF showing code and diagrams; a document page; background
tasks. This file reads the text side only. Draft, caret and focus are Pike's browser reader (S14). Many facts are
not expressible yet (no fold, no tracks, no blocks, no freshness field); the baseline is meant to show those gaps
as n/e, and each probe starts to judge when its word lands.
"""
import re

SEED = ["look", "clock 2026-09-25"]
STEPS = {
    "set": ("My workspace: projects on the left, collapsed; my chat with JEFF; the document I'm writing; the "
            "background tasks JEFF runs for me.", None),
    "work": ("I'm editing the document's second paragraph. Meanwhile JEFF finishes the suite run, edits his own notes, "
             "and appends a result line to my document.", None),
}
M4_FACTS = set()


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


def probe(name, run):
    """-> (verdict, note). A probe whose word does not exist yet returns ("n/e", why)."""
    if name == "finished-task-shows":
        _as(run, "jeff", "look")
        _as(run, "jeff", 'do prop "Run the suite" status=done')
        out, _ = run.line("scene workspace")
        lines = out.splitlines()
        at = next((i for i, l in enumerate(lines) if '"Run the suite"' in l), None)
        if at is None:
            return "silent", "the finished task is missing from the tasks region"
        return ("holds", "") if '"done"' in " ".join(lines[at:at + 3]) else ("silent", "the finished task still reads as open")
    if name == "finished-says-when":
        _as(run, "jeff", 'do comment "Run the suite" line="log: 82 same"')     # a later comment must not look like a finish
        out, _ = run.line("scene workspace")
        seg = out[out.find("Run the suite"):][:400]
        if not re.search(r"\b(ago|\d{2}:\d{2})\b", seg):
            return "n/e", "no word for when a thing last changed ($touched); a finished task cannot say how fresh it is"
        # it must say when it FINISHED: the event that set status=done, not its creation or a later comment
        done = [e for e in run.desk.world.events if e["verb"] == "prop" and (e.get("args") or {}).get("status") == "done"
                and not e.get("undone")]
        if done and re.search(rf"\b{done[-1]['id']}\b", seg):
            return "holds", ""
        return "silent", "the task prints a time, but not the time it finished"
    if name == "jeff-elsewhere-leaves-my-edit":
        run.line('read "Draft: painter continuity"')
        _as(run, "jeff", 'read "JEFF notes"')
        _as(run, "jeff", 'do append "JEFF notes" line="suite: 82 same"')
        _, refused = run.line('do rewrite "Draft: painter continuity" text="Painter continuity\\nEvery gesture works in a real browser, and nothing a person typed is lost."')
        return ("visible", "my edit was refused by a change to another thing") if refused else ("holds", "")
    if name == "jeff-appends-to-my-doc":
        run.line('read "Draft: painter continuity"')
        _as(run, "jeff", 'read "Draft: painter continuity"')
        _as(run, "jeff", 'do append "Draft: painter continuity" line="Result: S14 holds (appended by JEFF)."')
        _, refused = run.line('do rewrite "Draft: painter continuity" text="Painter continuity\\nNothing a person typed is lost, even while a task writes."')
        s = next(s for s in run.desk.world.subjects.values() if s["title"] == "Draft: painter continuity")
        if refused:
            return "visible", "my paragraph edit was refused because JEFF appended a line: whole-value text (the text gateway case, c322)"
        return ("holds", "") if "appended by JEFF" in s["text"] else ("silent", "JEFF's appended line was lost")
    if name == "bar-collapsed-is-mine":
        out, refused = run.line("scene workspace")
        bar = next((l for l in out.splitlines() if l.strip().startswith("bar ")), "")
        if refused or "fold" not in bar:
            return "n/e", "no fold word: a collapsed bar cannot be said, so neither 'no event' nor 'not in Jeff's view' can be judged"
        n0 = len(run.desk.world.events)
        run.line("scene workspace")
        # the text side can judge the authored fold and that printing it makes no event; the viewer's own fold and
        # unfold (no event, not in JEFF's view) is the painter's, judged by Pike's browser reader
        return ("holds", "") if "folded" in bar and len(run.desk.world.events) == n0 else ("silent", f"bar printed as {bar.strip()[:60]}")
    if name == "code-formatted":
        out, _ = run.line("scene workspace")
        msgs = next((l for l in out.splitlines() if l.strip().startswith("msgs ")), "")
        if "```" not in out:
            return "holds", ""
        if "verbatim" in msgs:
            return "n/e", ("the chat is one text, so verbatim applies to all of it: the code keeps its spaces and the prose "
                           "stops wrapping; formatting code inside a message needs blocks or runs")
        return "n/e", "the chat prints its code as raw ``` lines; no blocks row source or verbatim role can be applied"
    if name == "columns-hold":
        out, refused = run.line("scene workspace")
        top = next((l for l in out.splitlines()[1:2]), "")
        if refused or "grid" not in top:
            return "n/e", "no tracks: the row sizes its columns by content (Pike's S14 saw the document column slide 60-80 px)"
        return "holds", ""       # the text side sees declared tracks; whether pixels hold is Pike's S14
    raise KeyError(name)
