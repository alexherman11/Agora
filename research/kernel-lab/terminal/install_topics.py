"""install_topics: make the help topics in topics.lines in a running world, each only if no topic of that name exists.

    python install_topics.py [--port 8810] [--world <desktop world dir>] [--as claude] [--dry]

Ordinary undoable words through the door, as Alex's agent; the world's own edits always win (a topic that exists is
left alone). Prints one receipt per topic made.
"""
import argparse
import json
import re
import shlex
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DESKTOP_WORLD = HERE.parents[1] / "window-lab" / "kernel-desktop" / "state" / "world"


def say(port, token, route, line):
    req = urllib.request.Request(f"http://127.0.0.1:{port}/{route}", json.dumps({"line": line}).encode(),
                                 {"Content-Type": "application/json", "Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8810)
    ap.add_argument("--world", default=str(DESKTOP_WORLD))
    ap.add_argument("--as", dest="who", default="claude")
    ap.add_argument("--file", default=str(HERE / "topics.lines"))
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--always", action="store_true", help="say every line (help fixes), looking first at what it edits")
    ap.add_argument("--refresh", action="store_true", help="rewrite a page nobody but its maker has changed since")
    a = ap.parse_args()
    sessions = json.loads((Path(a.world) / "keep" / "sessions.json").read_text(encoding="utf-8"))
    token = next(t for t, v in sessions.items() if v.get("signer") == a.who)
    have = say(a.port, token, "see", "rows topic")
    names = {str(r.get("name", "")).casefold() for r in have.get("rows", [])}
    for line in Path(a.file).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if a.always:
            word, target = (shlex.split(line) + ["", ""])[:2]
            if a.dry:
                print(f"would say {line[:90]}")
                continue
            say(a.port, token, "see", ("help " if word in ("word-set", "word.set") else "look ") + target)   # the look an edit needs
            out = say(a.port, token, "do", line)
            print(("ok     " if out.get("ok") else "REFUSED ") + out.get("text", "").splitlines()[0][:160])
            continue
        fields = dict(t.split("=", 1) for t in shlex.split(line) if "=" in t)
        name = fields.get("name", "")
        if name.casefold() in names:
            row = next(r for r in have.get("rows", []) if str(r.get("name", "")).casefold() == name.casefold())
            if not a.refresh:
                print(f"kept   {name} (already in the world)")
                continue
            trail = say(a.port, token, "see", f"history {row['id']}").get("rows", [])
            others = {r.get("by") for r in trail} - {trail[0].get("by")} if trail else set()
            if others:
                print(f"kept   {name}: changed by {', '.join(sorted(others))} since; their words stay")
                continue
            new = {f: v for f, v in fields.items() if f in ("title", "aliases", "words", "text", "order")
                   and str(row.get(f, "")) != v}
            if not new:
                print(f"same   {name}")
                continue
            sets = " ".join(f"{f}={json.dumps(v, ensure_ascii=False)}" for f, v in new.items())
            out = say(a.port, token, "do", f"set {row['id']} {sets}")
            print(("fresh  " if out.get("ok") else "REFUSED ") + f"{name}: {out.get('text', '').splitlines()[0][:120]}")
            continue
        if a.dry:
            print(f"would make {name}")
            continue
        out = say(a.port, token, "do", line)
        print(("made   " if out.get("ok") else "REFUSED ") + f"{name}: {out.get('text', '').splitlines()[0]}")


if __name__ == "__main__":
    main()
