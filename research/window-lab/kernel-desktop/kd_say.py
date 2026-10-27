"""kd_say: say lines to the desktop kernel as Alex's agent ("agent for Alex"), over its door, and print the receipts.

    python kd_say.py "window.open feed" "look" ...           readings go to /see, everything else to /do
    python kd_say.py --as alex "off window"                    as Alex himself (his pages' session)
    python kd_say.py --world <dir> --port <n> ...              another desktop world (a trial)
"""
import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SEE = {"help", "?", "look", "l", "rows", "holds", "status", "window.list", "window.desktop", "system.now", "media.now"}


def say(line, token, port=8810):
    route = "/see" if line.split()[0].lower() in SEE else "/do"
    req = urllib.request.Request(f"http://127.0.0.1:{port}{route}", json.dumps({"line": line}).encode(),
                                 {"Content-Type": "application/json", "Authorization": "Bearer " + token})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"ok": False, "text": f"the door said {e.code}: {e.read().decode()[:300]}"}
    except (urllib.error.URLError, OSError) as e:
        return {"ok": False, "text": f"the kernel is not answering on {port} ({e}); kdesk_on.py starts it"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lines", nargs="+")
    ap.add_argument("--as", dest="who", default="claude", choices=["claude", "alex"])
    ap.add_argument("--world", default=str(HERE / "state" / "world"))
    ap.add_argument("--port", type=int, default=8810)
    a = ap.parse_args()
    sessions = json.loads((Path(a.world) / "keep" / "sessions.json").read_text(encoding="utf-8"))
    token = next(t for t, v in sessions.items() if v.get("signer") == a.who)
    for line in a.lines:
        out = say(line, token, a.port)
        print(f"> {line}\n{out.get('text')}\n", flush=True)


if __name__ == "__main__":
    main()
