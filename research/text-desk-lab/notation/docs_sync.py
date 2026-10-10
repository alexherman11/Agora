"""docs_sync: keeps the five design documents the same in the repo's docs/ and in Alex's Obsidian vault.

    python docs_sync.py [--watch [seconds]] [--with <pid>] [--no-handbook]     default: one pass; --watch every 60 s

Two copies, either may be edited (Alex, 29 Sep: "both stay up to date automatically"). For each document it compares
the two copies, ignoring line endings (the vault keeps CRLF, the repo LF, and each keeps its own):
  - the same: remembered as the last agreed text;
  - one side still matches the last agreed text: the other side was edited, and is copied over;
  - both sides moved away from it, or they differ and were never agreed: refused, both left as they are, and the
    first differing line of each printed. Nothing guesses which edit wins. Make them agree by hand; the next pass
    remembers them.
When Agora or Dynamic Desk changes, it runs handbook_docs.py, so the Handbook's copies in the world follow.
Current Implementation's source is the Handbook binder (export_docs.py); an edit made to either markdown copy is still
carried to the other, and export_docs.py then warns that the export was edited directly, as it always has.
The last agreed text is kept as a hash in house-state/docs_sync.json (not in git). It never commits.
The keeper runs the watch (Alex, 9 Oct: it runs with the keeper, dies with the keeper, and there are never two):
--with <pid> ends the watch within 2 s of that process ending, however it ended, and a watch holds
house-state/docs_sync.lock for as long as it lives, so a second one says so and exits. The lock is the operating
system's, on the open file: it goes when its holder does and is never stale.
"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import explore       # _alive(): is a pid still running

HERE = Path(__file__).resolve().parent
REPO_DOCS = HERE.parents[2] / "docs"
VAULT_DOCS = Path("C:/Projects/Agora/docs")
ANOTHER = 76         # the exit code for "another watch already runs", as the house's is for another house
NAMES = ["Agora.md", "Agora Constitution.md", "Dynamic Desk.md", "Current Implementation.md", "Previous Work.md"]
HANDBOOK = {"Agora.md", "Dynamic Desk.md"}
STATE = HERE / "house-state" / "docs_sync.json"
LOCK = HERE / "house-state" / "docs_sync.lock"


def read(p):
    raw = p.read_bytes().decode("utf-8")
    return raw.replace("\r\n", "\n"), "\r\n" in raw


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write(p, text, crlf):
    p.write_bytes((text.replace("\n", "\r\n") if crlf else text).encode("utf-8"))


def first_difference(a, b):
    la, lb = a.split("\n"), b.split("\n")
    for i, (x, y) in enumerate(zip(la, lb)):
        if x != y:
            return i + 1, x[:100], y[:100]
    return min(len(la), len(lb)) + 1, "(ends)" if len(la) < len(lb) else "", "(ends)" if len(lb) < len(la) else ""


def one_pass(handbook=True):
    STATE.parent.mkdir(exist_ok=True)
    try:
        agreed = json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        agreed = {}
    said, moved = [], set()
    for name in NAMES:
        a, b = REPO_DOCS / name, VAULT_DOCS / name
        if not a.exists() or not b.exists():
            said.append(f"refused {name}: missing in {'the repo' if not a.exists() else 'the vault'}; copy it by hand")
            continue
        (ta, a_crlf), (tb, b_crlf) = read(a), read(b)
        if ta == tb:
            agreed[name] = digest(ta)
            continue
        last = agreed.get(name)
        if last and digest(ta) == last:
            write(a, tb, a_crlf)
            said.append(f"{name}: the vault's edit copied to the repo")
            agreed[name] = digest(tb)
            moved.add(name)
        elif last and digest(tb) == last:
            write(b, ta, b_crlf)
            said.append(f"{name}: the repo's edit copied to the vault")
            agreed[name] = digest(ta)
            moved.add(name)
        else:
            n, x, y = first_difference(ta, tb)
            why = "both copies changed since they last agreed" if last else "the copies differ and have never agreed"
            said.append(f"refused {name}: {why}; nothing written. First difference, line {n}:\n"
                        f"    repo:  {x}\n    vault: {y}")
    STATE.write_text(json.dumps(agreed, indent=1), encoding="utf-8")
    if handbook and moved & HANDBOOK:
        r = subprocess.run([sys.executable, "handbook_docs.py"], cwd=HERE, capture_output=True, text=True,
                           encoding="utf-8")
        said.append("handbook_docs.py: " + ((r.stdout or r.stderr).strip().splitlines() or ["(no output)"])[-1])
    return said


def only_one():
    """The open, locked file, or None when another watch holds it. Keep the result: the lock lasts as long as it does."""
    LOCK.parent.mkdir(exist_ok=True)
    f = open(LOCK, "a+")
    try:
        if sys.platform == "win32":
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        return None
    return f


def main():
    handbook = "--no-handbook" not in sys.argv
    if "--watch" not in sys.argv:
        print("\n".join(one_pass(handbook)) or "all five agree")
        return
    i = sys.argv.index("--watch")
    every = int(sys.argv[i + 1]) if len(sys.argv) > i + 1 and sys.argv[i + 1].isdigit() else 60
    keeper = int(sys.argv[sys.argv.index("--with") + 1]) if "--with" in sys.argv[:-1] else None
    held = only_one()
    if not held:
        print(time.strftime("%Y-%m-%d %H:%M:%S ") + "docs_sync: another watch is already running; not starting a second", flush=True)
        sys.exit(ANOTHER)
    print(f"docs_sync: watching every {every} s" + (f", for as long as {keeper} runs" if keeper else ""), flush=True)
    before = set()
    while True:
        said = one_pass(handbook)
        for line in said:
            if line not in before:          # a standing refusal is said once, not every pass
                print(time.strftime("%Y-%m-%d %H:%M:%S "), line, flush=True)
        before = set(said)
        until = time.time() + every
        while time.time() < until:
            time.sleep(2)
            if keeper and not explore._alive(keeper):
                print(time.strftime("%Y-%m-%d %H:%M:%S ") + f"docs_sync: {keeper} is gone; stopping", flush=True)
                return


if __name__ == "__main__":
    main()
