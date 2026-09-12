"""GPT Live WebRTC negotiation and its trusted server event connection.
Never expose the project key or retry a request that might have created a session.
"""

import json
import threading
import urllib.error
import urllib.request
from urllib.parse import quote

from websockets.sync.client import connect

from agora3.world import Refusal

API = "https://api.openai.com/v1/live/sessions"


def post(key, url, body):
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = response.read(1_000_000)
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        descriptions = {
            401: "The voice API key was rejected.",
            403: "This API project does not have permission to use GPT Live 1.",
            429: "The voice API project reached its usage or rate limit.",
        }
        raise Refusal(
            descriptions.get(
                exc.code, f"GPT Live could not complete the request (HTTP {exc.code})."
            )
        ) from None
    except Exception:
        raise Refusal(
            "The GPT Live connection failed. Check the server's network connection."
        ) from None


class LiveConnection:
    def __init__(self, key, configuration, sdp):
        result = post(
            key, API, {"session": configuration, "transport": {"type": "webrtc", "sdp": sdp}}
        )
        try:
            self.id = result["session"]["id"]
            self.sdp = result["transport"]["sdp"]
            if not isinstance(self.id, str) or not isinstance(self.sdp, str):
                raise ValueError("Invalid session response")
        except (KeyError, TypeError, ValueError):
            raise Refusal("GPT Live returned an incomplete connection response.") from None
        self._key = key
        self._lock = threading.Lock()
        try:
            self.socket = connect(
                "wss://api.openai.com/v1/live/sessions/" + quote(self.id, safe="") + "/attach",
                additional_headers={"Authorization": "Bearer " + key},
                open_timeout=15,
                close_timeout=3,
                max_size=2_000_000,
            )
        except Exception:
            self.hangup()
            raise Refusal("Could not attach JEFF to voice; call closure was requested.") from None

    def receive(self, timeout=0.5):
        return json.loads(self.socket.recv(timeout=timeout))

    def send(self, event):
        with self._lock:
            self.socket.send(json.dumps(event))

    def hangup(self):
        try:
            post(self._key, API + "/" + quote(self.id, safe="") + "/hangup", {})
        except Refusal:
            pass

    def disconnect(self):
        self.socket.close()
        self._key = ""
