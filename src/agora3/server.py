"""Loopback transport, durable conversation and independent recovery.
Never give authored frames operator credentials or execute their source on the host.
"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit

from agora3.bridge import NativeBridge
from agora3.chat_activity import ChatActivity
from agora3.gateway import Gateway
from agora3.http_transport import BoundedHTTPServer
from agora3.jeff import Jeff
from agora3.world import Refusal, encoded

FRAME = (Path(__file__).parent / "host/frame.html").read_text(encoding="utf-8")

RECOVERY = (Path(__file__).parent / "host/recovery.html").read_text(encoding="utf-8")


class Application:
    def __init__(self, directory):
        self.gateway = Gateway(directory)
        self.directory = Path(directory)
        self.gateway.seed()
        self.chat_lock = threading.RLock()
        self.running, self.events, self.reply, self.error = False, [], "", None
        self.activity = ChatActivity()
        self.jeff = self.jeff_identity = None
        self._status_cache = (0, {})
        self.bridge = NativeBridge(self.gateway)
        self.gateway.native_bridge = self.bridge
        self.bridge_error = None

    def connect_guest(self):
        try:
            result = self.bridge.start()
            self.bridge_error = None
            return result
        except Exception as exc:
            self.bridge_error = str(exc)
            return {"connected": False, "error": self.bridge_error}

    def _agent(self):
        identity = self.gateway.principal("jeff")
        if self.jeff is None or identity != self.jeff_identity:
            if self.jeff:
                self.jeff.close()
            self.jeff_identity = identity
            self.jeff = Jeff(
                self.directory,
                lambda name, args: self.gateway.dispatch(identity, name, args),
                self.gateway.describe,
            )
        return self.jeff

    def chat_status(self):
        query = self.gateway.world.query(["core.message"], 1000, reverse=True)
        messages = [item["facets"]["core.message"] for item in query["items"]]
        messages.sort(key=lambda m: m["created_at"])
        with self.chat_lock:
            return {
                "running": self.running,
                "reply": self.reply,
                "error": self.error,
                "events": self.events[-30:],
                "activity": self.activity.snapshot(),
                "messages": messages,
                "complete": query["complete"],
            }

    def send(self, message, actor):
        if not isinstance(message, str) or not message.strip() or len(message) > 30000:
            raise Refusal("Send a nonempty message of at most 30000 characters.")
        with self.chat_lock:
            if self.running:
                raise Refusal(
                    "JEFF is working. Stop the active turn before starting another in "
                    "this first runtime."
                )
            self.gateway.record_message(actor, "user", message)
            agent = self._agent()
            identity = self.jeff_identity
            self.running, self.reply, self.error, self.events = True, "", None, []
            self.activity = ChatActivity()

        def observe(event):
            with self.chat_lock:
                self.activity.observe(event)
                self.events.append(event)
                self.events = self.events[-200:]

        def work():
            try:
                reply = agent.send(message, observe)
                self.gateway.record_message(identity, "assistant", reply)
                self.reply = reply
            except Exception as exc:
                self.error = str(exc)
            finally:
                self.running = False

        threading.Thread(target=work, daemon=True, name="agora-jeff").start()
        return {"accepted": True, "running": True}

    def stop(self):
        if self.jeff:
            self.jeff.cancel()
        return {"stop_requested": True, "completed_changes_retained": True}

    def system_status(self):
        now = time.monotonic()
        if now - self._status_cache[0] < 5:
            return self._status_cache[1]
        try:
            status = self._agent().status()
        except Exception as exc:
            status = {"signed_in": False, "model": "gpt-6-astra", "error": str(exc)}
        result = {
            "guest": self.gateway.guest.status(),
            "yard": self.gateway.yard.status(),
            "native_bridge": self.bridge.status() | {"error": self.bridge_error},
            "jeff": status,
            "delegation": {
                "profile": "broad local development",
                "enabled": self.gateway.keep["enabled"],
                "generation": self.gateway.keep["generation"],
            },
        }
        self._status_cache = (now, result)
        return result

    def dispatch(self, role, method, args, actor=None):
        if method.startswith("host."):
            if role != "operator":
                raise Refusal("This operation belongs to the independent human recovery surface.")
            if method == "host.surface":
                html, revision = self.gateway.packages.shell()
                return {
                    "html": html,
                    "revision": revision,
                    "watermark": self.gateway.world.query(limit=1)["watermark"],
                    "enabled": self.gateway.keep["enabled"],
                }
            if method == "host.stop":
                return self.stop()
            if method == "host.revoke":
                self.gateway.revoke()
                self.stop()
                self.bridge.close()
                return {"enabled": False}
            if method == "host.resume":
                result = self.gateway.resume()
                self.connect_guest()
                return result
            if method == "host.stop_guest":
                self.gateway.revoke()
                self.stop()
                self.bridge.close()
                return self.gateway.guest.stop()
            if method == "host.start_guest":
                return self.gateway.guest.start()
            if method == "host.connect_guest":
                return self.connect_guest()
            if method == "host.reset_shell":
                if not self.gateway.keep["enabled"]:
                    raise Refusal("Resume development first, then restore the supplied shell.")
                actor = self.gateway.principal("human")
                source = (Path(__file__).parent / "builtin/shell/index.html").read_text(
                    encoding="utf-8"
                )
                package = self.gateway.packages.get("agora.shell")
                manifest = {
                    "name": "Agora Home",
                    "runtime": "browser-1",
                    "ui": {"entry": "index.html", "mount": "shell"},
                }
                self.gateway.packages.save(
                    actor,
                    id="agora.shell",
                    expected_revision=package["revision"],
                    files={"index.html": source},
                    manifest=manifest,
                )
                built = self.gateway.packages.build(
                    actor, id="agora.shell", expected_revision=package["revision"] + 1
                )
                return self.gateway.packages.install(
                    actor,
                    id="agora.shell",
                    build=built["build"],
                    expected_revision=self.gateway.packages.installation("agora.shell")["revision"],
                )
            raise Refusal("Unknown recovery operation.")
        if actor is None:
            raise Refusal("Authenticated request identity is required.")
        self.gateway.check_authority(actor)
        if method == "chat.status":
            return self.chat_status()
        if method == "chat.send":
            return self.send(args.get("message"), actor)
        if method == "chat.stop":
            return self.stop()
        if method == "chat.login":
            if role != "operator":
                raise Refusal("Account sign-in belongs to the human browser.")
            self._status_cache = (0, {})
            return self._agent().login()
        if method == "system.status":
            return self.system_status()
        return self.gateway.dispatch(actor, method, args)


def serve(directory, port=8790):
    app = Application(directory)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def respond(self, status, body, mime="application/json"):
            data = body.encode() if isinstance(body, str) else encoded(body).encode()
            self.send_response(status)
            for name, value in {
                "Content-Type": mime + "; charset=utf-8",
                "Content-Length": str(len(data)),
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "X-Frame-Options": "DENY",
            }.items():
                self.send_header(name, value)
            if mime == "text/html":
                self.send_header(
                    "Content-Security-Policy",
                    (
                        "default-src 'none'; script-src 'unsafe-inline'; style-src "
                        "'unsafe-inline'; connect-src 'self'; frame-src 'self' about:; "
                        "img-src data:; base-uri 'none'; frame-ancestors 'none'"
                    ),
                )
            self.end_headers()
            self.wfile.write(data)

        def valid_host(self):
            return self.headers.get("Host") in {f"127.0.0.1:{port}", f"localhost:{port}"}

        def do_GET(self):
            if not self.valid_host():
                return self.respond(403, {"error": "Use the local Agora address."})
            path = urlsplit(self.path).path
            if path in {"/", "/recovery"}:
                return self.respond(200, FRAME if path == "/" else RECOVERY, "text/html")
            return self.respond(404, {"error": "Not found."})

        def do_POST(self):
            if not self.valid_host() or self.path != "/api/rpc":
                return self.respond(403, {"error": "Invalid local endpoint."})
            origin = self.headers.get("Origin")
            if origin and origin not in {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}:
                return self.respond(403, {"error": "Cross-origin requests are not accepted."})
            token = self.headers.get("Authorization", "").removeprefix("Bearer ")
            try:
                actor = app.gateway.authenticate(token, operator=True, name="shell")
                role = "operator"
            except Refusal:
                return self.respond(401, {"error": "Open this browser with the local launch link."})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 4_000_000:
                    raise Refusal("Requests need a JSON body no larger than 4 MB.")
                request = json.loads(self.rfile.read(length))
                if not isinstance(request, dict) or set(request) != {"method", "args"}:
                    raise Refusal("Request requires method and args.")
                if not isinstance(request["method"], str) or not isinstance(request["args"], dict):
                    raise Refusal("method must be a string and args an object.")
                result = app.dispatch(role, request["method"], request["args"], actor)
                self.respond(200, {"result": result})
            except (ValueError, TypeError, KeyError) as exc:
                self.respond(400, {"error": str(exc)})
            except Exception as exc:
                self.respond(503, {"error": str(exc)})

    server = BoundedHTTPServer(("127.0.0.1", port), Handler)
    port = server.server_address[1]
    return server, app
