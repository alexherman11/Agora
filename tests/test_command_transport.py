"""Windows argument-length regression; real guest preflight is recorded separately."""

from unittest.mock import Mock

from agora3.guest import Guest


def test_large_command_uses_stdin_and_keeps_literal_text(tmp_path, monkeypatch):
    guest = Guest(tmp_path / "unused.json")
    transport = Mock(return_value={"exit_code": 0, "stdout": "ok"})
    monkeypatch.setattr(guest, "_ssh", transport)
    command = "printf '%s' '$(literal) `literal` café'\n#" + "x" * 44000
    assert guest.execute(command)["stdout"] == "ok"
    runner, timeout, payload = transport.call_args.args
    assert len(runner) < 500 and command not in runner
    assert payload == command and timeout == 30
    assert "execv" in runner and "sys.stdin.read" in runner


def test_action_payload_transport_is_unchanged(tmp_path, monkeypatch):
    guest = Guest(tmp_path / "unused.json")
    transport = Mock(return_value={"exit_code": 0, "stdout": '{"ok": true}', "truncated": False})
    monkeypatch.setattr(guest, "_ssh", transport)
    assert guest.run({"a.py": 'def main(a,c): return {"ok":True}'}, "a.py:main", {}, {}) == {
        "ok": True
    }
    import json

    payload = json.loads(transport.call_args.args[2])
    assert payload["entry"] == "a.py:main" and payload["context"] == {}
