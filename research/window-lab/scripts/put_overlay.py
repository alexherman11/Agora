"""a6313: put the overlay version of the Rocket League timer into the live note (a6285) through the door, so the house
writes Alex's file (scripts_mirror.py keeps the old one in agora-history).

    python research/window-lab/scripts/put_overlay.py check     reads the live note, says whether it holds the version
                                                                this replaces (git HEAD~ of the lab copy), sends nothing
    python research/window-lab/scripts/put_overlay.py put       the same check, then rewrites the text and does=

Sends nothing unless the live text is exactly the version it replaces."""
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apply  # noqa: E402

NOTE, WHO = "a6285", "worker-a6313"


def door(line):
    body = json.dumps({"session": "frontier", "as": WHO, "line": line, "whole": True}).encode()
    r = urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8794/api/do", data=body, method="POST"), timeout=60)
    return json.loads(r.read()).get("text", "")


def main(argv):
    base = argv[1] if len(argv) > 1 else "main"
    old = subprocess.run(["git", "show", f"{base}:research/window-lab/scripts/RocketLeagueTimer.ps1"], capture_output=True,
                         text=True, encoding="utf-8", check=True).stdout.replace("\r\n", "\n")
    new = (HERE / "RocketLeagueTimer.ps1").read_text(encoding="utf-8").replace("\r\n", "\n")
    got = door(f"read {NOTE} :3")
    body = got.split("\n---\n", 1)[1].rsplit("\n---", 1)[0] if "\n---\n" in got else ""
    same = body.rstrip("\n") == old.rstrip("\n")
    print(f"live note {NOTE}: {len(body)} chars; holds the version this replaces: {same}")
    if not same:
        print(got[:600])
        return 1
    if argv[:1] != ["put"]:
        return 0
    for line in (f"do rewrite {NOTE} text={apply.q(new)}", f"read {NOTE}", f"do prop {NOTE} does={apply.q(apply.DOES)}"):
        said = door(line)
        print(said[:300])
        if said.startswith("ERR") or "refused" in said[:200]:
            print("stopped: the line above was refused")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
