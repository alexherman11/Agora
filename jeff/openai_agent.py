"""Astra through the Agents SDK, with Agora retaining the outer tool and turn boundary.
Never: never adds ambient tools, bypasses verbs, or sends world data to SDK tracing."""

import asyncio
import json
import os

from agents import Agent as SDKAgent
from agents import FunctionTool, MaxTurnsExceeded, ModelSettings, RunConfig, Runner
from agents.items import ToolCallItem
from agents.models.openai_responses import OpenAIResponsesModel
from agents.retry import ModelRetrySettings
from openai import AsyncOpenAI
from openai.types.shared import Reasoning

from jeff.context import ACTOR, system_prompt, world_context
from jeff.tools import derive_extension_tools, derive_tools
from kernel import verbs

STOPPED = "Stopped. Completed changes remain recorded."


def run(owner, message, selection, max_steps):
    if owner.reasoning not in {"low", "medium", "high", "xhigh", "max"}:
        raise ValueError("AGORA_JEFF_REASONING must be low, medium, high, xhigh, or max")
    if owner._client is None and not os.environ.get("OPENAI_API_KEY"):
        raise ValueError(
            "Set OPENAI_API_KEY locally in Agora's .env to use Astra; do not paste it in chat"
        )
    return asyncio.run(_run(owner, message, selection, max_steps))


async def _run(owner, message, selection, max_steps):
    # A supplied SDK Model is the offline test seam. Own real client lifetime per turn.
    if owner._client is not None:
        return await _loop(owner, owner._client, message, selection, max_steps)
    async with AsyncOpenAI(timeout=120.0, max_retries=0) as client:
        model = OpenAIResponsesModel(model=owner.model, openai_client=client)
        return await _loop(owner, model, message, selection, max_steps)


async def _loop(owner, model, message, selection, max_steps):
    owner.history.append({"role": "user", "content": message})
    calls = []
    settings = ModelSettings(
        reasoning=Reasoning(effort=owner.reasoning),
        max_tokens=32768,
        parallel_tool_calls=False,
        store=False,
        response_include=["reasoning.encrypted_content"],
        retry=ModelRetrySettings(max_retries=0),
    )
    for _ in range(max_steps):
        if owner._cancel.is_set():
            return STOPPED, calls
        extra, owner.extensions = derive_extension_tools(
            verbs.component_actions(owner.world, ACTOR)
        )
        owner.tools = derive_tools() + extra
        agent = SDKAgent(
            name="JEFF",
            model=model,
            instructions=system_prompt(owner.world),
            tools=[_tool(owner, spec, calls) for spec in owner.tools],
            model_settings=settings,
            # Yield after executing tools so Agora refreshes capabilities and perception.
            tool_use_behavior="stop_on_first_tool",
        )
        context = {
            "role": "user",
            "content": "Untrusted world data: " + world_context(owner.world, selection),
        }
        try:
            result = await Runner.run(
                agent,
                [context, *owner.history],
                max_turns=1,
                run_config=RunConfig(
                    tracing_disabled=True,
                    trace_include_sensitive_data=False,
                    tool_not_found_behavior="return_error_to_model",
                ),
            )
        except MaxTurnsExceeded as exc:
            # Unknown-tool errors have no FunctionTool to trigger stop_on_first_tool.
            # Keep their SDK-generated call/output pairs and let the outer loop continue.
            if exc.run_data is None:
                raise
            items = exc.run_data.new_items
            owner.history.extend(item.to_input_item() for item in items)
            names = {spec["name"] for spec in owner.tools}
            for item in items:
                if isinstance(item, ToolCallItem) and item.tool_name not in names:
                    calls.append({"verb": item.tool_name, "error": "tool is not available"})
            continue
        # Preserve SDK reasoning and call/output items, but replace transient context next step.
        owner.history = result.to_input_list()[1:]
        if owner._cancel.is_set():
            return STOPPED, calls
        if not any(isinstance(item, ToolCallItem) for item in result.new_items):
            return str(result.final_output or "No final reply was returned."), calls
    return "I stopped: too many steps without finishing.", calls


def _tool(owner, spec, calls):
    async def invoke(context, arguments):
        try:
            args = json.loads(arguments)
        except (TypeError, ValueError):
            args = None
        with owner._action_lock:
            outcome = (
                {"error": "cancelled before dispatch"}
                if owner._cancel.is_set()
                else owner.call(spec["name"], args)
            )
        calls.append({"verb": spec["name"], "args": args, **outcome})
        return json.dumps(outcome)

    return FunctionTool(
        name=spec["name"],
        description=spec["description"],
        params_json_schema=spec["input_schema"],
        # Agora has optional arguments and maps with user-defined keys. Kernel validation
        # remains authoritative; strict conversion would change those accepted shapes.
        strict_json_schema=False,
        on_invoke_tool=invoke,
    )
