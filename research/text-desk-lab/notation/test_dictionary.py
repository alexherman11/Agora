# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_dictionary (a13316): one entry for every word, as world notes (dictionary.py; the format is
research/community-app/DICTIONARY-ENTRY.md). Imagined from the desk as it is lived in:

  1. before: a Help binder with no word= anywhere is plain help, and help prints its notes as before
  2. pike makes examine and move entries (word= takes= undo= from= bound=): help shows the entry's line, then the help;
     examine of the entry says it is one; rows dictionary lists every word, the house's verb notes too, bound
  3. juniper keeps typing inspect: she adds it to the entry's title, and inspect <id> is examine, with no source edit;
     sable adds shift to move's entry, and `do shift` moves; a verb note in a stored line may say do shift
  4. pike renames the entry inspect|x|ex: help inspect and help examine both read it, and examine still works
  5. a new verb note can't take inspect; an alias can't take tidy from the house's verb note (tidy stays the verb's,
     and the check names the clash)
  6. an entry bound to a word the code lacks says UNBOUND, and the check says so
  7. sable translates examine's help: help leaves the Spanish out and says where it is; read <entry> #es prints it
  8. the home base: entries from=module:home-base are unbound while it is not running, saying why, and bound once
     it publishes its rows (witnessed:host); a row with no entry is named by the check
  9. the check: a command with a help note but no word= is named once the dictionary is on

Builds its own small world in memory (roomworld.py) and never saves it; the home base's rows are written under a
world name of this test's own and removed at the end.
"""
import os
import re
import shutil
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


D, R = roomworld.build(house=True)
W = D.world
D._session = "dictionary-test-" + uuid.uuid4().hex[:8]
import dictionary   # noqa: E402
import helpnotes   # noqa: E402
import scene   # noqa: E402
import witnessed   # noqa: E402


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


def one(me, line):
    _, text, err = reply(me, line)[-1]
    return re.sub(r"^(?:(?:!!|~|  ) .*\n)+", "", text), err


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


EX = "examine <id> (or x, ex): one thing in depth: its line, its text, comments, links, where it is."
MV = "move <thing> into=<surface>: put a thing somewhere else."
try:
    # ---- 1. before: plain help ---------------------------------------------------------------------------------------
    out = reply("pike", f"look {R.HOME} :1", f"do create {R.HOME} kind=surface title=Help layout=column",
                "do prop $new role=help")
    HB = helpnotes.binder(W)
    made = reply("pike", f"look {HB} :1", f"do create {HB} kind=note title=\"examine|x|ex\" text={q(EX)}",
                 f"do create {HB} kind=note title=move text={q(MV)}",
                 f"do create {HB} kind=surface title=\"Home base words\" layout=column")
    check("the binder and two help notes are made", all(not e for _, _, e in made), made)
    EXA, MVA, HOMEB = [a for words, s, a in helpnotes.entries(W)][:2] + [W.last_created]
    t, e = one("pike", "help x")
    check("1. no word= anywhere: help x prints the note as it is (plain help, as before)", t == EX, t)
    check("1. ... and the check says nothing about entries", not [p for p in helpnotes.check(D) if "dictionary" in p],
          helpnotes.check(D))

    # ---- 2. entries ----------------------------------------------------------------------------------------------------
    out = reply("pike", f'do prop {EXA} word=see takes="<id>" from=kernel bound=examine may=anyone',
                f"do prop {MVA} word=do takes=\"<thing> into=<surface>\" undo=yes from=kernel bound=move")
    check("2. pike gives two help notes their entry props", all(not e for _, _, e in out), out)
    t, e = one("pike", "help examine")
    check("2. help examine: the entry's line (kind, takes, undo, who may, from, bound), then its help",
          t.splitlines()[0] == "examine | x | ex   (see · takes <id> · nothing to undo (a reading) · who may: "
          "anyone · from the kernel, bound to examine)" and t.splitlines()[1] == EX, t)
    t, e = one("pike", f"examine {EXA}")
    check("2. examine of the entry note says it is a dictionary entry, bound", "a dictionary entry (a13316): examine | x"
          " | ex: see · takes <id>" in t and "bound to examine" in t, t)
    check("2. examine|x|ex is no clash: x and ex are the code's own words for examine",
          not [p for p in helpnotes.check(D) if p.startswith("dictionary entry")], helpnotes.check(D))
    rs = scene.rows(D, "dictionary")
    words = {r["word"]: r for r in rs}
    check("2. rows dictionary lists the binder's entries and the house's verb notes, each bound",
          {"examine", "move", "tidy", "gather"} <= set(words) and words["tidy"]["from"] == "verb"
          and words["tidy"]["takes"] == "<surface>" and all(r["bound"] == "yes" for r in rs), rs)
    t, e = one("pike", "help tidy")
    check("2. help tidy (a verb note): its entry line comes from the note itself, with defaults",
          "entry: do · takes <surface> · undo takes it back · who may: anyone · from a verb note, bound to its own lines" in t, t)

    # ---- 3. aliases --------------------------------------------------------------------------------------------------
    t, e = one("juniper", f"inspect {R.BOARD}")
    check("3. before: inspect is no word here", "inspect" in (t + e) and ("unknown command" in t + e or "MISS" in t + e
                                                                        or "nothing" in t + e), (t, e))
    out = reply("juniper", f"read {EXA}", f'do retitle {EXA} title="examine|x|ex|inspect"')
    check("3. juniper adds inspect to examine's entry title", not out[-1][2], out)
    t, e = one("juniper", f"inspect {R.BOARD}")
    t2, _ = one("juniper", f"examine {R.BOARD}")
    check("3. inspect <id> is examine now, with no source edit", not e and t == t2 and R.BOARD in t, (t, e))
    out = reply("sable", f"read {MVA}", f'do retitle {MVA} title="move|shift"')
    made = reply("sable", f"look {R.HOME} :1", f"do create {R.HOME} kind=note title=Stray text=x")
    stray = W.last_created
    t, e = one("sable", f"do shift {stray} into={R.BOARD}")
    check("3. sable adds shift to move's entry, and do shift moves", not e and t.startswith("ok move")
          and W.nodes[stray]["parent"] == R.BOARD, (t, e))
    out = reply("sable", f"look {R.HOME} :1",
                f'do create {R.HOME} kind=note tags=verb title=park text="# park <thing>: put it on the Board\\n'
                f'do shift $1 into={R.BOARD}"')
    check("3. a verb note whose stored line says do shift is saved (bound as the built-in move, not refused)",
          not out[-1][2] and "not a verb here" not in out[-1][1], out)
    reply("sable", f"do move {stray} into={R.HOME}")
    t, e = one("sable", f"park {stray}")
    check("3. ... and park runs it: the stray note is on the Board again", not e and W.nodes[stray]["parent"] == R.BOARD,
          (t, e))

    # ---- 4. rename -----------------------------------------------------------------------------------------------------
    out = reply("pike", f"read {EXA}", f'do retitle {EXA} title="inspect|x|ex"')
    t, e = one("pike", "help inspect")
    t2, e2 = one("pike", "help examine")
    check("4. renamed inspect|x|ex: help inspect reads the entry, and help examine (the bound word) still does",
          t.startswith("inspect | x | ex") and t2 == t, (t, t2))
    t, e = one("pike", f"examine {R.BOARD}")
    check("4. ... and examine still works (the code's own word is the floor)", not e and R.BOARD in t, (t, e))
    check("4. ... and the check finds no missing entry for examine", not [p for p in helpnotes.check(D)
                                                                          if "entry for examine" in p], helpnotes.check(D))

    # ---- 5. clashes ----------------------------------------------------------------------------------------------------
    out = reply("juniper", f"look {R.HOME} :1",
                f'do create {R.HOME} kind=note tags=verb title=inspect text="# mine\\nlook $1"')
    check("5. a new verb note titled inspect is refused: the dictionary gives that word to examine",
          out[-1][2] or "ERR" in out[-1][1] or "refus" in out[-1][1].lower(), out)
    out = reply("pike", f"read {MVA}", f'do retitle {MVA} title="move|shift|tidy"')
    t, e = one("pike", f"do tidy {R.BOARD}")
    check("5. an alias can't take tidy from the house's verb note: do tidy still runs the verb",
          "verb tidy" in t or "(tidy " in t, (t, e))
    probs = helpnotes.check(D)
    check("5. ... and the check names the clash", any("names tidy, which the verb note" in p for p in probs), probs)
    reply("pike", f"read {MVA}", f'do retitle {MVA} title="move|shift"')

    # ---- 6. unbound ----------------------------------------------------------------------------------------------------
    out = reply("pike", f"look {HB} :1", f'do create {HB} kind=note title=frob text="frob <id>: frobs it."',
                "do prop $new word=do from=kernel bound=frobnicate undo=yes")
    t, e = one("pike", "help frob")
    check("6. an entry bound to a word the code lacks says UNBOUND, and why",
          "UNBOUND, nothing in the desk's code answers to frobnicate" in t, t)
    probs = helpnotes.check(D)
    rs = {r["word"]: r for r in scene.rows(D, "dictionary")}
    check("6. ... rows dictionary says bound=no with the reason, and the check does not fail on it (an entry may be "
          "written before its code lands)", rs["frob"]["bound"] == "no" and "frobnicate" in rs["frob"]["why"]
          and not any("frob" in p for p in probs), (rs.get("frob"), probs))
    FROB = W.last_created
    reply("pike", f"do remove {[a for w_, s, a in helpnotes.entries(W) if w_ == ['frob']][0]}")

    # ---- 7. translations -----------------------------------------------------------------------------------------------
    ES = "examina <id>: una cosa a fondo."
    out = reply("sable", f"read {EXA}", f"do append {EXA} line=\"## es\"", f"do append {EXA} line={q(ES)}")
    t, e = one("sable", "help x")
    check("7. help leaves the Spanish out and says where it is", ES not in t and f"also in: es (read {EXA} #es)" in t, t)
    t, e = one("sable", f"read {EXA} #es")
    check("7. read <entry> #es prints the Spanish", ES in t, t)

    # ---- 8. the home base ----------------------------------------------------------------------------------------------
    out = reply("pike", f"look {HOMEB} :1", f'do create {HOMEB} kind=note title=media.play text="media.play: play or '
                f'pause."', "do prop $new word=do undo=external may=stewards from=module:home-base bound=media.play")
    t, e = one("pike", "help media.play")
    check("8. the home base not running: media.play is unbound, saying why",
          "UNBOUND, the home-base is not running" in t, t)
    witnessed.write(D._session, "host", [{"name": "media.play", "about": "play or pause", "takes": ""},
                                         {"name": "media.next", "about": "the next song", "takes": ""}], by="test")
    t, e = one("pike", "help media.play")
    check("8. once it publishes its rows: bound", "from the module home-base, bound to media.play" in t, t)
    probs = helpnotes.check(D)
    check("8. a row with no entry is named by the check", any("publishes media.next" in p for p in probs), probs)

    # ---- 9. completeness -----------------------------------------------------------------------------------------------
    probs = helpnotes.check(D)
    check("9. a command with no entry is named, once the dictionary is on",
          any(p.startswith("no dictionary entry for look") for p in probs), probs)
    # ---- 10. a lending shelf, built from help alone (as Claude built one in frontier, 23 Oct) -------------------------
    out = reply("mica", f"look {R.HOME} :1", f'do create {R.HOME} kind=surface title="Tool shelf" layout=column',
                "do prop $new role=room")
    SHELF = W.last_created
    made = reply("mica", f"go {SHELF}", f"do create {SHELF} kind=note title=Ladder text=\"6 m, from Maya's garage.\"",
                 f"do create {SHELF} kind=note title=Drill text=\"Cordless, two batteries.\"",
                 f'do create {SHELF} kind=note tags=verb on={SHELF} title=lend text="# lend <tool> <name>: lend a tool '
                 f'on this shelf to a neighbour.\\ndo prop \\$1 lent_to=\\$2 lent_on=\\$today"',
                 f'do create {SHELF} kind=note tags=verb on={SHELF} title=return text="# return <tool>: it is back.\\n'
                 f'do prop \\$1 remove=lent_to,lent_on"',
                 f'do create {SHELF} kind=note tags=verb on={SHELF} title=who-has text="# who-has: what is lent, to '
                 f'whom.\\ntable prop:lent_to,in:\\$here cols=title,lent_to"',
                 f'do create {SHELF} kind=note tags=verb on={SHELF} title=borrow text="# borrow <tool>: lend it to '
                 f'yourself.\\nlend \\$1 \\$me"')
    check("10. mica makes a shelf room, two tools and four verbs; borrow's stored line is bound to lend",
          all(not e for _, _, e in made) and "lend → a" in made[-1][1], made[-1])
    LEND = [a for a in W.nodes if W.nodes[a].get("subject") and W.subjects[W.nodes[a]["subject"]]["title"] == "lend"][0]
    def props_of(aid):
        return W.subjects[W.nodes[aid]["subject"]].get("props") or {}
    LADDER = next(k["id"] for k in W.children(SHELF) if W.subjects.get(k.get("subject"), {}).get("title") == "Ladder")
    rs = {r["word"]: r for r in scene.rows(D, "dictionary")}
    check("10. the dictionary knows lend, and what it takes from its own first line", rs["lend"]["takes"] == "<tool> <name>"
          and rs["borrow"]["takes"] == "<tool>", (rs.get("lend"), rs.get("borrow")))
    t, e = one("mica", "lend Ladder maya")
    t2, e2 = one("mica", "borrow Drill")
    t3, e3 = one("mica", "who-has")
    check("10. lend, borrow and who-has work together", props_of(LADDER).get("lent_to") == "maya"
          and "Drill" in t3 and "maya" in t3 and "mica" in t3, (t, t2, t3))
    out = reply("mica", f"read {LEND}", f'do retitle {LEND} title="loan|prestar"', f'do append {LEND} line="## es"',
                f'do append {LEND} line="# prestar <herramienta> <nombre>: presta una herramienta a un vecino."')
    check("10. mica renames lend to loan, adds prestar, and a Spanish help section, with no source edit",
          all(not e for _, _, e in out), out)
    reply("mica", "return Drill")
    t, e = one("mica", "borrow Drill")
    check("10. the old stored line still runs: borrow says lend, bound to the note, now loan",
          not e and "(loan a" in t and "lent_to=mica" in t, (t, e))
    t, e = one("mica", "prestar Ladder juniper")
    check("10. prestar is loan", not e and "lent_to=juniper" in t, (t, e))
    t, e = one("mica", "help prestar")
    check("10. help prestar: the English help, the Spanish named, not printed among it",
          "presta una herramienta" not in t and f"also in: es (read {LEND} #es)" in t and "lend <tool> <name>" in t, t)
    t, e = one("mica", f"read {LEND} #es")
    check("10. read <verb> #es prints the Spanish", "presta una herramienta" in t, t)
    WHO = [a for a in W.nodes if W.nodes[a].get("subject") and W.subjects[W.nodes[a]["subject"]]["title"] == "who-has"][0]
    reply("mica", f"read {WHO}", f"do prop {WHO} word=see")
    t, e = one("mica", "help who-has")
    check("10. who-has said word=see: a reading, nothing to undo", "entry: see · takes nothing · nothing to undo" in t, t)
    t, e = one("mica", "lend Drill maya")
    check("10. typed, the old word lend is gone (only stored lines keep it)", "lend" in t + e and not
          "lent_to=maya" in t, (t, e))
finally:
    d = witnessed._dir(D._session)
    if d is not None and d.parent.exists() and d.parent.name == D._session:
        shutil.rmtree(d.parent, ignore_errors=True)

print("\nall passed" if not fails else f"\n{len(fails)} FAILED: " + "; ".join(fails))
sys.exit(1 if fails else 0)
