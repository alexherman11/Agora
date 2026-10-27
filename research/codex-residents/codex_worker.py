"""Codex SDK coding worker speaking the existing house stream protocol."""

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

from codex_resident import (
    DISABLED,
    PROFILE,
    SDK_VERSION,
    ThreadEnvelope,
    deny,
    output,
    receive,
    refresh_charter,
    require_subscription,
)
from openai_codex.client import CodexClient, CodexConfig
from worker_job import child_job
from worker_lease import worker_leases

HERE = Path(__file__).resolve().parent
MODEL = "gpt-6.1-sol"


class SelectionRefused(RuntimeError):
    """A request/capability mismatch is not a transient runtime failure."""


def pinned_catalog(model):
    """Return the pinned catalog and hash for `model`.

    Astra uses the residents' model-catalog.json/runtime-lock.json; Sol keeps its own.
    """
    for name, lock_name in (
        ("worker-model-catalog.json", "worker-runtime-lock.json"),
        ("model-catalog.json", "runtime-lock.json"),
    ):
        path = HERE / name
        slugs = {
            m.get("slug") for m in json.loads(path.read_text(encoding="utf-8")).get("models", [])
        }
        if model in slugs:
            lock = json.loads((HERE / lock_name).read_text(encoding="utf-8"))
            return path, lock["catalog_sha256"]
    raise SelectionRefused(
        f"Requested model unavailable: {model} is in no pinned catalog; no substitution"
    )


def runtime_config(directory, model=MODEL, *, mcp=None):
    from runtime_pin import catalog_matches, ensure_runtime, worker_record_url

    catalog, catalog_sha = pinned_catalog(model)
    servers = json.loads(Path(mcp).read_text(encoding="utf-8"))["mcpServers"] if mcp else {}
    if set(servers) == {"agora"}:
        from kernel_runtime_record import KernelRecord
        from runtime_pin import Checker
        Checker(record=KernelRecord(mcp)).check()
    else:
        ensure_runtime(record_url=worker_record_url(mcp) if mcp else None)
    lock = json.loads((HERE / "worker-runtime-lock.json").read_text(encoding="utf-8"))
    binary = os.environ.get("HOUSE_CODEX_BIN") or lock["binary"]
    if (
        not Path(binary).is_file()
        or hashlib.sha256(Path(binary).read_bytes()).hexdigest() != lock["binary_sha256"]
    ):
        raise RuntimeError("Worker runtime override does not match the checked pin")
    if not catalog_matches(catalog, catalog_sha):
        raise RuntimeError("Pinned worker catalog changed")
    return build_config(directory, binary, PROFILE, catalog)


def build_config(directory, binary, profile, catalog):
    """Configuration only; candidate probes cannot load the sign-in profile."""
    if importlib.metadata.version("openai-codex") != SDK_VERSION:
        raise RuntimeError(f"Worker requires openai-codex=={SDK_VERSION}")
    enabled = {
        "shell_tool",
        "unified_exec",
        "apply_patch_freeform",
        "view_image",
        "web_search",
        "web_search_request",
        "standalone_web_search",
        # The pinned runtime's native discovery path emits an unsupported call
        # with live inference. Code mode exposes its supported discovery wrapper.
        "code_mode",
        "code_mode_host",
    }
    overrides = [f"features.{name}=false" for name in DISABLED if name not in enabled]
    overrides += [f"features.{name}=true" for name in enabled]
    overrides += [
        'web_search="live"',
        "project_doc_max_bytes=0",
        "skills.include_instructions=false",
        "skills.bundled.enabled=false",
        "features.skip_host_skill_discovery=true",
        "orchestrator.skills.enabled=false",
        "orchestrator.mcp.enabled=false",
        "memories.generate_memories=false",
        "memories.use_memories=false",
        "include_apps_instructions=false",
        "include_collaboration_mode_instructions=false",
        "analytics.enabled=false",
        'history.persistence="none"',
        "agents.enabled=false",
        "tools.experimental_request_user_input.enabled=false",
        "notify=[]",
        'windows.sandbox="unelevated"',
        'sandbox_mode="workspace-write"',
        'approval_policy="never"',
        "model_catalog_json=" + json.dumps(str(catalog)),
    ]
    # The SDK merges env into this process. Presence-only internal switches (CI,
    # desktop sandbox routing) must be absent, not present with empty values.
    for key in list(os.environ):
        if key.startswith("CODEX_"):
            os.environ.pop(key)
    env = {"CODEX_HOME": str(profile), "OPENAI_API_KEY": "", "CODEX_API_KEY": ""}
    return CodexConfig(
        codex_bin=binary,
        cwd=str(directory),
        env=env,
        config_overrides=tuple(overrides),
        client_name="agora_desk_worker",
        client_title="Agora Desk worker",
    )


def thread_parameters(directory, model, prompt, mcp, extra_config=None):
    servers = json.loads(Path(mcp).read_text(encoding="utf-8"))["mcpServers"]
    if set(servers) not in ({"desk"}, {"agora"}):
        raise ValueError("Worker configuration must expose exactly one authorized world server")
    tools = ["see", "do", "lines"] if set(servers) == {"agora"} else ["desk"]
    config = {
        "mcp_servers": {
            name: {
                **entry,
                "enabled": True,
                "enabled_tools": tools,
                "tools": {tool: {"approval_mode": "approve"} for tool in tools},
            }
            for name, entry in servers.items()
        }
    }
    # Git commits in the worker's existing tree use the shared object database.
    repo = HERE.parents[1]
    config["sandbox_workspace_write.writable_roots"] = [str(directory), str(repo / ".git")]
    # Compact before the pinned 272k context fills; retain the thread across cards and restarts.
    config["model_auto_compact_token_limit"] = 180000
    config.update(extra_config or {})
    return {
        "model": model,
        "modelProvider": "openai",
        "cwd": str(directory),
        "config": config,
        "approvalPolicy": "never",
        "sandbox": "workspace-write",
        "developerInstructions": prompt,
        "dynamicTools": [],
    }


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

    threading.Thread(target=read_input, daemon=True).start()
    prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    with (
        CodexClient(
            runtime_config(directory, args.model, mcp=args.mcp_config), approval_handler=deny
        ) as client,
        child_job(client._proc),
    ):
        client.initialize()
        require_subscription(client)
        validate_selection(client.model_list(True).data, args.model, args.reasoning)
        params = thread_parameters(directory, args.model, prompt, args.mcp_config)
        if args.resume:
            params.pop("dynamicTools")
            params["threadId"] = args.resume
        started = client.request(
            "thread/resume" if args.resume else "thread/start",
            params,
            response_model=ThreadEnvelope,
        )
        if started.model != args.model or (args.resume and started.thread.id != args.resume):
            raise RuntimeError("Worker model or resumed conversation identity changed")
        output(
            {
                "type": "system",
                "subtype": "init",
                "session_id": started.thread.id,
                "model": started.model,
                "sdk": SDK_VERSION,
                "provider": "codex",
            }
        )
        while True:
            message = incoming.get()
            if message is None:
                break
            if message.get("type") != "user":
                raise ValueError("Expected house user message")
            content = message["message"]["content"]
            text = (
                content
                if isinstance(content, str)
                else "\n".join(c["text"] for c in content if c.get("type") == "text")
            )
            require_subscription(client)
            turn_id = client.turn_start(started.thread.id, text, {"effort": args.reasoning}).turn.id
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


def validate_selection(models, model, effort):
    """Validate before thread creation or any turn, using runtime capabilities."""
    available = {m.model: m for m in models}
    if model not in available:
        raise SelectionRefused(f"Requested model unavailable: {model}; no substitution")
    metadata = available[model].model_dump(by_alias=True, mode="json")
    levels = {v["reasoningEffort"] for v in metadata.get("supportedReasoningEfforts", [])}
    if effort == "ultra" or effort not in levels:
        raise SelectionRefused(
            f"Requested effort unavailable: {effort}; no substitution or delegation"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--resume")
    parser.add_argument("--reasoning", default="medium")
    parser.add_argument("--timeout", type=float, default=3600)
    parser.add_argument("--mcp-config", required=True)
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--lease", action="append", default=[])
    parser.add_argument("--world")
    parser.add_argument("--target")
    parser.add_argument("--actor")
    args = parser.parse_args()
    try:
        with worker_leases(args.lease):
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
