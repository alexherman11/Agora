"""gate (6 Oct, Claude, for the Seabright app): the one address people outside this machine reach, in front of the door.

    python gate.py [port] --world seabright [--door http://127.0.0.1:8794] [--state DIR] [--lens square]
                   [--host 127.0.0.1] [--secure] [--reserve alex,claude]
    python gate.py invite --by alex [--uses 1] [--days 7] [--name <name>] [--state DIR]

The door and deskd trust whoever reaches them: `as` is a word the caller supplies, and a request with no Origin is a
local program that may do anything. That is right on one machine and wrong on the internet. The gate changes neither;
it stands in front of the door and is the only thing a reverse proxy points at.

  - Nobody enters without an invite (Community App, People). An invite is a code made on this machine by a member:
    its maker, how many may use it, when it ends, and who came through it. `gate.py invite` prints its /join path.
  - /join?k=<code> asks for a name once and gives the device a key (a cookie). From then on the gate, not the page,
    says who is acting: it writes `session` and `as` into every request it passes on, whatever the page sent.
  - A name is held by one device. Names in --reserve (and house, jeff) are never given out here.
  - It passes only what a painter needs (the page's files, scene, style, version, events, observe, do, the stream),
    one world, and refuses the door's own words (visit, home, write home, worktree) and /door/swap.
  - Codes and keys are kept only as SHA-256 hashes, in <state>/gate.json, never in the world.

Not built: an invite as a thing in the world, roles, a second device for one person, leaving, rate limits beyond a
simple one per device, and anything about what a member may do once inside (everyone may do what the desk allows).
"""
import hashlib
import http.client
import json
import re
import secrets
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlencode, urlparse

HERE = Path(__file__).resolve().parent
NAME = re.compile(r"[a-z][a-z0-9_-]{1,23}$")
ALWAYS_RESERVED = {"house", "jeff", "everyone", "nobody", "all"}
API_GET = {"/api/scene", "/api/style", "/api/version", "/api/events", "/api/snapshot"}
API_POST = {"/api/do", "/api/observe"}
DOOR_WORDS = ("visit", "home", "worktree", "write home")
DO_KEYS = ("line", "observed", "gesture", "whole")
MAX_BODY = 256 * 1024
RATE = (30, 10.0)                     # at most 30 lines in any 10 s from one device
HOP = {"connection", "keep-alive", "transfer-encoding", "te", "trailer", "upgrade", "host", "content-length",
       "cookie", "origin", "sec-fetch-site", "sec-fetch-mode", "sec-fetch-dest", "x-forwarded-for"}

GATE = None


def digest(secret):
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


class Gate:
    def __init__(self, world, door, state, lens="square", secure=False, reserve=()):
        self.world, self.lens, self.secure = world, lens, secure
        u = urlparse(door)
        self.door = (u.hostname, u.port)
        self.path = Path(state) / "gate.json"
        self.reserved = ALWAYS_RESERVED | {r.strip().lower() for r in reserve if r.strip()}
        self.lock = threading.Lock()
        self.lines = {}                # device hash -> times of its recent lines
        self.load()

    def load(self):
        try:
            d = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            d = {}
        self.invites, self.devices = d.get("invites", {}), d.get("devices", {})

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps({"invites": self.invites, "devices": self.devices}, indent=1), encoding="utf-8")
        tmp.replace(self.path)

    def invite(self, by, uses=1, days=7.0, name=None):
        """-> the code, said once. Only its hash is kept."""
        code = secrets.token_urlsafe(18)
        with self.lock:
            self.load()
            self.invites[digest(code)] = {"by": by, "uses": int(uses), "came": [], "made": time.time(),
                                          "ends": time.time() + float(days) * 86400, "name": name}
            self.save()
        return code

    def open_invite(self, code):
        """-> (the invite, None) or (None, why not)."""
        inv = self.invites.get(digest(code or ""))
        if inv is None:
            return None, "This invite is not one this place made. Ask the person who sent it for a new one."
        if time.time() > inv["ends"]:
            return None, f"This invite from {inv['by']} has ended. Ask them for a new one."
        if len(inv["came"]) >= inv["uses"]:
            return None, f"This invite from {inv['by']} has been used. Ask them for a new one."
        return inv, None

    def peek(self, code):
        """As open_invite, on what is on disk now: `gate.py invite` is another process."""
        with self.lock:
            self.load()
            return self.open_invite(code)

    def join(self, code, name):
        """-> (a device key, None) or (None, why not). The key is said once."""
        with self.lock:
            self.load()
            inv, why = self.open_invite(code)
            if inv is None:
                return None, why
            name = (inv.get("name") or name or "").strip().lower()
            if not NAME.match(name):
                return None, "A name here is 2 to 24 letters, digits, - or _, starting with a letter."
            if name in self.reserved or any(d["name"] == name for d in self.devices.values()):
                return None, f"Someone here is already called {name}. Pick another name."
            key = secrets.token_urlsafe(32)
            self.devices[digest(key)] = {"name": name, "via": digest(code)[:12], "by": inv["by"], "at": time.time()}
            inv["came"].append(name)
            self.save()
        return key, None

    def who(self, cookie):
        """The name this device holds, or None."""
        for part in (cookie or "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == "desk" and v:
                d = self.devices.get(digest(v))
                return (digest(v), d["name"]) if d else None
        return None

    def may_speak(self, dev):
        now = time.time()
        with self.lock:
            t = [x for x in self.lines.get(dev, []) if now - x < RATE[1]]
            ok = len(t) < RATE[0]
            if ok:
                t.append(now)
            self.lines[dev] = t
        return ok


PAGE = """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;background:#FBFAF7;color:#14171A;margin:0;padding:24px;max-width:28em}}
input,button{{font:inherit;padding:10px;border:1px solid #14171A33;border-radius:6px;width:100%;box-sizing:border-box;margin-top:8px}}
button{{background:#3F5D73;color:#fff;border:0}} .why{{color:#A24E2C}}</style>
<h1>{title}</h1>{body}"""


def page(title, body):
    return PAGE.format(title=title, body=body).encode("utf-8")


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="text/html; charset=utf-8", extra=()):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _foreign(self):
        """A POST from a page of another site. A page of ours sends an Origin that is this Host."""
        origin = self.headers.get("Origin")
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            return True
        return origin is not None and urlparse(origin).netloc != (self.headers.get("Host") or "")

    def _home(self, name):
        return "/lens.html?" + urlencode({"session": GATE.world, "as": name, "lens": GATE.lens, "inspect": "0"})

    def _no_key(self, api):
        if api:
            return self._json({"error": "this device has no key to this place; open your invite link"}, 401)
        self._send(401, page("You need an invite", "<p>This place is entered by an invite from someone already in it. "
                                                   "Open the link or scan the code they gave you.</p>"))

    def _join_page(self, code, why=""):
        inv, gone = GATE.peek(code)
        if inv is None:
            return self._send(403, page("This invite can't be used", f"<p class=why>{esc(gone)}</p>"))
        named = inv.get("name")
        field = (f"<p>You are joining as <b>{esc(named)}</b>.</p>" if named else
                 '<label>What should people here call you?<input name="name" autocomplete="nickname" '
                 'autocapitalize="none" required minlength="2" maxlength="24"></label>')
        self._send(200, page("Join", f"<p>{esc(inv['by'])} invited you.</p>"
                                     + (f"<p class=why>{esc(why)}</p>" if why else "")
                                     + f'<form method="post" action="/join"><input type="hidden" name="k" value="{esc(code)}">'
                                       f"{field}<button>Come in</button></form>"))

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        me = GATE.who(self.headers.get("Cookie"))
        if u.path == "/join":
            if me:
                return self._send(303, b"", extra=[("Location", self._home(me[1]))])
            return self._join_page(q.get("k", ""))
        if me is None:
            return self._no_key(u.path.startswith(("/api/", "/door/")))
        dev, name = me
        if u.path == "/":
            return self._send(303, b"", extra=[("Location", self._home(name))])
        if u.path == "/door/stream":
            keep = {k: q[k] for k in ("since",) if k in q}
            return self._stream("/door/stream?" + urlencode({"session": GATE.world, **keep}))
        if u.path.startswith("/door/") or (u.path.startswith("/api/") and u.path not in API_GET):
            return self._json({"error": "the gate does not pass this on"}, 404)
        if u.path.startswith("/api/"):
            q["session"], q["as"] = GATE.world, name
            return self._pass("GET", u.path + "?" + urlencode(q), None)
        self._pass("GET", quote(u.path, safe="/-._~") + ("?" + u.query if u.query else ""), None)

    def do_POST(self):
        u = urlparse(self.path)
        n = int(self.headers.get("Content-Length", 0) or 0)
        if n > MAX_BODY:
            return self._json({"error": "that is too much to send at once"}, 413)
        body = self.rfile.read(n) if n else b""
        if self._foreign():
            return self._json({"error": "this place answers only its own pages"}, 403)
        if u.path == "/join":
            f = {k: v[0] for k, v in parse_qs(body.decode("utf-8", "replace")).items()}
            key, why = GATE.join(f.get("k", ""), f.get("name", ""))
            if key is None:
                return self._join_page(f.get("k", ""), why)
            cookie = f"desk={key}; Path=/; HttpOnly; SameSite=Lax; Max-Age=31536000" + ("; Secure" if GATE.secure else "")
            name = GATE.who("desk=" + key)[1]
            return self._send(303, b"", extra=[("Set-Cookie", cookie), ("Location", self._home(name))])
        me = GATE.who(self.headers.get("Cookie"))
        if me is None:
            return self._no_key(True)
        dev, name = me
        if u.path not in API_POST:
            return self._json({"error": "the gate does not pass this on"}, 404)
        try:
            a = json.loads(body or b"{}")
        except ValueError:
            a = None
        if not isinstance(a, dict):
            return self._json({"error": "the body must be a JSON object"}, 400)
        if u.path == "/api/do":
            a = {k: a[k] for k in DO_KEYS if k in a}
            line = str(a.get("line", "")).strip()
            for part in ([line] if a.get("whole") else line.split(";")):
                low = " ".join(part.lower().split())
                if any(low == w or low.startswith(w + " ") for w in DOOR_WORDS):
                    return self._json({"text": "", "error": f"`{part.split()[0]}` is not a word this place takes from "
                                                            "a phone or a browser. Nothing was done."})
            if not GATE.may_speak(dev):
                return self._json({"text": "", "error": "too many lines at once; wait a few seconds. Nothing was done."}, 429)
        a["session"], a["as"] = GATE.world, name
        self._pass("POST", u.path, json.dumps(a).encode("utf-8"))

    def _upstream(self, method, path, body, timeout):
        headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP}
        if body is not None:
            headers["Content-Length"] = str(len(body))
            headers["Content-Type"] = "application/json"
        c = http.client.HTTPConnection(*GATE.door, timeout=timeout)
        c.request(method, path, body=body, headers=headers)
        return c, c.getresponse()

    def _pass(self, method, path, body):
        try:
            c, r = self._upstream(method, path, body, 300)
            data = r.read()
        except OSError as e:
            return self._json({"error": f"the desk behind the gate did not answer ({e})"}, 502)
        self.send_response(r.status)
        for k, v in r.getheaders():
            if k.lower() not in HOP and k.lower() != "set-cookie":
                self.send_header(k, v)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        c.close()

    def _stream(self, path):
        try:
            c, r = self._upstream("GET", path, None, 60)
        except OSError as e:
            return self._json({"error": f"the desk behind the gate did not answer ({e})"}, 502)
        self.send_response(r.status)
        self.send_header("Content-Type", r.getheader("Content-Type") or "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        try:
            while True:
                chunk = r.read1(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
        except OSError:
            pass                                  # the page went away, or the door did
        finally:
            c.close()


def arg(a, flag, default=None):
    return a[a.index(flag) + 1] if flag in a[:-1] else default


def main():
    global GATE
    a = sys.argv[1:]
    state = arg(a, "--state", str(HERE / "house-state"))
    if a and a[0] == "invite":
        g = Gate("", "http://127.0.0.1:0", state)
        by = arg(a, "--by")
        if not by:
            sys.exit("invite --by <the member making it>")
        code = g.invite(by.lower(), uses=int(arg(a, "--uses", "1")), days=float(arg(a, "--days", "7")),
                        name=(arg(a, "--name") or "").lower() or None)
        print(f"/join?k={code}")
        return
    port = int(next((x for x in a if x.isdigit()), "8795"))
    world = arg(a, "--world")
    if not world:
        sys.exit("gate.py [port] --world <the one world this gate opens>")
    GATE = Gate(world, arg(a, "--door", "http://127.0.0.1:8794"), state, lens=arg(a, "--lens", "square"),
                secure="--secure" in a, reserve=(arg(a, "--reserve", "") or "").split(","))
    srv = ThreadingHTTPServer((arg(a, "--host", "127.0.0.1"), port), Handler)
    srv.daemon_threads = True
    print(f"gate on http://localhost:{port} for {world}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
