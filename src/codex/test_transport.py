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
    sys.path.insert(0, str(HOUSE.parents[2] / "desktop"))
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
        act=lambda *a, **k: "fixture charter receipt",  # no native world act under test
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


@pytest.mark.parametrize(
    "model,catalog", [("gpt-6.1-sol", "worker-model-catalog.json"),
                      ("gpt-6-astra", "model-catalog.json")],
)
def test_resident_model_selection_keeps_the_no_tools_boundary(tmp_path, model, catalog):
    """A charter landing must not drop the running resident's Sol support."""
    import json
    from codex_resident import build_config

    config = build_config(tmp_path, "fixture.exe", tmp_path, model=model)
    selected = next(x.split("=", 1)[1] for x in config.config_overrides
                    if x.startswith("model_catalog_json="))
    assert Path(json.loads(selected)).name == catalog
    assert "features.shell_tool=false" in config.config_overrides
    assert "features.multi_agent=false" in config.config_overrides
    assert config.env["OPENAI_API_KEY"] == config.env["CODEX_API_KEY"] == ""


def test_worker_and_resident_share_a_fail_closed_subscription_guard():
    """Exercise the real import edge that broke when only one adapter was parked."""
    import codex_worker
    from codex_resident import require_subscription

    assert codex_worker.require_subscription is require_subscription
    client = Mock()
    client.account_read.return_value.model_dump.return_value = {"account": {"type": "apiKey"}}
    with pytest.raises(RuntimeError, match="subscription"):
        require_subscription(client)
    client.account_read.assert_called_once_with({"refreshToken": False})
    client.turn_start.assert_not_called()
    client.account_login_start.assert_not_called()


def test_kernel_resident_uses_supported_discovery_with_no_native_tools(tmp_path):
    from codex_resident import build_config
    opts=build_config(tmp_path,'fixture.exe',tmp_path,door=True).config_overrides
    assert 'features.code_mode=true' in opts and 'features.code_mode_host=true' in opts
    for name in ('shell_tool','unified_exec','apply_patch_freeform','view_image','web_search','computer_use','multi_agent'):
        assert f'features.{name}=false' in opts
    default=build_config(tmp_path,'fixture.exe',tmp_path).config_overrides
    assert 'features.code_mode=false' in default


def test_kernel_resident_exposes_only_existing_three_door_tools(tmp_path):
    import json
    from codex_resident import kernel_door_server
    path=tmp_path/'mcp.json'
    path.write_text(json.dumps({'mcpServers':{'agora':{'command':'fixture','args':[]}}}))
    server=kernel_door_server(path)
    assert server['enabled_tools']==['see','do','lines']
    assert set(server['tools'])=={'see','do','lines'}
    path.write_text(json.dumps({'mcpServers':{'agora':{},'unapproved':{}}}))
    with pytest.raises(ValueError,match='only the Agora'):kernel_door_server(path)
