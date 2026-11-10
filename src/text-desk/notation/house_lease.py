"""One process owns a world's house until its OS lock handle closes."""

import os
from contextlib import contextmanager


class HouseOwned(RuntimeError):
    """Another process already owns this world's house."""


@contextmanager
def house_lease(directory):
    # Separate from the short world journal lock: holding that would deadlock verbs.
    # Never unlink this file: contenders must lock the same underlying file.
    with (directory / "house-owner.lock").open("a+b") as stream:
        if not stream.tell():
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise HouseOwned("House world lease is held or unavailable") from exc
        # Closing releases the lock even on exceptions or process termination.
        yield
