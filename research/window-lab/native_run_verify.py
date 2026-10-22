"""One shared native-run verifier for the browser (a9231) and AgoraMail (a9011): a10179.

A harness that holds a live job scope (sandbox_job, a9868) for its whole run builds a Verifier, and the verifier
observes four things, read-only, and says for each what it observed and what it could not prove:

  family    every member of the held job, by identity; no process outside the job names the run's profile (before
            launch: an engine already holding it would be reused; during: an out-of-job or brokered engine; after
            cleanup: a survivor); the consumer's own engine report (WebView2 BrowserProcessId, effective
            UserDataFolder, process list) cross-checked against job members and their measured roles; job members
            with no measured provenance (birth receipt, or a measured parent chain) are unknown
  windows   top-level windows on the hidden sandbox desktop owned by job members, and an explicitly scoped
            observation of the Default desktop (owner PIDs only: no titles, no pixels) finding none of ours
  network   TCP endpoints (GetExtendedTcpTable, v4 and v6) and UDP bindings (GetExtendedUdpTable) owned by job
            members, sampled at a stated interval, judged against the run's allowlist
  writes    before/after hashes of the run-owned roots (profile, scratch), bounded metadata of the other roots the
            run names, the job's I/O accounting, and the system's install records (uninstall keys, services, Run)

Verdicts (Mica c10185, Rowan c10186, JEFF c10193): each check is `violation` (something forbidden was seen),
`unknown` (an observation it needed failed or was not made), or `observed` (looked, saw nothing forbidden). An
`observed` verdict always says `not_proven`: what snapshots and samples cannot show (transient connections between
samples, UDP/QUIC remotes, brokered traffic such as DNS in Dnscache, hostnames behind IPs, deleted or reverted
writes, writes outside the scanned roots, desktops not observed). There is no `pass`. `allow_interaction()` is
True only when every check is `observed`; a consumer must stop before input or DevTools otherwise.

What it never does: terminate, adopt, signal or open with write access any process; change a setting or a
security descriptor; install; read file contents outside the run-owned roots (those are hashed, never stored);
store a command line, a window title, or another process's path. Command lines of engine-named processes outside
the job are read in memory only to ask "does it name our profile", and dropped.
"""
import ctypes as c
from ctypes import wintypes as w
import hashlib
import ipaddress
import ntpath
import os
from pathlib import Path
import re
import socket
import struct
import threading
import time

from sandbox_receipts import error, path_key

ENGINE_IMAGES = ("msedgewebview2.exe", "msedge.exe")
VIOLATION, UNKNOWN, OBSERVED = "violation", "unknown", "observed"
MAX_FILES = 20000                 # per root; more is unknown, never a partial clean
MAX_HASH_BYTES = 1 << 30          # per run-owned root
LISTEN = 2
TCP_STATES = {1: "closed", 2: "listen", 3: "syn-sent", 4: "syn-received", 5: "established", 6: "fin-wait-1",
              7: "fin-wait-2", 8: "close-wait", 9: "closing", 10: "last-ack", 11: "time-wait", 12: "delete-tcb"}

# What each check cannot prove, by a stable key. A consumer names the keys it needs proven in run["must_prove"]; any of
# them present in a judged check refuses interaction (c10251), and a key the verifier does not know refuses too.
NOT_PROVEN = {
    "family": {
        "family.brokered": "processes started outside this job by a broker, service or WMI that never name the "
                           "profile on their command line",
        "family.between_samples": "membership between samples (a member that lived only between two samples)",
    },
    "windows": {
        "windows.between_samples": "windows that existed only between samples",
        "windows.other_desktops": "desktops other than the sandbox and Default (other window stations, secure "
                                  "desktop)",
        "windows.message_only": "message-only windows (no desktop)",
    },
    "network": {
        "network.between_samples": "connections opened and closed between samples",
        "network.udp_remotes": "UDP and QUIC remote endpoints (only local bindings are visible)",
        "network.brokered": "traffic made for the job by processes outside it (DNS in the Dnscache service, BITS, "
                            "the WebView2 updater)",
        "network.hostname": "that a remote IP is the allowed hostname (an IP matched the harness's own resolution "
                            "of it, kept with its provenance)",
        "network.urls": "URLs, redirects, workers and frames (sockets show endpoints, not requests)",
    },
    "writes": {
        "writes.transient": "files written then deleted or reverted within the run",
        "writes.unscanned": "writes outside the scanned roots",
        "writes.attribution": "which job process made which write (I/O totals name no path)",
        "writes.brokered": "writes by processes outside the job made on its behalf",
    },
}
ALL_LIMITS = {k for d in NOT_PROVEN.values() for k in d}


def check(status, observed, evidence=None, reasons=None, not_proven=None):
    limits = dict(not_proven or {})
    return {"status": status, "observed": observed, "not_proven": list(limits.values()),
            "not_proven_keys": list(limits), "reasons": list(reasons or []), "evidence": evidence or {}}


def role_of(image, command_line):
    """A member's role, measured from its own image and command line (only this word is kept)."""
    image = image.lower()
    if image == "conhost.exe":
        return "console host"
    m = re.search(r"--type=([\w-]+)", command_line or "")
    if m:
        return m.group(1)
    return "browser" if image in ENGINE_IMAGES else "process"


def resolve_allowed(host, port, *, lookup=socket.getaddrinfo, wall=time.time):
    """One allowlist entry, resolved by the harness before launch, keeping its provenance: the host, port, the
    addresses this resolver gave, when, and how. An endpoint matching it is 'an address the harness resolved for host',
    never proof that the connection was to that host (network.hostname stays not proven)."""
    infos = lookup(host, port, proto=socket.IPPROTO_TCP)
    ips = sorted({i[4][0] for i in infos})
    return {"host": host, "port": port, "ips": ips, "resolved_at": wall(), "how": "socket.getaddrinfo, system "
            "resolver, before launch"}


def worst(statuses):
    return VIOLATION if VIOLATION in statuses else UNKNOWN if UNKNOWN in statuses else OBSERVED


def is_loopback(addr):
    try:
        return ipaddress.ip_address(addr.split("%")[0]).is_loopback
    except ValueError:
        return False


def is_unspecified(addr):
    try:
        return ipaddress.ip_address(addr.split("%")[0]).is_unspecified
    except ValueError:
        return False


def names_root(command_line, roots):
    """Does this command line name one of the roots (as itself or a path under it)? Case-insensitive, normalised."""
    text = command_line.replace("/", "\\").lower()
    for root in roots:
        key = path_key(root).lower()
        if key and re.search(re.escape(key) + r'(?=$|[\\"\s,;])', text):
            return True
    return False


def under(path, roots):
    key = path_key(path).lower()
    return any(key == path_key(r).lower() or key.startswith(path_key(r).lower().rstrip("\\") + "\\") for r in roots)


# ---- the native reads (all read-only) ------------------------------------------------------------------------------

class PROCESSENTRY32W(c.Structure):
    _fields_ = [("dwSize", w.DWORD), ("cntUsage", w.DWORD), ("th32ProcessID", w.DWORD),
                ("th32DefaultHeapID", c.c_size_t), ("th32ModuleID", w.DWORD), ("cntThreads", w.DWORD),
                ("th32ParentProcessID", w.DWORD), ("pcPriClassBase", w.LONG), ("dwFlags", w.DWORD),
                ("szExeFile", w.WCHAR * 260)]


class UNICODE_STRING(c.Structure):
    _fields_ = [("Length", w.USHORT), ("MaximumLength", w.USHORT), ("Buffer", c.c_void_p)]


class BasicAndIo(c.Structure):
    _fields_ = [(n, c.c_int64) for n in ("user", "kernel", "period_user", "period_kernel")] + [
        (n, w.DWORD) for n in ("faults", "total", "active", "terminated")] + [
        (n, c.c_uint64) for n in ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]


class Native:
    """Typed Win32 reads. Every process handle is PROCESS_QUERY_LIMITED_INFORMATION only."""
    QUERY = 0x1000

    def __init__(self):
        self.k = c.WinDLL("kernel32", use_last_error=True)
        self.u = c.WinDLL("user32", use_last_error=True)
        self.nt = c.WinDLL("ntdll")
        self.ip = c.WinDLL("iphlpapi")
        self.enum_type = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
        for dll, name, result, args in [
            (self.k, "CreateToolhelp32Snapshot", w.HANDLE, [w.DWORD, w.DWORD]),
            (self.k, "Process32FirstW", w.BOOL, [w.HANDLE, c.POINTER(PROCESSENTRY32W)]),
            (self.k, "Process32NextW", w.BOOL, [w.HANDLE, c.POINTER(PROCESSENTRY32W)]),
            (self.k, "OpenProcess", w.HANDLE, [w.DWORD, w.BOOL, w.DWORD]),
            (self.k, "CloseHandle", w.BOOL, [w.HANDLE]),
            (self.k, "GetProcessTimes", w.BOOL, [w.HANDLE] + [c.POINTER(w.FILETIME)] * 4),
            (self.k, "GetExitCodeProcess", w.BOOL, [w.HANDLE, c.POINTER(w.DWORD)]),
            (self.k, "QueryFullProcessImageNameW", w.BOOL, [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)]),
            (self.k, "IsProcessInJob", w.BOOL, [w.HANDLE, w.HANDLE, c.POINTER(w.BOOL)]),
            (self.k, "QueryInformationJobObject", w.BOOL, [w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.c_void_p]),
            (self.nt, "NtQueryInformationProcess", c.c_long, [w.HANDLE, c.c_int, c.c_void_p, w.ULONG,
                                                              c.POINTER(w.ULONG)]),
            (self.u, "OpenDesktopW", w.HANDLE, [w.LPCWSTR, w.DWORD, w.BOOL, w.DWORD]),
            (self.u, "CloseDesktop", w.BOOL, [w.HANDLE]),
            (self.u, "EnumDesktopWindows", w.BOOL, [w.HANDLE, self.enum_type, w.LPARAM]),
            (self.u, "GetWindowThreadProcessId", w.DWORD, [w.HWND, c.POINTER(w.DWORD)]),
            (self.u, "IsWindowVisible", w.BOOL, [w.HWND]),
            (self.ip, "GetExtendedTcpTable", w.DWORD, [c.c_void_p, c.POINTER(w.DWORD), w.BOOL, w.ULONG,
                                                      c.c_int, w.ULONG]),
            (self.ip, "GetExtendedUdpTable", w.DWORD, [c.c_void_p, c.POINTER(w.DWORD), w.BOOL, w.ULONG,
                                                      c.c_int, w.ULONG]),
        ]:
            fn = getattr(dll, name)
            fn.restype, fn.argtypes = result, args

    # processes
    def processes(self):
        """[(pid, parent pid, image basename)] of every process now (Toolhelp; image name needs no handle)."""
        snap = self.k.CreateToolhelp32Snapshot(0x2, 0)
        if not snap or snap == w.HANDLE(-1).value:
            raise c.WinError(c.get_last_error())
        try:
            entry, out = PROCESSENTRY32W(dwSize=c.sizeof(PROCESSENTRY32W)), []
            ok = self.k.Process32FirstW(snap, c.byref(entry))
            while ok:
                out.append((int(entry.th32ProcessID), int(entry.th32ParentProcessID), entry.szExeFile))
                ok = self.k.Process32NextW(snap, c.byref(entry))
            return out
        finally:
            self.k.CloseHandle(snap)

    def open(self, pid):
        h = self.k.OpenProcess(self.QUERY, False, pid)
        if not h:
            raise c.WinError(c.get_last_error())
        return h

    def close(self, h):
        self.k.CloseHandle(h)

    def identity(self, h):
        """(creation FILETIME, image path key) of a live process handle, or None if it has ended."""
        code = w.DWORD()
        if not self.k.GetExitCodeProcess(h, c.byref(code)) or code.value != 259:
            return None
        times = [w.FILETIME() for _ in range(4)]
        if not self.k.GetProcessTimes(h, *(c.byref(t) for t in times)):
            raise c.WinError(c.get_last_error())
        size, image = w.DWORD(32768), c.create_unicode_buffer(32768)
        if not self.k.QueryFullProcessImageNameW(h, 0, image, c.byref(size)):
            raise c.WinError(c.get_last_error())
        return (times[0].dwHighDateTime << 32 | times[0].dwLowDateTime, path_key(image.value))

    def in_job(self, h, job):
        value = w.BOOL()
        if not self.k.IsProcessInJob(h, job, c.byref(value)):
            raise c.WinError(c.get_last_error())
        return bool(value.value)

    def command_line(self, h):
        """ProcessCommandLineInformation (60, Windows 8.1+): the process's own command line, held in memory only."""
        need = w.ULONG(0)
        self.nt.NtQueryInformationProcess(h, 60, None, 0, c.byref(need))
        if not need.value:
            raise OSError("command line length unavailable")
        buf = c.create_string_buffer(need.value)
        status = self.nt.NtQueryInformationProcess(h, 60, buf, need, c.byref(need))
        if status != 0:
            raise OSError(f"NtQueryInformationProcess status {status & 0xFFFFFFFF:#x}")
        us = UNICODE_STRING.from_buffer(buf)
        return c.wstring_at(us.Buffer, us.Length // 2) if us.Buffer else ""

    def job_io(self, job):
        info = BasicAndIo()
        if not self.k.QueryInformationJobObject(job, 8, c.byref(info), c.sizeof(info), None):
            raise c.WinError(c.get_last_error())
        return {n: int(getattr(info, n)) for n in ("total", "active", "terminated", "read_ops", "write_ops",
                                                   "other_ops", "read_bytes", "write_bytes", "other_bytes")}

    # windows
    def desktop_window_owners(self, desktop):
        """[(owner pid, visible)] of the top-level windows on a desktop of this window station. No titles read."""
        h = self.u.OpenDesktopW(desktop, 0, False, 0x0001 | 0x0040)       # DESKTOP_READOBJECTS | DESKTOP_ENUMERATE
        if not h:
            raise c.WinError(c.get_last_error())
        out = []

        @self.enum_type
        def each(hwnd, _):
            pid = w.DWORD()
            self.u.GetWindowThreadProcessId(hwnd, c.byref(pid))
            out.append((int(pid.value), bool(self.u.IsWindowVisible(hwnd))))
            return True
        try:
            if not self.u.EnumDesktopWindows(h, each, 0) and not out:
                err = c.get_last_error()
                if err:
                    raise c.WinError(err)
            return out
        finally:
            self.u.CloseDesktop(h)

    # network
    def _table(self, fn, family, cls):
        size = w.DWORD(0)
        for _ in range(5):
            buf = c.create_string_buffer(max(size.value, 4))
            rc = fn(buf, c.byref(size), False, family, cls, 0)
            if rc == 0:
                return buf
            if rc != 122:                                                   # ERROR_INSUFFICIENT_BUFFER
                raise OSError(f"table call failed ({rc})")
        raise OSError("table kept growing")

    def tcp(self):
        """[(pid, state, local addr, local port, remote addr, remote port)] for IPv4 and IPv6."""
        out = []
        buf = self._table(self.ip.GetExtendedTcpTable, socket.AF_INET, 5)   # TCP_TABLE_OWNER_PID_ALL
        n = struct.unpack_from("<I", buf, 0)[0]
        for i in range(n):
            st, la, lp, ra, rp, pid = struct.unpack_from("<6I", buf, 4 + 24 * i)
            out.append((pid, st, socket.inet_ntop(socket.AF_INET, struct.pack("<I", la)), socket.ntohs(lp & 0xFFFF),
                        socket.inet_ntop(socket.AF_INET, struct.pack("<I", ra)), socket.ntohs(rp & 0xFFFF)))
        buf = self._table(self.ip.GetExtendedTcpTable, socket.AF_INET6, 5)
        n = struct.unpack_from("<I", buf, 0)[0]
        for i in range(n):
            off = 4 + 56 * i
            la, ra = buf.raw[off:off + 16], buf.raw[off + 24:off + 40]
            _, lp = struct.unpack_from("<2I", buf, off + 16)
            _, rp, st, pid = struct.unpack_from("<4I", buf, off + 40)
            out.append((pid, st, socket.inet_ntop(socket.AF_INET6, la), socket.ntohs(lp & 0xFFFF),
                        socket.inet_ntop(socket.AF_INET6, ra), socket.ntohs(rp & 0xFFFF)))
        return out

    def udp(self):
        """[(pid, local addr, local port)] for IPv4 and IPv6. A UDP socket has no remote in this table."""
        out = []
        buf = self._table(self.ip.GetExtendedUdpTable, socket.AF_INET, 1)   # UDP_TABLE_OWNER_PID
        n = struct.unpack_from("<I", buf, 0)[0]
        for i in range(n):
            la, lp, pid = struct.unpack_from("<3I", buf, 4 + 12 * i)
            out.append((pid, socket.inet_ntop(socket.AF_INET, struct.pack("<I", la)), socket.ntohs(lp & 0xFFFF)))
        buf = self._table(self.ip.GetExtendedUdpTable, socket.AF_INET6, 1)
        n = struct.unpack_from("<I", buf, 0)[0]
        for i in range(n):
            off = 4 + 28 * i
            _, lp, pid = struct.unpack_from("<3I", buf, off + 16)
            out.append((pid, socket.inet_ntop(socket.AF_INET6, buf.raw[off:off + 16]), socket.ntohs(lp & 0xFFFF)))
        return out

    # installs
    def install_records(self):
        """Names only: uninstall entries (machine, 32-bit, user), services, and the user's and machine's Run values."""
        import winreg
        out = {}
        keys = {
            "uninstall-machine": (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                                  winreg.KEY_WOW64_64KEY, "keys"),
            "uninstall-machine-32": (winreg.HKEY_LOCAL_MACHINE,
                                     r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                                     winreg.KEY_WOW64_32KEY, "keys"),
            "uninstall-user": (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", 0,
                               "keys"),
            "services": (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services", 0, "keys"),
            "run-user": (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0, "values"),
            "run-machine": (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                            winreg.KEY_WOW64_64KEY, "values"),
        }
        for label, (hive, sub, view, what) in keys.items():
            try:
                with winreg.OpenKey(hive, sub, 0, winreg.KEY_READ | view) as k:
                    names, i = [], 0
                    while True:
                        try:
                            names.append(winreg.EnumKey(k, i) if what == "keys" else winreg.EnumValue(k, i)[0])
                        except OSError:
                            break
                        i += 1
                    out[label] = sorted(names)
            except FileNotFoundError:
                out[label] = []
            except OSError as exc:
                out[label] = {"unreadable": error(exc)}
        return out


# ---- folders -------------------------------------------------------------------------------------------------------

def snapshot_root(root, *, hash_files, exclude=(), max_files=None, max_bytes=None):
    """{"files": {rel: [size, mtime_ns, sha256|None]}, "unreadable": [rel], "complete": bool, "reason": str}.

    Never follows a reparse point (a junction or symlink is recorded, not entered). Contents are hashed only when
    hash_files (the run's own roots); never stored."""
    root = Path(root)
    max_files = MAX_FILES if max_files is None else max_files
    max_bytes = MAX_HASH_BYTES if max_bytes is None else max_bytes
    out = {"files": {}, "unreadable": [], "reparse": [], "complete": True, "reason": ""}
    if not root.exists():
        out["missing"] = True
        return out
    budget, ex = max_bytes, [path_key(str(e)).lower() for e in exclude]

    def excluded(p):
        k = path_key(str(p)).lower()
        return any(k == e or k.startswith(e.rstrip("\\") + "\\") for e in ex)

    stack = [root]
    while stack:
        d = stack.pop()
        try:
            entries = list(os.scandir(d))
        except OSError:
            out["unreadable"].append(str(Path(d).relative_to(root)) or ".")
            continue
        for e in entries:
            p = Path(e.path)
            if excluded(p):
                continue
            rel = str(p.relative_to(root))
            try:
                st = e.stat(follow_symlinks=False)
                reparse = bool(getattr(st, "st_file_attributes", 0) & 0x400) or e.is_symlink()
            except OSError:
                out["unreadable"].append(rel)
                continue
            if reparse:
                out["reparse"].append(rel)
                continue
            if e.is_dir(follow_symlinks=False):
                stack.append(p)
                continue
            if len(out["files"]) >= max_files:
                out.update(complete=False, reason=f"more than {max_files} files")
                return out
            digest = None
            if hash_files:
                if st.st_size > budget:
                    out.update(complete=False, reason=f"more than {max_bytes} bytes to hash")
                    return out
                try:
                    h = hashlib.sha256()
                    with open(p, "rb") as f:
                        for chunk in iter(lambda: f.read(1 << 20), b""):
                            h.update(chunk)
                    digest = h.hexdigest()
                    budget -= st.st_size
                except OSError:
                    out["unreadable"].append(rel)
                    continue
            out["files"][rel] = [st.st_size, st.st_mtime_ns, digest]
    return out


def diff_roots(before, after):
    a, b = before["files"], after["files"]
    return {"added": sorted(set(b) - set(a)), "removed": sorted(set(a) - set(b)),
            "changed": sorted(k for k in set(a) & set(b) if a[k] != b[k])}


# ---- the verifier --------------------------------------------------------------------------------------------------

class Verifier:
    """Held by the harness beside its live job scope, from before launch until after cleanup.

        v = Verifier(run, scope)
        v.before()                     # before sandbox_window.start(..., job=scope)
        v.start_sampling(0.1)          # once the root birth is resumed
        v.gate()                       # before any input/CDP: refuse unless allow_interaction()
        v.stop_sampling()
        ... sandbox_window.close(name) ...
        v.after()                      # after cleanup, scope still held
        report = v.verdict()

    run: {"name": sandbox name, "profile_roots": [...], "scratch_roots": [...] (both run-owned, hashed),
          "watched_roots": [...] (metadata only, the repo and any user-profile paths the run names),
          "exclude": [...] (the harness's own receipts, under a watched root), "engine_images": [...],
          "allow_remote": [resolve_allowed(host, port), ...] (host, port, ips and DNS provenance; a bare [ip, port]
          has no provenance and is unknown), "allow_loopback": bool, "require_engine_report": bool,
          "births": [{"pid", "created", "exe"}] (the launcher's measured birth receipts, sandbox_window's manifest
          "owners"), "must_prove": [NOT_PROVEN keys this consumer needs proven; each one present refuses]}
    A member is explained only by measurement: it matches a birth receipt (pid, creation time, image path), or its
    recorded parent pid is an explained member created no later than it. Its role is read from its own command line
    (role_of). Nothing a caller says about a pid explains it.
    engine_report(): {"browser_pid": int, "user_data_folder": str, "processes": [{"pid": int, "kind": str}]} or
          None, read by the consumer from its actual WebView2 control (BrowserProcessId, UserDataFolder,
          GetProcessInfos). The verifier never reaches into the engine itself.
    """

    def __init__(self, run, scope, *, native=None, engine_report=None, clock=time.monotonic, wall=time.time):
        self.run = dict(run)
        self.run.setdefault("engine_images", list(ENGINE_IMAGES))
        self.run.setdefault("allow_remote", [])
        self.run.setdefault("allow_loopback", False)
        self.run.setdefault("watched_roots", [])
        self.run.setdefault("exclude", [])
        self.run.setdefault("must_prove", [])
        births = self.run.pop("births", []) or []
        self.scope, self.native = scope, native or Native()
        self.engine_report = engine_report
        self.clock, self.wall = clock, wall
        self.owned = [str(p) for p in self.run.get("profile_roots", []) + self.run.get("scratch_roots", [])]
        self.samples, self.findings = [], {k: [] for k in ("family", "windows", "network", "writes")}
        self.unknowns = {k: [] for k in self.findings}
        self.members = {}                      # pid -> {"created", "exe", "first", "last"}
        self.pre = self.post = None
        self._stop, self._thread, self._lock = threading.Event(), None, threading.Lock()
        self.interval = None
        self.reports = []
        self.births = []
        for b in births:
            self.add_birth(b)

    def add_birth(self, birth):
        """A launcher's measured birth receipt: {"pid": int, "created": FILETIME int, "exe": absolute path}. It explains
        a member only if the verifier's own reading of that member has the same creation time and image."""
        if not (isinstance(birth, dict) and type(birth.get("pid")) is int and type(birth.get("created")) is int
                and isinstance(birth.get("exe"), str) and ntpath.isabs(birth["exe"])):
            raise ValueError("a birth is the launcher's receipt: pid, created and an absolute exe")
        with self._lock:
            self.births.append({"pid": birth["pid"], "created": birth["created"], "exe": path_key(birth["exe"])})

    # bookkeeping
    def _bad(self, check_name, what):
        with self._lock:
            if what not in self.findings[check_name]:
                self.findings[check_name].append(what)

    def _unknown(self, check_name, what):
        with self._lock:
            if what not in self.unknowns[check_name]:
                self.unknowns[check_name].append(what)

    # outside the job: who names our profile?
    def outside_with_profile(self, members, procs=None):
        """-> (pids naming our profile outside the job, unreadable engine-named pids). Nothing is stored but pids."""
        n, images = self.native, {i.lower() for i in self.run["engine_images"]}
        named, unreadable = [], []
        for pid, _, image in (n.processes() if procs is None else procs):
            if pid in members or pid in (0, 4) or image.lower() not in images:
                continue
            try:
                h = n.open(pid)
            except OSError as exc:
                if getattr(exc, "winerror", None) != 87:          # 87: no such process now (it ended), not unknown
                    unreadable.append({"pid": pid, "image": image.lower()})
                continue
            try:
                if self.scope is not None and self.scope.handle and n.in_job(h, self.scope.handle):
                    continue                    # joined after our snapshot: the next sample lists it
                if names_root(n.command_line(h), self.run.get("profile_roots", [])):
                    named.append({"pid": pid, "image": image.lower()})
            except OSError:
                unreadable.append({"pid": pid, "image": image.lower()})
            finally:
                n.close(h)
        return named, unreadable

    def before(self):
        """Before launch: nothing holds our profile already; owned roots are empty or hashed; install records."""
        t = self.wall()
        pre = {"at": t}
        try:
            named, unreadable = self.outside_with_profile(set())
            pre["profile_holders"] = named
            pre["unreadable_engines"] = unreadable
            if named:
                self._bad("family", f"before launch, {len(named)} process(es) outside the job already named the "
                                    f"run's profile: an engine would be reused ({named})")
            if unreadable:
                self._unknown("family", f"before launch, {len(unreadable)} engine-named process(es) could not be "
                                        f"read to rule out our profile ({unreadable})")
        except OSError as exc:
            self._unknown("family", f"before launch, the process list failed: {error(exc)}")
        pre["owned"] = {r: snapshot_root(r, hash_files=True) for r in self.owned}
        pre["watched"] = {r: snapshot_root(r, hash_files=False, exclude=self.owned + self.run["exclude"])
                          for r in self.run["watched_roots"]}
        try:
            pre["installs"] = self.native.install_records()
        except OSError as exc:
            pre["installs"] = {"unreadable": error(exc)}
        self.pre = pre
        return pre

    def sample(self):
        """One instant: job members, outside engines, windows on both desktops, sockets. -> the sample record."""
        n, s = self.native, {"t": self.clock(), "at": self.wall()}
        # 1. the job's own member list (bounded; incomplete raises and is unknown)
        try:
            snap = self.scope.snapshot()
            s["job"] = snap
        except Exception as exc:
            self._unknown("family", f"job membership list unavailable at a sample: {error(exc)}")
            s["job_error"] = error(exc)
            self.samples.append(s)
            return s
        members = set(snap["pids"])
        try:
            procs = n.processes()
        except OSError as exc:
            procs = None
            self._unknown("family", f"process list failed at a sample: {error(exc)}")
        parents = {pid: (ppid, image) for pid, ppid, image in procs or []}
        for pid in snap["pids"]:
            try:
                h = n.open(pid)
            except OSError as exc:
                if getattr(exc, "winerror", None) != 87 and pid not in self.members:
                    self._unknown("family", f"job member {pid} could not be opened to read its identity")
                continue
            try:
                ident = n.identity(h)
                if ident is None:
                    continue                    # ended since the list was taken
                if not n.in_job(h, self.scope.handle):
                    self._unknown("family", f"pid {pid} from the job list is not in the job on its own handle "
                                            f"(reused between list and open)")
                    continue
                rec = self.members.get(pid)
                if rec is None:
                    # first sight: parent pid (Toolhelp, as recorded at its creation) and role (its own command line)
                    try:
                        role = role_of(ntpath.basename(ident[1]), n.command_line(h))
                    except OSError:
                        role = None
                    rec = self.members[pid] = {"created": ident[0], "exe": ntpath.basename(ident[1]),
                                               "path": ident[1], "ppid": (parents.get(pid) or (None,))[0],
                                               "role": role, "first": s["t"]}
                elif rec["created"] != ident[0]:
                    self._unknown("family", f"pid {pid} changed identity while in the job list")
                rec["last"] = s["t"]
            except OSError as exc:
                self._unknown("family", f"job member {pid} identity unreadable: {error(exc)}")
            finally:
                n.close(h)
        # 2. outside the job, naming our profile
        try:
            if procs is None:
                raise OSError("process list unavailable")
            named, unreadable = self.outside_with_profile(members, procs)
            for p in named:
                self._bad("family", f"{p['image']} pid {p['pid']} names the run's profile outside the job "
                                    f"(out-of-job or reused engine)")
            for p in unreadable:
                self._unknown("family", f"{p['image']} pid {p['pid']} outside the job could not be read to rule out "
                                        f"our profile")
            s["outside_named"] = [p["pid"] for p in named]
        except OSError as exc:
            self._unknown("family", f"process list failed at a sample: {error(exc)}")
            named = []
        ours = members | {p["pid"] for p in named}
        # 3. windows: the sandbox desktop (expected), Default (must hold none of ours)
        sandbox = f"agora-sandbox-{self.run['name']}"
        for desk in (sandbox, "Default"):
            try:
                owners = n.desktop_window_owners(desk)
                mine = [(pid, vis) for pid, vis in owners if pid in ours]
                s.setdefault("windows", {})[desk] = {"total": len(owners), "ours": len(mine),
                                                     "ours_visible": sum(1 for _, v in mine if v)}
                if desk == "Default" and mine:
                    self._bad("windows", f"{len(mine)} window(s) of job/profile processes on the Default desktop "
                                         f"(pids {sorted({p for p, _ in mine})})")
            except OSError as exc:
                self._unknown("windows", f"desktop {desk} could not be enumerated: {error(exc)}")
        # 4. sockets
        try:
            tcp = [r for r in n.tcp() if r[0] in ours]
            udp = [r for r in n.udp() if r[0] in ours]
            s["tcp"], s["udp"] = [list(r) for r in tcp], [list(r) for r in udp]
            self._judge_net(tcp, udp)
        except OSError as exc:
            self._unknown("network", f"socket tables unreadable at a sample: {error(exc)}")
        # 5. the consumer's engine report
        if self.engine_report is not None:
            try:
                rep = self.engine_report()
            except Exception as exc:
                rep = None
                self._unknown("family", f"engine report failed: {error(exc)}")
            if rep is not None:
                self.reports.append(rep)
                self._judge_engine(rep, members)
        self.samples.append(s)
        return s

    def _allow(self):
        """{(ip, port): host} from entries that keep their provenance; an entry without it is unknown, never allowed."""
        allow = {}
        for e in self.run["allow_remote"]:
            if (isinstance(e, dict) and e.get("host") and type(e.get("port")) is int and e.get("ips")
                    and e.get("resolved_at") and e.get("how")):
                for ip in e["ips"]:
                    allow[(ip, e["port"])] = e["host"]
            else:
                self._unknown("network", f"allowlist entry without host/port/DNS provenance, not used: {e!r}"[:200])
        return allow

    def _judge_net(self, tcp, udp):
        allow = self._allow()
        loop = self.run["allow_loopback"]
        for pid, st, la, lp, ra, rp in tcp:
            where = f"pid {pid} {TCP_STATES.get(st, st)} {la}:{lp} -> {ra}:{rp}"
            if st == LISTEN:
                if not is_loopback(la):
                    self._bad("network", f"listening beyond loopback: {where}")
                elif not loop:
                    self._bad("network", f"listening on loopback, not allowed for this run: {where}")
                continue
            if is_unspecified(ra):
                continue
            if is_loopback(ra):
                if not loop:
                    self._bad("network", f"loopback connection, not allowed for this run: {where}")
                continue
            if (ra, rp) not in allow:
                self._bad("network", f"remote endpoint not in the allowlist: {where}")
        for pid, la, lp in udp:
            if is_loopback(la):
                if not loop:
                    self._bad("network", f"UDP bound on loopback, not allowed for this run: pid {pid} {la}:{lp}")
            else:
                self._unknown("network", f"UDP bound beyond loopback (its remotes are not observable): pid {pid} "
                                         f"{la}:{lp}")

    def _judge_engine(self, rep, members):
        bp, folder = rep.get("browser_pid"), rep.get("user_data_folder")
        if type(bp) is not int or bp <= 0:
            self._unknown("family", "engine report has no browser process id")
        elif bp not in members:
            self._bad("family", f"the engine's browser process {bp} is not in the job (reused or brokered engine)")
        if not folder:
            self._unknown("family", "engine report has no effective user data folder")
        elif not under(folder, self.run.get("profile_roots", [])):
            self._bad("family", "the engine's effective user data folder is not the run's profile")
        def norm(kind):
            return re.sub(r"[^a-z]", "", str(kind or "").lower()).replace("process", "")
        for p in rep.get("processes") or []:
            if p.get("pid") not in members:
                self._bad("family", f"engine process {p.get('pid')} ({p.get('kind')}) is not in the job")
            elif p.get("pid") in self.members and self.members[p["pid"]]["role"] is not None and \
                    norm(p.get("kind")) != norm(self.members[p["pid"]]["role"]):
                self._unknown("family", f"engine process {p['pid']} is reported as {p.get('kind')!r} but its own "
                                        f"command line says {self.members[p['pid']]['role']!r}")

    def start_sampling(self, interval=0.1):
        self.interval = interval

        def loop():
            while not self._stop.is_set():
                try:
                    self.sample()
                except Exception as exc:               # a sampler that stopped proves nothing after it stopped
                    self._unknown("family", f"sampler stopped: {error(exc)}")
                    return
                self._stop.wait(interval)
        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def stop_sampling(self):
        self._stop.set()
        if self._thread:
            self._thread.join(5)
            if self._thread.is_alive():
                self._unknown("family", "sampler did not stop within 5 s")

    def gate(self):
        """One fresh sample, then the verdict: the consumer refuses interaction unless allow_interaction()."""
        self.sample()
        return self.verdict(final=False)

    def after(self):
        """After cleanup (scope still held): survivors naming our profile, the job's totals, folders, installs."""
        post = {"at": self.wall()}
        try:
            named, unreadable = self.outside_with_profile(set())
            post["survivors"] = named
            if named:
                self._bad("family", f"after cleanup, {len(named)} process(es) still name the run's profile "
                                    f"outside the job: {named}")
            if unreadable:
                self._unknown("family", f"after cleanup, {len(unreadable)} engine-named process(es) could not be "
                                        f"read: {unreadable}")
        except OSError as exc:
            self._unknown("family", f"after cleanup, the process list failed: {error(exc)}")
        try:
            post["job"] = self.scope.snapshot()
            post["io"] = self.native.job_io(self.scope.handle)
        except Exception as exc:
            self._unknown("writes", f"job accounting unavailable after cleanup: {error(exc)}")
        post["owned"] = {r: snapshot_root(r, hash_files=True) for r in self.owned}
        post["watched"] = {r: snapshot_root(r, hash_files=False, exclude=self.owned + self.run["exclude"])
                           for r in self.run["watched_roots"]}
        try:
            post["installs"] = self.native.install_records()
        except OSError as exc:
            post["installs"] = {"unreadable": error(exc)}
        self.post = post
        return post

    # ---- verdicts ----
    def verdict(self, final=True):
        """final=False (the gate, mid-run): family, windows and network so far; writes are compared only after
        cleanup and say so. allow_interaction is judged on the checks that can be judged at that moment."""
        out = {"phase": "final" if final else "gate", "family": self._family(final), "windows": self._windows(),
               "network": self._network()}
        out["writes"] = self._writes() if final else check(UNKNOWN, "not compared yet: writes are compared after "
                                                                    "cleanup", {}, [], NOT_PROVEN["writes"])
        judged = ("family", "windows", "network", "writes") if final else ("family", "windows", "network")
        # c10251: a limit this consumer needs proven refuses interaction while any judged check still lists it; a key
        # the verifier does not know refuses too (fail closed on a typo)
        need = list(self.run["must_prove"])
        out["blocking_limits"] = sorted({k for k in need if k not in ALL_LIMITS} |
                                        {k for c in judged for k in out[c]["not_proven_keys"] if k in need})
        out["allow_interaction"] = (all(out[k]["status"] == OBSERVED for k in judged)
                                    and not out["blocking_limits"])
        out["coverage"] = self._coverage()
        return out

    def _coverage(self):
        ts = [s["t"] for s in self.samples if "job" in s]
        gaps = [b - a for a, b in zip(ts, ts[1:])]
        return {"samples": len(ts), "failed_samples": len(self.samples) - len(ts), "interval_requested": self.interval,
                "span_s": round(ts[-1] - ts[0], 3) if ts else 0, "max_gap_s": round(max(gaps), 3) if gaps else None}

    def _status(self, name, extra_unknown=()):
        unk = self.unknowns[name] + list(extra_unknown)
        return (VIOLATION if self.findings[name] else UNKNOWN if unk else OBSERVED), unk

    def _family(self, final=True):
        extra = []
        good = [s for s in self.samples if "job" in s]
        if not good:
            extra.append("no job membership sample was taken")
        if self.pre is None:
            extra.append("no before-launch observation (an engine already holding the profile was not ruled out)")
        if final and self.post is None:
            extra.append("no after-cleanup observation (survivors not ruled out)")
        if self.run.get("require_engine_report") and not self.reports:
            extra.append("the consumer's engine report (BrowserProcessId, UserDataFolder, process list) was "
                         "required and never given")
        how, why = self.provenance()
        for pid in sorted(why):
            extra.append(f"job member {pid} ({self.members[pid]['exe']}, {self.members[pid]['role']}) has no measured "
                         f"provenance: {why[pid]}")
        status, unk = self._status("family", extra)
        members = [{"pid": p, "created": m["created"], "exe": m["exe"], "role": m["role"], "ppid": m["ppid"],
                    "provenance": how.get(p)} for p, m in sorted(self.members.items())]
        return check(status, f"{len(members)} distinct job member(s) over {len(good)} sample(s); outside processes "
                             f"named {self.run['engine_images']} checked for the profile before launch, at every "
                             f"sample and after cleanup", {"members": members, "reports": len(self.reports)},
                     self.findings["family"] + unk, NOT_PROVEN["family"])

    def provenance(self):
        """-> ({pid: how it is explained}, {pid: why it is not}), by measurement only. A birth explains the member whose
        pid, creation time and image path the verifier itself read; a child is explained when its recorded parent pid
        is an explained member created no later than it (a later-created holder of that pid is a reuse, not the
        parent). Parent pids come from Toolhelp; roles from each member's own command line."""
        how, why = {}, {}
        for pid, m in self.members.items():
            for b in self.births:
                if b["pid"] == pid:
                    if (b["created"], b["exe"]) == (m["created"], path_key(m["path"])):
                        how[pid] = "birth receipt (pid, creation time and image match)"
                    else:
                        why[pid] = "a birth receipt names this pid but its creation time or image differ"
        changed = True
        while changed:
            changed = False
            for pid, m in self.members.items():
                if pid in how or pid in why:
                    continue
                parent = self.members.get(m["ppid"])
                if parent is not None and m["ppid"] in how and parent["created"] <= m["created"]:
                    how[pid] = f"child of {m['ppid']} ({parent['exe']}, {parent['role']}), created after it"
                    changed = True
        for pid, m in self.members.items():
            if pid in how or pid in why:
                continue
            parent = self.members.get(m["ppid"])
            if m["ppid"] is None:
                why[pid] = "its parent pid was not read"
            elif parent is None:
                why[pid] = f"its recorded parent {m['ppid']} was never seen as a job member"
            elif parent["created"] > m["created"]:
                why[pid] = f"pid {m['ppid']} was created after it (a reused pid, not its parent)"
            else:
                why[pid] = f"its parent {m['ppid']} is itself unexplained"
        return how, why

    def _windows(self):
        extra = [] if any("windows" in s for s in self.samples) else ["no desktop was enumerated"]
        status, unk = self._status("windows", extra)
        seen = {}
        for s in self.samples:
            for d, v in (s.get("windows") or {}).items():
                seen.setdefault(d, {"samples": 0, "max_ours": 0})
                seen[d]["samples"] += 1
                seen[d]["max_ours"] = max(seen[d]["max_ours"], v["ours"])
        return check(status, "top-level window owners on the sandbox desktop and on Default, owner PIDs only, at "
                             "every sample", seen, self.findings["windows"] + unk, NOT_PROVEN["windows"])

    def _network(self):
        extra = [] if any("tcp" in s for s in self.samples) else ["no socket table was read"]
        status, unk = self._status("network", extra)
        endpoints = sorted({(r[4], r[5]) for s in self.samples for r in s.get("tcp", [])
                            if r[1] != LISTEN and not is_unspecified(r[4])})
        allow = {}
        for e in self.run["allow_remote"]:
            if isinstance(e, dict) and type(e.get("port")) is int:
                for ip in e.get("ips") or []:
                    allow[(ip, e["port"])] = e.get("host")
        cov = self._coverage()
        return check(status, f"TCP endpoints and UDP bindings of job members (and of out-of-job profile holders) at "
                             f"{cov['samples']} sample(s), requested every {self.interval} s, largest gap "
                             f"{cov['max_gap_s']} s", {"remote_endpoints": [
                                 [ip, port, ("loopback" if is_loopback(ip) else allow.get((ip, port)))]
                                 for ip, port in endpoints],
                                                       "allow_remote": self.run["allow_remote"],
                                                       "allow_loopback": self.run["allow_loopback"]},
                     self.findings["network"] + unk, NOT_PROVEN["network"])

    def _writes(self):
        extra, ev = [], {}
        if self.pre is None or self.post is None:
            extra.append("no before or no after snapshot")
            status, unk = self._status("writes", extra)
            return check(status, "nothing compared", ev, self.findings["writes"] + unk, NOT_PROVEN["writes"])
        for kind in ("owned", "watched"):
            for root, b in self.pre[kind].items():
                a = self.post[kind].get(root) or {}
                for snap, when in ((b, "before"), (a, "after")):
                    if not snap.get("complete", False):
                        extra.append(f"{kind} root {root} {when}: incomplete ({snap.get('reason')})")
                    if snap.get("unreadable"):
                        extra.append(f"{kind} root {root} {when}: {len(snap['unreadable'])} unreadable entr(ies)")
                d = diff_roots(b, a)
                ev.setdefault(kind, {})[root] = {k: (v[:50] if kind == "owned" else len(v)) for k, v in d.items()}
                if kind == "watched" and any(d.values()):
                    self._bad("writes", f"changed outside the run's own roots, under {root}: "
                                        f"{', '.join(f'{len(v)} {k}' for k, v in d.items() if v)} (attribution not "
                                        f"measured)")
                    ev["watched"][root]["paths"] = (d["added"] + d["changed"] + d["removed"])[:20]
        bi, ai = self.pre.get("installs") or {}, self.post.get("installs") or {}
        for label in sorted(set(bi) | set(ai)):
            x, y = bi.get(label), ai.get(label)
            if not isinstance(x, list) or not isinstance(y, list):
                extra.append(f"install record {label} unreadable")
                continue
            new = sorted(set(y) - set(x))
            if new:
                self._bad("writes", f"new install record(s) in {label}: {new}")
        ev["io"] = (self.post or {}).get("io")
        if ev["io"] is None:
            extra.append("job I/O accounting not read")
        status, unk = self._status("writes", extra)
        return check(status, "hashes of the run's own roots, metadata of the named roots, install records, and the "
                             "job's I/O totals, before and after", ev, self.findings["writes"] + unk,
                     NOT_PROVEN["writes"])
