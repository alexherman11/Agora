"""JEFF's loop: a conversation, four tools, the desk in view. A client and nothing more.
Never: never imports past verbs, project, and scene; never acts as anyone but jeff."""

from __future__ import annotations

import dataclasses
import json
import os
from dataclasses import dataclass, field
from typing import Any

from jeff.context import ACTOR, system_prompt
from jeff.tools import derive_tools
from kernel import verbs
from kernel.verbs import VerbError

DEFAULT_MODEL = "claude-sonnet-5"
MAX_STEPS = 12


@dataclass
class Turn:
    reply: str
    calls: list[dict[str, Any]] = field(default_factory=list)


class Agent:
    """One conversation with the model. Memory is the message list; it ends with the process."""

    def __init__(self, world: verbs.Store, client: Any = None, model: str | None = None) -> None:
        self.world = world
        self._client = client
        self.model = model or os.environ.get("AGORA_JEFF_MODEL", DEFAULT_MODEL)
        self.tools = derive_tools()
        self.history: list[dict[str, Any]] = []

    @property
    def client(self) -> Any:
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic()
        return self._client

    def turn(self, message: str) -> Turn:
        """One user message in; tool calls until the model stops; one reply out."""
        self.history.append({"role": "user", "content": message})
        calls: list[dict[str, Any]] = []
        for _ in range(MAX_STEPS):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt(self.world),
                tools=self.tools,
                messages=self.history,
            )
            blocks = [_block(b) for b in response.content]
            self.history.append({"role": "assistant", "content": blocks})
            uses = [b for b in blocks if b["type"] == "tool_use"]
            if not uses:
                reply = "".join(b["text"] for b in blocks if b["type"] == "text")
                return Turn(reply, calls)
            results = []
            for use in uses:
                outcome = self.call(use["name"], use["input"])
                calls.append({"verb": use["name"], "args": use["input"], **outcome})
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": use["id"],
                        "content": json.dumps(outcome.get("result", outcome.get("error"))),
                        "is_error": "error" in outcome,
                    }
                )
            self.history.append({"role": "user", "content": results})
        return Turn("I stopped: too many steps without finishing.", calls)

    def call(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Run one verb as jeff. A refusal comes back as data the model can read and fix."""
        fn = verbs.VERBS.get(name)
        if fn is None:
            return {"error": f"no verb {name!r}; the verbs are {sorted(verbs.VERBS)}"}
        try:
            return {"result": _plain(fn(self.world, ACTOR, **args))}
        except VerbError as exc:
            return {"error": str(exc)}
        except TypeError as exc:
            return {"error": f"bad arguments for {name}: {exc}"}


def _block(block: Any) -> dict[str, Any]:
    if block.type == "text":
        return {"type": "text", "text": block.text}
    if block.type == "tool_use":
        return {"type": "tool_use", "id": block.id, "name": block.name, "input": dict(block.input)}
    return {"type": block.type}


def _plain(value: Any) -> Any:
    """A verb's result as JSON data: records become objects, a minted id becomes {"entity"}."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.asdict(value)
    if isinstance(value, str):
        return {"entity": value}
    return value
