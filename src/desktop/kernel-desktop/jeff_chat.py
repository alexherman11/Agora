"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

jeff_chat: put JEFF's chat in the world: the old desk's jeff-chat lens (frontier a5210) and its home-style (s5205),
ported to the kernel's things (said lines in the Conversation chat, the house-agent's live `doing`), Alex's
conversation-draft (what his next line answers), and the JEFF button's line (Shell settings jeff_open). Through the
ordinary door, undoably; the world's copies are authoritative afterwards (run again to replace them).

    python jeff_chat.py [--world <dir>] [--port 8810]

Ported unchanged: the layout, names, roles and style; the run of lines by one writer under one name; Alex's lines at the
right; Answer. Left behind (the kernel has no source for them yet): the Everything feed (every line to or by Alex,
anywhere), the To chips, attaching what is open, captures, voice, usage, and commenting on a document's words.
"""
import argparse
import json
from pathlib import Path
from kd_say import say

HERE = Path(__file__).resolve().parent


def install(token, port=8810):
    out = []

    def line(text):
        r = say(text, token, port)
        if not r.get("ok"):
            raise RuntimeError(f"{text[:80]}: {r.get('text')}")
        out.append(r["text"].splitlines()[0])
        return r

    def q(text):
        return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
    chats = line("rows chat name=Conversation")["rows"]
    if not chats:
        raise RuntimeError("no Conversation chat yet: kdesk makes it when it starts (moving_in)")
    convo = chats[0]["id"]
    desk_id = "s" + "".join(c for c in convo if c.isdigit())          # the painter's id for it (painter.Facade.num)
    for kind, name, filename, extra in (("style", "home-style", "home-style.style", ""),
                                        ("lens", "jeff-chat", "jeff-chat.lens", " style=home-style")):
        text = (HERE / "lenses" / filename).read_text(encoding="utf-8").replace("$CONVO", desk_id)
        rows = line(f"rows {kind} name={name}")["rows"]
        if rows:
            line(f"look {rows[0]['id']}")
            line(f"set {rows[0]['id']} text={q(text)}{extra}")
        else:
            line(f"make kind={kind} name={name} text={q(text)}{extra}")
    if not line("rows conversation-draft")["rows"]:
        line(f"make kind=conversation-draft name=\"Alex's next line\" chat={convo} sees=me")
    shell = line("rows shell-settings")["rows"]
    if shell:
        line(f"look {shell[0]['id']}")
        line(f'set {shell[0]["id"]} jeff_open="window.open jeff-chat"')
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", type=Path, default=HERE / "state" / "world")
    ap.add_argument("--port", type=int, default=8810)
    a = ap.parse_args()
    sessions = json.loads((a.world / "keep" / "sessions.json").read_text(encoding="utf-8"))
    token = next(t for t, v in sessions.items() if v.get("signer") == "claude")
    for r in install(token, a.port):
        print(r)
