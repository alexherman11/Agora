# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_comment_reply (13 Oct): a reply under a comment that stays open.

    python test_comment_reply.py

Alex, 13 Oct, in the design-review window: 'can we make it so the agents can reply in line ... reply to the comments'.
Until now a comment's reply could only be given by closing it (resolve line=). `comment <thing> id=<cNN> line=...`
adds a reply under that comment and leaves it open; it calls the original conversation partners; undo
takes that one reply away; the comments rows carry the thread. Builds its own small world (roomworld.py).
"""
import os
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import roomworld   # noqa: E402
import scene       # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build(say=False)
W = D.world


def say(me, *lines):
    W.me = me
    per = D._per
    if me not in per:
        per[me] = ({}, {W.root}, len(W.events))
    D.seen, D.open, D.last_event_seen = per[me]
    D._window = ""
    token, out = uuid.uuid4().hex, []
    for line in lines:
        r = D.dispatch("desk", {"line": line, "whole": True, "reply": token})
        out.append((r.get("text") or "", r.get("error") or ""))
        if r.get("error"):
            break
    return out


A, B = "juniper", "pike"
CORNER = R.corner[A]
txt, err = say(A, f"look {CORNER} :1", f'do create {CORNER} kind=note title="a paragraph" text="A change is a room."')[-1]
NOTE = W.last_created
check("a note to comment on", NOTE and not err, txt + err)
txt, err = say(A, f"read {NOTE}", f'do comment {NOTE} line="is this restrictive?"')[-1]
s = W.subjects[W.nodes[NOTE]["subject"]] if NOTE in getattr(W, "nodes", {}) else next(x for x in W.subjects.values() if x["comments"])
CID = s["comments"][0]["id"]
check("the comment is made", not err and CID.startswith("c"), txt + err)

txt, err = say(B, f"read {NOTE}", f'do comment {NOTE} id={CID} line="a room may hold many things."')[-1]
c = s["comments"][0]
check("a reply lands under the comment", not err and c["replies"] == [{"by": B, "text": "a room may hold many things."}], txt + err)
check("the comment stays open", c["resolved"] is False)
check("the reply calls the comment's writer", W.events[-1].get("to") == [A], W.events[-1].get("to"))
check("the receipt says so", "stays open" in txt and A in txt, txt)

txt, err = say(A, f"read {NOTE}", f'do comment {NOTE} id={CID} line="then say so in the design."')[-1]
check("a second reply calls the first replier, not its own writer", not err and W.events[-1].get("to") == [B], (txt, err, W.events[-1].get("to")))
txt, err = say(A, f"read {NOTE}")[-1]
check("read prints the thread, each reply signed", "a room may hold many things." in txt and "then say so in the design." in txt and "(open)" in txt, txt)
rows = scene.rows(D, f"comments:{NOTE}")
if rows:
    check("the comments rows carry the thread", rows[0]["replies"].count("\n") == 1 and rows[0]["replies"].startswith(f"{B}: "), rows)

txt, err = say(A, "undo")[-1]
check("undo takes back that one reply", not err and len(c["replies"]) == 1 and c["resolved"] is False, (txt, err, c))
txt, err = say(B, f'do comment {NOTE} id=c99999 line="x"')[-1]
check("a reply to no comment is refused in words", "is not a comment on" in (txt + err), txt + err)
say(A, f"read {NOTE}", f"do resolve {NOTE} id={CID}")
txt, err = say(B, f"read {NOTE}", f'do comment {NOTE} id={CID} line="late"')[-1]
check("a reply to a resolved comment is refused in words", "is resolved" in (txt + err), txt + err)

print(f"\n{len(fails)} failed" if fails else "\nall passed")
sys.exit(1 if fails else 0)
