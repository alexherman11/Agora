"""Operator-owned voice sessions for the continuing resident conversation.
Never give authored code a microphone, API key, or a second action gateway.
"""

import threading
import uuid
from contextlib import nullcontext

from agora3 import voice_credentials
from agora3.voice_context import MODEL, VOICE, configuration
from agora3.voice_session import VoiceSession
from agora3.voice_transport import LiveConnection
from agora3.world import Refusal


class VoiceService:
    def __init__(self, app, connect=LiveConnection):
        self.app, self.connect = app, connect
        self.lock = threading.RLock()
        self.session = None

    @staticmethod
    def client(value):
        if not isinstance(value, str) or not 16 <= len(value) <= 100:
            raise Refusal("Voice needs a browser session identifier.")
        return value

    def start(self, actor, client, sdp):
        self.client(client)
        if not isinstance(sdp, str) or not sdp.startswith("v=0") or len(sdp) > 100_000:
            raise Refusal("Voice needs a valid browser audio offer.")
        self.app.gateway.check_authority(actor)
        resident = self.app.resident.owned()
        with self.lock:
            if self.session and not self.session.done.is_set():
                raise Refusal("A voice call is already active. End it before starting another.")
            session = VoiceSession(self.app, actor, client, resident["id"])
            self.session = session
        try:
            connection = self.connect(
                voice_credentials.load_key(self.app.directory),
                configuration(resident["name"], self.app.chat_status()["messages"]),
                sdp,
            )
            session.attach(connection)
            backend = self.app.backend_snapshot()
            if backend["running"]:
                identifier = "existing-" + backend["id"]
                session.coordination.received(identifier, "existing")
                session.coordination.accepted(identifier, backend["id"])
            session.authorized()
            if session.closing.is_set():
                raise Refusal("The voice call was cancelled while connecting.")
            return {"sdp": connection.sdp, "model": MODEL, "voice": VOICE}
        except Exception:
            session.close()
            if session.connection is None:
                session.done.set()
            raise

    def status(self, client):
        self.client(client)
        with self.lock:
            session = self.session
            own = bool(session and session.client == client)
            if own:
                session.heartbeat()
            return {
                "configured": voice_credentials.configured(self.app.directory),
                "active": bool(session and not session.done.is_set()),
                "owner": own,
                "model": MODEL,
                "voice": VOICE,
                **(session.status() if session else {}),
            }

    def end(self, client):
        self.client(client)
        with self.lock:
            if self.session and not self.session.done.is_set():
                if self.session.client != client:
                    raise Refusal("End this voice call from the browser that started it.")
                self.session.close()
        return {"closing": True}

    def close(self):
        with self.lock:
            if self.session:
                self.session.close()

    def text_context(self):
        with self.lock:
            session = self.session
            if session:
                try:
                    session.authorized()
                except Refusal:
                    return ""
                with session.lock:
                    return session.transcript.request() or ""
        return ""

    def conversation(self):
        with self.lock:
            session = self.session
            if not session:
                return {"active": False, "messages": []}
            with session.lock:
                return {
                    "active": not session.done.is_set() and not session.closing.is_set(),
                    "messages": session.transcript.preview(session.client),
                    **session.status(),
                }

    def chat_projection(self):
        # A flush must not fall between reading durable messages and their live tail.
        with self.lock:
            session = self.session
            with session.lock if session else nullcontext():
                query = self.app.gateway.world.query(["core.message"], 1000, reverse=True)
                return query, self.conversation()

    def converse(self, message, actor, *, delegate=False):
        """During voice, typed input goes to the conversational side before any handoff."""
        with self.lock:
            session = self.session
            if not session or session.closing.is_set() or session.done.is_set():
                return None
            session.authorized()
            self.app.gateway.check_authority(actor)
            with session.lock:
                if delegate and session.jobs.full():
                    raise Refusal(
                        "Too many pending handoffs; wait for JEFF before sending another."
                    )
                self.app.gateway.record_message(actor, "user", message)
                session.transcript.typed(message)
                if delegate:
                    request = session.transcript.request()
                    identifier = "manual-" + uuid.uuid4().hex
                    session.coordination.received(identifier, "typed")
                    session.jobs.put_nowait((identifier, request))
                else:
                    session.coordination.conversation_input(message)
            return {"accepted": True, "route": "harness" if delegate else "conversation"}
