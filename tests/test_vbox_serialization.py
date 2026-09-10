import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from agora3.guest import Guest, GuestError


def test_control_calls_share_one_lock_across_guest_instances(tmp_path, monkeypatch):
    monkeypatch.setenv("AGORA_VBOX_LOCKFILE", str(tmp_path / "vbox.lock"))
    state = {"active": 0, "maximum": 0}
    mutex = threading.Lock()

    def process(args, timeout):
        with mutex:
            state["active"] += 1
            state["maximum"] = max(state["maximum"], state["active"])
        time.sleep(0.02)
        with mutex:
            state["active"] -= 1
        return {"exit_code": 0, "stdout": "ok", "stderr": ""}

    monkeypatch.setattr("agora3.guest._process", process)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: Guest._vbox("showvminfo", "test"), range(8)))
    assert results == ["ok"] * 8 and state["maximum"] == 1


def test_only_transient_reads_retry_and_failure_releases_lock(tmp_path, monkeypatch):
    monkeypatch.setenv("AGORA_VBOX_LOCKFILE", str(tmp_path / "vbox.lock"))
    calls = []

    def process(args, timeout):
        calls.append(args)
        return {"exit_code": 1, "stdout": "", "stderr": "already locked for a session"}

    monkeypatch.setattr("agora3.guest._process", process)
    monkeypatch.setattr("agora3.guest.time.sleep", lambda _: None)
    with pytest.raises(GuestError):
        Guest._vbox("showvminfo", "test")
    assert len(calls) == 3
    with pytest.raises(GuestError):
        Guest._vbox("snapshot", "test", "restore", "clean")
    assert len(calls) == 4
    monkeypatch.setattr(
        "agora3.guest._process", lambda *a: {"exit_code": 0, "stdout": "recovered", "stderr": ""}
    )
    assert Guest._vbox("showvminfo", "test") == "recovered"
