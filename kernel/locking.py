"""A reentrant, process-shared lock for each local world.
Never: never reads content, mutates world state, or supplies authority."""

from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from functools import wraps
from pathlib import Path

_guard = threading.Lock()
_locks: dict[str, threading.RLock] = {}
_local = threading.local()


@contextmanager
def locked(path: Path):
    key = str(path.resolve())
    with _guard:
        lock = _locks.setdefault(key, threading.RLock())
    with lock:
        held = getattr(_local, "held", set())
        if key in held:
            yield
            return
        with (path / ".world.lock").open("a+b") as handle:
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            _local.held = held | {key}
            try:
                yield
            finally:
                _local.held = held
                handle.seek(0)
                if os.name == "nt":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def synchronized(fn):
    """Serialize a Store method or a command whose first argument is a Store."""

    @wraps(fn)
    def call(world, *args, **kwargs):
        with locked(world.world.path):
            return fn(world, *args, **kwargs)

    return call
