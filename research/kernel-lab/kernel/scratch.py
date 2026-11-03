"""Scratch folders that a sandboxed worker can write to.

Since Python 3.12.4, tempfile.mkdtemp and tempfile.TemporaryDirectory on Windows make owner-only folders:
SYSTEM, Administrators and OWNER RIGHTS, with nothing inherited from the parent. The House's Codex workers run
in a Windows sandbox whose group CodexSandboxUsers gets Modify only by inheritance, so they cannot write into
such a folder ("Access is denied"), even inside their own worktree. A plain Path.mkdir inherits the parent's
ACL, so these replacements make the folder that way. Same signatures as tempfile's.
"""
import os
import shutil
import tempfile
import weakref
from pathlib import Path


def mkdtemp(suffix="", prefix="tmp", dir=None):
    """Make a fresh folder <dir>/<prefix><8 hex><suffix> that inherits its parent's ACL; return its path."""
    base = Path(dir) if dir is not None else Path(tempfile.gettempdir())
    for _ in range(100):
        path = base / f"{prefix}{os.urandom(4).hex()}{suffix}"
        try:
            path.mkdir(parents=True)
        except FileExistsError:
            continue
        return os.path.abspath(path)
    raise FileExistsError(f"no free scratch folder name under {base}")


def _remove(name, ignore_errors):
    shutil.rmtree(name, ignore_errors=ignore_errors)


class TemporaryDirectory:
    """Like tempfile.TemporaryDirectory, but the folder inherits its parent's ACL."""

    def __init__(self, suffix=None, prefix=None, dir=None, ignore_cleanup_errors=False):
        self.name = mkdtemp(suffix or "", "tmp" if prefix is None else prefix, dir)
        self._ignore_cleanup_errors = ignore_cleanup_errors
        self._finalizer = weakref.finalize(self, _remove, self.name, ignore_cleanup_errors)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name!r}>"

    def __enter__(self):
        return self.name

    def __exit__(self, *exc):
        self.cleanup()

    def cleanup(self):
        if self._finalizer.detach() is not None or os.path.exists(self.name):
            _remove(self.name, self._ignore_cleanup_errors)
