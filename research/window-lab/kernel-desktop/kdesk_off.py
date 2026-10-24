"""kdesk_off: stop Alex's desktop on the new kernel, all of it, and give the screen back as it was.

    python kdesk_off.py

It ends the kernel's process tree (the kernel, the window host, the little guy, their browser engines), then any of
its module processes left over, by their command lines, and checks that the strip the Agora taskbar held is given
back to the screen's work area. It writes nothing to the world, so the next start shows exactly what the world says
(the words `off window`, `off guy` are the switches inside the world; undo turns them on again).

It touches nothing else: not the home base (hud.py), not the frontier keeper, not the Windows taskbar.
"""
import ctypes
import subprocess
import time
from ctypes import wintypes as wt

MINE = ("kernel-desktop\\kdesk.py", "kdesk.py --", "kernel-desktop\\kd_window.py", "kernel-desktop\\kd_guy.py",
        "kernel-desktop\\kd_system.py", "kernel-desktop\\kd_media.py")


def processes():
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='python.exe' or Name='pythonw.exe' or Name='cmd.exe'\" | "
          "ForEach-Object { \"$($_.ProcessId)`t$($_.CommandLine)\" }")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=60,
                         creationflags=0x08000000).stdout
    found = []
    for line in out.splitlines():
        pid, _, cmd = line.partition("\t")
        if any(m.lower() in cmd.lower() for m in MINE) and "kdesk_off" not in cmd and "--headless" not in cmd:
            found.append((int(pid), cmd))
    return found


def work_area():
    u = ctypes.WinDLL("user32")
    u.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    r = wt.RECT()
    u.SystemParametersInfoW(0x30, 0, ctypes.byref(r), 0)
    full = u.GetSystemMetrics(1)
    return r.bottom, full


def main():
    procs = processes()
    kernels = [p for p in procs if "kdesk.py" in p[1].lower()]
    for pid, _ in kernels or procs:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, creationflags=0x08000000)
    time.sleep(0.5)
    left = processes()
    for pid, _ in left:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, creationflags=0x08000000)
    time.sleep(1.0)
    left = processes()
    bottom, full = work_area()
    print(f"kdesk off: stopped {len(procs)} process(es); {len(left)} left; the work area ends at {bottom} of {full}")


if __name__ == "__main__":
    main()
