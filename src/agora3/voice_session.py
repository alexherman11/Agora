"""Trusted Live event handling and asynchronous delegation into JEFF's existing turn.
Never infer actions from speech or retry a possibly accepted backend request.
"""

import json
import logging
import queue
import threading
import time
import traceback
import uuid
from collections import deque

from agora3.gateway import Principal
from agora3.voice_context import Transcript, spoken_chunks
from agora3.voice_coordination import Coordination
from agora3.world import Refusal


class VoiceSession:
    def __init__(self, app, actor, client, resident_id):
        self.app, self.actor, self.client = app, actor, client
        self.identity = Principal("jeff", actor.generation, resident_id)
        self.lock = threading.RLock()
        self.closing, self.done = threading.Event(), threading.Event()
        self.connection = None
        self.last_seen = time.monotonic()
        self.close_started = None
        self.error, self.confirmed_closed, self.seconds = None, False, 0
        self.transcript = Transcript(self.record)
        self.seen = deque(maxlen=2000)
        self.delegations = deque(maxlen=1000)
        self.jobs = queue.Queue(maxsize=20)
        self.coordination = Coordination()
        self.started = False
        self.failure = None
        self.phase = "starting"
        self.last_event = None

    def authorized(self):
        self.app.gateway.check_authority(self.actor)
        if self.app.resident.owned()["id"] != self.identity.agent_id:
            raise Refusal("The resident identity changed; start a new voice call.")

    def record(self, role, text):
        self.authorized()
        self.app.gateway.record_message(self.actor if role == "user" else self.identity, role, text)

    def heartbeat(self):
        self.last_seen = time.monotonic()

    def status(self):
        return {
            "closing": self.closing.is_set(),
            "closed": self.done.is_set(),
            "confirmed_closed": self.confirmed_closed,
            "seconds": self.seconds,
            "error": self.error,
            "failure": self.failure,
            "coordination": self.coordination.snapshot(),
        }

    def failed(self, exc, phase=None):
        # Keep diagnostic metadata, never event payloads, audio, keys or exception text.
        detail = {
            "at": time.time(),
            "phase": phase or self.phase,
            "exception": type(exc).__name__,
            "last_event": self.last_event,
            "stack": [
                {"function": frame.name, "line": frame.lineno}
                for frame in traceback.extract_tb(exc.__traceback__)[-8:]
            ],
        }
        for direction in ("rcvd", "sent"):
            code = getattr(getattr(exc, direction, None), "code", None)
            if isinstance(code, int):
                detail[direction + "_close_code"] = code
        self.failure = detail
        logging.getLogger(__name__).error("Voice failure %s", json.dumps(detail))
        self.error = (
            "Voice disconnected during "
            + detail["phase"]
            + " ("
            + detail["exception"]
            + "). Your completed work remains in chat."
        )

    def attach(self, connection):
        self.connection = connection
        threading.Thread(target=self.run, daemon=True, name="agora-voice-events").start()
        threading.Thread(target=self.work, daemon=True, name="agora-voice-delegation").start()

    def send(self, kind, **values):
        event_id = values.pop("event_id", uuid.uuid4().hex)
        try:
            self.connection.send({"type": kind, "event_id": event_id, **values})
        except Exception as exc:
            self.failed(exc, "sending " + kind)
            raise

    def close(self):
        if not self.closing.is_set():
            self.close_started = time.monotonic()
            self.closing.set()

    def commentary(self, delegation, text):
        for chunk in spoken_chunks(text[:12_000]):
            self.send("session.commentary.append", delegation_id=delegation, content=chunk)

    def handle(self, event):
        kind = event.get("type", "")
        self.last_event = kind if isinstance(kind, str) and len(kind) < 100 else "unknown"
        # Reflected raw audio is deliberately neither retained nor interpreted.
        event_id = event.get("event_id")
        if event_id:
            if event_id in self.seen:
                return
            self.seen.append(event_id)
        if kind == "session.started":
            self.started = True
        self.coordination.acknowledge(event)
        if kind in {"session.usage.updated", "session.closed"}:
            seconds = (event.get("usage") or {}).get("seconds")
            if isinstance(seconds, (int, float)):
                self.seconds = max(self.seconds, seconds)
        if kind == "session.closed":
            self.confirmed_closed = True
            self.close()
            return
        if kind == "error":
            self.error = "GPT Live reported a session error. End the call and try again."
            self.close()
            return
        if kind in {"session.input_transcript.delta", "session.output_transcript.delta"}:
            with self.lock:
                self.transcript.append(event)
            self.coordination.heard("user" if "input_" in kind else "assistant")
        elif kind == "session.delegation.created" and not self.closing.is_set():
            delegation = event.get("delegation") or {}
            identifier = delegation.get("id")
            if delegation.get("target") != "client" or not isinstance(identifier, str):
                return
            if identifier in self.delegations:
                return
            self.delegations.append(identifier)
            with self.lock:
                request = self.transcript.request()
                if request:
                    self.coordination.received(identifier, "voice", identifier)
                    try:
                        self.jobs.put_nowait((identifier, request))
                    except queue.Full:
                        self.coordination.change(identifier, "failed", "Too many pending requests")
                        self.commentary(identifier, "Too many pending requests. Please pause.")

    def work(self):
        while not self.closing.is_set() and not self.done.is_set():
            try:
                identifier, request = self.jobs.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                # Only retry an explicit 'not admitted yet' during turn startup.
                deadline = time.monotonic() + 30
                while not self.closing.is_set():
                    self.authorized()
                    activity = self.app.voice_request(request, self.actor)
                    if activity:
                        self.coordination.accepted(identifier, activity)
                        break
                    if time.monotonic() > deadline:
                        raise Refusal("JEFF is still connecting. Please try your request again.")
                    self.closing.wait(0.2)
            except Exception as exc:
                self.coordination.change(
                    identifier, "failed", "JEFF could not accept this request; check chat"
                )
                if not self.closing.is_set():
                    try:
                        message = (
                            str(exc)
                            if isinstance(exc, Refusal)
                            else "JEFF could not accept the request."
                        )
                        self.commentary(identifier, message)
                    except Exception:
                        self.close()

    def tick(self):
        self.authorized()
        if time.monotonic() - self.last_seen > 30:
            self.error = "The browser disconnected; the voice call was ended."
            self.close()
        if self.started and not self.closing.is_set():
            for activity, identifier in self.coordination.activities():
                self.coordination.observe(activity, identifier, self.app.backend_snapshot(activity))
            self.coordination.flush(self.send)

    def run(self):
        close_sent = False
        try:
            while not self.confirmed_closed:
                if self.closing.is_set():
                    if not close_sent:
                        self.send("session.close")
                        self.close_started = time.monotonic()
                        close_sent = True
                    if time.monotonic() - self.close_started > 5:
                        break
                else:
                    try:
                        self.phase = "updating voice context"
                        self.tick()
                    except Refusal:
                        self.error = "Voice authority changed; the call was ended."
                        self.close()
                        continue
                try:
                    self.phase = "receiving voice events"
                    event = self.connection.receive()
                    self.phase = "handling voice event"
                    self.handle(event)
                except TimeoutError:
                    pass
        except Exception as exc:
            if self.failure is None:
                self.failed(exc)
        finally:
            self.close()
            self.coordination.close()
            try:
                with self.lock:
                    self.transcript.flush()
            except Exception:
                self.error = "Voice ended; the last transcript fragments could not be saved."
            if not self.confirmed_closed:
                self.connection.hangup()
            try:
                self.connection.disconnect()
            finally:
                self.done.set()
