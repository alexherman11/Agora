"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

Read-only Windows desktop telemetry; standard library only, no UI or workers.

CPU's first call deliberately waits 100 ms; subsequent calls are delta samples.
Network rates are interface-counter sums (virtual interfaces can double-count).
GB/MB/KB display units use powers of 1024. Failed readings are None.
"""

import ctypes as C
from ctypes import wintypes as W
from functools import wraps
import json
import ntpath
import threading
import time
import uuid


def _safe(method):
    @wraps(method)
    def call(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except Exception:
            return None
    return call


def _bind(dll, name, result, *args):
    fn = getattr(dll, name)
    fn.restype, fn.argtypes = result, args
    return fn


# Private DLL objects: never mutate ctypes.windll's shared function prototypes.
_kernel = C.WinDLL("kernel32", use_last_error=True)
_user = C.WinDLL("user32", use_last_error=True)
_ip = C.WinDLL("iphlpapi")
_dwm = C.WinDLL("dwmapi")
_P = C.c_void_p
_U64 = C.c_ulonglong
_HRESULT = C.c_long


class _GUID(C.Structure):
    _fields_ = [("data1", W.DWORD), ("data2", W.WORD),
                ("data3", W.WORD), ("data4", W.BYTE * 8)]

    @classmethod
    def parse(cls, value):
        return cls.from_buffer_copy(uuid.UUID(value).bytes_le)


class _Memory(C.Structure):
    _fields_ = [("length", W.DWORD), ("load", W.DWORD)] + [
        (name, _U64) for name in ("total", "available", "total_page",
                                  "available_page", "total_virtual",
                                  "available_virtual", "extended")]


class _Power(C.Structure):
    _fields_ = [("ac", W.BYTE), ("flags", W.BYTE), ("pct", W.BYTE),
                ("reserved", W.BYTE), ("life", W.DWORD), ("full", W.DWORD)]


class _IfRow(C.Structure):
    # netioapi.h MIB_IF_ROW2: retain native alignment, including flags padding.
    _fields_ = [("luid", _U64), ("index", W.ULONG), ("guid", _GUID),
                ("alias", W.WCHAR * 257), ("description", W.WCHAR * 257),
                ("address_length", W.ULONG), ("address", W.BYTE * 32),
                ("permanent_address", W.BYTE * 32)] + [
        (name, W.ULONG) for name in ("mtu", "type", "tunnel", "media",
                                   "physical_media", "access", "direction")
    ] + [("flags", W.BYTE), ("status", C.c_int), ("admin", C.c_int),
         ("connection_state", C.c_int), ("network_guid", _GUID),
         ("connection_type", C.c_int)] + [
        (name, _U64) for name in ("tx_speed", "rx_speed", "in_octets",
            "in_unicast", "in_nonunicast", "in_discards", "in_errors",
            "in_unknown", "in_unicast_octets", "in_multicast_octets",
            "in_broadcast_octets", "out_octets", "out_unicast",
            "out_nonunicast", "out_discards", "out_errors",
            "out_unicast_octets", "out_multicast_octets",
            "out_broadcast_octets", "out_queue")]


class _IfTable(C.Structure):
    _fields_ = [("count", W.ULONG), ("rows", _IfRow * 1)]


_system_times = _bind(_kernel, "GetSystemTimes", W.BOOL,
                      C.POINTER(W.FILETIME), C.POINTER(W.FILETIME), C.POINTER(W.FILETIME))
_memory = _bind(_kernel, "GlobalMemoryStatusEx", W.BOOL, C.POINTER(_Memory))
_power = _bind(_kernel, "GetSystemPowerStatus", W.BOOL, C.POINTER(_Power))
_get_table = _bind(_ip, "GetIfTable2", W.ULONG, C.POINTER(_P))
_free_table = _bind(_ip, "FreeMibTable", None, _P)
_open_process = _bind(_kernel, "OpenProcess", W.HANDLE, W.DWORD, W.BOOL, W.DWORD)
_close = _bind(_kernel, "CloseHandle", W.BOOL, W.HANDLE)
_image = _bind(_kernel, "QueryFullProcessImageNameW", W.BOOL,
               W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD))
_foreground = _bind(_user, "GetForegroundWindow", W.HWND)
_pid = _bind(_user, "GetWindowThreadProcessId", W.DWORD, W.HWND, C.POINTER(W.DWORD))
_title_length = _bind(_user, "GetWindowTextLengthW", C.c_int, W.HWND)
_title_text = _bind(_user, "GetWindowTextW", C.c_int, W.HWND, W.LPWSTR, C.c_int)
_visible = _bind(_user, "IsWindowVisible", W.BOOL, W.HWND)
_owner = _bind(_user, "GetWindow", W.HWND, W.HWND, W.UINT)
_style = _bind(_user, "GetWindowLongW", W.LONG, W.HWND, C.c_int)
_cloaked = _bind(_dwm, "DwmGetWindowAttribute", _HRESULT,
                 W.HWND, W.DWORD, _P, W.DWORD)
_EnumProc = C.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
_enum = _bind(_user, "EnumWindows", W.BOOL, _EnumProc, W.LPARAM)
# WinDLL (not OleDLL) keeps HRESULTs as integers, including RPC_E_CHANGED_MODE.
_ole = C.WinDLL("ole32")
_coinit = _bind(_ole, "CoInitializeEx", _HRESULT, _P, W.DWORD)
_couninit = _bind(_ole, "CoUninitialize", None)
_create = _bind(_ole, "CoCreateInstance", _HRESULT,
                C.POINTER(_GUID), _P, W.DWORD, C.POINTER(_GUID), C.POINTER(_P))
_CLSID = _GUID.parse("bcde0395-e52f-467c-8e3d-c4579291692e")
_ENUM_IID = _GUID.parse("a95664d2-9614-4f35-a746-de8db63617e6")
_VOLUME_IID = _GUID.parse("5cdf2c82-841e-4546-9722-0cf74078229a")


def _com(obj, slot, result, argtypes, *args):
    vtable = C.cast(obj, C.POINTER(C.POINTER(_P))).contents
    return C.WINFUNCTYPE(result, _P, *argtypes)(vtable[slot])(obj, *args)


def _check(hr):
    if hr < 0:
        raise OSError(f"HRESULT 0x{hr & 0xffffffff:08x}")


def _times():
    idle, kernel, user = W.FILETIME(), W.FILETIME(), W.FILETIME()
    if not _system_times(C.byref(idle), C.byref(kernel), C.byref(user)):
        raise C.WinError(C.get_last_error())
    return tuple((v.dwHighDateTime << 32) | v.dwLowDateTime for v in (idle, kernel, user))


def _program(hwnd):
    pid = W.DWORD()
    if not _pid(hwnd, C.byref(pid)) or not pid.value:
        return None
    handle = _open_process(0x1000, False, pid.value)  # QUERY_LIMITED_INFORMATION
    if not handle:
        return None
    try:
        buf, size = C.create_unicode_buffer(32768), W.DWORD(32768)
        if not _image(handle, 0, buf, C.byref(size)):
            return None
        return ntpath.splitext(ntpath.basename(buf.value))[0].lower() or None
    finally:
        _close(handle)


def _title(hwnd):
    buf = C.create_unicode_buffer(min(32767, max(0, _title_length(hwnd))) + 1)
    _title_text(hwnd, buf, len(buf))
    return buf.value


def _rate_text(rate):
    for unit in ("B/s", "KB/s", "MB/s", "GB/s"):
        if rate < 1024 or unit == "GB/s":
            return f"{rate:.0f} {unit}" if rate < 100 and unit == "B/s" else (
                f"{rate:.1f} {unit}" if rate < 10 else f"{rate:.0f} {unit}")
        rate /= 1024


class Reader:
    """Independent sampling history; share a Reader safely between threads.

    Apps are sorted by descending window count, then ascending program name.
    A vanished/inaccessible window is skipped; an API-level failure returns None.
    """

    def __init__(self, exclude=("python", "pythonw")):
        self.exclude = frozenset(name.lower() for name in exclude)
        self._cpu_previous = None
        self._net_previous = None
        self._cpu_lock = threading.Lock()
        self._net_lock = threading.Lock()

    @_safe
    def cpu(self):
        with self._cpu_lock:
            previous = self._cpu_previous
            current = _times()
            if previous is None:
                previous = current
                time.sleep(0.1)
                current = _times()
            self._cpu_previous = current
            idle, kernel, user = (b - a for a, b in zip(previous, current))
            total = kernel + user  # kernel time includes idle time
            if total <= 0 or min(idle, kernel, user) < 0:
                return None
            return max(0.0, min(100.0, (total - idle) * 100.0 / total))

    @_safe
    def memory(self):
        status = _Memory()
        status.length = C.sizeof(status)
        if not _memory(C.byref(status)) or not status.total:
            return None
        return {"pct": float(status.load),
                "used_gb": (status.total - status.available) / 1024**3,
                "total_gb": status.total / 1024**3}

    @_safe
    def network(self):
        with self._net_lock:
            table = _P()
            try:
                if _get_table(C.byref(table)) or not table:
                    return None
                header = C.cast(table, C.POINTER(_IfTable)).contents
                rows = C.cast(table.value + _IfTable.rows.offset, C.POINTER(_IfRow))
                counters = {rows[i].luid: (rows[i].in_octets, rows[i].out_octets)
                            for i in range(header.count)
                            if rows[i].status == 1 and rows[i].type != 24
                            and rows[i].access != 1}
                now = time.perf_counter()
            finally:
                if table:
                    _free_table(table)
            previous = self._net_previous
            self._net_previous = now, counters
            down = up = 0.0
            if previous is not None and now > previous[0]:
                # Match LUIDs: new/disappearing adapters and reset counters must
                # not create spikes from cumulative lifetime traffic.
                for luid, (rx, tx) in counters.items():
                    if luid in previous[1]:
                        old_rx, old_tx = previous[1][luid]
                        down += max(0, rx - old_rx) / (now - previous[0])
                        up += max(0, tx - old_tx) / (now - previous[0])
            return {"down": down, "up": up}

    @_safe
    def volume(self):
        enumerator, device, endpoint = _P(), _P(), _P()
        hr = _coinit(None, 0)  # COINIT_MULTITHREADED; balances S_OK and S_FALSE
        initialized = hr >= 0
        if hr < 0 and (hr & 0xffffffff) != 0x80010106:  # existing STA is usable
            return None
        try:
            _check(_create(C.byref(_CLSID), None, 1, C.byref(_ENUM_IID), C.byref(enumerator)))
            # Zero-based vtable slots, including IUnknown 0/1/2:
            # IMMDeviceEnumerator::GetDefaultAudioEndpoint=4;
            # IMMDevice::Activate=3; IAudioEndpointVolume::
            # GetMasterVolumeLevelScalar=9, GetMute=15; IUnknown::Release=2.
            _check(_com(enumerator, 4, _HRESULT, (C.c_int, C.c_int, C.POINTER(_P)),
                        0, 1, C.byref(device)))  # eRender, eMultimedia
            _check(_com(device, 3, _HRESULT, (C.POINTER(_GUID), W.DWORD, _P, C.POINTER(_P)),
                        C.byref(_VOLUME_IID), 23, None, C.byref(endpoint)))
            level, muted = C.c_float(), W.BOOL()
            _check(_com(endpoint, 9, _HRESULT, (C.POINTER(C.c_float),), C.byref(level)))
            _check(_com(endpoint, 15, _HRESULT, (C.POINTER(W.BOOL),), C.byref(muted)))
            return {"pct": max(0, min(100, round(level.value * 100))), "muted": bool(muted.value)}
        finally:
            try:
                for obj in (endpoint, device, enumerator):
                    if obj:
                        _com(obj, 2, W.ULONG, ())
            finally:
                if initialized:
                    _couninit()

    @_safe
    def battery(self):
        status = _Power()
        if not _power(C.byref(status)) or status.flags in (128, 255) or status.flags & 128:
            return None
        if status.pct > 100:  # 255 means unknown, never display a fictitious 100%
            return None
        return {"pct": int(status.pct), "charging": bool(status.flags & 8)}

    @_safe
    def focused(self):
        hwnd = _foreground()
        if not hwnd:
            return None
        program = _program(hwnd)
        return {"program": program, "title": _title(hwnd)} if program else None

    @_safe
    def apps(self):
        counts, errors = {}, []

        @_EnumProc
        def visit(hwnd, _):
            try:
                if not _visible(hwnd) or _owner(hwnd, 4) or _style(hwnd, -20) & 0x80:
                    return True  # GW_OWNER, GWL_EXSTYLE, WS_EX_TOOLWINDOW
                if not _title(hwnd).strip():
                    return True
                cloak = W.DWORD()
                if _cloaked(hwnd, 14, C.byref(cloak), C.sizeof(cloak)) < 0 or cloak.value:
                    return True
                program = _program(hwnd)
                if program and program not in self.exclude:
                    counts[program] = counts.get(program, 0) + 1
                return True
            except Exception as exc:
                errors.append(exc)
                return False

        if not _enum(visit, 0) or errors:
            return None
        return [{"program": name, "count": count}
                for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]

    @_safe
    def read_all(self):
        cpu = self.cpu()
        result = {"cpu": None if cpu is None else {"pct": cpu, "text": f"{cpu:.0f}%"},
                  "memory": self.memory(), "network": self.network(),
                  "volume": self.volume(), "battery": self.battery(),
                  "focused": self.focused(), "apps": self.apps(), "at": time.time()}
        for name in ("memory", "volume", "battery"):
            value = result[name]
            if value is not None:
                value["text"] = "muted" if value.get("muted") else f"{value['pct']:.0f}%"
                if name == "battery" and value["charging"]:
                    value["text"] += " ⚡"
        net = result["network"]
        if net is not None:
            net["text"] = f"↓{_rate_text(net['down'])} ↑{_rate_text(net['up'])}"
        return result


if __name__ == "__main__":
    reader = Reader()
    print(json.dumps(reader.read_all()), flush=True)
    time.sleep(1)
    print(json.dumps(reader.read_all()), flush=True)
