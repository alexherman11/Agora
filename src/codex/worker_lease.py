"""Process-held worker/card leases prevent overlapping owners during recovery."""

import os
import time
from contextlib import ExitStack, contextmanager
from pathlib import Path


@contextmanager
def worker_leases(paths, timeout=45):
    """Acquire in a fixed order. OS locks are released even when the adapter is killed."""
    with ExitStack() as stack:
        for path in sorted({str(Path(p).resolve()) for p in paths}):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            file = stack.enter_context(open(path, "a+b"))
            if not file.tell():
                file.write(b"0")
                file.flush()
            deadline = time.monotonic() + timeout
            while True:
                try:
                    file.seek(0)
                    if os.name == "nt":
                        import msvcrt

                        msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl

                        fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise RuntimeError(
                            f"Previous worker still owns lease: {Path(path).parent.name}"
                        ) from None
                    time.sleep(0.2)
        yield
