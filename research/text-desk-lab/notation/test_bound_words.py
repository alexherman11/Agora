"""test_bound_words (a1156, from a1147): stored lines bind their words when saved; nothing takes over a word later.

    python test_bound_words.py

Builds its own small world (roomworld.py), in memory, never saved. Each check is a line of the commission's 'done
when', or of Juniper's c1337 (a room may stand over a word only out loud: overrides=<id>), tried on a house trash verb,
the lens acts that use it, and the residents' corners and sills.

a3029: until then it read a copy of the live world, whose two trash lenses happened to be written by sable (the one
who changes trash here, told on the receipt) and by someone with no sill (told on the receipt too). When pike became
the Desktop lens's last writer, pike was told on their sill, which the check did not look at, and it failed. Here the
three kinds of author are made on purpose: the changer, one with a sill, one without.
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
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
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


def last(me, *lines):
    """-> (text, error) of the last line run."""
    got = reply(me, *lines)
    return got[-1][1], got[-1][2]


import rooms   # noqa: E402
import verbs   # noqa: E402

LOUNGE, BOARD = R.LOUNGE, R.BOARD
JC, PC = R.corner["juniper"], R.corner["pike"]
print(f"world (built, in memory): Lounge {LOUNGE}, Board {BOARD}, Juniper's corner {JC}, Pike's corner {PC}")


def make(me, fid, title, text="x", extra=""):
    """A note made in one act, text and all (no rewrite: the read fence would want a read first). -> (id, text, err)"""
    t, e = last(me, f"look {fid} :1", f'do create {fid} kind=note title="{title}" text="{text}" {extra}'.strip())
    return (W.last_created if not e else None), t, e


def prop(nid, key):
    n = W.nodes[nid]
    return ((W.subjects[n["subject"]] if n.get("subject") else n).get("props") or {}).get(key)


def subj(aid):
    return W.subjects[W.nodes[aid]["subject"]]


def sill_notes(who, title):
    fid = rooms.corner_of(W, who)
    return [k["id"] for k in W.children(fid) if k.get("subject") and W.subjects[k["subject"]]["title"] == title]


# ---- the world before a1156: a house trash verb, and lenses whose acts use it -------------------------------------
# as the live world had them (a1174 trash, a589 command-center, a1180 trash-probe, a134 p-gesture), each lens written by
# someone chosen: sable will change trash (told on the receipt), pike has a sill (told there), claude has none (the
# receipt says so). Their texts are put in memory, as lines saved before bindings were
last("jeff", f"look {R.HOME} :1", f'do create {R.HOME} kind=surface title=Trash')
TRASHF = W.last_created
make("juniper", R.HOME, "trash", f"# put a thing in the Trash: trash <id>\\ndo prop $1 status=trashed\\ndo move $1 into={TRASHF}",
     "tags=verb on=house")
LENS_TEXT = {
    "desk-board": ("pike", 'board : column, of tag:probe, each card\ncard : text "$title", on menu "delete" do trash $item'),
    "trash-probe": ("sable", f'probe : column, the {R.NOTE}\n  x : text "delete", role tool, on click do trash $item\n'
                             f'  y : text "$title"'),
    "guest-bin": ("claude", 'bin : column, of tag:probe, each b\nb : text "$title", role tool, on click do trash $item'),
    "p-gesture": ("sable", 'root : column\n  list : of tag:probe, each card\ncard : text "$title $beds", '
                           'on click do prop $item beds=9; prop $item color=red'),
}
for title, (who, text) in LENS_TEXT.items():
    lid, t, e = make(who, R.DESKTOP, title, "x", "tags=lens")
    assert lid, (title, e)
    subj(lid)["text"] = text

# ---- the lines saved before bindings bind once, to what they mean now ---------------------------------------------
# start from the world as it is before landing, with no binding anywhere
W._binds_version = 0
for s in W.subjects.values():
    s.pop("binds", None)
for n in W.nodes.values():
    n.pop("binds", None)
lenses = [s for s in W.subjects.values() if "lens" in (s.get("tags") or []) and W.appearances_of(s["id"])]
lens_acts = [s for s in lenses if any(wd == "trash" for wd, _, _ in verbs.line_words(D, "lens", s["text"]))]
bare = [s for s in lenses if any(wd == "prop" for wd, _, _ in verbs.line_words(D, "lens", s["text"]))]
TRASH = next(s for s in verbs.all_verbs(W) if verbs._names(s["title"]) == ["trash"])
TA = W.appearances_of(TRASH["id"])[0]
check("before the first line after landing, no stored line here is bound",
      not any(s.get("binds") for s in W.subjects.values()) and lens_acts, [s["title"] for s in lens_acts])
n0 = len(W.events)
last("juniper", "look")
cc = [s for s in lens_acts if s.get("binds")]
bev = [e for e in W.events[n0:] if e["verb"] == "bind"]
check("it is one event by the house, naming every holder it bound (Juniper c1421: never quietly)",
      len(bev) == 1 and bev[0]["by"] == "house" and all(W.appearances_of(s["id"])[0] in bev[0]["args"]["holders"] for s in cc),
      W.events[n0:])
if bev:
    print("     " + bev[0]["note"][:260])
t, e = last("sable", f"history {W.appearances_of(cc[0]['id'])[0]}") if cc else ("", "")
check("... and history on a bound lens shows it", "bind" in t and "house" in t, e or t)
t, e = last("juniper", f"undo {bev[0]['id']}") if bev else ("", "no event")
check("undo of it takes the bindings back", not e and not any(s.get("binds") for s in cc), e or t)
W._binds_version = 0
last("juniper", "look")
cc = [s for s in lens_acts if s.get("binds")]
check("after it, every lens whose acts use a world verb is bound, to the verb it meant (trash)",
      len(cc) == len(lens_acts) and all(s["binds"]["words"].get("trash", {}).get("id") == TRASH["id"] for s in cc),
      [(s["title"], s.get("binds")) for s in lens_acts])
for s in cc:
    print(f"     {W.appearances_of(s['id'])[0]} {s['title']!r}: trash -> {s['binds']['words']['trash']['at']} (as {s['binds']['by']})")
# p-gesture's `on click do prop $item beds=9; prop $item color=red`: the compiler puts do before the first step only,
# so the second was always a bare prop, which nothing answers. It is kept unbound, saying why
check("a lens act with a bare built-in word (prop) is kept unbound, saying a stored line says do prop",
      all("do prop" in (s.get("binds") or {}).get("missing", {}).get("prop", "") for s in bare), [s.get("binds") for s in bare])

# ---- (4) a world verb never takes a built-in's word ---------------------------------------------------------------
for word in ("append", "prop", "look", "go", "delete"):
    vid, t, e = make("pike", PC, word, f"do append {PC} line=hijacked", "tags=verb on=house")
    check(f"a world verb titled {word} is refused when made, naming the built-in", e and "a word the desk itself answers" in e
          and not vid, e or t)
vid, t, e = make("pike", PC, "tidy", "do prop $1 tidied=pike", "tags=verb")
check("a retired built-in's word (tidy) may still be a world verb (a990), carried by its maker", vid and not e, e)
PT = vid
# renaming into a built-in's word is the same act
t, e = last("pike", f"read {PT} :3", f'do retitle {PT} title=append')
check("... and renaming one to a built-in's word is refused", e and "a word the desk itself answers" in e, e or t)
t, e = last("pike", f"look {PT} :1", f"do remove {PT}")

# ---- (4) a word another verb answers where it would live: refused, unless it says overrides= ------------------------
HV, t, e = make("juniper", JC, "polish", "do prop $1 polished=house", "tags=verb on=house")
check("Juniper makes a house verb, polish", HV and not e, e)
LV, t, e = make("pike", LOUNGE, "polish", "do prop $1 polished=lounge", f"tags=verb on={LOUNGE}")
check("a Lounge polish is refused while the house's answers there, naming it", not LV and HV in e and "overrides=" in e, e or t)
print("     " + e.split(". Nothing")[0])
LV, t, e = make("pike", LOUNGE, "polish", "do prop $1 polished=lounge", f"tags=verb on={LOUNGE} overrides={TA}")
check("overrides= naming a verb that is not what it stands over is refused, naming the one it would", not LV and HV in e, e or t)
DR, t, e = make("pike", PC, "polish", "do prop $1 polished=draft", "tags=verb")
check("a carried draft with the word is refused too (it would take the word over for its maker)", not DR and HV in e, e or t)

# a rule bound to the house polish, saved before any override exists
R1, t, e = make("sable", LOUNGE, "polish the shiny", "when tag:shiny do polish", "tags=rule")
check("a rule in the Lounge calling bare polish is saved, and says what its word is bound to",
      R1 and "saved:" in t and f"polish → {HV}" in t, e or t)
LV, t, e = make("pike", LOUNGE, "polish", "do prop $1 polished=lounge", f"tags=verb on={LOUNGE} overrides={HV}")
check("with overrides=<the house polish>, the Lounge polish is accepted", LV and not e, e)
NOTE, _, _ = make("pike", LOUNGE, "a cup")
rooms_go = lambda me, fid: last(me, f"go {fid} :1")
rooms_go("juniper", LOUNGE)
t, e = last("juniper", f"look {NOTE} :1", f"polish {NOTE}")
check("a typed bare polish in the Lounge runs the Lounge's, and its receipt names both",
      prop(NOTE, "polished") == "lounge" and f"over polish {HV}" in t and LV in t, e or t)
print("     " + next((l for l in t.splitlines() if l.startswith("(polish")), "")[:200])
rooms_go("juniper", BOARD)
BN, _, _ = make("pike", BOARD, "a plate")
t, e = last("juniper", f"look {BN} :1", f"polish {BN}")
check("in the Board a typed polish is still the house's (typed words behave as today)", prop(BN, "polished") == "house", e or t)
X, _, _ = make("pike", BOARD, "a spoon")
t, e = last("pike", f"look {X} :1", f"do tag {X} add=shiny")
check("the rule saved before the override still runs the house polish: a verb made later changes no stored line",
      prop(X, "polished") == "house", t)

# ---- (1) a stored word nothing answers is refused at save ---------------------------------------------------------
R2, t, e = make("sable", LOUNGE, "frob them", "when tag:frobby do frobnicate", "tags=rule")
check("a rule saved with a word nothing answers is refused (saved broken), naming the way in",
      "saved broken" in t and "frobnicate is not a verb here" in t and "make the verb first" in t, e or t)
print("     " + next(l for l in t.splitlines() if "saved broken" in l)[:220])
VB, t, e = make("sable", LOUNGE, "frobwrap", "frobnicate $1", f"tags=verb on={LOUNGE}")
check("a verb whose lines say a word nothing answers is refused when made", not VB and "frobnicate is not a verb here" in e, e or t)
t, e = last("sable", f"look {JC} :1", f'do prop {JC} wake="look; frobnicate"')
check("a wake line with a word nothing answers is refused when set", "wake line is stored text" in e and "frobnicate" in e, e or t)
FV, t, e = make("juniper", JC, "frobnicate", "do prop $1 frobbed=yes", "tags=verb on=house")
check("a verb made later with that word is accepted", FV and not e, e)
Y, _, _ = make("pike", BOARD, "a fork")
t, e = last("pike", f"look {Y} :1", f"do tag {Y} add=frobby")
check("... and the rule saved before it still does nothing: no stored word is taken over", prop(Y, "frobbed") is None, t)
D._rulestate = None             # a new desk process reads every rule afresh: the binding is in the world, not the desk
t, e = last("pike", "rules")
check("... even read afresh by a new process, the rule stays broken, saying why",
      "BROKEN" in next((l for l in t.splitlines() if R2 in l), ""), t)
VB, t, e = make("sable", LOUNGE, "frobwrap", "frobnicate $1", f"tags=verb on={LOUNGE}")
check("a verb saved now with the word binds to it", VB and f"frobnicate → {FV}" in t, e or t)

# ---- (2) a bound verb removed: its lines fail loudly, and never find another --------------------------------------
t, e = last("juniper", f"look {HV} :1", f"do remove {HV}")
Z, _, _ = make("pike", BOARD, "a knife")
t, e = last("pike", f"look {Z} :1", f"do tag {Z} add=shiny")
note = next((l for l in t.splitlines() if "could not" in l), "")
check("the rule bound to the removed house polish fails loudly with the reason, and runs no other polish",
      prop(Z, "polished") is None and f"polish {HV} is gone; this line was bound to it" in note, t)
print("     " + note.strip()[:220])
rooms_go("juniper", LOUNGE)
t, e = last("juniper", f"look {NOTE} :1", f"polish {NOTE}")
check("the Lounge polish that stood over it fails loudly too, at its next run", f"overrides {HV}, which is gone" in e, e or t)
print("     " + e.splitlines()[-1][:220])

# ---- (3) a verb's lines change: each author of a line bound to it is told on their sill ---------------------------
W1, t, e = make("juniper", JC, "stamp", "do prop $1 stamped=1", "tags=verb on=house")
RP, t, e = make("pike", PC, "stamp the post", "when tag:post do stamp", "tags=rule")
VS, t, e = make("sable", rooms.corner_of(W, "sable"), "restamp", "stamp $1", "tags=verb on=house")
RJ, t, e = make("juniper", JC, "stamp mine", "when tag:mine do stamp", "tags=rule")
check("Pike's rule, Sable's verb and Juniper's own rule are each bound to stamp",
      all((subj(x).get("binds") or {}).get("words", {}).get("stamp", {}).get("id") == W.nodes[W1]["subject"] for x in (RP, VS, RJ)),
      [subj(x).get("binds") for x in (RP, VS, RJ) if x])
title = "stamp changed; these of yours use it"
t, e = last("juniper", f"read {W1} :3", f'do rewrite {W1} text="do prop $1 stamped=2"')
pn, sn = sill_notes("pike", title), sill_notes("sable", title)
check("editing stamp's lines leaves a note on Pike's sill and on Sable's, each naming their own line",
      len(pn) == 1 and len(sn) == 1 and RP in subj(pn[0])["text"] and VS in subj(sn[0])["text"]
      and RP not in subj(sn[0])["text"], (t, [subj(x)["text"] for x in pn + sn]))
check("... and Juniper's own line is named on her receipt, not her sill",
      not sill_notes("juniper", title) and "these of yours use it" in t and RJ in t, t)
print("     " + subj(pn[0])["text"].replace("\n", " / ")[:300] if pn else "     (no note)")
n_notes = len(sill_notes("pike", title))
t, e = last("juniper", f"read {W1} :3", f'do rewrite {W1} text="# stamps it\\ndo prop $1 stamped=2"')
check("a change only to its # description lines tells no one", len(sill_notes("pike", title)) == n_notes, t)

# the real case: the house's trash, used by three lenses' acts, one by each kind of author. a3029: each lens is named
# where its author will read it: the changer's on the receipt, pike's in the note on their sill, claude's (no sill) on
# the receipt, saying so. Until a3029 this looked only at the receipt, so an author with a sill failed it
trash_title = "trash changed; these of yours use it"
t, e = last("sable", f"read {TA} :3", f'do append {TA} line="do prop $1 binned=1"')
told = [l for l in t.splitlines() if l.startswith("~ trash")]
for l in told:
    print("     " + l[:240])
app = lambda title: W.appearances_of(next(s for s in cc if s["title"] == title)["id"])[0]
mine = next((l for l in told if "these of yours use it" in l), "")
nosill = next((l for l in told if "claude has lines that use it and no sill to tell" in l), "")
psill = sill_notes("pike", trash_title)
check("changing the house's trash tells the authors of the lens acts bound to it (or says who has no sill)",
      len(cc) == 3 and app("trash-probe") in mine and app("guest-bin") in nosill and len(psill) == 1
      and app("desk-board") in subj(psill[0])["text"] and app("desk-board") not in mine + nosill
      and not sill_notes("sable", trash_title), (e or t, [subj(x)["text"] for x in psill]))

# ---- undo, and the lens and wake paths ----------------------------------------------------------------------------
R3, t, e = make("pike", BOARD, "frob board", "when tag:fb do frobnicate", "tags=rule")
t, e = last("pike", f"read {R3} :3", f'do rewrite {R3} text="when tag:fb do restamp"')
rewrite_ev = W.events[-1]["id"]
check("rewriting a rule binds its new word", subj(R3)["binds"]["words"].get("restamp", {}).get("id") == W.nodes[VS]["subject"], subj(R3).get("binds"))
t, e = last("pike", f"undo {rewrite_ev}")
check("undo of the rewrite brings back the old text with its old binding", subj(R3)["binds"]["text"] == subj(R3)["text"]
      and "frobnicate" in subj(R3)["binds"]["words"], (e, subj(R3).get("binds")))

LN, t, e = make("pike", BOARD, "frob lens", "window : column\\n  b : text \\\"go\\\", role tool, on click do frobnicate $item", "tags=lens")
check("a lens whose act calls frobnicate binds it when saved", LN and subj(LN)["binds"]["words"].get("frobnicate", {}).get("id")
      == W.nodes[FV]["subject"], (e, t))
LB, t, e = make("pike", BOARD, "bad lens", "window : column\\n  b : text \\\"go\\\", role tool, on click do zonk $item", "tags=lens")
check("a lens whose act calls a word nothing answers is refused when saved", not LB and "lens" in e and "zonk" in e, e or t)
F2, t, e = make("pike", BOARD, "a bowl")
D._act_home, D._act_binds = (BOARD,), verbs.lens_binds(W, [W.nodes[LN]["subject"]])
try:
    be("alex")
    r = D.dispatch("desk", {"line": f"look {F2} :1; do frobnicate {F2}", "whole": False})
finally:
    D._act_home = D._act_binds = None
check("a press on that lens runs the verb it was bound to", prop(F2, "frobbed") == "yes", r)

t, e = last("juniper", f"look {JC} :1", f'do prop {JC} wake="look; restamp {F2}"')
check("a wake line calling restamp is bound when set", not e and verbs.stored_at(W, JC)[1]["words"]["restamp"]["id"]
      == W.nodes[VS]["subject"], e or t)
t, e = last("sable", f"look {VS} :1", f"do remove {VS}")
D._act_home, D._act_binds = verbs.stored_at(W, JC)
try:
    be("juniper")
    r = D.dispatch("desk", {"line": f"restamp {F2}", "whole": True})
finally:
    D._act_home = D._act_binds = None
check("once restamp is gone, the wake fails loudly with the reason", f"restamp {VS} is gone" in (r.get("error") or ""), r)
t, e = last("juniper", f"restamp {F2}")
check("... and a typed restamp is a plain miss, as today", "nothing here answers" in e + t and "bound" not in e + t, e or t)

print()
print("all ok" if not fails else f"{len(fails)} FAILED: " + ", ".join(fails))
sys.exit(1 if fails else 0)
