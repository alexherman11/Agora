"""Films and pictures in chat (a5941) as desk lines: the world half of the commission, kept as files so it can be read,
tried on a copy and applied to the live world after the code it needs (the `media` word, `on pop`) has landed.

    python src/desktop/media-chat/apply.py lines <out.desk>    every line, for a copy (explore.py <world> --as <you> < out.desk)
    python src/desktop/media-chat/apply.py stage [--as <name>] live, BEFORE the landing: the style, the lens
                       untagged (not compiled) and alex's player note; the chats are not touched
    python src/desktop/media-chat/apply.py finish [--as <name>] live, AFTER the landing: the lens tagged, and the
                       two chat lenses' message words given `media` and Pop out (four lines each, nothing else moves)
    python src/desktop/media-chat/apply.py note [--as <name>]  live: the finish lines as a note in the Home base
                       room, so someone with only the desk can run them

What the lines make, in the Home base room (f5204), all world data anyone may change afterwards:
  - the style `media-player-style` and the lens `media-player` (style=media-player-style): one film, filling a window;
  - alex's player note (role=media-player actor=alex): src= what his player window shows, set by Pop out;
  - in jeff-chat (a5210, the home base chat) and conversation (a5086), the words of each message say `media`, and
    `on pop` sets src= on the reader's own player note, then asks the host for `window media-player`.
Applying stage twice makes everything twice: it is for a world that has none of it yet."""
import json
import pathlib
import re
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOM = "f5204"
PLAYER = "Alex's player (what a popped-out film shows)"
POP = ['on pop do prop prop:role=media-player,prop:actor=$me src="$value" opened=$now', "on pop host window media-player"]

# the message words of each chat lens, exactly as they stand, and what they become: the same lines, then media and Pop out
CHATS = {
    "a5210": ('    body : text "$s.said"\n      marks\n      role words', "      "),
    "a5086": ('  body : text "$said"\n    marks\n    role body', "    "),
}


def q(s):
    """A value as the desk reads it: in double quotes, with backslash, quote and dollar escaped and newlines as \\n."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def text(name):
    return (HERE / name).read_text(encoding="utf-8").rstrip("\n")


def stage(tagged=False):
    tags = "tags=lens " if tagged else ""
    return [f"look {ROOM}",
            f"do create {ROOM} kind=note title=media-player-style tags=style text={q(text('media-player.style'))}",
            f"do create {ROOM} kind=note title=media-player {tags}style=media-player-style text={q(text('media-player.lens'))}",
            f'do create {ROOM} kind=note title="{PLAYER}" role=media-player actor=alex']


def chats():
    out = []
    for lens, (old, ind) in CHATS.items():
        new = old + "".join("\n" + ind + w for w in ["media"] + POP)
        out += [f"read {lens}", f"do replace {lens} old={q(old)} new={q(new)}"]
    return out


FINISH = ['read "media-player"', 'do tag "media-player" add=lens']


def door(line, who):
    body = json.dumps({"session": "frontier", "as": who, "line": line, "whole": True}).encode()
    r = urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8794/api/do", data=body, method="POST"), timeout=60)
    return json.loads(r.read()).get("text", "")


def main(argv):
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d       # noqa: E731
    who = opt("--as", "worker-a5941")
    if not argv or argv[0] not in ("lines", "stage", "finish", "note"):
        print(__doc__)
        return 0
    if argv[0] == "note":
        # the finishing lines as a note in the Home base room, for whoever finishes it from the desk alone (JEFF)
        # a line's \n must stay two characters in the note, so each line is one command when copied: a stored text
        # turns \n into a line break, and \\n into \n (ran on a copy, 16 Oct)
        body = ("Run these desk lines, one call each, AFTER commission a5941 has landed (before, the chats would stop "
                "compiling: the running code would not know the word media). Each replace names the exact words it "
                "changes; if one is refused, read the lens again: someone changed those lines.\n\n"
                + "\n".join(x.replace("\\n", "\\\\n") for x in FINISH + chats()))
        title = "Media in chat: the lines to finish a5941 after it lands"
        print(door(f'look {ROOM}', who)[:80])
        if not door(f'read "{title}"', who).startswith(("ERR", "MISS")):
            print(door(f'do rewrite "{title}" text={q(body)}', who)[:400])
        else:
            print(door(f'do create {ROOM} kind=note title="{title}" text={q(body)}', who)[:400])
        return 0
    if argv[0] == "lines":
        out = stage(tagged=True) + chats()
        pathlib.Path(argv[1]).write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"wrote {len(out)} lines to {argv[1]}")
        return 0
    for line in (stage() if argv[0] == "stage" else FINISH + chats()):
        said = door(line, who)
        print(said[:400])
        if said.startswith("ERR") or re.search(r"\bERR\b|refused", said[:300]):
            print("stopped: the line above was refused")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
