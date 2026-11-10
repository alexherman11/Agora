"""Queue new Frontier @codex mentions for this chat's recurring heartbeat.

poll keeps mentions pending until ack records a response or a reviewed no-op.
Only the desk's HTTP event API is read; this script never writes to the world.
"""

import argparse
import json
import os
import re
import urllib.request
from pathlib import Path

STATE = Path(__file__).resolve().parents[2] / "local/codex-residents/mention-watch.json"
URL = "http://127.0.0.1:8794/api/events?session=frontier&as=codex&since="


def texts(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from texts(child)
    elif isinstance(value, list):
        for child in value:
            yield from texts(child)


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("poll", "ack"))
    parser.add_argument("ids", nargs="*")
    parser.add_argument("--note", default="")
    args = parser.parse_args()
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {
        "since": 4013, "pending": {}, "handled": {}
    }
    if args.action == "poll":
        with urllib.request.urlopen(URL + str(state["since"]), timeout=30) as response:
            result = json.load(response)
        if result["total"] < state["since"]:
            raise RuntimeError("Frontier event count moved backward; inspect before resetting it")
        for event in result["events"]:
            actor = str(event.get("by", "")).split("/")[0].lower()
            if actor in ("codex", "house") or event["id"] in state["handled"]:
                continue
            if any(re.search(r"(?<![\w@])@codex\b", s, re.I) for s in texts(event.get("args", {}))):
                state["pending"][event["id"]] = {
                    key: event.get(key) for key in ("id", "by", "at", "verb", "target", "args")
                }
        # since is an API array offset, not the numeric suffix of an event id.
        state["since"] = result["total"]
    else:
        if not args.ids or not args.note:
            parser.error("ack requires event ids and --note with a receipt or no-op reason")
        if any(event_id not in state["pending"] for event_id in args.ids):
            parser.error("ack ids must all be pending")
        for event_id in args.ids:
            del state["pending"][event_id]
            state["handled"][event_id] = args.note
    STATE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, STATE)
    output = {"since": state["since"], "pending": list(state["pending"].values())}
    print(json.dumps(output, ensure_ascii=False))


def main():
    # The background poller and this chat's ack/poll calls share the queue.
    # Serialize the whole read/modify/write, including the HTTP cursor advance.
    import msvcrt
    import time
    STATE.parent.mkdir(parents=True, exist_ok=True)
    with STATE.with_suffix(".lock").open("a+b") as lock:
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        deadline = time.monotonic() + 40
        while True:
            lock.seek(0)
            try:
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("Mention queue busy; retry without resetting it") from None
                time.sleep(0.1)
        run()


if __name__ == "__main__":
    main()
