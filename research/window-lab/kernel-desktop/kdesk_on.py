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
    sys.path.insert(0, str(HERE))
    from kdesk_keeper import ask
    if answering() or ask("status"):
        return "already running"
    (HERE / "state").mkdir(exist_ok=True)
    log = HERE / "state" / "kdesk.log"
    # pythonw: no console window at all (a `cmd /c` start showed a black console on Alex's screen, 23 Oct 19:04);
    # kdesk writes its own log
    once = "--resident-manifest" in sys.argv or "--manager-manifest" in sys.argv
    if once:
        # a manifest installs once: that start runs the kernel directly, as before, not under a keeper that would
        # pass it to every restart
        line = f'"{PYW}" "{HERE / "kdesk.py"}" --port {PORT} --log "{log}"'
    else:
        # 28 Oct: the keeper holds the ports and modules; the kernel is its child and restarts alone (kd_reload)
        line = (f'"{PYW}" "{HERE / "kdesk_keeper.py"}" --port {PORT} --log "{HERE / "state" / "keeper.log"}"'
                f' --kernel-log "{log}"')
    if "--resident-manifest" in sys.argv:          # a reviewed resident move, this start only (agents/SABLE-MOVE.md)
        line += f' --resident-manifest "{Path(sys.argv[sys.argv.index("--resident-manifest") + 1]).resolve()}"'
    if "--manager-manifest" in sys.argv:           # approved fresh manager, distinct from resident migration
        line += f' --manager-manifest "{Path(sys.argv[sys.argv.index("--manager-manifest") + 1]).resolve()}"'
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
