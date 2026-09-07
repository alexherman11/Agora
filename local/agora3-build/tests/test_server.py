"""Real loopback HTTP checks for authentication, origin and host recovery separation."""

import json
import threading
import urllib.error
import urllib.request

import pytest

from agora3.server import serve


@pytest.fixture
def server(tmp_path):
    http, app = serve(tmp_path, 0)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{http.server_address[1]}", app
    http.shutdown()
    http.server_close()
    thread.join(3)


def rpc(server, method, args=None, *, token=None, origin=None, host=None):
    url, app = server
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = "Bearer " + token
    if origin:
        headers["Origin"] = origin
    if host:
        headers["Host"] = host
    request = urllib.request.Request(
        url + "/api/rpc",
        headers=headers,
        data=json.dumps({"method": method, "args": args or {}}).encode(),
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, json.load(exc)


def test_authentication_and_origin_are_enforced(server):
    _, app = server
    token = app.gateway.keep["operator"]
    assert rpc(server, "world.query")[0] == 401
    assert rpc(server, "world.query", token=token)[0] == 200
    assert rpc(server, "world.query", token=token, origin="https://foreign.example")[0] == 403
    assert rpc(server, "world.query", token=token, host="foreign.example")[0] == 403


def test_guest_cannot_recover_or_supply_identity(server):
    _, app = server
    token = app.gateway.keep["guest"]
    assert rpc(server, "host.revoke", token=token)[0] == 401
    assert rpc(server, "chat.send", {"message": "spoofed request"}, token=token)[0] == 401
    assert rpc(server, "system.status", token=token)[0] == 401
    assert app.gateway.keep["enabled"]
    code, _ = rpc(server, "world.transact", {"actor": "human", "changes": []}, token=token)
    assert code == 401


def test_revocation_blocks_existing_token_and_preserves_host_recovery(server):
    _, app = server
    operator, guest = app.gateway.keep["operator"], app.gateway.keep["guest"]
    assert rpc(server, "host.revoke", token=operator)[0] == 200
    assert rpc(server, "world.query", token=guest)[0] == 401
    assert rpc(server, "world.query", token=operator)[0] == 400
    assert rpc(server, "host.surface", token=operator)[0] == 200
    app.connect_guest = lambda: {"connected": False, "test_double": True}
    assert rpc(server, "host.resume", token=operator)[0] == 200
    assert rpc(server, "world.query", token=guest)[0] == 401
    assert rpc(server, "world.query", token=operator)[0] == 200


def test_runtime_records_and_recovery_remain_outside_authored_surface(server):
    _, app = server
    token = app.gateway.keep["operator"]
    code, result = rpc(server, "host.surface", token=token)
    assert code == 200
    assert token not in result["result"]["html"]
    assert app.gateway.keep["guest"] not in result["result"]["html"]
    code, _ = rpc(
        server,
        "world.transact",
        {
            "changes": [
                {
                    "id": "agora.installation.agora.shell",
                    "expected_revision": 1,
                    "facets": {"agora.installation": {"build": "fake"}},
                }
            ]
        },
        token=token,
    )
    assert code == 400
    assert app.gateway.world.verify()["ok"]


def test_recovery_restores_code_without_rewinding_application_data(server):
    _, app = server
    token = app.gateway.keep["operator"]
    note = app.gateway.world.get("welcome-1")
    rpc(
        server,
        "world.transact",
        {
            "changes": [
                {
                    "id": note["id"],
                    "expected_revision": note["revision"],
                    "facets": {"core.text": {"text": "Keep this newer content"}},
                }
            ]
        },
        token=token,
    )
    before = app.gateway.packages.installation("agora.shell")["revision"]
    assert rpc(server, "host.reset_shell", token=token)[0] == 200
    assert app.gateway.packages.installation("agora.shell")["revision"] == before + 1
    assert (
        app.gateway.world.get("welcome-1")["facets"]["core.text"]["text"]
        == "Keep this newer content"
    )
