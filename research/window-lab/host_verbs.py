"""host_verbs.py: what the home base can be asked to do from inside the world (a5300). 15 Oct 2026.

    python host_verbs.py                     the verbs, as the rows the home base says (witnessed:host)
    python host_verbs.py settings [lens]     the settings the home base would read from its lens note now

A lens asks with `on click host <verb> [words]` (scene.py). The painter sends that to the program it is painted in
(window.pywebview.api.host(verb, words) in the home base) and never to the desk; the home base answers through call()
here. So a new button is lens lines only, and a new power is one entry in VERBS below, never a new js_api in hud.py.

The table is closed on purpose: named verbs, no program to run, no shell line, no keys pressed but the media keys.
media.* (a6443) press through Windows' media session first (media.py); media.like and media.unlike change Spotify's
Liked Songs through its Web API, once Alex has connected it (spotify_like.py).
`notify <words>` (a5824) shows a toast through notify.py; its words are shown, never run.
`window <lens>` (a5500) opens only the desk's own painter on a lens, as lens_window.py does; never another program.
`wm.start [lenses]` and `wm.stop` (a6113) start and stop the window manager, wm.py, as the home base's child
(wm_switch.py); while it runs the home base says witnessed:wm.

Settings are props on the lens note the home base paints (home-base, a5208), read through the door each time it opens:
    hotkey=Ctrl+Alt+J      the key that shows or hides it (Ctrl, Alt, Shift, Win + a letter, digit, F1-F24 or Space)
    monitor=main           main, or 1, 2 ... in the order Windows lists its monitors
    hide_taskbar=yes       no leaves the taskbar showing; yes covers it while the home base is shown (hud.py covers the
                           whole monitor, never hides the taskbar's own window, so a killed home base leaves it whole)
    capture=on             a5834: the control screen (capture/capture.py: hold Ctrl+Alt and drag) runs while the home
                           base runs, putting each capture on the person's own chat draft; off stops it at the next
                           Ctrl+Alt+J (and keeps it off from the next start)
    winkey=on              a5980: a bare tap of the Windows key shows or hides it (winkey.py); off gives the Win key
                           back to Windows (Start opens from it again) within 15 seconds; the hotkey above stays
A prop that is missing or does not read keeps its default, and settings() says which ones did not.

What hud.py adds to use this (a5300's hook, put into hud.py by a5394):
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

DEFAULTS = {"hotkey": "Ctrl+Alt+J", "monitor": "main", "hide_taskbar": "yes", "capture": "on", "winkey": "on"}


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
            raise Refused(f"media.{action}: " + ("the media session did not take it" if action in ("shuffle", "repeat")
                                                  else "neither the media session, Spotify nor the media key took it"))
        threading.Timer(0.8, hud.say_desktop).start()            # the new song, soon after
        return f"media.{action} to {did}"
    return press


def _like(liked):
    # a6443: the heart. The song is what Windows' media session says now; spotify_like.Library asks Spotify's account
    # which track that is (never a guess) and saves or removes it. Refused with the reason when it cannot know
    def press(hud, words):
        import media
        import spotify_like
        st = media.SESSION.state() if media.SESSION.start() else None
        s = (st or {}).get("s") if st else None
        if not s or not (s.get("title") or "").strip():
            raise Refused("nothing is playing that Windows' media session names")
        player = media.player_of(s.get("app"))
        if player != "Spotify":
            raise Refused(f"the song is playing in {player}; Liked Songs is Spotify's")
        try:
            said = media.likes().set(s["title"], s.get("artist") or "", liked)
        except spotify_like.Refused as e:
            raise Refused(str(e))
        threading.Timer(0.1, hud.say_desktop).start()             # the heart, filled or not, at once
        return said
    return press


_CONNECT_LOCK = threading.Lock()


def _connect(hud, words):
    """Only an explicit button press may open the account setup pages."""
    import media
    import spotify_connect
    import spotify_like
    import webbrowser
    if not _CONNECT_LOCK.acquire(blocking=False):
        return "Spotify connection is already open"
    try:
        library = media.likes()
    except Exception:
        _CONNECT_LOCK.release()
        raise Refused(spotify_like.connection_message(None)) from None
    library.connect_status = "Spotify connection is open in your browser."

    def refresh():
        try:
            hud.say_desktop()
        except Exception:
            # Refresh failure must not leak connection details via a thread traceback.
            pass

    def run():
        try:
            spotify_connect.connect(library, webbrowser.open)
            library.connect_status = ""
        except Exception as error:
            # Do not publish account replies, codes or tokens into the world.
            library.connect_status = spotify_like.connection_message(error)
        finally:
            _CONNECT_LOCK.release()
            refresh()

    try:
        threading.Thread(target=run, daemon=True).start()
    except Exception:
        _CONNECT_LOCK.release()
        library.connect_status = spotify_like.connection_message(None)
        refresh()
        raise Refused(library.connect_status) from None
    return "opening Spotify connection"


def _window(hud, words):
    # a5500: a dock icon opens an Agora app as its own window: one lens, painted as the home base's own person in its
    # world, as lens_window.py does (Edge in app mode). A lens name only: no program, path or address
    lens = words.strip().strip('"')
    if not re.fullmatch(r"[a-z][a-z0-9-]*", lens):
        raise Refused(f"window takes a lens's name (lower case, words joined by -); got {words!r}")
    import lens_window
    p = lens_window.open_window(lens, hud.a.who, hud.a.world)
    hud.hide()
    return f"opened {lens} as a window (process {p.pid})"


def _notify(hud, words):
    # a5824: a Windows toast, title Agora, silent unless the words begin with ! (notify.py says how and its limits).
    # This one leaves no record in the world; the house verb `notify` does (a line in Notifications sent)
    import notify
    text, sound = notify.words_of(words)
    if not text:
        raise Refused("notify takes the words to show")
    try:
        got = notify.show(text, sound=sound, by=getattr(getattr(hud, "a", None), "who", ""))
    except RuntimeError as e:
        raise Refused(f"Windows did not take the toast: {e}")
    return f"notified: {text[:80]}" + (" (with sound)" if sound else "") + ("" if got == "shown" else f" ({got})")


def _start(hud, words):
    # a5980: with the Win key taken by the home base, Start opens from here (and from Ctrl+Esc, Windows' own). No key is
    # pressed: hud.open_start asks Windows for the Start menu as its window menu does (WM_SYSCOMMAND SC_TASKLIST)
    hud.hide()
    hud.open_start()
    return "opened the Start menu"


def _wm_start(hud, words):
    # a6113: the window manager (wm.py) from a dock icon, never a terminal. Words: the lenses to open as windows,
    # comma-separated (none: wm.py's own three). wm_switch.py says how it never leaves a window displaced
    lenses = words.strip().strip('"')
    if lenses and not re.fullmatch(r"[a-z][a-z0-9-]*(,[a-z][a-z0-9-]*)*", lenses):
        raise Refused(f"wm.start takes lens names joined by commas, or nothing; got {words!r}")
    import wm_switch
    try:
        said = wm_switch.SWITCH.start(hud, lenses)
    except RuntimeError as e:
        raise Refused(str(e))
    hud.hide()                                                   # the strip is under the home base: show it
    return said


def _wm_stop(hud, words):
    import wm_switch
    return wm_switch.SWITCH.stop(hud)


VERBS = {
    "bring": ("bring that window forward and put the home base away", "window", _bring),
    "notify": ("show a Windows notification, title Agora (silent; words beginning ! ring)", "words", _notify),
    "hide": ("put the home base away", "", _hide),
    "start": ("put the home base away and open Windows' Start menu", "", _start),
    "window": ("open a lens as its own window (an Agora app) and put the home base away", "lens", _window),
    "wm.start": ("start the window manager (Agora windows in a strip; witnessed:wm says it is on) and put the home base "
                 "away", "lenses", _wm_start),
    "wm.stop": ("stop the window manager: every window back where it was, its own windows closed", "", _wm_stop),
    "media.play": ("play or pause (Spotify, else the media key)", "", _media("play")),
    "media.next": ("the next song", "", _media("next")),
    "media.prev": ("the song before, or this one from its start", "", _media("prev")),
    "media.shuffle": ("shuffle on or off (the media session's own control)", "", _media("shuffle")),
    "media.repeat": ("repeat: off, then all, then this song, then off", "", _media("repeat")),
    "media.like": ("save the song playing to Spotify's Liked Songs", "", _like(True)),
    "media.unlike": ("take the song playing out of Spotify's Liked Songs", "", _like(False)),
    "media.connect": ("connect Spotify through its consent page; no library changes", "", _connect),
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
        # a5834: the thing's own line, not the first: a '!! since your last look' line often comes before it, and
        # every setting then read as its default
        head = next((ln for ln in text.splitlines() if re.match(r"a\d+ ", ln)), "")
        props = parse_props(head) if text and not text.startswith("ERR") else {}
        read = bool(head)
    except (OSError, ValueError):
        props, read = {}, False
    for k in DEFAULTS:
        v = str(props.get(k, "")).strip()
        if not v:
            continue
        ok = (k == "hotkey" and hotkey(v)) or (k == "monitor" and (v == "main" or v.isdigit())) or \
             (k == "hide_taskbar" and v in ("yes", "no")) or (k in ("capture", "winkey") and v in ("on", "off"))
        (out.__setitem__(k, v) if ok else bad.append(f"{k}={v}"))
    out["unread"] = bad
    out["read"] = read            # a5980: False when the door did not answer, so a caller can keep what it had
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
