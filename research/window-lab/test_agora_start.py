"""Startup/recovery checks with isolated state and no production services launched."""

import importlib.util
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("agora_start", Path(__file__).with_name("agora_start.py"))
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


@pytest.fixture
def service_check(tmp_path, monkeypatch):
    monkeypatch.setattr(launcher, "STATE", tmp_path)
    monkeypatch.setattr(launcher, "STATUS", tmp_path / "status.json")
    monkeypatch.setattr(launcher, "log", lambda _: None)
    started = []
    monkeypatch.setattr(launcher, "start", lambda args, cwd, **kw: started.append((args, kw)))
    return started


def process(script, arguments=""):
    return {"ProcessId": 123, "CommandLine": f'"{launcher.PY}" "{script}" {arguments}'}


def test_cold_start_launches_keeper_before_hud(service_check, monkeypatch):
    monkeypatch.setattr(launcher, "process_inventory", lambda: [])
    monkeypatch.setattr(launcher, "door_up", lambda: False)
    launcher.tend()
    assert [Path(x[0][1]).name for x in service_check] == ["keeper.py"]


def test_live_services_are_adopted_without_restart(service_check, monkeypatch):
    entries = [process(launcher.NOTATION / "keeper.py", "frontier --port 8794"),
               process(launcher.NOTATION / "house.py", "frontier"),
               process(launcher.NOTATION / "door.py", "8794 --world frontier"),
               process(launcher.LAB / "hud.py")]
    monkeypatch.setattr(launcher, "process_inventory", lambda: entries)
    monkeypatch.setattr(launcher, "door_up", lambda: True)
    launcher.tend()
    assert service_check == []
    assert json.loads(launcher.STATUS.read_text())["door_ready"]


def test_orphan_door_restores_house_and_hud_not_second_keeper(service_check, monkeypatch):
    monkeypatch.setattr(launcher, "process_inventory",
                        lambda: [process(launcher.NOTATION / "door.py", "8794 --world frontier")])
    monkeypatch.setattr(launcher, "door_up", lambda: True)
    stale = launcher.STATE / "hud.pid"
    stale.write_text(str(__import__("os").getpid()))  # a live but unrelated PID must not block startup
    launcher.tend()
    assert [Path(x[0][1]).name for x in service_check] == ["house.py", "hud.py"]
    assert service_check[0][1]["env"]["DESKD"] == "http://127.0.0.1:8794"
    assert not stale.exists()


def test_inspection_failure_never_starts_services(service_check, monkeypatch):
    def failed():
        raise RuntimeError("CIM unavailable")
    monkeypatch.setattr(launcher, "process_inventory", failed)
    with pytest.raises(RuntimeError, match="CIM"):
        launcher.tend()
    assert service_check == []


def test_other_checkout_does_not_count_as_this_desk():
    entries = [process(Path("C:/Other/research/window-lab/hud.py"))]
    assert not launcher.script_pids(entries, launcher.LAB / "hud.py")


def test_launcher_lease_releases_after_process_death(tmp_path):
    lease = tmp_path / "launcher.lock"
    code = (
        f"import sys,os;sys.path.insert(0,{str(Path(__file__).parent)!r});"
        "from agora_start import lifetime_lease\n"
        "with lifetime_lease(sys.argv[1]) as acquired:\n"
        " print(acquired,os.getpid(),flush=True)\n"
        " sys.stdin.read()\n"
    )
    owner = subprocess.Popen([sys.executable, "-c", code, str(lease)],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    child = None
    try:
        ready, child = owner.stdout.readline().split()
        child = int(child)
        assert ready == "True"
        with launcher.lifetime_lease(lease) as acquired:
            assert not acquired
        os.kill(child, signal.SIGTERM)  # actual Python, not the venv's Windows redirector
        child = None
        owner.wait(timeout=5)
        with launcher.lifetime_lease(lease) as acquired:
            assert acquired
    finally:
        if child is not None:
            os.kill(child, signal.SIGTERM)
        if owner.poll() is None:
            owner.kill()
            owner.wait(timeout=5)
