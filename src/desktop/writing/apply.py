"""The Writing room back in Agora's own look, with its comments and Talk, and in the home base on the left of JEFF's chat
(a5949). The world half of the commission, kept as files so it can be read, tried on a copy, and applied to the live
world AFTER the code it needs has landed (a lens stood on a thing; section-of, words-before, words-after; `light` and
`on select` in a Markdown text).

    python src/desktop/writing/apply.py lines <out.desk>     the lines (explore.py <world> --as <you> < out.desk)
    python src/desktop/writing/apply.py update <out.desk>    lines that rewrite this commission's lenses in place
    python src/desktop/writing/apply.py backup [--as <name>]   first: each note it changes, as it stands, into before-a5949/
    python src/desktop/writing/apply.py check     every old= passage against those texts (each must stand once)
    python src/desktop/writing/apply.py door [--as <name>] [--port 8794] [--world frontier]
                                         all of it through a door, line by line, stopping at the first refusal

What the lines do, all world data anyone may change afterwards:
  - home-style (a5206) and review (a4200) gain the roles the Writing page paints with (roles-home.style, roles-review.style);
  - a new lens doc-page (doc-page.lens) in the Writing room (f3402): one document's page, stood on it;
  - writing (a5911) becomes design-review's page around doc-page (writing.lens), in the review style;
  - design-review (a4039) is doc-page when stood on a document, else writing (design-review.lens);
  - home-viewer (a5486): what is open stands on the left of JEFF's chat; with= stands any lens on it (home-viewer.lens);
  - home-tiling (a5692): the viewer takes more of the width while something is open in it;
  - home-dock (a5564): an icon with opens= and window= opens in the viewer and has a small pop out;
  - the dock's Writing room icon (a5573) opens= the writing lens again (window=writing stays, as its pop out).
Every line that changes a text says the words it replaces (do replace), or reads the note first and rewrites it whole
(the lenses this commission owns the shape of): run it on a world whose lenses are as they were on 16 Oct."""
import json
import pathlib
import re
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOM = "f3402"


def q(s):
    """A value as the desk reads it: in double quotes, with backslash, quote and dollar escaped and newlines as \\n."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def text(name):
    return (HERE / name).read_text(encoding="utf-8").rstrip("\n")


HOME_ANCHOR = "role nx : text down, soft, pad left gap /2, pad right gap /2"
REVIEW_ANCHOR = "role light     : on mark at 16%"
TILING_OLD = "    pinned : column\n      share 7\n"
TILING_NEW = ("    pinned : column\n"
              "      let wide = 32 when count(prop:role=home-view,prop:actor=$me,prop:viewing,-prop:viewing=a5080) + count(prop:role=home-view,prop:actor=$me,prop:find) > 0\n"
              "      let wide = 7 otherwise\n"
              "      share $wide\n")
DOCK = [("  view : column\n    only when ($d.opens or \"\") != \"\" and $d.opens != \"chat\"\n    role appicon\n    role appicon.on when $d.opens = $v.viewing\n    on click do prop $v viewing=$d.opens back=\"$v.viewing\" find=\"\"\n",
         "  view : column\n    only when ($d.opens or \"\") != \"\" and $d.opens != \"chat\"\n    role appicon\n    role appicon.on when $d.opens = $v.viewing\n    on click do prop $v viewing=$d.opens back=\"$v.viewing\" find=\"\" with=\"\"\n"),
        ("  window : column\n    only when ($d.window or \"\") != \"\"\n",
         "  pop : text \"pop out\"\n    role applabel\n    only when ($d.window or \"\") != \"\" and ($d.opens or \"\") != \"\"\n    on click host window $d.window\n"
         "  window : column\n    only when ($d.window or \"\") != \"\" and ($d.opens or \"\") = \"\"\n")]


def lines():
    out = ["read a5206", f"do replace a5206 old={q(HOME_ANCHOR)} new={q(HOME_ANCHOR + chr(10) + text('roles-home.style'))}",
           "read a4200", f"do replace a4200 old={q(REVIEW_ANCHOR)} new={q(REVIEW_ANCHOR + chr(10) + text('roles-review.style'))}",
           f"look {ROOM}", f"do create {ROOM} kind=note title=doc-page tags=lens style=review text={q(text('doc-page.lens'))}",
           "read a5911", f"do rewrite a5911 text={q(text('writing.lens'))}", "do prop a5911 style=review",
           "read a4039", f"do rewrite a4039 text={q(text('design-review.lens'))}",
           "read a5486", f"do rewrite a5486 text={q(text('home-viewer.lens'))}",
           "read a5692", f"do replace a5692 old={q(TILING_OLD)} new={q(TILING_NEW)}",
           "read a5564"]
    out += [f"do replace a5564 old={q(o)} new={q(n)}" for o, n in DOCK]
    out += ["look a5573", "do prop a5573 opens=a5911"]
    return out


def update():
    """Lines that rewrite this commission's own lenses where they already stand (a copy being tried again)."""
    return ['read "doc-page"', f'do rewrite "doc-page" text={q(text("doc-page.lens"))}',
            "read a5911", f"do rewrite a5911 text={q(text('writing.lens'))}",
            "read a4039", f"do rewrite a4039 text={q(text('design-review.lens'))}",
            "read a5486", f"do rewrite a5486 text={q(text('home-viewer.lens'))}"]


def door(line, who, port, world):
    body = json.dumps({"session": world, "as": who, "line": line, "whole": True}).encode()
    r = urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/api/do", data=body, method="POST"), timeout=60)
    return json.loads(r.read()).get("text", "")


TOUCHED = ("a5206", "a4200", "a5911", "a4039", "a5486", "a5692", "a5564", "a5573")
BEFORE = HERE / "before-a5949"


def body(said):
    """The text of a note from `read <id> :3` as the door prints it: between the first --- line and the next."""
    ls = said.splitlines()
    i = ls.index("---")
    j = ls.index("---", i + 1)
    return "\n".join(ls[i + 1:j]), [x for x in ls[:i] if "appears at" in x]


def backup(who, port, world):
    """Each note this changes, as it stands now, kept beside this file so it can be put back by hand."""
    BEFORE.mkdir(exist_ok=True)
    for i in TOUCHED:
        text, head = body(door(f"read {i} :3", who, port, world))
        (BEFORE / f"{i}.txt").write_text(text + "\n", encoding="utf-8")
        (BEFORE / f"{i}.head.txt").write_text("\n".join(head) + "\n", encoding="utf-8")
        print(f"kept {i}: {len(text)} characters · {head[0][:140] if head else ''}")


def check():
    """Every old= passage of a replace, against the texts backup kept: each must stand there exactly once."""
    bad = 0
    for line in lines():
        if not line.startswith("do replace "):
            continue
        i = line.split()[2]
        old = line.split(" old=", 1)[1].split(" new=", 1)[0]
        old = json.loads(old.replace("\\$", "$")) if old.startswith('"') else old
        n = (BEFORE / f"{i}.txt").read_text(encoding="utf-8").count(old)
        print(f"{i}: old= stands {n} time(s): {old[:70]!r}")
        bad += n != 1
    return bad


def main(argv):
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d       # noqa: E731
    if not argv or argv[0] not in ("lines", "update", "door", "backup", "check"):
        print(__doc__)
        return 0
    out = update() if argv[0] == "update" else lines()
    if argv[0] in ("lines", "update"):
        pathlib.Path(argv[1]).write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"wrote {len(out)} lines to {argv[1]}")
        return 0
    who, port, world = opt("--as", "worker-a5949"), opt("--port", "8794"), opt("--world", "frontier")
    if argv[0] == "backup":
        backup(who, port, world)
        return 0
    if argv[0] == "check":
        return 1 if check() else 0
    for line in out:
        said = door(line, who, port, world)
        print(said[:300])
        bad = [x for x in said.splitlines() if x.startswith(("ERR", "MISS")) or x.startswith("~ ! lens")]
        if bad and not (line.startswith("do rewrite a5911") and all("writing does not compile" in x for x in bad)):
            print("stopped: the line above was refused or left a lens not compiling:", bad[:2])
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
