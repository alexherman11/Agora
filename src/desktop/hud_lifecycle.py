"""Home-base lifecycle: conservative observations, two misses, and Windows identity.

No process enumeration or Win32 calls happen at import. Policy tests use copies and
fake inventories; the native adapter is shared by the supervisor and hud.py.
"""
from dataclasses import dataclass
import hashlib
import json
import ntpath
import subprocess
from urllib.parse import urlsplit


def path_key(value):
    return ntpath.normcase(ntpath.normpath(str(value)))


def scope_key(world, door):
    parsed = urlsplit(door)
    host = parsed.hostname or ""
    if host.lower() in ("localhost", "::1"):
        host = "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return f"{world}|{parsed.scheme.lower()}://{host.lower()}:{port}{parsed.path.rstrip('/')}"


def mutex_name(world, door):
    return "Local\\Agora.HomeBase." + hashlib.sha256(scope_key(world, door).encode()).hexdigest()


def pid_path(state, world, door):
    if scope_key(world, door) == scope_key("frontier", "http://127.0.0.1:8794"):
        return state / "hud.pid"                 # compatible with existing launchers
    return state / ("hud-" + hashlib.sha256(scope_key(world, door).encode()).hexdigest()[:16] + ".pid")


def read_pid(path):
    """None means unreadable/malformed, 0 absent, positive means recorded pid."""
    try:
        value = path.read_text().strip()
        return int(value) if value.isdigit() and int(value) > 0 else None
    except FileNotFoundError:
        return 0
    except OSError:
        return None


def remove_own_pid(path, pid):
    if read_pid(path) == pid:
        path.unlink(missing_ok=True)


@dataclass(frozen=True)
class Process:
    pid: int
    parent: int
    created: int                       # native GetProcessTimes FILETIME, not a rounded display time
    exe: str
    argv: tuple
    healthy: bool = False              # responsive native "Agora home base" window


def same_script(argument, expected):
    """Exact script path, including sibling worker checkouts of this repository."""
    argument, expected = path_key(argument), path_key(expected)
    if not ntpath.isabs(argument):
        return False
    def family(value):
        before, marker, after = value.partition("\\.worktrees\\")
        return before + "\\" + after.split("\\", 1)[1] if marker and "\\" in after else value
    return family(argument) == family(expected)


def script_args(proc, script):
    # Skip only interpreter switches without an operand; -c/-m and unknown
    # switches must never turn a script mentioned in arbitrary words into a host.
    args = proc.argv[1:]
    while args and args[0] in ("-u", "-B", "-E", "-s", "-S", "-I", "-O", "-OO"):
        args = args[1:]
    return args[1:] if args and same_script(args[0], script) else None


def option(args, name, default):
    for i, arg in enumerate(args):
        if arg == name:
            return args[i + 1] if i + 1 < len(args) else None
        if arg.startswith(name + "="):
            return arg[len(name) + 1:]
    return default


@dataclass(frozen=True)
class Scope:
    hud: str
    keeper: str
    world: str = "frontier"
    door: str = "http://127.0.0.1:8794"

    def hosts(self, processes):
        found = []
        for p in processes:
            args = script_args(p, self.hud)
            if args is not None and "--stop" not in args:
                door = option(args, "--door", "http://127.0.0.1:8794")
                if (option(args, "--world", "frontier") == self.world and door
                        and scope_key(self.world, door) == scope_key(self.world, self.door)):
                    found.append(p)
        return found

    def keepers(self, processes):
        found = []
        for p in processes:
            args = script_args(p, self.keeper)
            if args and args[0] == self.world and str(option(args, "--port", "8794")) == str(urlsplit(self.door).port):
                found.append(p)
        return found


def leaves(hosts):
    """The venv launcher and its interpreter are one host, not two."""
    parents = {p.parent for p in hosts}
    return [p for p in hosts if p.pid not in parents]


def other_hosts(processes, scope, pid, parent):
    """Exclude our own launcher, never an existing interpreter which spawned us."""
    me = next((p for p in processes if p.pid == pid), None)
    return [p for p in scope.hosts(processes) if p.pid != pid and not (
        me is not None and p.pid == parent and me.parent == parent
        and p.argv[1:] == me.argv[1:] and path_key(p.exe) != path_key(me.exe)
        and ntpath.basename(path_key(p.exe)) == ntpath.basename(path_key(me.exe))
        and p.created <= me.created)]


class Misses:
    def __init__(self, seconds=5):
        self.seconds, self.first = seconds, None

    def check(self, missing, now):
        if not missing:
            self.first = None
            return False
        if self.first is None:
            self.first = now
            return False
        if now - self.first < self.seconds:
            return False
        self.first = None
        return True


class Monitor:
    """Each tick returns a recheck delay. Unknown resets consecutive misses."""
    def __init__(self, scope):
        self.scope = scope
        self.hud_misses, self.keeper_misses = Misses(), Misses()
        self.cooldown = 0
        self.said = None

    def tick(self, processes, pid, door_ready, now, *, start, end, healthy, log):
        def say(message):
            if message != self.said:
                log(message)
                self.said = message

        if processes is None or pid is None:
            self.hud_misses.check(False, now)
            self.keeper_misses.check(False, now)
            say("unknown: process inventory or hud pid record unreadable; do nothing and recheck")
            return 5
        hosts = self.scope.hosts(processes)
        keepers = self.scope.keepers(processes)
        # A live pid which cannot be reconciled with the command-line inventory
        # is not evidence of absence. A reused pid known to be unrelated is stale.
        recorded = next((p for p in processes if p.pid == pid), None)
        if recorded and recorded not in hosts and script_args(recorded, self.scope.hud) is not None:
            self.hud_misses.check(False, now)
            say("unknown: hud pid belongs to a different scope; preserving the record")
            return 5
        if self.keeper_misses.check(not door_ready and not keepers, now):
            say("two misses: the desk is not answering and no keeper runs; starting keeper")
            start("keeper")
        if hosts:
            self.hud_misses.check(False, now)
            actual = leaves(hosts)
            if not door_ready or not keepers:
                say("unknown: keeper/desk restarting; existing home base left alone")
                return 5
            good = sorted((p for p in actual if p.healthy), key=lambda p: (p.created, p.pid), reverse=True)
            if len(actual) > 1 and good:
                survivor = good[0]
                for extra in actual:
                    if extra == survivor:
                        continue
                    # Revalidate the survivor before EVERY victim, so a dead
                    # survivor cannot cost us the only remaining healthy host.
                    if not healthy(survivor):
                        say("unknown: duplicate survivor no longer healthy; cleanup deferred")
                        return 5
                    result = end(extra)
                    log(f"duplicate home base: keep {survivor.pid} created={survivor.created}; "
                        f"end {extra.pid} created={extra.created}: {result}")
            elif len(actual) > 1:
                say("unknown: multiple hosts but none confirmed healthy; cleanup deferred")
                return 5
            say("home base running; hud pid record preserved")
            return 60
        if not door_ready or not keepers:
            self.hud_misses.check(False, now)
            say("unknown: keeper/desk restarting or not ready; home base left alone")
            return 5
        if now < self.cooldown:
            self.hud_misses.check(False, now)
            return 5
        if self.hud_misses.check(True, now):
            say("two misses: no home base process for this world; starting hud (pid record preserved)")
            start("hud")
            self.cooldown = now + 30
        else:
            say("first miss: no home base process; preserving hud pid and rechecking")
        return 5


class Windows:
    """Typed Win32 calls. Never terminate by name or a bare/reused pid."""
    def __init__(self):
        import ctypes as c
        from ctypes import wintypes as w
        self.c, self.w = c, w
        self.k = c.WinDLL("kernel32", use_last_error=True)
        self.u = c.WinDLL("user32", use_last_error=True)
        self.shell = c.WinDLL("shell32", use_last_error=True)
        self.enum_type = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
        for dll, name, result, args in [
            (self.k, "OpenProcess", w.HANDLE, [w.DWORD, w.BOOL, w.DWORD]),
            (self.k, "CloseHandle", w.BOOL, [w.HANDLE]),
            (self.k, "GetExitCodeProcess", w.BOOL, [w.HANDLE, c.POINTER(w.DWORD)]),
            (self.k, "GetProcessTimes", w.BOOL, [w.HANDLE] + [c.POINTER(w.FILETIME)] * 4),
            (self.k, "QueryFullProcessImageNameW", w.BOOL, [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)]),
            (self.k, "TerminateProcess", w.BOOL, [w.HANDLE, w.UINT]),
            (self.k, "WaitForSingleObject", w.DWORD, [w.HANDLE, w.DWORD]),
            (self.k, "CreateMutexW", w.HANDLE, [c.c_void_p, w.BOOL, w.LPCWSTR]),
            (self.k, "LocalFree", c.c_void_p, [c.c_void_p]),
            (self.shell, "CommandLineToArgvW", c.POINTER(w.LPWSTR), [w.LPCWSTR, c.POINTER(c.c_int)]),
            (self.u, "EnumWindows", w.BOOL, [self.enum_type, w.LPARAM]),
            (self.u, "GetWindowTextW", c.c_int, [w.HWND, w.LPWSTR, c.c_int]),
            (self.u, "GetWindowThreadProcessId", w.DWORD, [w.HWND, c.POINTER(w.DWORD)]),
            (self.u, "SendMessageTimeoutW", w.LPARAM,
             [w.HWND, w.UINT, w.WPARAM, w.LPARAM, w.UINT, w.UINT, c.POINTER(c.c_size_t)]),
        ]:
            fn = getattr(dll, name)
            fn.restype, fn.argtypes = result, args

    def argv(self, command):
        count = self.c.c_int()
        pointer = self.shell.CommandLineToArgvW(command, self.c.byref(count))
        if not pointer:
            raise OSError("CommandLineToArgvW failed")
        try:
            return tuple(pointer[i] for i in range(count.value))
        finally:
            self.k.LocalFree(pointer)

    def of_handle(self, handle):
        c, w = self.c, self.w
        code = w.DWORD()
        if not self.k.GetExitCodeProcess(handle, c.byref(code)) or code.value != 259:
            return None
        times = [w.FILETIME() for _ in range(4)]
        if not self.k.GetProcessTimes(handle, *(c.byref(t) for t in times)):
            return None
        size, image = w.DWORD(32768), c.create_unicode_buffer(32768)
        if not self.k.QueryFullProcessImageNameW(handle, 0, image, c.byref(size)):
            return None
        return (times[0].dwHighDateTime << 32 | times[0].dwLowDateTime, path_key(image.value))

    def identity(self, pid):
        handle = self.k.OpenProcess(0x1000, False, pid)
        if not handle:
            return None
        try:
            return self.of_handle(handle)
        finally:
            self.k.CloseHandle(handle)

    def healthy(self, proc):
        if self.identity(proc.pid) != (proc.created, path_key(proc.exe)):
            return False
        c, w, found = self.c, self.w, []
        @self.enum_type
        def visit(hwnd, unused):
            pid = w.DWORD()
            self.u.GetWindowThreadProcessId(hwnd, c.byref(pid))
            if pid.value == proc.pid:
                title = c.create_unicode_buffer(256)
                self.u.GetWindowTextW(hwnd, title, len(title))
                result = c.c_size_t()
                if title.value == "Agora home base" and self.u.SendMessageTimeoutW(
                        hwnd, 0, 0, 0, 0x2 | 0x20, 250, c.byref(result)):  # WM_NULL, ABORTIFHUNG|ERRORONEXIT
                    found.append(hwnd)
            return True
        return bool(self.u.EnumWindows(visit, 0) and found)

    def end(self, proc):
        # One handle is used for identity AND termination; no check/kill PID race.
        handle = self.k.OpenProcess(0x1000 | 0x1 | 0x100000, False, proc.pid)
        if not handle:
            return "refused: cannot open verified process"
        try:
            if self.of_handle(handle) != (proc.created, path_key(proc.exe)):
                return "refused: process identity changed"
            if not self.k.TerminateProcess(handle, 0):
                return "refused: TerminateProcess failed"
            return "ended" if self.k.WaitForSingleObject(handle, 3000) == 0 else "termination pending"
        finally:
            self.k.CloseHandle(handle)


class Mutex:
    def __init__(self, native, name):
        self.native, self.name, self.handle = native, name, None

    def acquire(self):
        c = self.native.c
        c.set_last_error(0)
        handle = self.native.k.CreateMutexW(None, False, self.name)
        if not handle:
            raise OSError(c.get_last_error(), "cannot create home-base mutex")
        if c.get_last_error() == 183:             # ERROR_ALREADY_EXISTS: close only OUR handle
            self.native.k.CloseHandle(handle)
            return False
        self.handle = handle
        return True

    def close(self):
        if self.handle:
            self.native.k.CloseHandle(self.handle)
            self.handle = None


# CreationDate has microsecond precision. Compare it with the native FILETIME
# before trusting the command line; retain the FULL native value for termination.
INVENTORY = r"""
$ErrorActionPreference = 'Stop'
$rows = @(Get-CimInstance Win32_Process -Filter "Name like 'python%'" | ForEach-Object {
    if (-not $_.CommandLine -or -not $_.ExecutablePath -or -not $_.CreationDate) { throw 'incomplete process row' }
    [PSCustomObject]@{pid=$_.ProcessId; parent=$_.ParentProcessId; exe=$_.ExecutablePath;
        created=$_.CreationDate.ToUniversalTime().ToFileTimeUtc(); command=$_.CommandLine}
})
ConvertTo-Json -InputObject $rows -Compress
"""


def inventory(native, run=subprocess.run):
    """None is unknown, never an empty/failed process listing disguised as absence."""
    try:
        result = run(["powershell", "-NoProfile", "-NonInteractive", "-Command", INVENTORY],
                     capture_output=True, text=True, timeout=30, creationflags=0x08000000)
        if result.returncode:
            return None
        rows = json.loads(result.stdout)
        if not isinstance(rows, list):
            return None
        processes = []
        for row in rows:
            pid = int(row["pid"])
            identity = native.identity(pid)
            if (identity is None or abs(identity[0] - int(row["created"])) >= 10
                    or identity[1] != path_key(row["exe"])):
                return None                     # raced an exit/reuse; recheck, don't guess
            if ntpath.basename(identity[1]) not in ("python.exe", "pythonw.exe"):
                return None
            proc = Process(pid, int(row["parent"]), identity[0], identity[1], native.argv(row["command"]))
            processes.append(proc)
        return processes
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        return None


def with_health(processes, scope, native):
    if processes is None:
        return None
    from dataclasses import replace
    hosts = leaves(scope.hosts(processes))
    return [replace(p, healthy=native.healthy(p)) if p in hosts else p for p in processes]
