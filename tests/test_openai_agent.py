"""The real Agents SDK runs JEFF's tools; scripted model responses replace only inference."""

import asyncio
import copy
import json

import httpx
import pytest
from agents import Model
from agents.items import ModelResponse
from agents.models.openai_responses import OpenAIResponsesModel
from agents.usage import Usage
from openai import AsyncOpenAI
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseOutputText,
    ResponseReasoningItem,
)

from jeff.agent import Agent
from kernel import events, store, verbs
from tests.component_fixtures import click_cases, counter


def call(name, args, id="1"):
    return ResponseFunctionToolCall(
        type="function_call",
        id="fc_" + id,
        call_id="call_" + id,
        name=name,
        arguments=json.dumps(args),
        status="completed",
    )


def reply(text):
    return ResponseOutputMessage(
        type="message",
        id="msg_1",
        role="assistant",
        status="completed",
        content=[ResponseOutputText(type="output_text", text=text, annotations=[])],
    )


class ScriptedModel(Model):
    def __init__(self, script):
        self.script = list(script)
        self.requests = []

    async def get_response(self, **kwargs):
        self.requests.append(
            {
                "input": copy.deepcopy(kwargs["input"]),
                "instructions": kwargs["system_instructions"],
                "tools": [t.name for t in kwargs["tools"]],
                "settings": kwargs["model_settings"],
                "tracing": kwargs["tracing"],
            }
        )
        step = self.script.pop(0)
        output = step() if callable(step) else step
        return ModelResponse(output=output, usage=Usage(), response_id=None)

    async def stream_response(self, **kwargs):
        raise AssertionError("the bounded adapter does not stream")
        yield


def astra(world, model):
    return Agent(world, provider="openai-agents", model="gpt-6-astra", client=model)


def test_sdk_preserves_reasoning_history_and_uses_only_world_tools(world):
    verbs.ensure_desk(world)
    ref = verbs.mint(world, "alex", {"core.name": {"name": "Before"}})
    verbs.place(world, "alex", ref)
    model = ScriptedModel(
        [
            [
                ResponseReasoningItem(
                    type="reasoning", id="rs_1", summary=[], encrypted_content="opaque-reasoning"
                ),
                call(
                    "attach", {"entity": ref, "facet_type": "core.name", "body": {"name": "After"}}
                ),
            ],
            [reply("Renamed.")],
            [reply("Still here.")],
        ]
    )
    agent = astra(world, model)
    turn = agent.turn("Rename the note.")
    assert turn.reply == "Renamed." and turn.calls[0]["result"]["written_by"] == "jeff"
    assert "Before" not in model.requests[0]["instructions"]
    assert "Before" in model.requests[0]["input"][0]["content"]
    assert "After" in model.requests[1]["input"][0]["content"]
    assert model.requests[0]["tools"] == [v.name for v in verbs.REGISTRY]
    assert model.requests[0]["tracing"].is_disabled()
    settings = model.requests[0]["settings"]
    assert settings.reasoning.effort == "medium" and settings.store is False
    assert settings.temperature is None and settings.parallel_tool_calls is False
    assert any(i.get("encrypted_content") == "opaque-reasoning" for i in agent.history)
    agent.turn("Remember the change?")
    assert (
        sum(
            i.get("content", "").startswith("Untrusted world data:")
            for i in model.requests[-1]["input"]
            if isinstance(i.get("content"), str)
        )
        == 1
    )
    rebuilt = store.rebuild(world.world)
    try:
        assert rebuilt.snapshot() == world.snapshot()
    finally:
        rebuilt.close()


def test_sdk_discovers_new_action_in_the_same_turn(world):
    verbs.ensure_desk(world)
    ref = verbs.mint(world, "jeff", {"core.component": counter()})
    verbs.test_component(world, "jeff", ref, click_cases())
    model = ScriptedModel(
        [
            [call("activate_component", {"entity": ref, "revision": 1, "expected_revision": 0})],
            [call("extension_increment", {"amount": 5}, "2")],
            [reply("Five.")],
        ]
    )
    turn = astra(world, model).turn("Activate it and increment by five.")
    assert not any("error" in c for c in turn.calls)
    assert "extension_increment" not in model.requests[0]["tools"]
    assert "extension_increment" in model.requests[1]["tools"]
    assert verbs.component_view(world, "alex")["tree"]["text"] == "5"


def test_sdk_refusals_are_returned_and_actor_cannot_be_forged(world):
    ref = verbs.mint(world, "alex")
    before = world.world.log.read_bytes()
    model = ScriptedModel(
        [
            [call("attach", {"entity": ref, "facet_type": "core.name", "body": {"nom": "bad"}})],
            [
                call(
                    "attach",
                    {
                        "entity": ref,
                        "facet_type": "core.name",
                        "body": {"name": "bad"},
                        "actor": "alex",
                    },
                    "2",
                )
            ],
            [reply("Refused.")],
        ]
    )
    turn = astra(world, model).turn("Try invalid requests.")
    assert all("error" in c for c in turn.calls)
    assert world.world.log.read_bytes() == before
    outputs = [i for i in model.requests[-1]["input"] if i.get("type") == "function_call_output"]
    assert len(outputs) == 2 and all("error" in json.loads(i["output"]) for i in outputs)


def test_sdk_stop_keeps_completed_work_and_blocks_later_dispatch(world):
    ref = verbs.mint(world, "alex")
    model = ScriptedModel([])
    agent = astra(world, model)

    def stopped_response():
        agent.cancel()
        return [
            call(
                "attach",
                {"entity": ref, "facet_type": "core.name", "body": {"name": "Too late"}},
                "2",
            )
        ]

    model.script = [
        [call("attach", {"entity": ref, "facet_type": "core.name", "body": {"name": "Saved"}})],
        stopped_response,
        [reply("Resumed.")],
    ]
    turn = agent.turn("Do two changes.")
    assert turn.reply.startswith("Stopped.")
    assert turn.calls[-1]["error"] == "cancelled before dispatch"
    assert world.facet(ref, "core.name").body == {"name": "Saved"}
    assert agent.turn("Continue.").reply == "Resumed."
    assert len(list(events.replay(world.world))) == 2


def test_sdk_outer_budget_is_finite_and_keeps_tool_results(world, monkeypatch):
    monkeypatch.setattr("jeff.agent.MAX_STEPS", 1)
    model = ScriptedModel([[call("mint", {})]])
    agent = astra(world, model)
    turn = agent.turn("Create an object.")
    assert "too many steps" in turn.reply and len(turn.calls) == 1
    assert agent.history[-1]["type"] == "function_call_output"


def test_missing_key_fails_before_mutation_or_history(world, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    agent = Agent(world, provider="openai-agents", model="gpt-6-astra")
    before = world.world.log.read_bytes()
    with pytest.raises(ValueError, match="Set OPENAI_API_KEY locally"):
        agent.turn("Change something.")
    assert agent.history == [] and world.world.log.read_bytes() == before


def test_sdk_unknown_tool_is_an_instructive_refusal(world):
    before = world.world.log.read_bytes()
    model = ScriptedModel([[call("nonexistent", {})], [reply("Corrected.")]])
    turn = astra(world, model).turn("Try an unavailable tool.")
    assert turn.reply == "Corrected."
    assert turn.calls[0]["error"] == "tool is not available"
    assert any(i.get("type") == "function_call_output" for i in model.requests[-1]["input"])
    assert world.world.log.read_bytes() == before


def test_actual_responses_transport_and_dynamic_tool_schemas(world):
    requests = []
    outputs = [[call("mint", {"facets": {"core.name": {"name": "SDK note"}}})], [reply("Created.")]]

    def respond(request):
        assert request.url.path == "/v1/responses"
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "id": "resp_" + str(len(requests)),
                "object": "response",
                "created_at": 0,
                "status": "completed",
                "model": "gpt-6-astra",
                "error": None,
                "output": [item.model_dump() for item in outputs.pop(0)],
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "total_tokens": 15,
                    "input_tokens_details": {"cached_tokens": 0},
                    "output_tokens_details": {"reasoning_tokens": 0},
                },
            },
        )

    client = AsyncOpenAI(
        api_key="offline-test",
        base_url="https://offline.invalid/v1",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond)),
        max_retries=0,
    )
    try:
        agent = astra(world, OpenAIResponsesModel("gpt-6-astra", client))
        assert agent.turn("Create a note.").reply == "Created."
    finally:
        asyncio.run(client.close())
    assert len(requests) == 2
    request = requests[0]
    assert request["model"] == "gpt-6-astra" and request["store"] is False
    assert request["reasoning"]["effort"] == "medium"
    assert request["max_output_tokens"] == 32768
    assert "temperature" not in request and "top_p" not in request
    assert all(t["type"] == "function" and t["strict"] is False for t in request["tools"])
    mint = next(t for t in request["tools"] if t["name"] == "mint")
    assert "core.component" in mint["parameters"]["properties"]["facets"]["properties"]
    outputs = [i for i in requests[1]["input"] if i.get("type") == "function_call_output"]
    assert json.loads(outputs[0]["output"])["result"]["entity"].startswith("ent_")
