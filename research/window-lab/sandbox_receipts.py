"""Offline-testable cleanup admission and bounded native-probe diagnostics.

Records are accidental-process-reuse fences, not authentication against another
process running as the same user. No OS calls, process discovery or effects here.
"""
import json
import ntpath
import time
import uuid
from pathlib import Path


def path_key(value):
    return ntpath.normcase(ntpath.normpath(value)) if value else ""


def message(exc):
    """Only known system phrases cross the receipt boundary; never raw text."""
    text = str(exc)[:1024].lower()
    for needle, public in (
        ("access is denied", "Access denied"), ("access denied", "Access denied"),
        ("operation aborted", "Operation aborted"), ("operation was canceled", "Operation canceled"),
        ("operation was cancelled", "Operation canceled"), ("class not registered", "Class not registered"),
        ("timed out", "Timed out"), ("timeout", "Timed out"),
    ):
        if needle in text:
            return public
    return "Exception message redacted"


def error(exc):
    name = type(exc).__name__
    def number(value):
        return value if type(value) is int else None
    result = {"type": name[:80] if name.isidentifier() else "Exception",
              "message": message(exc), "winerror": number(getattr(exc, "winerror", None)),
              "hresult": number(getattr(exc, "HResult", None))}
    receipt = getattr(exc, "receipt", None)
    if isinstance(receipt, dict):
        result["metadata_receipt"] = {}
        if type(receipt.get("returncode")) is int:
            result["metadata_receipt"]["returncode"] = receipt["returncode"]
        if "stderr" in receipt:
            result["metadata_receipt"]["stderr"] = message(receipt["stderr"])
        if "reason" in receipt:
            result["metadata_receipt"]["reason"] = "Process metadata unavailable"
    return result


def write(path, data):
    """Inherited-ACL temp file, atomic replacement; never tempfile(mode=0700)."""
    path = Path(path)
    scratch = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with scratch.open("x", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2)
            stream.flush()
            import os
            os.fsync(stream.fileno())
        scratch.replace(path)
    finally:
        scratch.unlink(missing_ok=True)


def update_manifest(path, fields):
    """Merge presentation metadata without racing a launch/cleanup receipt."""
    import os
    if set(fields) - {"pid", "port", "url", "profile", "at", "viewport"}:
        raise ValueError("ownership metadata is not a presentation update")
    path = Path(path)
    lock = path.with_suffix(".cleanup-lock")
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        if state.get("cleanup"):
            raise RuntimeError("cleanup receipt needs reconciliation; no metadata overwrite")
        state.update(fields)
        write(path, state)
        return state
    finally:
        os.close(fd)
        lock.unlink(missing_ok=True)


def complete(owner):
    def process(p):
        return (isinstance(p, dict) and type(p.get("pid")) is int and p["pid"] > 0
                and type(p.get("created")) is int and p["created"] > 0
                and isinstance(p.get("exe"), str) and ntpath.isabs(p["exe"]))
    return (process(owner) and process(owner.get("parent"))
            and "profile" in owner and isinstance(owner["profile"], str)
            and (not owner["profile"] or ntpath.isabs(owner["profile"])))


def same(expected, actual):
    """Empty profile means verified absence of a profile argument, not unknown."""
    if not complete(expected) or not complete(actual):
        return False
    for obj in (expected, actual):
        if obj.get("profile") and path_key(obj["profile"]) != obj["profile"]:
            return False
    return all(expected[k] == actual[k] for k in ("pid", "created", "profile")) and (
        path_key(expected["exe"]) == path_key(actual["exe"])
        and expected["parent"]["pid"] == actual["parent"]["pid"]
        and expected["parent"]["created"] == actual["parent"]["created"]
        and path_key(expected["parent"]["exe"]) == path_key(actual["parent"]["exe"]))


def cleanup(state, backend, persist, remaining):
    """Each backend admission pins and rechecks ONE handle, never taskkill /T.

    backend.finish(owner): checks full identity on the same handle it terminates.
    backend.gone(owner): True only on confirmed absence of that process identity.
    remaining(): [] means known empty; None means unknown, never success.
    Every intent is persisted before the effect. Failed persistence stops effects.
    """
    owners = state.get("owners", [])
    attempts = state.setdefault("cleanup", [])
    # Unknown/legacy manifests are never promoted from window PID membership.
    if (not isinstance(owners, list) or not owners
            or any(not complete(p) for p in owners)
            or len({p["pid"] for p in owners}) != len(owners)
            or set(state.get("pids", [])) - {p["pid"] for p in owners}):
        attempts.append({"status": "refused", "reason": "ownership incomplete"})
        persist(state)
        return {"ok": False, "reason": "ownership incomplete"}
    from sandbox_birth import METHOD, bound
    if any(p.get("method") == METHOD and not bound(state, p) for p in owners):
        attempts.append({"status": "refused", "reason": "birth receipt inconsistent"})
        persist(state)
        return {"ok": False, "reason": "birth receipt inconsistent"}
    ok = True
    # Children before parents while parent creation evidence remains observable.
    parents = {p["pid"]: p["parent"]["pid"] for p in owners}
    by_pid = {p["pid"]: p for p in owners}
    for child in owners:
        parent = child["parent"]
        expected = by_pid.get(parent["pid"])
        if expected and (parent["created"] != expected["created"]
                         or path_key(parent["exe"]) != path_key(expected["exe"])):
            attempts.append({"status": "refused", "reason": "parent ownership inconsistent"})
            persist(state)
            return {"ok": False, "reason": "parent ownership inconsistent"}

    def depth(pid):
        seen = set()
        while pid in parents:
            if pid in seen:
                raise ValueError("ownership cycle")
            seen.add(pid)
            pid = parents[pid]
        return len(seen)

    try:
        order = sorted(owners, key=lambda p: depth(p["pid"]), reverse=True)
    except ValueError:
        attempts.append({"status": "refused", "reason": "ownership cycle"})
        persist(state)
        return {"ok": False, "reason": "ownership cycle"}
    for owner in order:
        # Unknown crash outcome is reconciled, not replayed. A live process
        # after a persisted pending attempt needs explicit maintainer review.
        pending = any(r.get("pid") == owner["pid"] and r.get("created") == owner["created"]
                      and r.get("status") == "pending" for r in attempts)
        if pending:
            try:
                absent = backend.gone(owner)
            except Exception:
                absent = False
            if not absent:
                attempts.append({"status": "refused", "pid": owner["pid"],
                                 "reason": "previous effect unknown; reconcile"})
                persist(state)
                return {"ok": False, "reason": "previous effect unknown"}
        record = {"pid": owner["pid"], "created": owner["created"], "status": "pending"}
        attempts.append(record)
        persist(state)
        try:
            if backend.gone(owner):
                record.update(status="gone")
            else:
                # finish returns only redacted typed fields, never command text.
                record.update(backend.finish(owner))
                if record["status"] != "ended" or not backend.gone(owner):
                    ok = False
        except Exception as exc:
            record.update(status="failed", error=error(exc))
            ok = False
        persist(state)
    try:
        left = remaining()
    except Exception as exc:
        left = None
        attempts.append({"status": "inspection_failed", "error": error(exc)})
    ok = ok and left == []
    state["cleanup_complete"] = ok
    state["remaining_pids"] = sorted(set(left)) if left is not None else None
    persist(state)
    return {"ok": ok, "reason": "confirmed" if ok else "cleanup incomplete"}


class Diagnostics:
    """A receipt recorder, not proof that its caller or engine is isolated."""
    def __init__(self, save, *, clock=time.monotonic, child_id=None):
        self.clock, self.start, self.save = clock, clock(), save
        self.child_id = child_id or uuid.uuid4().hex
        self.data = {"schema": 1, "events": [], "deadline_fired": False,
                     "navigation_success": False, "child_ready": False}
        self.event("created")

    def event(self, phase, **values):
        # Callers supply typed metadata only, never URI/title/body/command text.
        allowed = {"success", "navigation_id", "exit_code", "kind", "error",
                   "messages_enabled", "host_objects_allowed", "top_channel",
                   "child_channel"}
        if set(values) - allowed:
            raise ValueError("unreviewed receipt field")
        if phase not in {
            "created", "import", "initializing", "initialized", "initialization_failed",
            "evaluation_failed", "native_failed", "deadline_fired", "navigation_completed",
            "child_ready", "child_ready_refused", "browser_process_exited", "process_failed",
            "disposing", "disposed", "parent_deadline", "handshake_wait",
        }:
            raise ValueError("unreviewed receipt phase")
        for key, value in values.items():
            if key == "error":
                # Accept exceptions, never a caller-supplied arbitrary dict.
                if not isinstance(value, BaseException):
                    raise ValueError("receipt requires an exception")
                values[key] = error(value)
            if key in {"navigation_id", "exit_code"} and type(value) is not int:
                raise ValueError("receipt requires integer")
            if key in {"success", "messages_enabled", "host_objects_allowed",
                       "top_channel", "child_channel"} and type(value) is not bool:
                raise ValueError("receipt requires boolean")
            if key == "kind" and (not isinstance(value, str) or not value.isidentifier() or len(value) > 80):
                raise ValueError("receipt requires bounded enum")
        if phase == "disposing":
            self.data["disposing"] = True
        if phase == "process_failed" or (phase == "browser_process_exited"
                                         and not (self.data.get("disposing")
                                                  and values.get("kind") == "Normal")):
            self.data["process_failure"] = True
            self.data["child_ready"] = False
        if len(self.data["events"]) >= 128:
            self.data["truncated"] = True
        else:
            self.data["events"].append({"phase": phase, "elapsed_ms": round(
                (self.clock() - self.start) * 1000, 3), **values})
        self.data["phase"] = phase
        self.save(self.data)

    def exception(self, phase, exc):
        self.event(phase, error=exc)

    def deadline(self):
        self.data["deadline_fired"] = True
        self.event("deadline_fired")  # persist BEFORE the caller closes/disposes

    def navigation(self, navigation_id, success):
        if type(navigation_id) is not int or type(success) is not bool:
            raise ValueError("navigation requires integer identity and boolean success")
        self.data.update(navigation_id=navigation_id, navigation_success=success,
                         child_ready=False)
        self.event("navigation_completed", navigation_id=navigation_id, success=success)

    def child_ready(self, child_id, navigation_id, *, top_channel, child_channel,
                    messages_enabled, host_objects_allowed):
        if any(type(v) is not bool for v in (top_channel, child_channel,
                                           messages_enabled, host_objects_allowed)):
            raise ValueError("handshake requires booleans")
        if (child_id != self.child_id or navigation_id != self.data.get("navigation_id")
                or self.data["navigation_success"] is not True
                or self.data["deadline_fired"] or self.data.get("truncated")
                or self.data.get("process_failure")):
            self.event("child_ready_refused")
            return False
        passed = all(v is False for v in (top_channel, child_channel, messages_enabled,
                                         host_objects_allowed))
        self.data["child_ready"] = passed
        self.event("child_ready", success=passed, navigation_id=navigation_id,
                   top_channel=top_channel, child_channel=child_channel,
                   messages_enabled=messages_enabled, host_objects_allowed=host_objects_allowed)
        return passed

    @property
    def passed(self):
        return (self.data["child_ready"] and self.data["navigation_success"]
                and not self.data["deadline_fired"] and not self.data.get("process_failure")
                and not self.data.get("truncated"))
