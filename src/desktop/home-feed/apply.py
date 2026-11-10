"""At work -> an agent's live feed (a5988), the world half: kept here as files, so it can be tried on a copy and applied
live after feeds.py (the house's writer of witnessed:feed-<name>) has landed.

    python src/desktop/home-feed/apply.py lines <out.desk>     the lines (explore.py <world> --as <who> < out.desk)
    python src/desktop/home-feed/apply.py update <out.desk>    lines that rewrite home-feed and home-work only
    python src/desktop/home-feed/apply.py door [--as <name>]   all of it to the live door, line by line, stopping
                                                                       at a refusal

What the lines make or change, all in the Home base room (f5204):
  - home-style gains the roles of the feed (feed.style);
  - a new lens, home-feed, an agent's feed stood on its card or corner (home-feed.lens);
  - home-work (At work) is rewritten: residents at work and the workers of cards at work; pressing one opens its card
    or corner in the viewer with home-feed (viewing=<id> with=home-feed) (home-work.lens); home-work-small counts both.
home-viewer is not touched: it needs a5949's viewer (with=<lens> stands any lens on the thing open), so run
src/desktop/writing/apply.py first. Applying twice appends the roles twice and makes a second home-feed: it is
for a world that has none of it yet."""
import json
import pathlib
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOM = "f5204"
SMALL_OLD = 'n : text "$(count(house doing=working)) at work"'
SMALL_NEW = 'n : text "$(count(house doing=working) + count(prop:commission=working)) at work"'


def q(s):
    """A value as the desk reads it: in double quotes, with backslash, quote and dollar escaped and newlines as \\n."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def text(name):
    return (HERE / name).read_text(encoding="utf-8").rstrip("\n")


def lines():
    # one command a line: the door reads each request whole (a5659, 15 Oct)
    return ['read "home-style"', f'do append "home-style" line={q(text("feed.style"))}',
            f"look {ROOM}",
            f"do create {ROOM} kind=note title=home-feed tags=lens style=home-style text={q(text('home-feed.lens'))}",
            'read "home-work"', f'do rewrite "home-work" text={q(text("home-work.lens"))}',
            'read "home-work-small"', f'do replace "home-work-small" old={q(SMALL_OLD)} new={q(SMALL_NEW)}']


def update():
    """Lines that rewrite the two lenses only, for a world that already has all of it."""
    return ['read "home-feed"', f'do rewrite "home-feed" text={q(text("home-feed.lens"))}',
            'read "home-work"', f'do rewrite "home-work" text={q(text("home-work.lens"))}']


def door(line, who):
    body = json.dumps({"session": "frontier", "as": who, "line": line, "whole": True}).encode()
    r = urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8794/api/do", data=body, method="POST"), timeout=60)
    return json.loads(r.read()).get("text", "")


def main(argv):
    who = argv[argv.index("--as") + 1] if "--as" in argv else "worker-a5988"
    if argv[:1] in (["lines"], ["update"]) and len(argv) > 1:
        out = lines() if argv[0] == "lines" else update()
        pathlib.Path(argv[1]).write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"wrote {len(out)} lines to {argv[1]}")
        return 0
    if argv[:1] == ["door"]:
        for line in lines():
            said = door(line, who)
            print(said[:400])
            if said.startswith("ERR") or "refused" in said[:200] or "MISS" in said[:200]:
                print("stopped: the line above was refused")
                return 1
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
