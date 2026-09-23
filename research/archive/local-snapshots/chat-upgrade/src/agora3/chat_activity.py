"""Bounded, transient progress snapshots for reconnecting chat clients.
Never treat progress as durable conversation or expose tool arguments/results.
"""

import time
import uuid


class ChatActivity:
    def __init__(self):
        self.id = uuid.uuid4().hex
        self.messages = {}
        self.tool = None
        self.started_at = time.time()

    def observe(self, event):
        kind = event.get("type")
        if kind in {"text.delta", "text.started", "text.completed"}:
            item_id = event.get("id") or "legacy"
            if item_id not in self.messages and len(self.messages) >= 100:
                return
            item = self.messages.setdefault(
                item_id, {"id": item_id, "text": "", "phase": "commentary", "complete": False}
            )
            available = max(
                0,
                1_000_000
                - sum(len(value["text"]) for key, value in self.messages.items() if key != item_id),
            )
            if kind == "text.delta":
                item["text"] = (item["text"] + event.get("text", ""))[:available]
            elif kind == "text.completed":
                item["text"] = event.get("text", "")[:available]
                item["complete"] = True
            if event.get("phase"):
                item["phase"] = event["phase"]
        elif kind == "tool.started":
            self.tool = {"name": event["name"], "started_at": time.time(), "running": True}
        elif kind == "tool.completed" and self.tool:
            if event.get("name") == self.tool["name"]:
                self.tool["running"] = False

    def snapshot(self):
        return {
            "id": self.id,
            "started_at": self.started_at,
            "messages": [dict(item) for item in self.messages.values()],
            "tool": dict(self.tool) if self.tool else None,
        }
