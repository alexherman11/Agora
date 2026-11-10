"""Names, not ids (a6109): the world half. The painter now draws every id in words as the name of what it names (scene
things_of, lens.js); these lines make a press on a name open it in the home base's viewer, and give the HUD's own
id-printing lines names. Kept as files so they can be read, tried on a copy, and applied to the live world AFTER the
code has landed (`on link` on any part; the `ids` word).

    python src/desktop/names/apply.py lines <out.desk>     the lines (explore.py <world> --as <you> < out.desk)
    python src/desktop/names/apply.py check [--as <name>] [--port 8794] [--world frontier]
                                         every old= passage against the world's text now (each must stand once)
    python src/desktop/names/apply.py door [--as <name>] [--port 8794] [--world frontier]
                                         all of it through a door, line by line, stopping at the first refusal;
                                         it checks every passage first and keeps each note's live text in before-a6109/

What the lines do, all world data anyone may change afterwards:
  - a house verb `view <id>` (view.verb): opens it in your viewer (role=home-view, actor=you), with Back;
  - home-base (a5208): `on link do view $value` on its root, so a name pressed anywhere in the home base opens there;
  - home-board (a5548): an opened card says 'Open' (view it) where it said '<id> · read <id> on the desk ...';
  - waiting-on-me (a5439): the bare '$item' at the foot of an opened item goes (its title is the name, Open here opens);
  - home-viewer (a5486): the open thing's head says its kind, not '<kind> · <id>' (the id is on hover, in Properties);
  - doc-page (a6079) no longer says where its links go; writing (a5911) says it, for the documents it holds (they open
    in Writing, as before), so a document opened in the viewer opens its links in the viewer. (writing/*.lens agree.)
At work, the chat headers ('in a5949'), notices and every other line that prints an id need no line here: the painter
names them, and the root's `on link` opens them.
Every line that changes a lens says the words it replaces (do replace), so it is refused where someone changed them."""
import json
import pathlib
import re
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOM = "f5204"


def q(s):
    """A value as the desk reads it: in double quotes, with backslash, quote and dollar escaped and newlines as \\n."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def text(name):
    return (HERE / name).read_text(encoding="utf-8").rstrip("\n")


# (note, old, new): each old passage must stand in the note exactly once
REPLACES = [
    ("a5208", "  role home\n  tiles : column\n",
              "  role home\n  on link do view $value\n  tiles : column\n"),
    ("a5548", '    where : text "$c.item · read $c.item on the desk to open it fully"\n      role hint\n',
              '    open : text "Open"\n      role chip\n      on click do view $c.item\n'),
    ("a5439", '      where : text "$item"\n        role hint\n', ""),
    ("a5486", '    kind : text "$kind · $item"\n', '    kind : text "$kind"\n'),
    # a link in a document is the lens around it to place: Writing opens it in Writing, the viewer in the viewer
    ("a6079", '              on link do read $w; do prop $w open=$value back="$w.open"\n', ""),
    ("a5911", "app : column\n  share 1\n  global : row\n",
              'app : column\n  share 1\n  on link do read $w; do prop $w open=$value back="$w.open"\n  global : row\n'),
]


def lines():
    out = [f"look {ROOM}", f"do create {ROOM} kind=note title=view tags=verb text={q(text('view.verb'))}", "do prop $new on=house"]
    for note, old, new in REPLACES:
        out += [f"read {note}", f"do replace {note} old={q(old)} new={q(new)}"]
    return out


def door(line, who, port, world):
    body = json.dumps({"session": world, "as": who, "line": line, "whole": True}).encode()
    r = urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/api/do", data=body, method="POST"), timeout=60)
    return json.loads(r.read()).get("text", "")


def body(said):
    ls = said.splitlines()
    i = ls.index("---")
    return "\n".join(ls[i + 1:ls.index("---", i + 1)])


BEFORE = HERE / "before-a6109"


def check(who, port, world, keep=False):
    """Every old= passage against the world's text now; each must stand once. keep: save each note's text first."""
    bad = 0
    for note, old, _ in REPLACES:
        said = door(f"read {note} :3", who, port, world)
        now = body(said)
        if keep:
            BEFORE.mkdir(exist_ok=True)
            (BEFORE / f"{note}.txt").write_text(now + "\n", encoding="utf-8")
        n = now.count(old)
        print(f"{note}: old= stands {n} time(s): {old[:70]!r}" + (f"  (kept in before-a6109/{note}.txt)" if keep else ""))
        bad += n != 1
    return bad


def main(argv):
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d       # noqa: E731
    if not argv or argv[0] not in ("lines", "door", "check"):
        print(__doc__)
        return 0
    if argv[0] == "lines":
        out = lines()
        pathlib.Path(argv[1]).write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"wrote {len(out)} lines to {argv[1]}")
        return 0
    who, port, world = opt("--as", "worker-a6109"), opt("--port", "8794"), opt("--world", "frontier")
    if argv[0] == "check":
        return 1 if check(who, port, world) else 0
    # door: first every passage, the live text of each note kept beside this file; nothing is sent unless all stand
    if check(who, port, world, keep=True):
        print("stopped before sending anything: a passage above no longer stands once")
        return 1
    new = None
    for line in lines():
        if "$new" in line and new:             # the door does not carry $new between requests (builders' notebook)
            line = line.replace("$new", new)
        said = door(line, who, port, world)
        print(said[:300])
        if "(\u0024new = " in said or "($new = " in said:
            new = said.split("($new = ", 1)[1].split(")", 1)[0]
        made = re.search(r"→ created (a\d+)", said)       # a create's own receipt names what it made
        if made:
            new = made.group(1)
        if [x for x in said.splitlines() if x.startswith(("ERR", "MISS")) or x.startswith("~ ! lens")]:
            print("stopped: the line above was refused or left a lens not compiling")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
