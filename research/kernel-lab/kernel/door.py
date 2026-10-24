"""The door: lines in, receipts and rows out, over HTTP on loopback (SHAPE section 10).

    POST /do   {line, press?, saw?}           a line, as whoever the session says
    POST /see  {line}                         a reading; writes nothing
    POST /keep/account {account, name, invite?, answers?, agent?}   the entry service's call (SHAPE section 3)
    GET  /health

Who acts comes only from the session: the entry service's `agora_session` cookie (or `Authorization: Bearer <token>`, for
programs), which the kernel asks the entry service about (`POST <entry>/internal/session/check`, cached at most 30 s;
research/community-app/site/SEAM.md). An `as` in the body is ignored.

    python -m kernel.door --world <dir> --genesis <genesis.json> --port 8840 --entry http://127.0.0.1:8841
The shared secret comes from the environment (KERNEL_SHARED_SECRET), never from a file this code writes.
"""
import argparse
import hmac
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .kernel import Kernel, Refused
from .modules import Host

SESSION_CACHE_S = 30


class EntryClient:
    """Asks the entry service who a session token belongs to: `POST <entry>/internal/session/check {token}` with
    `X-Kernel-Secret: <secret>`, answered `{account: <id> | null, method, agent, record}` (SEAM.md section 3, frozen
    and committed by the sign-in story in ea15bb2). -> {account: <account id>, method, agent} or None."""

    def __init__(self, url, secret, cache_s=SESSION_CACHE_S):
        self.url, self.secret, self.cache_s = url.rstrip("/"), secret, cache_s
        self.cache, self.lock = {}, threading.Lock()

    def check(self, token):
        now = time.time()
        with self.lock:
            hit = self.cache.get(token)
            if hit and hit[0] > now:
                return hit[1]
        req = urllib.request.Request(f"{self.url}/internal/session/check", json.dumps({"token": token}).encode(),
                                     {"Content-Type": "application/json", "X-Kernel-Secret": self.secret})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                said = json.loads(r.read())
        except urllib.error.HTTPError:
            said = {}
        except (urllib.error.URLError, OSError):
            return None                             # the entry service is away: no one is signed in, nothing cached
        acct, rec = said.get("account"), said.get("record")
        ans = None
        if isinstance(acct, str) and acct and not (rec or {}).get("disabled"):
            ans = {"account": acct, "method": said.get("method"), "agent": said.get("agent")}
        with self.lock:
            self.cache[token] = (now + self.cache_s, ans)
        return ans


# the entry service's session cookie, on https and in test mode
SESSION_COOKIES = ("__Host-agora_session", "agora_session")


def make_handler(kernel, entry, secret):
    class Handler(BaseHTTPRequestHandler):
        server_version = "agora-kernel/0"

        def log_message(self, *a):
            pass

        def _send(self, code, body):
            data = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass                                    # a pane closed while its read was being painted

        def _body(self):
            n = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(n) or b"{}")
            except json.JSONDecodeError:
                return None
            return body if isinstance(body, dict) else None

        def _cross_site(self):
            origin = self.headers.get("Origin")
            return origin is not None and origin != f"http://{self.headers.get('Host')}"

        def _actor(self):
            token = None
            auth = self.headers.get("Authorization") or ""
            if auth.startswith("Bearer "):
                token = auth[7:].strip()
            for part in (self.headers.get("Cookie") or "").split(";"):
                k, _, v = part.strip().partition("=")
                if k in SESSION_COOKIES and v:
                    token = token or v
            if not token:
                return None, "sign in first"
            who = entry.check(token)
            if not who or not who.get("account"):
                return None, "this session is not signed in (or has ended); sign in again"
            pid = kernel.accounts.get(who["account"])
            if pid is None:
                return None, "this account has not joined the place yet"
            return kernel.actor_for(pid, who.get("agent")), None

        def _raw(self, code, data, ctype, extra=()):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(data)))
            for k, v in extra:
                self.send_header(k, v)
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass                                    # navigation cancelled an asset request

        def _stream(self, since):
            """Server-sent events: one `world` message per record, carrying only its number (what changed is read
            through the scene, with who-sees applied), and the happenings the reader may see as `happen`."""
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            actor, _ = self._actor()
            seq = since if since is not None else len(kernel.log.records)
            hap = len(kernel.happenings)
            try:
                self.wfile.write(b": the kernel's stream\n\n")
                self.wfile.flush()
                while True:
                    with kernel.changed:
                        if len(kernel.log.records) == seq and len(kernel.happenings) == hap:
                            kernel.changed.wait(15)
                    n = len(kernel.log.records)
                    out = b""
                    while seq < n:
                        seq += 1
                        out += f"id: {seq}\nevent: world\ndata: {json.dumps({'seq': seq})}\n\n".encode()
                    for h in kernel.happenings[hap:]:
                        if actor is not None and kernel.may_hear(actor.person, h):
                            out += f"event: happen\ndata: {json.dumps(kernel.happening_for(actor.person, h))}\n\n".encode()
                    hap = len(kernel.happenings)
                    self.wfile.write(out or b": still here\n\n")
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
                return

        def do_GET(self):
            from urllib.parse import parse_qs, urlparse
            u = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            if u.path == "/health":
                return self._send(200, {"ok": True, "records": len(kernel.log.records)})
            if u.path in ("/door/stream", "/stream"):
                last = self.headers.get("Last-Event-ID") or q.get("since")
                return self._stream(int(last) if last and last.isdigit() else None)
            if u.path == "/dev/signin" and kernel.dev_sessions is not None:
                # dev only (start_kernel.py --dev-entry): sets the session cookie on this loopback origin, then goes on
                tok = q.get("token", "")
                nxt = q.get("next", "/lens.html")
                if self.client_address[0] not in ("127.0.0.1", "::1") or tok not in kernel.dev_sessions() \
                        or not nxt.startswith("/"):
                    return self._send(403, {"error": "not a dev session"})
                return self._raw(302, b"", "text/plain", [("Location", nxt), (
                    "Set-Cookie", f"agora_session={tok}; HttpOnly; SameSite=Lax; Path=/")])
            if u.path == "/api/version":
                return self._send(200, painter.version_info())
            if u.path in ("/web", "/web/", "/web/host.js", "/web/host.css"):
                page = {"/web": "index.html", "/web/": "index.html"}.get(u.path, u.path.rsplit("/", 1)[-1])
                from .painter import LAB, TYPES
                file = LAB / "hosts" / "web" / page
                return self._raw(200, file.read_bytes(), TYPES[file.suffix])
            if u.path in ("/api/scene", "/api/style"):
                actor, why = self._actor()
                if actor is None:
                    return self._send(401, {"error": why, "refused": why})
                fn = painter.scene if u.path == "/api/scene" else painter.style
                return self._send(200, fn(actor.person, q))
            from .painter import static_file
            got = static_file(u.path)
            if got:
                return self._raw(200, got[0], got[1])
            self._send(404, {"error": "no such route"})

        def do_POST(self):
            if self._cross_site():
                return self._send(403, {"error": "the door answers only its own pages"})
            body = self._body()
            if body is None:
                return self._send(400, {"error": "the body must be a JSON object"})
            if self.path == "/keep/account":
                # loopback and the shared secret, in X-Kernel-Secret (SEAM.md, frozen)
                given = (self.headers.get("X-Kernel-Secret") or "").encode()
                if not secret or self.client_address[0] not in ("127.0.0.1", "::1") or not hmac.compare_digest(given, secret.encode()):
                    return self._send(403, {"error": "only the entry service may call this"})
                try:
                    out = kernel.join(body.get("account"), body.get("name"), body.get("invite"),
                                      body.get("answers"), body.get("agent"))
                except Refused as exc:
                    return self._send(403, {"refused": str(exc)})
                return self._send(200, out)
            if self.path in ("/do", "/see"):
                actor, why = self._actor()
                if actor is None:
                    return self._send(401, {"error": why})
                line = body.get("line")
                if not isinstance(line, str) or not line.strip():
                    return self._send(400, {"error": "an empty line"})
                out = kernel.run(actor, line, press=body.get("press"), saw=body.get("saw"),
                                 mode="see" if self.path == "/see" else "do")
                out["as"] = kernel.name(actor.id)
                return self._send(200, out)
            if self.path in ("/api/do", "/api/observe", "/api/selection"):
                actor, why = self._actor()
                if actor is None:
                    return self._send(401, {"error": why})
                if self.path == "/api/do":
                    if not str(body.get("line") or "").strip():
                        return self._send(400, {"error": "an empty line"})
                    return self._send(200, painter.do(actor, body))
                if self.path == "/api/observe":
                    return self._send(200, {"ok": True, "kept": 0})       # a page's report: not kept on the kernel yet
                return self._send(200, {"error": "selection snapshots are not on the kernel yet"})
            if self.path == "/api/style":
                from .painter import desk_modules
                return self._send(200, desk_modules()["style"].for_painter({"text": str(body.get("text", ""))},
                                                                         body.get("theme")))
            self._send(404, {"error": "no such route"})

    from .painter import Facade
    painter = Facade(kernel)
    return Handler


class Server(ThreadingHTTPServer):
    # On Windows SO_REUSEADDR lets a second server bind a port another already holds, and requests then go to either:
    # a taken port must fail loudly instead (found 23 Oct: a stand-in shared 8818 with the entry service's fake Google)
    allow_reuse_address = sys.platform != "win32"
    daemon_threads = True
    # the default listen queue is 5: on Council night twenty phones pressing at once beside thirty open streams had a
    # connection reset (WinError 10054, found 23 Oct)
    request_queue_size = 128


def serve(kernel, entry_url, secret, port, root, cache_s=SESSION_CACHE_S):
    srv = Server(("127.0.0.1", port), make_handler(kernel, EntryClient(entry_url, secret, cache_s), secret))
    host = Host(kernel, root)
    host.reconcile()
    srv.daemon_threads = True
    return srv, host


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--genesis")
    ap.add_argument("--port", type=int, default=8840)
    ap.add_argument("--entry", default="http://127.0.0.1:8841")
    a = ap.parse_args()
    genesis = json.loads(Path(a.genesis).read_text(encoding="utf-8")) if a.genesis else None
    k = Kernel(a.world, genesis)
    srv, host = serve(k, a.entry, os.environ.get("KERNEL_SHARED_SECRET", ""), a.port, Path(__file__).resolve().parent.parent)
    print(f"kernel on http://127.0.0.1:{srv.server_address[1]} · world {a.world} · {len(k.log.records)} records", flush=True)
    try:
        srv.serve_forever()
    finally:
        host.stop_all()


if __name__ == "__main__":
    main()
