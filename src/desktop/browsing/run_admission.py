"""OFFLINE retained-Job fixture. Not authorized to launch by source readiness.

No legacy process query/adoption, taskkill, public page or privileged web bridge.
Native execution requires a separately admitted guarded lane and lead approval.
"""
import hashlib
import json
import sys
import uuid
from pathlib import Path

from admission_job import guard_details, require_guard, run, write
from admission_result import message_boundary_passed

HERE = Path(__file__).resolve().parent
# Intentionally empty: no installed interpreter identity has been admitted.
# No environment variable, child receipt or automatic discovery fills this.
REVIEWED_HOST_IMAGES = {}


def main():
    # Lazy imports keep offline tests free from import-time Windows API calls.
    sys.path.insert(0, str(HERE.parent))
    sys.path.insert(0, str(HERE.parents[1] / "text-desk" / "notation"))
    import guard_context
    if sys.argv[1:] == ["--guard-status"]:
        print(json.dumps(guard_details(guard_context.read()), sort_keys=True))
        return 0
    if sys.argv[1:]:
        raise ValueError("supported option: --guard-status (read-only)")
    require_guard(guard_context.read)
    if not REVIEWED_HOST_IMAGES:
        print("refused: effective interpreter identity awaits review; no native initialization")
        return 2
    import native_run_verify
    import sandbox_window as sandbox
    from hud_lifecycle import Windows

    sandbox.STATE.mkdir(parents=True, exist_ok=True)  # same setup as shared open()
    name = "admit-" + uuid.uuid4().hex[:12]
    token = uuid.uuid4().hex
    folder = Path(sandbox.agora_tmp.directory(name + "-"))
    sources = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
               for p in (Path(__file__), HERE / "admission_probe.py",
                         HERE / "admission_result.py", HERE / "admission_job.py",
                         HERE / "admission_policy.py", HERE.parent / "native_run_verify.py",
                         HERE.parent / "sandbox_job.py", HERE.parent / "sandbox_window.py",
                         HERE.parent / "sandbox_birth.py")}
    write(folder / "source.json", sources)
    def verifier(scope):
        return native_run_verify.Verifier(
            {"name": name, "profile_roots": [str(folder / "profile")],
             "scratch_roots": [str(folder)], "watched_roots": [str(HERE)],
             "exclude": [str(HERE / "__pycache__")],
             "allow_remote": [], "allow_loopback": False,
             "require_engine_report": True,
             # Rowan c10545 / JEFF e26277: ONE local observation only.
             # Brokered processes and unscanned writes remain NOT PROVEN in
             # the report, explicitly accepted limits for this fixture alone.
             # This is never public-web containment acceptance.
             "must_prove": []},
            scope)
    process_reader = native_run_verify.Native()
    result = run(
        sandbox, guard_context.read, Windows(), name, folder,
        [sys.executable, str(HERE / "admission_probe.py"), str(folder),
         "agora-sandbox-" + name, token], token, verifier_factory=verifier,
        host_images=REVIEWED_HOST_IMAGES, processes=process_reader.processes)
    passed = (result.get("phase") == "child_exit"
              and result.get("engine_admitted") is True
              and result.get("job_closure") == "proven empty"
              and result.get("guard_code") == 0
              and result.get("native_verification", {}).get("allow_interaction") is True
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
