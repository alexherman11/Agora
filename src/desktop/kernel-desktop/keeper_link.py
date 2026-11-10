"""keeper_link: the kernel's side of kdesk_keeper. Only used when the keeper started this kernel (AGORA_KEEPER set);
without it kdesk works exactly as before, so tests and trial worlds don't change.

- KeptModule stands in for kernel.modules.ModuleProcess: same fields and methods the Host and the kernel use, but
  the process belongs to the keeper, so it outlives this kernel.
- serve_on(...) builds the door's server on a listening socket the keeper shares, so the port never closes.
- KeptOrigins stands in for kdesk.WindowOrigins: each window keeps its port across kernel restarts.
"""
import base64
import json
import os
import socket
import subprocess
import threading
from pathlib import Path

LINK = None


class _Proc:
    """The bits of a Popen the kernel reads: pid, poll, wait."""
    def __init__(self, pid, mod):
        self.pid, self.mod, self.returncode = pid, mod, None

    def poll(self):
        return self.returncode if self.mod.stdout_closed.is_set() else None

    def wait(self, timeout=None):
        if not self.mod.stdout_closed.wait(timeout):
            raise subprocess.TimeoutExpired("module", timeout)
        return self.returncode


class Link:
    def __init__(self, spec):
        port, secret = spec.split()
        self.sock = socket.create_connection(("127.0.0.1", int(port)), timeout=10)
        self.sock.settimeout(None)
        self.rf = self.sock.makefile("r", encoding="utf-8", newline="\n")
        self.wlock = threading.Lock()
        self.replies, self.rid = {}, 0
        self.mods = {}
        self._send({"t": "kernel", "secret": secret, "pid": os.getpid()})
        self.welcome = json.loads(self.rf.readline())
        self.widget_key = self.welcome["widget_key"]
        self.memory = dict(self.welcome.get("memory") or {})
        threading.Thread(target=self._read, daemon=True, name="keeper-link").start()

    def _send(self, msg):
        data = (json.dumps(msg) + "\n").encode("utf-8")
        with self.wlock:
            self.sock.sendall(data)

    def send(self, msg):
        try:
            self._send(msg)
        except OSError:
            pass

    def request(self, msg, timeout=30):
        with self.wlock:
            self.rid += 1
            rid = self.rid
        box = {"event": threading.Event(), "answer": None}
        self.replies[rid] = box
        self._send(dict(msg, rid=rid))
        if not box["event"].wait(timeout):
            raise RuntimeError(f"the keeper did not answer {msg.get('t')}")
        return box["answer"]

    def _read(self):
        try:
            for line in self.rf:
                if not line.strip():
                    continue
                msg = json.loads(line)
                t = msg.get("t")
                if t == "drain":
                    threading.Thread(target=self._drain, daemon=True).start()
                    continue
                if t == "reply":
                    box = self.replies.pop(msg.get("rid"), None)
                    if box:
                        box["answer"] = msg
                        box["event"].set()
                    continue
                m = self.mods.get(str(msg.get("mid")))
                if m is None:
                    continue
                if t == "from":
                    try:
                        m.handle(msg.get("msg") or {})
                    except Exception as exc:              # noqa: BLE001  one bad message never stops the reader
                        m.err = (m.err + [f"{(msg.get('msg') or {}).get('t')} failed in the kernel: {exc!r}"])[-20:]
                elif t == "err":
                    m.err = (m.err + [str(msg.get("line"))])[-20:]
                elif t == "exit":
                    m.ended(msg.get("code"))
        except (OSError, ValueError):
            pass
        # the keeper is gone: so is everything this kernel served; end, the keeper's job ends us anyway
        os._exit(3)

    serving = staticmethod(lambda: [])   # -> every server on the keeper's sockets (kdesk sets it)

    def _drain(self):
        """Stop accepting (the keeper's sockets keep queueing), give requests in progress a second, then end.
        Live streams never finish; their pages reconnect to the same port."""
        import time
        stops = [threading.Thread(target=s.shutdown, daemon=True) for s in self.serving()]
        for t in stops:
            t.start()
        for t in stops:
            t.join(1)
        time.sleep(1)
        os._exit(0)

    def shared(self, port):
        """A listening socket for this port, from the keeper (made there if new). -> socket"""
        blob = (self.welcome.get("listeners") or {}).get(str(port))
        if blob is None:
            r = self.request({"t": "listen", "port": port})
            if r.get("error"):
                raise OSError(r["error"])
            blob, port = r["share"], r["port"]
            self.welcome.setdefault("listeners", {})[str(port)] = blob
        return socket.fromshare(base64.b64decode(blob))

    def remember(self, key, value):
        self.memory[key] = value
        self.send({"t": "remember", "key": key, "value": value})


def connect():
    """-> the Link, or None when this kernel was not started by a keeper."""
    global LINK
    spec = os.environ.get("AGORA_KEEPER")
    if not spec or LINK is not None:
        return LINK
    LINK = Link(spec)
    return LINK


def serve_on(server_cls, sock, handler):
    """The door's server, on a socket that is already listening (the keeper's)."""
    srv = server_cls(sock.getsockname(), handler, bind_and_activate=False)
    srv.socket.close()
    srv.socket = sock
    srv.server_address = sock.getsockname()
    return srv


def install(KM):
    """Modules started by this kernel's Host become the keeper's."""
    base = KM.ModuleProcess

    class KeptModule(base):
        def __init__(self, host, mid, argv, cwd):            # noqa: super().__init__ would start a process
            self.host, self.mid = host, mid
            self.write_lock = threading.Lock()
            self.pending, self.offer_receipt, self.err = {}, [], []
            self.offered, self.stdout_closed = threading.Event(), threading.Event()
            self.err_thread = threading.Thread(target=lambda: None, daemon=True)
            self.err_thread.start()
            k = host.kernel
            home = Path(k.dir) / "modules" / str(k.state.get(mid, "name") or mid)
            LINK.mods[mid] = self
            # a module (and all it starts) never gets AGORA_KEEPER: a House review's test kernel joined the live keeper
            # with it and knocked Alex's kernel off (28 Oct 21:24)
            r = LINK.request({"t": "start", "mid": mid, "argv": list(argv), "cwd": str(cwd), "env": {e: v for e, v in os.environ.items() if e != "AGORA_KEEPER"},
                              "log": str(home / "stderr.log")})
            self.proc = _Proc(r.get("pid"), self)
            self.adopted = bool(r.get("adopted"))

        def alive(self):
            return not self.stdout_closed.is_set()

        def send(self, msg):
            if not self.stdout_closed.is_set():
                LINK.send({"t": "send", "mid": self.mid, "msg": msg})

        def ended(self, code):
            if LINK.mods.get(self.mid) is self:
                LINK.mods.pop(self.mid, None)
            self.proc.returncode = code
            self.stdout_closed.set()
            for p in list(self.pending.values()):
                p["event"].set()

        def stop(self):
            LINK.send({"t": "stop", "mid": self.mid})
            self.stdout_closed.wait(6)

    KM.ModuleProcess = KeptModule
    return KeptModule


def kept_origins(base_cls, server_cls, door_port):
    """kdesk.WindowOrigins, but each window's port is the keeper's and stays the same across kernel restarts."""
    class KeptOrigins(base_cls):
        def __init__(self, kernel, handler):
            super().__init__(kernel, handler)
            self.by_port = {}
            leases = LINK.memory.get("window-ports") or {}
            self.waiting = []
            for port in sorted({int(p) for p in (LINK.welcome.get("listeners") or {})} - {int(door_port)}):
                self.waiting.append(self._serve(port, start=False))
            self.leases = {w: self.by_port[p] for w, p in leases.items() if p in self.by_port}

        def begin(self):
            """Answer on the kept window ports (once the kept modules are back: kdesk.start)."""
            for server in self.waiting:
                self._go(server)
            self.waiting = []

        @staticmethod
        def _go(server):
            threading.Thread(target=server.serve_forever, kwargs={"poll_interval": .1}, daemon=True,
                             name="window-door").start()

        def _serve(self, port, start=True):
            server = serve_on(server_cls, LINK.shared(port), self.handler)
            self.servers.append(server)
            self.by_port[server.server_address[1]] = server
            if start:
                self._go(server)
            return server

        def origin(self, wid):
            with self.lock:
                with self.kernel.lock:
                    active = {w for w in self.kernel.things("window") if not self.kernel.state.get(w, "forgotten")}
                if wid not in active:
                    raise ValueError("no such window")
                self.leases = {w: s for w, s in self.leases.items() if w in active}
                if wid not in self.leases:
                    used = set(self.leases.values())
                    server = next((s for s in self.servers if s not in used), None) or self._serve(0)
                    self.leases[wid] = server
                    LINK.remember("window-ports", {w: s.server_address[1] for w, s in self.leases.items()})
                return f"http://127.0.0.1:{self.leases[wid].server_address[1]}"

        def close(self):
            for server in self.servers:
                server.shutdown()       # this kernel stops serving; the keeper's socket stays open

    return KeptOrigins
