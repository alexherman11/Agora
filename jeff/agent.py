"""JEFF's loop: a conversation, derived tools, the desk in view. A client and nothing more.
Never: never imports past verbs, project, and scene; never acts as anyone but jeff."""

from __future__ import annotations

import dataclasses
import json
import os
import threading
from dataclasses import dataclass, field
from typing import Any

from client_layout import free_slot
from jeff.context import ACTOR, system_prompt, world_context
from jeff.tools import derive_extension_tools, derive_tools
from kernel import scene, verbs
from kernel.verbs import VerbError

DEFAULT_MODEL = "claude-sonnet-5"
# Bounded authoring turns need room for inspect → draft → test → revise → activate.
MAX_STEPS = 24


@dataclass
class Turn:
    reply: str
    calls: list[dict[str, Any]] = field(default_factory=list)


class Agent:
    """One conversation with the model. Memory is the message list; it ends with the process."""

    def __init__(
        self,
        world: verbs.Store,
        client: Any = None,
        model: str | None = None,
        *,
        provider: str | None = None,
        reasoning: str | None = None,
    ) -> None:
        self.world = world
        self._client = client
        self.provider = provider or os.environ.get("AGORA_JEFF_PROVIDER", "anthropic")
        if self.provider not in {"anthropic", "openai-agents", "openai-account"}:
            raise ValueError(
                "AGORA_JEFF_PROVIDER must be anthropic, openai-agents or openai-account"
            )
        default = DEFAULT_MODEL if self.provider == "anthropic" else "gpt-6-astra"
        self.model = model or os.environ.get("AGORA_JEFF_MODEL", default)
        self.reasoning = reasoning or os.environ.get("AGORA_JEFF_REASONING", "medium")
        self.tools = derive_tools()
        self.extensions = {}
        self.history: list[dict[str, Any]] = []
        self._turn_lock = threading.Lock()
        self._action_lock = threading.Lock()
        self._cancel = threading.Event()
        self._account_harness = None

    @property
    def account_harness(self):
        if self._account_harness is None:
            from jeff.codex_agent import AccountHarness

            self._account_harness = AccountHarness(self)
        return self._account_harness

    def close(self):
        if self._account_harness is not None:
            self._account_harness.close()

    @property
    def client(self) -> Any:
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic(timeout=30.0, max_retries=0)
        return self._client

    def cancel(self) -> None:
        with self._action_lock:
            self._cancel.set()

    def turn(self, message: str, selection: str | None = None) -> Turn:
        if not self._turn_lock.acquire(blocking=False):
            raise ValueError("JEFF is already working; stop or wait for the current turn")
        try:
            self._cancel.clear()
            if self.provider == "openai-account":
                reply, calls = self.account_harness.run(message, selection, MAX_STEPS)
                return Turn(reply, calls)
            if self.provider == "openai-agents":
                from jeff.openai_agent import run

                reply, calls = run(self, message, selection, MAX_STEPS)
                return Turn(reply, calls)
            return self._turn(message, selection)
        finally:
            self._turn_lock.release()

    def _turn(self, message: str, selection: str | None) -> Turn:
        """One user message in; tool calls until the model stops; one reply out."""
        self.history.append({"role": "user", "content": message})
        calls: list[dict[str, Any]] = []
        for _ in range(MAX_STEPS):
            if self._cancel.is_set():
                return Turn("Stopped. Completed changes remain recorded.", calls)
            extra, self.extensions = derive_extension_tools(
                verbs.component_actions(self.world, ACTOR)
            )
            self.tools = derive_tools() + extra
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                system=system_prompt(self.world),
                tools=self.tools,
                messages=[
                    {
                        "role": "user",
                        "content": "Untrusted world data: " + world_context(self.world, selection),
                    }
                ]
                + self.history,
            )
            blocks = [_block(b) for b in response.content]
            self.history.append({"role": "assistant", "content": blocks})
            uses = [b for b in blocks if b["type"] == "tool_use"]
            if not uses:
                reply = "".join(b["text"] for b in blocks if b["type"] == "text")
                return Turn(reply, calls)
            results = []
            for use in uses:
                with self._action_lock:
                    outcome = (
                        {"error": "cancelled before dispatch"}
                        if self._cancel.is_set()
                        else self.call(use["name"], use["input"])
                    )
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
        if not isinstance(name, str) or not isinstance(args, dict):
            return {"error": "tool name must be a string and arguments an object"}
        fn = verbs.VERBS.get(name)
        if name in self.extensions:
            target = self.extensions[name]
            try:
                return {
                    "result": verbs.invoke_component(
                        self.world,
                        ACTOR,
                        target["component"],
                        target["revision"],
                        target["name"],
                        args,
                    )
                }
            except VerbError as exc:
                return {"error": str(exc)}
        if fn is None:
            return {"error": f"no verb {name!r}; the verbs are {sorted(verbs.VERBS)}"}
        try:
            if name == "place" and "transform" not in args:
                args = dict(
                    args,
                    transform=free_slot(
                        scene.tree(self.world, ACTOR, args.get("scene", scene.DESK))
                    ),
                )
            return {"result": _plain(fn(self.world, ACTOR, **args))}
        except VerbError as exc:
            return {"error": str(exc)}
        except (TypeError, ValueError) as exc:
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
