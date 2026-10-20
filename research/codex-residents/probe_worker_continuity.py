"""Opt-in real-model evidence: resume a worker thread, compact, then complete another turn."""

import argparse
import json
import threading
import time
import uuid
from pathlib import Path

from codex_resident import ThreadEnvelope, deny, receive
from codex_worker import MODEL, runtime_config, thread_parameters
from openai_codex.client import CodexClient
from worker_job import child_job


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", required=True)
    parser.parse_args()
    root = Path(__file__).resolve().parents[2] / "local/codex-residents"
    folder = root / ("continuity-probe-" + uuid.uuid4().hex[:10])
    first, second = folder / "first", folder / "second"
    first.mkdir(parents=True)
    second.mkdir()
    mcp = folder / "mcp.json"
    # Use the real worker configuration, but never ask the model to use any tool.
    mcp.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "desk": {
                        "command": str(
                            Path(__file__).resolve().parents[2] / ".venv/Scripts/python.exe"
                        ),
                        "args": [
                            str(
                                Path(__file__).resolve().parents[1]
                                / "text-desk-lab/notation/desk_mcp.py"
                            )
                        ],
                        "env": {
                            "DESK_AS": "codex",
                            "DESK_SESSION": "frontier",
                            "DESKD": "http://127.0.0.1:8794",
                        },
                    }
                }
            }
        )
    )
    marker = "walnut-" + uuid.uuid4().hex[:10]
    prompt = (
        "You are a continuity verification helper. Never use tools. "
        "Follow the short memory check precisely."
    )
    results = {"model": MODEL, "kind": "real model; no production task or file changes"}

    def turn(client, thread, text):
        events = []
        tid = client.turn_start(thread, text, {"effort": "low"}).turn.id
        assert receive(client, tid, events.append)
        assert not any(
            e.get("data", {}).get("item", {}).get("type") in ("commandExecution", "mcpToolCall")
            for e in events
        ), "Verification unexpectedly used a tool"
        return events[-1].get("result", "")

    for index, cwd in enumerate((first, second)):
        with (
            CodexClient(runtime_config(cwd), approval_handler=deny) as client,
            child_job(client._proc),
        ):
            timer = threading.Timer(120, client.close)
            timer.daemon = True
            timer.start()
            try:
                client.initialize()
                params = thread_parameters(cwd, MODEL, prompt, mcp)
                if index:
                    params.pop("dynamicTools")
                    params["threadId"] = results["thread"]
                started = client.request(
                    "thread/resume" if index else "thread/start",
                    params,
                    response_model=ThreadEnvelope,
                )
                if not index:
                    results["thread"] = started.thread.id
                    reply = turn(
                        client,
                        started.thread.id,
                        f"Remember the exact marker {marker}. Reply only SAVED.",
                    )
                    assert "SAVED" in reply
                    (folder / "result.json").write_text(json.dumps(results, indent=2))
                    print("First real turn completed; process closes before resume.", flush=True)
                else:
                    assert started.thread.id == results["thread"]
                    assert marker in turn(
                        client, started.thread.id, "What exact marker did I ask you to remember?"
                    )
                    results["resumed_in_new_process_and_cwd"] = True
                    print(
                        "Same thread resumed in a second process/cwd; marker recalled.", flush=True
                    )
                    (folder / "result.json").write_text(json.dumps(results, indent=2))

                    def turns(thread_id=started.thread.id):
                        data = client.thread_read(thread_id, include_turns=True).model_dump(
                            by_alias=True, mode="json"
                        )
                        return data["thread"].get("turns", [])

                    before = {t["id"] for t in turns()}
                    client.thread_compact(started.thread.id)
                    compacted = False
                    deadline = time.monotonic() + 90
                    while time.monotonic() < deadline:
                        completed = [
                            t
                            for t in turns()
                            if t["id"] not in before and t.get("status") == "completed"
                        ]
                        if any(
                            i.get("type") == "contextCompaction"
                            for t in completed
                            for i in t.get("items", [])
                        ):
                            compacted = True
                            break
                        time.sleep(0.5)
                    assert compacted
                    results["compaction_completed"] = True
                    assert marker in turn(
                        client,
                        started.thread.id,
                        "After compaction, repeat the exact saved marker.",
                    )
                    results["completed_turn_after_compaction"] = True
            finally:
                timer.cancel()
    (folder / "result.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2), flush=True)


if __name__ == "__main__":
    run()
