"""door: the front door that stays while deskd changes behind it (a1505, phase 1 of a1483).

    python door.py [port] [--world frontier] [--state DIR] [--no-git] [--static DIR]
                                                default port 8794, state house-state/; --static: deskd's static dir

It is meant to change almost never, and imports nothing of the desk's (no deskd, scene or desk), so a landing that
breaks those cannot break it. It:
  - holds the port browsers and the house talk to, and passes every request to the deskd behind it (a private port);
  - when git HEAD moves (unless --no-git), starts a new deskd on the new code, beside the old one. The new one is
    asked /api/health, then every scene the door served in the last two hours (the lenses people have open), built by
    the new process itself, which also fills its cache. If all answer, requests go to the new one from then on, and the
    old one finishes the calls it was answering before it is stopped. If not, the old one stays, the new one is
    stopped, and the door says why in its news;
  - answers /door/stream: a page's one long connection (Server-Sent Events). It carries the world's events, each with
    its index as its id, and the door's news. The door reads events from whichever deskd is current, so a swap is not
    seen on the stream: no gap, no duplicate. A page that reconnects says the last id it saw (Last-Event-ID);
  - answers /door/status (the code running, the news) and, to local programs only, POST /door/swap (swap now; a test
    may give the new deskd's argv and env);
  - keeps its news (each swap: when, from, to, the commits in between, whether the painter's own files changed, or why
    it was refused) in <state>/door.json, so a page opened in the evening can say what changed that day.
A request that could not reach a deskd at all (refused: it never arrived) is sent again to the current one; so is a
POST /api/do carrying a gesture id, since deskd acts once per id (a1008) and the ids live in the shared world.
Log: <state>/door.log; each deskd's output: <state>/deskd.out.
"""
import http.client
import json
import os
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PY = sys.executable
HOP = {"connection", "keep-alive", "transfer-encoding", "te", "trailer", "upgrade", "proxy-authorization",
       "proxy-authenticate", "host", "content-length", "origin", "sec-fetch-site", "sec-fetch-mode", "sec-fetch-dest"}


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def git(*args):
    try:
        return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:
        return ""


def ask(port, path, timeout=10.0, method="GET", body=None, headers=None):
    """One request to a deskd. -> (status, headers, body bytes); raises OSError when it can't be reached."""
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        c.request(method, path, body=body, headers=headers or {})
        r = c.getresponse()
        return r.status, r.getheaders(), r.read()
    finally:
        c.close()


class Backend:
    """One deskd process behind the door."""

    def __init__(self, door, code, argv=None, env=None):
        self.port, self.code, self.busy, self.started = free_port(), code, 0, time.time()
        self.lock = threading.Lock()
        out = open(door.state / "deskd.out", "a", encoding="utf-8")
        out.write(f"--- {time.strftime('%Y-%m-%d %H:%M:%S')} door starts deskd {code} on {self.port}\n")
        out.flush()
        cmd = [PY, *(argv or ["deskd.py"]), str(self.port), *([door.static] if door.static and not argv else [])]
        self.proc = subprocess.Popen(cmd, cwd=HERE, env={**os.environ, "DESKD_CODE": code, "DESKD_PARENT": str(os.getpid()), **(env or {})},
                                     stdout=out, stderr=subprocess.STDOUT)
        self.painter = None

    def alive(self):
        return self.proc.poll() is None

    def enter(self):
        with self.lock:
            self.busy += 1

    def leave(self):
        with self.lock:
            self.busy -= 1

    def stop(self, wait_busy=120.0):
        """The old one finishes the calls it is answering, then goes."""
        t = time.time() + wait_busy
        while self.busy > 0 and time.time() < t and self.alive():
            time.sleep(0.1)
        if self.alive():
            self.proc.terminate()
            try:
                self.proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.proc.kill()


class Door:
    def __init__(self, port, world, state, watch_git, static=None):
        self.port, self.world, self.state, self.watch_git, self.static = port, world, Path(state), watch_git, static
        self.state.mkdir(parents=True, exist_ok=True)
        self.current, self.swapping = None, threading.Lock()
        self.scenes = {}                 # the scene queries pages asked for: query string -> last asked (time)
        self.changed = threading.Condition()
        self.head = git("rev-parse", "HEAD") if watch_git else ""
        try:
            saved = json.loads((self.state / "door.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            saved = {}
        self.news = saved.get("news", [])[-200:]
        self.serial = len(self.news)

    def log(self, msg):
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
        print(line, flush=True)
        with (self.state / "door.log").open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def say(self, item):
        item = {"at": time.strftime("%Y-%m-%d %H:%M:%S"), **item}
        with self.changed:
            self.news = (self.news + [item])[-200:]
            self.serial += 1
            self.changed.notify_all()
        try:
            tmp = self.state / "door.json.tmp"
            tmp.write_text(json.dumps({"news": self.news}, ensure_ascii=False, indent=1), encoding="utf-8")
            os.replace(tmp, self.state / "door.json")
        except OSError as e:
            self.log(f"could not keep the news: {e}")

    def status(self):
        b = self.current
        return {"code": b.code if b else None, "painter": b.painter if b else None, "up": bool(b and b.alive()),
                "since": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(b.started)) if b else None,
                "news": self.news[-60:], "serial": self.serial}

    # ---------- starting and swapping ----------
    def healthy(self, b, timeout=90.0):
        """-> None if the new deskd answers health and every recent scene; else why not, in words."""
        t = time.time() + timeout
        while True:
            if not b.alive():
                tail = ""
                try:
                    tail = (self.state / "deskd.out").read_text(encoding="utf-8", errors="replace").strip().splitlines()[-1][:200]
                except (OSError, IndexError):
                    pass
                return f"exited ({b.proc.returncode}) before answering" + (f": {tail}" if tail else "")
            try:
                st, _h, body = ask(b.port, "/api/health", timeout=3)
                if st == 200 and json.loads(body).get("ok"):
                    break
            except (OSError, ValueError):
                pass
            if time.time() > t:
                return f"did not answer health within {int(timeout)} s"
            time.sleep(0.25)
        try:
            b.painter = json.loads(ask(b.port, "/api/version", timeout=10)[2]).get("painter")
        except (OSError, ValueError):
            pass
        old = self.current
        for qs in [q for q, at in sorted(self.scenes.items(), key=lambda x: -x[1]) if time.time() - at < 7200][:6]:
            try:
                new = json.loads(ask(b.port, "/api/scene?" + qs, timeout=60)[2])
            except (OSError, ValueError) as e:
                return f"could not build a scene a page has open ({qs}): {e}"
            if "refused" in new and old is not None and old.alive():
                try:
                    was = json.loads(ask(old.port, "/api/scene?" + qs, timeout=60)[2])
                except (OSError, ValueError):
                    was = {}
                if "refused" not in was:
                    lens = parse_qs(qs).get("lens", ["?"])[0]
                    return f"refuses lens {lens}, which the running code paints: {str(new['refused'])[:160]}"
        return None

    def start_first(self):
        while True:
            code = (git("rev-parse", "--short", "HEAD") if self.watch_git else "") or "dev"
            b = Backend(self, code)
            why = self.healthy(b)
            if why is None:
                self.current = b
                self.log(f"door: deskd {code} answers on {b.port}; the door is on {self.port}")
                return
            self.log(f"door: the first deskd ({code}) failed: {why}; trying again in 30 s")
            b.stop(0)
            time.sleep(30)

    def swap(self, code=None, argv=None, env=None, commits=None, head=None):
        """Start a new deskd beside the current one and switch to it if it is healthy. -> (ok, why)."""
        with self.swapping:
            old = self.current
            code = code or (git("rev-parse", "--short", "HEAD") if self.watch_git else "") or "dev"
            b = Backend(self, code, argv, env)
            why = self.healthy(b)
            if commits is None:
                commits = self.commits(head) if head else []
            dirty = [l[3:] for l in git("status", "--porcelain", "--untracked-files=no").splitlines() if l.endswith(".py")] if self.watch_git else []
            item = {"from": old.code if old else None, "to": code, "commits": commits,
                    **({"dirty": dirty[:8]} if dirty else {})}
            if why is not None:
                b.stop(0)
                self.log(f"door: kept {old.code if old else 'nothing'}; the new deskd ({code}) {why}")
                why = f"the new code ({code}) {why}"
                self.say({**item, "ok": False, "why": why})
                return False, why
            item["painter"] = bool(old and b.painter and old.painter and b.painter != old.painter)
            self.current = b
            self.log(f"door: now deskd {code} on {b.port} (was {old.code if old else '-'}); the old one finishes its calls")
            self.say({**item, "ok": True})
            if old is not None:
                threading.Thread(target=old.stop, daemon=True).start()
            return True, None

    def commits(self, head):
        """The commits between the code that ran and `head`, first parent only, without the docs exports."""
        rng = f"{self.head}..{head}" if self.head else f"-1 {head}"
        out = []
        for l in git("log", "--first-parent", "--format=%h%x09%s", *rng.split()).splitlines()[:20]:
            h, _, s = l.partition("\t")
            if not s.startswith("docs:"):
                out.append([h, s[:140]])
        return out

    def watch(self):
        """git HEAD moving is a landing (or anyone's commit): swap to it. A deskd that died is started again."""
        while True:
            time.sleep(2)
            try:
                if self.watch_git:
                    now = git("rev-parse", "HEAD")
                    if now and now != self.head:
                        self.log(f"door: HEAD moved {self.head[:7]} -> {now[:7]}")
                        self.swap(head=now)
                        self.head = now          # a refused swap is not tried again until HEAD moves again
                b = self.current
                if b is not None and not b.alive() and not self.swapping.locked():
                    self.log(f"door: deskd {b.code} exited ({b.proc.returncode}); starting one again")
                    self.swap(code=b.code, commits=[])
            except Exception as e:           # the door must not die of anything it watches
                self.log(f"door: watch failed: {type(e).__name__}: {e}")

    def backend(self, wait=30.0):
        t = time.time() + wait
        while time.time() < t:
            b = self.current
            if b is not None and b.alive():
                return b
            time.sleep(0.2)
        return None


DOOR = None


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8", extra=()):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def _foreign(self):
        """As deskd judges it (review 29 Sep): a page from another site. deskd sees the door's requests without Origin,
        so the door judges them first, against its own address."""
        origin = self.headers.get("Origin")
        own = {f"http://127.0.0.1:{DOOR.port}", f"http://localhost:{DOOR.port}"}
        return (origin is not None and origin not in own) or self.headers.get("Sec-Fetch-Site") == "cross-site"

    def _local_program(self):
        return self.headers.get("Origin") is None and self.headers.get("Sec-Fetch-Site") is None

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/door/status":
            return self._json(DOOR.status())
        if u.path == "/door/stream":
            return self._stream(u)
        if u.path == "/api/scene":
            q = {k: v[0] for k, v in parse_qs(u.query).items() if k != "have"}
            DOOR.scenes[urlencode(sorted(q.items()))] = time.time()
            if len(DOOR.scenes) > 40:
                DOOR.scenes.pop(min(DOOR.scenes, key=DOOR.scenes.get))
        self._pass("GET", None)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(n) if n else b""
        if urlparse(self.path).path == "/door/swap":
            if not self._local_program():
                return self._json({"error": "only a local program may swap the door's deskd"}, 403)
            try:
                a = json.loads(body or b"{}")
            except ValueError:
                return self._json({"error": "the body must be JSON"}, 400)
            ok, why = DOOR.swap(code=a.get("code"), argv=a.get("argv"), env=a.get("env"), commits=a.get("commits"))
            return self._json({"ok": ok, "why": why, **DOOR.status()})
        self._pass("POST", body)

    def _pass(self, method, body):
        if self.path.startswith("/api/") and self._foreign() or (method == "POST" and self._foreign()):
            return self._json({"error": "deskd answers only its own pages"}, 403)
        headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP}
        if body is not None:
            headers["Content-Length"] = str(len(body))
        again = method == "GET"
        if method == "POST" and urlparse(self.path).path == "/api/do":
            try:
                again = bool(json.loads(body or b"{}").get("gesture"))
            except (ValueError, AttributeError):
                again = False
        deadline = time.time() + 60
        while True:
            b = DOOR.backend()
            if b is None:
                return self._json({"error": "no deskd is answering behind the door; it is being started again"}, 503)
            b.enter()
            try:
                st, hs, data = ask(b.port, self.path, timeout=300, method=method, body=body, headers=headers)
                break
            except ConnectionRefusedError:
                pass                              # it never arrived: safe to send to whichever deskd is current
            except OSError as e:
                if not again or time.time() > deadline:
                    return self._json({"error": f"the deskd behind the door stopped while answering ({e}); "
                                                "whether it was done is unknown until the view repaints"}, 502)
            finally:
                b.leave()
            if time.time() > deadline:
                return self._json({"error": "no deskd answered behind the door within 60 s"}, 503)
            time.sleep(0.2)
        self.send_response(st)
        for k, v in hs:
            if k.lower() not in HOP:
                self.send_header(k, v)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _stream(self, u):
        """One page's long connection: the world's events (id = the event's index + 1), and the door's news."""
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        session = q.get("session", "desktop")
        since = self.headers.get("Last-Event-ID") or q.get("since")
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True

        def put(kind, data, eid=None):
            msg = (f"id: {eid}\n" if eid is not None else "") + f"event: {kind}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
            self.wfile.write(msg.encode("utf-8"))
            self.wfile.flush()

        def events(n):
            b = DOOR.backend(wait=5)
            if b is None:
                return None
            b.enter()
            try:
                st, _h, body = ask(b.port, "/api/events?" + urlencode({"session": session, "since": n}), timeout=60)
                return json.loads(body) if st == 200 else None
            except (OSError, ValueError):
                return None
            finally:
                b.leave()

        try:
            n = int(since) if since not in (None, "") else None
        except ValueError:
            n = None
        try:
            put("door", DOOR.status())
            told, beat = DOOR.serial, time.time()
            while True:
                if n is None:                   # a page with no last id starts at the present
                    r = events(10 ** 9)
                    n = r["total"] if r else None
                else:
                    r = events(n)
                    if r:
                        for k, e in enumerate(r["events"]):
                            put("world", e, n + k + 1)
                        n += len(r["events"])
                if DOOR.serial != told:
                    told = DOOR.serial
                    put("door", DOOR.status())
                if time.time() - beat > 15:
                    self.wfile.write(b": beat\n\n")
                    self.wfile.flush()
                    beat = time.time()
                with DOOR.changed:
                    DOOR.changed.wait(0.5)
        except (OSError, ValueError):
            return                               # the page went away


def main():
    global DOOR
    a = sys.argv[1:]
    port = int(next((x for x in a if x.isdigit()), "8794"))
    world = a[a.index("--world") + 1] if "--world" in a[:-1] else "frontier"
    state = a[a.index("--state") + 1] if "--state" in a[:-1] else str(HERE / "house-state")
    static = a[a.index("--static") + 1] if "--static" in a[:-1] else None
    DOOR = Door(port, world, state, "--no-git" not in a, static)
    DOOR.start_first()
    threading.Thread(target=DOOR.watch, daemon=True).start()
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    srv.daemon_threads = True
    print(f"door on http://localhost:{port}", flush=True)
    try:
        srv.serve_forever()
    finally:
        if DOOR.current:
            DOOR.current.stop(5)


if __name__ == "__main__":
    main()
