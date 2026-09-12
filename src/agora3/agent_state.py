"""Protected resident identity and the durable model-conversation binding.
Never silently reset a conversation or claim that a copied world owns its agent.
"""

import copy
from pathlib import Path

from agora3.world import Refusal, identifier

OBJECT = "agora.agent.resident"
FACET = "agora.agent"


class AgentState:
    def __init__(self, gateway, directory):
        self.gateway = gateway
        self.directory = str(Path(directory).resolve())

    def read(self):
        try:
            obj = self.gateway.world.get(OBJECT)
            return obj, copy.deepcopy(obj["facets"][FACET])
        except Refusal:
            return None, {
                "id": "jeff",
                "name": "JEFF",
                "owner_world": self.directory,
                "checkpoint": None,
                "session": None,
                "continuity": "New resident; no previous model session is claimed.",
            }

    def public(self):
        _, value = self.read()
        return {
            **{key: value[key] for key in ("id", "name", "checkpoint", "continuity")},
            "resumable": bool(value["session"]),
            "owner_matches": value["owner_world"] == self.directory,
        }

    def owned(self):
        _, value = self.read()
        if value["owner_world"] != self.directory:
            raise Refusal(
                "This is a copy of another resident's world. Explicitly transfer the resident "
                "before continuing; a copied journal must not start a second JEFF."
            )
        return value

    def _save(self, actor, obj, value):
        self.gateway.commit(
            actor,
            [
                {
                    "id": OBJECT,
                    "expected_revision": obj["revision"] if obj else 0,
                    "facets": {FACET: value},
                }
            ],
            internal=True,
        )

    def configure(self, actor, *, agent_id, name, checkpoint=None, continuity):
        """Operator-only setup/transfer; existing session identity is preserved."""
        identifier(agent_id)
        if actor.name != "human" or not isinstance(name, str) or not 1 <= len(name) <= 80:
            raise Refusal("Resident setup requires the human operator and a short name.")
        with self.gateway.lock:
            obj, value = self.read()
            if obj and value["id"] != agent_id:
                raise Refusal("Do not replace a resident identity during a world transfer.")
            value.update(
                id=agent_id,
                name=name,
                checkpoint=checkpoint,
                continuity=continuity,
                owner_world=self.directory,
            )
            self._save(actor, obj, value)
        return self.public()

    def bind(self, actor, thread_id, model):
        with self.gateway.lock:
            self.owned()
            obj, value = self.read()
            session = {"thread_id": thread_id, "model": model, "provider": "openai"}
            if value["session"] and value["session"] != session:
                raise Refusal(
                    "A resident already has a conversation; resume it instead of resetting."
                )
            if value["session"] == session:
                return
            value["session"] = session
            self._save(actor, obj, value)

    def fork(self, actor, *, thread_id, continuity):
        """Bind an explicitly forked world to its own model conversation."""
        if actor.name != "human":
            raise Refusal("Only the operator can establish a worldline fork.")
        with self.gateway.lock:
            obj, value = self.read()
            if not obj or value["owner_world"] == self.directory:
                raise Refusal("Fork binding requires a copied, not already owned, resident.")
            if not thread_id or thread_id == (value.get("session") or {}).get("thread_id"):
                raise Refusal("A fork needs its own distinct model conversation.")
            value["fork_origin"] = {"world": value["owner_world"], "session": value.get("session")}
            value["owner_world"] = self.directory
            value["session"] = {
                "thread_id": thread_id,
                "model": "gpt-6-astra",
                "provider": "openai",
            }
            value["continuity"] = continuity
            self._save(actor, obj, value)
        return self.public()
