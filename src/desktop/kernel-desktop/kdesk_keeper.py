"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

kdesk_keeper: the part of the desktop that stays up while the kernel restarts (design approved by Alex, 28 Oct:
https://claude.ai/artifact/8AeCzyWnJZkn1jBbQX1BLf).

    pythonw kdesk_keeper.py --port 8810 --log state/keeper.log [--world ...] [--kernel-log state/kdesk.log]

It owns the two things that must not blink when the kernel restarts:
- the listening sockets (8810 and one per window), handed to each kernel with socket.share, so a page's request made
  while no kernel runs waits in the queue and is answered by the next one;
- the module processes, whose stdin/stdout it relays to whichever kernel is connected. Modules don't know.

The kernel (kdesk.py, a child) connects back over one loopback socket (AGORA_KEEPER="port secret"). When it ends,
for any reason, the keeper starts another (after 1, 2, 5, then 10 s if it keeps failing) and modules keep running.
Ask for a restart with `kdesk_keeper.py --restart-kernel` (kd_reload does this). Kill the keeper and everything ends:
modules live in its kill-on-close job and exit when their stdin closes (kdesk_off.py does this).

While no kernel is connected, a module's own line is refused ("the kernel is restarting"), as a timed-out one is.
A new kernel gets each module's last word list and live holds replayed; a module whose greeting would differ is
restarted, the others never notice.
"""
import argparse
import base64
import json
import os
import secrets
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE = HERE / "state"
INFO = STATE / "keeper.json"
NO_WINDOW = 0x08000000
GAP = "the kernel is restarting; nothing was done"


def log(*a):
    print(time.strftime("%H:%M:%S"), "keeper:", *a, flush=True)


def kill_on_close_job():
    """Children in this job end when the keeper ends, however it ends (widget_browser.py has the same)."""
    sys.path.insert(0, str(HERE))
    from widget_browser import _job_that_dies_with_us
    return _job_that_dies_with_us()


def put_in_job(job, proc):
    if not job:
        return
    import ctypes
    from ctypes import wintypes as wt
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.AssignProcessToJobObject.argtypes = [wt.HANDLE, wt.HANDLE]
    k.AssignProcessToJobObject(job, wt.HANDLE(int(proc._handle)))


class Line:
    """Newline JSON over a socket, with a write lock."""
    def __init__(self, sock):
        self.sock, self.lock = sock, threading.Lock()
        self.rf = sock.makefile("r", encoding="utf-8", newline="\n")

    def send(self, msg):
        data = (json.dumps(msg) + "\n").encode("utf-8")
        with self.lock:
            self.sock.sendall(data)

    def __iter__(self):
        for line in self.rf:
            if line.strip():
                yield json.loads(line)

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


class Mod:
    """One module process the keeper started, and what it has said that a new kernel needs again."""
    def __init__(self, keeper, mid, argv, cwd, env, log_path):
        self.keeper, self.mid, self.argv, self.cwd = keeper, mid, list(argv), cwd
        self.env, self.log_path, self.replaced = env, log_path, False
        self.hello = None              # the last greeting a kernel sent it
        self.offer = None              # the last word list it offered
        self.holds = {}                # its lease -> word
        self.lease_map = {}            # its lease -> the current kernel's lease
        self.asked = {}                # hold use -> word, while a kernel answers
        self.wlock = threading.Lock()
        self.proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1,
                                     creationflags=NO_WINDOW)
        put_in_job(keeper.job, self.proc)
        self.log = None
        if log_path:
            try:
                Path(log_path).parent.mkdir(parents=True, exist_ok=True)
                self.log = open(log_path, "a", encoding="utf-8")
                self.log.write(f"--- started {time.strftime('%Y-%m-%d %H:%M:%S')} pid {self.proc.pid} (by the keeper)\n")
                self.log.flush()
            except OSError:
                self.log = None
        threading.Thread(target=self._out, daemon=True, name=f"out-{mid}").start()
        threading.Thread(target=self._err, daemon=True, name=f"err-{mid}").start()

    def alive(self):
        return self.proc.poll() is None

    def write(self, msg):
        with self.wlock:
            try:
                self.proc.stdin.write(json.dumps(msg) + "\n")
                self.proc.stdin.flush()
            except (BrokenPipeError, OSError, ValueError):
                pass

    def _out(self):
        try:
            for line in self.proc.stdout:
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    self.keeper.to_kernel({"t": "err", "mid": self.mid, "line": f"not JSON: {line.strip()[:200]}"})
                    continue
                self.keeper.from_module(self, msg)
        except (ValueError, OSError):
            pass
        code = self.proc.wait()
        if self.log:
            self.log.close()
        self.keeper.module_ended(self, code)

    def _err(self):
        try:
            for line in self.proc.stderr:
                if self.log:
                    try:
                        self.log.write(line)
                        self.log.flush()
                    except (OSError, ValueError):
                        pass
                self.keeper.to_kernel({"t": "err", "mid": self.mid, "line": line.rstrip()})
        except (ValueError, OSError):
            pass

    def stop(self):
        self.write({"t": "off"})
        try:
            self.proc.wait(2)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/PID", str(self.proc.pid), "/T", "/F"], capture_output=True,
                           creationflags=NO_WINDOW)
            try:
                self.proc.wait(3)
            except subprocess.TimeoutExpired:
                pass


class Keeper:
    def __init__(self, a):
        self.a = a
        self.secret = secrets.token_urlsafe(24)
        self.widget_key = secrets.token_urlsafe(32)       # one key for every kernel: modules read it once, at start
        self.job = kill_on_close_job()
        self.lock = threading.RLock()
        self.mods = {}                  # mid -> Mod
        self.listeners = {}             # port -> listening socket
        self.memory = {}                # what a kernel asked to have back next time (window leases)
        self.kernel = None              # Line to the connected kernel
        self.kernel_pid = None
        self.kernel_proc = None
        self.restart = threading.Event()
        self.stopping = False
        self.ctl = socket.socket()
        self.ctl.bind(("127.0.0.1", 0))
        self.ctl.listen(16)

    # ---------------------------------------------------------------- sockets
    def listen(self, port):
        with self.lock:
            if port and port in self.listeners:
                return port
            s = socket.socket()
            s.bind(("127.0.0.1", port))          # no SO_REUSEADDR: a taken port fails loudly (door.Server says why)
            s.listen(128)
            port = s.getsockname()[1]
            self.listeners[port] = s
            return port

    def share(self, port, pid):
        return base64.b64encode(self.listeners[port].share(pid)).decode()

    # ---------------------------------------------------------------- the kernel
    def kernel_loop(self):
        backoff = [1, 2, 5, 10]
        fails = 0
        while not self.stopping:
            env = dict(os.environ, AGORA_KEEPER=f"{self.ctl.getsockname()[1]} {self.secret}")
            argv = [sys.executable, str(HERE / "kdesk.py"), "--port", str(self.a.port)]
            if self.a.world:
                argv += ["--world", self.a.world]
            if self.a.kernel_log:
                argv += ["--log", self.a.kernel_log]
            argv += self.a.kernel_args
            began = time.time()
            self.restart.clear()
            self.kernel_proc = p = subprocess.Popen(argv, cwd=str(HERE), env=env, creationflags=NO_WINDOW)
            put_in_job(self.job, p)
            log(f"kernel started (pid {p.pid})")
            while p.poll() is None and not self.restart.is_set() and not self.stopping:
                time.sleep(0.2)
            if p.poll() is None:
                # ask it to stop taking requests and finish the ones it has (they'd be cut off by a kill), then end
                # it: new requests wait in the ports' queues for the next kernel
                self.to_kernel({"t": "drain"})
                try:
                    p.wait(3)
                except subprocess.TimeoutExpired:
                    pass
                self.kill_kernel(p)
                log("kernel stopped for a restart")
                fails = 0
                continue
            log(f"kernel ended by itself (code {p.returncode})")
            fails = fails + 1 if time.time() - began < 30 else 1
            wait = backoff[min(fails - 1, len(backoff) - 1)]
            log(f"starting it again in {wait} s")
            end = time.time() + wait
            while time.time() < end and not self.restart.is_set() and not self.stopping:
                time.sleep(0.2)

    def kill_kernel(self, p):
        pids = [str(p.pid)] + ([str(self.kernel_pid)] if self.kernel_pid else [])
        for pid in pids:
            subprocess.run(["taskkill", "/PID", pid, "/T", "/F"], capture_output=True, creationflags=NO_WINDOW)
        try:
            p.wait(5)
        except subprocess.TimeoutExpired:
            pass

    def to_kernel(self, msg):
        k = self.kernel
        if k is None:
            return False
        try:
            k.send(msg)
            return True
        except OSError:
            return False

    def serve_kernel(self, line, first):
        if first.get("secret") != self.secret:
            line.close()
            return
        with self.lock:
            if self.kernel is not None:
                self.kernel.close()
            self.kernel, self.kernel_pid = line, int(first["pid"])
            for m in self.mods.values():
                m.lease_map = {}
            welcome = {"t": "welcome", "widget_key": self.widget_key, "memory": self.memory,
                       "listeners": {str(p): self.share(p, self.kernel_pid) for p in self.listeners},
                       "modules": {mid: {"pid": m.proc.pid, "argv": m.argv} for mid, m in self.mods.items() if m.alive()}}
        line.send(welcome)
        log(f"kernel connected (pid {self.kernel_pid}); {len(self.listeners)} ports, {len(self.mods)} modules kept")
        try:
            for msg in line:
                self.from_kernel(line, msg)
        except (OSError, ValueError):
            pass
        with self.lock:
            if self.kernel is line:
                self.kernel, self.kernel_pid = None, None
                log("kernel gone; ports and modules kept")

    def from_kernel(self, line, msg):
        t = msg.get("t")
        rid = msg.get("rid")
        if t == "listen":
            try:
                port = self.listen(int(msg.get("port") or 0))
                line.send({"t": "reply", "rid": rid, "port": port, "share": self.share(port, self.kernel_pid)})
            except OSError as exc:
                line.send({"t": "reply", "rid": rid, "error": str(exc)})
        elif t == "remember":
            self.memory[str(msg.get("key"))] = msg.get("value")
        elif t == "start":
            line.send(dict(self.start_module(msg), t="reply", rid=rid))
        elif t == "send":
            self.to_module(str(msg.get("mid")), msg.get("msg") or {})
        elif t == "stop":
            m = self.mods.get(str(msg.get("mid")))
            if m:
                threading.Thread(target=m.stop, daemon=True).start()

    # ---------------------------------------------------------------- modules
    def start_module(self, msg):
        mid, argv = str(msg["mid"]), list(msg["argv"])
        with self.lock:
            m = self.mods.get(mid)
            if m and m.alive() and m.argv == argv:
                return {"pid": m.proc.pid, "adopted": True}
            if m and m.alive():                       # the world now runs it differently: a fresh one
                m.stop()
            m = Mod(self, mid, argv, msg.get("cwd"), msg.get("env"), msg.get("log"))
            self.mods[mid] = m
            log(f"module {mid} started (pid {m.proc.pid})")
            return {"pid": m.proc.pid, "adopted": False}

    def to_module(self, mid, msg):
        m = self.mods.get(mid)
        if not m:
            return
        t = msg.get("t")
        if t == "hello":
            same = m.hello == msg
            first = m.hello is None
            m.hello = msg
            if first or not same:
                if not first:                           # its greeting changed (grants, owner): only it restarts
                    log(f"module {mid}: greeting changed; restarting it")
                    m.replaced = True
                    m.stop()
                    with self.lock:
                        m = self.mods[mid] = Mod(self, mid, m.argv, m.cwd, m.env, m.log_path)
                    m.hello = msg
                    log(f"module {mid} started again (pid {m.proc.pid})")
                m.write(msg)
                return
            self.replay(m)                              # the same greeting: it never hears the restart
            return
        if t == "held" and str(msg.get("use", "")).startswith("keeper:"):
            word = m.asked.pop(msg["use"], None)
            old = msg["use"].split(":", 2)[2]
            if msg.get("lease"):
                m.lease_map[old] = msg["lease"]
            else:
                log(f"module {mid}: hold {word} {old} not given back: {msg.get('refused')}")
                m.holds.pop(old, None)
            return
        if t == "held" and msg.get("lease"):
            word = m.asked.pop(msg.get("use"), msg.get("word"))
            m.holds[msg["lease"]] = word
        m.write(msg)

    def replay(self, m):
        if m.offer is not None:
            self.to_kernel({"t": "from", "mid": m.mid, "msg": m.offer})
        for lease, word in list(m.holds.items()):
            use = f"keeper:{m.mid}:{lease}"
            m.asked[use] = word
            self.to_kernel({"t": "from", "mid": m.mid, "msg": {"t": "hold", "use": use, "word": word}})
        log(f"module {m.mid}: kept; replayed its words and {len(m.holds)} hold(s)")

    def from_module(self, m, msg):
        t = msg.get("t")
        if t == "offer":
            m.offer = msg
        elif t == "hold":
            m.asked[msg.get("use")] = msg.get("word")
        elif t == "release":
            lease = msg.get("lease")
            m.holds.pop(lease, None)
            msg = dict(msg, lease=m.lease_map.pop(lease, lease))
        if self.to_kernel({"t": "from", "mid": m.mid, "msg": msg}):
            return
        # no kernel: answer what waits for an answer, as a refusal; drop the rest
        if t in ("do", "see") and msg.get("id"):
            m.write({"t": "done" if t == "do" else "rows", "id": msg["id"], "ok": False, "text": GAP, "rows": [],
                     "made": [], "refused": GAP})
        elif t == "see" and msg.get("use"):
            m.write({"t": "rows", "use": msg.get("use"), "refused": GAP})
        elif t == "hold":
            m.asked.pop(msg.get("use"), None)
            m.write({"t": "held", "use": msg.get("use"), "word": msg.get("word"), "refused": GAP})

    def module_ended(self, m, code):
        with self.lock:
            if self.mods.get(m.mid) is m:
                del self.mods[m.mid]
        log(f"module {m.mid} ended (code {code})")
        if m.replaced:
            return                                      # a fresh copy took its place; the kernel need not know
        self.to_kernel({"t": "exit", "mid": m.mid, "code": code})

    # ---------------------------------------------------------------- control
    def accept_loop(self):
        while not self.stopping:
            try:
                conn, _ = self.ctl.accept()
            except OSError:
                return
            threading.Thread(target=self.serve_conn, args=(conn,), daemon=True).start()

    def serve_conn(self, conn):
        line = Line(conn)
        try:
            first = next(iter(line))
        except (StopIteration, OSError, ValueError):
            line.close()
            return
        if first.get("t") == "kernel":
            return self.serve_kernel(line, first)
        if first.get("secret") != self.secret:
            return line.close()
        cmd = first.get("t")
        if cmd == "restart-kernel":
            log("restart asked for")
            self.restart.set()
            line.send({"ok": True, "text": "the kernel restarts; windows and modules stay"})
        elif cmd == "status":
            line.send({"ok": True, "kernel": self.kernel_pid, "ports": sorted(self.listeners),
                       "modules": {mid: m.proc.pid for mid, m in self.mods.items()}})
        line.close()

    def run(self):
        self.a.port = self.listen(self.a.port)            # the door's port first: taken means another desktop runs
        info = Path(self.a.info)
        info.parent.mkdir(parents=True, exist_ok=True)
        tmp = info.with_suffix(".tmp")
        tmp.write_text(json.dumps({"pid": os.getpid(), "port": self.ctl.getsockname()[1], "secret": self.secret,
                                   "door": self.a.port}))
        os.replace(tmp, info)
        threading.Thread(target=self.accept_loop, daemon=True, name="keeper-ctl").start()
        log(f"keeping port {self.a.port}; control on {self.ctl.getsockname()[1]}")
        try:
            self.kernel_loop()
        finally:
            self.stopping = True
            for m in list(self.mods.values()):
                m.stop()


def ask(cmd, info_path=INFO):
    """For kd_reload and kdesk_on: talk to a running keeper. -> its answer, or None if none runs."""
    try:
        info = json.loads(Path(info_path).read_text())
        s = socket.create_connection(("127.0.0.1", info["port"]), timeout=5)
    except (OSError, ValueError, KeyError):
        return None
    line = Line(s)
    try:
        line.send({"t": cmd, "secret": info["secret"]})
        return next(iter(line), None)
    except (OSError, ValueError):
        return None
    finally:
        line.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8810)
    ap.add_argument("--world")
    ap.add_argument("--log")
    ap.add_argument("--kernel-log")
    ap.add_argument("--info", default=str(INFO), help="where it says how to reach it (a trial keeper uses its own)")
    ap.add_argument("--restart-kernel", action="store_true")
    ap.add_argument("--status", action="store_true")
    a, rest = ap.parse_known_args()
    a.kernel_args = rest
    if a.restart_kernel or a.status:
        print(ask("restart-kernel" if a.restart_kernel else "status", a.info) or "no keeper is running")
        return
    if a.log:
        Path(a.log).parent.mkdir(parents=True, exist_ok=True)
        sys.stdout = sys.stderr = open(a.log, "a", encoding="utf-8", buffering=1)
    Keeper(a).run()


if __name__ == "__main__":
    main()
