"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

Install Twitch chat, its adapter, view and dock pin once through ordinary world lines.

Called at desktop startup. Whatever is already in the world stays as authored: nothing here overwrites it.
No window opens here. The reader is stopped with `off twitch`.

Twitch is an adapter (agora/modules/adapters): the module named twitch runs the one adapter source, and the
adapter thing named twitch holds what it does (its text, seeded from twitch.adapter) and its settings, which it reads
again every few seconds. Which channel is a setting, never code: `set <the twitch adapter> channel=<name>`. A world
that had the 3 Nov chat keeps the channel that chat already named; a new world waits until someone sets one.
"""
from pathlib import Path

from kd_say import say

HERE = Path(__file__).resolve().parent
ADAPTERS = HERE.parents[1] / "agora" / "modules" / "adapters"


def q(text):
    # Kernel Lines quoting; the text is always one literal value.
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def install(token, port=8810):
    receipts = []

    def line(text):
        out = say(text, token, port)
        if not out.get("ok"):
            raise RuntimeError("Twitch setup stopped: " + out.get("text", "world line refused"))
        receipts.extend(out.get("records", []))
        return out

    def find(kind, clause):
        return line(f"rows {kind} {clause}")["rows"]

    modules = find("module", "name=twitch")
    if not modules:
        raise RuntimeError("Twitch source module is missing")
    chats = find("chat", "name=twitch")
    chat = chats[0]["id"] if chats else line(
        f'make kind=chat name=twitch title="Twitch chat" read_only=yes source={modules[0]["id"]}')["made"][0]
    if not find("adapter", "name=twitch"):
        channel = str((chats[0] if chats else {}).get("channel") or "")
        text = (ADAPTERS / "twitch.adapter").read_text(encoding="utf-8")
        line(f"make kind=adapter name=twitch title=\"Twitch chat reader\" into={chat}"
             + (f" channel={q(channel)}" if channel else "") + f" text={q(text)}")
    painter_chat = "s" + "".join(c for c in chat if c.isdigit())
    for kind, name, filename, extra in (
        ("style", "twitch-style", "twitch-style.style", ""),
        ("lens", "twitch-chat", "twitch-chat.lens", " style=twitch-style"),
    ):
        if not find(kind, f"name={name}"):
            text = (HERE / "lenses" / filename).read_text(encoding="utf-8").replace("$CHAT", painter_chat)
            line(f"make kind={kind} name={name} text={q(text)}{extra}")
    if not find("button", "slot=twitch"):
        line('make kind=button name=twitch-pin label="Twitch" icon=message-circle bar=taskbar '
             'slot=twitch does="window.open twitch-chat"')
    return receipts
