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


def _rule(run, who, text):
    """a1027: a rule is a note tagged rule; its text is the rule (quotes inside it escaped as \\")."""
    _as(run, who, "look")
    return _as(run, who, f'do create f01 kind=note tags=rule title="a rule" text="{text}"')


def _drop(run, who, rid):
    _as(run, who, f"look {rid} :1")
    return _as(run, who, f"do remove {rid}")


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
        out, refused = _rule(run, "sable", 'on append by=pike do append line=\\"(noted by the room)\\"')
        m = re.search(r"~ rule (a\d+) saved:", out)
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
        _drop(run, "sable", STATE["rid"])
        _as(run, "sable", 'do prop "Shop talk" last=nobody')
        out, _ = _rule(run, "sable", "on append by=pike do prop last=pike")
        rid = re.search(r"~ rule (a\d+) saved:", out).group(1)
        _as(run, "pike", 'do append "Shop talk" line="and again"')
        out, refused = _as(run, "sable", 'do prop "Shop talk" last=sable')
        _drop(run, "sable", rid)
        if not refused:
            return "silent", "sable overwrote what her rule wrote without having seen it"
        if "stale" not in out or f"your rule {rid}" not in out:
            return "visible", f"refused, but not for her rule's deed: {out.splitlines()[-1][:160]!r}"
        return "holds", ""
    if name == "authorless-rule-as-before":
        # a rule with no recorded author (a656; a1027: a rule note made before its world's log began) runs as whoever
        # tripped it, its line says 'via rule', and no event of it carries tripped_by (no one's fence or !! line changes)
        out, _ = _rule(run, "sable", 'on append by=pike do append line=\\"(an old rule)\\"')
        rid = re.search(r"~ rule (a\d+) saved:", out).group(1)
        w = run.desk.world
        run.desk._rulestate[w.nodes[rid]["subject"]]["author"] = None     # as a note whose making no event recorded
        n0 = len(run.desk.world.events)
        _, rp = _as(run, "pike", 'do append "Shop talk" line="old times"')
        tail = _lines(run)[-2:]
        ruled = [e for e in run.desk.world.events[n0:] if e.get("via") == f"rule {rid}"]
        _drop(run, "sable", rid)
        if rp or tail != ["Pike: old times", f"Pike, via rule {rid}: (an old rule)"]:
            return "silent", f"after pike's line the chat reads {tail!r}"
        if not ruled or any(e["by"] != "pike" or "tripped_by" in e for e in ruled):
            return "silent", f"the old rule's events read {[(e['id'], e['by'], e.get('tripped_by')) for e in ruled]!r}"
        return "holds", ""
    # a744 (talk, 3a): a plain read of a chat shows what is new to you, under one header
    if name == "catch-up-alternating":
        # juniper and pike take 20 turns on a chat with 30 lines of history: read, then say something. Every read's body
        # is one header plus exactly the lines added since that reader's last read, their own included; nothing skipped.
        old = [f"Alex: old line {k}" for k in range(30)]
        _as(run, "alex", 'do create f01 kind=chat title="Pair talk" text="' + "\\n".join(old) + '"')
        shown, last = {"juniper": [], "pike": []}, {}
        for t in range(20):
            who = ("juniper", "pike")[t % 2]
            _as(run, who, "look")
            out, refused = _as(run, who, 'read "Pair talk"')
            lines = _chat("Pair talk", run)
            body = _body(out)
            start = last.get(who, len(lines) - 10)
            want = ([f"({start} earlier lines folded; read {_app(run, 'Pair talk')} :3 for all)"] if start else []) + lines[start:]
            if refused or body != want:
                return "silent", f"turn {t}, {who} read {body[:3]!r}... wanted {want[:3]!r}... ({len(body)} vs {len(want)} lines)"
            shown[who] += lines[start:]
            last[who] = len(lines)
            _, refused = _as(run, who, f'do append "Pair talk" line="turn {t}"')
            if refused:
                return "visible", f"turn {t}: {who}'s line was refused"
        for who in shown:
            out, _ = _as(run, who, 'read "Pair talk"')
            shown[who] += [l for l in _body(out) if not l.startswith("(")]
            missed = [l for l in _chat("Pair talk", run)[30:] if l not in shown[who]]     # every line said in the 20 turns
            if missed:
                return "silent", f"{who} never saw {missed[:3]!r}"
        out, _ = _as(run, "pike", 'read "Pair talk"')
        if _body(out) != [f"(nothing new since you last read; 50 lines; read {_app(run, 'Pair talk')} :3 or tail=<n>)"]:
            return "visible", f"a read with nothing new printed {_body(out)!r}"
        return "holds", ""
    if name == "first-read-fenced":
        # a first read shows the last 10 lines and does not unlock a rewrite; :3 does; after that, a read that folds only
        # lines already seen keeps it unlocked
        _as(run, "wren", "look")
        out, _ = _as(run, "wren", 'read "Pair talk"')
        if len(_body(out)) != 11:
            return "silent", f"wren's first read printed {len(_body(out))} lines, not a header and 10"
        _, rw = _as(run, "wren", 'do rewrite "Pair talk" text="Wren: tidied"')
        if not rw:
            return "silent", "wren rewrote the chat having seen only its last 10 lines"
        _as(run, "wren", 'read "Pair talk" :3')
        _as(run, "juniper", 'do append "Pair talk" line="one more"')
        out, _ = _as(run, "wren", 'read "Pair talk"')
        if _body(out)[1:] != ["Juniper: one more"]:
            return "silent", f"wren's catch-up read printed {_body(out)!r}"
        out, rw = _as(run, "wren", 'do rewrite "Pair talk" text="Wren: tidied"')
        if rw:
            return "visible", f"wren has seen every line and was refused: {out.splitlines()[-1][:120]!r}"
        return "holds", ""
    # a834 (talk, 3a2): the append receipt counts only lines by others you were never shown; an unread chat takes a line
    if name == "receipt-no-wolf":
        # lived 30 Sep: Sable read Shop talk whole, appended, and was told others had added. Two readers, two appends each:
        # one read it all (:3), one had a first read that folded the top (those lines were there, and the read said so)
        wishes = [f"{('Juniper', 'Pike', 'Wren')[k % 3]}: wish {k}" for k in range(14)]
        _as(run, "alex", 'do create f01 kind=chat title="Wishes" text="' + "\\n".join(wishes) + '"')
        for who, how in (("sable", 'read "Shop talk" :3'), ("kestrel", 'read "Wishes"')):
            chat = how.split('"')[1]
            _as(run, who, "look")
            _as(run, who, how)
            for k in range(2):
                out, refused = _as(run, who, f'do append "{chat}" line="note {k}"')
                if refused:
                    return "visible", f"{who}'s append {k} to {chat} was refused: {out.splitlines()[0][:100]}"
                if "others" in out or "haven't" in out:
                    return "silent", f"{who} read {chat} and appended; receipt {k} cries wolf: {out.splitlines()[1:]!r}"
        return "holds", ""
    if name == "receipt-counts-others":
        _as(run, "juniper", 'do append "Wishes" line="a lens for the porch"')
        out, _ = _as(run, "kestrel", 'do append "Wishes" line="and a clock"')
        want = f"1 line from others you haven't seen; read {_app(run, 'Wishes')}"
        if want not in out:
            return "silent", f"after juniper's line kestrel's receipt reads {out.splitlines()[1:]!r}"
        _as(run, "pike", 'do append "Wishes" line="a bigger desk"')
        out, _ = _as(run, "kestrel", 'do append "Wishes" line="and quiet"')
        if f"2 lines from others you haven't seen; read {_app(run, 'Wishes')}" not in out:
            return "silent", f"after pike's line too kestrel's receipt reads {out.splitlines()[1:]!r}"
        read, _ = _as(run, "kestrel", 'read "Wishes"')
        if _body(read)[1:] != ["Kestrel: note 0", "Kestrel: note 1", "Juniper: a lens for the porch", "Kestrel: and a clock",
                               "Pike: a bigger desk", "Kestrel: and quiet"]:
            return "silent", f"kestrel's catch-up read printed {_body(read)!r}"
        out, _ = _as(run, "kestrel", 'do append "Wishes" line="thanks"')
        if "others" in out or "haven't" in out:
            return "silent", f"kestrel caught up; the next receipt still says {out.splitlines()[1:]!r}"
        return "holds", ""
    if name == "append-unread-lands":
        # three residents were refused posting to Wishes because they had not read it first
        out, refused = _as(run, "moss", 'do append "Wishes" line="a garden"')
        if refused:
            return "visible", f"moss has never read Wishes and was refused: {out.splitlines()[0][:120]!r}"
        if _chat("Wishes", run)[-1] != "Moss: a garden":
            return "silent", f"moss's line reads {_chat('Wishes', run)[-1]!r}"
        if f"you haven't read this chat; read {_app(run, 'Wishes')} to see it" not in out:
            return "visible", f"moss's receipt does not say the chat is unread: {out.splitlines()[1:]!r}"
        for act in ('do rewrite "Wishes" text="Moss: only mine"', 'do retitle "Wishes" title="Moss wishes"'):
            out, refused = _as(run, "moss", act)
            if not refused:
                return "silent", f"moss appended without reading and then {act.split()[1]} went through"
        if _chat("Wishes", run)[0] != "Juniper: wish 0":
            return "silent", "the chat's first line is gone"
        return "holds", ""
    raise KeyError(name)


def _chat(title, run):
    return next(s for s in run.desk.world.subjects.values() if s["title"] == title)["text"].splitlines()


def _app(run, title):
    w = run.desk.world
    sid = next(k for k, s in w.subjects.items() if s["title"] == title)
    return w.appearances_of(sid)[0]


def _body(out):
    return out.split("\n---\n", 1)[1].split("\n---", 1)[0].splitlines()


STATE = {}


OLD = ["Alex: is the renderer ready?", "Jeff: tomorrow", "an unsigned line from before", "Priya: Jeff: quoting him"]


def _lines(run):
    s = next(s for s in run.desk.world.subjects.values() if s["title"] == "Shop talk")
    return s["text"].splitlines()
