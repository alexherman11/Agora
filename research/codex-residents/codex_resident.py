"""Codex SDK transport for house messages, including explicitly selected image crops.

No desk code is imported here. The house owns identity, the welcome, wake/rest,
news, commands and commissions. This process only turns a user message into
assistant text, with an empty system/developer prompt and no tools.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import queue
import sys
import threading
from pathlib import Path

from openai_codex.client import CodexClient, CodexConfig
from pydantic import BaseModel

SDK_VERSION = "0.147.0"
MODEL = "gpt-6-astra"
PROFILE = Path(__file__).resolve().parents[2] / "local" / "codex-residents" / "profile"
DISABLED = """
apps connectors plugins remote_plugin recommended_plugins plugin_hooks hooks codex_hooks
shell_tool unified_exec shell_snapshot apply_patch_freeform view_image
js_repl js_repl_tools_only code_mode code_mode_only code_mode_host
computer_use browser_use browser_use_external in_app_browser
multi_agent multi_agent_v2 collab collaboration_modes goals token_budget
memories memory_tool external_agent_memory_import chronicle image_generation imagegenext
workspace_dependencies web_search web_search_cached web_search_request standalone_web_search
tool_search search_tool skill_search tool_suggest deferred_executor
request_permissions request_permissions_tool request_rule current_time_reminder
default_mode_request_user_input skill_mcp_dependency_install sleep_tool
""".split()


def resident_inputs(content):
    if isinstance(content, str):
        return content
    result = []
    for block in content:
        if block.get("type") == "text":
            result.append({"type": "text", "text": block["text"]})
        elif block.get("type") == "image":
            source = block.get("source") or {}
            if source.get("type") != "base64" or source.get("media_type") != "image/png":
                raise ValueError("Resident images must be selected PNG crops")
            import base64

            raw = base64.b64decode(source["data"], validate=True)
            if not raw.startswith(b"\x89PNG\r\n\x1a\n") or len(raw) > 2 * 1024 * 1024:
                raise ValueError("Invalid resident PNG crop")
            result.append({"type": "image", "url": "data:image/png;base64," + source["data"]})
        else:
            raise ValueError("Unsupported resident input block")
    return result


class ThreadIdentity(BaseModel):
    id: str


class ThreadEnvelope(BaseModel):
    thread: ThreadIdentity
    model: str


class ConfigEnvelope(BaseModel):
    config: dict


def deny(method, params):
    if method == "item/permissions/requestApproval":
        return {"permissions": {}, "scope": "turn"}
    if method == "item/tool/call":
        return {
            "success": False,
            "contentItems": [{"type": "inputText", "text": "No tools are available."}],
        }
    return {"decision": "decline"}


def runtime_config(directory, binary=None):
    from runtime_pin import catalog_matches, ensure_runtime

    lock = ensure_runtime()
    binary = binary or os.environ.get("HOUSE_CODEX_BIN") or lock["binary"]
    if (
        not Path(binary).is_file()
        or hashlib.sha256(Path(binary).read_bytes()).hexdigest() != lock["binary_sha256"]
    ):
        raise RuntimeError("Runtime override does not match the checked pin")
    catalog = Path(__file__).with_name("model-catalog.json")
    if not catalog_matches(catalog, lock["catalog_sha256"]):
        raise RuntimeError("Pinned resident catalog changed")
    return build_config(directory, binary, PROFILE)


def build_config(directory, binary, profile):
    """Configuration only; candidate probes use their own empty profile."""
    if importlib.metadata.version("openai-codex") != SDK_VERSION:
        raise RuntimeError(
            f"This adapter was verified with openai-codex=={SDK_VERSION}; recheck before upgrading"
        )
    if any((Path(profile) / name).exists() for name in ("AGENTS.md", "AGENTS.override.md")):
        raise RuntimeError("Resident profile contains global instructions; keep its prompt empty")
    overrides = [f"features.{name}=false" for name in DISABLED] + [
        'web_search="disabled"',
        "tools.update_plan.enabled=false",
        "tools.experimental_request_user_input.enabled=false",
        "project_doc_max_bytes=0",
        "skills.include_instructions=false",
        "skills.bundled.enabled=false",
        "features.skip_host_skill_discovery=true",
        "orchestrator.skills.enabled=false",
        "orchestrator.mcp.enabled=false",
        "memories.generate_memories=false",
        "memories.use_memories=false",
        "include_environment_context=false",
        "include_apps_instructions=false",
        "include_permissions_instructions=false",
        "include_collaboration_mode_instructions=false",
        "analytics.enabled=false",
        'history.persistence="none"',
        'developer_instructions=""',
        'instructions=""',
        "agents.enabled=false",
        "notify=[]",
        "model_catalog_json=" + json.dumps(str(Path(__file__).with_name("model-catalog.json"))),
    ]
    env = {k: "" for k in os.environ if k.startswith("CODEX_") and k != "CODEX_HOME"}
    env["CODEX_HOME"] = str(profile)
    return CodexConfig(
        codex_bin=binary,
        cwd=str(directory),
        env=env,
        config_overrides=tuple(overrides),
        client_name="agora_desk_resident",
        client_title="Agora Desk resident",
    )


def thread_parameters(client, directory, model, *, config=None, ephemeral=False):
    effective = client.request("config/read", {}, response_model=ConfigEnvelope).config
    isolated = {
        "mcp_servers": {name: {"enabled": False} for name in effective.get("mcp_servers") or {}}
    }
    isolated.update(config or {})
    return {
        "model": model,
        "modelProvider": "openai",
        "cwd": str(directory),
        "config": isolated,
        "environments": [],
        "selectedCapabilityRoots": [],
        "approvalPolicy": "never",
        "sandbox": "read-only",
        "baseInstructions": "",
        "developerInstructions": "",
        "dynamicTools": [],
        "ephemeral": ephemeral,
    }


def event_data(event):
    value = event.payload
    raw = getattr(value, "params", None)
    return raw if isinstance(raw, dict) else value.model_dump(by_alias=True, mode="json")


def receive(client, turn_id, emit):
    """Keep completed text in order; a failed/interrupted turn runs no desk lines."""
    messages = {}
    try:
        while True:
            event = client.next_turn_notification(turn_id)
            data = event_data(event)
            emit({"type": "codex_event", "method": event.method, "data": data})
            if event.method == "item/completed":
                item = data.get("item") or {}
                if item.get("type") == "agentMessage":
                    messages[item["id"]] = item.get("text", "")
                elif item.get("type") == "contextCompaction":
                    emit({"type": "system", "subtype": "compact_boundary"})
            elif event.method == "thread/compacted":
                emit({"type": "system", "subtype": "compact_boundary"})
            elif event.method == "turn/completed":
                turn = data["turn"]
                if turn["status"] != "completed":
                    error = turn.get("error") or {}
                    emit(
                        {
                            "type": "result",
                            "is_error": True,
                            "subtype": turn["status"],
                            "result": error.get("message") or turn["status"],
                        }
                    )
                    return False
                text = "\n".join(messages.values())
                emit(
                    {
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": text}],
                        },
                    }
                )
                emit({"type": "result", "is_error": False, "result": text})
                return True
    finally:
        client.unregister_turn_notifications(turn_id)


def output(event):
    print(json.dumps(event, ensure_ascii=False), flush=True)


def serve(args):
    directory = Path.cwd()
    incoming, closed = queue.Queue(), threading.Event()

    def read_input():
        try:
            for line in sys.stdin:
                incoming.put(json.loads(line))
        finally:
            closed.set()
            incoming.put(None)

    # A house closes stdin to stop a resident. Interrupt an in-flight model turn,
    # including when EOF arrives while the main thread waits for runtime events.
    threading.Thread(target=read_input, daemon=True).start()
    with CodexClient(runtime_config(directory), approval_handler=deny) as client:
        client.initialize()
        available = {m.model for m in client.model_list(True).data}
        if args.model not in available:
            raise RuntimeError(f"{args.model} is unavailable; no model was substituted")
        parameters = thread_parameters(client, directory, args.model)
        if args.resume:
            parameters.pop("dynamicTools")
            parameters.pop("ephemeral")
            started = client.request(
                "thread/resume",
                {"threadId": args.resume, **parameters},
                response_model=ThreadEnvelope,
            )
            if started.thread.id != args.resume:
                raise RuntimeError("The runtime resumed another conversation")
        else:
            started = client.request("thread/start", parameters, response_model=ThreadEnvelope)
        if started.model != args.model:
            raise RuntimeError("The runtime selected another model")
        output(
            {
                "type": "system",
                "subtype": "init",
                "session_id": started.thread.id,
                "model": started.model,
                "sdk": SDK_VERSION,
                "tools": [],
                "system_prompt": "",
            }
        )
        while True:
            message = incoming.get()
            if message is None:
                break
            if message.get("type") != "user":
                raise ValueError("Expected a house user message")
            content = message["message"]["content"]
            text = resident_inputs(content)
            turn_id = client.turn_start(
                started.thread.id, text, {"effort": args.reasoning, "environments": []}
            ).turn.id
            finished = threading.Event()

            def watch(turn=turn_id, done=finished):
                import time

                deadline = time.monotonic() + args.timeout
                while not done.wait(0.1):
                    if closed.is_set() or time.monotonic() >= deadline:
                        timer = threading.Timer(5, client.close)
                        timer.daemon = True
                        timer.start()
                        try:
                            client.turn_interrupt(started.thread.id, turn)
                            done.wait(5)
                        finally:
                            if not done.is_set():
                                client.close()
                            timer.cancel()
                        return

            watcher = threading.Thread(target=watch, daemon=True)
            watcher.start()
            try:
                if not receive(client, turn_id, output):
                    return 1
            finally:
                finished.set()
                watcher.join(timeout=6)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--resume")
    parser.add_argument("--reasoning", default="medium")
    parser.add_argument("--timeout", type=float, default=1200)
    args = parser.parse_args()
    try:
        return serve(args)
    except Exception as exc:
        output(
            {
                "type": "result",
                "is_error": True,
                "subtype": type(exc).__name__,
                "result": str(exc)[:1000],
            }
        )
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
