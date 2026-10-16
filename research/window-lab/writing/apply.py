"""The Writing app (a5820) as desk lines: the world half of the commission, kept here as files so it can be read, tried
on a copy and applied to the live world after the code it needs (the `markdown` word, `on link`) has landed.

    python research/window-lab/writing/apply.py lines <out.desk>     the lines (explore.py <world> --as <you> < out.desk)
    python research/window-lab/writing/apply.py update <out.desk>    lines that rewrite the style and lens where they are
    python research/window-lab/writing/apply.py door [--as <name>]   all of it, to the live door, line by line, stopping at a refusal

What the lines make, in the Writing room (f3402), all world data anyone may change afterwards:
  - the style `writing` and the lens `writing` (style=writing);
  - a surface "Notes (Writing)" where + New puts a new one-text document (a note, role=doc: a4865);
  - a writer's note for alex (role=writer actor=alex), what his Writing window has open;
  - the dock's Writing room icon (a5573) opens the Writing app as its own window: opens= becomes window=writing.
Applying twice makes everything twice: it is for a world that has none of it yet."""
import json
import pathlib
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOM = "f3402"


def q(s):
    """A value as the desk reads it: in double quotes, with backslash, quote and dollar escaped and newlines as \\n."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def text(name):
    return (HERE / name).read_text(encoding="utf-8").rstrip("\n")


def lines(who="alex"):
    # one command a line: the door reads each request whole (a5659, 15 Oct)
    return [f"look {ROOM}",
            f"do create {ROOM} kind=note title=writing-style tags=style text={q(text('writing.style'))}",
            f"do create {ROOM} kind=note title=writing tags=lens style=writing-style text={q(text('writing.lens'))}",
            f'do create {ROOM} kind=surface title="Notes (Writing)" layout=column',
            'do prop "Notes (Writing)" role=notes',
            f"do create {ROOM} kind=note title=\"{who.capitalize()}'s writing (what the Writing app has open)\" role=writer actor={who}",
            "look a5573",
            "do prop a5573 window=writing remove=opens"]


def update():
    """Lines that rewrite the style and the lens (by their titles) in a world that has them."""
    return ['read "writing-style"', f'do rewrite "writing-style" text={q(text("writing.style"))}',
            'read "writing"', f'do rewrite "writing" text={q(text("writing.lens"))}']


def door(line, who):
    body = json.dumps({"session": "frontier", "as": who, "line": line, "whole": True}).encode()
    r = urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8794/api/do", data=body, method="POST"), timeout=60)
    return json.loads(r.read()).get("text", "")


def main(argv):
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d       # noqa: E731
    who = opt("--as", "worker-a5820")
    if not argv or argv[0] not in ("lines", "update", "door"):
        print(__doc__)
        return 0
    out = update() if argv[0] == "update" else lines()
    if argv[0] in ("lines", "update"):
        pathlib.Path(argv[1]).write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"wrote {len(out)} lines to {argv[1]}")
        return 0
    for line in out:
        said = door(line, who)
        print(said[:400])
        if said.startswith("ERR") or "refused" in said[:200]:
            print("stopped: the line above was refused")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
