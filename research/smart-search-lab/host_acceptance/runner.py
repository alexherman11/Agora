"""Source-only candidate. --run requires separate House authority; never auto-admits.

No host check has been run by the author. See CONTRACT.md before invoking.
The receipt argument records external authorization; it does NOT grant authority.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    manifest = json.loads((HERE / "source-manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["sha256"].items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or digest(path) != expected:
            raise RuntimeError("source drift: " + name)
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verify-source", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--authority-record")
    ap.add_argument("--attempt")
    args = ap.parse_args()
    manifest = verify()  # stdlib only; no admission read, import or filesystem mutation
    if args.verify_source and not args.run:
        print(json.dumps({"source_verified": len(manifest["sha256"]),
                          "host_checks_executed": False, "authority": "not established"}))
        return 0
    if not args.run or not args.authority_record or not args.attempt:
        ap.error("execution held: requires --run --authority-record <House record> --attempt <fresh id>")
    if not args.attempt.startswith("search-") or not args.attempt.replace("-", "").isalnum():
        ap.error("attempt must be a fresh search-<alphanumeric> name")
    # This is an acknowledgment, not an authentication system or a grant.
    # House must authorize the named path and attempt outside this program.
    authority = args.authority_record
    tmp = os.environ.get("AGORA_TMP", "")
    if not tmp or not Path(tmp).is_absolute() or not Path(tmp).resolve().is_relative_to(ROOT):
        ap.error("House must name AGORA_TMP explicitly inside this worktree; no default/fallback")
    sys.path.insert(0, str(ROOT / "research/text-desk-lab/notation"))
    import guard_context
    observations = []

    def gate(boundary, cleanup=False):
        observation = guard_context.read()  # unchanged fixed-path consumer
        observations.append({"boundary": boundary, "value": observation})
        if not cleanup and not observation.get("admitted"):
            raise RuntimeError("admission refused at " + boundary + "; no retry")
        return observation

    gate("before sandbox import (import configures scratch)")
    sys.path.insert(0, str(ROOT / "research/window-lab"))
    import sandbox_window as sb
    from sandbox_birth import bound
    name = args.attempt
    if sb.state_file(name).exists():
        raise RuntimeError("attempt exists; no adoption or retry")
    result = {"scope": "synthetic authenticated lexical search; semantics held",
              "authority_record": authority, "attempt": name,
              "manifest_sha256": digest(HERE / "source-manifest.json"),
              "host_checks_executed": False, "result": "unproved"}
    guard = sb.Guard(name, "Apps and World text search")
    report = Path(tmp) / (name + "-source-harness.json")
    run_root = Path(tmp) / (name + "-fixture")
    if run_root.exists() or report.exists():
        raise RuntimeError("fresh path required; no reuse")
    started = False
    try:
        gate("fixture directory")
        run_root.mkdir()  # never clear/retry a path, including on PermissionError
        with guard:
            gate("job creation")
            with sb.job_scope(name) as scope:
                try:
                    gate("authenticated fixture child birth")
                    pid = sb.start(name, [str(Path(sys._base_executable).resolve()), "-B",
                                         str(HERE / "fixture.py"), str(run_root),
                                         "--sandbox-profile=" + str(run_root)], job=scope)
                    started = True
                    state = sb.load(name)
                    if (len(state["owners"]) != 1 or not bound(state, state["owners"][0])
                            or state["owners"][0]["pid"] != pid
                            or state["launches"][0].get("job_assigned") is not True):
                        raise RuntimeError("fixture birth/job binding unconfirmed")
                    result["birth"] = state
                    result["host_checks_executed"] = True
                    deadline = time.monotonic() + 90
                    evidence = run_root / "result.json"
                    while not evidence.exists() and time.monotonic() < deadline:
                        gate("bounded fixture wait")
                        snapshot = scope.snapshot()
                        if not snapshot["active"]:
                            raise RuntimeError("fixture exited without result")
                        time.sleep(.1)  # bounded polling, never waits for refused admission
                    if not evidence.exists():
                        raise RuntimeError("90 second fixture deadline; no retry")
                    result["fixture"] = json.loads(evidence.read_text(encoding="utf-8"))
                    result["job_before_off"] = scope.snapshot()
                    members = result["fixture"].get("processes", {})
                    expected = [members.get("fixture"), members.get("browser"),
                                *members.get("modules", [])]
                    if (not all(type(p) is int and p > 0 for p in expected)
                            or not members.get("modules")
                            or not set(expected).issubset(result["job_before_off"]["pids"])):
                        raise RuntimeError("fixture/browser/module job membership unconfirmed")
                finally:
                    if started:
                        # Unsafe context permits only cleanup of this live owned
                        # scope. Never cleanup/adopt anything using a saved PID.
                        gate("owned job off", cleanup=True)
                        result["cleanup"] = sb.close(name, quiet=True)
                        result["job_after_off"] = scope.snapshot()
                        if result["cleanup"].get("receipt"):
                            result["cleanup_receipt"] = json.loads(
                                Path(result["cleanup"]["receipt"]).read_text(encoding="utf-8"))
        code, verdict = guard.verdict()
        result["guard"] = {"code": code, "verdict": verdict,
                           "foreground_available": bool(guard.first.get("foreground"))}
        gate("postflight")
        closed = result.get("job_after_off", {})
        ok = (result.get("fixture", {}).get("ok") is True
              and result.get("cleanup", {}).get("ok") is True
              and closed.get("active") == 0 and closed.get("pids") == []
              and result.get("cleanup_receipt", {}).get("job_closure") == "proven empty"
              and code == 0 and result["guard"]["foreground_available"])
        result["result"] = "PASS scoped host assertions" if ok else "FAIL/UNKNOWN; no approval"
    except BaseException as exc:
        result["error"] = {"type": type(exc).__name__, "message": str(exc)}
        result["result"] = "FAIL/REFUSED; retain artifacts; no retry"
    finally:
        result["guard_observations"] = observations
        # Receipt only; no profile traversal, deletion or admission publication.
        report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(str(report))
    return 0 if result["result"] == "PASS scoped host assertions" else 1


if __name__ == "__main__":
    raise SystemExit(main())
