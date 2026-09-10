import json
import threading
import urllib.error
import urllib.request
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from agora3.bridge import NativeBridge, _HTTPServer, handler_for
from agora3.gateway import Gateway
from agora3.guest import GuestError


@pytest.fixture
def listener(tmp_path):
    gateway = Gateway(tmp_path)
    bridge = NativeBridge(gateway)
    bridge.generation = gateway.keep["generation"]
    bridge.server = _HTTPServer(("127.0.0.1", 0), handler_for(bridge))
    bridge.thread = threading.Thread(target=bridge.server.serve_forever, daemon=True)
    bridge.thread.start()
    try:
        yield bridge
    finally:
        bridge.close()


def call(bridge, name, args=None, token=None, path="/rpc", origin=None):
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = "Bearer " + token
    if origin:
        headers["Origin"] = origin
    request = urllib.request.Request(
        f"http://127.0.0.1:{bridge.server.server_address[1]}{path}",
        data=json.dumps({"name": name, "args": args or {}}).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, json.load(exc)


def test_guest_token_can_mutate_through_the_gateway(listener):
    status, result = call(
        listener,
        "world.transact",
        {
            "changes": [
                {
                    "id": "native-note",
                    "expected_revision": 0,
                    "facets": {"core.text": {"text": "hi"}},
                },
            ]
        },
        listener.gateway.keep["guest"],
    )
    assert status == 200
    assert result["result"]["items"][0]["written_by"] == "guest"
    assert listener.gateway.world.verify()["ok"] is True


@pytest.mark.parametrize("name", ["host.revoke", "chat.send", "system.shutdown"])
def test_protected_routes_never_dispatched(listener, name, monkeypatch):
    monkeypatch.setattr(listener.gateway, "describe", lambda: [{"name": name}])
    dispatch = Mock()
    monkeypatch.setattr(listener.gateway, "dispatch", dispatch)
    status, result = call(listener, name, token=listener.gateway.keep["guest"])
    assert status == 400
    assert "Protected host" in result["error"]
    dispatch.assert_not_called()


def test_no_token_or_operator_token_cannot_use_guest_listener(listener):
    for token in (None, "wrong", listener.gateway.keep["operator"]):
        status, _ = call(listener, "world.query", token=token)
        assert status == 400
    assert listener.gateway.world.query()["items"] == []


def test_revoke_invalidates_bridge_and_resume_requires_reconnect(listener):
    token = listener.gateway.keep["guest"]
    listener.gateway.revoke()
    assert call(listener, "world.query", token=token)[0] == 400
    listener.gateway.resume()
    token = listener.gateway.keep["guest"]
    status, result = call(listener, "world.query", token=token)
    assert status == 400
    assert "Reconnect" in result["error"]


def test_listener_rejects_browser_origin_and_other_paths(listener):
    token = listener.gateway.keep["guest"]
    assert call(listener, "world.query", token=token, origin="https://example.org")[0] == 400
    assert call(listener, "world.query", token=token, path="/host/recovery")[0] == 400


def test_listener_caps_native_response(listener, monkeypatch):
    monkeypatch.setattr(listener.gateway, "dispatch", lambda *args: {"large": "x" * 4_000_001})
    status, result = call(listener, "world.query", token=listener.gateway.keep["guest"])
    assert status == 413
    assert "smaller queries" in result["error"]


def test_bridge_requires_separate_candidate_configuration():
    with pytest.raises(GuestError, match="separate candidate yard"):
        NativeBridge(SimpleNamespace(guest=Mock())).start()


def test_bridge_refuses_yard_pointing_at_live_machine():
    live = Mock(_config=Mock(return_value={"vm_id": "same"}))
    yard = Mock(_configured=Mock(return_value=(live, "snapshot")))
    with pytest.raises(GuestError, match="distinct VMs"):
        NativeBridge(SimpleNamespace(guest=live, yard=yard)).start()
