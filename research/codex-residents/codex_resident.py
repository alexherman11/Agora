"""Codex SDK transport for house messages, including explicitly selected image crops.

The house owns identity, wake/rest, news, commands and commissions. The sole
developer instruction is the live charter; its read-only compaction hook shares
the house reader. Residents still have no tools.
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
from openai_codex.generated.v2_all import ThreadInjectItemsResponse
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


def runtime_config(directory, binary=None, model=MODEL):
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
    return build_config(directory, binary, PROFILE, model=model)


def model_catalog(model):
    """Use reviewed model metadata; resident permissions/instructions stay empty.

    The original resident catalog contains Astra only. Sol's exact metadata is
    already pinned for builders; using it does not grant builder capabilities.
    """
    from runtime_pin import catalog_matches

    for name, pin in (("model-catalog.json", "runtime-lock.json"),
                      ("worker-model-catalog.json", "worker-runtime-lock.json")):
        path = Path(__file__).with_name(name)
        lock = json.loads(Path(__file__).with_name(pin).read_text(encoding="utf-8"))
        if not catalog_matches(path, lock["catalog_sha256"]):
            raise RuntimeError("Pinned model catalog changed")
        if model in {m["slug"] for m in json.loads(path.read_text(encoding="utf-8"))["models"]}:
            return path
    raise ValueError(f"{model} has no reviewed resident metadata; no model was substituted")


def require_subscription(client):
    """Read metadata only. Never log in/out, read tokens, or fall back to an API key."""
    result = client.account_read({"refreshToken": False})
    account = result.model_dump(by_alias=True, mode="json").get("account") or {}
    if account.get("type") != "chatgpt":
        raise RuntimeError("A ChatGPT subscription sign-in is required; no model turn was sent")
    config = client.request("config/read", {}, response_model=ConfigEnvelope).config
    custom = (config.get("model_providers") or {}).get("openai") or {}
    if any(custom.get(k) for k in ("base_url", "env_key", "experimental_bearer_token",
                                   "http_headers", "env_http_headers")):
        raise RuntimeError("Custom OpenAI authentication/routing is not allowed")
    return "chatgpt"


def build_config(directory, binary, profile, model=MODEL):
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
        "model_catalog_json=" + json.dumps(str(model_catalog(model))),
    ]
    env = {k: "" for k in os.environ if k.startswith("CODEX_") and k != "CODEX_HOME"}
    env["CODEX_HOME"] = str(profile)
    env["OPENAI_API_KEY"] = ""
    env["CODEX_API_KEY"] = ""
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


def refresh_charter(client, thread_id, args, emit):
    """A raw developer item is model-visible history, not a synthetic user turn."""
    if getattr(args, "kernel_context", None):
        # The new kernel uses the resident's existing door. Do not read an old
        # world or create a session to refresh its charter and next task rows.
        hook_dir = Path(__file__).resolve().parents[1] / "kernel-lab" / "modules" / "house"
        if str(hook_dir) not in sys.path:
            sys.path.insert(0, str(hook_dir))
        from charter_hook import context
        try:
            text = context(**json.loads(args.kernel_context))
            client.request("thread/inject_items", {"threadId": thread_id, "items": [
                {"type": "message", "role": "developer",
                 "content": [{"type": "input_text", "text": text}]}]},
                response_model=ThreadInjectItemsResponse)
            emit({"type": "kernel_context", "ok": True})
        except Exception as exc:
            emit({"type": "kernel_context", "ok": False, "error": type(exc).__name__})
        return
    if not getattr(args, "world", None):
        return
    notation = Path(__file__).resolve().parents[1] / "text-desk-lab" / "notation"
    if str(notation) not in sys.path:
        sys.path.insert(0, str(notation))
    import charter
    try:
        reading = charter.live_reading(args.world)
        text = reading.text
        client.request("thread/inject_items",
                       {"threadId": thread_id, "items": [
                           {"type": "message", "role": "developer",
                            "content": [{"type": "input_text", "text": text}]}]},
                       response_model=ThreadInjectItemsResponse)
        emit(charter.read_event(reading))
    except Exception as exc:
        # The current turn/pending messages must survive an unavailable charter.
        emit(charter.read_event(error=type(exc).__name__))


def emit_plan_usage(client, emit, timeout=2):
    """Optional metadata must not hold up answers or accumulate hung requests."""
    previous = vars(client).get("_agora_usage_job")
    if previous is not None and previous.is_alive():
        return
    job = threading.Thread(target=_read_plan_usage, args=(client, emit), daemon=True)
    client._agora_usage_job = job
    job.start()
    job.join(timeout)
    if job.is_alive():
        emit({"type": "plan_usage_unavailable", "provider": "codex",
              "reason": "Codex account/rateLimits/read timed out; waiting for CLI response"})


def _read_plan_usage(client, emit):
    """Read-only CLI account metadata. No account/credit mutations or model turn."""
    from openai_codex.generated.v2_all import GetAccountRateLimitsResponse
    try:
        result = client.request(
            "account/rateLimits/read", None, response_model=GetAccountRateLimitsResponse)
        raw = result.model_dump(by_alias=True, mode="json")
        # Never put account/credit details in the house stream.
        def bucket(value):
            if not isinstance(value, dict):
                return {}
            clean = {"limitId": value.get("limitId")}
            for name in ("primary", "secondary"):
                window = value.get(name)
                if isinstance(window, dict):
                    clean[name] = {
                        k: window.get(k) for k in ("usedPercent", "windowDurationMins", "resetsAt")}
            return clean
        data = {"rateLimits": bucket(raw.get("rateLimits")),
                "rateLimitsByLimitId": {
                    k: bucket(v) for k, v in (raw.get("rateLimitsByLimitId") or {}).items()}}
        emit({"type": "codex_event", "method": "account/rateLimits/read", "data": data})
    except Exception as exc:
        # Error strings can include request details; retain only the class.
        emit({"type": "plan_usage_unavailable", "provider": "codex",
              "reason": "Codex account/rateLimits/read unavailable (" + type(exc).__name__ + ")"})


def receive(client, turn_id, emit, on_compact=None):
    """Keep completed text in order; a failed/interrupted turn runs no desk lines."""
    messages = {}
    compacted_items = set()

    def compact(key):
        if key != "legacy" and "legacy" in compacted_items:
            compacted_items.remove("legacy")
            compacted_items.add(key)
            return
        if key not in compacted_items:
            compacted_items.add(key)
            emit({"type": "system", "subtype": "compact_boundary"})
            if on_compact:
                on_compact()
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
                    compact(item.get("id", "legacy"))
            elif event.method == "thread/compacted":
                if not compacted_items:   # legacy duplicate of the item lifecycle
                    compact("legacy")
            elif event.method == "turn/completed":
                emit_plan_usage(client, emit)
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
                emit({"type": "result", "is_error": False, "result": text, "turn_id": turn_id})
                return True
    finally:
        client.unregister_turn_notifications(turn_id)


_OUTPUT_LOCK = threading.Lock()


def output(event):
    # A late quota response may arrive alongside the next turn's stream.
    with _OUTPUT_LOCK:
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
    with CodexClient(runtime_config(directory, model=args.model), approval_handler=deny) as client:
        client.initialize()
        require_subscription(client)
        available = {m.model: m for m in client.model_list(True).data}
        if args.model not in available:
            raise RuntimeError(f"{args.model} is unavailable; no model was substituted")
        metadata = available[args.model].model_dump(by_alias=True, mode="json")
        efforts = {x["reasoningEffort"] for x in metadata.get("supportedReasoningEfforts", [])}
        if args.reasoning not in efforts:
            raise RuntimeError(f"Reasoning effort {args.reasoning} is unavailable; no substitution")
        parameters = thread_parameters(client, directory, args.model)
        if getattr(args, "mcp_config", None):
            # The kernel's house (kernel-lab/modules/house): the door adapter as this resident's one MCP server,
            # with its own session. Every other configured server stays disabled. Unproven with a live model.
            server = json.loads(Path(args.mcp_config).read_text(encoding="utf-8"))["mcpServers"]["agora"]
            parameters["config"]["mcp_servers"]["agora"] = server
        if getattr(args, "charter_file", None):
            parameters["developerInstructions"] = Path(args.charter_file).read_text(
                encoding="utf-8")
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
                "authentication": "chatgpt",
                "system_prompt": parameters["developerInstructions"],
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
            require_subscription(client)
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
                if not receive(client, turn_id, output, lambda: refresh_charter(
                        client, started.thread.id, args, output)):
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
    parser.add_argument("--charter-file")
    parser.add_argument("--world")
    parser.add_argument("--target")
    parser.add_argument("--actor")
    parser.add_argument("--mcp-config", help="a file naming the door adapter as the one MCP server (the kernel's house)")
    parser.add_argument("--kernel-context", help="House's read-only compaction context, using its existing door")
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
