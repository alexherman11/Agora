"""notebook_add.py (a7784): append one entry at the end of a section of the live builders' notebook, through the door,
after reading the whole note (the desk's fence). Prints what it did.

    python src/desktop/combined-review/notebook_add.py "<section heading>" "<entry>"
"""
import json
import sys
import urllib.request

WHO = "worker-a7784"


def door(line):
    body = json.dumps({"session": "frontier", "as": WHO, "line": line, "whole": True}).encode()
    req = urllib.request.Request("http://127.0.0.1:8794/api/do", body, {"Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(req, timeout=60).read())
    return (("ERR " + out["error"] + "\n") if out.get("error") else "") + (out.get("text") or "")


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def main():
    section, entry = sys.argv[1], sys.argv[2]
    nid = next(l.split()[0] for l in door("find role=builders-notebook").splitlines() if "Builders' notebook" in l)
    text = door(f"read {nid} :3")
    sec = door(f"read {nid} #{section}")
    last = [l for l in sec.splitlines() if l.startswith("- ")][-1]
    if text.count(last) != 1:
        raise SystemExit(f"the section's last line is not unique in the note: {last[:80]}")
    print(door(f"do replace {nid} old={q(last)} new={q(last + chr(10) + entry)}").splitlines()[0][:200])


if __name__ == "__main__":
    main()
