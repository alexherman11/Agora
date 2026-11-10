"""Opt-in real-model check: discover and call the Desk from a worker worktree."""

import argparse
import json
import threading
import uuid
from pathlib import Path

from codex_resident import ThreadEnvelope, deny, receive
from codex_worker import MODEL, runtime_config, thread_parameters
from openai_codex.client import CodexClient
from worker_job import child_job


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", required=True)
    parser.add_argument("--cwd", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    folder = root / "local/codex-residents" / ("desk-probe-" + uuid.uuid4().hex[:10])
    folder.mkdir()
    directory = args.cwd.resolve() if args.cwd else folder
    mcp = folder / "mcp.json"
    mcp.write_text(json.dumps({"mcpServers": {"desk": {
        "command": str(root / ".venv/Scripts/python.exe"),
        "args": [str(root / "src/text-desk/notation/desk_mcp.py")],
        "env": {"DESK_AS": "codex", "DESK_PIN": "1", "DESK_SESSION": "frontier",
                "DESKD": "http://127.0.0.1:8794"},
    }}}), encoding="utf-8")
    events = []
    with (
        CodexClient(runtime_config(directory), approval_handler=deny) as client,
        child_job(client._proc),
    ):
        client.initialize()
        params = thread_parameters(
            directory, MODEL, "Read-only Desk transport test. Do not edit files or the Desk.",
            mcp,
        )
        params["ephemeral"] = True
        started = client.request("thread/start", params, response_model=ThreadEnvelope)
        turn = client.turn_start(
            started.thread.id,
            'Discover the desk tool, then call its help command. Do not use the shell or '
            'resources listing. Report whether you received the actual Desk manual.',
            {"effort": "low"},
        ).turn.id
        timer = threading.Timer(90, client.close)
        timer.start()
        try:
            ok = receive(client, turn, events.append)
        finally:
            timer.cancel()
    calls = [e["data"]["item"] for e in events if e.get("method") == "item/completed"
             and e.get("data", {}).get("item", {}).get("type") == "mcpToolCall"]
    result = {
        "thread": started.thread.id,
        "completed": ok,
        "desk_calls": [{"server": i.get("server"), "tool": i.get("tool"),
                        "status": i.get("status"), "error": i.get("error")} for i in calls],
        "report": [e.get("result") for e in events if e.get("type") == "result"],
    }
    (folder / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    assert ok and any(i.get("server") == "desk" and i["status"] == "completed" for i in calls)


if __name__ == "__main__":
    main()
