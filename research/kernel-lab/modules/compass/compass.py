"""A reviewed loopback compass host. Persistent configuration and points are world things.

The browser owns the actual orientation/motion sensors. This process owns their
word-layer leases and serves a page; off kills the host and all its leases. It
keeps only transient calls/leases, and never writes private storage.
"""
import json
import re
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

write_lock = threading.Lock()
pending, leases = {}, {}


def send(msg):
    with write_lock:
        print(json.dumps(msg), flush=True)


def door(value):
    if not re.fullmatch(r"http://127\.0\.0\.1:[0-9]{1,5}", value):
        raise ValueError("the compass proof accepts a loopback door only")
    return value


class Page(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, code, data, kind):
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if urllib.parse.urlsplit(self.path).path != "/":
            return self.reply(404, b"no such page", "text/plain")
        self.reply(200, Path(__file__).with_name("compass.html").read_bytes(), "text/html; charset=utf-8")

    def do_POST(self):
        # A page is a person, not a module grant: preserve its session at the door.
        if self.path != "/line" or self.headers.get("Origin") != f"http://{self.headers.get('Host')}":
            return self.reply(403, b"{}", "application/json")
        try:
            body = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length", "0")), 16384)))
            base = door(body["door"])
            mode = "/see" if body.get("see") else "/do"
            req = urllib.request.Request(base + mode, json.dumps({"line": body["line"]}).encode(),
                                         {"Content-Type": "application/json", "Cookie": self.headers.get("Cookie", "")})
            try:
                with urllib.request.urlopen(req, timeout=15) as response:
                    code, data = response.status, response.read()
            except urllib.error.HTTPError as exc:
                code, data = exc.code, exc.read()
            self.reply(code, data, "application/json")
        except (ValueError, KeyError, OSError):
            self.reply(400, b'{"error":"compass cannot reach that loopback door"}', "application/json")


server = ThreadingHTTPServer(("127.0.0.1", 0), Page)
server.daemon_threads = True
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{server.server_address[1]}"
for raw in sys.stdin:
    msg = json.loads(raw)
    kind = msg.get("t")
    if kind == "hello":
        send({"t": "offer", "words": [
            {"word": "compass.page", "kind": "see", "takes": "<id> door=<url>",
             "help": "compass.page <view> door=<loopback URL>: a phone page of world map points. Make a "
                     "compass-view with points_kind=, in_group=, solved_word= and title=. The view's own id "
                     "is used to read its configuration. Points need lat/lon/title/text; no private storage."},
            {"word": "compass.motion", "kind": "hold", "takes": "",
             "help": "compass.motion: the phone's orientation and linear acceleration while its page runs; "
                     "compass.stop or off compass releases it. Sensor permission stays the browser's."},
            {"word": "compass.start", "kind": "hold", "takes": "",
             "help": "compass.start: hold compass.motion for this person's page. The page starts sensors only "
                     "after a lease is acknowledged. compass.stop releases this person's leases."},
            {"word": "compass.stop", "kind": "do", "takes": "", "undo": "external",
             "help": "compass.stop: release this person's phone sensor leases; the page stops its sensors."}]})
    elif kind == "call":
        word, use = msg["word"], msg["use"]
        person = msg["caller"]["person"]
        if word == "compass.page":
            try:
                q = urllib.parse.urlencode({"door": door(msg["args"]["kv"]["door"]),
                                            "view": msg["args"]["target"]})
                send({"t": "answer", "use": use, "text": url + "/?" + q,
                      "rows": [{"url": url + "/?" + q}]})
            except (KeyError, ValueError):
                send({"t": "answer", "use": use, "refused": "name a view and a loopback door"})
        elif word == "compass.start":
            pending[use] = person
            send({"t": "hold", "use": use, "word": "compass.motion"})
        elif word == "compass.stop":
            for lease in leases.pop(person, []):
                send({"t": "release", "lease": lease})
            send({"t": "answer", "use": use, "external": True, "text": "phone sensors released"})
        else:
            send({"t": "answer", "use": use, "refused": "compass.motion is held through compass.start"})
    elif kind == "held":
        person = pending.pop(msg["use"], None)
        if msg.get("lease"):
            leases.setdefault(person, []).append(msg["lease"])
        send({"t": "answer", "use": msg["use"], "text": msg.get("lease", ""),
              **({"refused": msg["refused"]} if msg.get("refused") else {})})
    elif kind == "status?":
        send({"t": "status", "use": msg["use"], "doing": f"phone compass at {url}; {sum(map(len, leases.values()))} leases"})
    elif kind == "off":
        server.shutdown()
        break
server.server_close()
