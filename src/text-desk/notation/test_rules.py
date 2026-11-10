# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_rules (a1027): rules become quiet notes; scripts retire into verbs.

    python test_rules.py

Builds its own small world (roomworld.py), in memory, never saved. The rule the three residents asked for without
comparing notes (Juniper e1957, Sable e1958, Pike e1959) is written as three rule notes, by juniper, in a Rules
surface on the Board; then the house lands a commission, as it does (look; do prop commission=landed landed=<head>),
and each line of the commission's 'done when' is checked.

a3029: until then it read a copy of the live world, and 'a narrated look never lists rule notes' failed once the
Board held more than its look shows (the Rules surface fell into '+12 more'). What the live world lent it is made
here: a Rough spots surface with an open spot claude found, a commission that landed before any rule, and the old
script 'arrive' a world from before a1027 still holds.
"""
import os
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:2000]}"))
    if not ok:
        fails.append(name)


import roomworld   # noqa: E402

D, R = roomworld.build()
W = D.world


def be(me):
    per = D._per = getattr(D, "_per", None) or {}
    W.me = me
    if me not in per:
        per[me] = ({}, {W.root}, len(W.events))
    D.seen, D.open, D.last_event_seen = per[me]
    D._window = ""


def reply(me, *lines):
    be(me)
    token, out = uuid.uuid4().hex, []
    for line in lines:
        r = D.dispatch("desk", {"line": line, "whole": True, "reply": token})
        out.append((line, r.get("text") or "", r.get("error") or ""))
        if r.get("error"):
            break
    return out


def said(me, *lines):
    """Lines in one reply -> (text, error) of the last, without the '!! since your last look' catch-up."""
    _, text, err = reply(me, *lines)[-1]
    strip = lambda t: "\n".join(l for l in t.splitlines() if not l.startswith(("!!", "   ")))
    return strip(text), strip(err)


import rooms   # noqa: E402

BOARD, LOUNGE = R.BOARD, R.LOUNGE
SABLE, PIKE, JUNIPER = (R.corner[a] for a in ("sable", "pike", "juniper"))
# what the live world lent this test until a3029, made here: Rough spots with an open spot claude found (claude has no
# corner, so no sill), a commission the house landed before any rule was written, and an old script from before a1027
reply("jeff", f"look {BOARD} :1", f'do create {BOARD} kind=surface title="Rough spots"')
SPOTS = W.last_created
reply("claude", f"look {SPOTS} :1", f'do create {SPOTS} kind=note title="A spot claude found" family=silence status=open text=x')
OLD = reply("house", f"look {BOARD} :1", f'do create {BOARD} kind=task title="An old commission" asked_by=pike '
            f'commission=landed landed=0000000 text=x')[-1]
assert not OLD[2], OLD
D.scripts = {"arrive": "look"}       # a world from before a1027 still holds its scripts; they never run
print(f"world (built, in memory): Board {BOARD}, Lounge {LOUNGE}, Rough spots {SPOTS}, corners {SABLE} {PIKE} {JUNIPER}")


def subj(nid):
    return W.subjects[W.nodes[nid]["subject"]]


def prop(nid, k):
    return (subj(nid).get("props") or {}).get(k)


def made_in(fid, title):
    return [k["id"] for k in W.children(fid) if k["type"] == "appearance" and subj(k["id"])["title"] == title]


def q(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


# ---- the three rules, as juniper writes them ------------------------------------------------------------------------
R1 = ('when kind:task,prop:commission=landed do create corner:$item.asked_by kind=note '
      'title="your live check is due: $item.title" text="$item landed as $item.landed. Live it, and say what you found on $item."')
R2 = "when kind:task,prop:commission=landed do prop answered-by:$item,prop:family,-prop:status=cured,-prop:status=curing status=curing"
R3 = ('when prop:family,prop:status=curing do create corner:$item.maker kind=note title="your live check is due: $item.title" '
      'text="$item is curing: a fix for what you found is in. Live it, and set it cured when it holds (cured is a person\'s word)."')

got = reply("juniper", f"go {BOARD} :1", f"look {BOARD} :1", f"do create {BOARD} kind=surface title=Rules layout=column")
check("juniper makes a Rules surface on the Board", not got[-1][2], got[-1])
RULES = W.last_created


def write_rule(me, title, text, where=None):
    got = reply(me, f"look {where or RULES} :1", f"do create {where or RULES} kind=note tags=rule title={q(title)} text={q(text)}")
    return W.last_created, got[-1][1], got[-1][2]


r1, t1, e1 = write_rule("juniper", "A landed commission: the asker's live check is due", "# Juniper e1957, Sable e1958, Pike e1959\n" + R1)
check("a rule note is saved and says so: its home, who it acts as, what already matches", not e1 and f"~ rule {r1} saved: when kind:task" in t1
      and f"lives in Board ({BOARD})" in t1 and "acts as juniper" in t1 and "already match, counted as handled" in t1, e1 or t1)
r2, t2, e2 = write_rule("juniper", "A landed commission cures what it answers (curing, never cured)", R2)
r3, t3, e3 = write_rule("juniper", "A rough spot curing: its reporter's live check is due", R3)
check("the other two are saved", not e2 and not e3 and "saved:" in t2 and "saved:" in t3, (e2 or t2, e3 or t3))

typo, tt, te = write_rule("juniper", "A typo", R1.replace("do create", "do craete"))
check("a rule with a typo is still saved, marked broken with the reason", not te and f"~ rule {typo} saved broken:" in tt
      and "craete is not a verb" in tt and "never fires until its text is fixed" in tt, te or tt)
typo2, tt2, _ = write_rule("juniper", "A typo in a term", R1.replace("prop:commission", "prp:commission"))
check("a misspelled selection term is broken too, naming the term", "saved broken" in tt2 and "prp" in tt2, tt2)
typo3, tt3, _ = write_rule("juniper", "A typo in a blank", R1.replace("$item.asked_by", "$itme.asked_by"))
check("a misspelled blank is broken too", "saved broken" in tt3 and "$itme" in tt3, tt3)
typo4, tt4, _ = write_rule("juniper", "A typo in a target", R2.replace("answered-by:", "answred-by:"))
check("a misspelled term in a selection target is broken too, not read as a prop", "saved broken" in tt4 and "answred-by" in tt4, tt4)

# ---- quiet ------------------------------------------------------------------------------------------------------------
# a3029: r1 sits inside the Rules surface, where a narrated look never reaches anyway; a rule note held by the Board
# itself is the one the look must leave out, beside a card it must still list
rq, tq, eq = write_rule("juniper", "A rule in the room itself", "when tag:quiet-probe do tag add=heard", where=BOARD)
t, e = said("juniper", f"go {BOARD} :1", "look")
check("a narrated look never lists rule notes", not e and rq not in t and r1 not in t and RULES in t and R.CARDS[0] in t, e or eq or t)
t, e = said("juniper", f"look {RULES} :2")
check("the tree marks them as rules, a broken one as broken", f"{r1} note" in t and "· rule ·" in t
      and "rule, broken (rules says why)" in t, t)
t, e = said("pike", "rules")
check("rules lists every one: home, author, fired, broken", not e and all(x in t for x in (r1, r2, r3, typo))
      and f"lives in Board ({BOARD}) · acts as juniper · fired 0x" in t and "BROKEN: craete is not a verb" in t, e or t)
t, e = said("pike", f"examine {r1}")
check("examine on a rule note says the same", not e and "a rule (its home is the room holding it" in t
      and "acts as juniper · fired 0x" in t, e or t)

# ---- a commission that answers two rough spots lands ----------------------------------------------------------------
got = reply("pike", f"look {SPOTS} :1", f'do create {SPOTS} kind=note title="A probe spot, found by Pike" family=silence status=open text=x')
SPOT = W.last_created
CLAUDE = next(k["id"] for k in W.children(SPOTS) if k["type"] == "appearance" and prop(k["id"], "status") == "open"
              and __import__("verbs")._author(W, subj(k["id"])["id"]) == "claude")
got = reply("sable", f"look {SABLE} :1", f'do create {SABLE} kind=task title="Probe: a fix for two spots" asked_by=sable text=x',
            f"look {SPOT} :1", f"do link $new {SPOT} as=answers")
TASK = next(i for i in made_in(SABLE, "Probe: a fix for two spots"))
got += reply("sable", f"look {CLAUDE} :1", f"look {TASK} :1", f"do link {TASK} {CLAUDE} as=answers")
check("sable's task answers pike's spot and one claude made", not any(x[2] for x in got), got)
t = reply("sable", f"find answered-by:{TASK}")[-1][1]
check("answered-by: finds what a task answers", SPOT in t and CLAUDE in t, t)
t = reply("sable", f"find answers:{SPOT}")[-1][1]
check("answers: finds what answers a spot", TASK in t, t)

n0 = len(W.events)
got = reply("house", f"look {TASK} :1", f"do prop {TASK} commission=landed landed=abc1234")
land_ev = next(ev["id"] for ev in W.events[n0:] if ev["verb"] == "prop" and ev["target"] == TASK)
receipt = got[-1][1]
print("     the house's receipt:\n" + "\n".join("       " + l for l in receipt.splitlines() if l.startswith("~")))
sill = made_in(SABLE, "your live check is due: Probe: a fix for two spots")
check("landed: a note on the asker's sill, 'your live check is due: <title>'", len(sill) == 1, receipt)
sill_s = subj(sill[0]) if sill else {}
check("its text is filled when it fires ($item.landed)", "landed as abc1234" in sill_s.get("text", ""), sill_s.get("text"))
ev = next((x for x in W.events[n0:] if x["verb"] == "create" and (x.get("undo") or {}).get("delete") in sill), {})
check("it fires as its author, from its home, recorded via=rule and tripped by the house",
      ev.get("by") == "juniper" and ev.get("via") == f"rule {r1}" and ev.get("tripped_by") == "house" and ev.get("cause") == land_ev, ev)
check("the spot it answers is set to curing", prop(SPOT, "status") == "curing", prop(SPOT, "status"))
psill = made_in(PIKE, "your live check is due: A probe spot, found by Pike")
check("and the same note lands on the reporter's sill", len(psill) == 1, receipt)
check("the spot claude made goes curing too, and finds no sill: skipped quietly", prop(CLAUDE, "status") == "curing"
      and "no sill" not in receipt and "could not" not in receipt, receipt)
check("never cured: cured stays a person's word", "cured" not in {prop(SPOT, "status"), prop(CLAUDE, "status")})
check("the commission that landed before the rule was written fired nothing (it was counted as handled)",
      not made_in(PIKE, "your live check is due: An old commission"), receipt)
check("the broken rules did not fire", f"~ {typo} " not in receipt and f"~ {typo2} " not in receipt and f"~ {typo3} " not in receipt, receipt)
t, e = said("pike", "rules")
check("rules shows what fired, and the quiet skip", f"{r1} " in t and "fired 1x" in t and f"skipped 1x (last: {CLAUDE}, no sill for 'claude')" in t, t)

# ---- undo reverses a firing ------------------------------------------------------------------------------------------
t, e = said("house", f"undo {land_ev}")
check("undo of the command that set them off undoes the firings too, and says so", not e and "rule consequence(s): " in t
      and not made_in(SABLE, "your live check is due: Probe: a fix for two spots")
      and not made_in(PIKE, "your live check is due: A probe spot, found by Pike")
      and prop(SPOT, "status") == "open" and prop(CLAUDE, "status") == "open" and prop(TASK, "commission") is None, e or t)

# ---- landed, reverted, landed again: the asker is told twice -------------------------------------------------------
reply("house", f"look {TASK} :1", f"do prop {TASK} commission=landed landed=abc1234")
reply("house", f"look {TASK} :1", f"do prop {TASK} commission=reverted")
reply("house", f"look {TASK} :1", f"do prop {TASK} commission=landed landed=def5678")
again = [subj(a)["text"] for a in made_in(SABLE, "your live check is due: Probe: a fix for two spots")]
check("a commission that lands, is reverted and lands again fires again: it entered the selection twice",
      len(again) == 2 and any("def5678" in x for x in again), again)

# ---- moving the rule note moves its home ------------------------------------------------------------------------------
rh, th, eh = write_rule("juniper", "Things tagged herenow come here", "when tag:herenow do move into=$here")
check("a rule using $here lives in the Board", f"lives in Board ({BOARD})" in th, eh or th)
got = reply("juniper", f"look {rh} :1", f"look {LOUNGE} :1", f"do move {rh} into={LOUNGE}")
check("moving the note moves its home, and the receipt says so", not got[-1][2] and f"~ rule {rh} saved" in got[-1][1]
      and f"lives in Lounge ({LOUNGE})" in got[-1][1], got[-1])
got = reply("pike", f"look {SPOT} :1", f"do tag {SPOT} add=herenow")
check("it acts from its new home: $here is the Lounge", W.nodes[SPOT]["parent"] == LOUNGE, got[-1])
t, e = said("pike", "look")
check("still quiet in the Lounge's narrated look", rh not in t, t)

# ---- a fixed rule re-arms; a new author is told ----------------------------------------------------------------------
got = reply("pike", f"read {typo}", f'do replace {typo} old="do craete" new="do create"')
check("fixing a typo saves the rule, re-armed, and tells its new author it acts as them", not got[-1][2]
      and f"~ rule {typo} saved" in got[-1][1] and "this rule now acts as you (it acted as juniper)" in got[-1][1], got[-1])
t, e = said("pike", "rules")
check("rules names the new author", f'{typo} "A typo" · lives in Board ({BOARD}) · acts as pike' in t, t)

# ---- an event rule still fires as its author --------------------------------------------------------------------------
LT = W.nodes[LOUNGE]["props"]["talk"]
ro, to_, eo = write_rule("sable", "Pike's lines in the Lounge get a mark", "on append by=pike do prop marked=pike")
got = reply("pike", f"do append {LT} line=\"hello from the probe\"")
evs = [x for x in W.events[-3:] if x["verb"] == "prop" and x.get("via") == f"rule {ro}"]
check("on <verb> by=<actor> fires as its author (sable), tripped by pike", evs and evs[0]["by"] == "sable"
      and evs[0].get("tripped_by") == "pike", got[-1])

# ---- the old doors ----------------------------------------------------------------------------------------------------
t, e = said("juniper", "rule when tag:x do tag add=y")
check("rule when ... refuses and gives the exact create line", "rules are notes now" in e
      and 'do create $here kind=note tags=rule title="<what it does>" text="when tag:x do tag add=y"' in e, e or t)
t, e = said("juniper", "script morning = look")
check("script refuses, naming the door", "scripts are verbs now: make a note tagged verb" in e and "run X is just X" in e, e or t)
t, e = said("juniper", "run arrive")
check("run refuses, naming the door: run arrive is just arrive", "run arrive is just arrive" in e, e or t)
t, e = said("juniper", "scripts")
check("scripts says so too, and names the old one that never runs", "scripts are verbs now" in t and "arrive" in t, e or t)
t, e = said("juniper", "look corner:sable :1")
check("corner:<name> is someone's corner, anywhere a target goes", SABLE in t, e or t)
t, e = said("juniper", "look corner:claude :1")
check("corner: of a name with no corner says no sill", "no sill for 'claude'" in e, e or t)

print(f"\n{'all passed' if not fails else str(len(fails)) + ' FAILED'}")
sys.exit(1 if fails else 0)
