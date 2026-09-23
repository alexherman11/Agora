"""Host-boundary tests use fake transport; live VM checks are separately recorded."""

import json
from unittest.mock import Mock

import pytest

from agora3.guest import Guest, GuestError, validate_sources

VM_ID = "70564d95-70e8-454a-8bf9-28ae8dffe3bc"
INFO = "\n".join(
    [
        'name="Agora3-test"',
        'VMState="running"',
        'clipboard="disabled"',
        'draganddrop="disabled"',
        'nic1="nat"',
    ]
)


@pytest.fixture
def guest(tmp_path, monkeypatch):
    (tmp_path / "key").write_text("fixture key", encoding="utf-8")
    (tmp_path / "known_hosts").write_text(
        "[127.0.0.1]:22333 ssh-ed25519 fixture-host-key\n", encoding="utf-8"
    )
    config = {
        "backend": "virtualbox",
        "vm_id": VM_ID,
        "ssh_host": "127.0.0.1",
        "ssh_port": 22333,
        "ssh_user": "jeff",
        "identity_file": "key",
        "known_hosts": "known_hosts",
    }
    path = tmp_path / "machine.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    machine = Guest(path)
    monkeypatch.setattr(
        machine, "_vbox", lambda *args: "Value: true" if args[0] == "getextradata" else INFO
    )
    return machine


def test_missing_guest_never_falls_back_to_host(tmp_path, monkeypatch):
    process = Mock()
    monkeypatch.setattr("agora3.guest._process", process)
    machine = Guest(tmp_path / "missing.json")
    assert machine.status()["available"] is False
    with pytest.raises(GuestError, match="configuration"):
        machine.execute("touch host-file")
    process.assert_not_called()


@pytest.mark.parametrize(
    "field,value",
    [
        ("backend", "host"),
        ("vm_id", "Debian 13"),
        ("ssh_host", "example.org"),
        ("ssh_user", "-oProxyCommand=bad"),
        ("ssh_port", "22 -F other"),
    ],
)
def test_invalid_configuration_is_rejected(guest, field, value):
    config = json.loads(guest.config_path.read_text())
    config[field] = value
    guest.config_path.write_text(json.dumps(config))
    assert guest.status()["available"] is False


def test_lifecycle_refuses_unowned_vm(guest, monkeypatch):
    calls = []
    monkeypatch.setattr(guest, "_vbox", lambda *args: calls.append(args) or "No value set!")
    with pytest.raises(GuestError, match="ownership"):
        guest.stop()
    assert not any(call[0] == "controlvm" for call in calls)


def test_guest_shared_folder_prevents_execution(guest, monkeypatch):
    monkeypatch.setattr(
        guest, "_owned", lambda _: INFO + '\nSharedFolderNameMachineMapping1="host"'
    )
    with pytest.raises(GuestError, match="shared folders"):
        guest.execute("true")


def test_ssh_keeps_authored_command_off_host_shell(guest, monkeypatch):
    process = Mock(return_value={"stdout": "ok", "stderr": "", "exit_code": 0, "truncated": False})
    monkeypatch.setattr("agora3.guest._process", process)
    command = "printf '%s' 'hello; $(something)'"
    assert guest.execute(command)["stdout"] == "ok"
    args = process.call_args.args[0]
    assert args[0] == "ssh"
    assert "StrictHostKeyChecking=yes" in args
    assert "ForwardAgent=no" in args
    assert "ClearAllForwardings=yes" in args
    assert args[-2] == "jeff@127.0.0.1"
    assert "sudo -n timeout" in args[-1]


@pytest.mark.parametrize(
    "name", ["../host.py", "/host.py", "C:/host.py", "a\\host.py", "a/../x.py", "./x.py"]
)
def test_source_paths_cannot_escape_package(guest, name):
    with pytest.raises(GuestError, match="relative paths"):
        guest.run({name: ""}, name + ":main", {}, {})


def test_authored_source_only_transported_never_host_executed(guest, tmp_path, monkeypatch):
    marker = tmp_path / "must-not-exist"
    source = f"open({str(marker)!r}, 'w').write('bad')\ndef main(args, context): return 42"
    transport = Mock(
        return_value={"stdout": "42", "stderr": "", "exit_code": 0, "truncated": False}
    )
    monkeypatch.setattr(guest, "_ssh", transport)
    assert guest.run({"main.py": source}, "main.py:main", {}, {}) == 42
    assert not marker.exists()
    payload = json.loads(transport.call_args.args[2])
    assert payload["source_files"]["main.py"] == source
    assert "compile(source" in transport.call_args.args[0]


def test_invalid_guest_output_rejected(guest, monkeypatch):
    monkeypatch.setattr(
        guest,
        "_ssh",
        lambda *args: {
            "stdout": "not JSON",
            "stderr": "",
            "exit_code": 0,
            "truncated": False,
        },
    )
    with pytest.raises(GuestError, match="valid JSON"):
        guest.run({"main.py": ""}, "main.py:main", {}, {})


def test_stop_uses_configured_vm_id_even_after_integration_changes(guest, monkeypatch):
    calls = []

    def vbox(*args):
        calls.append(args)
        return (
            "Value: true"
            if args[0] == "getextradata"
            else INFO.replace('"disabled"', '"bidirectional"')
        )

    monkeypatch.setattr(guest, "_vbox", vbox)
    guest.stop()
    assert ("controlvm", VM_ID, "poweroff") in calls


def test_entry_has_to_name_package_python():
    with pytest.raises(GuestError, match="supplied Python"):
        validate_sources({"a.py": ""}, "missing.py:main")


def test_stop_does_not_depend_on_guest_ssh_keys(guest, monkeypatch):
    config = json.loads(guest.config_path.read_text())
    config["identity_file"] = "missing-key"
    guest.config_path.write_text(json.dumps(config))
    calls = []

    def vbox(*args):
        calls.append(args)
        return "Value: true" if args[0] == "getextradata" else INFO

    monkeypatch.setattr(guest, "_vbox", vbox)
    guest.stop()
    assert ("controlvm", VM_ID, "poweroff") in calls
