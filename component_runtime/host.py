"""A serialized interpreter subprocess with fresh JS contexts and a hard response deadline."""

import atexit
import os
import subprocess
import sys
import threading
from pathlib import Path
from queue import Empty, Queue

_lock = threading.Lock()
_process = None
_responses = None


def _read(process, responses):
    while line := process.stdout.readline(500_002):
        responses.put(line)
    responses.put("")


def stop():
    global _process
    if _process:
        _process.kill()
        _process.wait()
        _process.stdin.close()
        _process.stdout.close()
        _process = None


def evaluate(data):
    global _process, _responses
    with _lock:
        if _process is None or _process.poll() is not None:
            stop()
            env = {
                k: v
                for k, v in os.environ.items()
                if k.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP"}
            }
            _process = subprocess.Popen(
                [sys.executable, "-I", str(Path(__file__).with_name("runner.py"))],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            _responses = Queue()
            threading.Thread(target=_read, args=(_process, _responses), daemon=True).start()
        try:
            _process.stdin.write(data + "\n")
            _process.stdin.flush()
            result = _responses.get(timeout=2)
            if not result or len(result) > 500_000 or not result.endswith("\n"):
                raise ValueError("interpreter stopped or exceeded the output limit")
            return result
        except (Empty, OSError, ValueError) as exc:
            stop()
            raise ValueError("component interpreter failed or exceeded its deadline") from exc


atexit.register(stop)
