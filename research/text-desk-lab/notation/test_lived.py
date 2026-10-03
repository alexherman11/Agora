"""test_lived (a3165): a lived= before landing is a report as of a commit, and the promise ends at the landing.

    python test_lived.py

A small world in memory (roomworld.py) and a git repository of its own in a temporary folder, where commissions are
branches landed as the house lands them (merge --no-ff). The house's part is the workshop's own code (compare_lived,
lived_vs_landed), run with a stand-in house whose lines go through the desk's dispatch. The story, as someone meets it:
pike asks a commission, lives it at a commit and says so; then it lands
  - unchanged, while main moved elsewhere: the promise ends kept, its receipt stating its reach, pike not asked again;
  - with a later commit by the worker: it stays open, naming the file, until pike lives it as it landed;
  - after the worker merged main and resolved a conflict in its own file: it stays open (code nobody lived), and pike
    ends it on their own word;
and the edges: the door's record names the commit when lived= doesn't; no commit at all is one's own word, as before; a
commit git doesn't know; a lived= that names its commit only after the landing; landed is the house's word alone.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import promises    # noqa: E402
import roomworld   # noqa: E402
import workshop    # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build(say=False)
W = D.world
B = R.BOARD


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


class House:
    """What the workshop needs of the house: its world, and its lines run as the house's (; separates them)."""
    world, said = "roomworld-inmemory", []

    def load(self):
        return W

    def act(self, who, line):
        out = say(who, *[p.strip() for p in line.split(";")])
        self.said.append(out)
        return out


tmp = tempfile.TemporaryDirectory()
REPO = Path(tmp.name)
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def git(*args, ok=True):
    r = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, env=ENV)
    assert not ok or r.returncode == 0, (args, r.stdout, r.stderr)
    return r.stdout.strip()


def write(name, text, msg=None):
    (REPO / name).parent.mkdir(parents=True, exist_ok=True)
    (REPO / name).write_text(text, encoding="utf-8")
    git("add", "--", name)
    if msg:
        git("commit", "-q", "-m", msg)
        return git("rev-parse", "HEAD")


def land(branch):
    """As workshop.land merges: --no-ff into main. -> the merge commit, short, as landed= holds it."""
    git("checkout", "-q", "main")
    git("merge", "-q", "--no-ff", branch, "-m", f"land {branch}")
    return git("rev-parse", "--short", "HEAD")


git("init", "-q", "-b", "main")
write("lab/a.py", "a = 1\n")
write("lab/b.py", "b = 1\n")
write("docs/Current Implementation.md", "one\n")
write("other.py", "o = 1\n", "start")
workshop.REPO = REPO
WS = workshop.Workshop(House())

say("pike", 'promise to=pike "turn promises on"')      # a world has promises once it has its Promises surface


def commission(title):
    """pike asks a commission -> (card, promise)."""
    t = say("pike", f"look {B} :1", f'do create {B} kind=task title="{title}" owner=pike asked_by=pike status=open')
    card = re.findall(r"created (a\d+)", t)[-1]
    t = say("pike", f"look {card} :1", f"do prop {card} commission=asked")
    say("house", f"look {card} :1", f"do prop {card} commission=working")
    return card, re.search(r"asker's promise: (a\d+)", t).group(1)


def landed(card, head):
    say("house", f"look {card} :1", f"do prop {card} commission=landed landed={head}")
    WS.compare_lived(W)


def reads(p, me="pike"):
    return promises.phrase(W, promises.state(W, W.nodes[p]["subject"]), promises._person(W, me))


# ---- landed unchanged: kept at the landing, with its reach, and pike is not asked again -------------------------------
K1, P1 = commission("Doors")
git("checkout", "-q", "-b", "worker/k1")
c1 = write("lab/a.py", "a = 2\n", "k1: a")
t = say("pike", f"look {K1} :1", f'do prop {K1} lived="{K1}@{c1[:7]}: the door opens"')
check("lived= naming a commit before landing is a report as of it, and ends nothing",
      f"reports {P1} as of {c1[:7]}, not landed yet" in t and "kept" not in t.split("kept if")[0], t)
check("the promise reads 'lived at <commit>, not landed yet', and is still open",
      reads(P1) == f"your own promise · lived at {c1[:7]}, not landed yet" and P1 in say("pike", "promises"), reads(P1))
git("checkout", "-q", "main")
write("other.py", "o = 2\n")
write("docs/Current Implementation.md", "two\n", "main moves elsewhere")
n = len(W.events)
landed(K1, land("worker/k1"))
check("the same code landed: kept, and the receipt states its reach",
      reads(P1) == f"kept: lived at {c1[:7]}; landed on a main that moved in 2 other files since; health passed", reads(P1))
check("to someone else it says who lived it", reads(P1, "sable").startswith(f"kept: pike lived at {c1[:7]};"), reads(P1, "sable"))
check("by the house's one act, and pike is asked nothing", [e["by"] for e in W.events[n:]] == ["house", "house"]
      and P1 not in say("pike", "promises"), W.events[n:])
t = say("pike", f"examine {P1}")
check("examine tells it act by act", f"lived by pike" in t and f"as of {c1[:7]}: {K1}@{c1[:7]}: the door opens" in t
      and "compared with the landing by house" in t, t)
n = len(W.events)
WS.compare_lived(W)
check("and nothing is said twice", len(W.events) == n)

# ---- the worker commits after the visit: still open, naming the file; a re-live ends it -------------------------------
K2, P2 = commission("Windows")
git("checkout", "-q", "-b", "worker/k2")
c2 = write("lab/a.py", "a = 3\n", "k2: a")
say("pike", f"look {K2} :1", f'do prop {K2} lived="{K2}@{c2[:7]}: the window opens"')
write("lab/b.py", "b = 2\n", "k2: b, after the visit")
landed(K2, land("worker/k2"))
check("landed with a later commit: still open, 'landed differently from what you lived', naming the file",
      reads(P2).startswith(f"your own promise · landed differently from what you lived at {c2[:7]}: lab/b.py (live it as it landed")
      and f"report {P2} how=" in reads(P2), reads(P2))
check("it is on pike's list, held", P2 in say("pike", "promises"), say("pike", "promises"))
t = say("pike", f"look {K2} :1", f'do prop {K2} lived="lived it as it landed: both open"')
check("a re-live after the landing ends it kept, on pike's word", "kept (your own word)" in t and reads(P2).startswith("kept (your own word)"), t)
t = say("pike", f"look {K2} :1", f'do prop {K2} lived="{K2}@{c2[:7]}: again"')
check("nothing reopens: a promise that ended stays ended", reads(P2).startswith("kept (your own word): lived it as it landed"), reads(P2))

# ---- the worker merged main and resolved a conflict in its own file: code nobody lived --------------------------------
K3, P3 = commission("Stairs")
git("checkout", "-q", "-b", "worker/k3")
c3 = write("lab/a.py", "a = 4  # stairs\n", "k3: a")
say("pike", f"look {K3} :1", f'do prop {K3} lived="{K3}@{c3[:7]}: the stairs hold"')
git("checkout", "-q", "main")
write("lab/a.py", "a = 5  # main\n")
write("other.py", "o = 3\n", "main changes a.py too, and other.py")
git("checkout", "-q", "worker/k3")
git("merge", "-q", "main", ok=False)
write("lab/a.py", "a = 45  # both\n", "k3: merge main, resolved")
c = workshop.lived_vs_landed(c3, land("worker/k3"))
check("the comparison: the resolved file differs; main's other file is counted, never a difference",
      c["files"] == ["lab/a.py"] and c["other"] == 1 and c["also"] == ["lab/a.py"], c)
landed(K3, git("rev-parse", "--short", "HEAD"))
check("a conflict resolved in the commission's own file keeps it open", f"landed differently from what you lived at {c3[:7]}: lab/a.py" in reads(P3), reads(P3))
t = say("pike", f"look {P3} :1", f'report {P3} how="the merge only joined two numbers"')
check("pike may say the difference didn't matter, and it shows as pike's word",
      reads(P3) == "kept (your own word): the merge only joined two numbers", reads(P3))

# ---- main changed the commission's file without a conflict, merged by the landing: kept, and said ---------------------
K4, P4 = commission("Roof")
git("checkout", "-q", "-b", "worker/k4")
c4 = write("lab/b.py", "b = 2\nroof = 1\n", "k4: b")
git("checkout", "-q", "main")
write("lab/b.py", "top = 0\nb = 2\n", "main changes b.py at its other end")
VIS = REPO / "visits.json"
VIS.write_text(json.dumps({"world": "roomworld-inmemory", "last": {"pike": {K4: c4}}}), encoding="utf-8")
promises.VISITS = VIS
t = say("pike", f"look {K4} :1", f'do prop {K4} lived="the roof keeps the rain out"')
check("no commit named: the commit the door last pinned for pike in it, and the receipt says so",
      f"as of {c4[:7]}, the commit the door last pinned for you in {K4}" in t, t)
landed(K4, land("worker/k4"))
check("kept, saying main also changed the commission's own file",
      reads(P4) == f"kept: lived at {c4[:7]}; landed on a main that had not moved elsewhere since, and in the commission's own "
                   f"lab/b.py, merged in unlived; health passed", reads(P4))

# ---- edges --------------------------------------------------------------------------------------------------------------
K5, P5 = commission("Cellar")
t = say("pike", f"look {K5} :1", f'do prop {K5} lived="ran its tests by hand"')
check("no commit named and none at the door: pike's own word, as before", "kept (your own word)" in t, t)
K6, P6 = commission("Attic")
say("pike", f"look {K6} :1", f'do prop {K6} lived="{K6}@abc1234: looked fine"')
git("checkout", "-q", "-b", "worker/k6")
write("lab/a.py", "a = 6\n", "k6: a")
landed(K6, land("worker/k6"))
check("a commit git doesn't know: still open, saying nothing could be compared",
      "could not be compared with it: abc1234 is no commit git knows here" in reads(P6), reads(P6))
K7, P7 = commission("Porch")
git("checkout", "-q", "-b", "worker/k7")
c7 = write("lab/a.py", "a = 7\n", "k7: a")
say("house", f"look {K7} :1", f"do prop {K7} commission=landed landed={land('worker/k7')}")
t = say("pike", f"look {K7} :1", f'do prop {K7} lived="{K7}@{c7[:7]}: sat on it before it landed"')
check("lived= naming its commit after the landing: the house compares at its next pass",
      "has landed, and the house compares what landed" in t and "the house has not compared it" in reads(P7), (t, reads(P7)))
WS.compare_lived(W)
check("and it ends kept", reads(P7).startswith(f"kept: lived at {c7[:7]}; landed on a main that had not moved"), reads(P7))
K8, P8 = commission("Gate")
say("pike", f"look {K8} :1", f'do prop {K8} lived="{K8}@{c7[:7]}: early"')
t = say("pike", f"look {P8} :1", f"landed {P8} lived={c7[:7]}")
check("landed is the house's word alone", t.startswith("ERR") and "the house's word" in t, t)
ev = [e for e in W.events if e["verb"] == "report"][-1]["id"]
say("pike", f"undo {ev}")
check("a report as of a commit undone leaves the promise as it was", reads(P8) == "your own promise", reads(P8))

tmp.cleanup()
print(f"\n{len(fails)} failed" if fails else "\nall ok")
sys.exit(1 if fails else 0)
