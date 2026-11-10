"""friction: Rough spots (f747) is the list of frictions; research/command-center/FRICTION.md is its one-way export.

    python friction.py freeze                 copy the hand-written FRICTION.md to research/archive/ (once, a778)
    python friction.py lines [source.md]      print a look, then one desk `create` line per entry F<n>, for the import
    python friction.py check <session> [source.md]
                                              compare each note with f=F<n> in the world with its entry, word for word
    python friction.py export <session> [--dry]
                                              write FRICTION.md from the world: every placed note with a family= prop,
                                              grouped by status, each with its id and f= if it has one

A friction is a note with family= (a769, Revision 1): status=open|curing|cured, or unchecked for an entry imported and
not yet checked. The world is the list. The export is one-way: its first line says so, and every export overwrites
the file whole, so an edit made to the file is gone at the next export. export_docs.py runs it after each landing.

`source.md` defaults to the frozen hand-written log, research/archive/FRICTION-by-hand-to-29-Sep.md.
The world is read under its lock (export_docs.load) and nothing is saved.
"""

import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent.parent
EXPORT = RESEARCH / "command-center" / "FRICTION.md"
FROZEN = RESEARCH / "archive" / "FRICTION-by-hand-to-29-Sep.md"
HOME = "f747"                                            # Rough spots, in Frontier
ORDER = ["open", "curing", "unchecked", "cured"]         # a769 Revision 1; any other status follows, by name
HEAD = re.compile(r"^## F(\d+)\. (.+?)\s*$")


def entries(path=FROZEN):
    """[(n, title, text)] from a hand-written log: '## F<n>. <title>' starts an entry; its text is every line up to
    the next '## ', with blank lines trimmed at both ends and nothing else changed."""
    out = []
    for line in Path(path).read_text(encoding="utf-8").replace("\r\n", "\n").split("\n"):
        m = HEAD.match(line)
        if m:
            out.append([int(m.group(1)), m.group(2), []])
        elif line.startswith("## "):
            sys.exit(f"a heading that is not an entry: {line!r}")
        elif out:
            out[-1][2].append(line)
    return [(n, t, "\n".join(body).strip("\n")) for n, t, body in out]


def q(s):
    """A desk value, quoted as desk_knife's export quotes it: shlex and the do parser each halve a backslash, \\n is
    a newline, and $today is written \\$today so it isn't filled when the line runs."""
    return '"' + str(s).replace("\\", "\\\\\\\\").replace('"', '\\"').replace("\n", "\\n").replace("$today", "\\$today") + '"'


def lines(path=FROZEN):
    """A look first: the desk refuses a create into a surface its author hasn't seen."""
    return [f"look {HOME}"] + [f"do create {HOME} title={q(t)} text={q(text)} f=F{n} status=unchecked family=unsorted"
                               for n, t, text in entries(path)]


def placed(world):
    """{subject id: [appearance ids]} for every subject that appears somewhere."""
    out = {}
    for n in world.nodes.values():
        if n["type"] == "appearance":
            out.setdefault(n["subject"], []).append(n["id"])
    return out


def num(i):
    return int(re.sub(r"\D", "", i) or 0)


def check(world, path=FROZEN):
    """Every entry has exactly one placed note with its f=, whose title and text are the entry's; returns the faults."""
    want = {f"F{n}": (t, text) for n, t, text in entries(path)}
    where = placed(world)
    have = {}
    for sid, s in world.subjects.items():
        f = (s.get("props") or {}).get("f")
        if f and sid in where:
            have.setdefault(f, []).append(s)
    faults = []
    for f, (t, text) in want.items():
        got = have.get(f, [])
        if len(got) != 1:
            faults.append(f"{f}: {len(got)} placed notes with f={f}")
            continue
        s = got[0]
        if s["title"] != t:
            faults.append(f"{f}: title {s['title']!r} is not {t!r}")
        if s["text"] != text:
            k = next((i for i, (a, b) in enumerate(zip(s["text"], text)) if a != b), min(len(s["text"]), len(text)))
            faults.append(f"{f}: text differs at character {k}: world {s['text'][k:k + 40]!r}, entry {text[k:k + 40]!r}")
    faults += [f"{f}: in the world, not in the source" for f in have if f not in want]
    return faults, len(want)


def export(world, session):
    """The whole file, from the world."""
    where = placed(world)
    groups = {}
    for sid, s in world.subjects.items():
        p = s.get("props") or {}
        if "family" in p and sid in where:
            groups.setdefault(p.get("status") or "(no status)", []).append(s)
    statuses = [x for x in ORDER if x in groups] + sorted(x for x in groups if x not in ORDER)
    out = [f"> Generated from the world {session} by friction.py; one way. Editing this file changes nothing, and the "
           f"next export overwrites it. The list lives in the desk: Rough spots ({HOME}) in Frontier.",
           "",
           "# Rough spots",
           "",
           "Every note in the world with a `family=` prop, grouped by status (a769: open, curing, cured; unchecked is "
           "imported from the hand-written log, F1 to F32, and not yet checked). To add one: `do create "
           f"{HOME} title=\"...\" text=\"...\" family=<family> status=open`.",
           ""]
    for st in statuses:
        notes = sorted(groups[st], key=lambda s: (num((s["props"].get("f") or "F999999")), num(where[s["id"]][0])))
        out += [f"## {st} ({len(notes)})", ""]
        for s in notes:
            p = s["props"]
            meta = [", ".join(sorted(where[s["id"]], key=num)), f"family={p['family']}", f"status={p.get('status', '')}"]
            if p.get("f"):
                meta.append(f"f={p['f']}")
            out += [f"### {p['f'] + '. ' if p.get('f') else ''}{s['title']}", "", " · ".join(meta), ""]
            if s["text"].strip():
                out += [s["text"].strip("\n"), ""]
    return "\n".join(out).rstrip("\n") + "\n"


def write(body, dry=False):
    """Overwrite the export whole when it differs: one-way, so a hand edit is simply gone."""
    old = EXPORT.read_bytes().decode("utf-8").replace("\r\n", "\n") if EXPORT.exists() else None
    if old == body:
        return f"unchanged  {EXPORT}"
    if dry:
        return f"would write {EXPORT}"
    EXPORT.write_text(body, encoding="utf-8", newline="\n")
    return f"wrote      {EXPORT}"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    cmd, rest = args[0], args[1:]
    if cmd == "freeze":
        if FROZEN.exists():
            sys.exit(f"{FROZEN} exists already; left alone")
        shutil.copyfile(EXPORT, FROZEN)
        print(f"copied {EXPORT} to {FROZEN}")
    elif cmd == "lines":
        for line in lines(rest[0] if rest else FROZEN):
            print(line)
    elif cmd in ("check", "export"):
        import export_docs
        session = rest[0] if rest else "frontier"
        world = export_docs.load(session).world
        if cmd == "check":
            faults, n = check(world, rest[1] if len(rest) > 1 else FROZEN)
            for f in faults:
                print(f)
            print(f"{n} entries; {n - len({f.split(':')[0] for f in faults})} identical in the world; {len(faults)} faults")
            sys.exit(1 if faults else 0)
        print(write(export(world, session), "--dry" in sys.argv))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
