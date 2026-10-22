"""The verifier's ONE fake family run (a10179), on the landed Job Object and Guard. No engine, no browser, no mail.

    python research/window-lab/check_native_run_fake.py reads     the verifier's Windows reads, counts only
    python research/window-lab/check_native_run_fake.py run       the one fake family run (authorized by a10179)

`run`: fresh house admission (guard_context), then under Guard a held job_scope; the verifier observes before
launch; a python fixture is started suspended in the job on a hidden agora-sandbox desktop with
--sandbox-profile=<its run-owned profile>; it starts a grandchild, opens a tk window there, makes a loopback-only
socket pair, writes one file in its profile, reports its pids and ports, and waits. The verifier samples every
0.1 s, gates, then the job is cleaned up (sandbox_window.close) and the verifier observes after. The report holds
the verdict and its own evidence only: no titles, no command lines, no other process's paths, no install names.
Refusal is final, not a retry loop. Never rerun without a new explicit authorization.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sandbox_window as sb  # noqa: E402
from sandbox_receipts import error, write  # noqa: E402
import native_run_verify as nv  # noqa: E402
sys.path.insert(0, str(HERE.parents[0] / "text-desk-lab/notation"))
import guard_context  # noqa: E402
# what start/close import lazily, imported now: a module first imported mid-run writes __pycache__ into the
# watched repo, the harness's own write, not the job's
import sandbox_birth, sandbox_owned, sandbox_job, hud_lifecycle  # noqa: E401,E402,F401

ROOT = HERE.parents[1]
EVIDENCE = HERE / "native-verify" / "evidence"

FIXTURE = (
    "import json,os,pathlib,socket,subprocess,sys,time\n"
    "g=subprocess.Popen([sys.executable,'-I','-S','-c','import time; time.sleep(30)'],close_fds=True,"
    "creationflags=0x08000000)\n"
    "srv=socket.socket(); srv.bind(('127.0.0.1',0)); srv.listen(1)\n"
    "cli=socket.create_connection(srv.getsockname()); acc,_=srv.accept()\n"
    "prof=pathlib.Path(sys.argv[2].split('=',1)[1]); (prof/'fixture-wrote.txt').write_text('fake','utf-8')\n"
    "win=None\n"
    "try:\n"
    "    import tkinter; win=tkinter.Tk(); win.title('agora nrv fake'); win.geometry('320x200'); win.update()\n"
    "except Exception as e: win=repr(type(e).__name__)\n"
    "ready=pathlib.Path(sys.argv[1]); tmp=ready.with_suffix('.pending')\n"
    "tmp.write_text(json.dumps({'child':os.getpid(),'grandchild':g.pid,'listen':srv.getsockname()[1],"
    "'client':cli.getsockname()[1],'window':win is not None and not isinstance(win,str)}),'utf-8')\n"
    "tmp.replace(ready)\n"
    "end=time.time()+30\n"
    "while time.time()<end:\n"
    "    if not isinstance(win,str) and win is not None: win.update()\n"
    "    time.sleep(0.05)\n"
)


def reads():
    """Each Windows read once; counts only (nothing about any process, window or program is printed)."""
    n, out = nv.Native(), {}
    for label, fn in (("processes", n.processes), ("tcp", n.tcp), ("udp", n.udp),
                      ("default_desktop_windows", lambda: n.desktop_window_owners("Default"))):
        try:
            out[label] = len(fn())
        except Exception as exc:
            out[label] = {"error": error(exc)}
    try:
        recs = n.install_records()
        out["install_records"] = {k: (len(v) if isinstance(v, list) else "unreadable") for k, v in recs.items()}
    except Exception as exc:
        out["install_records"] = {"error": error(exc)}
    me = os.getpid()
    out["own_tcp_rows_seen_for_a_loopback_pair"] = None
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    c = socket.create_connection(s.getsockname())
    a, _ = s.accept()
    rows = [r for r in n.tcp() if r[0] == me]
    out["own_tcp_rows_seen_for_a_loopback_pair"] = sorted(nv.TCP_STATES.get(r[1], r[1]) for r in rows)
    for x in (a, c, s):
        x.close()
    h = n.open(me)
    try:
        out["own_identity_readable"] = n.identity(h) is not None
        out["own_command_line_readable"] = bool(n.command_line(h))
    finally:
        n.close(h)
    print(json.dumps(out, indent=2))
    return 0


def run():
    name = "nrv-a10179-" + uuid.uuid4().hex[:8]
    os.makedirs(sb.STATE, exist_ok=True)
    report = sb.STATE / (name + "-check.json")
    data = {"scope": "one fake enrolled python family; no engine, browser, mail or public network",
            "source_sha256": {p: hashlib.sha256((HERE / p).read_bytes()).hexdigest()
                              for p in ("native_run_verify.py", "check_native_run_fake.py", "sandbox_job.py",
                                        "sandbox_window.py")}}
    data["house_preflight"] = guard_context.read()
    if not data["house_preflight"]["admitted"]:
        data["result"] = "refused before job/desktop/child creation; no retry"
        data["house_preflight"] = {"admitted": False, "reason": data["house_preflight"].get("reason")}
        write(report, data)
        print(json.dumps(data, indent=2))
        return 2
    data["house_preflight"] = {"admitted": True}
    run_root = sb.STATE / (name + "-run")
    profile, scratch = run_root / "profile", run_root / "scratch"
    profile.mkdir(parents=True)
    scratch.mkdir()
    ready = scratch / "ready.json"
    executable = str(Path(sys._base_executable).resolve())
    spec = {"name": name, "profile_roots": [str(profile)], "scratch_roots": [str(scratch)],
            "watched_roots": [str(ROOT)],
            "exclude": [str(sb.STATE), str(ROOT / ".git"), str(HERE / "__pycache__"),
                        str(ROOT / "research/text-desk-lab/notation/__pycache__")],
            "engine_images": ["python.exe", "pythonw.exe"] + list(nv.ENGINE_IMAGES),
            "allow_remote": [], "allow_loopback": True}
    data["run"] = {k: v for k, v in spec.items() if k != "name"}
    guard, ok = sb.Guard(name, name), False
    try:
        with guard:
            if not guard_context.read()["admitted"]:
                raise RuntimeError("house context changed/expired; no retry")
            with sb.job_scope(name) as scope:
                data["job"] = dict(scope.descriptor)
                v = nv.Verifier(spec, scope)
                v.before()
                try:
                    pid = sb.start(name, [executable, "-I", "-S", "-c", FIXTURE, str(ready),
                                          "--sandbox-profile=" + str(profile)], job=scope)
                    v.explain(pid)
                    deadline = time.monotonic() + 8
                    while not ready.exists() and time.monotonic() < deadline:
                        time.sleep(0.02)
                    fixture = json.loads(ready.read_text(encoding="utf-8"))
                    data["fixture"] = fixture
                    v.explain(fixture["grandchild"])
                    v.start_sampling(0.1)
                    time.sleep(2.0)
                    data["gate"] = v.gate()
                    time.sleep(0.5)
                    v.stop_sampling()
                    seen = {r[3] for s in v.samples for r in s.get("tcp", [])}
                    data["sampler_saw_fixture_ports"] = {"listen": fixture["listen"] in seen,
                                                        "client": fixture["client"] in seen}
                    data["sandbox_windows_max_ours"] = max(
                        (s.get("windows", {}).get(f"agora-sandbox-{name}", {}).get("ours", 0) for s in v.samples),
                        default=0)
                finally:
                    v.stop_sampling()
                    if sb.state_file(name).exists():
                        data["cleanup"] = sb.close(name, quiet=True)
                    v.after()
                    data["verdict"] = v.verdict()
    except BaseException as exc:
        data["error"] = error(exc)
    finally:
        if hasattr(guard, "first"):
            code, words = guard.verdict()
            data["guard"] = {"code": code, "verdict": words}
            if not guard.first.get("foreground"):
                data["guard"]["verdict"] = "unknown Alex-screen continuity: local foreground unavailable"
        else:
            data["guard"] = {"code": 1, "verdict": "guard not started"}
        data["house_postflight"] = {"admitted": guard_context.read()["admitted"]}
        verdict = data.get("verdict") or {}
        ok = (not data.get("error") and (data.get("cleanup") or {}).get("ok") and data["guard"]["code"] == 0
              and all(verdict.get(k, {}).get("status") in ("observed", "unknown")
                      for k in ("family", "windows", "network", "writes")))
        data["result"] = ("completed: each check reported observed or unknown with its limits (see verdict)" if ok
                          else "failed or refused; no retry")
        write(report, data)
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        write(EVIDENCE / f"fake-{time.strftime('%Y%m%d')}.json", data)
    print(str(report))
    print(json.dumps({k: data.get(k) for k in ("result", "error", "guard", "sampler_saw_fixture_ports",
                                                "sandbox_windows_max_ours")}, indent=2))
    for k in ("family", "windows", "network", "writes"):
        x = (data.get("verdict") or {}).get(k, {})
        print(k, x.get("status"), "|", x.get("observed"), "|", x.get("reasons"))
    return 0 if ok else 1


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    raise SystemExit(reads() if mode == "reads" else run() if mode == "run" else
                     sys.exit("usage: check_native_run_fake.py reads|run"))
