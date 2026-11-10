"""Parent-held Job lifetime for the OFFLINE admission fixture.

The file exchange below coordinates trusted fixture code. It is not an
authenticated host service or a grant to workers. JSON never establishes
ownership: the parent checks a held kernel process handle against its live Job.
No legacy discovery, job adoption, PID termination or external-runtime cleanup.
"""
import hashlib
import json
import math
import ntpath
import sys
import threading
import time
from functools import wraps
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sandbox_receipts import error, write


class Refused(RuntimeError):
    """Only fixed fixture reasons, never native exception text."""
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def guard_details(result, *, now=None):
    """Bounded metadata from the supported reader; never new admission policy."""
    result = result if isinstance(result, dict) else {}
    raw = result.get("observation")
    raw = raw if isinstance(raw, dict) else {}
    observed = raw.get("observed_at")
    age = None
    if type(observed) in (int, float) and math.isfinite(observed):
        age = (time.time() if now is None else now) - observed
        age = round(age, 3) if math.isfinite(age) else None
    exe = raw.get("foreground_exe")
    # Only an image basename, never titles, command lines or arbitrary fields.
    exe = (exe if isinstance(exe, str) and 0 < len(exe) <= 128
           and ntpath.basename(exe) == exe and not any(ord(c) < 32 for c in exe)
           else "unknown")
    reason = result.get("reason")
    return {
        "admitted": result.get("admitted") is True,
        "reason": reason[:200] if isinstance(reason, str) else "not supplied",
        "foreground_exe": exe,
        "game": raw.get("game") if type(raw.get("game")) is bool else None,
        "observation_age_seconds": age,
    }


class GuardRefused(Refused):
    def __init__(self, details):
        self.guard = details
        super().__init__("fresh house guard refused; no admission: " +
                         json.dumps(details, sort_keys=True))


def require_guard(reader):
    details = guard_details(reader())
    if not details["admitted"]:
        raise GuardRefused(details)
    return details


def read(path):
    with Path(path).open("rb") as stream:
        data = stream.read(65537)
    if len(data) > 65536:
        raise ValueError("oversized fixture receipt")
    return json.loads(data)


def engine_report(folder, token, host=None, engine=None):
    """Fixture coordination only; the shared verifier measures kernel provenance."""
    path = Path(folder) / "engine-request.json"
    if not path.exists():
        return None
    if host is None or engine is None:
        raise Refused("measured host and engine binding required")
    with host.lock:
        return _engine_report(folder, token, host, engine)


def _engine_report(folder, token, host, engine):
    path = Path(folder) / "engine-request.json"
    request = read(path)
    receipt = read(Path(folder) / "receipt.json")
    report = request.get("engine_report")
    host.envelope(receipt)
    host.envelope(request, pid_key="host_pid")
    engine.check(request)
    if (request.get("request") != token
            or type(request.get("host_pid")) is not int
            or request["host_pid"] != receipt.get("pid")
            or not isinstance(report, dict)
            or report.get("browser_pid") != request.get("engine_pid")):
        raise Refused("engine report envelope mismatch")
    if (read(path) != request or read(Path(folder) / "receipt.json") != receipt):
        raise Refused("engine report changed during read")
    host.check()
    return report


def image_key(value):
    return ntpath.normcase(ntpath.normpath(value))


def _locked(method):
    @wraps(method)
    def call(self, *args, **kwargs):
        with self.lock:
            return method(self, *args, **kwargs)
    return call


class HostFence:
    """Browser-only correlation fence; not a host service or worker authority.

    An empty reviewed image inventory admits nothing. Process APIs and image
    hashing are injectable for offline tests; no JSON field supplies provenance.
    """
    def __init__(self, scope, native, root, token, desktop, profile, allowed,
                 processes, digest=None):
        self.scope, self.native, self.root = scope, native, root
        self.token, self.desktop = token, desktop
        self.profile = image_key(str(profile))
        self.allowed = dict(allowed)
        self.processes = processes
        self.digest = digest or (lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest())
        self.handles, self.chain, self.binding = {}, [], None
        self.lock = threading.RLock()
        self.closed = False

    def _identity(self, pid):
        if self.closed:
            raise Refused("host fence closed; no reopen")
        if pid not in self.handles:
            handle = self.native.k.OpenProcess(0x1000 | 0x100000, False, pid)
            if not handle:
                raise Refused("host identity unavailable")
            self.handles[pid] = handle
        handle = self.handles[pid]
        birth = self.native.of_handle(handle)
        self.scope.native.verify(self.scope.handle)
        if birth is None or not self.scope.native.contains(self.scope.handle, handle):
            raise Refused("host identity ended or outside retained job")
        return (birth[0], image_key(birth[1]))

    @_locked
    def pin(self, pid):
        if self.closed:
            raise Refused("host fence closed; no reopen")
        if type(pid) is not int or pid <= 0 or not self.allowed:
            raise Refused("reviewed host image inventory required")
        if self.binding:
            if pid != self.binding["host"]["pid"]:
                raise Refused("effective host changed")
            return self.check()
        try:
            parents = self._parents()
            current, seen, chain = pid, set(), []
            for _ in range(16):
                if current in seen or current not in parents:
                    raise Refused("host ancestry missing or cyclic")
                seen.add(current)
                birth = self._identity(current)
                if chain and birth[0] > chain[-1]["created"]:
                    raise Refused("host ancestry birth order invalid")
                entry = {"pid": current, "created": birth[0], "exe": birth[1]}
                chain.append(entry)
                if current == self.root["pid"]:
                    if birth != (self.root["created"], image_key(self.root["exe"])):
                        raise Refused("launcher birth changed")
                    break
                expected = self.allowed.get(birth[1])
                if expected is None or self.digest(birth[1]) != expected:
                    raise Refused("effective interpreter image not reviewed")
                current = parents[current]
            else:
                raise Refused("host ancestry depth exceeded")
            # Direct hosts must also match an explicitly reviewed image.
            first = chain[0]
            if (first["exe"] not in self.allowed
                    or self.allowed[first["exe"]] != self.digest(first["exe"])):
                raise Refused("effective interpreter hash mismatch")
            first["file_sha256"] = self.allowed[first["exe"]]
            self.chain = [(entry, parents[entry["pid"]]) for entry in chain]
            self.binding = {"request": self.token, "job_id": self.scope.descriptor["id"],
                            "root": dict(chain[-1]), "host": dict(first),
                            "desktop": self.desktop, "profile": self.profile}
            return self.check()
        except BaseException:
            self.close()
            raise

    def _parents(self):
        rows = self.processes()
        result = {}
        for pid, parent, _ in rows:
            if pid in result:
                raise Refused("ambiguous process snapshot")
            result[pid] = parent
        return result

    @_locked
    def check(self):
        if self.closed:
            raise Refused("host fence closed; no reopen")
        if not self.binding:
            raise Refused("effective host not pinned")
        if self.binding["job_id"] != self.scope.descriptor["id"]:
            raise Refused("retained Job identity changed")
        parents = self._parents()
        snapshot = self.scope.snapshot()
        for entry, parent in self.chain:
            pid = entry["pid"]
            if (parents.get(pid) != parent or pid not in snapshot["pids"]
                    or self._identity(pid) != (entry["created"], entry["exe"])):
                raise Refused("host provenance changed")
            if pid != self.root["pid"]:
                if (entry["exe"] not in self.allowed
                        or self.digest(entry["exe"]) != self.allowed[entry["exe"]]):
                    raise Refused("interpreter ancestor hash changed")
        host = self.binding["host"]
        if self.digest(host["exe"]) != self.allowed.get(host["exe"]):
            raise Refused("effective interpreter hash changed")
        return json.loads(json.dumps(self.binding))

    @_locked
    def envelope(self, value, pid_key="pid", initial=False):
        if (value.get("request") != self.token or value.get("desktop") != self.desktop
                or image_key(str(value.get("profile", ""))) != self.profile
                or type(value.get(pid_key)) is not int):
            raise Refused("host envelope mismatch")
        if initial and not self.binding and value.get("phase") == "importing":
            if value.get("binding") is not None:
                raise Refused("unissued host binding")
            return self.pin(value[pid_key])
        binding = self.check()
        if (initial and value.get("phase") == "importing" and value.get("binding") is None
                and value[pid_key] == binding["host"]["pid"]):
            return binding  # same pending envelope while the response is read
        if value[pid_key] != binding["host"]["pid"] or value.get("binding") != binding:
            raise Refused("host binding mismatch")
        return binding

    @_locked
    def close(self):
        # Retain any handle whose close failed for explicit reconciliation.
        self.closed = True
        for pid, handle in list(self.handles.items()):
            if self.native.k.CloseHandle(handle) == 0:
                raise Refused("host handle close failed")
            del self.handles[pid]


class EngineFence:
    """Pins an engine birth to the parent's retained Job until cleanup."""
    def __init__(self, scope, native, root, token, host=None):
        self.scope, self.native, self.root, self.token = scope, native, root, token
        self.engine = None
        self.handle = None
        self.birth = None
        self.host = host
        self.lock = host.lock if host else threading.RLock()
        self.closed = False

    @_locked
    def check(self, request):
        if self.closed:
            raise Refused("engine fence closed; no reopen")
        if self.host:
            self.host.envelope(request, pid_key="host_pid")
        if (request.get("request") != self.token
                or request.get("host_pid") != (
                    self.host.binding["host"]["pid"] if self.host else self.root["pid"])
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
            minimum = self.host.binding["host"]["created"] if self.host else self.root["created"]
            if (birth is None or birth[0] < minimum
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
                    "exe": birth[1], "binding": self.host.check() if self.host else None,
                    "scope": "offline fixture; enrolled family only"}
        except BaseException:
            self.close()
            raise

    @_locked
    def close(self):
        self.closed = True
        if self.handle:
            if self.native.k.CloseHandle(self.handle) == 0:
                raise Refused("engine handle close failed")
            self.handle = None


def run(api, guard_read, native, name, folder, argv, token,
        *, verifier_factory=None, host_images=(), processes=None, digest=None,
        clock=time.monotonic, pause=time.sleep, timeout=40):
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
    if verifier_factory is None:
        result.update(phase="refused", reason="shared verifier required; no launch")
        write(folder / "launch.json", result)
        return result
    if not host_images or processes is None:
        result.update(phase="refused",
                      reason="reviewed effective-host configuration absent; no launch")
        write(folder / "launch.json", result)
        return result
    try:
        result["guard_admission"] = require_guard(guard_read)
    except GuardRefused as exc:
        result.update(phase="refused", reason=exc.reason, guard_admission=exc.guard)
        write(folder / "launch.json", result)
        return result
    with api.Guard(name, "Agora offline admission probe") as guard:
        with api.job_scope(name) as scope:
            fence = None
            host = None
            verifier = None
            started = False
            try:
                verifier = verifier_factory(scope)
                verifier.before()
                # Re-read immediately before the shared suspended birth.
                result["guard_admission"] = require_guard(guard_read)
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
                host = HostFence(scope, native, root, token, "agora-sandbox-" + name,
                                 folder / "profile", host_images, processes, digest)
                fence = EngineFence(scope, native, root, token, host)
                verifier.engine_report = lambda: engine_report(folder, token, host, fence)
                verifier.add_birth({k: root[k] for k in ("pid", "created", "exe")})
                verifier.start_sampling(0.1)
                result.update(pid=pid, job=dict(scope.descriptor), phase="waiting_engine")
                write(folder / "launch.json", result)
                deadline = clock() + timeout
                request = None
                while clock() < deadline:
                    result["guard_admission"] = require_guard(guard_read)
                    receipt = folder / "receipt.json"
                    if receipt.exists():
                        child = read(receipt)
                        first = host.binding is None
                        binding = host.envelope(child, initial=True)
                        if first:
                            result["host_binding"] = binding
                            write(folder / "host-binding.json", binding)
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
                            observed = verifier.gate()
                            result["interaction_gate"] = observed
                            if observed.get("allow_interaction") is not True:
                                raise Refused("shared verifier refused interaction")
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
                if isinstance(exc, GuardRefused):
                    result["guard_admission"] = exc.guard
                result.update(phase="refused", error_type=type(exc).__name__,
                              error=error(exc),
                              reason=exc.reason if isinstance(exc, Refused)
                              else "fixture boundary failed; see redacted error")
            finally:
                if verifier:
                    try:
                        verifier.stop_sampling()
                    except Exception as exc:
                        result["verifier_stop_error"] = type(exc).__name__
                if fence:
                    try:
                        fence.close()
                    except Exception as exc:
                        result["engine_handle_close_error"] = type(exc).__name__
                if host:
                    try:
                        host.close()
                    except Exception as exc:
                        result["host_handle_close_error"] = type(exc).__name__
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
                if verifier:
                    try:
                        verifier.after()
                        result["native_verification"] = verifier.verdict()
                    except Exception as exc:
                        result["native_verification"] = {
                            "allow_interaction": False, "status": "unknown",
                            "error_type": type(exc).__name__}
                write(folder / "launch.json", result)
    result["guard_code"], result["guard"] = guard.verdict()
    write(folder / "launch.json", result)
    return result
