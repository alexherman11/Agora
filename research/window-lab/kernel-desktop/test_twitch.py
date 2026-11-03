"""Hidden fixture proof. Temporary worlds, headless modules, fake Twitch sockets."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kdesk
import twitch_chat
from test_kdesk import scratch_dir
from kd_twitch import Twitch, parse_message
from kernel.kernel import Actor
from kernel.painter import Facade


class Socket:
    def __init__(self, frames=()):
        self.frames = iter(frames)
        self.sent = []
        self.closed = False

    def send(self, line):
        self.sent.append(line)

    def recv(self, timeout=None):
        return next(self.frames, "")

    def close(self):
        self.closed = True


class TwitchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = scratch_dir("twitch-test-")
        self.k, self.srv, self.host, self.entry = kdesk.start(self.tmp, 0, modules=False, headless=True)
        self.alex = self.k.accounts["desktop:alex"]
        self.actor = Actor(self.alex, self.alex, "person")
        self.mid = next(m for m in self.k.things("module") if self.k.state.get(m, "name") == "twitch")
        self.port = self.srv.server_address[1]
        twitch_chat.install(self.entry.token("alex"), self.port, channel="dr_bizzlebop")
        self.chat = next(c for c in self.k.things("chat") if self.k.state.get(c, "name") == "twitch")
        self.t = Twitch()
        self.t.m.hello = {"id": self.mid}
        self.t.m.do = lambda line: self.k.module_own(self.mid, line)
        self.t.m.see = lambda line: self.k.module_own(self.mid, line, mode="see")

    def tearDown(self):
        self.srv.shutdown()
        self.k.modules = None
        self.host.stop_all()
        self.srv.server_close()

    def runline(self, line):
        out = self.k.run(self.actor, line)
        self.assertTrue(out["ok"], out)
        return out

    def test_ingestion_names_literal_text_dedup_and_no_presence(self):
        payload = 'hello @JEFF "$value"; make kind=post text=oops <img src=x> \\back'
        frame = f"@display-name=Friendly\\sViewer;id=abc :viewer!v@v PRIVMSG #dr_bizzlebop :{payload}"
        sock = Socket()
        before = len(self.k.log.records)
        for _ in range(3):
            self.assertTrue(self.t.receive_frame(sock, frame, self.chat, "dr_bizzlebop"))
        rows = self.runline(f"chat {self.chat}")["rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["by"], "Friendly Viewer")
        self.assertEqual(rows[0]["text"], payload)
        self.assertEqual(rows[0]["to"], [])
        self.assertEqual(rows[0]["from"], "twitch")
        said = self.k.things("said")[0]
        self.assertFalse(self.k.state.get(said, "for"))
        self.assertFalse(self.k.state.get(said, "to"))
        happenings = [self.k.happening_for(self.alex, h) for h in self.k.happenings if said in (h.get("made") or [])]
        self.assertTrue(happenings)
        self.assertTrue(all(h.get("to") == [] for h in happenings))
        self.assertEqual(len(self.k.log.records), before + 1)
        before = len(self.k.log.records)
        for _ in range(386):
            self.t.receive_frame(sock, "PING :tmi.twitch.tv\r\n:server JOIN #dr_bizzlebop\r\n"
                                 "@id=presence :server ROOMSTATE #dr_bizzlebop", self.chat, "dr_bizzlebop")
        self.assertEqual(len(self.k.log.records), before)
        self.assertEqual(set(sock.sent), {"PONG :tmi.twitch.tv"})
        self.assertFalse(self.k.things("post"))

    def test_crlf_frames_preserve_unicode_separators_in_message_data(self):
        payload = "first\u2028middle\u2029last"
        frame = ("@id=unicode;display-name=Viewer :viewer!v@v PRIVMSG #dr_bizzlebop :"
                 + payload + "\r\nPING :tmi.twitch.tv\r\n")
        sock = Socket()
        self.assertTrue(self.t.receive_frame(sock, frame, self.chat, "dr_bizzlebop"))
        rows = self.runline(f"chat {self.chat}")["rows"]
        self.assertEqual([r["text"] for r in rows], [payload])
        self.assertEqual(sock.sent, ["PONG :tmi.twitch.tv"])

    def test_source_restriction_read_only_and_restart_dedup(self):
        line = f'chat.receive {self.chat} text=hello speaker=Viewer external_id=xyz'
        self.assertFalse(self.k.run(self.actor, line)["ok"])
        self.assertFalse(self.k.run(self.actor, f"say {self.chat} hello")["ok"])
        self.assertTrue(self.k.module_own(self.mid, line)["ok"])
        shop = self.runline('make kind=chat name=Other')["made"][0]
        self.assertFalse(self.k.module_own(self.mid, line.replace(self.chat, shop))["ok"])
        from kernel.kernel import Kernel
        replay = Kernel(self.tmp)
        before = len(replay.log.records)
        self.assertTrue(replay.module_own(self.mid, line)["ok"])
        self.assertEqual(len(replay.log.records), before)
        self.assertEqual(len(replay.things("said")), 1)

    def test_protocol_has_no_account_sends_and_reconnects_cleanly(self):
        sockets = []
        def connect(endpoint, **kwargs):
            self.assertEqual(endpoint, "wss://irc-ws.chat.twitch.tv:443")
            sock = Socket(["PING :tmi.twitch.tv\r\nRECONNECT"])
            sockets.append(sock)
            return sock
        self.t.connect = connect
        for _ in range(2):
            self.t.session((self.chat, "dr_bizzlebop"))
        self.assertEqual(len(sockets), 2)
        for sock in sockets:
            self.assertTrue(sock.closed)
            self.assertEqual(sock.sent[:2], ["CAP REQ :twitch.tv/tags twitch.tv/commands", "PASS SCHMOOPIIE"])
            self.assertRegex(sock.sent[2], r"^NICK justinfan\d+$")
            self.assertEqual(sock.sent[3:], ["JOIN #dr_bizzlebop", "PONG :tmi.twitch.tv"])
            self.assertFalse(any(x.startswith("PRIVMSG") for x in sock.sent))

    def test_denied_import_stops_and_does_not_continue_frame(self):
        calls = []
        self.t.m.do = lambda line: calls.append(line) or {"ok": False}
        line = "@id=a;display-name=A :a!a@a PRIVMSG #dr_bizzlebop :hey"
        self.assertFalse(self.t.receive_frame(Socket(), line + "\r\n" + line, self.chat, "dr_bizzlebop"))
        self.assertTrue(self.t.denied)
        self.assertEqual(len(calls), 1)

    def test_installer_preserves_edits_and_unpinned_button_and_paints(self):
        lens = self.runline("rows lens name=twitch-chat")["rows"][0]["id"]
        pin = self.runline("rows button slot=twitch")["rows"][0]["id"]
        self.t.receive_frame(Socket(), '@id=paint;display-name=Viewer :viewer!v@v PRIVMSG #dr_bizzlebop :Hi there',
                             self.chat, "dr_bizzlebop")
        scene = Facade(self.k).scene(self.alex, {"lens": "twitch-chat"})
        self.assertNotIn("refused", scene, scene)
        style = Facade(self.k).style(self.alex, {"name": "twitch-style"})
        self.assertNotIn("refused", style, style)
        import json
        rendered = json.dumps(scene)
        self.assertIn("Viewer", rendered)
        self.assertIn("Hi there", rendered)
        self.assertNotIn("on edit", rendered)
        self.runline(f"look {lens}; set {lens} title=Custom")
        self.runline(f'look {pin}; set {pin} bar=""')
        before = len(self.k.log.records)
        self.assertEqual(twitch_chat.install(self.entry.token("alex"), self.port, channel="dr_bizzlebop"), [])
        self.assertEqual(len(self.k.log.records), before)
        self.assertEqual(self.k.state.get(lens, "title"), "Custom")
        self.assertFalse(self.k.state.get(pin, "bar"))

    def test_bar_button_opens_headless_window_and_reuses_it(self):
        # Only fixture modules; genesis passed --headless to every window host.
        self.k.modules = self.host
        self.host.reconcile()
        import time
        deadline = time.monotonic() + 20
        while not self.k.find_entry("window.open") and time.monotonic() < deadline:
            time.sleep(.1)
        pin = self.runline("rows button slot=twitch")["rows"][0]["id"]
        for _ in range(2):
            self.runline(f"press {pin}")
        deadline = time.monotonic() + 10
        opened = []
        while not opened and time.monotonic() < deadline:
            windows = self.runline("window.list")["rows"]
            opened = [w for w in windows if w.get("shows") == "twitch-chat"]
            if not opened:
                time.sleep(.1)
        self.assertEqual(len(opened), 1)

    def test_fake_irc_server_imports_named_lines_over_real_websocket(self):
        import threading
        from websockets.sync.server import serve
        from websockets.sync.client import connect
        received, errors = [], []

        def irc(ws):
            try:
                received.extend(ws.recv(timeout=5) for _ in range(4))
                ws.send(":tmi.twitch.tv 366 justinfan123 #dr_bizzlebop :End of /NAMES list\r\n"
                        "@id=first;display-name=FriendlyViewer :viewer!v@v PRIVMSG #dr_bizzlebop :hello @JEFF\r\n"
                        "@id=second;display-name=OtherViewer :other!v@v PRIVMSG #dr_bizzlebop :nice stream\r\n"
                        "@id=first;display-name=FriendlyViewer :viewer!v@v PRIVMSG #dr_bizzlebop :hello @JEFF\r\n"
                        "PING :tmi.twitch.tv\r\n")
                received.append(ws.recv(timeout=5))
                ws.send("RECONNECT\r\n")
            except Exception as exc:
                errors.append(repr(exc))

        with serve(irc, "127.0.0.1", 0) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = server.socket.getsockname()[1]
            self.t.connect = lambda endpoint, **kw: connect(f"ws://127.0.0.1:{port}", **kw)
            try:
                self.t.session((self.chat, "dr_bizzlebop"))
            finally:
                server.shutdown()
                thread.join(5)
        self.assertEqual(errors, [])
        self.assertEqual(received[:2], ["CAP REQ :twitch.tv/tags twitch.tv/commands", "PASS SCHMOOPIIE"])
        self.assertRegex(received[2], r"^NICK justinfan\d+$")
        self.assertEqual(received[3:], ["JOIN #dr_bizzlebop", "PONG :tmi.twitch.tv"])
        rows = self.runline(f"chat {self.chat}")["rows"]
        self.assertEqual([(r["by"], r["text"]) for r in rows],
                         [("FriendlyViewer", "hello @JEFF"), ("OtherViewer", "nice stream")])
        self.assertTrue(all(r["to"] == [] and r["from"] == "twitch" for r in rows))
        self.assertEqual(self.t.state, "connected to #dr_bizzlebop (read-only)")

    def test_wrong_channel_status_and_missing_id_ignored(self):
        for line in ("@id=a :a!a@a PRIVMSG #elsewhere :hey", ":a!a@a PRIVMSG #dr_bizzlebop :hey",
                     "@id=a :server USERSTATE #dr_bizzlebop", "PING :tmi.twitch.tv"):
            self.assertIsNone(parse_message(line, "dr_bizzlebop"))



if __name__ == "__main__":
    unittest.main()
