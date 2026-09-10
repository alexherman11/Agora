"""Reentrant host-file serialization shared by threads and cooperating processes.
Never infer authority or mutate native records; callers own those decisions.
"""

import os
import threading
import time
from pathlib import Path

_registry_guard = threading.Lock()
_registry = {}


class _State:
    def __init__(self):
        self.mutex = threading.RLock()
        self.local = threading.local()


class ProcessLock:
    """Lock byte zero on Windows and the complete file on POSIX.

    Instances resolving to the same path share reentrancy within this process.
    The lock file must remain in place for the lifetime of the world service.
    """

    def __init__(self, path, timeout=15):
        self.path = Path(path).resolve()
        self.timeout = timeout
        key = os.path.normcase(str(self.path))
        with _registry_guard:
            self._state = _registry.setdefault(key, _State())

    def __enter__(self):
        if not self._state.mutex.acquire(timeout=self.timeout):
            raise TimeoutError("Timed out waiting for the native authority lock.")
        depth = getattr(self._state.local, "depth", 0)
        if depth:
            self._state.local.depth = depth + 1
            return self
        handle = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            handle = self.path.open("a+b")
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            deadline = time.monotonic() + self.timeout
            while True:
                try:
                    self._acquire(handle)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(
                            "Timed out waiting for another native world writer."
                        ) from None
                    time.sleep(0.02)
            self._state.local.handle = handle
            self._state.local.depth = 1
            return self
        except BaseException:
            if handle is not None:
                handle.close()
            self._state.mutex.release()
            raise

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            depth = self._state.local.depth - 1
            self._state.local.depth = depth
            if depth == 0:
                handle = self._state.local.handle
                try:
                    self._release(handle)
                finally:
                    handle.close()
                    del self._state.local.handle
        finally:
            self._state.mutex.release()

    @staticmethod
    def _acquire(handle):
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)

    @staticmethod
    def _release(handle):
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle, fcntl.LOCK_UN)
