"""test_reach: a line the desk did not do leaves a trace, and `wish` carries it (9 Oct 2026, a3806).

On a small world it builds itself (roomworld.build(house=True)), with the reaches file in a temporary place:
  - a refusal and a miss are each recorded (who, the line, what came back, its shape); a line that ran is not
  - the same refusal about two different things is one shape, counted twice; `rows reaches` lists the most met first
  - `wish <words>` from any room lands in the chat with role=wishes, signed, with the last line the desk refused
    and what it said; a wish with nothing refused before it is just its words
  - a test world (roomworld..., ...-try) writes no file
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import roomworld
import verbs

FAILED = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {detail}"))
    if not ok:
        FAILED.append(name)


d, R = roomworld.build(house=True)
verbs.REACHES = Path(tempfile.mkdtemp(prefix="reaches-"))
W = d.world


def say(me, *lines):
    W.me = me
    out = []
    for l in lines:
        r = d.dispatch("desk", {"line": l, "whole": True})
        out.append(r.get("text") or "ERR " + r["error"])
    return "\n".join(out)


say("pike", "do move zz99 into=f1")
check("a test world writes no file", not list(verbs.REACHES.glob("*")), list(verbs.REACHES.glob("*")))
check("... but the last refused line is still at hand for $reach", (verbs.last_reach(d) or {}).get("kind") == "refused", verbs.last_reach(d))

d._session = "smallworld"
made = say("jeff", f"look {R.HOME} :1", f'do create {R.HOME} kind=chat title="Wishes" members=all role=wishes')
WISHES = made.split("created ")[1].split()[0]
t = say("sable", f"go {R.LOUNGE} :1", "wish the couch is too low")
text = W.subjects[W.nodes[WISHES]["subject"]]["text"]
check("a wish with nothing refused before it is just its words, signed", "Sable: the couch is too low" in text and "typed:" not in text, (t, text))

say("pike", f"do move zz99 into={R.SHELF}")
say("pike", f"do move qq7 into={R.SHELF}")
say("pike", "frobnicate the shelf")
say("pike", f"look {R.SHELF}")
rows = verbs.reach_rows(d)
check("two refusals of one shape count as one row of 2, first", rows and rows[0]["n"] == 2 and rows[0]["kind"] == "refused" and "no such id" in rows[0]["shape"], rows)
check("the miss is a row by its word", any(r["shape"] == "miss: frobnicate" and r["n"] == 1 for r in rows), rows)
check("a line that ran is not recorded", len(rows) == 2 and sum(r["n"] for r in rows) == 3, rows)
t = say("pike", "rows reaches")
check("rows reaches prints them", "rows reaches: 2" in t and "n=2" in t and "who=pike" in t, t)

say("pike", f"do move zz99 into={R.SHELF}")
t = say("pike", f"go {R.BOARD} :1", "wish I meant the letter")
text = W.subjects[W.nodes[WISHES]["subject"]]["text"]
last = text.splitlines()[-1]
check("wish from another room lands in Wishes with what was typed and what came back",
      last.startswith("Pike: I meant the letter [typed: do move zz99 into=") and "came back: no such id 'zz99'" in last, (t, last))
check("the wish's receipt does not print the line back (a3806)", "said:" not in t and "now:" not in t, t)
check("... and another person's wish does not carry Pike's refusal", "typed:" not in say("juniper", "wish the tea is cold") and
      W.subjects[W.nodes[WISHES]["subject"]]["text"].splitlines()[-1] == "Juniper: the tea is cold",
      W.subjects[W.nodes[WISHES]["subject"]]["text"].splitlines()[-1])

print()
print("all passed" if not FAILED else f"{len(FAILED)} failed: " + "; ".join(FAILED))
sys.exit(1 if FAILED else 0)
