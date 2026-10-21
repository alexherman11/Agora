"""spotify_like.py: Like (save to Liked Songs) from the home base's music panel (a6443). 17 Oct 2026.

    python spotify_like.py status                    connected or not, and what the house holds (never a token)
    python spotify_like.py connect                   Alex's one-time step: asks for the app's client id the first
                                                     time, then opens Spotify's consent page in his browser
    python spotify_like.py forget                    the house forgets the sign-in (the tokens file goes)

How (route 1 of a6443's three, chosen): Spotify's Web API, signed in once with OAuth's PKCE flow, which needs no
secret: a client id from an app Alex registers at developer.spotify.com, and his one consent click. Since February 2026
a Development Mode app works only while its owner has Spotify Premium, and for at most five users (his own account
is one). What it asks (SCOPES): read and change his library, and read what is playing (to know the exact track: the
system media session gives only the words title and artist, and two songs can share them).
    GET    /me/player/currently-playing        the track Spotify is playing, as a URI (spotify:track:...)
    GET    /me/library/contains?uris=<uri>     liked or not (Feb 2026: the library endpoints take URIs)
    PUT    /me/library?uris=<uri>              like: into Liked Songs
    DELETE /me/library?uris=<uri>              unlike
Where it keeps things: research/text-desk-lab/notation/house-state/spotify/ (not in git, never in the world, never in
chat): app.json {client_id}, token.json {access_token, refresh_token, expires_at}. Nothing prints a token.

The truth about what it knows (Library.state_of -> (liked, why)): yes or no only when Spotify's account says what is
playing and its name is the song Windows says; else unknown, with why (not connected, another player, Spotify said
another song, Spotify did not answer). A press on an unknown heart is refused with that why, never guessed.

Every address is a parameter (api=, accounts=, store=): tests run against fake_spotify.py, never Spotify itself, and
never Alex's library.
"""
import base64
import hashlib
import json
import os
import re
import secrets
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
STORE = HERE.parent / "text-desk-lab" / "notation" / "house-state" / "spotify"
API = "https://api.spotify.com/v1"
ACCOUNTS = "https://accounts.spotify.com"
PORT = 8797                                           # the consent page sends him back here, to this PC only
REDIRECT = f"http://127.0.0.1:{PORT}/callback"        # Spotify takes a loopback address only as 127.0.0.1, not localhost
SCOPES = "user-library-read user-library-modify user-read-currently-playing"
FRESH = 30                                            # seconds a like state is trusted before it is asked again
STEPS = ("Once: create an app at developer.spotify.com/dashboard (Web API; redirect "
         f"{REDIRECT}), press Connect Spotify here, paste its Client ID, then approve Spotify's consent page. "
         "Development Mode requires the app owner to have Premium. No client secret is needed.")
SHORT = "Spotify is not connected. Press Connect Spotify for the one-time setup."


class Refused(Exception):
    pass


# Only these authored messages may leave the connection flow. Never stringify
# browser/network/store exceptions or OAuth response fields for the panel/CLI.
CONNECT_RECOVERY = " Press Connect Spotify for a fresh attempt; old local tabs may have expired."
CONNECT_ERRORS = {
    "setup_bind": "Spotify's local setup page could not start.",
    "setup_expired": "Spotify's Client ID setup page expired. Finish creating the app first.",
    "setup_browser": "The browser could not open Spotify's Client ID setup page.",
    "setup_wait": "Spotify's local setup page stopped before receiving the Client ID.",
    "client_id": "That is not a valid Spotify Client ID. Use the app's ID, never its secret.",
    "callback_bind": "Spotify's local return listener could not start. Consent was not opened.",
    "callback_expired": "Spotify's local return listener expired before a matching answer arrived.",
    "callback_browser": "The browser could not open Spotify's consent page.",
    "callback_wait": "Spotify's local return listener stopped before a matching answer arrived.",
    "consent": "Spotify consent was declined or did not return an authorization code.",
    "exchange": "Spotify's authorization answer could not be exchanged for a sign-in.",
    "persistence": "Spotify's connection details could not be saved. Connection was not confirmed.",
    "unexpected": "Spotify did not connect because setup could not finish.",
}


class ConnectionFailure(Refused):
    def __init__(self, reason):
        self.reason = (reason if isinstance(reason, str) and reason in CONNECT_ERRORS
                       else "unexpected")
        super().__init__(CONNECT_ERRORS[self.reason] + CONNECT_RECOVERY)


def connection_message(error):
    """Public allowlist boundary, including when an unexpected exception occurs."""
    reason = error.reason if type(error) is ConnectionFailure else "unexpected"
    if not isinstance(reason, str):
        reason = "unexpected"
    return CONNECT_ERRORS.get(reason, CONNECT_ERRORS["unexpected"]) + CONNECT_RECOVERY


def open_connection_page(open_page, url, stage):
    """Keep browser launch asynchronous, but observe False/errors without leaking them."""
    failed = threading.Event()

    def run():
        try:
            if open_page(url) is False:
                failed.set()
        except Exception:
            failed.set()

    try:
        threading.Thread(target=run, daemon=True).start()
    except Exception:
        raise ConnectionFailure(stage + "_browser") from None
    return failed


def _norm(s):
    """Case/spacing only: distinct live/remastered versions must not match."""
    return " ".join((s or "").casefold().split())


class Library:
    def __init__(self, store=STORE, api=API, accounts=ACCOUNTS, fresh=FRESH):
        self.store, self.api, self.accounts, self.fresh = Path(store), api.rstrip("/"), accounts.rstrip("/"), fresh
        self.lock = threading.Lock()
        self.known = {}                 # (title, artist) -> {"uri", "liked", "why", "at"}
        self.asking = set()
        self.stopped = False
        self.connect_status = ""

    # -- the store
    def _read(self, name):
        try:
            return json.loads((self.store / name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _write(self, name, data):
        self.store.mkdir(parents=True, exist_ok=True)
        tmp = self.store / (name + ".tmp")
        tmp.write_text(json.dumps(data), encoding="utf-8")
        os.replace(tmp, self.store / name)

    def client_id(self):
        return (self._read("app.json").get("client_id") or "").strip()

    def connected(self):
        return bool(self._read("token.json").get("refresh_token"))

    # -- tokens
    def _post_form(self, url, form):
        req = urllib.request.Request(url, data=urllib.parse.urlencode(form).encode(), method="POST",
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read() or b"{}")

    def _keep(self, got, old_refresh=""):
        self._write("token.json", {"access_token": got["access_token"],
                                   "refresh_token": got.get("refresh_token") or old_refresh,
                                   "expires_at": time.time() + float(got.get("expires_in") or 3600) - 60})

    def token(self, renew=False):
        t = self._read("token.json")
        if not t.get("refresh_token"):
            raise Refused("Spotify is not connected. " + STEPS)
        if renew or time.time() >= float(t.get("expires_at") or 0):
            try:
                got = self._post_form(self.accounts + "/api/token", {"grant_type": "refresh_token",
                                      "refresh_token": t["refresh_token"], "client_id": self.client_id()})
            except urllib.error.HTTPError as e:
                if e.code in (400, 401):
                    raise Refused("Spotify's sign-in has ended (revoked or expired): connect again. " + STEPS)
                raise Refused(f"Spotify's sign-in server answered {e.code}")
            except OSError:
                raise Refused("Spotify's sign-in server did not answer")
            self._keep(got, t["refresh_token"])
            t = self._read("token.json")
        return t["access_token"]

    # -- the Web API
    def call(self, method, path, query=None, again=True):
        url = self.api + path + ("?" + urllib.parse.urlencode(query) if query else "")
        req = urllib.request.Request(url, method=method, data=b"" if method in ("PUT", "DELETE") else None,
                                     headers={"Authorization": "Bearer " + self.token()})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                body = r.read()
                return r.status, (json.loads(body) if body.strip() else None)
        except urllib.error.HTTPError as e:
            if e.code == 401 and again:
                self.token(renew=True)
                return self.call(method, path, query, again=False)
            if e.code == 403:
                raise Refused("Spotify refused it (403): a Development Mode app works only while its owner has "
                              "Premium, and only for the accounts on its user list")
            if e.code == 429:
                raise Refused("Spotify asks to wait a little (429, too many requests)")
            raise Refused(f"Spotify answered {e.code} to {method} {path}")
        except OSError:
            raise Refused("Spotify did not answer")

    def playing(self):
        """-> {uri, name, artists} of the track Spotify's account is playing, or None (nothing, or not a track)."""
        code, o = self.call("GET", "/me/player/currently-playing")
        item = (o or {}).get("item") if code == 200 else None
        if not item or item.get("type") != "track":
            return None
        return {"uri": item.get("uri"), "name": item.get("name") or "",
                "artists": [a.get("name") or "" for a in item.get("artists") or []]}

    def contains(self, uri):
        code, o = self.call("GET", "/me/library/contains", {"uris": uri})
        if code != 200 or not isinstance(o, list) or not o or not isinstance(o[0], bool):
            raise Refused("Spotify did not say whether the song is liked")
        return bool(o[0])

    # -- what the panel asks
    def check(self, title, artist):
        """Ask Spotify now (blocking). -> {"uri", "liked": yes|no|unknown, "why"} and keep it."""
        key = (title, artist)
        try:
            p = self.playing()
            if not p:
                got = {"uri": "", "liked": "unknown", "why": "Spotify's account says nothing is playing on it"}
            elif (not (p["uri"] or "").startswith("spotify:track:")
                  or _norm(p["name"]) != _norm(title) or not artist
                  or _norm(artist) not in {_norm(a) for a in p["artists"]}):
                got = {"uri": "", "liked": "unknown", "why": "Spotify's account says another song is playing than "
                       "Windows does (another device?)"}
            else:
                got = {"uri": p["uri"], "liked": "yes" if self.contains(p["uri"]) else "no", "why": ""}
        except Refused as e:
            got = {"uri": "", "liked": "unknown", "why": str(e)}
        got["at"] = time.time()
        with self.lock:
            self.known[key] = got
        return got

    def state_of(self, title, artist, player="Spotify"):
        """-> (liked, why) at once, from what is known; asks Spotify in the background when that is old or new."""
        if player != "Spotify":
            return "unknown", f"the song is playing in {player}; Liked Songs is Spotify's"
        if not self.client_id() or not self.connected():
            return "unknown", self.connect_status or SHORT
        key = (title, artist)
        with self.lock:
            k = self.known.get(key)
            old = not k or time.time() - k["at"] > self.fresh
            if old and key not in self.asking and not self.stopped:
                self.asking.add(key)
                threading.Thread(target=self._ask, args=key, daemon=True).start()
        if not k or old:
            return "unknown", "asking Spotify"
        return k["liked"], k["why"]

    def _ask(self, title, artist):
        try:
            self.check(title, artist)
        finally:
            with self.lock:
                self.asking.discard((title, artist))

    def set(self, title, artist, liked):
        """Like (True) or unlike (False) the song playing now. -> the words said; raises Refused when it cannot know
        which track it is, or Spotify refuses."""
        k = self.check(title, artist)                  # always fresh: never like a song from a stale guess
        if k["liked"] == "unknown":
            raise Refused(k["why"])
        want = "yes" if liked else "no"
        if k["liked"] == want:
            return "already " + ("in Liked Songs" if liked else "not in Liked Songs")
        self.call("PUT" if liked else "DELETE", "/me/library", {"uris": k["uri"]})
        with self.lock:
            self.known[(title, artist)] = {**k, "liked": want, "at": time.time()}
        return ("saved to" if liked else "removed from") + " Liked Songs"

    def stop(self):
        self.stopped = True

    # -- the one-time connect (PKCE)
    def connect(self, open_page, client_id=None, port=PORT, wait=300):
        """Alex's consent, once. open_page(url) shows Spotify's page (his browser; a test's stand-in); Spotify sends
        the browser back to 127.0.0.1:<port>/callback with a code, which is traded for tokens. -> words said."""
        cid = (client_id or self.client_id()).strip()
        if not re.fullmatch(r"[0-9a-zA-Z]{16,64}", cid):
            raise ConnectionFailure("client_id")
        verifier = secrets.token_urlsafe(64)[:96]
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        state = secrets.token_urlsafe(16)
        got = {}

        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                u = urllib.parse.urlparse(self.path)
                q = dict(urllib.parse.parse_qsl(u.query))
                if u.path != "/callback":
                    self.send_response(404)
                    self.end_headers()
                    return
                ok = q.get("state") == state and "code" in q
                if q.get("state") == state:
                    got.update(q if ok else {"error": "consent was not granted"})
                body = ("Authorization received. Finishing the connection; you can close this tab." if ok else
                        "Not connected: the answer did not match this sign-in.").encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass

        try:
            srv = HTTPServer(("127.0.0.1", port), H)
        except Exception:
            raise ConnectionFailure("callback_bind") from None
        redirect = f"http://127.0.0.1:{srv.server_port}/callback"
        try:
            srv.timeout = 1
            url = self.accounts + "/authorize?" + urllib.parse.urlencode({
                "client_id": cid, "response_type": "code", "redirect_uri": redirect,
                "scope": SCOPES, "state": state,
                "code_challenge_method": "S256", "code_challenge": challenge})
            failed = open_connection_page(open_page, url, "callback")
            end = time.monotonic() + wait
            while not got:
                if failed.is_set():
                    raise ConnectionFailure("callback_browser")
                if time.monotonic() >= end:
                    break
                try:
                    srv.handle_request()
                except Exception:
                    raise ConnectionFailure("callback_wait") from None
            if failed.is_set():
                raise ConnectionFailure("callback_browser")
        finally:
            srv.server_close()
        if not got:
            raise ConnectionFailure("callback_expired")
        if "error" in got:
            raise ConnectionFailure("consent")
        try:
            tok = self._post_form(self.accounts + "/api/token", {"grant_type": "authorization_code", "code": got["code"],
                                  "redirect_uri": redirect, "client_id": cid, "code_verifier": verifier})
            if (not isinstance(tok, dict) or not tok.get("access_token")
                    or not tok.get("refresh_token")):
                raise ValueError("missing sign-in fields")
        except Exception:
            raise ConnectionFailure("exchange") from None
        try:
            self._keep(tok)
            self._write("app.json", {"client_id": cid})
        except Exception:
            raise ConnectionFailure("persistence") from None
        return "connected: the house can now read and change Liked Songs"

    def forget(self):
        try:
            (self.store / "token.json").unlink()
        except OSError:
            pass


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "status"
    lib = Library()
    if what == "status":
        print("client id:", "set" if lib.client_id() else "not set", "| signed in:", "yes" if lib.connected() else "no")
        if not lib.connected():
            print(STEPS)
    elif what == "connect":
        import webbrowser
        import spotify_connect
        try:
            print(spotify_connect.connect(lib, webbrowser.open))
        except Refused as e:
            sys.exit(str(e))
    elif what == "forget":
        lib.forget()
        print("forgotten: the house holds no Spotify sign-in now")
    else:
        sys.exit(__doc__)
