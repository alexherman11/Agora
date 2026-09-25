"""Attacks kept open as instruments: routes by which a lens can still behave like worse JavaScript.

A4 (juniper-6, round six): the program moves into scripts and rules, which the scene cannot show. Jeff's ban on
gestures running scripts or firing rules was reverted on Alex's word (25 Sep: explore a real solution, no
stopgaps), so this route is open until proposals that preview the whole cascade exist. The probes say so.
"""
import re

SEED = ["look"]
STEPS = {
    "a4": ("A board of cards. Clicking a card tidies it: marks it done, prefixes its title, clears its week. "
           "Someone else once made a rule: when anything is tagged, Beta goes to week 99.", None),
}
M4_FACTS = {"click-says-all"}


def plan():
    return {}


def read_scene(tree, p):
    return {}


def read_view(rows, p):
    return {}


def judge(key, value, p):
    return "holds"


def probe(name, run):
    """-> (verdict, note). verdict: holds | silent | visible."""
    w = run.desk.world
    if name == "click-says-all":
        # What a click will do is written next to it. Click Alpha and compare what changed with what was written.
        out, _ = run.line("scene innocent")
        m = re.search(r'"Alpha" · click: (.+?) · key', out)
        if not m:
            return "visible", "no click line printed for Alpha"
        said = m.group(1)
        named = set(re.findall(r"\b[as]\d+\b", said))
        subj = {i: (w.nodes.get(i) or {}).get("subject", i) for i in named}
        named |= set(subj.values())
        n0 = len(w.events)
        _, refused = run.line(said if said.startswith(("do ", "run ")) else "do " + said)
        if refused:
            return "visible", f"the click '{said}' was refused"
        changed = {}
        for e in w.events[n0:]:
            s = (w.nodes.get(e["target"]) or {}).get("subject", e["target"])
            if e["target"] not in named and s not in named:
                changed[e["target"]] = e.get("via") or e["verb"]
        if changed:
            return "silent", f"the click said '{said}' and also changed " + ", ".join(f"{t} (via {v})" for t, v in changed.items())
        return "holds", ""
    if name == "definitions-have-history":
        kinds = {e["verb"] for e in w.events}
        if not kinds & {"script", "rule", "define"}:
            return "silent", "script tidy and rule r1 made no event: history reads as complete, and they cannot be undone or forked as history"
        return "holds", ""
    raise KeyError(name)
