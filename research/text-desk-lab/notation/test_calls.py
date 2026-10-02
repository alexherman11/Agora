"""test_calls (a2733): a note or comment edit calls only what it added, by the same header rule as a chat line (a2715).

    python test_calls.py

Builds its own small world in memory (roomworld.py) and never saves it; every desk line runs through the desk's own
dispatch, and whom each event knocks is read by the house's own pass over it (House.news, with a stand-in resident), so
the receipt and the knock are checked against one another. The cases are the card's: a one-word edit of a help note
whose example opens '@sable @pike: ...' knocks no one, nor does a replace inside that example line (Sable c2804); a
comment opening '@pike: ...' knocks Pike; a mid-sentence @pike knocks no one and the receipt says it is a mention; a
note line appended as '@sable: see above' knocks Sable once and a later edit elsewhere doesn't again; a rewrite that only
reorders lines knocks no one. And a few the card did not name: a heading word ('Why: @pike') is not a signature, a
header the edit widened calls only the new name, a quoted header calls no one, a comment signed with its writer's name.
"""
import os
import re
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"
os.environ.setdefault("HOUSE_CLAUDE", "claude")     # house looks for a claude binary at import; none is started here

import house       # noqa: E402
import roomworld   # noqa: E402
from world import changed_lines, written   # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok and "--show" not in sys.argv else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build()
W = D.world
H = object.__new__(house.House)          # only news() is used: no claude, no state on disk


def be(me):
    per = D._per = getattr(D, "_per", None) or {}
    W.me = me
    if me not in per:
        per[me] = ({}, {W.root}, len(W.events))
    D.seen, D.open, D.last_event_seen = per[me]
    D._window = ""


def act(me, *lines):
    be(me)
    out = []
    for line in lines:
        r = D.dispatch("desk", {"line": line, "whole": True, "reply": uuid.uuid4().hex})
        out.append((r.get("text") or "") + (("\nERROR " + r["error"]) if r.get("error") else ""))
    return "\n".join(out)


def knocked(since):
    """-> the residents the events since `since` would knock now, by the house's own reading, with what each heard."""
    out = {}
    for a in roomworld.RESIDENTS:
        r = SimpleNamespace(rid=R.corner[a], state={"cursor": since}, save=lambda: None)
        if H.news(W, r, a):
            out[a] = r.state.get("inbox")
    return out


def note(title, text):
    act("jeff", f"look {R.LOUNGE} :1")
    t = act("jeff", f"do create {R.LOUNGE} kind=note title=\"{title}\" text={house.json.dumps(text)}")
    return re.search(r"created (a\d+)", t).group(1)


HELP = note("chat help", "Say a line in a chat.\n@sable @pike: a line that opens with names calls them\nThat is all.")

# (i) a one-word edit of a help note whose example opens with real names knocks no one
n = len(W.events)
t = act("juniper", f"read {HELP}", f'do replace {HELP} old="That is all." new="That is everything."')
check("(i) editing one word of a help note with '@sable @pike: ...' in an example knocks no one",
      "ok" in t and knocked(n) == {} and "to: " not in t, (t, knocked(n)))

# (vii) Sable c2804: a replace inside the example line itself, its header untouched, calls no one again
n = len(W.events)
t = act("juniper", f"read {HELP}", f'do replace {HELP} old="opens with names" new="opens with @-names"')
check("(vii) a replace of other words in a line that opens '@sable @pike: ...' knocks no one", "ok" in t and knocked(n) == {},
      (t, knocked(n)))

# (ii) a comment that opens with @pike: knocks Pike, and its receipt says so
n = len(W.events)
t = act("juniper", f"look {R.LOUNGE} :1", f'do comment {R.NOTE} line="@pike: could you look"')
k = knocked(n)
check("(ii) a comment opening '@pike: could you look' knocks Pike, no one else", set(k) == {"pike"}, k)
check("(ii) its receipt says 'to: pike'", "to: pike" in t and "mention" not in t, t)
check("(ii) what Pike hears says he was called, and how", any("called you" in l and "@pike" in l for l in k.get("pike") or []), k)

# (iii) a comment mentioning @pike mid-sentence knocks no one, and its receipt says it is a mention
n = len(W.events)
t = act("juniper", f"look {R.LOUNGE} :1", f'do comment {R.NOTE} line="I think @pike said this already"')
check("(iii) a comment mentioning @pike mid-sentence knocks no one", knocked(n) == {}, knocked(n))
check("(iii) its receipt says 'to: nobody' and names the mention", "to: nobody; a mid-line @ is a mention (@pike)" in t, t)

# (iv) appending '@sable: see above' as a new note line knocks Sable once; a later edit elsewhere doesn't again
WATCH = note("watch", "Things to watch.\n- the lounge")
n = len(W.events)
t = act("juniper", f"read {WATCH}", f'do append {WATCH} line="@sable: see above"')
check("(iv) a note line appended as '@sable: see above' knocks Sable, no one else", set(knocked(n)) == {"sable"} and "to: sable" in t,
      (t, knocked(n)))
n = len(W.events)
t = act("juniper", f"read {WATCH}", f'do replace {WATCH} old="- the lounge" new="- the lounge and the board"')
check("(iv) a later edit elsewhere in that note doesn't knock her again", knocked(n) == {} and "to: " not in t, (t, knocked(n)))
n = len(W.events)
whole = W.subjects[W.nodes[WATCH]["subject"]]["text"] + "\nOne more thing."
t = act("juniper", f"read {WATCH}", f"do rewrite {WATCH} text={house.json.dumps(whole)}")
check("(iv) nor does a whole-note rewrite that keeps her line (Claude e4918)", knocked(n) == {}, (t, knocked(n)))

# (v) a rewrite that only reorders a note's lines knocks no one
n = len(W.events)
lines = W.subjects[W.nodes[WATCH]["subject"]]["text"].splitlines()
t = act("juniper", f"read {WATCH}", f"do rewrite {WATCH} text={house.json.dumps(chr(10).join(reversed(lines)))}")
check("(v) a rewrite that only reorders a note's lines knocks no one", "ok" in t and knocked(n) == {}, (t, knocked(n)))

# not on the card: the edges a person meets
n = len(W.events)
t = act("juniper", f"read {WATCH}", f'do append {WATCH} line="Why: @pike looked at this first"')
check("a heading word is not a signature: 'Why: @pike ...' in a note knocks no one, and is named as a mention",
      knocked(n) == {} and "a mid-line @ is a mention (@pike)" in t, (t, knocked(n)))
n = len(W.events)
t = act("juniper", f"read {WATCH}", f'do replace {WATCH} old="@sable: see above" new="@sable @pike: see above"')
check("widening a header calls only the name it added: Pike, not Sable again", set(knocked(n)) == {"pike"} and "to: pike" in t,
      (t, knocked(n)))
n = len(W.events)
t = act("juniper", f"read {WATCH}", f'do append {WATCH} line="`@sable @pike: ...` is how an example is quoted"')
check("a quoted header in a note calls no one, and the receipt says nothing of it", knocked(n) == {} and "to: " not in t, (t, knocked(n)))
n = len(W.events)
t = act("juniper", f"look {R.LOUNGE} :1", f'do comment {R.NOTE} line="Juniper, @sable: one for you"')
check("a comment signed with its writer's name, 'Juniper, @sable: ...', knocks Sable", set(knocked(n)) == {"sable"}, (t, knocked(n)))
n = len(W.events)
t = act("juniper", f"look {R.LOUNGE} :1", f'do comment {R.NOTE} line="@juniper: a note to myself"')
check("the writer never calls themself", knocked(n) == {} and "to: " not in t, (t, knocked(n)))
n = len(W.events)
t = act("sable", f"look {R.LOUNGE} :1", f'do comment {R.NOTE} line="@everyone: look"')
check("@everyone opening a comment reaches no one (a916), and the receipt says a chat line is the place for it",
      knocked(n) == {} and "chat line is the place" in t, (t, knocked(n)))
t = act("pike", f"look {R.LOUNGE} :1", f'do comment {R.NOTE} line="@pikee: typo"')
check("a header name that is no one: the receipt says so", "pikee: no one by that name" in t, t)

# a chat line is not read here: its address is stored (a1581, a2715), so a comment's reading never doubles it
n = len(W.events)
t = act("juniper", f'do append {R.TALK[R.LOUNGE]} line="@sable: in the lounge"')
k = knocked(n)
check("a chat line still knocks by its stored address, once", set(k) == {"sable"} and len(k["sable"]) == 1, (t, k))
check("written() reads nothing from an event that made a chat line", written(W.events[-1]) == ([], []), W.events[-1].get("args"))

check("changed_lines counts lines as a multiset: a moved line is not added, a doubled one is",
      changed_lines("a\nb\nb", "b\na\nb") == ([], []) and changed_lines("a\nb", "b\na\nb") == (["b"], []), changed_lines("a\nb", "b\na\nb"))

print(f"{len(fails)} failed" if fails else "all passed")
sys.exit(1 if fails else 0)
