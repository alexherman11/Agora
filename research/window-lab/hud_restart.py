"""hud_restart.py: stop the running home base and start this checkout's hud.py again, detached, so it outlives the
terminal or agent that started it (a5736).

    python hud_restart.py [--show] [--debug-port N]

--show          it opens shown (over the whole screen) instead of waiting for Ctrl+Alt+J
--debug-port N  WebView2 opens a DevTools port on 127.0.0.1:N, for hud_measure.py. Any program on this PC can drive the
                page through it: restart again without it when done.
Its output goes to state/hud.out. Off switch: python hud.py --stop.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    a = sys.argv[1:]
    py = getattr(sys, "_base_executable", sys.executable)
    subprocess.run([py, str(HERE / "hud.py"), "--stop"], cwd=HERE)
    env = dict(os.environ)
    env.pop("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS", None)
    if "--debug-port" in a:
        env["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = f"--remote-debugging-port={int(a[a.index('--debug-port') + 1])}"
    args = [py, str(HERE / "hud.py")] + (["--show"] if "--show" in a else [])
    (HERE / "state").mkdir(exist_ok=True)
    out = open(HERE / "state" / "hud.out", "ab")
    # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_BREAKAWAY_FROM_JOB: not ended with whoever started it
    flags = 0x8 | 0x200 | 0x01000000
    try:
        p = subprocess.Popen(args, cwd=HERE, env=env, stdout=out, stderr=out, stdin=subprocess.DEVNULL, creationflags=flags)
    except OSError:          # a job that forbids breaking away
        p = subprocess.Popen(args, cwd=HERE, env=env, stdout=out, stderr=out, stdin=subprocess.DEVNULL,
                             creationflags=0x8 | 0x200)
    time.sleep(4)
    print("hud_restart: started", p.pid, "running" if p.poll() is None else f"exited {p.returncode}")


if __name__ == "__main__":
    main()
