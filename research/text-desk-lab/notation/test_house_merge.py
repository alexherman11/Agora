# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_house_merge: a branch that does not merge into main is merged by the HOUSE, in the builder's own worktree
(a6753; Codex builders cannot write .git, and five cards stalled on 'merge main into your branch' on 20 Oct).

    python test_house_merge.py

A small world in memory (roomworld.py) and a git repository of its own in a temporary folder, standing in for the main
checkout, with each card's branch checked out in a real git worktree as the house makes them. The workshop's own
land()/landed() run with a stand-in house; health is stubbed (all well). What is checked:
  1. clean: a refusal that a merge of main clears: the house merges main into the branch, commits it, judges it again,
     and it lands
  2. a text conflict: the house leaves the markers in the file, uncommitted, keeps the builder's uncommitted work (now
     committed on the branch), says the files and the blocks on the card, card back to working; ready with a marker
     still in: refused, nothing committed; edited (no git) and ready: the house commits the merge and it lands with the
     builder's resolution
  3. a binary conflict: not merged, the card says which file is binary, no merge left half-done, the branch unchanged
  4. an untracked file in the worktree that main also adds: committed first, so it is never overwritten; it conflicts
     as text and the builder's words are inside the markers
"""
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
NOTATION = "research/text-desk-lab/notation"
sys.path.insert(0, str(HERE.parents[1] / "window-lab"))
import agora_tmp
from types import SimpleNamespace
import atexit
import shutil
tmp = SimpleNamespace(name=agora_tmp.directory("landing-regression-"))
atexit.register(shutil.rmtree, tmp.name, ignore_errors=True)
REPO = Path(tmp.name) / "live"
TREES = Path(tmp.name) / "trees"
os.environ["LANDING_LIVE"] = str(REPO)
os.environ["LANDING_ROOM"] = str(Path(tmp.name) / "room")
os.environ.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")

import roomworld   # noqa: E402
import workshop    # noqa: E402
import landing     # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build(say=False)
W = D.world
B = R.BOARD


def say(me, *lines):
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
    return out


class House:
    world = "roomworld-inmemory"
    dir = Path(tmp.name) / "house-state"

    def load(self):
        return W

    def act(self, who, line):
        from desk import split_batch
        out = say(who, *[p.strip() for p in split_batch(line)])
        if "ERR" in out:
            print("house refused:", line[:120], "->", out[-300:])
        return out


class Wk:
    """What land() needs of a worker: its branch, worktree, names and saved state."""
    def __init__(self, cid, tree):
        self.cid, self.branch, self.asked_by, self.actor = cid, f"worker/{cid}", "pike", f"worker-{cid}"
        self.tree = tree
        self.state, self.heard = {"session_provider": "codex"}, []

    def save(self):
        pass

    def send(self, text):
        self.heard.append(text)

    def alive(self):
        return True

    def log(self, kind, data):
        pass


def git(*args, cwd=REPO, ok=True):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if ok:
        assert r.returncode == 0, (args, r.stdout, r.stderr)
    return r.stdout.strip()


def put(root, name, data, msg=None):
    p = Path(root) / NOTATION / name
    p.parent.mkdir(parents=True, exist_ok=True)
    (p.write_bytes if isinstance(data, bytes) else lambda t: p.write_text(t, encoding="utf-8"))(data)
    if msg:
        git("add", "--", f"{NOTATION}/{name}", cwd=root)
        git("commit", "-q", "-m", msg, cwd=root)


def get(root, name):
    return (Path(root) / NOTATION / name).read_text(encoding="utf-8")


REPO.mkdir()
git("init", "-q", "-b", "main")
git("config", "core.autocrlf", "false")
put(REPO, "a.py", "".join(f"a{i} = {i}\n" for i in range(10)))
put(REPO, "pic.bin", b"PNG\0" + bytes(range(40)))
put(REPO, ".gitignore", "house-state/\nsessions/\n")
git("add", "-A")
git("commit", "-q", "-m", "start")

_git = workshop.git
workshop.git = lambda *a, cwd=REPO, **k: _git(*a, cwd=cwd, **k)     # its default cwd is the real checkout
workshop.REPO = REPO
landing.health = lambda world, cwd, **how: {"ok": True, "lenses_ok": [], "failed": [], "text": "all well"}
WS = workshop.Workshop(House())
WS.export_docs = lambda cid: ""
WS.compare_lived = lambda w: None
WS.finish = lambda cid, wk, keep_branch: None
WS.refresh_copies = lambda: None


def commission(title, files):
    """A card at ready, its branch made from main as it is now, checked out in a worktree of its own."""
    t = say("pike", f"look {B} :1", f'do create {B} kind=task title="{title}" owner=pike asked_by=pike status=open')
    card = re.findall(r"created (a\d+)", t)[-1]
    say("pike", f"look {card} :1", f"do prop {card} commission=asked")
    say("house", f"look {card} :1", f"do prop {card} commission=ready")
    tree = TREES / card
    git("worktree", "add", "-q", "-b", f"worker/{card}", str(tree), "main")
    for name, data in files.items():
        put(tree, name, data)
    git("add", "-A", cwd=tree)
    git("commit", "-q", "-m", f"{card}: {title}", cwd=tree)
    return card, W.nodes[card]["subject"], Wk(card, tree)


def on_main(files, msg):
    for name, data in files.items():
        put(REPO, name, data)
    git("add", "-A")
    git("commit", "-q", "-m", msg)


def said_since(sid, since):
    return [" ".join(str(v) for v in (e.get("args") or {}).values() if isinstance(v, str)) for e in W.events[since:]
            if e["by"] == "house" and e["verb"] == "comment"
            and (e["target"] == sid or (W.nodes.get(e["target"]) or {}).get("subject") == sid)]


def state(sid):
    return (W.subjects[sid].get("props") or {}).get("commission")


def ready(card):
    say("house", f"look {card} :1", f"do prop {card} commission=ready")


def merging(tree):
    return subprocess.run(["git", "rev-parse", "-q", "--verify", "MERGE_HEAD"], cwd=tree, capture_output=True).returncode == 0


# ---- 1. clean: what a merge of main clears is merged, committed, judged again and landed -------------------------------
K1, S1, wk1 = commission("Quiet", {"b.py": "# b\n"})
on_main({"c.py": "# c\n"}, "main moves")
mark = len(W.events)
WS.landed(W, K1, W.subjects[S1], wk1, {"landed": [], "refused": [(wk1.branch, "does not merge into main: (as if main moved)")],
                                        "parked": [], "text": ""})
said = said_since(S1, mark)
check("1. clean: the house merged main into the branch and said so", any("merged main into it (cleanly" in t for t in said), said)
check("1. clean: the branch holds main's change, by a merge commit of the house's",
      (TREES / K1 / NOTATION / "c.py").exists() and "Merge main into worker/" in git("log", "-1", "--format=%s", cwd=TREES / K1))
check("1. clean: judged again, and landed", state(S1) == "landed" and (REPO / NOTATION / "b.py").exists(), (state(S1), said))

# ---- 2. a text conflict: markers left for plain edits, then committed by the house -------------------------------------
K2, S2, wk2 = commission("Clash", {"a.py": get(REPO, "a.py").replace("a3 = 3\n", "a3 = 'branch'\n")})
on_main({"a.py": get(REPO, "a.py").replace("a3 = 3\n", "a3 = 'main'\n")}, "main changes the same line")
put(TREES / K2, "notes.md", "the builder's unsaved notes\n")            # uncommitted work in the worktree
head_before = git("rev-parse", "HEAD", cwd=TREES / K2)
mark = len(W.events)
WS.land(W, K2, W.subjects[S2], wk2)
said = said_since(S2, mark)
text = get(TREES / K2, "a.py")
check("2. conflict: back to working, the card names the file and shows the block with both sides",
      state(S2) == "working" and any("a.py" in t and "<<<<<<<" in t and "a3 = 'branch'" in t and "a3 = 'main'" in t for t in said), said)
check("2. conflict: the markers are in the file, not committed (a merge in progress)",
      "<<<<<<<" in text and ">>>>>>>" in text and merging(TREES / K2), text)
check("2. conflict: the builder's uncommitted work was committed first, never lost",
      "notes.md" in git("show", "--name-only", "--format=", "HEAD", cwd=TREES / K2) and
      get(TREES / K2, "notes.md") == "the builder's unsaved notes\n" and head_before != git("rev-parse", "HEAD", cwd=TREES / K2))
check("2. conflict: the worker is told, with the files to edit", any("a.py" in h and "no git" in h for h in wk2.heard), wk2.heard)
check("2. conflict: main is untouched", "a3 = 'main'" in get(REPO, "a.py") and "branch" not in get(REPO, "a.py"))

ready(K2)
mark = len(W.events)
WS.land(W, K2, W.subjects[S2], wk2)
said = said_since(S2, mark)
check("2. ready with a marker still in: refused, back to working, nothing committed",
      state(S2) == "working" and any("still in" in t for t in said) and merging(TREES / K2), said)

resolved = re.sub(r"<<<<<<<[^\n]*\n.*?>>>>>>>[^\n]*\n", "a3 = 'both'\n", text, flags=re.S)
put(TREES / K2, "a.py", resolved)                                        # a plain file edit, no git
ready(K2)
mark = len(W.events)
WS.land(W, K2, W.subjects[S2], wk2)
said = said_since(S2, mark)
check("2. edited and ready: the house committed the merge and said so", any("the house committed the merge" in t for t in said)
      and not merging(TREES / K2), said)
check("2. and it landed with the builder's resolution", state(S2) == "landed" and "a3 = 'both'" in get(REPO, "a.py")
      and "<<<<<<<" not in get(REPO, "a.py"), (state(S2), get(REPO, "a.py")))

# ---- 3. a binary conflict: refused with a clear comment, nothing left half-done --------------------------------------
K3, S3, wk3 = commission("Picture", {"pic.bin": b"PNG\0branch" + bytes(range(30))})
on_main({"pic.bin": b"PNG\0main" + bytes(range(50))}, "main changes the picture")
head3 = git("rev-parse", "HEAD", cwd=TREES / K3)
mark = len(W.events)
WS.land(W, K3, W.subjects[S3], wk3)
said = said_since(S3, mark)
check("3. binary: back to working, the card says which file is binary and that nothing was merged",
      state(S3) == "working" and any("binary" in t and "pic.bin" in t for t in said), said)
check("3. binary: no merge left in progress, the branch where it was",
      not merging(TREES / K3) and git("rev-parse", "HEAD", cwd=TREES / K3) == head3
      and (TREES / K3 / NOTATION / "pic.bin").read_bytes().startswith(b"PNG\0branch"))

# ---- 4. an untracked file in the worktree that main also adds ---------------------------------------------------------
K4, S4, wk4 = commission("Both", {"a.py": get(REPO, "a.py").replace("a7 = 7\n", "a7 = 'branch'\n")})
on_main({"a.py": get(REPO, "a.py").replace("a7 = 7\n", "a7 = 'main'\n"), "new.txt": "main's new file\n"}, "main adds new.txt")
put(TREES / K4, "new.txt", "the builder's own new.txt, never committed\n")
mark = len(W.events)
WS.land(W, K4, W.subjects[S4], wk4)
said = said_since(S4, mark)
new = get(TREES / K4, "new.txt")
check("4. untracked collision: committed first, then a text conflict the card lists",
      state(S4) == "working" and any("new.txt" in t for t in said) and merging(TREES / K4), said)
check("4. untracked collision: the builder's words are kept, inside the markers beside main's",
      "the builder's own new.txt" in new and "main's new file" in new and "<<<<<<<" in new, new)

print(f"{len(fails)} FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
