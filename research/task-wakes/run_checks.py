"""Bounded integration/health runs; fake transports only, with retained output."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
LAB = HERE.parent / "text-desk-lab" / "notation"
sys.path.insert(0, str(HERE.parent / "window-lab"))
import agora_tmp
agora_tmp.configure()


def main():
    mode = sys.argv[1]
    if mode == "health":
        cmd = [sys.executable, str(LAB / "health.py"), "frontier-try", "--json"]
    else:
        cmd = [sys.executable, str(HERE / "pytest_integration.py"), mode]
    started = time.monotonic()
    with (HERE / (mode + ".log")).open("w", encoding="utf-8") as output:
        process = subprocess.run(cmd, cwd=HERE.parents[1], env=os.environ.copy(),
                                 stdout=output, stderr=subprocess.STDOUT, timeout=600)
    report = {"command": cmd, "exit": process.returncode,
              "seconds": round(time.monotonic() - started, 3)}
    (HERE / (mode + "-result.json")).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    print((HERE / (mode + ".log")).read_text(encoding="utf-8")[-8000:])
    raise SystemExit(process.returncode)


if __name__ == "__main__":
    main()
