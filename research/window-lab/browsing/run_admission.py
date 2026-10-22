"""OFFLINE retained-Job fixture. Not authorized to launch by source readiness.

No legacy process query/adoption, taskkill, public page or privileged web bridge.
Native execution requires a separately admitted guarded lane and lead approval.
"""
import hashlib
import sys
import uuid
from pathlib import Path

from admission_job import run, write
from admission_result import message_boundary_passed

HERE = Path(__file__).resolve().parent


def main():
    # Lazy imports keep offline tests free from import-time Windows API calls.
    sys.path.insert(0, str(HERE.parent))
    sys.path.insert(0, str(HERE.parents[1] / "text-desk-lab" / "notation"))
    import sandbox_window as sandbox
    import guard_context
    from hud_lifecycle import Windows

    if guard_context.read().get("admitted") is not True:
        raise RuntimeError("fresh world-owned guard admission required; no launch")
    sandbox.STATE.mkdir(parents=True, exist_ok=True)  # same setup as shared open()
    name = "admit-" + uuid.uuid4().hex[:12]
    token = uuid.uuid4().hex
    folder = Path(sandbox.agora_tmp.directory(name + "-"))
    sources = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
               for p in (Path(__file__), HERE / "admission_probe.py",
                         HERE / "admission_result.py", HERE / "admission_job.py",
                         HERE / "admission_policy.py")}
    write(folder / "source.json", sources)
    result = run(
        sandbox, guard_context.read, Windows(), name, folder,
        [sys.executable, str(HERE / "admission_probe.py"), str(folder),
         "agora-sandbox-" + name, token], token)
    passed = (result.get("phase") == "child_exit"
              and result.get("engine_admitted") is True
              and result.get("job_closure") == "proven empty"
              and result.get("guard_code") == 0
              and message_boundary_passed(result.get("child", {})))
    result["offline_message_boundary_passed"] = passed
    result["native_adversarial_containment"] = "not certified by this message fixture"
    write(folder / "launch.json", result)
    print("receipt_directory:", folder)
    print("offline_message_boundary_passed:", passed)
    print("job_closure:", result["job_closure"])
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
