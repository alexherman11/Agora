"""The reader (a6460): the world half. The painter half (quiet names, the read-only document's spacing, the words
for-alex(), lead(), gist(), read-minutes()) must have LANDED first: the lens uses those words and does not compile
without them. Kept as files so they can be read, tried on a copy, and applied live after the landing.

    python research/window-lab/reader/apply.py lines <out.desk>     the lines (explore.py <world> --as <you> < out.desk)
    python research/window-lab/reader/apply.py check [--as <name>] [--port 8794] [--world frontier]
                                         every old= passage against the world's text now (each must stand once)
    python research/window-lab/reader/apply.py door [--as <name>] [--port 8794] [--world frontier]
                                         all of it through a door, line by line, stopping at the first refusal;
                                         it checks every passage first and keeps each note's live text in before/

What the lines do, all world data anyone may change afterwards:
  - home-style (a5206) and review (a4200) gain the rd* roles (home-style.roles, review.roles), before the lens;
  - lens `reader` (reader.lens), a note in the Home base room, and Alex's reader note (role=reader actor=alex);
  - home-viewer (a5486): a thing waiting on Alex (tagged ready-for-review, or design=waiting) opens in the reader
    unless Open with says otherwise; Open with offers `reader` for anything;
  - writing (a5911): Read / Write over the open document; a waiting one opens to Read;
  - home-board (a5548): a press on a needs-you line's words opens it in the reader (one press), and every Open there
    clears the viewer's Open with, so the reader is what opens;
  - waiting-on-me (a5439): Open here clears Open with too.
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


VIEWER_HEAD_OLD = '''  let using = ($v.with or "")
  head : row
    role viewhead
    title : text "$title"
      role heading
      clamp 2
      share 1
'''
VIEWER_HEAD_NEW = '''  let using = ($v.with or "")
  let waits = "yes" when ($tags or "") has "ready-for-review" or ($design or "") = "waiting"
  let waits = "no" otherwise
  let answered = "yes" when count(prop:role=reader,prop:actor=$me,prop:last=$item) > 0
  let answered = "no" otherwise
  let reading = "yes" when using = "" and islens = "no" and (waits = "yes" or answered = "yes")
  let reading = "no" otherwise
  head : row
    role viewhead
    title : text "$title"
      role heading
      clamp 2
      share 1
      only when reading = "no"
    reads : text "Waiting on you"
      role meta
      share 1
      only when reading = "yes"
'''
VIEWER_PAGE_OLD = '''    page : text "page"
      role chip
      role chip.on when using = "doc-page" or (using = "" and isdoc = "yes")
'''
VIEWER_PAGE_NEW = '''    reader : text "reader"
      role chip
      role chip.on when using = "reader" or reading = "yes"
      on click when using != "reader" and reading = "no" do prop $v with=reader
    page : text "page"
      role chip
      role chip.on when using = "doc-page" or (using = "" and isdoc = "yes" and reading = "no")
'''
VIEWER_OWN_OLD = '''      role chip.on when using = "" and isdoc = "no"
      only when using != "" or isdoc = "yes"
'''
VIEWER_OWN_NEW = '''      role chip.on when using = "" and isdoc = "no" and reading = "no"
      only when (using != "" or isdoc = "yes") and reading = "no"
'''
VIEWER_BRANCH_OLD = '''  doc : column
    share 1
    only when using = "" and islens = "no" and isdoc = "yes"
    lens doc-page
  known : column
    share 1
    only when using = "" and islens = "no" and isdoc = "no" and ($kind = "note" or $kind = "chat" or $kind = "surface")
    lens home-$kind
  plain : column
    share 1
    scroll scroll
    only when using = "" and islens = "no" and isdoc = "no" and $kind != "note" and $kind != "chat" and $kind != "surface"
'''
VIEWER_BRANCH_NEW = '''  read : column
    share 1
    only when reading = "yes"
    lens reader
  doc : column
    share 1
    only when using = "" and islens = "no" and isdoc = "yes" and reading = "no"
    lens doc-page
  known : column
    share 1
    only when using = "" and islens = "no" and isdoc = "no" and reading = "no" and ($kind = "note" or $kind = "chat" or $kind = "surface")
    lens home-$kind
  plain : column
    share 1
    scroll scroll
    only when using = "" and islens = "no" and isdoc = "no" and reading = "no" and $kind != "note" and $kind != "chat" and $kind != "surface"
'''
WRITING_OLD = '''shown : column
  share 1
  lens doc-page
'''
WRITING_NEW = '''# a6460: Read sets the open document as an article (lens reader: a summary on top, answers at the foot); Write is the
# page to write and comment in. A document waiting on Alex opens to Read; the choice is kept on the writer note (mode=)
shown : column
  share 1
  let waits = "yes" when ($tags or "") has "ready-for-review" or ($design or "") = "waiting"
  let waits = "yes" when count(prop:role=reader,prop:actor=$me,prop:last=$item) > 0
  let waits = "no" otherwise
  let reading = "yes" when ($w.mode or "") = "read" or (($w.mode or "") = "" and waits = "yes")
  let reading = "no" otherwise
  modes : row
    gap
    r : text "Read"
      role viewtab
      role viewtab.on when reading = "yes"
      on click when reading = "no" do read $w; do prop $w mode=read
    wr : text "Write"
      role viewtab
      role viewtab.on when reading = "no"
      on click when reading = "yes" do read $w; do prop $w mode=write
  reads : column
    share 1
    only when reading = "yes"
    lens reader
  writes : column
    share 1
    only when reading = "no"
    lens doc-page
'''
BOARD_REVIEW_OLD = '''    what : text "$(($c.brief or $c.title))"
      role nbtitle
      clamp 1
      share 1
    ok : text "Looks good"
'''
BOARD_REVIEW_NEW = '''    what : text "$(($c.brief or $c.title))"
      role nbtitle
      clamp 1
      share 1
      on click do read $hv; do prop $hv viewing=$c back="$hv.viewing" find="" with=""
    ok : text "Looks good"
'''
BOARD_DESIGN_OLD = '''    what : text "$(($c.brief or $c.title))"
      role nbtitle
      clamp 1
      share 1
    build : text "Build it"
'''
BOARD_DESIGN_NEW = '''    what : text "$(($c.brief or $c.title))"
      role nbtitle
      clamp 1
      share 1
      on click do read $hv; do prop $hv viewing=$c back="$hv.viewing" find="" with=""
    build : text "Build it"
'''
BOARD_READ_OLD = '''      read : text "Read it in the middle"
        role nbbtn
        on click do read $hv; do prop $hv viewing=$c back="$hv.viewing" find=""
'''
BOARD_READ_NEW = '''      read : text "Read it in the middle"
        role nbbtn
        on click do read $hv; do prop $hv viewing=$c back="$hv.viewing" find="" with=""
'''
WAITING_OLD = '''  let was = $hv.back
  on click when ($hv.find or "") != "" do prop $hv viewing=$w back="$hv.viewing" find=""
  on click when ($hv.find or "") = "" do prop $hv viewing=$w back="$hv.viewing"'''
WAITING_NEW = '''  let was = $hv.back
  let using = ($hv.with or "")
  on click when ($hv.find or "") != "" do prop $hv viewing=$w back="$hv.viewing" find="" with=""
  on click when ($hv.find or "") = "" do prop $hv viewing=$w back="$hv.viewing" with=""'''
WAITING_HEAD_OLD = '''    on click when $item != ($rd.reviewing or "") and $rd.full = "yes" do prop $rd reviewing=$w full=no
    on click when $item != ($rd.reviewing or "") and ($rd.full or "") != "yes" do prop $rd reviewing=$w
    on click when $item = $rd.reviewing and $rd.full = "yes" do prop $rd reviewing="" full=no
    on click when $item = $rd.reviewing and ($rd.full or "") != "yes" do prop $rd reviewing=""
'''
WAITING_HEAD_NEW = '''    # a6460: one press reads the item in the middle, through the same house verb as a named reference.
    on click do view $w
'''

# (note, old, new): each old passage must stand in the note exactly once
REPLACES = [
    ("a5486", VIEWER_HEAD_OLD, VIEWER_HEAD_NEW),
    ("a5486", VIEWER_PAGE_OLD, VIEWER_PAGE_NEW),
    ("a5486", VIEWER_OWN_OLD, VIEWER_OWN_NEW),
    ("a5486", VIEWER_BRANCH_OLD, VIEWER_BRANCH_NEW),
    ("a5911", WRITING_OLD, WRITING_NEW),
    ("a5548", BOARD_REVIEW_OLD, BOARD_REVIEW_NEW),
    ("a5548", BOARD_DESIGN_OLD, BOARD_DESIGN_NEW),
    ("a5548", BOARD_READ_OLD, BOARD_READ_NEW),
    ("a5439", WAITING_OLD, WAITING_NEW),
    ("a5439", WAITING_HEAD_OLD, WAITING_HEAD_NEW),
]
# a copy where an earlier round of these lines ran (20 Oct, before an answered thing stayed in the reader): its lines
# brought up to today's. relens and test_reader.py use them; the live world never had the earlier round
UPGRADES = [
    ("a5439", WAITING_HEAD_OLD, WAITING_HEAD_NEW),
    ("a5486", '  let reading = "yes" when using = "" and islens = "no" and waits = "yes"\n',
     '  let answered = "yes" when count(prop:role=reader,prop:actor=$me,prop:last=$item) > 0\n  let answered = "no" otherwise\n'
     '  let reading = "yes" when using = "" and islens = "no" and (waits = "yes" or answered = "yes")\n'),
    ("a5911", '  let waits = "no" otherwise\n  let reading = "yes" when ($w.mode',
     '  let waits = "yes" when count(prop:role=reader,prop:actor=$me,prop:last=$item) > 0\n  let waits = "no" otherwise\n  let reading = "yes" when ($w.mode'),
]
STYLES = [("a5206", "home-style.roles"), ("a4200", "review.roles")]


def lines():
    out = []
    for note, f in STYLES:
        out += [f"read {note} :3", f"do append {note} line={q(text(f))}"]
    out += [f"look {ROOM}",
            f"do create {ROOM} kind=note title=reader tags=lens style=home-style text={q(text('reader.lens'))}",
            f"do create {ROOM} kind=note title={q('Alex' + chr(39) + 's reader (what the reader keeps for him: Skim, an answer being written)')} role=reader actor=alex"]
    for note, old, new in REPLACES:
        out += [f"read {note} :3", f"do replace {note} old={q(old)} new={q(new)}"]
    return out


def door(line, who, port, world):
    body = json.dumps({"session": world, "as": who, "line": line, "whole": True}).encode()
    r = urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/api/do", data=body, method="POST"), timeout=60)
    return json.loads(r.read()).get("text", "")


def body(said):
    ls = said.splitlines()
    i = ls.index("---")
    return "\n".join(ls[i + 1:ls.index("---", i + 1)])


BEFORE = HERE / "before"


def check(who, port, world, keep=False):
    """Every old= passage against the world's text now; each must stand once. keep: save each note's text first."""
    bad = 0
    for note in sorted({n for n, _, _ in REPLACES} | {n for n, _ in STYLES}):
        now = body(door(f"read {note} :3", who, port, world))
        if keep:
            BEFORE.mkdir(exist_ok=True)
            (BEFORE / f"{note}.txt").write_text(now + "\n", encoding="utf-8")
        for n, old, _ in REPLACES:
            if n == note:
                k = now.count(old)
                print(f"{note}: old= stands {k} time(s): {old.strip().splitlines()[0][:70]!r}")
                bad += k != 1
        if note in {n for n, _ in STYLES} and "role rdpage" in now:
            print(f"{note}: already holds the reader's roles")
            bad += 1
    if "reader" in [t for t in re.findall(r'note "([^"]+)" · [^\n]*tags lens', door("find reader", who, port, world))]:
        print("a lens called reader already stands")
        bad += 1
    return bad


def main(argv):
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d       # noqa: E731
    if not argv or argv[0] not in ("lines", "relens", "door", "check"):
        print(__doc__)
        return 0
    if argv[0] == "relens":          # a copy where the lines already ran: the lens again, from reader.lens
        out = [f"look {ROOM}", "read reader :3", f"do rewrite reader text={q(text('reader.lens'))}"]
        for note, old, new in (UPGRADES if "upgrade" in argv[2:] else REPLACES):   # and any notes named after the file
            if note in argv[2:]:
                out += [f"read {note} :3", f"do replace {note} old={q(old)} new={q(new)}"]
        pathlib.Path(argv[1]).write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"wrote {len(out)} lines to {argv[1]}")
        return 0
    if argv[0] == "lines":
        out = lines()
        pathlib.Path(argv[1]).write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"wrote {len(out)} lines to {argv[1]}")
        return 0
    who, port, world = opt("--as", "jeff"), opt("--port", "8794"), opt("--world", "frontier")
    if argv[0] == "check":
        return 1 if check(who, port, world) else 0
    # door: first every passage, the live text of each note kept beside this file; nothing is sent unless all stand
    if check(who, port, world, keep=True):
        print("stopped before sending anything: a passage above no longer stands once")
        return 1
    for line in lines():
        said = door(line, who, port, world)
        print(said[:300])
        if [x for x in said.splitlines() if x.startswith(("ERR", "MISS")) or x.startswith("~ ! lens")]:
            print("stopped: the line above was refused or left a lens not compiling")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
