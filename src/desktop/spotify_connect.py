"""Explicit Connect button: local Client ID form, then Spotify's PKCE consent.

Nothing opens at import/startup. Tests supply a stand-in browser and Library.
The form takes an app identifier only, never a password or client secret.
"""
import html
import secrets
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

from spotify_like import PORT, REDIRECT, ConnectionFailure, open_connection_page


def connect(library, open_page, *, port=PORT, wait=300):
    cid = library.client_id()
    if not cid:
        nonce = secrets.token_urlsafe(32)
        answer = {}

        class Form(BaseHTTPRequestHandler):
            def reply(self, code, body):
                body = body.encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Security-Policy", "default-src 'none'; form-action 'self'")
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                q = urllib.parse.urlparse(self.path)
                if q.path != "/setup" or urllib.parse.parse_qs(q.query).get("state") != [nonce]:
                    return self.reply(404, "Not found")
                self.reply(200, '<!doctype html><title>Connect Spotify</title>'
                    '<h1>Connect Spotify</h1><p>Create a Web API app at '
                    '<a href="https://developer.spotify.com/dashboard">Spotify for Developers</a>. '
                    'Its redirect address must be <code>' + html.escape(REDIRECT) + '</code>.</p>'
                    '<p>Development Mode requires the app owner to have Premium.</p>'
                    '<p>Finish creating your app first. If this temporary page expires, '
                    'press Connect Spotify for a fresh page.</p>'
                    '<form method="post" action="/setup">'
                    '<input type="hidden" name="state" value="' + nonce + '">'
                    '<label>Client ID <input name="client_id" required pattern="[a-zA-Z0-9]{16,64}" '
                    'autocomplete="off"></label><button>Continue to Spotify</button></form>'
                    '<p>No password or client secret belongs here.</p>')

            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                if self.path != "/setup" or not 0 < n <= 1024:
                    return self.reply(400, "Invalid request")
                data = urllib.parse.parse_qs(self.rfile.read(n).decode("utf-8"))
                import re
                candidate = data.get("client_id", [""])[0].strip()
                if data.get("state") != [nonce] or not re.fullmatch(r"[a-zA-Z0-9]{16,64}", candidate):
                    return self.reply(400, "Invalid request")
                answer["client_id"] = candidate
                self.reply(200, "Opening Spotify's consent page. You can close this tab.")

            def log_message(self, *args):
                pass

        try:
            server = HTTPServer(("127.0.0.1", 0), Form)
        except Exception:
            raise ConnectionFailure("setup_bind") from None
        try:
            server.timeout = 0.25
            url = f"http://127.0.0.1:{server.server_port}/setup?state={nonce}"
            failed = open_connection_page(open_page, url, "setup")
            until = time.monotonic() + wait
            while not answer:
                if failed.is_set():
                    raise ConnectionFailure("setup_browser")
                if time.monotonic() >= until:
                    break
                try:
                    server.handle_request()
                except Exception:
                    raise ConnectionFailure("setup_wait") from None
            if failed.is_set():
                raise ConnectionFailure("setup_browser")
        finally:
            server.server_close()
        if not answer:
            raise ConnectionFailure("setup_expired")
        cid = answer["client_id"]
    return library.connect(open_page, cid, port=port, wait=wait)
