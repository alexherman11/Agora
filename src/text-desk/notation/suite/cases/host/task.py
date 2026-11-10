"""A lens about me and about today, as a person writes one for their own tasks (juniper-7).

Two things must hold for a lens to be someone's and to be about every day it is opened: the host names ($me,
$today) bind wherever a lens word can use them, and writing the lens does not freeze today into it.
"""
import re

SEED = ["look", "clock 2026-09-25"]
STEPS = {
    "1": ("My tasks, due today, shown to me; and a week that starts today.", None),
    "2": ("The next day.", None),
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


def probe(name, run):
    """-> (verdict, note)"""
    if name == "binds-everywhere":
        out, refused = run.line("scene mine")
        if refused:
            return "visible", out.splitlines()[0]
        bad = []
        if "me=juniper" not in out:
            bad.append("text")
        if "1 of kind:task,prop:owner=juniper" not in out:
            bad.append("of")
        if "no today" in out or "only when" in out and "$today=20" not in out:
            bad.append("only when")
        if "uninterpretable" in out:
            bad.append("derive")
        return ("holds", "") if not bad else ("silent", "host names do not bind in: " + ", ".join(bad))
    if name == "follows-the-clock":
        out, _ = run.line("scene week")
        m = re.search(r"days-from\((\d{4}-\d{2}-\d{2})", out)
        today = run.desk.today
        if not m:
            return "visible", "the week printed no range"
        return ("holds", "") if m.group(1) == today else ("silent", f"the week starts {m.group(1)} while today is {today}")
    if name == "writing-leaves-today-alone":
        # the person writes $today in a lens the natural way, without an escape
        run.line('do create f01 kind=note title="natural week" tags=lens text="w : column, derive days = days-from $today 2026-12-31, over $days, each d, clamp 1\\nd : text \\"$it.date\\""')
        s = next(s for s in run.desk.world.subjects.values() if s["title"] == "natural week")
        if "$today" in s["text"]:
            return "holds", ""
        return "silent", "the command that wrote the lens froze today into it: " + re.search(r"days-from \S+", s["text"]).group()
    raise KeyError(name)
