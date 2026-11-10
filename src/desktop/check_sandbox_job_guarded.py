"""Explicit ONE guarded fake family, no browser/network/UI/input or legacy adoption.

Run only under a card authorizing this attempt. Refusal is final, not a retry
loop. Enrolled-job closure is distinct from externally delegated engine closure.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import uuid

import sandbox_window as sb
from sandbox_birth import bound
from sandbox_receipts import error, write
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "text-desk/notation"))
import guard_context


def main():
    name = "job-a9868-" + uuid.uuid4().hex[:10]
    os.makedirs(sb.STATE, exist_ok=True)
    report = sb.STATE / (name + "-check.json")
    data = {"scope": "one fake enrolled child/grandchild; no native engine",
            "browser_or_mail_launched": False, "child_started": False,
            "runtime_closure": "unknown: external delegation not certified"}
    data["source_sha256"] = {p: hashlib.sha256((sb.HERE / p).read_bytes()).hexdigest()
                             for p in ("sandbox_job.py", "sandbox_window.py", "sandbox_birth.py",
                                       "sandbox_receipts.py", "check_sandbox_job_guarded.py")}
    data["house_preflight"] = guard_context.read()
    if not data["house_preflight"]["admitted"]:
        data["result"] = "refused before job/desktop/child creation; no retry"
        write(report, data)
        print(str(report))
        print(json.dumps(data, indent=2))
        return 2
    profile = sb.STATE / (name + "-fake-profile")
    profile.mkdir()
    ready = profile / "ready.json"
    # No shell, UI, handles inherited from harness, network or private data.
    # sys._base_executable avoids a venv shim spawning an unmeasured root.
    executable = str(Path(sys._base_executable).resolve())
    child = (
        "import json,os,pathlib,subprocess,sys,time\n"
        "p=subprocess.Popen([sys.executable,'-I','-S','-c',"
        "'import time; time.sleep(20)'],close_fds=True,creationflags=0x08000000)\n"
        "ready=pathlib.Path(sys.argv[1]); tmp=ready.with_suffix('.pending')\n"
        "tmp.write_text(json.dumps({'child':os.getpid(),'grandchild':p.pid}),encoding='utf-8')\n"
        "tmp.replace(ready)\n"
        "time.sleep(20)\n"
    )
    guard = sb.Guard(name, name)
    try:
        with guard:
            # Recheck immediately before creating even the empty Job Object.
            data["house_before_effect"] = guard_context.read()
            if not data["house_before_effect"]["admitted"]:
                raise RuntimeError("house context changed/expired; no retry")
            with sb.job_scope(name) as scope:
                data["job"] = dict(scope.descriptor)
                try:
                    pid = sb.start(name, [executable, "-I", "-S", "-c", child, str(ready),
                                          "--sandbox-profile=" + str(profile)], job=scope)
                    data.update(child_started=True, pid=pid)
                    st = sb.load(name)
                    data["birth_manifest"] = st
                    data["manifest_complete"] = (len(st["owners"]) == 1
                        and bound(st, st["owners"][0]) and st["launches"][0]["job_assigned"] is True
                        and st["launches"][0]["status"] == "running")
                    deadline = time.monotonic() + 4
                    while not ready.exists() and time.monotonic() < deadline:
                        time.sleep(0.02)
                    members = json.loads(ready.read_text(encoding="utf-8"))
                    data["fixture_members"] = members
                    snapshot = scope.snapshot()
                    data["job_before_cleanup"] = snapshot
                    data["grandchild_proven_in_job"] = (members["child"] == pid
                        and members["grandchild"] != pid
                        and {pid, members["grandchild"]}.issubset(snapshot["pids"])
                        and snapshot["active"] >= 2)
                    if not data["grandchild_proven_in_job"]:
                        raise RuntimeError("fixture grandchild job membership unconfirmed")
                finally:
                    if sb.state_file(name).exists():
                        # One explicit cleanup of this live scope only. No
                        # replay, external cleanup helper or outside-job kill.
                        data["cleanup"] = sb.close(name, quiet=True)
                        path = Path(data["cleanup"].get("receipt", sb.state_file(name)))
                        data["cleanup_manifest"] = json.loads(path.read_text(encoding="utf-8"))
                        data["receipt_path"] = str(path)
                    data["job_final"] = scope.snapshot()
    except BaseException as exc:
        data["error"] = error(exc)
        data["result"] = "failed or refused; no retry; last-handle close is not proof"
    finally:
        if hasattr(guard, "first"):
            code, words = guard.verdict()
            data["guard"] = {"code": code, "verdict": words}
            if not guard.first.get("foreground"):
                data["guard"]["verdict"] = ("unknown Alex-screen continuity: local foreground unavailable; "
                                           "house snapshots are bounded admission only")
        else:
            data["guard"] = {"code": 1, "verdict": "guard not started"}
        data["house_postflight"] = guard_context.read()
        ok = (not data.get("error") and data.get("manifest_complete")
              and data.get("grandchild_proven_in_job") and data.get("cleanup", {}).get("ok")
              and data.get("cleanup_manifest", {}).get("job_closure") == "proven empty"
              and data.get("job_final", {}).get("pids") == []
              and data.get("job_final", {}).get("active") == 0
              and data["guard"]["code"] == 0 and data["house_postflight"]["admitted"])
        if ok:
            data["result"] = "PASS: enrolled fake job confirmed empty; engine delegation unverified"
        write(report, data)
    print(str(report))
    print(json.dumps(data, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
