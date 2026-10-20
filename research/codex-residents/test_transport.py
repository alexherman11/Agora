"""Protocol boundaries that protect real desk actions and existing conversations."""

import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from codex_resident import receive
from prepare_house import HOUSE
from setup_corners import made


def test_creation_receipt_uses_new_thing_not_echoed_parent():
    receipt = (
        'ok create f185 kind=surface title="Rowan\'s corner" [e3933] → created f1603\n now: f185'
    )
    assert made(receipt, "f") == "f1603"


def event(method, data):
    return SimpleNamespace(method=method, payload=SimpleNamespace(params=data))


def test_completed_text_is_once_and_in_order():
    client = Mock()
    client.next_turn_notification.side_effect = [
        event("item/agentMessage/delta", {"delta": "> do create"}),
        event("item/completed", {"item": {"id": "m1", "type": "agentMessage", "text": "> look"}}),
        event("item/completed", {"item": {"id": "m1", "type": "agentMessage", "text": "> look"}}),
        event("item/completed", {"item": {"id": "m2", "type": "agentMessage", "text": "> rest"}}),
        event("turn/completed", {"turn": {"status": "completed"}}),
    ]
    output = []
    assert receive(client, "t", output.append)
    assert [e["result"] for e in output if e["type"] == "result"] == ["> look\n> rest"]
    assert len([e for e in output if e["type"] == "assistant"]) == 1


@pytest.mark.parametrize("status", ["failed", "interrupted"])
def test_failed_or_interrupted_turn_cannot_apply_partial_commands(status):
    client = Mock()
    client.next_turn_notification.side_effect = [
        event(
            "item/completed",
            {"item": {"id": "m1", "type": "agentMessage", "text": "> do remove f1"}},
        ),
        event("turn/completed", {"turn": {"status": status, "error": {"message": "stopped"}}}),
    ]
    output = []
    assert not receive(client, "t", output.append)
    assert not any(e["type"] == "assistant" for e in output)
    assert output[-1]["is_error"] is True


def test_house_hook_routes_only_new_provider_and_preserves_claude():
    sys.path.insert(0, str(HOUSE.parent))
    module = types.ModuleType("candidate_house")
    module.__file__ = str(HOUSE)
    # Read/import the existing house, without running it or touching any world.
    exec(compile(HOUSE.read_text(encoding="utf-8"), str(HOUSE), "exec"), module.__dict__)
    sys.path.insert(0, str(HOUSE.parents[2] / "window-lab"))
    from agora_tmp import directory
    tmp_path = Path(directory("transport-charter-test-"))
    from roomworld import build
    desk, _ = build(say=False)
    world = desk.world
    props = {"provider": "codex", "reasoning": "medium"}
    host = SimpleNamespace(
        dir=tmp_path, world="transport-inmemory",
        fake=None,
        claude="claude.exe",
        load=lambda: world,
        act=lambda *a, **k: "",  # charter receipt only; no native world act under test here
    )
    world.nodes["f_test"] = {"props": props}
    resident = module.Resident(host, "f_test")
    with (
        patch.object(module.subprocess, "Popen") as popen,
        patch.object(module.threading, "Thread"),
    ):
        popen.return_value.pid = 12345
        resident.start("gpt-6-astra")
        cmd = popen.call_args.args[0]
        assert Path(cmd[1]).name == "codex_resident.py"
        assert cmd[cmd.index("--reasoning") + 1] == "medium"
        assert "--charter-file" in cmd
        resident.state["session"] = "codex-thread"
        resident.start("gpt-6-astra")
        assert popen.call_args.args[0][-2:] == ["--resume", "codex-thread"]
        props.clear()
        with pytest.raises(ValueError, match="saved conversation belongs to codex"):
            resident.start("claude-opus-5-5")
        legacy = module.Resident(host, "f_legacy")
        legacy.state["session"] = "claude-session"
        legacy.start("claude-opus-5-5")
        cmd = popen.call_args.args[0]
        assert cmd[0] == "claude.exe" and cmd[-2:] == ["--resume", "claude-session"]
        assert "charter: not read: note missing" in cmd[cmd.index("--system-prompt") + 1]
        assert cmd[cmd.index("--tools") + 1] == ""
