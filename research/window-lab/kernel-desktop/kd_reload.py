"""kd_reload: after an edit, restart only what the edit touched, not the whole desktop.

    python kd_reload.py              show what is stale and refresh it
    python kd_reload.py --dry        only show what is stale
    python kd_reload.py --full       also restart the whole desktop if the kernel itself changed
    python kd_reload.py window       only these modules (leave someone else's half-done module alone)

What is stale is read from the machine, not guessed: a module is stale when a source file of its own is newer
than its running process; pages/ are stale when newer than the last refresh (or the window module's start).

    pages/ (html, js, css)           window.reload all: pages load again in place; nothing closes
    a module's .py                   off <module>, on <module>: that module's process only (window blinks
                                     every Agora window for a few seconds; house keeps its builders' state)
    modproto.py                      every module (they all import it)
    kernel-lab/kernel/, kdesk.py     only the kernel, through the keeper: nothing closes (without a keeper, the
                                     whole desktop, only with --full)
    kdesk_keeper.py                  the whole desktop (kdesk_off, kdesk_on): only with --full
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from kd_say import say  # noqa: E402

STAMP = HERE / "state" / "kd_reload.stamp"
KERNEL = [ROOT / "research" / "kernel-lab" / "kernel", HERE / "kdesk.py", HERE / "keeper_link.py"]
KEEPER = [HERE / "kdesk_keeper.py"]
OWN_ENTRY = {"kd_system.py", "kd_media.py", "kd_guy.py"}       # kernel-desktop modules besides the window host
NOT_MODULE = {"kdesk.py", "kd_say.py", "kd_reload.py", "kdesk_on.py", "kdesk_off.py", "modproto.py",
              "kdesk_keeper.py", "keeper_link.py"}


def processes():
    """-> (kdesk start time, [(module name, entry path, start time, pid)]) from the processes running now."""
    ps = ("$k=(Get-NetTCPConnection -State Listen -LocalPort 8810 -ea 0 | select -First 1).OwningProcess;"
          "if($k){Get-CimInstance Win32_Process -Filter \"ProcessId=$k or ParentProcessId=$k\" |"
          " % { [pscustomobject]@{pid=$_.ProcessId; parent=$_.ParentProcessId; cmd=$_.CommandLine;"
          " start=[double](New-TimeSpan -Start (Get-Date '1970-01-01') -End $_.CreationDate.ToUniversalTime()).TotalSeconds} }"
          " | ConvertTo-Json -Compress}")
    from kdesk_keeper import ask, INFO
    if ask("status") is not None:                    # under a keeper, the kernel and modules are the keeper's children
        ps = ps.replace("(Get-NetTCPConnection -State Listen -LocalPort 8810 -ea 0 | select -First 1).OwningProcess",
                        str(json.loads(INFO.read_text())["pid"]))
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True).stdout.strip()
    rows = json.loads(out) if out else []
    rows = rows if isinstance(rows, list) else [rows]
    keeper = next((r for r in rows if "kdesk_keeper.py" in (r["cmd"] or "")), None)
    kd = next((r for r in rows if "kdesk.py" in (r["cmd"] or "") and "kdesk_keeper.py" not in (r["cmd"] or "")), None)
    mods = []
    for r in rows:
        if r is kd or "kdesk_keeper.py" in (r["cmd"] or ""):
            continue
        entry = next((Path(a.strip('"')) for a in (r["cmd"] or "").split() if a.strip('"').endswith(".py")), None)
        if entry:
            name = entry.stem.removeprefix("kd_").removesuffix("_module")
            mods.append((name, entry, r["start"], r["pid"]))
    return (kd["start"] if kd else None), mods, (keeper["start"] if keeper else None)


def own_files(entry):
    """A module's own source: its entry, and for the window host every other non-module .py beside it."""
    if entry.parent == HERE:
        if entry.name != "kd_window.py":
            return [entry]
        return [p for p in HERE.glob("*.py") if p.name not in OWN_ENTRY | NOT_MODULE and not p.name.startswith("test_")
                and p.name != "kd_window.py"] + [entry]
    return [p for p in entry.parent.glob("*.py") if not p.name.startswith("test_")]


def newer(files, than):
    return sorted({str(p.relative_to(ROOT)) for p in files if p.exists() and p.stat().st_mtime > than})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("only", nargs="*", help="refresh only these modules (and pages if window is named)")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--skip", nargs="*", default=[], help="leave these modules running (the House skips itself "
                                                           "while workers run, and restarts later)")
    a = ap.parse_args()
    kd_start, mods, keeper_start = processes()
    if kd_start is None:
        print("the desktop is not running (kdesk_on.py starts it)")
        return
    sessions = json.loads((HERE / "state" / "world" / "keep" / "sessions.json").read_text(encoding="utf-8"))
    token = next(t for t, v in sessions.items() if v.get("signer") == "alex")

    kernel = [] if a.only else newer([p for d in KERNEL for p in (d.glob("*.py") if d.is_dir() else [d])], kd_start)
    proto = newer([HERE / "modproto.py"], min((m[2] for m in mods), default=kd_start))
    stale = {}
    for name, entry, start, _ in mods:
        files = newer(own_files(entry), start) + (proto if proto else [])
        if files and (not a.only or name in a.only) and name not in a.skip:
            stale[name] = files
    window_start = next((m[2] for m in mods if m[0] == "window"), kd_start)
    since = max(window_start, STAMP.stat().st_mtime if STAMP.exists() else 0)
    pages = newer([p for p in (HERE / "pages").rglob("*") if p.is_file()], since) if "window" not in stale else []

    from kdesk_keeper import ask
    kept = ask("status") is not None
    keeper = [] if a.only or not kept else newer(KEEPER, keeper_start)
    if not (kernel or keeper or stale or pages):
        print("nothing is stale: everything running is as new as its source")
        return
    if keeper:
        print("the keeper itself changed (" + ", ".join(keeper) + "): the whole desktop must restart"
              + ("" if a.full else "; run again with --full to do it"))
    if kernel:
        print("kernel changed (" + ", ".join(kernel[:4]) + (" …" if len(kernel) > 4 else "") + "): "
              + ("only the kernel restarts; windows and modules stay" if kept else
                 "the whole desktop must restart" + ("" if a.full else "; run again with --full to do it")))
    for name, files in stale.items():
        print(f"{name}: {', '.join(files[:4])}{' …' if len(files) > 4 else ''}")
    if pages:
        print(f"pages: {', '.join(pages[:4])}{' …' if len(pages) > 4 else ''}")
    if a.dry:
        return

    if (keeper or (kernel and not kept)) and a.full:
        print("restarting the whole desktop: every Agora window and both bars close, then come back")
        subprocess.run([sys.executable, str(HERE / "kdesk_off.py")])
        subprocess.run([sys.executable, str(HERE / "kdesk_on.py"), "--wait"])
        STAMP.touch()
        return
    if kernel and kept:
        old = processes()[0]
        print(ask("restart-kernel").get("text"))
        end = time.monotonic() + 60
        while time.monotonic() < end and processes()[0] in (None, old):
            time.sleep(0.5)
        while time.monotonic() < end:
            try:
                if "window.list" in (say("help all", token).get("text") or ""):
                    break
            except Exception:                        # noqa: BLE001  still starting
                pass
            time.sleep(0.5)
        print("kernel: " + ("running again" if processes()[0] not in (None, old) else "NOT back yet; see state/kdesk.log"))
    for name in stale:
        old = {m[3] for m in mods if m[0] == name}
        print(say(f"off {name}", token).get("text"))
        end = time.monotonic() + 15
        while time.monotonic() < end and old & {m[3] for m in processes()[1]}:
            time.sleep(0.3)
        print(say(f"on {name}", token).get("text"))
        end = time.monotonic() + 30
        while time.monotonic() < end and not any(m[0] == name for m in processes()[1]):
            time.sleep(0.5)
        print(f"{name}: " + ("running again" if any(m[0] == name for m in processes()[1]) else "NOT back yet; status " + name))
    if pages:
        print(say("window.reload all", token).get("text"))
    STAMP.parent.mkdir(exist_ok=True)
    STAMP.touch()


if __name__ == "__main__":
    main()
