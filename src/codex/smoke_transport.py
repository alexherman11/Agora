"""Bounded live SDK check: two turns and process resume, no desk access."""

import json
import queue
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def visit(directory, prompt, resume=None):
    cmd = [sys.executable, str(HERE / "codex_resident.py"), "--timeout", "180"]
    if resume:
        cmd += ["--resume", resume]
    proc = subprocess.Popen(
        cmd,
        cwd=directory,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    events = queue.Queue()

    def read():
        for line in proc.stdout:
            events.put(json.loads(line))
        events.put(None)

    threading.Thread(target=read, daemon=True).start()
    proc.stdin.write(
        json.dumps({"type": "user", "message": {"content": [{"type": "text", "text": prompt}]}})
        + "\n"
    )
    proc.stdin.flush()
    deadline, sid, result = time.monotonic() + 200, None, None
    try:
        while time.monotonic() < deadline:
            ev = events.get(timeout=max(0.1, deadline - time.monotonic()))
            if ev is None:
                raise RuntimeError("Adapter exited before a result: " + proc.stderr.read()[-1000:])
            if ev.get("subtype") == "init":
                sid = ev["session_id"]
            if ev.get("type") == "result":
                result = ev
                break
        assert result and not result.get("is_error"), result
        return sid, result["result"]
    finally:
        proc.stdin.close()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def main():
    with tempfile.TemporaryDirectory(prefix="agora-codex-smoke-") as directory:
        sid, first = visit(
            directory, "Remember the word lantern. Reply with exactly READY, and nothing else."
        )
        print(json.dumps({"first": first, "thread": sid}), flush=True)
        resumed, second = visit(
            directory, "What single word did I ask you to remember? Reply with only that word.", sid
        )
        print(json.dumps({"second": second, "same_thread": resumed == sid}), flush=True)
        assert first.strip() == "READY" and second.strip().lower() == "lantern" and sid == resumed
    print(
        "PASS: live gpt-6-astra reply and conversation resume across adapter processes; "
        "no desk actions"
    )


if __name__ == "__main__":
    main()
