"""check_roles: does each direction style define every role the live home-style does? (a5534, worker-a5534)

    python src/desktop/directions/check_roles.py

Reads home-style (a5206) from the live world through the keeper's door (a read, signed worker-a5534) and the
direction-*.style files here. A role missing from a direction paints unstyled when that direction is worn.
"""
import json
import pathlib
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent


def roles(text):
    return {l.split()[1] for l in text.splitlines() if l.startswith("role ") and len(l.split()) > 1}


def main():
    body = json.dumps({"session": "frontier", "as": "worker-a5534", "line": "read a5206", "whole": True}).encode()
    req = urllib.request.Request("http://127.0.0.1:8794/api/do", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as f:
        text = json.loads(f.read()).get("text", "")
    home = roles(text.split("---", 1)[-1])
    print(f"home-style: {len(home)} roles")
    for p in sorted(HERE.glob("direction-*.style")):
        mine = roles(p.read_text(encoding="utf-8"))
        miss = sorted(home - mine)
        print(f"{p.stem}: {len(mine)} roles; missing {len(miss)}" + (": " + " ".join(miss) if miss else ""))


if __name__ == "__main__":
    main()
