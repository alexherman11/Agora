"""test_sayings (a3319, lines phase 2): one showing lists chat lines and comments as they are, and For you asks it.

    python test_sayings.py

Builds its own small world in memory (roomworld.py) and never saves it; every desk line runs through the desk's own
dispatch. Checks, by the card's goals: (i) a comment opening '@alex: ...' on a card shows in Alex's For you naming
the card, and an answer addressed to its writer lands as a comment on the card and reaches them; (ii) For you is
`sayings for:<name>`, a lens draws it with no inbox: source, and inbox:<name> is the same rows under its first name;
(iii) a headerless worker comment on a commission still knocks whoever asked and is not in their For you; (iv) no
comment's id, text or resolved state changes by being listed, and a comment from before the rule (no stored
address) is never counted; (v) the showing asks rooms.calls: changing it changes the rows, with no lens edit; and the
endings: you answer (a reply, or a later comment on the thing), or the writer withdraws; someone else's resolve
doesn't end it for you.
"""
import copy
import os
import re
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import persons     # noqa: E402
import rooms       # noqa: E402
import roomworld   # noqa: E402
import scene       # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build()
W = D.world


def be(me):
    per = D._per = getattr(D, "_per", None) or {}
    W.me = me
    if me not in per:
        per[me] = ({}, {W.root}, len(W.events))
    D.seen, D.open, D.last_event_seen = per[me]
    D._window = ""


def say(me, line, whole=True):
    be(me)
    r = D.dispatch("desk", {"line": line, "whole": whole, "reply": uuid.uuid4().hex})
    return (r.get("text") or "") + (("\nERROR " + r["error"]) if r.get("error") else "")


def comment(me, thing, words):
    """-> (comment id, its event, the receipt)"""
    say(me, f"read {thing}")
    t = say(me, f"do comment {thing} line=\"{words}\"")
    m = re.search(r"comment (c\d+) added", t)
    if not m:
        raise RuntimeError(f"no comment was made: {t}")
    return m.group(1), persons.comment_events(W)[m.group(1)], t


def rows(src):
    return scene.rows(D, src)


def row(src, saying):
    return next((r for r in rows(src) if r["saying"] == saying), None)


TALK = R.TALK[R.LOUNGE]
CARD = R.CARDS[0]
TITLE = W.subjects[W.nodes[CARD]["subject"]]["title"]
say("alex", f"look {R.DESKTOP} :1")
say("alex", f"do prop {R.DESKTOP} person=alex")            # as the live world: Alex is the person at the Desktop
say("jeff", f"look {CARD}")
say("jeff", f"do prop {CARD} asked_by=juniper commission=working")
check("the world knows Alex as a person", rooms.someone(W, "alex") == "person", rooms.someone(W, "alex"))

# ---- (iv) a comment from before the rule has no stored address, and is never counted ---------------------------
old, old_ev, _ = comment("pike", CARD, "@alex: written before the rule, with his name first")
old_ev.pop("to")                                           # as every comment made before a3319 is stored
check("day one: a comment with no stored address is not in For you, though it opens with his name",
      row("sayings for:alex", old) is None, rows("sayings for:alex"))
r = row(f"sayings in:{CARD}", old)
check("it is still a saying of its thing, as it was: its id, its words, to nobody",
      r and r["what"] == "comment" and r["said"].startswith("@alex: written before") and r["to"] == "" and r["answered"] == "", r)

# ---- (i) a comment that opens with his name shows in For you, naming the card ----------------------------------
cid, ev, t = comment("pike", CARD, "@alex: which of the two cards first?")
check("the comment's receipt says to: alex", "to: alex" in t, t)
check("whom it addresses is stored on its event, beside its args (the house tells residents every string arg)",
      ev.get("to") == ["alex"] and "to" not in ev["args"], ev)
r = row("sayings for:alex", cid)
check("(i) it shows in Alex's For you, naming the card, by its own id (no new id)",
      r and r["what"] == "comment" and r["in"] == TITLE and r["item"] == CARD and r["by"] == "Pike" and r["name"] == "pike"
      and r["to"] == "alex" and r["answered"] == "no" and r["state"] == "open" and r["eid"] == ev["id"] and r["at"], r)
check("and not in anyone else's", row("sayings for:sable", cid) is None and row("sayings for:pike", cid) is None, "")
mid_c, _, t = comment("pike", CARD, "as I said to @alex, the first card is nearly done")
check("a mid-line @alex in a comment is a mention: stored to nobody, not shown",
      W.events[-1].get("to") == [] and row("sayings for:alex", mid_c) is None, (t, W.events[-1]))
typo, tev, _ = comment("pike", CARD, "@alexx @everyone: nobody by that name, and no broadcast outside a chat line")
check("a name that is no one, and @everyone, are not stored as a comment's address", tev.get("to") == [], tev)

# ---- (iii) called is not shown ---------------------------------------------------------------------------------
wc, wev, _ = comment("worker-a1", CARD, "report: the tests pass, nothing else was checked")
check("(iii) a headerless worker comment on Juniper's commission still knocks her",
      rooms.reached(W, wev).get("juniper") == "call", rooms.reached(W, wev))
check("(iii) and is not in her For you", row("sayings for:juniper", wc) is None, rows("sayings for:juniper"))
hc, hev, _ = comment("pike", R.corner_desc["sable"], "a note left on a thing in Sable's corner")
check("a headerless comment on a thing in Sable's corner knocks her and is not shown",
      rooms.reached(W, hev).get("sable") == "call" and row("sayings for:sable", hc) is None, rooms.reached(W, hev))

# ---- endings: someone else's resolve doesn't end it; your answer does ------------------------------------------
before = copy.deepcopy([(c["id"], c["text"], c["resolved"]) for s in W.subjects.values() for c in s["comments"]])
say("sable", f"read {CARD}")
t = say("sable", f"do resolve {CARD} id={cid}")
r = row("sayings for:alex", cid)
check("someone else's resolve does not end it for Alex: still unanswered, and the row says who resolved it",
      "resolved" in t and r and r["answered"] == "no" and r["state"] == "resolved by Sable", (t, r))
say("alex", f"read {CARD}")
t = say("alex", f"do resolve {CARD} id={cid} line=\"too late\"")
check("a resolved comment takes no reply (so his answer is a new comment on the thing)", "already resolved" in t, t)
ans, aev, t = comment("alex", CARD, "@pike: the first one")
r = row("sayings for:alex", cid)
check("(i) his answer is a comment on the card, addressed to the asker, and the question is answered",
      ans and r and r["answered"] == "yes" and W.subjects[W.nodes[CARD]["subject"]]["comments"][-1]["id"] == ans, (t, r))
check("and it reaches the asker by the header rule: the knock reads it as a call, and it is in Pike's For you",
      rooms.reached(W, aev).get("pike") == "call" and row("sayings for:pike", ans) is not None, rooms.reached(W, aev))

q2, _, _ = comment("pike", R.CARDS[1], "@alex: and a second question")
say("alex", f"read {R.CARDS[1]}")
t = say("alex", f"do resolve {R.CARDS[1]} id={q2} line=\"yes, that one\"")
r = row("sayings for:alex", q2)
check("a reply by him (a resolve with words) answers it", r and r["answered"] == "yes", (t, r))
q3, _, _ = comment("pike", R.NOTE, "@alex: a question I will take back")
say("pike", f"read {R.NOTE}")
say("pike", f"do resolve {R.NOTE} id={q3}")
r = row("sayings for:alex", q3)
check("its writer's own resolve withdraws it", r and r["answered"] == "withdrawn" and r["state"] == "withdrawn", r)
q4, q4ev, _ = comment("pike", R.NOTE, "@alex: one made by mistake")
say("pike", f"undo {q4ev['id']}")
check("an undone comment is gone from For you", row("sayings for:alex", q4) is None, rows("sayings for:alex"))

# ---- (iv) nothing was changed by listing ------------------------------------------------------------------------
now = {c["id"]: (c["id"], c["text"], c["resolved"]) for s in W.subjects.values() for c in s["comments"]}
moved = [b for b in before if b[0] != cid and now.get(b[0]) != b]
check("(iv) no comment's id, text or resolved state changed, but the one Sable resolved", not moved and now[cid][2] is True, moved)
check("(iv) comments and lines keep their ids; a reply has its thread and stable ordinal",
      all(re.fullmatch({"comment": r"c\d+", "line": r"m\d+", "reply": r"c\d+/reply/\d+"}[r["what"]], r["saying"])
          for r in rows("sayings")), [r["saying"] for r in rows("sayings")][:40])

# ---- chat lines are sayings too, read as For you always read them ----------------------------------------------
t = say("sable", f'do append {TALK} line="@alex the couches arrived"')
lm = re.search(r"line (m\d+)", t).group(1)
r = row("sayings for:alex", lm)
check("a chat line addressed to Alex is in the same list, as a line",
      r and r["what"] == "line" and r["in"] == "Lounge talk" and r["by"] == "Sable" and r["answered"] == "no" and r["to"] == "alex", r)
say("sable", f'do append {TALK} line="@everyone a broadcast"')
check("an address to everyone is left out of For you, as before",
      not any("a broadcast" in r["said"] for r in rows("sayings for:alex")), "")
say("alex", f'do append {TALK} line="thank you"')
check("a line of his after it answers it (who wrote last)", row("sayings for:alex", lm)["answered"] == "yes", row("sayings for:alex", lm))
say("alex", f"look {R.DESKTOP} :1")
t = say("alex", f'do create {R.DESKTOP} kind=chat title="Talk with Alex, Pike" members=alex,pike')
DM = re.search(r"created (a\d+)", t).group(1)
say("pike", f"look {DM}")
t = say("pike", f'do append {DM} line="a plain line, no header"')
dm = re.search(r"line (m\d+)", t).group(1)
check("every line of a direct chat shows, addressed or not, and not for someone outside it",
      row("sayings for:alex", dm) is not None and row("sayings for:sable", dm) is None, rows("sayings for:alex")[-2:])
t = say("alex", f"rows sayings in:{TALK}")
check("rows sayings in:<chat> lists that chat's lines only", "what=line" in t and "what=comment" not in t and lm in t, t[:600])
both = rows("sayings for:alex")
check("one list holds both kinds, oldest first",
      {r["what"] for r in both} == {"line", "comment"} and [r["eid"] for r in both] == sorted((r["eid"] for r in both), key=scene._enum),
      [(r["eid"], r["what"]) for r in both])

# ---- (ii) inbox:<name> is the same rows, and a lens draws For you with no inbox: source ------------------------
old_rows = rows("inbox:alex")
check("(ii) inbox:<name> is sayings for:<name> under its first name, with the fields its rows had",
      [r["eid"] for r in old_rows] == [r["eid"] for r in both]
      and all(r["chat"] == r["in"] and r["who"] == r["by"] and r["open"] == ("yes" if r["answered"] == "no" else "no") for r in old_rows),
      old_rows[:2])
say("alex", f"look {R.HOME} :1")
LENS = ('page : column, of sayings for:$me, each fy\\n'
        'fy : column\\n'
        '  fyh : row, role mark when $answered = no\\n'
        '    fyc : text \\"$in\\"\\n'
        '    fyw : text \\"$by\\"\\n'
        '    fyr : text \\"$state\\", only when $state has resolved\\n'
        '  fys : text \\"$said\\"\\n'
        '  fyl : column, only when $what = line\\n'
        '    fya : text \\"\\", hint \\"answer\\", on edit do append $item line=\\"$value\\", only when $answered = no\\n'
        '  fyk : column, only when $what = comment\\n'
        '    fyq : text \\"\\", hint \\"answer on the card\\", on edit do comment $item line=\\"@$name: $value\\", only when $answered = no')
t = say("alex", f'do create {R.HOME} kind=note title=for-me tags=lens text="{LENS}"')
check("the For you lens compiles", "compiles" in t and "ERROR" not in t, t[-600:])
q5, _, _ = comment("juniper", R.CARDS[1], "@alex: a third question, open now")
t = say("alex", "scene for-me")
check("(ii) a lens with no inbox: source shows the comment, names its card, and offers an answer on the card",
      "inbox:" not in LENS and "a third question, open now" in t and "Card two" in t
      and f'do comment {R.CARDS[1]} line="@juniper: $value"' in t, t[-1800:])
check("and a line's answer box still appends to its chat", f"do append {DM} line=\"$value\"" in t, t[-1800:])

# ---- (v) the showing asks the house's rule ---------------------------------------------------------------------
n = len(rows("sayings for:alex"))
real = rooms.calls
try:
    rooms.calls = lambda w, s, to, actor: False
    quiet = rows("sayings for:alex")
    t_quiet = say("alex", "scene for-me")
finally:
    rooms.calls = real
check("(v) change rooms.calls and what the term lists changes: only the direct chat's lines are left",
      0 < len(quiet) < n and all(r["item"] == DM for r in quiet), [(r["in"], r["saying"]) for r in quiet])
check("(v) and the lens shows the change with no lens edit", "a third question, open now" not in t_quiet, t_quiet[-900:])
check("with the rule back, the rows are back", len(rows("sayings for:alex")) == n, "")

# ---- refusals and persons --------------------------------------------------------------------------------------
t = say("alex", "rows sayings calls:alex")
check("an unknown term is refused, naming the terms", "unknown term" in t and "for:<name>" in t, t)
check("help's list of sources names sayings", "sayings [for:<name>] [in:<id>]" in say("alex", "rows nothing"), say("alex", "rows nothing"))
say("jeff", "person begin")
if persons.on(W):
    r = row("sayings for:alex", q5)
    check("after person begin, the same rows: a comment's author is its event's person, and his own are still left out",
          r and r["by"] == "Juniper" and len(rows("sayings for:alex")) == n and row("sayings for:alex", ans) is None, r)

print("\n" + ("all ok" if not fails else f"{len(fails)} FAILED: " + "; ".join(fails)))
sys.exit(1 if fails else 0)
