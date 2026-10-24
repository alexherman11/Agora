"""kdesk_on: start Alex's desktop on the new kernel, detached, so it outlives whatever started it.

    python kdesk_on.py            start it (nothing happens if it already answers on 8810)
    python kdesk_on.py --wait     and wait until the kernel answers, printing what runs

It is started through WMI (Win32_Process Create), outside any Claude Code session's job, as the keeper is
(memory: keeper-runs-detached): a process started any other way from a session dies with that session.
Its output goes to state/kdesk.log. kdesk_off.py stops it all and gives the screen back.
"""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PYW = HERE.parents[2] / ".venv" / "Scripts" / "pythonw.exe"
PORT = 8810


def answering(port=PORT):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as r:
            return json.loads(r.read())
    except Exception:
        return None


def start():
    if answering():
        return "already running"
    (HERE / "state").mkdir(exist_ok=True)
    log = HERE / "state" / "kdesk.log"
    # pythonw: no console window at all (a `cmd /c` start showed a black console on Alex's screen, 23 Oct 19:04);
    # kdesk writes its own log
    line = f'"{PYW}" "{HERE / "kdesk.py"}" --port {PORT} --log "{log}"'
    ps = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = '"
          + line.replace("'", "''") + f"'; CurrentDirectory = '{HERE}' }}; $r.ReturnValue; $r.ProcessId")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=60,
                         creationflags=0x08000000)
    return out.stdout.strip().replace("\n", " pid ")


def main():
    said = start()
    print(f"kdesk: {said}")
    if "--wait" in sys.argv:
        end = time.time() + 40
        while time.time() < end and not answering():
            time.sleep(0.5)
        h = answering()
        print(f"kdesk: {'answering, ' + str(h['records']) + ' records' if h else 'not answering yet; see state/kdesk.log'}")


if __name__ == "__main__":
    main()
