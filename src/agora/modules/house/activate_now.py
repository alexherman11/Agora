"""activate_now: switch a landed change on, detached from the House (which may be one of the things restarted).

    activate_now.py --log <file> [kd_reload args...]      e.g. --skip house, or: house

Runs src/desktop/kernel-desktop/kd_reload.py with those arguments and writes what it said to the log.
Started by builders.py (spawn_reload) after a landing; never opens a window.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

RELOAD = Path(__file__).resolve().parents[4] / "src" / "desktop" / "kernel-desktop" / "kd_reload.py"
NO_WINDOW = 0x08000000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    a, rest = ap.parse_known_args()
    python = Path(sys.executable).with_name("python.exe")
    time.sleep(2)                                   # let the House finish telling the owner first
    with open(a.log, "w", encoding="utf-8") as out:
        out.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} kd_reload {' '.join(rest)}\n")
        out.flush()
        proc = subprocess.run([str(python), "-u", str(RELOAD), *rest], stdout=out, stderr=subprocess.STDOUT,
                              creationflags=NO_WINDOW, timeout=600)
        out.write(f"\nexit {proc.returncode}\n")


if __name__ == "__main__":
    main()
