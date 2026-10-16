"""push: put the direction files (styles and lenses) into a world as notes in the Home base room. worker-a5534, a5534.

    python research/window-lab/directions/push.py lines <file> [<file> ...] > out.txt     desk lines for explore.py
    python research/window-lab/directions/push.py door <file> [<file> ...]               through the keeper's door

Each file becomes the note titled by its name (direction-vector.style -> "direction-vector", tagged style;
direction-vector-base.lens -> "direction-vector-base", tagged lens, style= from its first `wears <style>` comment or
the style of the same direction). An existing note of that title in the room is looked at and rewritten; else created.
"""
import json
import pathlib
import re
import sys
import urllib.request

ROOM = "f5204"


def quote(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def spec(path):
    p = pathlib.Path(path)
    text = p.read_text(encoding="utf-8").rstrip("\n")
    title, kind = p.stem, p.suffix.lstrip(".")
    style = re.sub(r"-(base|[a-z]+)$", "", title) if kind == "lens" else None
    return title, kind, text, style


def lines_for(path, existing=None):
    title, kind, text, style = spec(path)
    if existing:
        return [f"look {existing}", f"do rewrite {existing} text={quote(text)}"]
    extra = f" style={style}" if style else ""
    return [f"look {ROOM}", f"do create {ROOM} kind=note title={quote(title)} tags={kind}{extra} text={quote(text)}"]


def door(line):
    body = json.dumps({"session": "frontier", "as": "worker-a5534", "line": line, "whole": True}).encode()
    req = urllib.request.Request("http://127.0.0.1:8794/api/do", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as f:
        r = json.loads(f.read())
    return r.get("text") or r.get("error") or json.dumps(r)


def explore(lines):
    import subprocess
    lab = pathlib.Path(__file__).resolve().parents[3] / "research" / "text-desk-lab" / "notation"
    r = subprocess.run([sys.executable, str(lab / "explore.py"), "frontier-try", "--as", "worker-a5534", "--whole"],
                       input="\n".join(lines) + "\n", capture_output=True, text=True, encoding="utf-8", cwd=lab)
    return r.stdout + r.stderr


def in_room(text):
    """title -> id of the notes listed by `look <room> :2`."""
    return {m.group(2): m.group(1) for m in re.finditer(r'^\s+(a\d+) note "([^"]+)"', text, re.M)}


def main():
    how, files = sys.argv[1], sys.argv[2:]
    if how == "try":     # the try world: the house re-copies it after every landing, so look before each push
        for f in files:
            have = in_room(explore([f"look {ROOM} :2"]))
            out = explore(lines_for(f, have.get(pathlib.Path(f).stem)))
            print("\n".join(l for l in out.splitlines() if re.match(r"^(ok |~|ERR|  -|.*refus)", l))[:2000])
        return
    ids = {}
    for f in files:
        if "=" in f:       # title=id: rewrite that note
            t, i = f.split("=", 1)
            ids[t] = i
    files = [f for f in files if "=" not in f]
    for f in files:
        ls = lines_for(f, ids.get(pathlib.Path(f).stem))
        if how == "lines":
            sys.stdout.buffer.write(("\n".join(ls) + "\n").encode("utf-8"))
        else:
            for l in ls:
                out = door(l)
                print(out[:1500])


if __name__ == "__main__":
    main()
