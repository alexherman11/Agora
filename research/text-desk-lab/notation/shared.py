"""shared: files many hands touch at once (a5296, from a5261 points 3-5; Alex wants many workers at once).

A commission is asked against files. Two things about a file make a worker discover trouble late, and both are known
the moment the card is asked:
  - it is uncommitted in the main checkout (the live one, where hand sessions work): new and never committed, no
    worker's branch has it at all (hud.py, 15 Oct: the Spotify worker could not edit it); with uncommitted edits, the
    branch has main's version while someone works on another (Codex's lens.js, which held up a4465 and a4473);
  - someone has said they are in it: a card with prop in_files=<paths> (the Handbook's rule for a session in a file).

check() reads both for one card. The house (workshop.step) calls it for every asked card before it looks for a slot,
so the card hears at once: a new, never-committed file holds the card until it is committed (or the card says
uncommitted=ok: it only mentions the file); the rest is a note, said once, and told to the worker when it starts.
A file is named by its path or its base name (lens.js, desk-shell/lens.js), as a word in the card's title or text.
"""
import re
import subprocess
from pathlib import Path

NOTATION = "research/text-desk-lab/notation"
SKIP = (f"{NOTATION}/sessions/", f"{NOTATION}/house-state/")     # worlds and the house's own state are never source
_POPEN = subprocess.Popen          # as imported: a test that stubs Popen for the workers it starts still reads git here


def uncommitted(live):
    """Paths with uncommitted changes in the checkout `live` (tracked or new), worlds aside. -> {path: how}, how one of
    'new' (no commit has it: untracked, or only added), 'changed', 'deleted'."""
    p = _POPEN(["git", "status", "--porcelain", "--untracked-files=all"], cwd=live, stdout=subprocess.PIPE,
               stderr=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace")
    stdout = p.stdout.read()                  # one pipe, read to its end: no thread (communicate makes them on Windows)
    p.wait(timeout=60)
    out = {}
    for line in (stdout or "").splitlines() if p.returncode == 0 else []:
        code, p = line[:2], line[3:].strip().strip('"')
        if " -> " in p:
            p = p.split(" -> ", 1)[1]
        if not p or p.startswith(SKIP) or p.endswith(".env"):
            continue
        out[p] = "new" if code in ("??", "A ", "AM", "AD") else "deleted" if "D" in code else "changed"
    return out


def mentions(text, path):
    """Does `text` name `path`, by itself or its base name, as a word? Base names shorter than four letters never count."""
    name = Path(path).name
    for word in dict.fromkeys((path, name)):
        if len(word) >= 4 and re.search(r"(?<![\w-])" + re.escape(word) + r"(?![\w-])", text):
            return True
    return False


def claims(w, but=None):
    """Who has said they are in which files: every subject with prop in_files (paths or base names, split on spaces or
    commas), but the subject `but`. -> [(word, appearance id, title, owner)]."""
    out = []
    for sid, s in w.subjects.items():
        said = str((s.get("props") or {}).get("in_files") or "").strip()
        if not said or said.lower() in ("none", "-") or sid == but:      # in_files=none: out of every file again
            continue
        apps = w.appearances_of(sid)
        for word in re.split(r"[\s,]+", said):
            if word:
                out.append((word, apps[0] if apps else sid, s.get("title", ""), (s.get("props") or {}).get("owner", "")))
    return out


def check(s, live, w=None, available=()):
    """One card against the checkout `live` and the world's claims. -> {hold: [path], note: [path], claimed: [...],
    key: what was found as one word (the house writes it on the card, so it is said once), text: what to say, worker:
    what to tell the worker, '' when nothing}."""
    text = f"{s.get('title', '')}\n{s.get('text') or ''}"
    dirty = uncommitted(live)
    named = {p: how for p, how in dirty.items() if mentions(text, p)}
    # A house-preserved handoff can supply files before they land on main.
    # The caller verifies its receipt/commit; this does not publish those files.
    hold = sorted(p for p, how in named.items() if how == "new" and p not in available)
    note = sorted(p for p, how in named.items() if how != "new")
    claimed = [(word, aid, title, owner) for word, aid, title, owner in (claims(w, s.get("id")) if w else [])
               if mentions(text, word)]
    key = " ".join([f"{p}:{named[p]}" for p in hold + note] + [f"{word}@{aid}" for word, aid, _, _ in claimed])
    said, worker = [], []
    if hold:
        files = ", ".join(hold)
        said.append(f"held: this names {files}, new in the main checkout and never committed, so no worker's branch has "
                    f"it. Whoever made it lands it (python {NOTATION}/landing.py --files <path> --as <name> --why \"...\"), "
                    "and this starts on its own once it is committed. If the card only mentions it, set uncommitted=ok "
                    "and it starts now.")
        worker.append(f"{files}: new in the main checkout and not committed; your branch does not have it. Don't "
                      "recreate it: ask on the commission.")
    if note:
        files = ", ".join(f"{p} ({named[p]})" for p in note)
        said.append(f"note: {files} uncommitted in the main checkout. The worker's branch has main's version; a landing "
                    "that changes the file keeps those edits on a parked/ branch and puts them back on top, where they "
                    "may conflict. Agree with whoever is in it first.")
        worker.append(f"{files}: someone has uncommitted edits to it in the main checkout; your branch has main's "
                      "version. Change it only as the commission needs, and say so in your done comment.")
    for word, aid, title, owner in claimed:
        said.append(f"note: {aid} \"{title[:60]}\"{' (' + owner + ')' if owner else ''} says it is in {word} (in_files).")
        worker.append(f"{aid} \"{title[:60]}\" says it is in {word}: read that card before you change it.")
    return {"hold": hold, "note": note, "claimed": claimed, "key": key, "text": " ".join(said),
            "worker": ("The house found, when this was asked: " + " ".join(worker)) if worker else ""}
