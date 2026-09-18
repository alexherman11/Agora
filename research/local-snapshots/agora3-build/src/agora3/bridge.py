"""A narrow native RPC listener reached by the live guest through pinned SSH.
Never expose host recovery, model credentials or this bridge to the candidate VM.
"""

import json
import os
import shlex
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler

from agora3.guest import GuestError
from agora3.http_transport import BoundedHTTPServer as _HTTPServer
from agora3.world import Refusal

GUEST_PORT = 18790
MAX_REQUEST = 4_000_000
MAX_RESPONSE = 4_000_000
_active_lock = threading.RLock()
_active = None

CLIENT = '''"""Native operations from Agora's credentialed live Linux workspace."""
import json
import urllib.error
import urllib.request

def call(name, args=None):
    with open("/run/agora/config.json", encoding="utf-8") as handle:
        config = json.load(handle)
    request = urllib.request.Request(
        config["url"],
        data=json.dumps({"name": name, "args": args or {}}).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + config["token"]},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        result = json.load(exc)
    if "error" in result:
        raise RuntimeError(result["error"])
    return result["result"]
'''

PROVISION = """import json, os, pathlib, sys, sysconfig
value = json.load(sys.stdin)
folder = pathlib.Path("/run/agora")
folder.mkdir(mode=0o700, exist_ok=True)
folder.chmod(0o700)
config = folder / "config.json"
config.write_text(json.dumps(value["config"]), encoding="utf-8")
config.chmod(0o600)
source = pathlib.Path("/opt/agora/agora_native.py")
source.parent.mkdir(parents=True, exist_ok=True)
source.write_text(value["client"], encoding="utf-8")
site = pathlib.Path(sysconfig.get_path("purelib"))
site.mkdir(parents=True, exist_ok=True)
(site / "agora-native.pth").write_text("/opt/agora\\n", encoding="utf-8")
print("native-client-installed")
"""


def handler_for(bridge):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _reply(self, status, value):
            body = bytearray()
            for chunk in json.JSONEncoder(allow_nan=False, separators=(",", ":")).iterencode(value):
                data = chunk.encode("utf-8")
                if len(body) + len(data) > MAX_RESPONSE:
                    status = 413
                    body = b'{"error":"Native response exceeds 4 MB; use smaller queries."}'
                    break
                body.extend(data)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            try:
                if self.path != "/rpc" or self.headers.get("Origin"):
                    raise Refusal("Only the guest native RPC endpoint is available.")
                length = int(self.headers.get("Content-Length", "0"))
                if not 1 <= length <= MAX_REQUEST:
                    raise Refusal("Native RPC requests must contain at most 4 MB of JSON.")
                auth = self.headers.get("Authorization", "")
                if not auth.startswith("Bearer "):
                    raise Refusal("A current guest session is required.")
                actor = bridge.gateway.authenticate(auth[7:], name="guest")
                if actor.generation != bridge.generation:
                    raise Refusal(
                        "Reconnect the native bridge after replacing development authority."
                    )
                request = json.loads(self.rfile.read(length))
                if not isinstance(request, dict) or set(request) != {"name", "args"}:
                    raise Refusal("Native RPC requires exactly name and args.")
                name = request["name"]
                allowed = {item["name"] for item in bridge.gateway.describe()}
                if not isinstance(name, str) or name not in allowed:
                    raise Refusal("This listener exposes native operations only.")
                if name.startswith(("host.", "chat.", "system.")):
                    raise Refusal("Protected host operations are not guest-native operations.")
                result = bridge.gateway.dispatch(actor, name, request["args"])
                bridge.gateway.check_authority(actor)
                self._reply(200, {"result": result})
            except (Refusal, GuestError, ValueError, KeyError, TypeError) as exc:
                self._reply(400, {"error": str(exc)})

    return Handler


class NativeBridge:
    def __init__(self, gateway):
        self.gateway = gateway
        self.server = None
        self.thread = None
        self.tunnel = None
        self.generation = None

    def status(self):
        running = self.tunnel is not None and self.tunnel.poll() is None
        keep = self.gateway.keep
        authorized = keep["enabled"] and keep["generation"] == self.generation
        return {
            "connected": running and authorized,
            "transport_running": running,
            "guest_port": GUEST_PORT,
            "generation": self.generation,
            "scope": "native development; no protected host or model endpoints",
        }

    def start(self):
        global _active
        with _active_lock:
            if _active is not None and _active is not self:
                raise GuestError("Only one live native bridge may run in this host process.")
            if self.tunnel is not None:
                self.close()
            yard = getattr(self.gateway, "yard", None)
            if yard is None:
                raise GuestError(
                    "A separate candidate yard must be configured before live native access."
                )
            yard_machine, _ = yard._configured()
            guest = self.gateway.guest
            config = guest._config()
            if yard_machine._config()["vm_id"] == config["vm_id"]:
                raise GuestError("The live guest and candidate yard must be distinct VMs.")
            guest._isolation(guest._owned(config))
            keep = self.gateway.keep
            actor = self.gateway.authenticate(keep["guest"], name="guest")
            self.gateway.check_authority(actor)
            self.generation = actor.generation
            self.server = _HTTPServer(("127.0.0.1", 0), handler_for(self))
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            _active = self
            try:
                port = self.server.server_address[1]
                self.tunnel = subprocess.Popen(
                    [
                        "ssh",
                        "-F",
                        "none",
                        "-N",
                        "-T",
                        "-p",
                        str(config["ssh_port"]),
                        "-i",
                        config["identity_file"],
                        "-o",
                        "BatchMode=yes",
                        "-o",
                        "IdentitiesOnly=yes",
                        "-o",
                        "StrictHostKeyChecking=yes",
                        "-o",
                        f"UserKnownHostsFile={config['known_hosts']}",
                        "-o",
                        "GlobalKnownHostsFile=none",
                        "-o",
                        "ForwardAgent=no",
                        "-o",
                        "ExitOnForwardFailure=yes",
                        "-o",
                        "ConnectTimeout=5",
                        "-o",
                        "ServerAliveInterval=15",
                        "-o",
                        "ServerAliveCountMax=2",
                        "-R",
                        f"127.0.0.1:{GUEST_PORT}:127.0.0.1:{port}",
                        "jeff@127.0.0.1",
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
                payload = json.dumps(
                    {
                        "config": {
                            "url": f"http://127.0.0.1:{GUEST_PORT}/rpc",
                            "token": keep["guest"],
                        },
                        "client": CLIENT,
                    }
                )
                provisioned = guest._ssh("python3 -c " + shlex.quote(PROVISION), 15, payload)
                if provisioned["exit_code"]:
                    raise GuestError("Could not provision the live guest native client.")
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    if self.tunnel.poll() is not None:
                        raise GuestError("Pinned SSH reverse forwarding could not be established.")
                    result = guest.execute(
                        "python3 -c "
                        + shlex.quote(
                            "import agora_native; agora_native.call('tools.list'); print('ready')"
                        ),
                        timeout=5,
                    )
                    if result["exit_code"] == 0 and result["stdout"].strip() == "ready":
                        self.gateway.check_authority(actor)
                        return self.status()
                    time.sleep(0.5)
                raise GuestError("The live guest could not reach the native bridge.")
            except BaseException:
                self.close()
                raise

    def close(self):
        global _active
        with _active_lock:
            if self.tunnel is not None:
                self.tunnel.terminate()
                try:
                    self.tunnel.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.tunnel.kill()
                    self.tunnel.wait(timeout=5)
                self.tunnel = None
            if self.server is not None:
                self.server.shutdown()
                self.server.server_close()
                self.server = None
            if self.thread is not None:
                self.thread.join(timeout=5)
                self.thread = None
            if _active is self:
                _active = None
