"""The surfaces a widget holds when its page is a browser tab, not a desktop window: the web host's half of what
kd_window.py offers on Alex's desktop (window.surface, window.bar). Holding one changes nothing on any screen; the
lease only says a page is open, so `holds` lists it and `off` ends it, as on the desktop.

Claude, 5 Nov 2026, for the Seabright public host (src/community/board/PUBLIC-HOST.md). Source: seam.
A genesis or steward installs it: module web-surface run=["<python>", "<this file>"] publishes="window.*" grants=""
"""
import json
import sys


def send(msg):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


for raw in sys.stdin:
    msg = json.loads(raw)
    t = msg.get("t")
    if t == "hello":
        send({"t": "offer", "words": [
            {"word": "window.surface", "kind": "hold", "takes": "", "may": "anyone",
             "help": "window.surface: a widget's page open in a browser tab (the web host), listed by holds and "
                     "ended by off. Nothing is drawn on any screen."},
            {"word": "window.bar", "kind": "hold", "takes": "", "may": "anyone",
             "help": "window.bar: a widget's slot in a web host's bar, listed by holds and ended by off."}]})
    elif t == "call":
        send({"t": "answer", "use": msg.get("use"), "refused": "these surfaces are held by a widget's page, not said"})
    elif t == "status?":
        send({"t": "status", "use": msg.get("use"), "doing": "web host surfaces for browser tabs"})
    elif t == "off":
        break
