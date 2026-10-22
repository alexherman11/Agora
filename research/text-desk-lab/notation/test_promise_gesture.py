# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_promise_gesture (a10089): a lens's one-click Decline is saved, and declines only for the one asked.

    python test_promise_gesture.py

Rowan staged `on click do decline $reason.source` in Alex's Waits on me and the stored-line check refused it at save:
'decline is the desk's own verb; a stored line says do decline ...', which it already said. `do decline <promise>` is
the desk's own promise command (desk_knife routes `do accept a2001` as `accept a2001`, a1587); the check now reads it
so. The row's $reason.source is the request's subject, so the promise commands take a subject id as well. In memory
(roomworld); every line through the desk's own dispatch.
"""
import os
import re
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import roomworld   # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build(say=False)
W = D.world


def say(me, *lines):
    """One reply as `me` -> the text of the last line run (an error is returned as 'ERR ...')."""
    W.me = me
    per = D._per
    if me not in per:
        per[me] = ({}, {W.root}, len(W.events))
    D.seen, D.open, D.last_event_seen = per[me]
    D._window = ""
    token, out = uuid.uuid4().hex, ""
    for line in lines:
        r = D.dispatch("desk", {"line": line, "whole": True, "reply": token})
        out = r.get("text") or ("ERR " + (r.get("error") or ""))
        if r.get("error"):
            break
    if out.startswith("!! since") or out.startswith("ERR !! since"):
        head, _, rest = out.partition("\n")
        while rest.startswith("   "):
            rest = rest.partition("\n")[2]
        out = ("ERR " if out.startswith("ERR") else "") + rest
    return out


B = R.BOARD
A = re.findall(r"created (a\d+)", say("sable", f"look {B} :1", f'do create {B} kind=task title="Two more things"'))[-1]
t = say("sable", f'ask to=juniper "the two more things" about={A}')
q = re.search(r"(a\d+) ask", t).group(1)

LENS = f'''waits : column
  decline : text "Decline"
    on click do decline {q}
  accept : text "Accept"
    on click do accept {q}
  withdraw : text "Withdraw"
    on click do withdraw {q}
  each : column
    of prop:kind=promise as reason
    each row
row : text "Decline $reason.title"
  on click do decline $reason.source
'''
import json  # noqa: E402
t = say("juniper", f"look {B} :1", f"do create {B} kind=note title=waits-buttons tags=lens text={json.dumps(LENS)}")
check("a lens whose buttons say do decline / do accept / do withdraw is saved",
      not t.startswith("ERR") and "created" in t and "desk's own verb" not in t, t)
lens = re.findall(r"created (a\d+)", t)[-1] if "created" in t else None
if lens:
    sid = W.nodes[lens]["subject"]
    import verbs  # noqa: E402
    entry = verbs.bind_text(D, "lens", LENS, B, "juniper")
    check("its stored lines leave nothing unbound: the promise words are the desk's own, as they run",
          not entry["missing"], entry["missing"])

# the line its Decline button sends, as each clicker
t = say("pike", f"look {q} :1", f"do decline {q}")
check("someone the request was not asked of cannot decline it (ordinary permissions)", t.startswith("ERR"), t)
check("and it is still open", "declined" not in say("sable", f"examine {q}"))
t = say("juniper", f"look {q} :1", f"do decline {q}")
check("the one it was asked of declines it with one click: the button's own line", "declined by you" in t, t)
check("an ended request refuses a second click", say("juniper", f"do decline {q}").startswith("ERR"))

# the action queue's row carries the request's subject ($reason.source = s2737), so the button sends a subject id
t = say("sable", f'ask to=juniper "one more thing" about={A}')
q2 = re.search(r"(a\d+) ask", t).group(1)
s2 = W.nodes[q2]["subject"]
t = say("pike", f"look {q2} :1", f"do decline {s2}")
check("by its subject id: someone not asked is refused by permission, not by 'no such id'",
      t.startswith("ERR") and "no such id" not in t, t)
t = say("juniper", f"look {q2} :1", f"do decline {s2}")
check("by its subject id: the one asked declines it (the line $reason.source makes)", "declined by you" in t, t)
check("by its subject id: a second click is refused", say("juniper", f"do decline {s2}").startswith("ERR"))

# a world verb named like a promise word is still never bound over the desk's own
t = say("juniper", f"look {B} :1", f'do create {B} kind=note title=sweeper tags=lens text="x : text \\"x\\"\\n  on click do sweep {B}"')
check("a lens naming a verb nobody made is still refused at save (the check is not weakened)",
      t.startswith("ERR") or "not a verb here" in t, t)

print("all passed" if not fails else f"{len(fails)} failed: {fails}")
sys.exit(1 if fails else 0)
