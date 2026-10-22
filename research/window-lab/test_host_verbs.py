"""test_host_verbs.py: the home base's verbs and settings, with a stand-in for the home base (a5300). 15 Oct 2026.

    python test_host_verbs.py

Nothing reaches the screen or Spotify: the media verbs are only listed here, never called (`python media.py play` is
the hand test). call() never raises; settings read props from examine's first line and keep defaults for the rest.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import host_verbs as H  # noqa: E402

bad = []


def check(what, ok, got=None):
    print(("ok   " if ok else "FAIL ") + what + ("" if ok else f"  (got {got!r})"))
    if not ok:
        bad.append(what)


class Home:
    def __init__(self):
        self.did = []

    def bring(self, h):
        self.did.append(("bring", h))
        return True

    def hide(self):
        self.did.append(("hide",))

    def say_desktop(self):
        self.did.append(("say",))


h = Home()
names = [r["name"] for r in H.rows()]
check("the rows are the verbs, each with what it does", names == ["bring", "notify", "hide", "start", "window", "wm.start", "wm.stop", "media.play", "media.next", "media.prev",
                                                     "media.shuffle", "media.repeat", "media.like", "media.unlike",
                                                     "media.connect", "voice.listen", "voice.stop", "voice.hush",
                                                     "voice.say"]
      and all(r["about"] for r in H.rows()), H.rows())
check("hide hides", H.call(h, "hide") == "ok hidden" and h.did[-1] == ("hide",), h.did)
# a5980: start puts the home base away, then asks for the Start menu (stood in for: nothing reaches the screen)
h.open_start = lambda: h.did.append(("start",))
check("start hides, then opens Start", H.call(h, "start") == "ok opened the Start menu" and h.did[-2:] == [("hide",), ("start",)], h.did)
check("bring takes the window's handle, as the build filled it", H.call(h, "bring", "1312") == "ok brought 1312 forward"
      and h.did[-1] == ("bring", 1312), h.did)
check("bring takes it quoted too", H.call(h, "bring", '"77"').startswith("ok") and h.did[-1] == ("bring", 77), h.did)
r = H.call(h, "bring", "Notepad")
check("bring refuses words that are not a handle, and does nothing", r.startswith("ERR bring takes") and h.did[-1] == ("bring", 77), r)
r = H.call(h, "shutdown")
check("an unknown verb is refused, naming the ones there are", r.startswith("ERR the home base has no verb 'shutdown'") and "media.next" in r, r)
# a5500: window <lens> opens a lens as its own window (lens_window, stood in for here: nothing reaches the screen)
import lens_window  # noqa: E402
opened = []
lens_window.open_window = lambda lens, who, world: opened.append((lens, who, world)) or type("P", (), {"pid": 42})()
h.a = type("A", (), {"who": "alex", "world": "frontier"})()
r = H.call(h, "window", "command-center")
check("window opens the lens as the home base's person in its world, and puts the home base away",
      r == "ok opened command-center as a window (process 42)" and opened == [("command-center", "alex", "frontier")]
      and h.did[-1] == ("hide",), (r, opened, h.did))
r = H.call(h, "window", "C:/Windows/notepad.exe")
check("window takes a lens's name only, never a path or a program", r.startswith("ERR window takes") and len(opened) == 1, r)
# a5824: notify <words> shows a toast (notify.show, stood in for here: nothing reaches the screen)
import notify  # noqa: E402
shown = []
notify.show = lambda words, sound=False, by="": shown.append((words, sound, by)) or "shown"
r = H.call(h, "notify", '"the writing area is done"')
check("notify shows the words, outer quotes off, silent, from the home base's person",
      r == "ok notified: the writing area is done" and shown[-1] == ("the writing area is done", False, "alex"), (r, shown))
r = H.call(h, "notify", "! it broke")
check("words that begin with ! ask for the sound", r.endswith("(with sound)") and shown[-1] == ("it broke", True, "alex"), (r, shown))
r = H.call(h, "notify", "  ")
check("notify with no words is refused and shows nothing", r.startswith("ERR notify takes") and len(shown) == 2, r)
# a6113: wm.start / wm.stop go to wm_switch.SWITCH (stood in for here: no window manager runs; test_wm_switch.py runs
# the real one on the sandbox desktop)
import wm_switch  # noqa: E402
asked = []
wm_switch.SWITCH = type("S", (), {"start": lambda s, hud, lenses: asked.append(("start", lenses)) or "started it",
                                  "stop": lambda s, hud: asked.append(("stop",)) or "stopped it"})()
r = H.call(h, "wm.start")
check("wm.start starts it with wm.py's own windows, then puts the home base away",
      r == "ok started it" and asked[-1] == ("start", "") and h.did[-1] == ("hide",), (r, asked, h.did))
r = H.call(h, "wm.start", "doc-editor,command-center")
check("wm.start takes lens names joined by commas", r.startswith("ok") and asked[-1] == ("start", "doc-editor,command-center"), r)
r = H.call(h, "wm.start", "doc-editor; calc.exe")
check("wm.start refuses anything but lens names, and starts nothing", r.startswith("ERR wm.start takes") and len(asked) == 2, r)
r = H.call(h, "wm.stop")
check("wm.stop stops it", r == "ok stopped it" and asked[-1] == ("stop",), r)


def no_toast(words, sound=False, by=""):
    raise RuntimeError("Access is denied")


notify.show = no_toast
r = H.call(h, "notify", "x")
check("a toast Windows did not take is said as a refusal", r == "ERR Windows did not take the toast: Access is denied", r)
check("a verb that fails says so instead of raising", H.call(type("X", (), {"hide": lambda s: 1 / 0})(), "hide").startswith("ERR hide failed: ZeroDivisionError"))

p = H.parse_props('a5208 note "home-base" · style=home-style hotkey=Ctrl+Shift+F9 monitor=2 note="a b" · 277w')
check("props read from examine's first line", p == {"style": "home-style", "hotkey": "Ctrl+Shift+F9", "monitor": "2", "note": "a b"}, p)
check("no props, no props", H.parse_props('a1 note "x" · 3w') == {})
check("hotkeys read", H.hotkey("Ctrl+Alt+J") == (0x3, 0x4A) and H.hotkey("Win+Space") == (0x8, 0x20) and H.hotkey("Ctrl+F12") == (0x2, 0x7B))
check("a bare key or an unknown modifier does not read", H.hotkey("J") is None and H.hotkey("Hyper+J") is None and H.hotkey("Ctrl+F25") is None)
a = H.work_area("main")
check("the main monitor's work area", len(a) == 4 and a[2] > 0 and a[3] > 0, a)
check("a monitor that is not there is the main one", H.work_area("9") == a, H.work_area("9"))

# settings through a door that is not there: the defaults, nothing unread
s = H.settings("http://127.0.0.1:9", "nowhere", "home-base")
check("no door: the defaults, and it says the door did not answer", s == {**H.DEFAULTS, "unread": [], "read": False}, s)
check("winkey is on unless the note says off", H.DEFAULTS["winkey"] == "on")

print("host verbs:", "all passed" if not bad else f"{len(bad)} failed")
sys.exit(1 if bad else 0)
