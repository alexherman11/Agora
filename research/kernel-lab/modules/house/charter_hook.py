"""Claude's SessionStart hook after a compaction: the charter, read again through the door as the agent, given back as
additional context (the old desk's charter.py --hook, on the kernel). Never acts; a failure says so and lets the
compaction go on.

    charter_hook.py --url http://127.0.0.1:8810 --token-file <file> --charter <id>
"""
import argparse
import json
import urllib.request
from pathlib import Path


def read(url, token, charter):
    req = urllib.request.Request(url.rstrip("/") + "/see", json.dumps({"line": f"look {charter}"}).encode(),
                                 {"Content-Type": "application/json", "Authorization": "Bearer " + token})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=10) as r:
        out = json.load(r)
    rows = out.get("rows") or [{}]
    return str(rows[0].get("text") or "").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--token-file", required=True)
    ap.add_argument("--charter", required=True)
    a = ap.parse_args()
    try:
        text = read(a.url, Path(a.token_file).read_text(encoding="utf-8").strip(), a.charter)
        text = ("## Alex's standing rules (read again after the compaction; look " + a.charter + " is the live one)\n\n"
                + text) if text else f"charter: not read: {a.charter} is empty; tell JEFF."
    except Exception as exc:                          # noqa: BLE001  the compaction must go on
        text = f"charter: not read after the compaction ({type(exc).__name__}); look {a.charter} reads it."
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
