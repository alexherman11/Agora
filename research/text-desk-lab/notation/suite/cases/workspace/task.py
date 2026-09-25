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
        out, _ = run.line("scene workspace")
        seg = out[out.find("Run the suite"):][:400]
        return ("holds", "") if re.search(r"\b(ago|\d{2}:\d{2})\b", seg) else \
            ("n/e", "no word for when a thing last changed ($touched); a finished task cannot say how fresh it is")
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
        return "n/e", "no fold word: a collapsed bar cannot be said, so neither 'no event' nor 'not in Jeff's view' can be judged"
    if name == "code-formatted":
        out, _ = run.line("scene workspace")
        return ("n/e", "the chat prints its code as raw ``` lines; no blocks row source or verbatim role can be applied") \
            if "```" in out else ("holds", "")
    if name == "columns-hold":
        return "n/e", "no tracks: the row sizes its columns by content (Pike's S14 saw the document column slide 60-80 px)"
    raise KeyError(name)
