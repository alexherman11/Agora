"""Real subprocess checks for exclusive ownership and adapter-crash cleanup."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from worker_lease import worker_leases

HERE = Path(__file__).resolve().parent


def test_worker_lease_survives_contention_and_releases_after_crash(tmp_path):
    lock = tmp_path / "worker.lock"
    code = (
        f"import sys;sys.path.insert(0,{str(HERE)!r});"
        "from worker_lease import worker_leases\n"
        "with worker_leases([sys.argv[1]]):\n"
        " print('READY',flush=True)\n"
        " sys.stdin.read()\n"
    )
    owner = subprocess.Popen(
        [sys.executable, "-c", code, str(lock)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert owner.stdout.readline().strip() == "READY"
        with pytest.raises(RuntimeError, match="Previous worker still owns"):
            with worker_leases([lock], timeout=0.1):
                pytest.fail("overlapping owners")
        owner.kill()
        owner.wait(timeout=5)
        with worker_leases([lock], timeout=1):
            assert lock.exists()
    finally:
        if owner.poll() is None:
            owner.kill()
            owner.wait(timeout=5)


@pytest.mark.skipif(os.name != "nt", reason="Windows process-tree recovery")
def test_adapter_death_terminates_only_its_runtime_child():
    import ctypes
    from ctypes import wintypes

    code = (
        f"import sys,subprocess;sys.path.insert(0,{str(HERE)!r});"
        "from worker_job import child_job\n"
        "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(120)'])\n"
        "with child_job(p):\n"
        " print(p.pid,flush=True)\n"
        " sys.stdin.read()\n"
    )
    owner = subprocess.Popen(
        [sys.executable, "-c", code], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
    )
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    api.OpenProcess.restype = wintypes.HANDLE
    api.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    api.WaitForSingleObject.restype = wintypes.DWORD
    api.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = None
    try:
        child = int(owner.stdout.readline().strip())
        handle = api.OpenProcess(0x100000, False, child)
        assert handle
        assert api.WaitForSingleObject(handle, 0) == 258  # child is still running
        owner.kill()
        owner.wait(timeout=5)
        assert api.WaitForSingleObject(handle, 5000) == 0  # OS job ended the orphan
    finally:
        if owner.poll() is None:
            owner.kill()
            owner.wait(timeout=5)
        if handle:
            api.CloseHandle(handle)
