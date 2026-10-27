"""Ask relay: right-click asks reach the Conversation, and lines to Claude wake Claude (26 Oct 2026, Alex's ask).

    python ask_relay.py relay          forever: each open ask-request in the kernel desk (8810) becomes Alex's own
                                       line in the Conversation (a5080, on the desk's door 8794), addressed to Claude,
                                       with where he asked and what about; the request is marked sent.
    python ask_relay.py wait [--since N]   block until a new Conversation line addressed to Claude arrives (by Alex),
                                       print it and exit. A Claude Code session runs this in the background, so a
                                       message to Claude wakes it.

Alex's words are relayed unchanged; the line says it came from a right-click (via=right-click), so nobody mistakes
it for something he typed in the chat. The relay holds no state of its own except the last line it has seen
(state/ask-relay.json); the requests' status lives in the kernel world.
"""
import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE = HERE / "state"
KEEP = HERE.parents[0] / "kernel-desktop" / "state" / "world" / "keep" / "sessions.json"
DESK = "http://127.0.0.1:8794/api/do"
KERNEL = "http://127.0.0.1:8810"
CHAT = "a5080"


def desk(line, who="claude"):
    req = urllib.request.Request(DESK, json.dumps({"session": "frontier", "as": who, "line": line}).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    if out.get("error"):
        raise RuntimeError(out["error"])
    return out.get("text", "")


def kernel(route, line):
    token = next(t for t, v in json.loads(KEEP.read_text(encoding="utf-8")).items() if v.get("agent") == "claude")
    req = urllib.request.Request(f"{KERNEL}/{route}", json.dumps({"line": line}).encode(),
                                 {"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b"{}")


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def thing_name(tid):
    """A readable name for what was right-clicked, from the kernel's own reading."""
    if not tid or tid == "-":
        return ""
    out = kernel("see", "look " + tid)
    text = (out.get("text") or "").strip().splitlines()
    first = text[0] if text else ""
    return first[:120] if not first.startswith("refused") else ""


def relay_once():
    out = kernel("see", "rows ask-request status=open")
    sent = 0
    for r in out.get("rows", []):
        name = thing_name(r.get("about"))
        where = r.get("where", "")
        line = r.get("text", "").strip()
        if not line:
            continue
        context = f"{where} — {name}" if name else where
        desk(f"do append {CHAT} line={q(line)} to=claude via=right-click asked_at={q(context)} thing={q(r.get('about', ''))}",
             who="alex")
        kernel("do", f"set {r['id']} status=sent")
        sent += 1
    return sent


def lines_to_claude(since):
    text = desk(f"rows lines:{CHAT}")
    found = []
    for raw in text.splitlines():
        m = re.search(r"line=(m\d+).*? by=(\S+) .*? to=(\S*) .*?seq=(\d+)", raw)
        if not m:
            continue
        mid, by, to, seq = m[1], m[2], m[3], int(m[4])
        if seq > since and by == "alex" and "claude" in to.split(","):
            found.append((seq, mid, raw.strip()))
    return found


def last_seq():
    seqs = [int(s) for s in re.findall(r"seq=(\d+)", desk(f"rows lines:{CHAT}"))]
    return max(seqs) if seqs else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["relay", "wait"])
    ap.add_argument("--since", type=int, help="wait: only lines after this seq (default: the saved marker, else now)")
    ap.add_argument("--every", type=float, default=2.0)
    a = ap.parse_args()
    STATE.mkdir(exist_ok=True)
    if a.mode == "relay":
        while True:
            try:
                n = relay_once()
                if n:
                    print(f"relayed {n}", flush=True)
            except Exception as e:                       # a desk restarting is ordinary; try again next tick
                print("relay: " + str(e)[:200], file=sys.stderr, flush=True)
            time.sleep(a.every)
    marker = STATE / "ask-relay.json"
    since = a.since
    if since is None:
        since = json.loads(marker.read_text())["seen"] if marker.exists() else last_seq()
    while True:
        try:
            found = lines_to_claude(since)
        except Exception as e:
            print("wait: " + str(e)[:200], file=sys.stderr, flush=True)
            found = []
        if found:
            seen = max(f[0] for f in found)
            marker.write_text(json.dumps({"seen": seen}))
            for seq, mid, raw in found:
                print(f"NEW {mid} seq={seq}\n{desk('examine ' + mid)[:3000]}\n")
            return
        time.sleep(a.every)


if __name__ == "__main__":
    main()
