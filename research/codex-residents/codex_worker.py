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
)
from openai_codex.client import CodexClient, CodexConfig

HERE = Path(__file__).resolve().parent
MODEL = "gpt-6.1-sol"


def runtime_config(directory):
    if importlib.metadata.version("openai-codex") != SDK_VERSION:
        raise RuntimeError(f"Worker requires openai-codex=={SDK_VERSION}")
    lock = json.loads((HERE / "worker-runtime-lock.json").read_text(encoding="utf-8"))
    catalog = HERE / "worker-model-catalog.json"
    for path, expected in ((Path(lock["binary"]), lock["binary_sha256"]),
                           (catalog, lock["catalog_sha256"])):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Pinned worker runtime changed: {path}")
    enabled = {"shell_tool", "unified_exec", "apply_patch_freeform", "view_image",
               "web_search", "web_search_request", "standalone_web_search"}
    overrides = [f"features.{name}=false" for name in DISABLED if name not in enabled]
    overrides += [f"features.{name}=true" for name in enabled]
    overrides += [
        'web_search="live"', "project_doc_max_bytes=0", "skills.include_instructions=false",
        "skills.bundled.enabled=false", "features.skip_host_skill_discovery=true",
        "orchestrator.skills.enabled=false", "orchestrator.mcp.enabled=false",
        "memories.generate_memories=false", "memories.use_memories=false",
        "include_apps_instructions=false", "include_collaboration_mode_instructions=false",
        "analytics.enabled=false", 'history.persistence="none"', "agents.enabled=false",
        "tools.experimental_request_user_input.enabled=false", "notify=[]",
        'windows.sandbox="unelevated"',
        'sandbox_mode="workspace-write"', 'approval_policy="never"',
        "model_catalog_json=" + json.dumps(str(catalog)),
    ]
    # The SDK merges env into this process. Presence-only internal switches (CI,
    # desktop sandbox routing) must be absent, not present with empty values.
    for key in list(os.environ):
        if key.startswith("CODEX_"):
            os.environ.pop(key)
    env = {"CODEX_HOME": str(PROFILE)}
    return CodexConfig(
        codex_bin=lock["binary"], cwd=str(directory), env=env,
        config_overrides=tuple(overrides), client_name="agora_desk_worker",
        client_title="Agora Desk worker",
    )


def thread_parameters(directory, model, prompt, mcp, extra_config=None):
    servers = json.loads(Path(mcp).read_text(encoding="utf-8"))["mcpServers"]
    if set(servers) != {"desk"}:
        raise ValueError("Worker configuration must expose only the authorized desk server")
    config = {"mcp_servers": {name: {**entry, "enabled": True,
                                    "enabled_tools": ["desk"],
                                    "tools": {"desk": {"approval_mode": "approve"}}}
                              for name, entry in servers.items()}}
    # Git commits in the worker's existing tree use the shared object database.
    repo = HERE.parents[1]
    config["sandbox_workspace_write.writable_roots"] = [str(directory), str(repo / ".git")]
    config.update(extra_config or {})
    return {
        "model": model, "modelProvider": "openai", "cwd": str(directory),
        "config": config,
        "approvalPolicy": "never", "sandbox": "workspace-write",
        "developerInstructions": prompt, "dynamicTools": [],
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
    with CodexClient(runtime_config(directory), approval_handler=deny) as client:
        client.initialize()
        if args.model not in {m.model for m in client.model_list(True).data}:
            raise RuntimeError(f"Requested model unavailable: {args.model}; no substitution")
        params = thread_parameters(directory, args.model, prompt, args.mcp_config)
        if args.resume:
            params.pop("dynamicTools")
            params["threadId"] = args.resume
        started = client.request(
            "thread/resume" if args.resume else "thread/start", params,
            response_model=ThreadEnvelope,
        )
        if started.model != args.model or (args.resume and started.thread.id != args.resume):
            raise RuntimeError("Worker model or resumed conversation identity changed")
        output({"type": "system", "subtype": "init", "session_id": started.thread.id,
                "model": started.model, "sdk": SDK_VERSION, "provider": "codex"})
        while True:
            message = incoming.get()
            if message is None:
                break
            if message.get("type") != "user":
                raise ValueError("Expected house user message")
            content = message["message"]["content"]
            text = content if isinstance(content, str) else "\n".join(
                c["text"] for c in content if c.get("type") == "text"
            )
            turn_id = client.turn_start(
                started.thread.id, text, {"effort": args.reasoning}
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
    parser.add_argument("--timeout", type=float, default=3600)
    parser.add_argument("--mcp-config", required=True)
    parser.add_argument("--prompt-file", required=True)
    args = parser.parse_args()
    try:
        return serve(args)
    except Exception as exc:
        output({"type": "result", "is_error": True,
                "subtype": type(exc).__name__, "result": str(exc)[:1000]})
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
