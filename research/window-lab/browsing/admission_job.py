"""Parent-held Job lifetime for the OFFLINE admission fixture.

The file exchange below coordinates trusted fixture code. It is not an
authenticated host service or a grant to workers. JSON never establishes
ownership: the parent checks a held kernel process handle against its live Job.
No legacy discovery, job adoption, PID termination or external-runtime cleanup.
"""
import json
import ntpath
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sandbox_receipts import write, error


class Refused(RuntimeError):
    """Only fixed fixture reasons, never native exception text."""
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def read(path):
    with Path(path).open("rb") as stream:
        data = stream.read(65537)
    if len(data) > 65536:
        raise ValueError("oversized fixture receipt")
    return json.loads(data)


class EngineFence:
    """Pins an engine birth to the parent's retained Job until cleanup."""
    def __init__(self, scope, native, root, token):
        self.scope, self.native, self.root, self.token = scope, native, root, token
        self.engine = None
        self.handle = None
        self.birth = None

    def check(self, request):
        if (request.get("request") != self.token
                or request.get("host_pid") != self.root["pid"]
                or type(request.get("engine_pid")) is not int
                or request["engine_pid"] <= 0):
            raise Refused("fixture identity mismatch")
        pid = request["engine_pid"]
        if self.engine is not None and self.engine != pid:
            raise Refused("engine changed; no reuse or automatic retry")
        if self.handle is None:
            self.handle = self.native.k.OpenProcess(0x1000 | 0x100000, False, pid)
            if not self.handle:
                raise Refused("engine identity unknown")
        try:
            birth = self.native.of_handle(self.handle)
            if (birth is None or birth[0] < self.root["created"]
                    or ntpath.basename(birth[1]).lower() != "msedgewebview2.exe"
                    or (self.birth is not None and birth != self.birth)):
                raise Refused("engine birth unknown, reused or predates launch")
            self.scope.native.verify(self.scope.handle)
            if not self.scope.native.contains(self.scope.handle, self.handle):
                raise Refused("engine outside retained job")
            snapshot = self.scope.snapshot()
            if pid not in snapshot["pids"] or snapshot["active"] < 1:
                raise Refused("engine no longer active in job")
            if self.native.of_handle(self.handle) != birth:
                raise Refused("engine changed during admission")
            self.engine, self.birth = pid, birth
            return {"request": self.token, "engine_pid": pid, "admitted": True,
                    "job_id": self.scope.descriptor["id"], "created": birth[0],
                    "exe": birth[1], "scope": "offline fixture; enrolled family only"}
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.handle:
            self.native.k.CloseHandle(self.handle)
            self.handle = None


def run(api, guard_read, native, name, folder, argv, token,
        *, clock=time.monotonic, pause=time.sleep, timeout=40):
    """Injected boundaries let tests exercise the real orchestration, without OS calls.

    No launch is admitted from a receipt. The shared launcher persists birth and
    assigns the suspended root before resuming. Shared close owns all cleanup.
    """
    from sandbox_birth import bound

    folder = Path(folder)
    if any(p.name != "source.json" for p in folder.iterdir()):
        raise Refused("fresh receipt directory required; retained evidence untouched")
    result = {"public_navigation": False, "legacy_runtime_closure": "UNKNOWN; untouched",
              "job_closure": "unknown", "engine_admitted": False, "phase": "preflight"}
    write(folder / "launch.json", result)  # persistence failure prevents launch
    if guard_read().get("admitted") is not True:
        result.update(phase="refused", reason="fresh house guard did not admit")
        write(folder / "launch.json", result)
        return result
    with api.Guard(name, "Agora offline admission probe") as guard:
        with api.job_scope(name) as scope:
            fence = None
            started = False
            try:
                # Re-read immediately before the shared suspended birth.
                if guard_read().get("admitted") is not True:
                    raise Refused("house guard changed before launch")
                started = True  # a partially failed start may have created a child
                pid = api.start(name, argv, job=scope)
                state = api.load(name)
                owners = state.get("owners", [])
                if (state.get("job") != scope.descriptor or len(owners) != 1
                        or owners[0].get("pid") != pid
                        or owners[0].get("job_id") != scope.descriptor["id"]
                        or owners[0].get("parent") != scope.descriptor["creator"]
                        or not bound(state, owners[0])
                        or len(state.get("launches", [])) != 1
                        or state["launches"][0].get("job_assigned") is not True):
                    raise Refused("launcher root receipt incomplete")
                root = owners[0]
                result.update(pid=pid, job=dict(scope.descriptor), phase="waiting_engine")
                write(folder / "launch.json", result)
                fence = EngineFence(scope, native, root, token)
                deadline = clock() + timeout
                request = None
                while clock() < deadline:
                    if guard_read().get("admitted") is not True:
                        raise Refused("house guard stale or unsafe during fixture")
                    receipt = folder / "receipt.json"
                    if receipt.exists():
                        child = read(receipt)
                        if child.get("pid") != pid:
                            raise Refused("child receipt PID mismatch")
                        if child.get("phase") == "child_exit":
                            if not result["engine_admitted"]:
                                raise Refused("child exited without engine admission")
                            result.update(phase="child_exit", child=child)
                            break
                    path = folder / "engine-request.json"
                    if path.exists():
                        current = read(path)
                        if request is None:
                            admission = fence.check(current)
                            request = current
                            write(folder / "engine-admission.json", admission)
                            result["engine_admitted"] = True
                        elif request != current:
                            raise Refused("engine request changed")
                        # Non-breakaway Job membership cannot migrate after
                        # admission. Keep the birth handle pinned, but don't
                        # mistake normal engine shutdown before child_exit for
                        # a reuse. Trusted fixture code rejects Core PID changes.
                    pause(0.02)
                else:
                    result.update(phase="deadline_fired", deadline_seconds=timeout)
            except (Exception, SystemExit) as exc:
                result.update(phase="refused", error_type=type(exc).__name__,
                              error=error(exc),
                              reason=exc.reason if isinstance(exc, Refused)
                              else "fixture boundary failed; see redacted error")
            finally:
                if fence:
                    try:
                        fence.close()
                    except Exception as exc:
                        result["engine_handle_close_error"] = type(exc).__name__
                if started:
                    # Must run BEFORE the retained Job handle closes. No fallback.
                    try:
                        cleanup = api.close(name, quiet=True)
                        result["cleanup"] = cleanup
                        if cleanup.get("ok") is True and cleanup.get("receipt"):
                            closed = read(cleanup["receipt"])
                            if (closed.get("job") == scope.descriptor
                                    and closed.get("job_closure") == "proven empty"
                                    and closed.get("remaining_pids") == []):
                                result["job_closure"] = "proven empty"
                    except Exception as exc:
                        result["cleanup"] = {"ok": False, "error_type": type(exc).__name__}
                write(folder / "launch.json", result)
    result["guard_code"], result["guard"] = guard.verdict()
    write(folder / "launch.json", result)
    return result
