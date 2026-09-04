"""A scripted stand-in for the Anthropic client, so JEFF's loop is tested without a model."""

from __future__ import annotations

import copy
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any


def text(content: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=content)


def tool_use(name: str, input: dict[str, Any], id: str = "call_1") -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=id, name=name, input=input)


class FakeClient:
    """Each script entry is a list of content blocks, or a function of the request kwargs."""

    def __init__(self, script: list[Any]) -> None:
        self.script = list(script)
        self.requests: list[dict[str, Any]] = []
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs: Any) -> SimpleNamespace:
        kwargs = copy.deepcopy(kwargs)  # the agent mutates its history after the call
        self.requests.append(kwargs)
        if not self.script:
            raise AssertionError("the script ran out of responses")
        step = self.script.pop(0)
        blocks = step(kwargs) if isinstance(step, Callable) else step
        return SimpleNamespace(
            content=blocks,
            stop_reason="tool_use" if any(b.type == "tool_use" for b in blocks) else "end_turn",
        )


def import_notes_script(path: str) -> list[Any]:
    """JEFF puts a notes file into the world: one mint with three facets, one place, one reply."""
    return [
        [
            tool_use(
                "mint",
                {
                    "facets": {
                        "core.name": {"name": "notes"},
                        "core.text": {"path": path},
                        "core.file-backing": {"path": path},
                    }
                },
                id="c1",
            )
        ],
        lambda req: [
            tool_use(
                "place",
                {
                    "entity": _last_result(req)["entity"],
                    "mode": "icon",
                    "transform": {"x": 40, "y": 40},
                },
                id="c2",
            )
        ],
        [text("Done: your notes are on the desk.")],
    ]


def _last_result(request: dict[str, Any]) -> dict[str, Any]:
    import json

    result = request["messages"][-1]["content"][0]["content"]
    return json.loads(result) if isinstance(result, str) else result
