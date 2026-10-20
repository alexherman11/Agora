"""Scratch space for sandbox tools and their children, isolated per worktree.

AGORA_TMP overrides the default research/window-lab/.tmp-agora directory.
Use a worktree directory even when the system temp appears writable: a sandbox
can allow creating a directory there but refuse files inside it.
"""
import os
from pathlib import Path
import tempfile
from uuid import uuid4


def configure():
    """Set Python and inherited Windows/browser temp paths to the same directory."""
    root = Path(__file__).resolve().parents[2]
    chosen = Path(os.environ.get("AGORA_TMP") or root / "research/window-lab/.tmp-agora")
    if not chosen.is_absolute():
        chosen = root / chosen
    chosen = chosen.resolve()
    if not chosen.is_relative_to(root):
        raise ValueError("AGORA_TMP must be inside this worktree")
    chosen.mkdir(parents=True, exist_ok=True)
    for name in ("AGORA_TMP", "TMP", "TEMP", "TMPDIR"):
        os.environ[name] = str(chosen)
    tempfile.tempdir = str(chosen)
    return chosen


def directory(prefix):
    """Create a unique scratch directory inheriting the parent's Windows ACL.

    tempfile.mkdtemp uses mode 0o700, whose owner-only ACL can exclude the
    sandbox token. Keep the default mkdir mode; do not change anyone's ACL.
    """
    root = configure()
    while True:
        chosen = root / (prefix + uuid4().hex)
        try:
            os.makedirs(chosen)
            return str(chosen)
        except FileExistsError:
            continue
