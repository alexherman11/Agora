"""measure_wm: how long from a key, and from a lens edit, to the windows in place (a5052 (c)). Many of each, not one.

    python measure_wm.py [--door http://127.0.0.1:8795] [--as claude] [--n 12]

Starts wm.py with its three windows, then asks (state/wm.keys, naming windows, so the focus is never taken) for n
slides, n pin/unpin pairs and n collapse/expand pairs, 2 s apart, and makes n lens edits to wm-strip through the door
(one word of the layout changed and changed back). Each timing is the host's own: from writing its rows, or from the
moment before the edit was sent, to the last window moved. Prints min, median and max of each.
"""
import argparse
import json
import re
import statistics
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wm   # noqa: E402


def ask(line, wait=2.0):
    wm.KEYS_FILE.write_text(line + "\n", encoding="utf-8")
    time.sleep(wait)


def door_do(door, who, line):
    body = json.dumps({"session": "frontier", "as": who, "line": line, "whole": True}).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(door + "/api/do", data=body,
                                                                    headers={"Content-Type": "application/json"}), timeout=60).read()).get("text") or ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--door", default="http://127.0.0.1:8795")
    ap.add_argument("--as", dest="who", default="claude")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--notation", default=str(HERE.parent / "text-desk" / "notation"))
    a = ap.parse_args()
    wm.LOG.unlink(missing_ok=True)
    host = subprocess.Popen([sys.executable, str(HERE / "wm.py"), "--door", a.door, "--as", a.who, "--notation", a.notation])
    time.sleep(16)
    for _ in range(a.n):
        ask("slide 1")
    for _ in range(a.n):
        ask("pin w2")
        ask("pin w2")
    for _ in range(a.n):
        ask("collapse w1")
        ask("expand w1")
    lid = re.search(r"(a\d+) note \"wm-strip\"", door_do(a.door, a.who, "find tags=lens title=wm-strip")).group(1)
    for k in range(a.n):
        door_do(a.door, a.who, f"read {lid}")
        old, new = ("  strip : row", "  strip : column") if k % 2 == 0 else ("  strip : column", "  strip : row")
        ask("mark lens edit", wait=0.1)
        door_do(a.door, a.who, f'do replace {lid} old="{old}" new="{new}"')
        time.sleep(2.5)
    ask("stop", wait=4)
    try:
        host.wait(30)
    except subprocess.TimeoutExpired:
        host.kill()
    got = {}
    for line in wm.LOG.read_text(encoding="utf-8").splitlines():
        m = re.search(r"\d ([a-z ]+?)(?: [wx]\d+)?: windows in place in (\d+) ms", line)
        if m:
            got.setdefault(m.group(1), []).append(int(m.group(2)))
    for what, ms in got.items():
        print(f"{what:12} n={len(ms):3}  min {min(ms):4} ms  median {round(statistics.median(ms)):4} ms  max {max(ms):4} ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
