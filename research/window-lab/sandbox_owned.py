"""Exact owned-process fences using the existing Windows handle adapter.

No import-time process queries. New suspended births use their original launch
facts plus exact returned-handle identity. Legacy receipts still require WMI
metadata for the supplied owned PID; denial is final, with no alternate route.
No process-tree kill, PID-only kill or discovery-by-desktop/profile fallback.
"""
import json
import ntpath
import subprocess

from hud_lifecycle import Windows
from sandbox_receipts import error, path_key, same


class MetadataUnavailable(RuntimeError):
    def __init__(self, receipt):
        super().__init__("Process metadata unavailable")
        self.receipt = receipt


class OwnedProcesses:
    def __init__(self, native=None, run=subprocess.run):
        self.native = native or Windows()
        self.run = run

    def metadata(self, pid):
        if type(pid) is not int or pid <= 0:
            raise ValueError("invalid owned PID")
        # Do not persist command lines: only canonical profile/parent identity.
        command = (
            "$ErrorActionPreference='Stop'; "
            f"Get-CimInstance Win32_Process -Filter 'ProcessId={pid}' "
            "| Select-Object ProcessId,ParentProcessId,CommandLine "
            "| ConvertTo-Json -Compress")
        result = self.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                          capture_output=True, text=True, timeout=3, creationflags=0x08000000)
        if result.returncode:
            receipt = {"returncode": result.returncode,
                       "stderr": error(RuntimeError(result.stderr))["message"]}
            raise MetadataUnavailable(receipt)
        row = json.loads(result.stdout)
        if not isinstance(row, dict) or row.get("ProcessId") != pid or not row.get("CommandLine"):
            raise MetadataUnavailable({"reason": "owned metadata unknown"})
        args = self.native.argv(row["CommandLine"])
        profiles = []
        for i, arg in enumerate(args):
            for flag in ("--user-data-dir", "--sandbox-profile"):
                if arg.startswith(flag + "="):
                    profiles.append(arg[len(flag) + 1:])
                elif arg == flag:
                    profiles.append(args[i + 1] if i + 1 < len(args) else "")
        if len(profiles) > 1 or profiles == [""]:
            raise MetadataUnavailable({"reason": "ambiguous profile"})
        if profiles and not ntpath.isabs(profiles[0]):
            raise MetadataUnavailable({"reason": "profile is not absolute"})
        parent_pid = row["ParentProcessId"]
        if type(parent_pid) is not int or parent_pid <= 0:
            raise MetadataUnavailable({"reason": "parent identity unknown"})
        parent = self.native.identity(parent_pid)
        if parent is None:
            raise MetadataUnavailable({"reason": "parent identity unknown"})
        return {"parent": {"pid": parent_pid, "created": parent[0], "exe": parent[1]},
                "profile": path_key(profiles[0]) if profiles else ""}

    def capture(self, pid):
        handle = self.native.k.OpenProcess(0x1000, False, pid)
        if not handle:
            raise OSError(self.native.c.get_last_error(), "Cannot inspect owned process")
        try:
            return self.on_handle(pid, handle)
        finally:
            self.native.k.CloseHandle(handle)

    def on_handle(self, pid, handle):
        before = self.native.of_handle(handle)
        if before is None:
            raise MetadataUnavailable({"reason": "process identity unknown"})
        data = self.metadata(pid)
        if data["parent"]["created"] > before[0]:
            raise MetadataUnavailable({"reason": "parent PID was reused"})
        if self.native.of_handle(handle) != before:
            raise MetadataUnavailable({"reason": "process changed during inspection"})
        return {"pid": pid, "created": before[0], "exe": before[1], **data}

    def gone(self, owner):
        handle = self.native.k.OpenProcess(0x1000, False, owner["pid"])
        if not handle:
            # Access denied is UNKNOWN, not absent. ERROR_INVALID_PARAMETER
            # means the PID is no longer a process.
            if self.native.c.get_last_error() == 87:
                return True
            raise OSError(self.native.c.get_last_error(), "Cannot inspect owned process")
        try:
            code = self.native.w.DWORD()
            if not self.native.k.GetExitCodeProcess(handle, self.native.c.byref(code)):
                raise OSError(self.native.c.get_last_error(), "Cannot inspect owned process")
            if code.value != 259:
                return True
            ident = self.native.of_handle(handle)
            if ident is None:
                raise MetadataUnavailable({"reason": "process identity unknown"})
            # Reused PID: old identity gone; never terminate the new one.
            return ident != (owner["created"], path_key(owner["exe"]))
        finally:
            self.native.k.CloseHandle(handle)

    def finish(self, owner):
        if owner.get("method") == "CreateProcessW-suspended-v1":
            return self.finish_birth(owner)
        # Absence of a command-line profile flag is not proof of the engine's
        # actual profile (e.g. a Python/WebView2 host sets it in-process).
        # Recording that absence is useful, but cannot admit termination.
        if not owner.get("profile"):
            return {"status": "refused", "reason": "profile identity unknown"}
        n = self.native
        handle = n.k.OpenProcess(0x1000 | 1 | 0x100000, False, owner["pid"])
        if not handle:
            return {"status": "refused", "winerror": n.c.get_last_error(),
                    "reason": "cannot open owned process"}
        try:
            if not same(owner, self.on_handle(owner["pid"], handle)):
                return {"status": "refused", "reason": "owned identity changed"}
            if not n.k.TerminateProcess(handle, 0):
                return {"status": "failed", "winerror": n.c.get_last_error(),
                        "reason": "owned termination failed"}
            wait = n.k.WaitForSingleObject(handle, 3000)
            return {"status": "ended" if wait == 0 else "pending", "wait": int(wait)}
        except MetadataUnavailable as exc:
            return {"status": "refused", "reason": "owned metadata unavailable",
                    "metadata_receipt": exc.receipt}
        finally:
            n.k.CloseHandle(handle)

    def finish_birth(self, owner):
        """Reopen and pin the recorded birth, never rediscover/adopt a child.

        Launch facts were captured before its initial thread ran. This verifies
        the same birth, not mutable engine configuration or descendant closure.
        Access denied remains a refusal; no WMI fallback or tree termination.
        """
        from sandbox_birth import valid
        if not valid(owner):
            return {"status": "refused", "reason": "birth receipt incomplete"}
        n = self.native
        handle = n.k.OpenProcess(0x1000 | 1 | 0x100000, False, owner["pid"])
        if not handle:
            return {"status": "refused", "winerror": n.c.get_last_error(),
                    "reason": "cannot open owned process"}
        try:
            if n.of_handle(handle) != (owner["created"], path_key(owner["exe"])):
                return {"status": "refused", "reason": "owned birth changed"}
            if not n.k.TerminateProcess(handle, 0):
                return {"status": "failed", "winerror": n.c.get_last_error(),
                        "reason": "owned termination failed"}
            wait = n.k.WaitForSingleObject(handle, 3000)
            return {"status": "ended" if wait == 0 else "pending", "wait": int(wait),
                    "scope": "recorded direct child only"}
        finally:
            n.k.CloseHandle(handle)
