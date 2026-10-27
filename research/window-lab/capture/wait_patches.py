"""a10486: the chat lenses wait for a capture still arriving. Staged world hunks with exact inverses; never applied live.

    python wait_patches.py            the hunks, as JSON (lens, old, new)
    python wait_patches.py forward    the desk lines that apply them (do replace, one exact passage each)
    python wait_patches.py inverse    the desk lines that take them back out

Release requests a draft reservation through the existing Desk route. Once
admitted, pending blocks native Send and the lens can show "Attaching capture…".
The bounded painter wait is presentation; native admission selects current IDs.
The original reply, audience and topic actions are preserved. The four normal
capture-bearing Send actions opt in; document comments/original-place reply
routes are unchanged and are not certified to carry capture attachments here.
These hunks have never been applied live.
"""
import json
import sys
from pathlib import Path

LENSES = {"jeff-chat": "a5210", "conversation": "a5086"}

COMING_HUD = '''    coming : row
      role attachment
      only when held = "" and ($draft.pending or "") != ""
      label : text "Attaching capture…"
        role meta
        share 1
      stop : text "×"
        role tool
        tip "Stop waiting" "Send without the capture still coming"
        on click do prop $draft pending=""
'''

COMING_NATIVE = '''  coming : row
    role attachment
    only when ($draft.pending or "") != ""
    label : text "Attaching capture…"
      role meta
      share 1
    stop : text "×"
      role tool
      tip "Stop waiting" "Send without the capture still coming"
      on click do prop $draft pending=""
'''

HUD_ATT = '    attachments : column\n      only when held = ""\n      of captures $draft.context\n'
HUD_SAY = '      hint "Write to JEFF, or anyone above…"\n      lines 1..12\n      commit explicit\n'
NATIVE_ATT = '  attachments : column\n    of captures $draft.context\n'
NATIVE_SAY = '    lines 3..10\n    commit explicit\n'


def patches():
    hunks = [
        ("jeff-chat", HUD_ATT, COMING_HUD + HUD_ATT),
        ("jeff-chat", HUD_SAY, HUD_SAY + '      waits "$draft.pending" "capture"\n'),
        ("conversation", NATIVE_ATT, COMING_NATIVE + NATIVE_ATT),
        ("conversation", NATIVE_SAY, NATIVE_SAY + '    waits "$draft.pending" "capture"\n'),
    ]
    # Freeze exact public lens source read through Desk, not a stale whole-lens
    # replacement. Every action keeps its audience/reply/topic and cleanup.
    bases = json.loads(Path(__file__).with_name("world-bases-20261022.json").read_text(encoding="utf-8"))
    needle = 'captures="$draft.context" context_from="$draft"'
    admitted = 'captures=current context_from="$draft" capture_generation="$(($draft.capture_generation or "0"))"'
    for name, text in bases.items():
        actions = [line for line in text.splitlines(keepends=True) if needle in line]
        if len(actions) != 2:
            raise ValueError(f"{name}: expected the two normal Conversation Send actions")
        hunks += [(name, line, line.replace(needle, admitted)) for line in actions]
    return hunks


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def apply(name, text, inverse=False):
    """The lens's text with the hunks applied (or taken out): each passage must stand exactly once."""
    for target, old, new in (patches()[::-1] if inverse else patches()):
        if target == name:
            a, b = (new, old) if inverse else (old, new)
            if text.count(a) != 1:
                raise ValueError(f"{name}: expected one occurrence of {a[:80]!r}, found {text.count(a)}")
            text = text.replace(a, b, 1)
    return text


def lines(inverse=False):
    out = []
    for name, old, new in (patches()[::-1] if inverse else patches()):
        a, b = (new, old) if inverse else (old, new)
        out += [f"read {LENSES[name]}", f"do replace {LENSES[name]} old={q(a)} new={q(b)}"]
    return out


if __name__ == "__main__":
    how = sys.argv[1] if len(sys.argv) > 1 else ""
    if how in ("forward", "inverse"):
        print("\n".join(lines(how == "inverse")))
    else:
        print(json.dumps([{"lens": n, "old": o, "new": w} for n, o, w in patches()], indent=2, ensure_ascii=False))
