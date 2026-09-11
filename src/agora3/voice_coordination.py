"""Bounded handoff receipts and factual progress for a voice conversation.
Never expose tool arguments, private reasoning, or call delivery proof of playback.
"""

import json
import threading
import time
import uuid
from collections import deque

from agora3.voice_context import spoken_chunks

LABELS = {
    "world.query": "Looking through the world",
    "world.get": "Reading an object",
    "world.focus": "Checking current focus",
    "world.transact": "Updating the world",
    "package.read": "Reading package contents",
    "package.get": "Reading a package",
    "package.check": "Checking a package",
    "package.build": "Building a package",
    "package.install": "Installing a package",
    "guest.execute": "Working in the Linux workspace",
    "experiment.observe": "Inspecting the interface",
    "experiment.interact": "Using the interface",
}


class Coordination:
    def __init__(self):
        self.lock = threading.RLock()
        self.requests = {}
        self.pending = {}
        self.outbox = deque()
        self.receipts = {}
        self.progress_keys = {}
        self.last_progress = {}
        self.progress_reports = {}
        self.last_report = {}
        self.input_receipts = {}
        self.heard_at = self.spoke_at = None
        self.last_activity = None

    def heard(self, role):
        with self.lock:
            if role == "user":
                self.heard_at = time.time()
            else:
                self.spoke_at = time.time()

    def received(self, identifier, source, delegation=None):
        with self.lock:
            self.requests[identifier] = {
                "id": identifier,
                "source": source,
                "delegation": delegation,
                "stage": "received",
                "detail": "Waiting to hand the request to JEFF",
                "received_at": time.time(),
                "updated_at": time.time(),
            }
            while len(self.requests) > 24:
                old = next(iter(self.requests))
                self.requests.pop(old)
                self.receipts = {key: value for key, value in self.receipts.items() if value != old}
                self.input_receipts = {
                    key: value for key, value in self.input_receipts.items() if value != old
                }
                for activity, request in list(self.pending.items()):
                    if request == old:
                        self.pending.pop(activity)
                        self.progress_keys.pop(activity, None)
                        self.last_progress.pop(activity, None)
                        self.progress_reports.pop(activity, None)
                        self.last_report.pop(activity, None)

    def change(self, identifier, stage, detail):
        with self.lock:
            if identifier in self.requests:
                self.requests[identifier].update(stage=stage, detail=detail, updated_at=time.time())
                self.requests[identifier].setdefault(stage + "_at", time.time())

    def accepted(self, identifier, activity):
        with self.lock:
            previous = self.pending.get(activity)
            if previous and previous != identifier:
                self.change(previous, "continued", "Continued with your newer follow-up")
            self.pending[activity] = identifier
            self.last_activity = activity
            self.change(identifier, "accepted", "Handed to the continuing JEFF conversation")
            if identifier in self.requests:
                self.requests[identifier]["activity"] = activity
            self.queue(identifier, "context", "JEFF has accepted the request and is working on it.")

    def conversation_input(self, message):
        identifier = "typed-" + uuid.uuid4().hex
        self.received(identifier, "conversation")
        self.change(identifier, "conversation", "Sending your message to the voice conversation")
        excerpt = message[:6000]
        self.queue(
            identifier,
            "input",
            "New conversation input from Alex, typed in the shared chat. "
            "Discuss and refine it with him; do not assume it authorizes backend work. User data: "
            + json.dumps(excerpt, ensure_ascii=False)
            + (" [Excerpt; complete message is saved in chat.]" if len(message) > 6000 else ""),
        )
        return identifier

    def queue(self, identifier, kind, text):
        with self.lock:
            if len(self.outbox) >= 60:
                self.change(identifier, "delivery_error", "Voice context queue is full; check chat")
                return
            self.outbox.append((identifier, kind, text))

    def snapshot(self):
        with self.lock:
            return {
                "requests": [
                    {k: v for k, v in row.items() if k != "delegation"}
                    for row in self.requests.values()
                ],
                "last_heard_at": self.heard_at,
                "last_spoke_at": self.spoke_at,
            }

    def activities(self):
        with self.lock:
            return list(self.pending.items())

    def observe(self, activity, identifier, snapshot):
        with self.lock:
            if self.pending.get(activity) != identifier or snapshot["id"] != activity:
                return
            if not snapshot["running"]:
                self.pending.pop(activity)
                self.progress_keys.pop(activity, None)
                self.last_progress.pop(activity, None)
                self.progress_reports.pop(activity, None)
                self.last_report.pop(activity, None)
                error = snapshot.get("error")
                self.change(
                    identifier,
                    "failed" if error else "completed",
                    "JEFF reported an error; check chat" if error else "JEFF's result is ready",
                )
                self.queue(
                    identifier,
                    "result",
                    error or snapshot.get("reply") or "JEFF finished without a reply.",
                )
                return
            reports = [
                m
                for m in snapshot.get("messages", [])
                if m.get("complete") and m.get("phase") == "commentary" and m.get("text")
            ]
            if reports and self.progress_reports.get(activity) != reports[-1]["id"]:
                if time.monotonic() - self.last_report.get(activity, 0) >= 20:
                    self.progress_reports[activity] = reports[-1]["id"]
                    self.last_report[activity] = time.monotonic()
                    self.queue(
                        identifier,
                        "progress",
                        "Astra's public progress report for this task "
                        "(ongoing work, not the final product): " + reports[-1]["text"][:1600],
                    )
            tool = snapshot.get("tool") or {}
            key = (tool.get("name"), tool.get("started_at"), tool.get("running"))
            if key == self.progress_keys.get(activity):
                return
            if time.monotonic() - self.last_progress.get(activity, 0) < 4:
                return
            self.progress_keys[activity] = key
            self.last_progress[activity] = time.monotonic()
            label = (
                LABELS.get(tool.get("name"), "Using an installed tool")
                if tool
                else "Working on your request"
            )
            detail = (
                label
                if not tool or tool.get("running")
                else label + " · action returned; JEFF is continuing"
            )
            self.change(identifier, "working", detail)
            self.queue(
                identifier,
                "context",
                "Observed backend state: " + detail + ". No final result yet.",
            )

    def flush(self, send):
        # Never hold our state lock across a transport operation.
        with self.lock:
            items = list(self.outbox)
            self.outbox.clear()
        for identifier, kind, text in items:
            with self.lock:
                row = self.requests.get(identifier)
                if not row or row["stage"] == "continued":
                    continue
                delegation = row["delegation"]
            chunks = [(uuid.uuid4().hex, chunk) for chunk in spoken_chunks(text[:12_000])]
            with self.lock:
                if kind == "result":
                    self.receipts.update({event_id: identifier for event_id, _ in chunks})
                    self.change(identifier, "sent", "Result sent to voice; waiting for receipt")
                elif kind == "input":
                    self.input_receipts.update({event_id: identifier for event_id, _ in chunks})
            for event_id, chunk in chunks:
                try:
                    send(
                        "session.commentary.append"
                        if kind in {"result", "progress", "speak"}
                        else "session.thinking.append",
                        event_id=event_id,
                        delegation_id=delegation,
                        content=chunk,
                    )
                except Exception:
                    self.change(
                        identifier,
                        "delivery_error",
                        "Could not confirm delivery to voice; check chat",
                    )
                    raise

    def acknowledge(self, event):
        if event.get("type") == "session.thinking.appended":
            with self.lock:
                identifier = self.input_receipts.pop(event.get("client_event_id"), None)
                if identifier and identifier not in self.input_receipts.values():
                    self.change(identifier, "conversation", "Voice received your chat message")
                    self.queue(
                        identifier,
                        "speak",
                        "Respond naturally to Alex's newest typed "
                        "conversation input now. Follow the discussion and selective "
                        "handoff policy; do not read the input receipt aloud.",
                    )
            return
        if event.get("type") != "session.commentary.appended":
            return
        with self.lock:
            identifier = self.receipts.pop(event.get("client_event_id"), None)
            if identifier and identifier not in self.receipts.values():
                self.change(identifier, "delivered", "Voice received the result")

    def close(self):
        with self.lock:
            for identifier, row in self.requests.items():
                if row["stage"] in {
                    "received",
                    "accepted",
                    "working",
                    "completed",
                    "sent",
                    "conversation",
                }:
                    self.change(
                        identifier, "call_ended", "Call ended; follow any remaining work in chat"
                    )
            self.outbox.clear()
