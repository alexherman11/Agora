"""test_wm_release: what wm.py's release-all will and will not end (a6113, after Codex's c6176 and JEFF's c6178).

    python research/window-lab/test_wm_release.py

No window, no Edge and no process of anyone else's: every process here is a dummy (python sleeping) this test starts,
and every wm.json is a fake one in a folder of its own (wm.STATE is pointed there). Each case writes a state file,
runs release_all, and looks at which dummies are still alive:
  - a process recorded with its creation time and executable, both still matching: ended
  - its pid recorded with another creation time (the pid given to a new process, as on 16 Oct): left alone, said
  - its pid recorded with another executable: left alone
  - a record with no creation time, and a bare pid (the old edge_pids form): left alone
  - a process that merely has one of the manager's profile folders on its command line, not recorded: left alone
  - a state file saved before Windows last started, and one with no save time (the form Codex found): renamed aside,
    nothing in it ended, even a record that matches
  - the host's own identity: alive only while pid, creation time and executable all match (wm_switch.other_host)
"""
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wm  # noqa: E402
import wm_switch  # noqa: E402

BASE = getattr(sys, "_base_executable", sys.executable)       # the interpreter itself: its pid is the process's
results = []
dummies = []


def check(what, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + what + ("" if ok else f"\n     {detail}"), flush=True)
    results.append(bool(ok))


def dummy(*extra):
    p = subprocess.Popen([BASE, "-c", "import time; time.sleep(120)", *extra], creationflags=0x08000000)
    dummies.append(p)
    time.sleep(0.3)
    return p


def release(st):
    wm.save_state(st) if "saved_at" not in st else wm.STATE.write_text(json.dumps(st), encoding="utf-8")
    said = []
    wm.release_all(say=lambda *a: said.append(" ".join(str(x) for x in a)))
    time.sleep(0.3)
    return "\n".join(said)


def base(**more):
    return {"world": "wmtest", "notation": str(tmp), "windows": [], **more}


tmp = Path(tempfile.mkdtemp(prefix="wm-release-test-"))
wm.STATE_DIR, wm.STATE, wm.LOG = tmp, tmp / "wm.json", tmp / "wm.log"
wm_switch.STATE = wm.STATE
try:
    a = dummy()
    rec = wm.identity(a.pid, why="dummy")
    check("identity reads a running process: pid, creation time, executable",
          rec and rec["created"] > 0 and rec["exe"].lower().endswith("python.exe"), rec)
    said = release(base(edge_procs=[rec]))
    time.sleep(0.5)
    check("a recorded process whose creation time and executable match is ended", a.poll() is not None, said)
    check("and the state says it is released, with nothing left to end",
          json.loads(wm.STATE.read_text())["edge_procs"] == [] and "released" in json.loads(wm.STATE.read_text()))

    b = dummy()
    rb = wm.identity(b.pid)
    said = release(base(edge_procs=[{**rb, "created": rb["created"] - 10_000_000}]))
    check("the same pid recorded with another creation time (a pid reused) is left alone", b.poll() is None, said)
    check("and release-all says why", "LEFT ALONE" in said and "another process" in said, said)

    said = release(base(unseen_procs=[{**rb, "exe": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"}]))
    check("the same pid and creation time with another executable is left alone", b.poll() is None, said)

    said = release(base(edge_procs=[{"pid": b.pid, "exe": rb["exe"]}], edge_pids=[b.pid], unseen_pids=[b.pid]))
    check("a record with no creation time, and a bare pid in the old edge_pids form, are left alone", b.poll() is None, said)
    check("and the record with no creation time is named", "was not recorded" in said, said)

    prof = wm.EDGE_ROOT / "20991231-000000" / "windows"
    c = dummy(f"--user-data-dir={prof}", f"--user-data-dir={HERE / 'state' / 'edge-profile'}")
    said = release(base(edge_procs=[]))
    check("a process that only has the manager's (or lens_window's) profile folder on its command line is left alone",
          c.poll() is None, said)

    d = dummy()
    rd = wm.identity(d.pid)
    said = release(base(edge_procs=[rd], saved_at=wm.boot_time() - 3600))
    stale = sorted(tmp.glob("wm.stale-*.json"))
    check("a state file saved before Windows last started acts on nothing, not even a record that matches",
          d.poll() is None, said)
    check("it is renamed aside, and says why", stale and not wm.STATE.exists() and "before Windows last started" in said,
          (stale, said))
    for s in stale:
        s.unlink()
    wm.STATE.write_text(json.dumps({"world": "wmtest", "host_pid": 1, "edge_pids": [d.pid], "unseen_pids": [d.pid],
                                    "windows": [{"kind": "agora", "hwnd": 0}]}), encoding="utf-8")
    said = []
    wm.release_all(say=lambda *x: said.append(" ".join(map(str, x))))
    check("a state file with no save time (the form found on 16 Oct) acts on nothing and is renamed aside",
          d.poll() is None and not wm.STATE.exists() and list(tmp.glob("wm.stale-*.json")), said)

    e = dummy()
    re_ = wm.identity(e.pid, why="the window manager host")
    wm.save_state(base(host=re_, windows=[{"kind": "agora", "hwnd": 0}]))
    check("a host recorded by identity and running is alive (a start is refused, naming it)",
          wm.host_alive(wm.load_state()) and wm_switch.other_host() == e.pid, wm.load_state())
    wm.save_state(base(host={**re_, "created": re_["created"] + 1}, windows=[{"kind": "agora", "hwnd": 0}]))
    check("the same pid with another creation time is not that host: no refusal, and release_left would act",
          not wm.host_alive(wm.load_state()) and wm_switch.other_host() == 0)
    wm.save_state(base(host_pid=e.pid, windows=[{"kind": "agora", "hwnd": 0}]))
    check("a bare host_pid (the old form) is never taken for a running host", not wm.host_alive(wm.load_state()))
    check("kill_same refuses a record whose creation time differs, and the process lives",
          "left alone" in wm.kill_same({**re_, "created": re_["created"] + 1}) and e.poll() is None)
finally:
    for p in dummies:
        if p.poll() is None:
            p.kill()
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
print("wm release:", "all passed" if all(results) else f"{results.count(False)} FAILED")
sys.exit(0 if all(results) else 1)
