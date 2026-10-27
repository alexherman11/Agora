"""Independent, fail-open lease for the Windows taskbar.

The host launches this through WMI, outside its process tree. It owns the hide,
and restores on host death, release, Explorer restart failure, or its own error.
HKCU Run is recovery only (never starts Agora); no shell replacement is installed.
--probe uses a hidden surrogate HWND and NEVER changes Explorer or the registry.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
LEASE = HERE / 'state' / 'taskbar-lease.json'
RUN_NAME = 'Agora taskbar recovery'
u, k, shell = (C.WinDLL(n) for n in ('user32', 'kernel32', 'shell32'))
u.FindWindowW.argtypes, u.FindWindowW.restype = [W.LPCWSTR, W.LPCWSTR], W.HWND
u.FindWindowExW.argtypes, u.FindWindowExW.restype = [W.HWND, W.HWND, W.LPCWSTR, W.LPCWSTR], W.HWND
u.ShowWindow.argtypes = [W.HWND, C.c_int]
u.IsWindow.argtypes = [W.HWND]
u.IsWindowVisible.argtypes = [W.HWND]
k.OpenProcess.argtypes, k.OpenProcess.restype = [W.DWORD, W.BOOL, W.DWORD], W.HANDLE
k.WaitForSingleObject.argtypes = [W.HANDLE, W.DWORD]
k.CloseHandle.argtypes = [W.HANDLE]
k.GetProcessTimes.argtypes = [W.HANDLE] + [C.POINTER(W.FILETIME)] * 4


class DATA(C.Structure):
    _fields_ = [('size', W.DWORD), ('hwnd', W.HWND), ('msg', W.UINT), ('edge', W.UINT),
                ('rect', W.RECT), ('param', W.LPARAM)]


shell.SHAppBarMessage.argtypes, shell.SHAppBarMessage.restype = [W.DWORD, C.POINTER(DATA)], C.c_size_t


def stamp(handle):
    times = [W.FILETIME() for _ in range(4)]
    if not k.GetProcessTimes(handle, *(C.byref(t) for t in times)):
        raise C.WinError()
    return (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime


def owner_alive(data):
    h = k.OpenProcess(0x100000 | 0x1000, False, data['owner'])
    if not h:
        return False
    try:
        return k.WaitForSingleObject(h, 0) == 258 and stamp(h) == data['created']
    finally:
        k.CloseHandle(h)


def taskbars():
    primary = u.FindWindowW('Shell_TrayWnd', None)
    found = [primary] if primary else []
    last = None
    while True:
        last = u.FindWindowExW(None, last, 'Shell_SecondaryTrayWnd', None)
        if not last:
            return found
        found.append(last)


def shell_state(value=None):
    d = DATA()
    d.size = C.sizeof(d)
    if value is None:
        return int(shell.SHAppBarMessage(4, C.byref(d)))
    d.param = value
    shell.SHAppBarMessage(10, C.byref(d))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data), encoding='utf-8')
    os.replace(tmp, path)


def recovery_registration(enable):
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run') as key:
        if enable:
            pyw = HERE.parents[2] / '.venv' / 'Scripts' / 'pythonw.exe'
            winreg.SetValueEx(key, RUN_NAME, 0, winreg.REG_SZ, f'"{pyw}" "{Path(__file__).resolve()}" --recover')
        else:
            try:
                winreg.DeleteValue(key, RUN_NAME)
            except FileNotFoundError:
                pass


def restore(path=LEASE, force=False, expected_guard=None):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return False
    if expected_guard is not None and data.get('guard') != expected_guard:
        return False
    if not force and owner_alive(data):
        return False
    if data.get('probe'):
        if u.IsWindow(data['probe']):
            # Probe stays hidden throughout; enabled state stands in for visibility.
            u.EnableWindow(W.HWND(data['probe']), True)
    else:
        end = time.monotonic() + 10
        while not taskbars() and time.monotonic() < end:
            time.sleep(.25)
        if not taskbars():
            return False  # leave the recovery entry and lease for next sign-in
        shell_state(data['state'])
        for hwnd in taskbars():
            u.ShowWindow(hwnd, 5)
        recovery_registration(False)
    data['restored'] = True
    write(path, data)
    return True


def watch(owner, path=LEASE, probe=0):
    h = k.OpenProcess(0x100000 | 0x1000, False, owner)
    if not h:
        return
    data = dict(owner=owner, created=stamp(h), state=0 if probe else shell_state(), probe=probe,
                guard=os.getpid(), ready=False, restored=False)
    # Durable recovery is installed BEFORE altering the shell.
    if not probe:
        restore(path)
        recovery_registration(True)
    write(path, data)
    try:
        if probe:
            u.EnableWindow(W.HWND(probe), False)
        else:
            if not taskbars():
                raise RuntimeError('Explorer taskbar absent; refusing replacement')
            shell_state(data['state'] | 1)  # auto-hide releases Explorer's reservation; preserve other bits
            for hwnd in taskbars():
                u.ShowWindow(hwnd, 0)
        data['ready'] = True
        write(path, data)
        while k.WaitForSingleObject(h, 250) == 258:
            current = json.loads(path.read_text(encoding='utf-8'))
            if current.get('release') or current.get('restored'):
                break
            if not probe:
                if not taskbars():
                    break  # Explorer died; fail open rather than hiding a new shell
                for hwnd in taskbars():
                    u.ShowWindow(hwnd, 0)
    finally:
        k.CloseHandle(h)
        restore(path, force=True)


class Lease:
    def __init__(self):
        self.started = False
        self.guard = None

    def acquire(self):
        if self.started:
            return
        try:
            active = json.loads(LEASE.read_text(encoding='utf-8'))
            if not active.get('restored') and owner_alive(active):
                raise RuntimeError('another desktop host already owns the Windows taskbar lease')
        except (OSError, ValueError):
            pass
        restore()
        pyw = HERE.parents[2] / '.venv' / 'Scripts' / 'pythonw.exe'
        line = f'"{pyw}" "{Path(__file__).resolve()}" --owner {os.getpid()}'
        ps = "$r=Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine='" + line.replace("'", "''") + "'}; if($r.ReturnValue -ne 0){exit 1}"
        subprocess.run(['powershell', '-NoProfile', '-Command', ps], check=True, capture_output=True,
                       timeout=20, creationflags=0x08000000)
        end = time.monotonic() + 8
        while time.monotonic() < end:
            try:
                data = json.loads(LEASE.read_text(encoding='utf-8'))
                if data['owner'] == os.getpid() and data['ready'] and not data['restored']:
                    self.started = True
                    self.guard = data['guard']
                    threading = __import__('threading')
                    threading.Thread(target=self._monitor, args=(data['guard'],), daemon=True).start()
                    return
            except (OSError, ValueError, KeyError):
                pass
            time.sleep(.1)
        restore(force=True)
        raise RuntimeError('taskbar guard did not become ready; Windows taskbar restored')

    def _monitor(self, pid):
        handle = k.OpenProcess(0x100000, False, pid)
        if not handle:
            restore(force=True, expected_guard=pid)
            return
        try:
            while self.started and self.guard == pid:
                if k.WaitForSingleObject(handle, 250) != 258:
                    restore(force=True, expected_guard=pid)
                    if self.guard == pid:
                        self.started = False
                    return
        finally:
            k.CloseHandle(handle)

    def release(self):
        if self.started:
            data = json.loads(LEASE.read_text(encoding='utf-8'))
            data['release'] = True
            write(LEASE, data)
            # guard owns restoration; wait for acknowledgement before another lease starts
            end = time.monotonic() + 3
            while time.monotonic() < end:
                if json.loads(LEASE.read_text(encoding='utf-8')).get('restored'):
                    break
                time.sleep(.05)
            else:
                restore(force=True)
            self.started = False
            self.guard = None


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--owner', type=int)
    ap.add_argument('--recover', action='store_true')
    ap.add_argument('--lease', type=Path, default=LEASE)
    ap.add_argument('--probe', type=int, default=0)
    args = ap.parse_args()
    if args.recover:
        restore(args.lease)
    elif args.owner:
        watch(args.owner, args.lease, args.probe)
