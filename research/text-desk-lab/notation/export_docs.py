"""export_docs: the desk is the source of Current Implementation; the markdown files are its exports.

    python export_docs.py [session] [--force] [--dry]

Reads the Handbook binder "How the desk is built" in the world (default `frontier`): its first note is the
document's title and introduction, and each later note is one `## section` (title = heading, text = body), in the
binder's order. Writes `Current Implementation.md` to the repo's docs/ and to Alex's Obsidian vault, and a text
`export` of the whole world beside the lab notes, so the record stays diffable (the pickle is not). It also writes
research/command-center/FRICTION.md from Rough spots (friction.py): one way, overwritten whole whenever it differs.

Each markdown export ends with a stamp naming the event it was exported at and a hash of what it wrote. When a file
no longer matches its stamp, someone edited the export directly: the script warns and leaves that file alone
(--force overwrites). Move the edit into the desk, then export again. A file whose content would not change is
left untouched, so a round with no Handbook edits makes no diff.

The world is loaded the way explore.py and deskd load it, under the session's lock, and nothing is saved.
"""

import hashlib
import pickle
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SESSIONS = HERE / "sessions"
BINDER = "How the desk is built"
DOC = "Current Implementation.md"
TARGETS = [Path("C:/Projects/Agora4/docs") / DOC, Path("C:/Projects/Agora/docs") / DOC]
WORLD_EXPORT = HERE.parent.parent / "object-facet-frontier" / "desk-export.txt"
STAMP = re.compile(r"\n*<!-- exported from the desk: .*? sha1:([0-9a-f]{12}) -->\n*\Z", re.S)


def load(session):
    """The saved desk, read under the same lock explore.py and deskd take from load to save."""
    import explore
    lock = SESSIONS / f"{session}.lock"
    # explore's lock: pid-aware, and it gives up rather than read without it. Review 29 Sep: this loop read unlocked
    # after 60 s and then removed a lock it had never taken, which could be another process's.
    try:
        explore.take_lock(lock)
    except SystemExit as e:        # the house calls this every pass: a busy lock is a failed step, retried, not an exit
        raise RuntimeError(str(e)) from None
    try:
        return pickle.loads((SESSIONS / f"{session}.pickle").read_bytes())
    finally:
        explore.release_lock(lock)


def binder_notes(world):
    hits = [n for n in world.nodes.values() if n["type"] == "surface" and n.get("title") == BINDER]
    if len(hits) != 1:
        sys.exit(f"expected one surface titled {BINDER!r}, found {len(hits)}")
    notes = [world.subjects[k["subject"]] for k in world.children(hits[0]["id"]) if k["type"] == "appearance"]
    if not notes:
        sys.exit(f"{BINDER!r} is empty")
    return notes


def join(notes):
    """First note: '# title' and the introduction. Each later note: '## title' and its body."""
    head, rest = notes[0], notes[1:]
    parts = [f"# {head['title']}\n\n{head['text'].strip()}"]
    parts += [f"## {s['title']}\n\n{s['text'].strip()}" if s["text"].strip() else f"## {s['title']}" for s in rest]
    return "\n\n".join(parts) + "\n"


def split(md):
    """The inverse of join, for importing a document into the binder: [(title, text)], the first is the title."""
    md = STAMP.sub("\n", md.replace("\r\n", "\n"))
    lines, fence, out = md.split("\n"), False, []
    for line in lines:
        if line.startswith("```"):
            fence = not fence
        if not fence and (line.startswith("# ") or line.startswith("## ")):
            out.append([line.split(" ", 1)[1].strip(), []])
        elif out:
            out[-1][1].append(line)
    return [(t, "\n".join(body).strip()) for t, body in out]


def sha(text):
    return hashlib.sha1(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()[:12]


def write(path, body, event, session, force, dry):
    stamp = (f"\n<!-- exported from the desk: world {session}, Home > Handbook > {BINDER}, at event {event}. "
             f"Edit it there; a direct edit here makes the next export stop and warn. sha1:{sha(body)} -->\n")
    if path.exists():
        raw = path.read_bytes().decode("utf-8")
        crlf = "\r\n" in raw
        old = raw.replace("\r\n", "\n")
        m = STAMP.search(old)
        old_body = old[:m.start()].rstrip("\n") + "\n" if m else old
        if old_body == body and m:
            return f"unchanged  {path}"
        # no stamp yet: an identical file just gains one; a different file has unknown edits
        edited = old_body != body and (not m or sha(old_body) != m.group(1))
        if edited and not force:
            return (f"WARNING    {path} was edited outside the desk (it no longer matches its export stamp); left alone. "
                    f"Move the edit into the Handbook, then export again (--force overwrites)")
    else:
        crlf = False
    if dry:
        return f"would write {path}"
    text = body + stamp
    path.write_bytes((text.replace("\n", "\r\n") if crlf else text).encode("utf-8"))
    return f"wrote      {path}"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    session = args[0] if args else "frontier"
    force, dry = "--force" in sys.argv, "--dry" in sys.argv
    desk = load(session)
    world = desk.world
    body = join(binder_notes(world))
    event = world.events[-1]["id"] if world.events else "e0"
    for path in TARGETS:
        print(write(path, body, event, session, force, dry))
    import friction       # a778: FRICTION.md is Rough spots, exported one way (overwritten whole, no stamp to check)
    print(friction.write(friction.export(world, session), dry))
    if session == "frontier":
        text = desk.cmd_export().rstrip("\n") + "\n"
        if dry:
            print(f"would write {WORLD_EXPORT}")
        elif WORLD_EXPORT.exists() and WORLD_EXPORT.read_text(encoding="utf-8") == text:
            print(f"unchanged  {WORLD_EXPORT}")
        else:
            WORLD_EXPORT.write_text(text, encoding="utf-8", newline="\n")
            print(f"wrote      {WORLD_EXPORT}")


if __name__ == "__main__":
    main()
