"""handbook_docs: the design documents, carried in the Handbook.

    python handbook_docs.py [world]          default world: frontier

Copies docs/Agora.md, docs/Dynamic Desk.md and AGENTS.md, verbatim, into the Handbook binder "What we're building" as
the notes "Agora", "Dynamic Desk" and "AGENTS.md" (Alex, 29 Sep: a handbook "like an always with them documentation",
instead of a library). The files are the source and Alex's: edit them there, then run this again (the keeper's
docs_sync watch does, within a minute of a file or the checkout's HEAD changing). It is the reverse of
export_docs.py, which makes the Handbook binder "How the desk is built" the source of Current Implementation.
Each note says how old it is in two props, since a reader inside the world cannot see the file: carried= is when
its text was last written here, revision= is the commit that last changed the file and that commit's date, or
"edited <date> after <commit>, uncommitted" when the file on disk is newer than git. A note whose text and revision
already match is left alone, so running it with nothing changed makes no event. Acts as `claude` through the desk, so
every change is an ordinary event with an author and an undo. Exits 1 if any note could not be written.
"""
import os
import pathlib
import re
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BINDER = "What we're building"
INTRO = ("These are the design documents and AGENTS.md (how we work), carried here so they go wherever you do. Agora "
         "is the larger goal everything here works toward; Dynamic Desk is what we are building first, with each "
         "claim marked Held, Leaning or Open. They are copies: the originals are Alex's files, and the keeper's "
         "docs_sync watch runs handbook_docs.py within a minute of one changing. Each copy's carried= says when it "
         "was written here and revision= which commit of the file it matches, so you can tell a copy that is behind. "
         "Don't edit them here; say what you'd change to Alex, or in the Lounge.")
DOCUMENTS = [("Agora", "docs/Agora.md"), ("Dynamic Desk", "docs/Dynamic Desk.md"), ("AGENTS.md", "AGENTS.md")]


def desk(world, lines):
    p = subprocess.run([sys.executable, "explore.py", world, "--as", "claude"], cwd=HERE, input="\n".join(lines) + "\n",
                       capture_output=True, text=True, encoding="utf-8", env=os.environ)
    return p.stdout + p.stderr


def quote(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\r\n", "\n").replace("\n", "\\n") + '"'


def git(*args):
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    return p.stdout.strip() if p.returncode == 0 else ""


def revision(name):
    """Which revision of the file the copy is: its last commit and that commit's date, or that it is newer than git."""
    last = git("log", "-1", "--format=%h of %ad", "--date=format:%d %b %Y", "--", name)
    if last and not git("status", "--porcelain", "--", name):
        return last
    edited = time.strftime("%d %b %Y", time.localtime((ROOT / name).stat().st_mtime))
    return f"edited {edited} after {last.split()[0]}, uncommitted" if last else f"edited {edited}, not in git"


def main():
    world = sys.argv[1] if len(sys.argv) > 1 else "frontier"
    shelf = desk(world, ["look Handbook :2"])
    m = re.search(r"(f\d+) surface \"What we're building\"", shelf)
    if m:
        fid = m.group(1)
    else:
        first = re.search(r"\n  (a\d+) note \"A shelf", shelf)
        out = desk(world, ["look Handbook :2", f'do create Handbook kind=surface title="{BINDER}" layout=column']
                   + ([f"do move $new after={first.group(1)}"] if first else []))
        fid = re.search(r"created (f\d+)", out).group(1)
        desk(world, [f"look {fid} :1", f"do create {fid} kind=note title=\"How these got here\" text={quote(INTRO)}"])
        print(f"made the binder {fid} in the Handbook")
    inside = desk(world, [f"look {fid} :2"])
    failed = False
    for title, name in DOCUMENTS:
        text = (ROOT / name).read_text(encoding="utf-8").replace("\r\n", "\n").strip()
        rev, today = revision(name), time.strftime("%d %b %Y %H:%M")
        m = re.search(rf"(a\d+) note \"{re.escape(title)}\".*", inside)
        if not m:
            out = desk(world, [f"look {fid} :1", f"do create {fid} kind=note title=\"{title}\" source=\"{name}\" "
                               f"carried=\"{today}\" revision=\"{rev}\" text={quote(text)}"])
            ok = "created" in out
            print(f"{title}: " + ("copied in, " + re.search(r"created (a\d+)", out).group(1) if ok else "ERR " + out[-300:]))
            failed |= not ok
            continue
        nid, line = m.group(1), m.group(0)
        # read prints a head line, ---, the text, ---, then links and comments. The copy matches only if the text is
        # all there is between the rules: a copy that merely contains it (the file lost its last lines) is behind.
        body = desk(world, [f"read {nid} :3"]).partition("\n---\n")[2]
        if body.startswith(text + "\n---\n") and "\n---\n" not in body[len(text) + 4:]:
            if f"revision={rev} " in line and "carried=" in line:
                print(f"{title}: {nid} already matches {name} ({rev})")
                continue
            # the words are the same and only what is known about them moved (a commit, or a copy never stamped):
            # carried= stays the day the words were written here; a copy never stamped can only say "by today"
            since = "" if "carried=" in line else f' carried="on or before {today}"'
            out = desk(world, [f"look {nid} :1", f'do prop {nid}{since} revision="{rev}"'])
            ok = "ok prop" in out
            print(f"{title}: " + (f"{nid} matches {name}; now says {rev}" if ok else "ERR " + out[-300:]))
            failed |= not ok
            continue
        out = desk(world, [f"look {nid} :1", f"do rewrite {nid} text={quote(text)}",
                           f'do prop {nid} carried="{today}" revision="{rev}"'])
        ok = "ok rewrite" in out and ("ok prop" in out or "nothing to change" in out)     # same minute, same commit
        print(f"{title}: " + (f"updated {nid} to {rev}" if ok else "ERR " + out[-300:]))
        failed |= not ok
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
