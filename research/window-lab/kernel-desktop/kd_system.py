"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

kd_system: what the machine is doing, as a module (SHAPE 11): system.now (see) and live widget values.

Claude (PROOF a13428), 24 Oct 2026; the readings themselves are sysread.py (ctypes only, nothing installed).

    system.now    CPU, memory, network, volume, battery, the window in front and the programs open   (see)

Every two seconds it writes <world>/modules/system/live.json, one key per reading (cpu, memory, network, volume,
battery, focused, apps), each {value, detail}; the desk's live layer (live.py) paints them onto widgets that `shows=`
that key. Nothing is recorded: a reading is not a fact. The title of the window in front is shown on Alex's own bar
and never written into the world. With --headless it writes fixed readings (hidden tests).
Off switch: off system.
"""
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from modproto import Module, log                    # noqa: E402

HEADLESS = "--headless" in sys.argv
OURS = ("python", "pythonw", "msedgewebview2")       # the desk's own windows are not "programs open"
NAMES = {"windowsterminal": "Terminal", "msedge": "Edge", "chatgpt": "ChatGPT", "obs64": "OBS", "code": "Code",
         "explorer": "Files", "applicationframehost": "Settings", "claude": "Claude", "spotify": "Spotify"}


def nice(program):
    return NAMES.get(program.lower(), program[:1].upper() + program[1:])


def _rate(b):
    for unit, n in (("MB/s", 1 << 20), ("KB/s", 1 << 10)):
        if b >= n:
            return f"{b / n:.1f} {unit}" if b < 10 * n else f"{b / n:.0f} {unit}"
    return f"{b:.0f} B/s"


def shape(r):
    """sysread.read_all() -> the live keys: each {value, detail}."""
    out = {}
    if r.get("cpu"):
        out["cpu"] = {"value": f"{r['cpu']['pct']:.0f}%", "detail": ""}
    if r.get("memory"):
        m = r["memory"]
        out["memory"] = {"value": f"{m['pct']:.0f}%", "detail": f"{m['used_gb']:.1f} of {m['total_gb']:.0f} GB"}
    if r.get("network"):
        n = r["network"]
        out["network"] = {"value": f"↓{_rate(n['down'])}", "detail": f"↑{_rate(n['up'])}"}
    if r.get("volume"):
        v = r["volume"]
        out["volume"] = {"value": "muted" if v["muted"] else f"{v['pct']}%", "detail": ""}
    b = r.get("battery")
    out["battery"] = ({"value": f"{b['pct']}%", "detail": "charging" if b["charging"] else "battery"} if b
                      else {"value": "", "detail": "no battery"})
    f = r.get("focused")
    out["focused"] = {"value": (f.get("title") or nice(f.get("program") or ""))[:90] if f else "",
                      "detail": nice(f.get("program") or "") if f else ""}
    apps = [a for a in (r.get("apps") or []) if a.get("program", "").lower() not in OURS]
    out["apps"] = {"value": " · ".join(nice(a["program"]) + (f" {a['count']}" if a["count"] > 1 else "")
                                       for a in apps[:7]),
                   "detail": f"{sum(a['count'] for a in apps)} windows"}
    return out


FIXED = {"cpu": {"pct": 12.0}, "memory": {"pct": 41.0, "used_gb": 13.1, "total_gb": 32.0},
         "network": {"down": 1200.0, "up": 300.0}, "volume": {"pct": 35, "muted": False},
         "battery": {"pct": 84, "charging": True},           # hidden tests read a laptop's battery (the shell's battery chip)
         "focused": {"program": "notepad", "title": "notes.txt - Notepad"},
         "apps": [{"program": "chrome", "count": 3}, {"program": "code", "count": 1}]}


class System:
    def __init__(self):
        self.home, self.last = None, {}
        self.reader = None
        self.m = Module(offer=self.offer(), on_call=self.call, on_hello=self.hello, on_off=self.off)

    def offer(self):
        return [{"word": "system.now", "kind": "see", "takes": "", "may": "anyone",
                 "help": "system.now: what this machine is doing: CPU, memory, network, volume, battery, the window "
                         "in front and the programs open. Widgets show the same (make kind=widget bar=top "
                         "side=right shows=cpu label=CPU order=30)."}]

    def hello(self, msg):
        if msg.get("home"):
            self.home = Path(msg["home"])

    def read(self):
        if HEADLESS:
            return FIXED
        if self.reader is None:
            import sysread
            self.reader = sysread.Reader(exclude=OURS)
        return self.reader.read_all()

    def call(self, msg):
        live = self.last or shape(self.read())
        rows = [dict(v, key=k, kind="reading") for k, v in live.items()]
        return {"text": "\n".join(f"{k}: {v['value']} ({v['detail']})" for k, v in live.items()), "rows": rows}

    def write(self):
        self.last = shape(self.read())
        if not HEADLESS:
            import native_shell
            path = native_shell.program_path(native_shell.u.GetForegroundWindow())
            symbol = native_shell.executable_icon(path)
            if symbol:
                self.last['focused']['symbol'] = symbol
        if not self.home:
            return
        tmp = self.home / "live.json.tmp"
        tmp.write_text(json.dumps(dict(self.last, at=time.time()), ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.home / "live.json")

    def loop(self):
        while not self.m.closed.is_set():
            try:
                self.write()
            except Exception as exc:                # noqa: BLE001  a reading never stops the module
                log(f"system reading failed: {exc!r}")
            self.m.closed.wait(2)

    def off(self):
        os._exit(0)

    def run(self):
        self.m.run_reader()
        self.m.ready.wait(30)
        self.loop()


if __name__ == "__main__":
    System().run()
