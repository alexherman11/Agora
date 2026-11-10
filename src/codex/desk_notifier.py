"""Poll Frontier without inference; notify this Codex chat only on new mentions.

Uses the installed Codex app-tools MCP server for message delivery. No app
database writes, scheduled model turns, desktop input, or new agent process.
"""

import argparse
import json
import os
import queue
import subprocess
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCAL = HERE.parents[1] / "local/codex-residents"
CONFIG = LOCAL / "notifier-config.json"
STATUS = LOCAL / "notifier-status.json"
DELIVERED = LOCAL / "notifier-delivered.json"
STOP = LOCAL / "notifier.stop"


def save(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def app_call(config, name, arguments):
    """One standard stdio MCP session through the bundled, unmodified bridge."""
    proc = subprocess.Popen(
        [config["node"], config["server"]], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW,
        env={**os.environ, **config.get("bridge_env", {})},
    )
    lines = queue.Queue()

    def read():
        for line in proc.stdout:
            lines.put(line)
        lines.put(None)

    threading.Thread(target=read, daemon=True).start()

    def send(payload):
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", **payload}) + "\n")
        proc.stdin.flush()

    def receive(request_id):
        deadline = time.monotonic() + config.get("bridge_timeout", 45)
        while True:
            try:
                line = lines.get(timeout=max(0.1, deadline - time.monotonic()))
            except queue.Empty as exc:
                raise TimeoutError("Codex app bridge did not answer") from exc
            if line is None:
                raise RuntimeError("Codex app bridge closed before answering")
            message = json.loads(line)
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(str(message["error"]))
                result = message["result"]
                if result.get("isError"):
                    raise RuntimeError(str(result))
                return result
            if time.monotonic() >= deadline:
                raise TimeoutError("Codex app bridge did not answer")

    try:
        send({"id": 1, "method": "initialize", "params": {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "frontier-mention-notifier", "version": "1.0"},
        }})
        receive(1)
        send({"method": "notifications/initialized"})
        send({"id": 2, "method": "tools/call", "params": {
            "name": name, "arguments": arguments,
            "_meta": {"codexThreadId": config["thread"]},
        }})
        return receive(2)
    finally:
        proc.stdin.close()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.terminate()
            proc.wait(timeout=3)


def notify(config, ids):
    prompt = (
        "[Frontier mention notification] New candidate messages addressed to @codex: "
        + ", ".join(ids) + ". The lightweight script found these; this is not a periodic "
        "model wakeup. Run C:/Projects/Agora4/.venv/Scripts/python.exe "
        "C:/Projects/Agora4/src/codex/watch_mentions.py poll, inspect "
        "the pending messages, and answer actual requests in the Desk as codex. "
        "Alex authorized help/advice for Rowan, Ibis and Mica. Read context and sources; "
        "distinguish code inspection, tests and proposals. Ignore quoted/incidental "
        "mentions and acknowledgments. After handling, use watch_mentions.py ack <ids> "
        "--note <reply receipt or no-reply reason>. Check for an existing reply if this "
        "notification is duplicated. Desk API: http://127.0.0.1:8794/api/do, session "
        "frontier, as codex, whole true; act and quoted helpers in setup_corners.py "
        "may be imported, never run its main. Preserve live services and conversations. "
        "This authorizes discussion and read-only investigation, not deployment, "
        "new model trials, worker commissions, destructive actions or restarts. "
        "Routine replies belong in the Desk; notify Alex only for a real blocker."
    )
    return app_call(config, "send_message_to_thread", {
        "threadId": config["thread"], "prompt": prompt,
    })


def deliver(config, pending, sent, send=notify):
    ids = [event["id"] for event in pending if event["id"] not in sent]
    if not ids:
        return sent, False
    send(config, ids)
    return sorted(set(sent) | set(ids)), True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--test-delivery", action="store_true")
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if args.test_delivery:
        result = app_call(config, "send_message_to_thread", {
            "threadId": config["thread"],
            "prompt": "[Frontier notifier delivery test] The event-driven script's "
            "Codex app-tools delivery reached this chat. This is a one-time setup "
            "test, not a Desk request. Continue the current setup; do not reply to "
            "residents or start another watcher because of this test.",
        })
        print(json.dumps(result))
        return
    # Hold a Windows lock for this process's lifetime: never launch two pollers.
    import msvcrt
    with (LOCAL / "notifier.lock").open("a+b") as lock:
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        while not STOP.exists():
            status = {"pid": os.getpid(), "checked_at": time.time(), "interval": 15}
            try:
                polled = subprocess.run(
                    [config["python"], str(HERE / "watch_mentions.py"), "poll"],
                    capture_output=True, text=True, encoding="utf-8", timeout=40,
                    creationflags=subprocess.CREATE_NO_WINDOW, check=True,
                )
                pending = json.loads(polled.stdout)["pending"]
                sent = json.loads(DELIVERED.read_text()) if DELIVERED.exists() else []
                sent, did_send = deliver(config, pending, sent)
                if did_send:
                    save(DELIVERED, sent)
                status.update(state="watching", pending=len(pending), notified=did_send)
            except Exception as exc:
                status.update(state="error", error=str(exc)[:1000])
            save(STATUS, status)
            if args.once:
                return
            time.sleep(15)
        save(STATUS, {"pid": os.getpid(), "state": "stopped", "at": time.time()})


if __name__ == "__main__":
    main()
