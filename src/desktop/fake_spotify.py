"""fake_spotify.py: a stand-in for Spotify's accounts and Web API, on this PC only (a6443). 17 Oct 2026.

    python fake_spotify.py [port]          serve one until stopped (default 8798)

What spotify_like.py speaks, and nothing more, held in memory: /authorize (answers at once with a redirect to the
redirect_uri, as Spotify does after Agree; checks the PKCE challenge later), /api/token (authorization_code with the
verifier, refresh_token), /v1/me/player/currently-playing, /v1/me/library/contains, PUT and DELETE /v1/me/library.
Fake.playing is what it says is playing; Fake.liked the URIs in its Liked Songs; Fake.fail makes the next call answer
a code (401, 403, 429); Fake.calls lists what was asked. Nothing here reaches Spotify or anyone's library.
"""
import base64
import hashlib
import json
import secrets
import sys
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Fake:
    def __init__(self, port=0):
        self.playing = {"type": "track", "uri": "spotify:track:fake0001", "name": "Night Drive",
                        "artists": [{"name": "Stand-in Band"}]}
        self.liked, self.calls, self.fail = set(), [], []
        self.codes, self.access, self.refresh = {}, set(), set()
        fake = self

        class H(BaseHTTPRequestHandler):
            def _send(self, code, body=None, headers=()):
                b = b"" if body is None else json.dumps(body).encode()
                self.send_response(code)
                for k, v in headers:
                    self.send_header(k, v)
                if body is not None:
                    self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)

            def _q(self):
                u = urllib.parse.urlparse(self.path)
                return u.path, dict(urllib.parse.parse_qsl(u.query))

            def _authed(self):
                tok = (self.headers.get("Authorization") or "").removeprefix("Bearer ")
                if fake.fail:
                    code = fake.fail.pop(0)
                    self._send(code, {"error": {"status": code}})
                    return False
                if tok not in fake.access:
                    self._send(401, {"error": {"status": 401, "message": "The access token expired"}})
                    return False
                return True

            def do_GET(self):
                path, q = self._q()
                fake.calls.append(("GET", path, q))
                if path == "/authorize":
                    code = secrets.token_urlsafe(8)
                    fake.codes[code] = (q.get("code_challenge"), q.get("redirect_uri"), q.get("client_id"))
                    loc = q["redirect_uri"] + "?" + urllib.parse.urlencode({"code": code, "state": q.get("state", "")})
                    return self._send(302, None, [("Location", loc)])
                if not self._authed():
                    return
                if path == "/v1/me/player/currently-playing":
                    return self._send(204) if not fake.playing else self._send(200, {"is_playing": True, "item": fake.playing})
                if path == "/v1/me/library/contains":
                    return self._send(200, [u in fake.liked for u in q.get("uris", "").split(",") if u])
                self._send(404, {"error": {"status": 404}})

            def _change(self, add):
                path, q = self._q()
                fake.calls.append(("PUT" if add else "DELETE", path, q))
                if not self._authed():
                    return
                if path != "/v1/me/library":
                    return self._send(404, {"error": {"status": 404}})
                for u in q.get("uris", "").split(","):
                    (fake.liked.add if add else fake.liked.discard)(u)
                self._send(200)

            def do_PUT(self):
                self._change(True)

            def do_DELETE(self):
                self._change(False)

            def do_POST(self):
                path, _ = self._q()
                n = int(self.headers.get("Content-Length") or 0)
                f = dict(urllib.parse.parse_qsl(self.rfile.read(n).decode()))
                fake.calls.append(("POST", path, {k: v for k, v in f.items() if k in ("grant_type", "client_id")}))
                if path != "/api/token":
                    return self._send(404, {"error": "not_found"})
                if f.get("grant_type") == "authorization_code":
                    c = fake.codes.pop(f.get("code"), None)
                    want = base64.urlsafe_b64encode(hashlib.sha256((f.get("code_verifier") or "").encode()).digest()).decode().rstrip("=")
                    if not c or c[0] != want or c[1] != f.get("redirect_uri") or c[2] != f.get("client_id"):
                        return self._send(400, {"error": "invalid_grant"})
                elif f.get("grant_type") == "refresh_token":
                    if f.get("refresh_token") not in fake.refresh:
                        return self._send(400, {"error": "invalid_grant"})
                else:
                    return self._send(400, {"error": "unsupported_grant_type"})
                a, r = "A" + secrets.token_urlsafe(12), "R" + secrets.token_urlsafe(12)
                fake.access.add(a)
                fake.refresh.add(r)
                self._send(200, {"access_token": a, "token_type": "Bearer", "expires_in": 3600, "refresh_token": r,
                                 "scope": "user-library-read user-library-modify user-read-currently-playing"})

            def log_message(self, *a):
                pass

        self.srv = ThreadingHTTPServer(("127.0.0.1", port), H)
        self.port = self.srv.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def expire(self):
        """Every access token stops working (the next call gets 401 and must refresh)."""
        self.access.clear()

    def close(self):
        self.srv.shutdown()
        self.srv.server_close()


def browser(url):
    """A stand-in for Alex's browser on the consent page: it presses Agree (follows the redirect)."""
    import urllib.request
    urllib.request.urlopen(url, timeout=10).read()


if __name__ == "__main__":
    f = Fake(int(sys.argv[1]) if len(sys.argv) > 1 else 8798)
    print(f"fake Spotify at {f.url} (accounts and api: {f.url}/v1); Ctrl+C stops it")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        f.close()
