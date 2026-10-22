"""One fresh, offline admission run; observes graceful exit, never taskkills.

Run with the pinned interpreter. A timeout leaves an honest receipt for review.
"""

import ctypes
import hashlib
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path

from admission_result import message_boundary_passed

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import sandbox_window as sandbox  # noqa: E402


def main():
    processes = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "$ErrorActionPreference='Stop'; @(Get-CimInstance Win32_Process | "
            "Where-Object {$_.Name -match "
            "'^(RocketLeague|FortniteClient.*|cs2|valorant.*|dota2)\\.exe$'}).Count",
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    if processes.stdout.strip() != "0" or sandbox.alex()["input desktop"] != "Default":
        raise RuntimeError("active/unlocked/no-game precondition not established")
    name = "admit-" + uuid.uuid4().hex[:12]
    folder = Path(sandbox.agora_tmp.directory(name + "-"))
    manifest = {
        "desktop": "agora-sandbox-" + name,
        "profile": str(folder / "profile"),
        "started_at": time.time(),
        "public_navigation": False,
        "source_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__), HERE / "admission_probe.py", HERE / "admission_result.py")
        },
    }
    kernel = ctypes.windll.kernel32
    kernel.OpenProcess.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_uint]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    with sandbox.Guard(name, "Agora offline admission probe") as guard:
        pid = sandbox.start(
            name,
            [sys.executable, str(HERE / "admission_probe.py"), str(folder), manifest["desktop"]],
        )
        manifest["pid"] = pid
        (folder / "launch.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        handle = kernel.OpenProcess(0x100000, False, pid)
        if not handle:
            manifest["wait"] = "unknown: no process handle"
        else:
            try:
                manifest["wait"] = int(kernel.WaitForSingleObject(handle, 40000))
            finally:
                kernel.CloseHandle(handle)
        time.sleep(2)
        manifest["remaining_windows"] = sandbox.top_windows_quiet(name)
    code, verdict = guard.verdict()
    manifest["guard_code"], manifest["guard"] = code, verdict
    (folder / "launch.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("receipt_directory:", folder)
    print(json.dumps(manifest, indent=2))
    receipt = folder / "receipt.json"
    passed = False
    if receipt.exists():
        print(receipt.read_text(encoding="utf-8"))
        passed = message_boundary_passed(json.loads(receipt.read_text(encoding="utf-8")))
    print("offline_message_boundary_passed:", passed)
    # Process inventory is read-only. Never adopt or terminate a PID from this query.
    query = (
        "$ErrorActionPreference='Stop'; @(Get-CimInstance Win32_Process | "
        "Where-Object {$_.Name -notmatch 'powershell|pwsh' -and $_.CommandLine -like '*"
        + name
        + "*'}).Count"
    )
    check = subprocess.run(
        ["powershell", "-NoProfile", "-Command", query],
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    manifest["matching_processes_after_exit"] = int(check.stdout.strip())
    manifest["offline_message_boundary_passed"] = passed
    (folder / "launch.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("matching_processes_after_exit:", manifest["matching_processes_after_exit"])
    clean = (
        manifest["wait"] == 0
        and not manifest["remaining_windows"]
        and manifest["matching_processes_after_exit"] == 0
    )
    return code or (0 if passed and clean else 2)


if __name__ == "__main__":
    raise SystemExit(main())
