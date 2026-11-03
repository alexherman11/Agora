"""Install Twitch chat, view and dock pin once through ordinary world lines.

Called at desktop startup. Existing views and an unpinned button stay as authored.
No window opens here. The anonymous reader is stopped with `off twitch`.
"""
from pathlib import Path

from kd_say import say
from kd_twitch import CHANNEL, q

HERE = Path(__file__).resolve().parent


def install(token, port=8810, channel="dr_bizzlebop"):
    channel = channel.lower().lstrip("#")
    if not CHANNEL.fullmatch(channel):
        raise ValueError("invalid Twitch channel")
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
        'make kind=chat name=twitch title="Twitch chat" read_only=yes '
        f'source={modules[0]["id"]} channel={channel}'
    )["made"][0]
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
