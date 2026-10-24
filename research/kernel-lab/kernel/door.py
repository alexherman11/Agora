"""The door: lines in, receipts and rows out, over HTTP on loopback (SHAPE section 10).

    POST /do   {line, press?, saw?}           a line, as whoever the session says
    POST /see  {line}                         a reading; writes nothing
    POST /keep/account {account, name, invite?, answers?, agent?}   the entry service's call (SHAPE section 3)
    GET  /health

Who acts comes only from the session: the entry service's `entry_sid` cookie (or `Authorization: Bearer <token>`, for
programs), which the kernel asks the entry service about (`POST <entry>/internal/session/check`, cached at most 30 s;
research/community-app/site/SEAM.md). An `as` in the body is ignored.

    python -m kernel.door --world <dir> --genesis <genesis.json> --port 8840 --entry http://127.0.0.1:8841
The shared secret comes from the environment (KERNEL_SHARED_SECRET), never from a file this code writes.
"""
import argparse
import hmac
import json
import os
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
    `Authorization: Bearer <secret>`, answered `{account: <record> | null, method, agent}` (SEAM.md section 3).
    -> {account: <account id>, method, agent} or None."""

    def __init__(self, url, secret, cache_s=SESSION_CACHE_S):
        self.url, self.secret, self.cache_s = url.rstrip("/"), secret, cache_s
        self.cache, self.lock = {}, threading.Lock()

    def check(self, token):
        now = time.time()
        with self.lock:
            hit = self.cache.get(token)
            if hit and hit[0] > now:
                return hit[1]
        # The agreed header is X-Kernel-Secret (SEAM.md, frozen 23 Oct); Bearer is sent too until the entry service's
        # change to it is committed, and then goes.
        req = urllib.request.Request(f"{self.url}/internal/session/check", json.dumps({"token": token}).encode(),
                                     {"Content-Type": "application/json", "X-Kernel-Secret": self.secret,
                                      "Authorization": f"Bearer {self.secret}"})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                said = json.loads(r.read())
        except urllib.error.HTTPError:
            said = {}
        except (urllib.error.URLError, OSError):
            return None                             # the entry service is away: no one is signed in, nothing cached
        # agreed: {account: <id>, method, agent, record}; an older answer put the record itself in `account`
        acct, rec = said.get("account"), said.get("record")
        if isinstance(acct, dict):
            acct, rec = acct.get("account_id"), acct
        ans = None
        if isinstance(acct, str) and acct and not (rec or {}).get("disabled"):
            ans = {"account": acct, "method": said.get("method"), "agent": said.get("agent")}
        with self.lock:
            self.cache[token] = (now + self.cache_s, ans)
        return ans


# the entry service's session cookie, on https and in test mode (agreed: agora_session; entry_sid was its first name)
SESSION_COOKIES = ("__Host-agora_session", "agora_session", "__Host-entry_sid", "entry_sid")


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
            self.wfile.write(data)

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

        def do_GET(self):
            if self.path == "/health":
                return self._send(200, {"ok": True, "records": len(kernel.log.records)})
            self._send(404, {"error": "no such route"})

        def do_POST(self):
            if self._cross_site():
                return self._send(403, {"error": "the door answers only its own pages"})
            body = self._body()
            if body is None:
                return self._send(400, {"error": "the body must be a JSON object"})
            if self.path == "/keep/account":
                # loopback and the shared secret, in X-Kernel-Secret (agreed); `Bearer <secret>` is still accepted
                given = (self.headers.get("X-Kernel-Secret") or "").encode()
                bearer = (self.headers.get("Authorization") or "").encode()
                if not secret or self.client_address[0] not in ("127.0.0.1", "::1") or not (
                        hmac.compare_digest(given, secret.encode()) or
                        hmac.compare_digest(bearer, f"Bearer {secret}".encode())):
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
            self._send(404, {"error": "no such route"})

    return Handler


def serve(kernel, entry_url, secret, port, root, cache_s=SESSION_CACHE_S):
    host = Host(kernel, root)
    host.reconcile()
    srv = ThreadingHTTPServer(("127.0.0.1", port),
                              make_handler(kernel, EntryClient(entry_url, secret, cache_s), secret))
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
