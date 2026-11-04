"""Read-only Twitch IRC, ported from window-lab/twitch.adapter (22 Oct).

The old adapter uses anonymous justinfan / SCHMOOPIIE, not an Alex token.
Keep that authentication: no .env values are needed, read, copied or published.
Only CAP, anonymous PASS/NICK, JOIN and PONG can go to Twitch. There is no send
word. Connection state lives in memory (twitch.now), never world facts/events.
off twitch is the normal module off switch; --headless never connects.
"""
import re
import secrets
import sys
import time
from modproto import Module

ENDPOINT = "wss://irc-ws.chat.twitch.tv:443"
CHANNEL = re.compile(r"[a-z0-9_]{1,25}")
MESSAGE = re.compile(r"^(?:@(?P<tags>\S+) )?:(?P<login>\w+)!\S+ PRIVMSG #(?P<channel>\w+) :(?P<text>.*)$")


def q(text):
    # Kernel Lines quoting; incoming words are always one literal value.
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def unescape(value):
    return re.sub(r"\\(.)", lambda m: {"s": " ", ":": ";", "r": "\r", "n": "\n",
                                      "\\": "\\"}.get(m[1], m[1]), value)


def parse_message(line, channel):
    m = MESSAGE.fullmatch(line)
    if not m or m["channel"].casefold() != channel:
        return None
    tags = dict(p.split("=", 1) for p in (m["tags"] or "").split(";") if "=" in p)
    # Twitch tags are requested at login; without an id there is no safe replay key.
    if not tags.get("id") or not m["text"]:
        return None
    return {"external_id": tags["id"], "speaker": unescape(tags.get("display-name") or m["login"]),
            "text": m["text"]}


class Twitch:
    def __init__(self, headless=False, connect=None):
        self.headless, self.connect = headless, connect
        self.socket = None
        self.state = "starting"
        self.denied = False
        self.m = Module(offer=[{
            "word": "twitch.now", "kind": "see", "takes": "", "may": "anyone",
            "help": "twitch.now: current read-only connection state, kept in memory. off twitch disconnects."
        }], on_call=self.call, on_status=lambda: self.state, on_off=self.close)

    def call(self, msg):
        return {"text": "Twitch: " + self.state, "rows": [{"kind": "twitch-live", "state": self.state}]}

    def close(self):
        if self.socket is not None:
            self.socket.close()

    def config(self):
        r = self.m.see("rows chat name=twitch")
        if not r.get("ok", True):
            # Not a lasting stop: a kernel restart refuses reads for a moment (3 Nov: Twitch stayed off after one).
            self.state = "waiting: chat reading refused; retrying"
            return None
        rows = [c for c in r.get("rows", []) if c.get("source") == self.m.hello.get("id")
                and c.get("read_only") == "yes"]
        if len(rows) != 1:
            return None
        c = rows[0]
        channel = str(c.get("channel") or "").lower().lstrip("#")
        return (c["id"], channel) if CHANNEL.fullmatch(channel) else None

    def receive_frame(self, ws, frame, chat, channel):
        # IRC separates commands with CRLF, not Unicode text line separators.
        for line in frame.split("\r\n"):
            if line.startswith("PING :"):
                # No arbitrary protocol reflection: answer only a single IRC token.
                host = line[6:]
                if re.fullmatch(r"[A-Za-z0-9.-]{1,253}", host):
                    ws.send("PONG :" + host)
                continue
            if line == "RECONNECT" or line.endswith(" RECONNECT"):
                return False
            item = parse_message(line, channel)
            if item:
                out = self.m.do(f"chat.receive {chat} " + " ".join(f"{k}={q(v)}" for k, v in item.items()))
                if not out.get("ok", False):
                    # Drop the rest of this frame and reconnect later with back-off. Lines carry their Twitch id and
                    # chat.receive skips ids it has, so a later delivery can't double a line. A kernel restart
                    # refuses for a moment, and a lasting stop then left Twitch off until someone restarted it.
                    self.state = "reconnecting: import refused or unconfirmed"
                    return False
        return True

    def session(self, config):
        if self.connect is None:
            from websockets.sync.client import connect
        else:
            connect = self.connect
        chat, channel = config
        ws = self.socket = connect(ENDPOINT, open_timeout=10, close_timeout=2)
        try:
            for line in ("CAP REQ :twitch.tv/tags twitch.tv/commands", "PASS SCHMOOPIIE",
                         "NICK justinfan" + str(secrets.randbelow(900000) + 100000), "JOIN #" + channel):
                ws.send(line)
            self.state = "joining #" + channel + " (read-only)"
            checked = time.monotonic()
            while not self.m.closed.is_set():
                if time.monotonic() - checked >= 2:
                    if self.config() != config:
                        return
                    checked = time.monotonic()
                # A short receive timeout permits off/config changes without hanging.
                try:
                    frame = ws.recv(timeout=2)
                except TimeoutError:
                    if self.config() != config:
                        return
                    continue
                if not frame or not isinstance(frame, str):
                    return
                if re.search(r"(?:^|\r\n):\S+ (?:366 \S+ #" + re.escape(channel)
                             + r"\b|ROOMSTATE #" + re.escape(channel) + r"\b)", frame):
                    self.state = "connected to #" + channel + " (read-only)"
                if not self.receive_frame(ws, frame, chat, channel):
                    return
        finally:
            ws.close()
            self.socket = None

    def run(self):
        self.m.run_reader()
        self.m.ready.wait(30)
        retry = 1
        while not self.m.closed.is_set() and not self.denied:
            if self.headless:
                self.state = "headless (no connection)"
                self.m.closed.wait(1)
                continue
            config = self.config()
            if self.denied:
                break
            if config is None:
                self.state = "waiting for Twitch chat setup"
                self.m.closed.wait(2)
                continue
            try:
                self.session(config)
                retry = 1
            except Exception:
                # Never log raw network/server exception text (or any credentials).
                self.state = "disconnected; retrying"
            if not self.denied:
                self.m.closed.wait(retry)
                retry = min(retry * 2, 30)
        self.close()
        # Keep the stopped module alive for diagnosis; House must not restart a denial.
        if self.denied:
            self.m.closed.wait()


if __name__ == "__main__":
    Twitch(headless="--headless" in sys.argv).run()
