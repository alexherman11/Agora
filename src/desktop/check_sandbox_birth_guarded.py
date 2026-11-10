"""ONE fake direct-child run. No browser, network, screen capture, input or adoption.

Explicit invocation only. Unknown/refused cleanup keeps all state. This is NOT
browser descendant containment or permission to resume retained browser/mail runs.
"""
import json
import os
from pathlib import Path
import sys
import uuid
from ctypes import byref, wintypes

import sandbox_window as sb
from sandbox_receipts import error, write
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "text-desk/notation"))
import guard_context


def main():
    name = "birth-a9388-" + uuid.uuid4().hex[:10]
    os.makedirs(sb.STATE, exist_ok=True)
    report = sb.STATE / (name + "-check.json")
    data = {"scope": "one fake direct child", "browser_launched": False,
            "runtime_closure": "unknown", "child_started": False}
    # The worker's observation is diagnostic only: HWND=0 cannot certify Alex's
    # context. Admission comes from the fixed house-owned observation path.
    state = wintypes.DWORD()
    query = sb.ctypes.windll.shell32.SHQueryUserNotificationState(byref(state))
    desktop = sb.alex()["input desktop"]
    data["preflight"] = {"notification_result": int(query), "notification_state": state.value,
                         "input_desktop": desktop}
    data["house_preflight"] = guard_context.read()
    if not data["house_preflight"]["admitted"]:
        data["result"] = "refused: fresh safe house context unavailable"
        write(report, data)
        print(json.dumps(data))
        return 2
    # The base interpreter avoids the venv launcher delegating a second process.
    executable = str(Path(sys._base_executable).resolve())
    profile = sb.STATE / (name + "-fake-profile")
    profile.mkdir()
    guard = sb.Guard(name, name)
    try:
        with guard:
            # Revalidate immediately before the effect; no waiting for admission.
            if not guard_context.read()["admitted"]:
                raise RuntimeError("house context changed/expired before child creation")
            pid = sb.start(name, [executable, "-I", "-S", "-c",
                                 "import time; time.sleep(5)",
                                 "--sandbox-profile=" + str(profile)])
            data["child_started"] = True
            data["pid"] = pid
            st = sb.load(name)
            from sandbox_birth import valid
            data["manifest_complete"] = (len(st["owners"]) == 1 and valid(st["owners"][0])
                                         and st["launches"][0]["status"] == "running")
            # Ordinary close verifies just recorded owners. It deliberately
            # returns unknown for unregistered descendants, even with no windows.
            data["cleanup"] = sb.close(name, quiet=True)
            st = sb.load(name)
            data["cleanup_attempts"] = st.get("cleanup", [])
            data["cleanup_complete"] = st.get("cleanup_complete", False)
            data["runtime_closure"] = st.get("runtime_closure", "unknown")
    except BaseException as exc:
        data["error"] = error(exc)
        data["result"] = "failed; no retry or unverified cleanup"
    finally:
        if hasattr(guard, "first"):
            code, words = guard.verdict()
            data["guard"] = {"code": code, "verdict": words}
            if not guard.first.get("foreground"):
                data["guard"]["visibility"] = "worker foreground unavailable; local verdict is not Alex-screen proof"
                data["guard"]["verdict"] = (
                    "unknown Alex-screen continuity: worker foreground unavailable; "
                    "house snapshots provide bounded admission only")
        else:
            data["guard"] = {"code": 1, "verdict": "guard never started"}
        data["house_postflight"] = guard_context.read()
        write(report, data)
    print(str(report))
    print(json.dumps(data, indent=2))
    return 0 if (data.get("manifest_complete") and data.get("guard", {}).get("code") == 0
                 and data.get("house_postflight", {}).get("admitted")
                 and any(x.get("status") in ("ended", "gone") for x in data.get("cleanup_attempts", []))) else 1


if __name__ == "__main__":
    raise SystemExit(main())
