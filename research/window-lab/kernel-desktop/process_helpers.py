"""OS seam for the explicit steward-only system.end-helpers word.

No inventory or process handle is opened at import. Selection is shared with
system.processes. No taskkill, name-based termination, files, or settings changes.
"""
import ctypes
from ctypes import wintypes as w
import time

import process_read

HELP = (
    "system.end-helpers [dry=yes]: stewards (including the desktop owner) only. "
    "List or end Chrome/Edge browser trees whose profile folder proves they are "
    "Agora test/snap helpers, using the same classification as system.processes. "
    "dry=yes lists all matching processes without ending anything. No PID, name "
    "or path selectors are accepted. Every process identity is checked again "
    "through an open OS handle before any termination. Active matching test/snap "
    "browsers are included; this is not an orphan detector. Receipts list PID, "
    "profile, outcome and estimated working-set bytes released after confirmed "
    "exit (shared pages overlap; this is not physical RAM freed). Missing or "
    "denied inventory refuses without another access method. Undo cannot restart "
    "ended helpers. No profile files are deleted."
)


class ProcessChanged(OSError):
    pass


class WindowsProcesses:
    """Hold the verified process object throughout termination, never reopen a PID."""
    def __init__(self):
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "OpenProcess": ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
            "GetProcessTimes": ([w.HANDLE] + [ctypes.POINTER(w.FILETIME)] * 4, w.BOOL),
            "TerminateProcess": ([w.HANDLE, w.UINT], w.BOOL),
            "WaitForSingleObject": ([w.HANDLE, w.DWORD], w.DWORD),
            "CloseHandle": ([w.HANDLE], w.BOOL),
        }
        for name, (args, result) in signatures.items():
            fn = getattr(self.api, name)
            fn.argtypes, fn.restype = args, result

    def open(self, row):
        handle = self.api.OpenProcess(0x1000 | 0x100000 | 0x0001, False, int(row["pid"]))
        if not handle:
            raise OSError("Cannot open helper process")
        try:
            stamps = [w.FILETIME() for _ in range(4)]
            if not self.api.GetProcessTimes(handle, *(ctypes.byref(t) for t in stamps)):
                raise OSError("Cannot verify helper identity")
            born = (stamps[0].dwHighDateTime << 32) | stamps[0].dwLowDateTime
            # CIM CreationDate has microsecond precision; FILETIME has 100ns.
            expected = int(row["born"]) - 504911232000000000
            if born // 10 != expected // 10 or self.exited(handle):
                raise ProcessChanged("Helper exited or PID was reused")
            return handle
        except BaseException:
            self.close(handle)
            raise

    def terminate(self, handle):
        if not self.api.TerminateProcess(handle, 1):
            raise OSError("Helper termination denied")

    def exited(self, handle):
        result = self.api.WaitForSingleObject(handle, 0)
        if result == 0xFFFFFFFF:
            raise OSError("Cannot verify helper exit")
        return result == 0

    def close(self, handle):
        self.api.CloseHandle(handle)


def end_helpers(prefixes, *, dry=False, collect=None, backend=None, clock=time.monotonic):
    """Fresh full inventory, preflight every handle, then root-first termination.

    The short collection timeout and bounded exit polling fit the module call's
    ten-second budget. Access/identity failures before execution are all-or-none;
    failures after execution are reported per process, never as "nothing done".
    """
    try:
        raw = (collect or process_read.collect)(prefixes, timeout=5)
        selected = process_read.helper_processes(raw, prefixes)
    except (OSError, ValueError, KeyError, TypeError, process_read.subprocess.SubprocessError):
        return {"refused": "Helper inventory unavailable; nothing ended; no alternate access attempted"}

    def depth(row):
        parent, seen = int(row["parent_pid"]), {int(row["pid"])}
        while parent in selected and parent not in seen:
            seen.add(parent)
            parent = int(selected[parent]["parent_pid"])
        return len(seen)

    candidates = sorted(selected.values(), key=lambda r: (depth(r), int(r["pid"])))
    rows = [dict(kind="helper-process", pid=int(p["pid"]), profile=p["profile"],
                 working_set=p.get("working_set"), private_bytes=p.get("private_bytes"),
                 outcome="would end" if dry else "not ended", released_working_set=0)
            for p in candidates]
    if dry or not rows:
        return result(rows, dry)
    handles = []
    try:
        backend = backend or WindowsProcesses()
        # Do not act on a partially verified tree.
        for candidate in candidates:
            handles.append(backend.open(candidate))
    except OSError:
        for handle in handles:
            backend.close(handle)
        return {"refused": "A helper exited, changed identity or could not be opened; nothing ended. "
                           "Read system.processes again; no alternate access attempted",
                "rows": rows}

    try:
        for row, handle in zip(rows, handles):
            try:
                if backend.exited(handle):
                    row["outcome"] = "already exited"
                else:
                    backend.terminate(handle)
                    row["outcome"] = "exit pending"
            except OSError:
                row["outcome"] = "denied; not ended"
        deadline = clock() + 1
        while True:
            pending = False
            for row, handle in zip(rows, handles):
                if row["outcome"] != "exit pending":
                    continue
                try:
                    if backend.exited(handle):
                        row["outcome"] = "ended"
                        row["released_working_set"] = row["working_set"]
                    else:
                        pending = True
                except OSError:
                    row["outcome"] = "exit unverified"
            if not pending or clock() >= deadline:
                break
            time.sleep(0.02)
    finally:
        for handle in handles:
            backend.close(handle)
    return result(rows, dry)


def result(rows, dry):
    released = sum(r["released_working_set"] or 0 for r in rows)
    unknown = sum(r["outcome"] == "ended" and r["working_set"] is None for r in rows)
    text = [f"{'Dry run: ' if dry else ''}{len(rows)} matching helper processes; "
            f"estimated working-set bytes released: {released} ({unknown} unknown).",
            "Shared pages overlap; this is not measured physical RAM freed. "
            "Only processes in this inventory are covered; a concurrently spawned process may remain."]
    text.extend(f"pid={r['pid']} profile={r['profile']}: {r['outcome']}; "
                f"working set={r['working_set']}; released estimate={r['released_working_set']}"
                for r in rows)
    return {"external": not dry and bool(rows), "text": "\n".join(text), "rows": rows}
