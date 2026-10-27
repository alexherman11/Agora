"""install_renames: one dotted spelling for each family of words (P4, approved by Alex 27 Oct 2026).

    python install_renames.py [--port 8810] [--world <desktop world dir>] [--as claude] [--dry]

Each rename is ordinary steward words through the door: `word.rename <old> to=<new>` keeps every stored line bound
(by entry id), then the old name stays an alias, so lens gestures, buttons and habits that say the old name still
work. Help texts that name an old word are rewritten to the new name. Already renamed: left alone. Undo takes any back.
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DESKTOP_WORLD = HERE.parents[1] / "window-lab" / "kernel-desktop" / "state" / "world"
TASK = ["add", "assign", "colour", "done", "edit", "filter", "move", "note", "note-colour", "note-style", "priority",
        "remove", "rename", "text"]
RENAMES = [(f"task-{w}", f"task.{w}") for w in TASK] + [
    ("word-set", "word.set"), ("word-rename", "word.rename"), ("dictionary-copy", "word.copy"),
    ("component-action", "component.action"), ("component-health", "component.health"),
    ("file-read", "file.read"), ("file-result", "file.result"),
    ("personal-view", "personal.view"), ("personal-style", "personal.style"),
]


def say(port, token, route, line):
    req = urllib.request.Request(f"http://127.0.0.1:{port}/{route}", json.dumps({"line": line}).encode(),
                                 {"Content-Type": "application/json", "Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def quoted(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8810)
    ap.add_argument("--world", default=str(DESKTOP_WORLD))
    ap.add_argument("--as", dest="who", default="claude")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    sessions = json.loads((Path(a.world) / "keep" / "sessions.json").read_text(encoding="utf-8"))
    token = next(t for t, v in sessions.items() if v.get("signer") == a.who)
    see = lambda line: say(a.port, token, "see", line)
    do = lambda line: say(a.port, token, "do", line)

    def entry(word):
        out = see("help " + word)
        rows = [r for r in out.get("rows", []) if r.get("kind") == "word"]
        return rows[0] if rows and (word in (rows[0].get("word"), rows[0].get("bound"))
                                    or word in str(rows[0].get("aliases", "")).split()) else None

    done = []
    for old, new in RENAMES:
        e = entry(old)
        if e is None:
            print(f"skip   {old}: no such word here")
            continue
        if a.dry:
            print(f"would  {old} -> {new}" if e.get("word") != new else f"kept   {new}")
            continue
        if e.get("word") != new:
            out = do(f"word.rename {e['id']} to={new}") if entry("word.rename") else do(f"word-rename {e['id']} to={new}")
            print(("ok     " if out.get("ok") else "REFUSED ") + out.get("text", "").splitlines()[0][:150])
            if not out.get("ok"):
                continue
        if old not in str(e.get("aliases") or "").split():
            aliases = " ".join(dict.fromkeys(str(e.get("aliases") or "").split() + [old]))
            see("help " + new)
            setword = "word.set" if entry("word.set") else "word-set"      # word-set itself is renamed on the way
            out = do(f"{setword} {new} aliases={quoted(aliases)}")
            print(("ok     " if out.get("ok") else "REFUSED ") + out.get("text", "").splitlines()[0][:150])
        else:
            print(f"kept   {new} (old name {old} answers too)")
        done.append((old, new))
    if a.dry or not done:
        return
    # help texts that name an old word say the new one
    every = see("help all").get("rows", [])
    pattern = re.compile(r"(?<![\w.-])(" + "|".join(re.escape(o) for o, _ in done) + r")(?![\w-])")
    names = dict(done)
    for row in every:
        e = entry(row["word"])
        text = str((e or {}).get("help") or "")
        if not e or not pattern.search(text):
            continue
        new_text = pattern.sub(lambda m: names[m.group(1)], text)
        out = do(f"word.set {e['word']} help={quoted(new_text)}")
        print(("help   " if out.get("ok") else "REFUSED ") + e["word"] + ": " + out.get("text", "").splitlines()[0][:100])


if __name__ == "__main__":
    main()
