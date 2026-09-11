from unittest.mock import Mock

import pytest

from agora3.check_tools import check_package
from agora3.gateway import Gateway
from agora3.guest import GuestError
from agora3.world import Refusal


@pytest.fixture
def setup(tmp_path, monkeypatch):
    gateway = Gateway(tmp_path)
    actor = gateway.principal("human")
    gateway.commit(
        actor,
        [{"id": "note", "expected_revision": 0, "facets": {"core.text": {"text": "original"}}}],
    )
    manifest = {
        "runtime": "python-1",
        "actions": {
            "edit": {
                "entry": "main.py:edit",
                "input_schema": {"type": "object"},
                "reads": {"ids": ["note"]},
            }
        },
    }
    gateway.packages.save(
        actor,
        id="test.check",
        expected_revision=0,
        files={"main.py": "def edit(args, ctx): return {}"},
        manifest=manifest,
    )
    calls = []
    machine = Mock()
    machine.config_path = tmp_path / "candidate-machine.json"
    machine._config.return_value = {"vm_id": "candidate"}
    machine.stop.side_effect = lambda: calls.append("stop")
    machine.start.side_effect = lambda: calls.append("start")
    machine._vbox.side_effect = lambda *args: calls.append(args)

    def run(files, entry, args, context, timeout=30):
        calls.append(entry)
        if entry == "__agora_check.py:main":
            return {"compiled": True}
        if args.get("error"):
            raise GuestError("intentional refusal")
        doc = next(o for o in context["objects"] if o["id"] == "note")
        return {
            "result": {"ok": True},
            "changes": [
                {
                    "id": "note",
                    "expected_revision": doc["revision"],
                    "facets": {"core.text": {"text": "candidate text"}},
                }
            ],
        }

    machine.run.side_effect = run
    monkeypatch.setattr(gateway.yard, "_configured", lambda: (machine, "clean"))
    monkeypatch.setattr(gateway.yard, "_ready", lambda guest: calls.append("ready"))
    monkeypatch.setattr(gateway.yard, "status", lambda: {"available": True})
    return gateway, actor, calls


def test_combined_checks_use_one_reset_and_never_apply_or_install(setup):
    gateway, actor, calls = setup
    result = check_package(
        gateway,
        actor,
        id="test.check",
        expected_revision=1,
        cases=[
            {"action": "edit", "args": {}, "expect_result": {"ok": True}},
            {"action": "edit", "args": {}, "expect_result": {"ok": True}},
        ],
    )
    assert result["passed"] and result["completed_cases"] == 2
    assert calls.count(("snapshot", "candidate", "restore", "clean")) == 1
    assert calls.count("stop") == 2 and calls.count("main.py:edit") == 2
    assert gateway.world.get("note")["revision"] == 1
    assert gateway.packages.installation("test.check")["revision"] == 0
    assert result["install_args"]["expected_revision"] == 0
    receipt = gateway.world.get(result["check_receipt"])["facets"]["agora.check"]
    assert all(r["proposed_changes"][0]["expected_revision"] == 1 for r in receipt["cases"])
    gateway.packages.install(actor, **result["install_args"])
    assert gateway.packages.installation("test.check")["revision"] == 1


def test_failed_case_records_prefix_and_stops_without_install_args(setup):
    gateway, actor, calls = setup
    result = check_package(
        gateway,
        actor,
        id="test.check",
        expected_revision=1,
        cases=[
            {"action": "edit", "args": {}, "expect_result": {"ok": True}},
            {"action": "edit", "args": {}, "expect_result": {"ok": False}},
            {"action": "edit", "args": {}, "expect_result": {"ok": True}},
        ],
    )
    assert not result["passed"] and result["completed_cases"] == 2
    assert "install_args" not in result and calls.count("stop") == 2
    assert gateway.world.get("note")["facets"]["core.text"]["text"] == "original"


def test_expected_error_is_checked_and_next_call_resets_again(setup):
    gateway, actor, calls = setup
    for _ in range(2):
        result = check_package(
            gateway,
            actor,
            id="test.check",
            expected_revision=1,
            cases=[
                {"action": "edit", "args": {"error": True}, "expect_error": "intentional refusal"}
            ],
        )
        assert result["passed"]
    assert calls.count(("snapshot", "candidate", "restore", "clean")) == 2


def test_invalid_case_and_stale_source_refuse_before_guest_start(setup):
    gateway, actor, calls = setup
    with pytest.raises(Refusal, match="Source revision changed"):
        check_package(
            gateway,
            actor,
            id="test.check",
            expected_revision=2,
            cases=[{"action": "edit", "args": {}}],
        )
    with pytest.raises(Refusal, match="both"):
        check_package(
            gateway,
            actor,
            id="test.check",
            expected_revision=1,
            cases=[{"action": "edit", "args": {}, "expect_result": {}, "expect_error": "x"}],
        )
    assert not calls


def test_guest_failure_always_closes_session(setup):
    gateway, actor, calls = setup
    result = check_package(
        gateway,
        actor,
        id="test.check",
        expected_revision=1,
        cases=[{"action": "edit", "args": {"error": True}}],
    )
    assert not result["passed"] and "intentional refusal" in result["cases"][0]["error"]
    assert calls[-1] == "stop"
