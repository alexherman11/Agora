"""Loopback transport, durable conversation and independent recovery.
Never give authored frames operator credentials or execute their source on the host.
"""

import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit

from agora3.agent_state import AgentState
from agora3.bridge import NativeBridge
from agora3.chat_activity import ChatActivity
from agora3.gateway import Gateway
from agora3.http_transport import BoundedHTTPServer
from agora3.jeff import Jeff
from agora3.voice import VoiceService
from agora3.work_specs import SPECS as WORK_SPECS
from agora3.world import Refusal, encoded

FRAME = (
    (Path(__file__).parent / "host/frame.html")
    .read_text(encoding="utf-8")
    .replace("__WORK_METHODS__", json.dumps([s["name"] for s in WORK_SPECS]))
)

RECOVERY = (Path(__file__).parent / "host/recovery.html").read_text(encoding="utf-8")


class Application:
    def __init__(self, directory):
        self.gateway = Gateway(directory)
        self.directory = Path(directory)
        self.gateway.seed()
        self.resident = AgentState(self.gateway, self.directory)
        self.chat_lock = threading.RLock()
        self.running, self.events, self.reply, self.error = False, [], "", None
        self.activity = ChatActivity()
        self.completed = {}
        self.jeff = self.jeff_identity = None
        self._status_cache = (0, {})
        self.bridge = NativeBridge(self.gateway)
        self.gateway.native_bridge = self.bridge
        self.bridge_error = None
        self.voice = VoiceService(self)
        self.work = None
        if os.environ.get("AGORA_WORKERS") == "1":
            from agora3.work_scheduler import WorkService

            self.work = WorkService(self.gateway, notify=self.worker_update)
            self.work.start()

    def worker_update(self, text):
        """Route important worker reports into the continuing executive conversation."""
        with self.chat_lock:
            agent = self.jeff if self.running else None
        if agent:
            return bool(agent.steer(text))
        try:
            result = self.send(text, self.gateway.principal("human"), record=False)
        except Exception:
            return False
        # If voice is connected, its ordinary activity observer delivers the executive's reply.
        with self.voice.lock:
            session = self.voice.session
            if session and not session.done.is_set():
                identifier = "work-update-" + result["activity_id"]
                session.coordination.received(identifier, "worker")
                session.coordination.accepted(identifier, result["activity_id"])
        return True

    def connect_guest(self):
        try:
            result = self.bridge.start()
            self.bridge_error = None
            return result
        except Exception as exc:
            self.bridge_error = str(exc)
            return {"connected": False, "error": self.bridge_error}

    def _agent(self):
        resident = self.resident.owned()
        identity = self.gateway.principal("jeff", agent_id=resident["id"])
        if self.jeff is None or identity != self.jeff_identity:
            if self.jeff:
                self.jeff.close()
            self.jeff_identity = identity
            self.jeff = Jeff(
                self.directory,
                lambda name, args: self.gateway.dispatch(identity, name, args),
                self.gateway.describe,
                continuity=self.resident,
                bind_session=lambda thread_id, model: self.resident.bind(
                    identity, thread_id, model
                ),
            )
        return self.jeff

    def chat_status(self):
        query, voice = self.voice.chat_projection()
        messages = [{"id": item["id"], **item["facets"]["core.message"]} for item in query["items"]]
        for message in messages:
            if message["text"].startswith("[Voice transcript]\n"):
                message["text"] = message["text"].removeprefix("[Voice transcript]\n")
                message["source"] = "voice"
        messages.extend(voice.pop("messages"))
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
                "resident": self.resident.public(),
                "work": self.gateway.work.dispatch(self.gateway.principal("human"), "work.list", {})
                if self.work
                else None,
                "voice": voice,
            }

    def send(self, message, actor, *, record=True, delegate=False):
        if not isinstance(message, str) or not message.strip() or len(message) > 30000:
            raise Refusal("Send a nonempty message of at most 30000 characters.")
        if record:
            conversational = self.voice.converse(message, actor, delegate=delegate)
            if conversational:
                return conversational
        # Runtime steering can deliver callbacks that acquire chat_lock. Snapshot
        # the target here, then wait for the runtime only after releasing the lock.
        with self.chat_lock:
            self.gateway.check_authority(actor)
            followup = (self.jeff, self.activity.id) if self.running and self.work else None
        if followup:
            agent, activity_id = followup
            if agent and agent.steer(message):
                if record:
                    self.gateway.record_message(actor, "user", message)
                return {
                    "accepted": True,
                    "running": True,
                    "activity_id": activity_id,
                    "route": "executive_followup",
                }
            raise Refusal(
                "The active turn could not accept the follow-up; check JEFF before retrying."
            )
        with self.chat_lock:
            if self.running:
                raise Refusal(
                    "JEFF is working. Stop the active turn before starting another in "
                    "this first runtime."
                )
            self.gateway.check_authority(actor)
            if record:
                context = self.voice.text_context()
                self.gateway.record_message(actor, "user", message)
                if context:
                    message = context + "\n\nAlex now writes:\n" + message
            agent = self._agent()
            identity = self.jeff_identity
            self.running, self.reply, self.error, self.events = True, "", None, []
            self.activity = ChatActivity()
            activity_id = self.activity.id

        def observe(event):
            with self.chat_lock:
                self.activity.observe(event)
                self.events.append(event)
                self.events = self.events[-200:]

        def work():
            try:
                reply = agent.send(message, observe)
                self.gateway.record_message(identity, "assistant", reply)
                with self.chat_lock:
                    self.reply = reply
            except Exception as exc:
                with self.chat_lock:
                    self.error = str(exc)
            finally:
                with self.chat_lock:
                    self.running = False
                    self.completed[activity_id] = {
                        "id": activity_id,
                        "running": False,
                        "reply": self.reply,
                        "error": self.error,
                    }
                    while len(self.completed) > 20:
                        del self.completed[next(iter(self.completed))]

        threading.Thread(target=work, daemon=True, name="agora-jeff").start()
        return {"accepted": True, "running": True, "activity_id": activity_id}

    def voice_request(self, message, actor):
        with self.chat_lock:
            self.gateway.check_authority(actor)
            followup = (self.jeff, self.activity.id) if self.running else None
        if followup:
            agent, activity_id = followup
            return activity_id if agent and agent.steer(message) else None
        return self.send(message, actor, record=False)["activity_id"]

    def backend_snapshot(self, activity=None):
        with self.chat_lock:
            if activity in self.completed:
                return dict(self.completed[activity])
            return {
                "id": self.activity.id,
                "running": self.running,
                "reply": self.reply,
                "error": self.error,
                "tool": self.activity.snapshot()["tool"],
                "messages": self.activity.snapshot()["messages"],
            }

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
            if method == "host.voice.reload":
                if args:
                    raise Refusal("Voice reload takes no arguments; it loads this checkout only.")
                return self.voice.reload()
            if method == "host.voice.status":
                return self.voice.status(args.get("client"))
            if method == "host.voice.end":
                return self.voice.end(args.get("client"))
            if method == "host.voice.start":
                return self.voice.start(actor, args.get("client"), args.get("sdp"))
            if method == "host.surface":
                html, revision = self.gateway.packages.shell()
                return {
                    "html": html,
                    "revision": revision,
                    "watermark": self.gateway.world.query(limit=1)["watermark"],
                    "enabled": self.gateway.keep["enabled"],
                    "workers": self.work is not None,
                }
            if method == "host.stop":
                return self.stop()
            if method == "host.stop_workers":
                stopped = []
                if self.work:
                    human = self.gateway.principal("human")
                    with self.gateway.lock:
                        for task in self.work.tasks():
                            if task["state"] in {
                                "queued",
                                "starting",
                                "running",
                                "waiting_resource",
                            }:
                                self.work.dispatch(human, "work.cancel", {"id": task["id"]})
                                stopped.append(task["id"])
                return {"cancelled": stopped, "retained_candidates": True}
            if method == "host.revoke":
                self.voice.close()
                if self.work:
                    self.work.close()
                self.gateway.revoke()
                self.stop()
                self.bridge.close()
                return {"enabled": False}
            if method == "host.resume":
                result = self.gateway.resume()
                if self.work and self.work.closed.is_set():
                    from agora3.work_scheduler import WorkService

                    self.work = WorkService(self.gateway, notify=self.worker_update)
                    self.work.start()
                self.connect_guest()
                return result
            if method == "host.stop_guest":
                self.voice.close()
                if self.work:
                    self.work.close()
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
            if not isinstance(args.get("delegate", False), bool):
                raise Refusal("delegate must be true or false.")
            return self.send(args.get("message"), actor, delegate=args.get("delegate", False))
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
                "Permissions-Policy": "microphone=(self), camera=()",
            }.items():
                self.send_header(name, value)
            if mime == "text/html":
                self.send_header(
                    "Content-Security-Policy",
                    (
                        "default-src 'none'; script-src 'self' 'unsafe-inline'; style-src "
                        "'self' 'unsafe-inline'; connect-src 'self'; media-src blob:; "
                        "frame-src 'self' about:; "
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
            if path in {"/voice.js", "/voice.css"}:
                source = (Path(__file__).parent / "host" / path[1:]).read_text(encoding="utf-8")
                return self.respond(
                    200, source, "text/javascript" if path.endswith(".js") else "text/css"
                )
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
