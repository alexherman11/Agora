"""handbook_docs: the design documents, carried in the Handbook.

    python handbook_docs.py [world]          default world: frontier

Copies docs/Agora.md and docs/Dynamic Desk.md, verbatim, into the Handbook binder "What we're building" as the notes
"Agora" and "Dynamic Desk" (Alex, 29 Sep: a handbook "like an always with them documentation", instead of a library).
The docs are the source and Alex's: edit them there, then run this again. It is the reverse of export_docs.py, which
makes the Handbook binder "How the desk is built" the source of Current Implementation. A note whose text already
matches is left alone, so running it with nothing changed makes no event. Acts as `claude` through the desk, so every
change is an ordinary event with an author and an undo.
"""
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
DOCS = HERE.parents[2] / "docs"
BINDER = "What we're building"
INTRO = ("These are the design documents, carried here so they go wherever you do. Agora is the larger goal "
         "everything here works toward; Dynamic Desk is what we are building first, with each claim marked Held, "
         "Leaning or Open. They are copies: the originals are Alex's, in docs/, and handbook_docs.py copies them "
         "here when they change. Don't edit them here; say what you'd change to Alex, or in the Lounge.")
DOCUMENTS = [("Agora", "Agora.md"), ("Dynamic Desk", "Dynamic Desk.md")]


def desk(world, lines):
    p = subprocess.run([sys.executable, "explore.py", world, "--as", "claude"], cwd=HERE, input="\n".join(lines) + "\n",
                       capture_output=True, text=True, encoding="utf-8", env=os.environ)
    return p.stdout + p.stderr


def quote(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\r\n", "\n").replace("\n", "\\n") + '"'


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
    for title, name in DOCUMENTS:
        text = (DOCS / name).read_text(encoding="utf-8").replace("\r\n", "\n").strip()
        m = re.search(rf"(a\d+) note \"{re.escape(title)}\"", inside)
        if not m:
            out = desk(world, [f"look {fid} :1", f"do create {fid} kind=note title=\"{title}\" source=\"docs/{name}\" text={quote(text)}"])
            print(f"{title}: " + ("copied in, " + re.search(r"created (a\d+)", out).group(1) if "created" in out else "ERR " + out[-300:]))
            continue
        nid = m.group(1)
        now = desk(world, [f"read {nid} :3"])
        if text in now:
            print(f"{title}: {nid} already matches docs/{name}")
            continue
        out = desk(world, [f"look {nid} :1", f"do rewrite {nid} text={quote(text)}"])
        print(f"{title}: " + ("updated " + nid if "ok rewrite" in out else "ERR " + out[-300:]))


if __name__ == "__main__":
    main()
