"""Start or reuse the combined Desk and open its authenticated human surface."""

from pathlib import Path
import json
import os
import subprocess
import sys
import time
import urllib.request
import uuid
import webbrowser


ROOT = Path(__file__).resolve().parent
PORT = json.loads((ROOT / "desk.json").read_text())["port"]


def live():
    try:
        keep = json.loads((ROOT / "world/keep.json").read_text())
        request = urllib.request.Request(
            f"http://127.0.0.1:{PORT}/api/rpc",
            data=json.dumps({"method": "package.catalog", "args": {}}).encode(),
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + keep["operator"]},
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            result = json.load(response).get("result", {})
            return bool(result.get("packages")) and result.get("source_included") is False
    except (OSError, ValueError, KeyError):
        return False


def main():
    if not live():
        launch_id = uuid.uuid4().hex
        log = (ROOT / "logs/service.log").open("a", encoding="utf-8", buffering=1)
        process = subprocess.Popen(
            [sys.executable, str(ROOT / "serve_desk.py")], cwd=ROOT,
            env=dict(os.environ, PYTHONUTF8="1", AGORA_DESK_LAUNCH_ID=launch_id),
            stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        deadline = time.monotonic() + 110
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise SystemExit("The Desk service exited. See logs/service.log.")
            if live() and (ROOT / "ready.json").exists():
                ready = json.loads((ROOT / "ready.json").read_text())
                if ready.get("launch_id") == launch_id:
                    break
            time.sleep(.3)
        else:
            raise SystemExit("Desk startup has not completed. See logs/service.log.")
    opened = False
    if "--no-open" not in sys.argv:
        keep = json.loads((ROOT / "world/keep.json").read_text())
        opened = webbrowser.open(f"http://127.0.0.1:{PORT}/#" + keep["operator"])
        if not opened:
            raise SystemExit("The Desk is ready, but the default browser could not be opened.")
    print(json.dumps({"ready": True, "port": PORT, "browser_opened": opened,
                      "model_turn_started": False}))


if __name__ == "__main__":
    main()
