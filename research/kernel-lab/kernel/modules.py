"""EDITING THE KERNEL (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
The kernel changes only to give every world a general capability: a word, a check, a kind of fact any app, module or
person can use. It never names its tenants: no app, module, person, kind or field name appears in this code except the
kernel's own (word, rule, kind, grant, person, ...). If your change needs `if kind == "..."`, a person's name or one app's
field, stop: the missing piece is a general word (a kind's policy, a rule step, a reading). Build that, or put it on the
Board. Names already here are debt (research/source-edits/SOURCE-AUDIT-KERNEL.md lists them); take them out when you can.

Modules: processes in any language that speak lines (SHAPE section 11).

Newline-separated JSON over the module's stdin and stdout. Every message has a type `t`.

    kernel -> module            module -> kernel
    hello {module, id, grants,  offer {words: [{word, kind, takes, help, may?, undo?, acts_on?, needs?}]}
                                (acts_on/needs: the shape the word's code reads; kinds.py)
           owner, place, for?,
           home}
    call {use, word, args,      see {use, line}        -> kernel answers {t: rows, use, text, rows, refused?}
          caller}               answer {use, lines?, text?, rows?, saw?, refused?}
                                accepted {use}        (external work only; a slow call returns "starting",
                                                       caller readings stay open until its final answer;
                                                       the module delivers the eventual receipt itself)
    done {use, ok, record?,     (after an answer with lines: whether the kernel admitted it, and what it made)
          made, text}
                                do {id, line, saw?}    -> {t: done, id, ok, text, rows, record?, made, refused?}
                                see {id, line}         -> {t: rows, id, ok, text, rows, refused?}
                                (a module on its own, outside any call: its grants alone, and its person's rights
                                 when it is installed `for` one)
    status? {use}               status {use, doing}
    off                         (it exits; after 2 s the kernel ends it)

Every message from a module goes through `ModuleProcess.handle`, so an extension adds a message type by overriding it.

The kernel starts the process, so the kernel can always stop it. A module holds no lock of the kernel's: it works while
the kernel serves others, reads through see words, and hands back lines, which the kernel admits or refuses whole.
What the process does on the machine (files, network) is NOT contained here; see SHAPE section 11.
"""
import json
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

CALL_TIMEOUT = 10.0
STATUS_TIMEOUT = 2.0
NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0      # CREATE_NO_WINDOW: nothing appears on the screen


class ModuleProcess:
    def __init__(self, host, mid, argv, cwd):
        self.host, self.mid = host, mid
        self.proc = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1,
                                     creationflags=NO_WINDOW)
        self.write_lock = threading.Lock()
        self.pending = {}          # use -> {"event", "answer", "caller"}
        self.offered = threading.Event()
        self.offer_receipt = []
        self.err = []
        self.stdout_closed = threading.Event()
        threading.Thread(target=self._read, daemon=True).start()
        self.err_thread = threading.Thread(target=self._read_err, daemon=True)
        self.err_thread.start()

    def alive(self):
        return self.proc.poll() is None

    def send(self, msg):
        with self.write_lock:
            try:
                self.proc.stdin.write(json.dumps(msg) + "\n")
                self.proc.stdin.flush()
            except (BrokenPipeError, OSError, ValueError):
                pass

    def _read_err(self):
        """What the module says on stderr: its last 20 lines here, for refusals and status, and all of it in
        `<world>/modules/<name>/stderr.log` (the desktop's kext kept this; 23 Oct)."""
        fh = None
        try:
            k = self.host.kernel
            home = Path(k.dir) / "modules" / str(k.state.get(self.mid, "name") or self.mid)
            home.mkdir(parents=True, exist_ok=True)
            fh = open(home / "stderr.log", "a", encoding="utf-8")
            fh.write(f"--- started {time.strftime('%Y-%m-%d %H:%M:%S')} pid {self.proc.pid}\n")
            fh.flush()
        except OSError:
            fh = None
        try:
            for line in self.proc.stderr:
                self.err = (self.err + [line.rstrip()])[-20:]
                if fh:
                    try:
                        fh.write(line)
                        fh.flush()
                    except (OSError, ValueError):
                        fh = None
        except (ValueError, OSError):
            pass                                   # `stop` closed the pipe under us
        if fh:
            fh.close()

    def _read(self):
        try:
            for line in self.proc.stdout:
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    self.err = (self.err + [f"not JSON: {line.strip()[:200]}"])[-20:]
                    continue
                try:
                    self.handle(msg)
                except Exception as exc:                # noqa: BLE001  one bad message never stops the reader
                    self.err = (self.err + [f"{msg.get('t')} failed in the kernel: {exc!r}"])[-20:]
                    self.host.kernel.refusals.keep(f"its {msg.get('t')} message failed in the kernel: {exc!r}",
                                                   str(msg.get("line") or msg.get("word") or ""), by=self.mid,
                                                   via="module", kind="error")
        except (ValueError, OSError):
            pass                                   # `stop` closed the pipe under us: the module is ending anyway
        finally:
            self.stdout_closed.set()
            for p in list(self.pending.values()):
                p["event"].set()                   # the process ended: every open call is answered by its absence

    def handle(self, msg):
        """One message from the module. Unknown types are ignored."""
        k = self.host.kernel
        t = msg.get("t")
        if t == "offer":
            self.offer_receipt = k.on_offer(self.mid, msg.get("words") or [])
            self.offered.set()
        elif t == "see" and msg.get("use") in self.pending:
            # answered on its own thread, so this reader keeps reading while the kernel works
            threading.Thread(target=self._see, args=(self.pending[msg["use"]]["caller"], msg), daemon=True).start()
        elif t in ("see", "do") and msg.get("id"):
            threading.Thread(target=self._own, args=(msg,), daemon=True).start()     # a module on its own
        elif t == "see":
            self.send({"t": "rows", "use": msg.get("use"), "refused": "no call of yours is open with that use"})
        elif t == "accepted":
            # An external operation can outlive the synchronous receipt deadline.
            # Keep its caller's narrowed reading context until the final answer.
            p = self.pending.get(msg.get("use"))
            if p is not None:
                p["accepted"] = {"t": "answer", "use": msg["use"], "external": True,
                                 "text": "starting; you will hear when the request settles",
                                 "rows": [{"request": msg["use"], "status": "starting"}]}
        elif t in ("answer", "status"):
            p = self.pending.get(msg.get("use"))
            if p is not None:
                p["answer"] = msg
                p["event"].set()
                if p.get("detached"):
                    # Never apply late declarative lines after a caller returned.
                    self.pending.pop(msg["use"], None)
        elif t == "happen":
            said = k.announce(self.mid, str(msg.get("word") or ""), msg.get("target"), msg.get("text") or "")
            if said != "ok":
                self.send({"t": "refused", "about": "happen", "word": msg.get("word"), "why": said})
                k.refusals.keep(said, f"happen {msg.get('word') or ''}", by=self.mid, via="module")
        elif t == "hold":
            lease, why = k.hold(self.mid, str(msg.get("word") or ""))
            self.send({"t": "held", "use": msg.get("use"), "word": msg.get("word"),
                       **({"lease": lease} if lease else {"refused": why})})
        elif t == "release":
            k.release(lease=msg.get("lease"))

    def _own(self, msg):
        k = self.host.kernel
        mode = "see" if msg["t"] == "see" else "do"
        r = k.module_own(self.mid, str(msg.get("line") or ""), mode=mode, saw=msg.get("saw"))
        self.send({"t": "rows" if mode == "see" else "done", "id": msg.get("id"), "ok": r["ok"],
                   "text": r.get("text", ""), "rows": r.get("rows", []), "made": r.get("made", []),
                   **({"record": r["records"][-1]} if r.get("records") else {}),
                   **({"refused": r["text"]} if not r["ok"] else {})})

    def _see(self, caller, msg):
        r = self.host.kernel.module_see(self.mid, caller, msg.get("line", ""))
        self.send({"t": "rows", "use": msg.get("use"), "text": r.get("text", ""), "rows": r.get("rows", []),
                   **({"refused": r["refused"]} if r.get("refused") else {})})

    def ask(self, msg, timeout, caller=None):
        use = uuid.uuid4().hex[:12]
        p = {"event": threading.Event(), "answer": None, "caller": caller}
        self.pending[use] = p
        self.send(dict(msg, use=use))
        p["event"].wait(timeout)
        if p["answer"] is None and p.get("accepted"):
            p["detached"] = True
            if p["answer"] is None:
                return p["accepted"]
        self.pending.pop(use, None)
        return p["answer"]

    def stop(self):
        self.send({"t": "off"})
        try:
            self.proc.wait(2)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(2)
        for s in (self.proc.stdin, self.proc.stdout, self.proc.stderr):
            try:
                s.close()
            except (OSError, ValueError):
                pass


class Host:
    """Starts and stops each module the world says is on (level-triggered: `reconcile` after every act)."""

    REST_S = 30.0     # a module that died is not started again for this long, so a crash is not a loop

    def __init__(self, kernel, root):
        self.kernel, self.root = kernel, Path(root)
        self.procs = {}
        self.died = {}           # mid -> (time, its last error line)
        self.lock = threading.Lock()
        kernel.modules = self

    def running(self, mid):
        p = self.procs.get(mid)
        return bool(p and p.alive())

    def why_down(self, mid):
        d = self.died.get(mid)
        if not d:
            return None
        left = self.REST_S - (time.time() - d[0])
        when = time.strftime("%H:%M:%S", time.localtime(d[0]))
        return (f"it stopped at {when} ({d[1] or 'it gave no reason'})"
                + (f"; it will be started again in {left:.0f} s" if left > 0 else ""))

    def reconcile(self):
        k = self.kernel
        with k.lock:
            want = {m: k.state.get(m, "run") for m in k.things("module") if k.state.get(m, "on")}
        with self.lock:
            for mid in list(self.procs):
                if mid not in want or not self.procs[mid].alive():
                    p = self.procs.pop(mid)
                    if mid in want:                    # on, but its process ended by itself: it died
                        self.died[mid] = (time.time(), (p.err[-1] if p.err else ""))
                        k.refusals.keep(f"{k.name(mid)} stopped by itself: {'; '.join(p.err[-3:]) or 'it gave no reason'}"
                                        f"; started again in {self.REST_S:g} s", "", by=mid, via="module", kind="died")
                    k.release(mid=mid)                 # whatever it held ends with it
                    threading.Thread(target=p.stop, daemon=True).start()
            for mid, run in want.items():
                d = self.died.get(mid)
                if d and time.time() - d[0] < self.REST_S:
                    continue
                if mid not in self.procs:
                    self.procs[mid] = p = ModuleProcess(self, mid, run, self.root)
                    p.send(k.hello_for(mid))

    def deliver(self, h):
        """A happening, to every running module that hears its word (SHAPE section 5)."""
        k = self.kernel
        for mid, p in list(self.procs.items()):
            if p.alive() and k.module_hears(mid, h):
                p.send({"t": "happen", **k.happening_for(None, h)})

    def wait_offered(self, mid, timeout=10):
        p = self.procs.get(mid)
        return p.offered.wait(timeout) if p else False

    def call(self, mid, word, args, caller):
        from .kernel import Refused
        p = self.procs.get(mid)
        name = self.kernel.state.get(mid, "name")
        ans = p.ask({"t": "call", "word": word, "args": args,
                     "caller": {"id": caller.id, "person": caller.person, "name": self.kernel.name(caller.person)}},
                    CALL_TIMEOUT, caller=caller) if p else None
        if ans is None:
            if p and p.stdout_closed.is_set():
                # its output ended before it answered: it is dying, though it may not have been reaped yet
                try:
                    p.proc.wait(2)
                except subprocess.TimeoutExpired:
                    pass
                p.err_thread.join(1)
            if p and not p.alive():
                raise Refused(f"{name} stopped while answering ({'; '.join(p.err[-2:]) or 'it gave no reason'}); "
                              f"nothing was done")
            raise Refused(f"{name} did not answer in {CALL_TIMEOUT:g} s; nothing was done")
        return ans

    def done(self, mid, use, said):
        """After an answer with lines: tell the module whether it was admitted, and what it made."""
        p = self.procs.get(mid)
        if p and use:
            p.send({"t": "done", "use": use, **said})

    def status(self, mid):
        p = self.procs.get(mid)
        ans = p.ask({"t": "status?"}, STATUS_TIMEOUT) if p else None
        return ans.get("doing") if ans else None

    def stop_all(self):
        with self.lock:
            for p in self.procs.values():
                p.stop()
            self.procs.clear()
