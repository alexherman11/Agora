"""Two-team research desks using the existing text-desk engine.

Private local state, per-actor attention, OS locking, atomic file replacement.
This is a research launcher, not Agora's authenticated native gateway.
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
import time
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent / "text-desk-lab" / "notation"
sys.path.insert(0, str(ENGINE))
from explore import fresh  # noqa: E402


@contextmanager
def session_lock(path, timeout=30):
    """An OS-owned lock releases on process death; no stale-file deletion."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if handle.seek(0, 2) == 0:
            handle.write(b"0")
            handle.flush()
        deadline = time.monotonic() + timeout
        while True:
            handle.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except (OSError, BlockingIOError):
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        "Desk busy; retry this invocation. No state changed."
                    ) from None
                time.sleep(0.05)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def run(state_dir, name, actor, lines, snapshot=False):
    state_dir = Path(state_dir)
    with session_lock(state_dir / (name + ".guard")):
        path = state_dir / (name + ".pickle")
        desk = pickle.loads(path.read_bytes()) if path.exists() else fresh()
        desk.world.me = actor
        per = getattr(desk, "_per", {})
        desk.seen, desk.open, desk.last_event_seen = per.get(
            actor, ({}, {desk.world.root}, len(desk.world.events))
        )
        desk._per = per
        if snapshot:
            return [json.dumps(desk.snapshot(), indent=2)], False
        output, refused = [], False
        for line in lines:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            result = desk.dispatch("desk", {"line": line})
            rendered = result.get("text") or ("ERR " + str(result.get("error")))
            output.append("> " + line + "\n" + rendered)
            if result.get("error"):
                refused = True
                break
        per[actor] = (desk.seen, desk.open, desk.last_event_seen)
        payload = pickle.dumps(desk)
        temporary = path.with_suffix(".tmp-" + str(os.getpid()))
        try:
            with temporary.open("wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()
        return output, refused


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--desk", choices=("team", "exchange"), default="team")
    parser.add_argument("--as", dest="actor", required=True)
    parser.add_argument("--command", action="append", default=[])
    parser.add_argument("--snapshot", action="store_true")
    args = parser.parse_args()
    actor = args.actor.strip().lower()
    if not actor or not all(c.isalnum() or c in "-_" for c in actor):
        parser.error("Use a nonempty actor name containing letters, digits, - or _.")
    lines = args.command or ([] if args.snapshot else sys.stdin.read().splitlines())
    output, refused = run(HERE / ".state", args.desk, actor, lines, args.snapshot)
    print("\n\n".join(output))
    return 1 if refused else 0


if __name__ == "__main__":
    raise SystemExit(main())
