"""Offline native admission tests with inherited-ACL, worktree-owned scratch.

Only pytest's scratch-directory fixture is replaced; engine/permission checks
are not replaced. System temp and the live sessions/captures are never opened.
"""
from pathlib import Path
import sys

LAB = Path(__file__).resolve().parents[1]
NOTATION = LAB.parent / "text-desk-lab" / "notation"
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(NOTATION))
import agora_tmp
import pytest


class Scratch:
    @pytest.fixture
    def tmp_path(self):
        # Retain owned test output for evidence. No foreign scratch cleanup.
        return Path(agora_tmp.directory("capture-admission-"))


if __name__ == "__main__":
    agora_tmp.configure()
    raise SystemExit(pytest.main([
        "-q", "-p", "no:cacheprovider",
        str(NOTATION / "test_capture_admission.py"),
        str(NOTATION / "test_message_context_lifecycle.py"),
        str(NOTATION / "test_message_context.py"),
    ], plugins=[Scratch()]))
