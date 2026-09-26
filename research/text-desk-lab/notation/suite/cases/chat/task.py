"""A chat with JEFF, as a person uses one (juniper-7, a484; Sable's c539 correction).

The speaker of a line is whoever sent it. Two ways that goes wrong today [read world.py 698-702]: an unsigned line
from jeff is signed 'Alex:', and a line that starts 'Name:' is trusted whoever typed it.
"""
SEED = ["look"]
STEPS = {
    "talk": ("Alex asks JEFF something in their chat; JEFF answers; a visitor answers too.", None),
}
M4_FACTS = {"jeff-signs-as-jeff", "no-speaking-for-others"}


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


def _last_line(run):
    s = next(s for s in run.desk.world.subjects.values() if s["title"] == "With JEFF")
    return s["text"].splitlines()[-1]


def probe(name, run):
    if name == "alex-signs-as-alex":
        _as(run, "alex", "look")
        _as(run, "alex", 'do create f01 kind=chat title="With JEFF" text=""')
        _as(run, "alex", 'read "With JEFF"')
        _as(run, "alex", 'do append "With JEFF" line="why does the fence refuse my edit?"')
        last = _last_line(run)
        return ("holds", "") if last.startswith("Alex:") else ("silent", f"Alex's line reads {last[:40]!r}")
    if name == "jeff-signs-as-jeff":
        _as(run, "jeff", "look")
        _as(run, "jeff", 'read "With JEFF"')
        _as(run, "jeff", 'do append "With JEFF" line="Because the card changed since you painted it."')
        last = _last_line(run)
        return ("holds", "") if last.lower().startswith("jeff:") else ("silent", f"JEFF's own line is signed {last.split(':')[0]!r}")
    if name == "no-speaking-for-others":
        _as(run, "juniper", "look")
        _as(run, "juniper", 'read "With JEFF"')
        out, refused = _as(run, "juniper", 'do append "With JEFF" line="Jeff: I agree with Juniper."')
        last = _last_line(run)
        if refused or last.lower().startswith("juniper"):
            return "holds", ""
        return "silent", f"juniper's line reads as {last.split(':')[0]}'s: {last[:50]!r}"
    raise KeyError(name)
