import json
from unittest.mock import Mock

import pytest

from agora3.guest import GuestError
from agora3.yard import Yard

MAIN_ID = "70564d95-70e8-454a-8bf9-28ae8dffe3bc"
YARD_ID = "923edbbd-93a1-482e-b0c9-6b7b08b984c3"
SNAPSHOT = "f8173771-84af-4066-9960-6d7972f0a048"


def main_guest():
    return Mock(_config=Mock(return_value={"vm_id": MAIN_ID}))


def test_missing_yard_cannot_fall_back_to_live_guest(tmp_path):
    live = main_guest()
    yard = Yard(tmp_path / "missing.json", live)
    with pytest.raises(GuestError, match="not configured"):
        yard.run({"main.py": ""}, "main.py:main", {}, {})
    live.run.assert_not_called()
    live.execute.assert_not_called()


def test_yard_rejects_the_main_machine(tmp_path, monkeypatch):
    config = tmp_path / "yard.json"
    config.write_text(json.dumps({"machine_config": "machine.json", "snapshot_id": SNAPSHOT}))
    live = main_guest()
    monkeypatch.setattr("agora3.yard.Guest", lambda path: live)
    with pytest.raises(GuestError, match="different VM"):
        Yard(config, live).run({"main.py": ""}, "main.py:main", {}, {})
    live.stop.assert_not_called()
    live.run.assert_not_called()


def test_every_candidate_resets_and_stops_its_own_vm(tmp_path, monkeypatch):
    calls = []
    machine = Mock()
    machine.config_path = tmp_path / "candidate-machine.json"
    machine._config.return_value = {"vm_id": YARD_ID}
    machine.stop.side_effect = lambda: calls.append("stop")
    machine.start.side_effect = lambda: calls.append("start")
    machine._vbox.side_effect = lambda *args: calls.append(args)
    machine.run.side_effect = lambda *args: calls.append("run") or {"ok": True}
    yard = Yard(tmp_path / "yard.json", main_guest())
    monkeypatch.setattr(yard, "_configured", lambda: (machine, SNAPSHOT))
    monkeypatch.setattr(yard, "_ready", lambda guest: calls.append("ready"))
    for _ in range(2):
        assert yard.run({"main.py": ""}, "main.py:main", {}, {}) == {"ok": True}
    expected = ["stop", ("snapshot", YARD_ID, "restore", SNAPSHOT), "start", "ready", "run", "stop"]
    assert calls == expected * 2


def test_failed_candidate_is_powered_off(tmp_path, monkeypatch):
    machine = Mock()
    machine.config_path = tmp_path / "candidate-machine.json"
    machine._config.return_value = {"vm_id": YARD_ID}
    machine.run.side_effect = GuestError("action failed")
    yard = Yard(tmp_path / "yard.json", main_guest())
    monkeypatch.setattr(yard, "_configured", lambda: (machine, SNAPSHOT))
    monkeypatch.setattr(yard, "_ready", lambda guest: None)
    with pytest.raises(GuestError, match="action failed"):
        yard.run({"main.py": ""}, "main.py:main", {}, {})
    assert machine.stop.call_count == 2


def test_clean_baseline_refuses_live_token_configuration():
    machine = Mock()
    machine.execute.return_value = {"exit_code": 1, "stdout": "", "stderr": ""}
    with pytest.raises(GuestError, match="live bridge configuration"):
        Yard._ready(machine)
