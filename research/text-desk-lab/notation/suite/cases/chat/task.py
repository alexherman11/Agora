"""A chat with JEFF, as a person uses one (juniper-7, a484; Sable's c539 correction).

The speaker of a line is whoever sent it. Two ways that goes wrong today [read world.py 698-702]: an unsigned line
from jeff is signed 'Alex:', and a line that starts 'Name:' is trusted whoever typed it.
"""
import re

SEED = ["look"]
STEPS = {
    "talk": ("Alex asks JEFF something in their chat; JEFF answers; a visitor answers too.", None),
}
M4_FACTS = {"jeff-signs-as-jeff", "no-speaking-for-others", "old-lines-stay", "two-speak-unread", "stale-rewrite-refused",
            "own-name-once", "verb-signs-caller", "rule-acts-as-author", "author-told-your-rule", "author-fenced-by-rule",
            "authorless-rule-as-before"}


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
    # a656: a live room. Lines already in a chat (old conventions, an unsigned one) must read exactly as before.
    if name == "old-lines-stay":
        _as(run, "alex", "look")
        _as(run, "alex", 'do create f01 kind=chat title="Shop talk" text="' + "\\n".join(OLD) + '"')
        for who in ("juniper", "pike", "sable", "wren"):
            _as(run, who, "look")
            _as(run, who, 'read "Shop talk"')
        return ("holds", "") if _lines(run)[:len(OLD)] == OLD else ("silent", f"the seeded lines read {_lines(run)[:3]!r}")
    if name == "two-speak-unread":
        a, ra = _as(run, "juniper", 'do append "Shop talk" line="the lens is back"')
        b, rb = _as(run, "pike", 'do append "Shop talk" line="and the fence held"')      # pike has not read juniper's line
        tail = _lines(run)[-2:]
        if ra or rb:
            return "visible", "an append was refused: " + (a if ra else b).splitlines()[0][:100]
        if tail != ["Juniper: the lens is back", "Pike: and the fence held"]:
            return "silent", f"the last two lines read {tail!r}"
        return "holds", ""
    if name == "stale-rewrite-refused":
        _, ra = _as(run, "juniper", 'do append "Shop talk" line="one more"')             # behind pike's line: still lands
        out, rw = _as(run, "juniper", 'do rewrite "Shop talk" text="Juniper: only me now"')
        if ra:
            return "visible", "juniper's second append was refused"
        if not rw:
            return "silent", "juniper rewrote the chat without having read pike's line"
        return ("holds", "") if "Pike: and the fence held" in _lines(run) else ("silent", "pike's line is gone")
    if name == "own-name-once":
        for typed, want in (("sable: hello all", "Sable: hello all"), ("SABLE:  loud", "Sable: loud"), ("Sable:quiet", "Sable: quiet")):
            out, refused = _as(run, "sable", f'do append "Shop talk" line="{typed}"')
            last = _lines(run)[-1]
            if refused or last != want:
                return "silent", f"sable typed {typed!r}; the chat reads {last!r}"
            if "your typed name was dropped" not in out:
                return "visible", f"the receipt for {typed!r} does not say why the name went: {out[:120]!r}"
        _as(run, "sable", 'do append "Shop talk" line="Juniper said so"')      # another's name: plain words
        return ("holds", "") if _lines(run)[-1] == "Sable: Juniper said so" else ("silent", f"reads {_lines(run)[-1]!r}")
    if name == "verb-signs-caller":
        _as(run, "juniper", 'do create f01 kind=note title=wave tags=verb text="# wave in Shop talk\\ndo append \\"Shop talk\\" line=\\"*waves at $1*\\""')
        _as(run, "juniper", "look")
        vid = next(a for a in run.desk.world.nodes if run.desk.world.title(run.desk.world.nodes[a]) == "wave")
        _as(run, "juniper", f"do prop {vid} on=house")
        out, refused = _as(run, "wren", "wave pike")
        last = _lines(run)[-1]
        if refused or last != "Wren: *waves at pike*":
            return "silent", f"wren used juniper's verb; the chat reads {last!r} ({out.splitlines()[-1][:80]})"
        return "holds", ""
    if name == "rule-acts-as-author":
        # a687 (decided in a683): a rule is a standing act its author chose, so it acts as its author. Sable's rule,
        # tripped by pike, adds a line signed 'Sable:' with no 'via' (the event carries it); pike's receipt says whose
        out, refused = _as(run, "sable", 'rule on append by=pike do append line="(noted by the room)"')
        m = re.search(r"^ok (r\d+):", out, re.M)
        rid = STATE["rid"] = m.group(1) if m else "?"
        n0 = len(run.desk.world.events)
        pout, rp = _as(run, "pike", 'do append "Shop talk" line="shipping it"')
        tail = _lines(run)[-2:]
        ruled = [e for e in run.desk.world.events[n0:] if e.get("via") == f"rule {rid}"]
        if refused or rp:
            return "visible", f"the rule or pike's line was refused: {(out if refused else pout).splitlines()[0][:100]}"
        if tail != ["Pike: shipping it", "Sable: (noted by the room)"]:
            return "silent", f"after pike's line the chat reads {tail!r}"
        if not ruled or any(e["by"] != "sable" or e.get("tripped_by") != "pike" for e in ruled):
            return "silent", f"the rule's events read {[(e['id'], e['by'], e.get('tripped_by')) for e in ruled]!r}"
        if f"{rid} fired on" not in pout or "as sable" not in pout:
            return "visible", f"pike's receipt does not say the rule acted as sable: {pout.splitlines()[-1][:100]!r}"
        return "holds", ""
    if name == "author-told-your-rule":
        # Sable has not looked since pike tripped the rule: her !! line names the deed as her rule's, not as 'by sable'
        out, _ = _as(run, "sable", "look")
        head = out.splitlines()[0] if out.startswith("!!") else ""
        want = f"your rule {STATE['rid']} did append"
        if want not in head:
            return "silent", f"sable's first line after the rule acted for her: {head[:160]!r}"
        return "holds", ""
    if name == "author-fenced-by-rule":
        # Sable keeps a prop she wrote; her rule rewrites it when pike speaks; she, who has not looked since, is refused
        # when she writes it again: the rule's deed was not on her receipts
        _as(run, "sable", f"rule drop {STATE['rid']}")
        _as(run, "sable", 'do prop "Shop talk" last=nobody')
        out, _ = _as(run, "sable", 'rule on append by=pike do prop last=pike')
        rid = re.search(r"^ok (r\d+):", out, re.M).group(1)
        _as(run, "pike", 'do append "Shop talk" line="and again"')
        out, refused = _as(run, "sable", 'do prop "Shop talk" last=sable')
        _as(run, "sable", f"rule drop {rid}")
        if not refused:
            return "silent", "sable overwrote what her rule wrote without having seen it"
        if "stale" not in out or f"your rule {rid}" not in out:
            return "visible", f"refused, but not for her rule's deed: {out.splitlines()[-1][:160]!r}"
        return "holds", ""
    if name == "authorless-rule-as-before":
        # a rule saved before a656 carries no author: it runs as whoever tripped it, its line says 'via rule', and no
        # event of it carries tripped_by (so no one's fence or !! line changes)
        out, _ = _as(run, "sable", 'rule on append by=pike do append line="(an old rule)"')
        rid = re.search(r"^ok (r\d+):", out, re.M).group(1)
        next(r for r in run.desk.rules if r["id"] == rid).pop("author")      # as a rule unpickled from before a656
        n0 = len(run.desk.world.events)
        _, rp = _as(run, "pike", 'do append "Shop talk" line="old times"')
        tail = _lines(run)[-2:]
        ruled = [e for e in run.desk.world.events[n0:] if e.get("via") == f"rule {rid}"]
        _as(run, "sable", f"rule drop {rid}")
        if rp or tail != ["Pike: old times", f"Pike, via rule {rid}: (an old rule)"]:
            return "silent", f"after pike's line the chat reads {tail!r}"
        if not ruled or any(e["by"] != "pike" or "tripped_by" in e for e in ruled):
            return "silent", f"the old rule's events read {[(e['id'], e['by'], e.get('tripped_by')) for e in ruled]!r}"
        return "holds", ""
    raise KeyError(name)


STATE = {}


OLD = ["Alex: is the renderer ready?", "Jeff: tomorrow", "an unsigned line from before", "Priya: Jeff: quoting him"]


def _lines(run):
    s = next(s for s in run.desk.world.subjects.values() if s["title"] == "Shop talk")
    return s["text"].splitlines()
