"""restart_house: turn the House off and on again from outside it (house.restart house).

    python restart_house.py --url http://127.0.0.1:8810 --token-file <file> [--delay 5]

The House cannot restart itself: `off house` ends its process, so its own `on house` would never be said. house.restart
starts this detached (outside the House's process tree), with the asking steward's token in a file; it waits a few
seconds so the asker's turn can end, says `off house`, waits for the House to stop, then says `on house`.
"""
import argparse
import json
import time
import urllib.request
from pathlib import Path


def say(url, token, line):
    req = urllib.request.Request(url + "/do", json.dumps({"line": line}).encode("utf-8"),
                                 {"Content-Type": "application/json", "Authorization": "Bearer " + token})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=30) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--token-file", required=True)
    ap.add_argument("--delay", type=float, default=5)
    a = ap.parse_args()
    token_file = Path(a.token_file)
    token = token_file.read_text(encoding="utf-8").strip()
    try:
        token_file.unlink()                       # the token is only needed for these two lines
    except OSError:
        pass
    time.sleep(a.delay)
    print(say(a.url, token, "off house").get("text"), flush=True)     # answers once its process has stopped
    time.sleep(3)
    print(say(a.url, token, "on house").get("text"), flush=True)


if __name__ == "__main__":
    main()
