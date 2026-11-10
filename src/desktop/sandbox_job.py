"""Opt-in, in-process kernel ownership of a newly launched sandbox family.

No job is reopened by name or adopted from a manifest. A live, unnamed handle
is the authority; JSON is a receipt, not authentication. Out-of-job delegation
and legacy runtimes remain outside this boundary.
"""
import copy
import ctypes as c
from ctypes import wintypes as w
import os
import time
import uuid

from sandbox_receipts import error

KILL_ON_CLOSE = 0x2000
_LIVE = {}


class BasicLimits(c.Structure):
    _fields_ = [("process_time", c.c_int64), ("job_time", c.c_int64),
                ("flags", w.DWORD), ("min_working", c.c_size_t),
                ("max_working", c.c_size_t), ("active_limit", w.DWORD),
                ("affinity", c.c_size_t), ("priority", w.DWORD), ("scheduling", w.DWORD)]


class IoCounters(c.Structure):
    _fields_ = [(name, c.c_uint64) for name in
                ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]


class ExtendedLimits(c.Structure):
    _fields_ = [("basic", BasicLimits), ("io", IoCounters),
                ("process_memory", c.c_size_t), ("job_memory", c.c_size_t),
                ("peak_process", c.c_size_t), ("peak_job", c.c_size_t)]


class Accounting(c.Structure):
    _fields_ = [(name, c.c_int64) for name in ("user", "kernel", "period_user", "period_kernel")] + [
        (name, w.DWORD) for name in ("faults", "total", "active", "terminated")]


class WindowsJob:
    """Only the newly created, non-inheritable unnamed job handle is used."""
    def __init__(self):
        self.k = c.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "CreateJobObjectW": ([c.c_void_p, w.LPCWSTR], w.HANDLE),
            "SetInformationJobObject": ([w.HANDLE, c.c_int, c.c_void_p, w.DWORD], w.BOOL),
            "QueryInformationJobObject": ([w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.c_void_p], w.BOOL),
            "AssignProcessToJobObject": ([w.HANDLE, w.HANDLE], w.BOOL),
            "IsProcessInJob": ([w.HANDLE, w.HANDLE, c.POINTER(w.BOOL)], w.BOOL),
            "TerminateJobObject": ([w.HANDLE, w.UINT], w.BOOL),
            "CloseHandle": ([w.HANDLE], w.BOOL),
        }
        for name, (args, result) in signatures.items():
            fn = getattr(self.k, name)
            fn.argtypes, fn.restype = args, result

    def checked(self, ok):
        if not ok:
            raise c.WinError(c.get_last_error())

    def create(self):
        handle = self.k.CreateJobObjectW(None, None)  # unnamed, non-inheritable
        self.checked(handle)
        try:
            limits = ExtendedLimits()
            limits.basic.flags = KILL_ON_CLOSE  # neither BREAKAWAY nor SILENT_BREAKAWAY
            self.checked(self.k.SetInformationJobObject(handle, 9, c.byref(limits), c.sizeof(limits)))
            self.verify(handle)
            return handle
        except BaseException:
            self.k.CloseHandle(handle)
            raise

    def verify(self, handle):
        limits = ExtendedLimits()
        self.checked(self.k.QueryInformationJobObject(handle, 9, c.byref(limits), c.sizeof(limits), None))
        if limits.basic.flags != KILL_ON_CLOSE:
            raise RuntimeError("job limits changed; containment unknown")

    def contains(self, handle, process):
        value = w.BOOL()
        self.checked(self.k.IsProcessInJob(process, handle, c.byref(value)))
        return bool(value.value)

    def assign(self, handle, process):
        self.verify(handle)
        self.checked(self.k.AssignProcessToJobObject(handle, process))
        if not self.contains(handle, process):
            raise RuntimeError("job membership unconfirmed; do not resume")

    def snapshot(self, handle):
        self.verify(handle)
        # Bounded list. More members or a racing query is unknown, never empty.
        class Pids(c.Structure):
            _fields_ = [("assigned", w.DWORD), ("listed", w.DWORD),
                        ("ids", c.c_size_t * 4096)]
        ids, account = Pids(), Accounting()
        self.checked(self.k.QueryInformationJobObject(handle, 3, c.byref(ids), c.sizeof(ids), None))
        self.checked(self.k.QueryInformationJobObject(handle, 1, c.byref(account), c.sizeof(account), None))
        if ids.listed > 4096 or ids.assigned != ids.listed:
            raise RuntimeError("job membership list incomplete")
        return {"pids": sorted(int(ids.ids[i]) for i in range(ids.listed)),
                "active": int(account.active), "total": int(account.total),
                "terminated": int(account.terminated)}

    def terminate(self, handle):
        self.verify(handle)
        self.checked(self.k.TerminateJobObject(handle, 0))

    def close(self, handle):
        self.checked(self.k.CloseHandle(handle))


class Scope:
    """Held by the harness for the entire run; never a detached helper/service."""
    def __init__(self, name, *, native=None, parent=None, clock=time.monotonic, pause=time.sleep):
        self.name, self.native = name, native
        self.parent, self.clock, self.pause = parent, clock, pause
        self.handle = None
        self.pid = os.getpid()
        self.descriptor = None
        self.closed = False

    def __enter__(self):
        if self.name in _LIVE or self.closed or self.handle:
            raise RuntimeError("job scope already used")
        if self.parent is None:
            from sandbox_owned import OwnedProcesses
            ident = OwnedProcesses().native.identity(self.pid)
            if ident is None:
                raise RuntimeError("job creator identity unavailable")
            self.parent = {"pid": self.pid, "created": ident[0], "exe": ident[1]}
        self.native = self.native or WindowsJob()
        self.handle = self.native.create()
        self.descriptor = {"schema": 1, "id": uuid.uuid4().hex, "creator": dict(self.parent),
                           "limits": KILL_ON_CLOSE, "breakaway": False,
                           "scope": "new enrolled family; external delegation unverified"}
        _LIVE[self.name] = self
        return self

    def admit(self, name, parent, state):
        if (_LIVE.get(name) is not self or self.closed or self.pid != os.getpid()
                or parent != self.parent or name != self.name):
            raise RuntimeError("live job scope mismatch")
        if state.get("job") != self.descriptor and (state.get("job") or state.get("pids")
                                                     or state.get("launches")):
            raise RuntimeError("no legacy or mixed job adoption")
        self.native.verify(self.handle)

    def snapshot(self):
        if self.closed or self.pid != os.getpid():
            raise RuntimeError("job owner no longer available")
        return self.native.snapshot(self.handle)

    def __exit__(self, *exc):
        # Last-handle close is a backstop, not an empty-job observation.
        try:
            if self.handle:
                self.native.close(self.handle)
        finally:
            self.closed = True
            _LIVE.pop(self.name, None)


def live(name, state):
    scope = _LIVE.get(name)
    if (scope is None or scope.closed or scope.pid != os.getpid()
            or scope.descriptor != state.get("job")):
        raise RuntimeError("live job handle unavailable or receipt mismatch")
    return scope


def cleanup(state, scope, persist, timeout=3):
    """Persist intent, terminate only the retained job, then observe it empty.

    Unknown termination is not replayed. A later empty observation can reconcile
    it. Closing a handle on crash is not itself a durable closure receipt.
    """
    from sandbox_birth import bound
    state["cleanup_complete"] = False
    state["job_closure"] = "unknown"
    state["remaining_pids"] = None
    state["runtime_closure"] = "unknown: external delegation not certified"
    attempts = state.setdefault("cleanup", [])
    if scope is not live(scope.name, state):
        raise RuntimeError("job identity mismatch")
    owners = state.get("owners") or []
    launches = state.get("launches") or []
    if (not owners or set(state.get("pids", [])) != {p.get("pid") for p in owners}
            or len(launches) != len(owners)
            or any(not bound(state, p) or p.get("job_id") != scope.descriptor["id"] for p in owners)
            or any(r.get("job_id") != scope.descriptor["id"] or r.get("job_assigned") is not True
                   for r in launches)):
        raise RuntimeError("job birth receipts incomplete; no termination")
    snapshot = scope.snapshot()
    pending = any(a.get("kind") == "job" and a.get("status") in ("pending", "unknown")
                  for a in attempts)
    if pending and (snapshot["pids"] or snapshot["active"]):
        persist(state)
        return {"ok": False, "reason": "previous job effect unknown; reconcile"}
    record = {"kind": "job", "job_id": scope.descriptor["id"], "status": "pending",
              "before": copy.deepcopy(snapshot)}
    attempts.append(record)
    persist(state)  # failure stops TerminateJobObject
    try:
        if snapshot["pids"] or snapshot["active"]:
            scope.native.terminate(scope.handle)
        deadline = scope.clock() + timeout
        while True:
            snapshot = scope.snapshot()
            if not snapshot["pids"] and snapshot["active"] == 0:
                record.update(status="empty", after=snapshot)
                state.update(cleanup_complete=True, job_closure="proven empty", remaining_pids=[])
                persist(state)
                return {"ok": True, "reason": "job confirmed empty", "scope": "enrolled job only"}
            if scope.clock() >= deadline:
                raise TimeoutError("job empty deadline timed out")
            scope.pause(0.02)
    except Exception as exc:
        record.update(status="unknown", error=error(exc))
        state.update(cleanup_complete=False, job_closure="unknown", remaining_pids=None)
        persist(state)
        return {"ok": False, "reason": "job closure unknown"}
