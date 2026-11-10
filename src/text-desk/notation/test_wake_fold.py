# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_wake_fold: a wake does not print again a note its conversation already holds (9 Oct 2026, a3806).

On a small world it builds itself (roomworld.build), with the house's fold_reads called as wake() calls it:
  - the first wake prints the note its wake line reads, whole
  - the next wake, the note unchanged, prints one line for it and the look as ever
  - after the note is edited the wake prints it whole again
  - after the conversation begins again (wake_read forgotten, as wake() does on lost or welcome_due) it is whole again
  - a wake line of one command folds too; a chat is never folded (its read already shows only what is new)
"""
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import house
import roomworld

FAILED = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {detail}"))
    if not ok:
        FAILED.append(name)


d, R = roomworld.build()
W = d.world
H = object.__new__(house.House)          # only fold_reads is used: no claude, no state on disk
H.load = lambda: W
r = SimpleNamespace(state={}, log=lambda *a: None)
SOUL = R.corner_desc["juniper"]
LINE = f"read {SOUL} :3; look"


def wake(line=LINE):
    W.me = "juniper"
    t = d.dispatch("desk", {"line": line})
    return H.fold_reads(r, line, t.get("text") or "ERR " + t["error"])


W.me = "juniper"
d.dispatch("desk", {"line": f"read {SOUL} :3", "whole": True})
d.dispatch("desk", {"line": f'do append {SOUL} line="{" ".join(["word"] * 80)}"', "whole": True})
check("a note of a few words is not worth folding (set up: this one is long)", len(W.subjects[W.nodes[SOUL]["subject"]]["text"].split()) > 60)
first = wake()
check("the first wake prints the note whole", "Juniper's own place." in first and "unchanged since" not in first, first)
second = wake()
check("the next wake, nothing changed, says so in one line and does not print it", "unchanged since I last showed it" in second
      and "Juniper's own place." not in second.split("[2]")[0], second)
check("... and the look is printed as ever", "[2] look" in second and "You are in" in second, second)
check("... and it is shorter", len(second) < len(first), (len(first), len(second)))
W.me = "juniper"
d.dispatch("desk", {"line": f'do append {SOUL} line="and a window"', "whole": True})
third = wake()
check("after an edit the wake prints the note whole again", "and a window" in third and "unchanged since" not in third, third)
r.state.pop("wake_read", None)
fourth = wake()
check("a conversation that begins again is shown it whole", "and a window" in fourth and "unchanged since" not in fourth, fourth)
one = wake(f"read {SOUL} :3")
one = wake(f"read {SOUL} :3")
check("a wake line of one command folds too", "unchanged since I last showed it" in one and "and a window" not in one, one)
chat = R.TALK[R.LOUNGE]
wake(f"read {chat}; look")
c2 = wake(f"read {chat}; look")
check("a chat is never folded by the house", "unchanged since I last showed it" not in c2, c2)

print()
print("all passed" if not FAILED else f"{len(FAILED)} failed: " + "; ".join(FAILED))
sys.exit(1 if FAILED else 0)
