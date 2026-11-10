"""A local stand-in for Google's sign-in, for test mode and the tests.

It speaks the same three endpoints the real flow uses (authorize, token,
certs), checks the client, the redirect address and PKCE the way Google does,
and signs ID tokens with a fresh RSA key. It only listens on loopback and the
entry service refuses to use it outside test mode. It looks nothing like
Google on purpose: it is a plain test page.
"""

from __future__ import annotations

import base64
import hashlib
import html
import json
import secrets
import threading
import time
import urllib.parse
from wsgiref.simple_server import WSGIRequestHandler, make_server

from . import jwt_rs256

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Google stand-in (test mode)</title>
<style>
body{{font:16px/1.5 system-ui,sans-serif;background:#fffbe8;color:#3a3320;margin:0;padding:24px}}
main{{max-width:420px;margin:0 auto;background:#fff;border:2px dashed #c9a227;border-radius:12px;padding:24px}}
h1{{font-size:20px;margin:0 0 4px}} p{{margin:0 0 16px;color:#6b5f3a}}
label{{display:block;font-size:14px;margin:12px 0 4px}}
input{{width:100%;box-sizing:border-box;padding:10px;border:1px solid #d8cfa8;border-radius:8px;font:inherit}}
button{{margin-top:16px;padding:10px 16px;border-radius:8px;border:0;background:#3a3320;color:#fff;font:inherit;cursor:pointer}}
button.quiet{{background:transparent;color:#6b5f3a;text-decoration:underline}}
</style></head><body><main>
<h1>Google stand-in</h1>
<p>Test mode only. This page pretends to be Google so sign-in can be tried without real keys.</p>
<form method="post" action="/authorize">
{hidden}
<label for="email">Email</label><input id="email" name="email" type="email" value="maya@example.com" required>
<label for="name">Name on the Google account</label><input id="name" name="name" value="Maya Rivera">
<button type="submit" name="choice" value="allow">Continue as this person</button>
<button class="quiet" type="submit" name="choice" value="cancel" formnovalidate>Cancel</button>
</form></main></body></html>"""


class StandIn:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str,
                 issuer: str, clock=time.time):
        self.client_id, self.client_secret = client_id, client_secret
        self.redirect_uri, self.issuer = redirect_uri, issuer
        self.clock = clock
        self.key = jwt_rs256.generate_key(2048)
        self.kid = "stand-in-" + secrets.token_hex(4)
        self.codes: dict[str, dict] = {}
        self.lock = threading.Lock()
        # Knobs the tests turn to imitate a misbehaving or hostile provider.
        self.tamper: dict = {}

    # -- WSGI ----------------------------------------------------------------
    def __call__(self, environ, start_response):
        path, method = environ.get("PATH_INFO", ""), environ["REQUEST_METHOD"]
        query = dict(urllib.parse.parse_qsl(environ.get("QUERY_STRING", "")))
        form = {}
        if method == "POST":
            size = int(environ.get("CONTENT_LENGTH") or 0)
            form = dict(urllib.parse.parse_qsl(environ["wsgi.input"].read(min(size, 65536)).decode()))
        if path == "/authorize" and method == "GET":
            return self._authorize_page(query, start_response)
        if path == "/authorize" and method == "POST":
            return self._authorize_answer(form, start_response)
        if path == "/token" and method == "POST":
            return self._token(form, start_response)
        if path == "/certs":
            return self._json(start_response, "200 OK", {"keys": [jwt_rs256.public_jwk(self.key, self.kid)]})
        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return [b"not here"]

    def _authorize_page(self, q, start_response):
        problems = []
        if q.get("client_id") != self.client_id:
            problems.append("unknown client")
        if q.get("redirect_uri") != self.redirect_uri:
            problems.append("redirect address not registered")
        if q.get("response_type") != "code" or q.get("code_challenge_method") != "S256":
            problems.append("needs code flow with S256 PKCE")
        if not q.get("state") or not q.get("nonce") or not q.get("code_challenge"):
            problems.append("missing state, nonce or challenge")
        if "openid" not in q.get("scope", "").split():
            problems.append("missing openid scope")
        if problems:
            start_response("400 Bad Request", [("Content-Type", "text/plain")])
            return ["; ".join(problems).encode()]
        keep = ("state", "nonce", "code_challenge")
        hidden = "".join(
            f'<input type="hidden" name="{k}" value="{html.escape(q[k], quote=True)}">' for k in keep)
        body = PAGE.format(hidden=hidden).encode()
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [body]

    def _authorize_answer(self, f, start_response):
        state = f.get("state", "")
        if f.get("choice") != "allow":
            return self._redirect(start_response, {"error": "access_denied", "state": state})
        code = secrets.token_urlsafe(24)
        email = f.get("email", "").strip()
        with self.lock:
            self.codes[code] = {"nonce": f.get("nonce", ""), "challenge": f.get("code_challenge", ""),
                                "email": email, "name": f.get("name", "").strip(),
                                "at": self.clock(), "used": False}
        return self._redirect(start_response, {"code": code, "state": state})

    def issue_code(self, nonce: str, challenge: str, email: str, name: str) -> str:
        """For tests: what pressing Continue would have produced."""
        code = secrets.token_urlsafe(24)
        with self.lock:
            self.codes[code] = {"nonce": nonce, "challenge": challenge, "email": email,
                                "name": name, "at": self.clock(), "used": False}
        return code

    def _token(self, f, start_response):
        bad = lambda why: self._json(start_response, "400 Bad Request", {"error": why})  # noqa: E731
        if f.get("grant_type") != "authorization_code":
            return bad("unsupported_grant_type")
        if f.get("client_id") != self.client_id or f.get("client_secret") != self.client_secret:
            return bad("invalid_client")
        if f.get("redirect_uri") != self.redirect_uri:
            return bad("invalid_grant")
        with self.lock:
            entry = self.codes.get(f.get("code", ""))
            if not entry or entry["used"] or self.clock() - entry["at"] > 300:
                return bad("invalid_grant")
            entry["used"] = True
        digest = hashlib.sha256(f.get("code_verifier", "").encode()).digest()
        if base64.urlsafe_b64encode(digest).rstrip(b"=").decode() != entry["challenge"]:
            return bad("invalid_grant")
        now = int(self.clock())
        sub = "1" + str(int(hashlib.sha256(entry["email"].lower().encode()).hexdigest()[:15], 16))
        claims = {"iss": self.issuer, "aud": self.client_id, "azp": self.client_id,
                  "sub": sub, "email": entry["email"], "email_verified": True,
                  "name": entry["name"], "iat": now, "exp": now + 3600, "nonce": entry["nonce"]}
        claims.update(self.tamper.get("claims", {}))
        key = self.tamper.get("key", self.key)
        token = jwt_rs256.sign(claims, key, self.tamper.get("kid", self.kid))
        if self.tamper.get("alg_none"):
            head = jwt_rs256.b64url_encode(json.dumps({"alg": "none", "kid": self.kid}).encode())
            token = head + "." + token.split(".")[1] + "."
        return self._json(start_response, "200 OK", {
            "access_token": secrets.token_urlsafe(16), "token_type": "Bearer",
            "expires_in": 3600, "scope": "openid email profile", "id_token": token})

    def _redirect(self, start_response, params):
        location = self.redirect_uri + "?" + urllib.parse.urlencode(params)
        start_response("303 See Other", [("Location", location), ("Content-Length", "0")])
        return [b""]

    @staticmethod
    def _json(start_response, status, obj):
        body = json.dumps(obj).encode()
        start_response(status, [("Content-Type", "application/json"),
                                ("Content-Length", str(len(body)))])
        return [body]


class _Quiet(WSGIRequestHandler):
    def log_message(self, *args):
        pass


def serve_in_thread(stand_in: StandIn, port: int):
    server = make_server("127.0.0.1", port, stand_in, handler_class=_Quiet)
    thread = threading.Thread(target=server.serve_forever, daemon=True, name="google-stand-in")
    thread.start()
    return server
