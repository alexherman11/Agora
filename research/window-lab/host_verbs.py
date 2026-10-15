"""host_verbs.py: what the home base can be asked to do from inside the world (a5300). 15 Oct 2026.

    python host_verbs.py                     the verbs, as the rows the home base says (witnessed:host)
    python host_verbs.py settings [lens]     the settings the home base would read from its lens note now

A lens asks with `on click host <verb> [words]` (scene.py). The painter sends that to the program it is painted in
(window.pywebview.api.host(verb, words) in the home base) and never to the desk; the home base answers through call()
here. So a new button is lens lines only, and a new power is one entry in VERBS below, never a new js_api in hud.py.

The table is closed on purpose: named verbs, no program to run, no shell line, no keys pressed but the media keys.

Settings are props on the lens note the home base paints (home-base, a5208), read through the door each time it opens:
    hotkey=Ctrl+Alt+J      the key that shows or hides it (Ctrl, Alt, Shift, Win + a letter, digit, F1-F24 or Space)
    monitor=main           main, or 1, 2 ... in the order Windows lists its monitors
    hide_taskbar=no        yes hides the taskbar while the home base is shown (read here; hud.py does the hiding)
A prop that is missing or does not read keeps its default, and settings() says which ones did not.

What hud.py adds to use this (a5300; written for Claude, since hud.py is Claude's uncommitted work):
    import host_verbs                                                         # beside import witnessed
    witnessed.write(self.a.world, "host", host_verbs.rows(), by="hud")        # in Hud.say_desktop, beside the desktop
    def host(self, verb, words=""):                                           # on Api
        return host_verbs.call(self._hud, verb, words)
    witnessed.clear(..., "host")                                              # in Hud.closed and in --stop
    self.settings = host_verbs.settings(self.door, self.a.world, self.a.lens) # in Hud.show, first; then use
        host_verbs.work_area(self.settings["monitor"]) for work_area(), and self.settings["hide_taskbar"]
    host_verbs.hotkey(s["hotkey"]) -> (mods, vk) for RegisterHotKey in Hud.keys (read once at start)
Once the lens asks with `host bring $w.name` and `host media.play`, CLICKS and media.CLICKS are no longer injected.
"""
import ctypes
import json
import re
import sys
import threading
import urllib.request
from ctypes import wintypes as wt

DEFAULTS = {"hotkey": "Ctrl+Alt+J", "monitor": "main", "hide_taskbar": "no"}


# -- the verbs: name -> (what it does, what words it takes, how). Each `how` gets the home base and the words, and
# answers a short line; a refusal raises Refused with the reason.
class Refused(Exception):
    pass


def _bring(hud, words):
    try:
        h = int(words.strip().strip('"'))
    except ValueError:
        raise Refused(f"bring takes a window's handle (a witnessed:desktop row's name); got {words!r}")
    if not hud.bring(h):
        raise Refused(f"no window {h}")
    return f"brought {h} forward"


def _hide(hud, words):
    hud.hide()
    return "hidden"


def _media(action):
    def press(hud, words):
        import media
        did = media.press(action)
        if not did:
            raise Refused(f"media.{action}: neither Spotify nor the media key took it")
        threading.Timer(0.8, hud.say_desktop).start()            # the new song, soon after
        return f"media.{action} to {did}"
    return press


VERBS = {
    "bring": ("bring that window forward and put the home base away", "window", _bring),
    "hide": ("put the home base away", "", _hide),
    "media.play": ("play or pause (Spotify, else the media key)", "", _media("play")),
    "media.next": ("the next song", "", _media("next")),
    "media.prev": ("the song before, or this one from its start", "", _media("prev")),
}


def rows():
    """What the home base says it can do, one row per verb: {name, about, takes}."""
    return [{"name": k, "about": v[0], "takes": v[1]} for k, v in VERBS.items()]


def call(hud, verb, words=""):
    """A lens's `host <verb> [words]`, from the painter. -> "ok <what was done>" or "ERR <why not>", never raises."""
    v = VERBS.get(str(verb))
    if v is None:
        return f"ERR the home base has no verb {verb!r}; it has {', '.join(VERBS)} (rows witnessed:host)"
    try:
        return "ok " + v[2](hud, str(words or ""))
    except Refused as e:
        return f"ERR {e}"
    except Exception as e:                                       # a fault in a verb must reach the page as words
        return f"ERR {verb} failed: {type(e).__name__}: {e}"


# -- settings: props on the lens note
_PROPS = re.compile(r'(\w+)=("(?:[^"\\]|\\.)*"|\S+)')


def parse_props(head):
    """The props of `examine`'s first line, e.g. 'a5208 note "home-base" · style=home-style hotkey=Ctrl+Alt+K · 277w'."""
    parts = head.split(" · ")
    out = {}
    for seg in parts[1:]:
        for k, v in _PROPS.findall(seg):
            out[k] = json.loads(v) if v.startswith('"') else v
    return out


def settings(door, world, lens, who="hud"):
    """-> DEFAULTS overlaid with the lens note's props, plus "unread": the props given that did not read."""
    out, bad = dict(DEFAULTS), []
    try:
        body = json.dumps({"session": world, "as": who, "line": f'examine "{lens}"'}).encode("utf-8")
        r = json.loads(urllib.request.urlopen(urllib.request.Request(door + "/api/do", data=body, method="POST"),
                                              timeout=3).read())
        text = r.get("text") or ""
        props = parse_props(text.splitlines()[0]) if text and not text.startswith("ERR") else {}
    except (OSError, ValueError):
        props = {}
    for k in DEFAULTS:
        v = str(props.get(k, "")).strip()
        if not v:
            continue
        ok = (k == "hotkey" and hotkey(v)) or (k == "monitor" and (v == "main" or v.isdigit())) or \
             (k == "hide_taskbar" and v in ("yes", "no"))
        (out.__setitem__(k, v) if ok else bad.append(f"{k}={v}"))
    out["unread"] = bad
    return out


MODS = {"ctrl": 0x2, "alt": 0x1, "shift": 0x4, "win": 0x8}


def hotkey(text):
    """'Ctrl+Alt+J' -> (modifiers, virtual key) for RegisterHotKey, or None when it does not read (no modifier is
    refused too: a bare key would be taken from every program)."""
    *mods, key = [p.strip().lower() for p in str(text).split("+")]
    if not mods or any(m not in MODS for m in mods):
        return None
    m = 0
    for x in mods:
        m |= MODS[x]
    if len(key) == 1 and key.isalnum():
        return m, ord(key.upper())
    if key == "space":
        return m, 0x20
    f = re.fullmatch(r"f([1-9]|1[0-9]|2[0-4])", key)
    return (m, 0x6F + int(f.group(1))) if f else None


# -- the monitor setting
class _MI(ctypes.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("rcMonitor", wt.RECT), ("rcWork", wt.RECT), ("dwFlags", wt.DWORD)]


def monitors():
    """-> [(left, top, width, height) of each monitor's work area, primary flag], in Windows' order."""
    user32 = ctypes.windll.user32
    out = []
    proc = ctypes.WINFUNCTYPE(wt.BOOL, wt.HMONITOR, wt.HDC, ctypes.POINTER(wt.RECT), wt.LPARAM)

    def each(hm, _dc, _r, _l):
        mi = _MI()
        mi.cbSize = ctypes.sizeof(mi)
        user32.GetMonitorInfoW(hm, ctypes.byref(mi))
        r = mi.rcWork
        out.append(((r.left, r.top, r.right - r.left, r.bottom - r.top), bool(mi.dwFlags & 1)))
        return True

    user32.EnumDisplayMonitors.argtypes = [wt.HDC, ctypes.c_void_p, proc, wt.LPARAM]
    user32.GetMonitorInfoW.argtypes = [wt.HMONITOR, ctypes.c_void_p]
    user32.EnumDisplayMonitors(None, None, proc(each), 0)
    return out


def work_area(monitor="main"):
    """The work area of `monitor` (main, or 1, 2 ...); the main one when that monitor is not there."""
    ms = monitors()
    if str(monitor).isdigit() and 1 <= int(monitor) <= len(ms):
        return ms[int(monitor) - 1][0]
    return next((a for a, primary in ms if primary), ms[0][0] if ms else (0, 0, 1280, 720))


if __name__ == "__main__":
    if sys.argv[1:2] == ["settings"]:
        print(settings("http://127.0.0.1:8794", "frontier", sys.argv[2] if len(sys.argv) > 2 else "home-base"))
    else:
        for r in rows():
            print(f"{r['name']:<11} {r['takes']:<7} {r['about']}")
        print("monitors:", monitors())
