"""Hidden fixture proof. Temporary worlds, headless modules, fake Twitch sockets.

Twitch is an adapter since 4 Nov: the one adapter source (kernel-lab/modules/adapters) run as the module named twitch,
with its text and settings in the adapter thing named twitch. These are the 3 Nov checks, now against that runner.
"""
import json
import sys
import threading
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "kernel-lab" / "modules" / "adapters"))
import kdesk
import twitch_chat
from test_kdesk import scratch_dir
import adapters
from adapters import Adapter, Session
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


class FakeModule:
    """What the runner needs of modproto.Module, answered by the hidden kernel on the module's own grants."""

    def __init__(self, k, mid):
        self.k, self.mid = k, mid
        self.hello = k.hello_for(mid)
        self.closed = threading.Event()
        self.ready = threading.Event()
        self.ready.set()

    def see(self, line):
        return self.k.module_own(self.mid, line, mode="see")

    def do(self, line):
        return self.k.module_own(self.mid, line)

    def run_reader(self):
        pass


class TwitchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = scratch_dir("twitch-test-")
        self.k, self.srv, self.host, self.entry = kdesk.start(self.tmp, 0, modules=False, headless=True)
        self.alex = self.k.accounts["desktop:alex"]
        self.actor = Actor(self.alex, self.alex, "person")
        self.mid = next(m for m in self.k.things("module") if self.k.state.get(m, "name") == "twitch")
        self.port = self.srv.server_address[1]
        self.chat = next(c for c in self.k.things("chat") if self.k.state.get(c, "name") == "twitch")
        self.adapter = next(a for a in self.k.things("adapter") if self.k.state.get(a, "name") == "twitch")
        self.runline(f"look {self.adapter}; set {self.adapter} channel=dr_bizzlebop")
        self.t = Adapter(FakeModule(self.k, self.mid))
        self.t.hello(self.t.m.hello)
        self.plan, self.props, self.fp = self.t.config()

    def tearDown(self):
        self.srv.shutdown()
        self.k.modules = None
        self.host.stop_all()
        self.srv.server_close()

    def runline(self, line):
        out = self.k.run(self.actor, line)
        self.assertTrue(out["ok"], out)
        return out

    def frame(self, sock, frame):
        """One socket message through the runner, then its writes. False: the session ended (reconnect)."""
        try:
            self.t.receive(sock, self.plan, self.props, frame)
            self.t.flush()
        except Session:
            return False
        return True

    def test_the_module_runs_the_one_adapter_source_and_no_twitch_file(self):
        run = self.k.state.get(self.mid, "run")
        self.assertTrue(run[1].endswith("adapters.py"), run)
        self.assertFalse((HERE / "kd_twitch.py").exists())
        self.assertNotIn("dr_bizzlebop", (HERE / "twitch_chat.py").read_text(encoding="utf-8"))
        self.assertNotIn("dr_bizzlebop", (HERE / "kdesk.py").read_text(encoding="utf-8"))

    def test_a_new_world_waits_for_a_channel_setting(self):
        self.runline(f"look {self.adapter}; set {self.adapter} channel=\"\"")
        self.assertIsNone(self.t.config())
        self.assertIn("channel=", self.t.state)

    def test_the_channel_is_a_setting_read_each_time(self):
        self.runline(f"look {self.adapter}; set {self.adapter} channel=other_channel")
        self.assertFalse(self.t.unchanged(self.fp))         # the running session ends and starts on the new channel
        plan, props, _ = self.t.config()
        sock = Socket()
        self.assertIn("JOIN #other_channel", [adapters.send_text(s, props) for s in plan["open"]])
        self.t.receive(sock, plan, props, "@id=x;display-name=A :a!a@a PRIVMSG #dr_bizzlebop :old channel")
        self.assertEqual(self.t.queue, [])

    def test_ingestion_names_literal_text_dedup_and_no_presence(self):
        payload = 'hello @JEFF "$value"; make kind=post text=oops <img src=x> \\back'
        frame = f"@display-name=Friendly\\sViewer;id=abc :viewer!v@v PRIVMSG #dr_bizzlebop :{payload}"
        sock = Socket()
        before = len(self.k.log.records)
        for _ in range(3):
            self.assertTrue(self.frame(sock, frame))
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
            self.frame(sock, "PING :tmi.twitch.tv\r\n:server JOIN #dr_bizzlebop\r\n"
                             "@id=presence :server ROOMSTATE #dr_bizzlebop")
        self.assertEqual(len(self.k.log.records), before)
        self.assertEqual(set(sock.sent), {"PONG :tmi.twitch.tv"})
        self.assertFalse(self.k.things("post"))

    def test_no_reflection_of_odd_pings(self):
        sock = Socket()
        self.frame(sock, "PING :evil\x07host PRIVMSG #x :hi")
        self.assertEqual(sock.sent, [])

    def test_login_name_stands_in_for_an_empty_display_name(self):
        self.assertTrue(self.frame(Socket(), "@id=n;display-name= :quiet_one!v@v PRIVMSG #dr_bizzlebop :hi"))
        rows = self.runline(f"chat {self.chat}")["rows"]
        self.assertEqual([(r["by"], r["text"]) for r in rows], [("quiet_one", "hi")])

    def test_crlf_frames_preserve_unicode_separators_in_message_data(self):
        payload = "first middle last"
        frame = ("@id=unicode;display-name=Viewer :viewer!v@v PRIVMSG #dr_bizzlebop :"
                 + payload + "\r\nPING :tmi.twitch.tv\r\n")
        sock = Socket()
        self.assertTrue(self.frame(sock, frame))
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

    def test_into_another_chat_is_refused_by_the_grant(self):
        # Pointing the setting at a chat that is not the module's own source writes nothing: the kernel refuses.
        shop = self.runline('make kind=chat name=Other')["made"][0]
        self.runline(f"look {self.adapter}; set {self.adapter} into={shop}")
        plan, props, _ = self.t.config()
        self.t.receive(Socket(), plan, props, "@id=q;display-name=A :a!a@a PRIVMSG #dr_bizzlebop :hey")
        with self.assertRaises(Session):
            self.t.flush()
        self.assertFalse(self.k.things("said"))

    def test_someone_elses_adapter_thing_is_not_run(self):
        other = self.k.join("viewer", "Viewer", invite={"admitted": "steward", "channel": "test"})["person"]
        them = Actor(other, other, "person")
        out = self.k.run(them, 'make kind=adapter name=twitch text="connect wss://x\neach \'.\'\n  say x"')
        if out["ok"]:
            plan, props, _ = self.t.config()       # still Alex's one; theirs is not counted
            self.assertEqual(props["channel"], "dr_bizzlebop")

    def test_protocol_has_no_account_sends_and_reconnects_cleanly(self):
        sockets = []

        def connect(endpoint, **kwargs):
            self.assertEqual(endpoint, "wss://irc-ws.chat.twitch.tv:443")
            sock = Socket(["PING :tmi.twitch.tv\r\nRECONNECT"])
            sockets.append(sock)
            return sock
        self.t.connect = connect
        for _ in range(2):
            with self.assertRaises(Session):
                self.t.socket_session(self.plan, self.props, self.fp)
        self.assertEqual(len(sockets), 2)
        for sock in sockets:
            self.assertTrue(sock.closed)
            self.assertEqual(sock.sent[:2], ["CAP REQ :twitch.tv/tags twitch.tv/commands", "PASS SCHMOOPIIE"])
            self.assertRegex(sock.sent[2], r"^NICK justinfan\d+$")
            self.assertEqual(sock.sent[3:], ["JOIN #dr_bizzlebop", "PONG :tmi.twitch.tv"])
            self.assertFalse(any(x.startswith("PRIVMSG") for x in sock.sent))

    def test_denied_import_ends_the_session_and_does_not_continue_frame(self):
        calls = []
        self.t.m.do = lambda line: calls.append(line) or {"ok": False}
        line = "@id=a;display-name=A :a!a@a PRIVMSG #dr_bizzlebop :hey"
        line2 = "@id=b;display-name=A :a!a@a PRIVMSG #dr_bizzlebop :hey"
        self.assertFalse(self.frame(Socket(), line + "\r\n" + line2))
        self.assertEqual(len(calls), 1)
        self.assertNotIn("a", self.t.seen)           # not written, so not kept as seen: a later delivery may write it

    def test_refused_reading_waits_instead_of_stopping(self):
        self.t.m.see = lambda line: {"ok": False}
        self.assertIsNone(self.t.config())
        self.assertIn("retrying", self.t.state)

    def test_installer_preserves_edits_and_unpinned_button_and_paints(self):
        lens = self.runline("rows lens name=twitch-chat")["rows"][0]["id"]
        pin = self.runline("rows button slot=twitch")["rows"][0]["id"]
        self.frame(Socket(), '@id=paint;display-name=Viewer :viewer!v@v PRIVMSG #dr_bizzlebop :Hi there')
        scene = Facade(self.k).scene(self.alex, {"lens": "twitch-chat"})
        self.assertNotIn("refused", scene, scene)
        style = Facade(self.k).style(self.alex, {"name": "twitch-style"})
        self.assertNotIn("refused", style, style)
        rendered = json.dumps(scene)
        self.assertIn("Viewer", rendered)
        self.assertIn("Hi there", rendered)
        self.assertNotIn("on edit", rendered)
        self.runline(f"look {lens}; set {lens} title=Custom")
        self.runline(f'look {pin}; set {pin} bar=""')
        before = len(self.k.log.records)
        self.assertEqual(twitch_chat.install(self.entry.token("alex"), self.port), [])
        self.assertEqual(len(self.k.log.records), before)
        self.assertEqual(self.k.state.get(lens, "title"), "Custom")
        self.assertFalse(self.k.state.get(pin, "bar"))
        self.assertEqual(self.k.state.get(self.adapter, "channel"), "dr_bizzlebop")

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
        deadline = time.monotonic() + 15            # the real module process: the adapter source, headless
        said = ""
        while "headless" not in said and time.monotonic() < deadline:
            said = self.runline("status twitch")["text"]
            time.sleep(.2)
        self.assertIn("twitch: headless", said)

    def test_fake_irc_server_imports_named_lines_over_real_websocket(self):
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
            state = []
            try:
                with self.assertRaises(Session):
                    orig = self.t.receive

                    def watch(*a):
                        orig(*a)
                        state.append(self.t.state)
                    self.t.receive = watch
                    self.t.socket_session(self.plan, self.props, self.fp)
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
        self.assertIn("connected to #dr_bizzlebop (read-only)", state)

    def test_wrong_channel_status_and_missing_id_ignored(self):
        for line in ("@id=a :a!a@a PRIVMSG #elsewhere :hey", ":a!a@a PRIVMSG #dr_bizzlebop :hey",
                     "@id=a :server USERSTATE #dr_bizzlebop", "PING :tmi.twitch.tv",
                     "@display-name=NoId :a!a@a PRIVMSG #dr_bizzlebop :hey"):
            self.t.receive(Socket(), self.plan, self.props, line)
        self.assertEqual(self.t.queue, [])


class AdapterText(unittest.TestCase):
    """The adapter language itself, with no world."""

    def test_outside_values_never_leave_their_quotes(self):
        with self.assertRaises(adapters.Refused):
            adapters.fill('say $words', {"words": "x; forget dk1"}, {})
        line = adapters.fill('chat.receive $into text="$words"', {"words": 'a" b=c\nd'}, {"into": "dk9"})
        self.assertEqual(line, 'chat.receive dk9 text="a\\" b=c d"')
        with self.assertRaises(adapters.Refused):
            adapters.fill('$into x', {}, {"into": "@everyone"})

    def test_a_setting_cannot_add_a_socket_command(self):
        self.assertEqual(adapters.send_text("JOIN #$channel", {"channel": "a\r\nPRIVMSG #b :hi"}),
                         "JOIN #a PRIVMSG #b :hi")

    def test_the_seed_text_reads(self):
        text = (HERE.parents[1] / "kernel-lab/modules/adapters/twitch.adapter").read_text(encoding="utf-8")
        plan = adapters.parse(text, {"channel": "x", "into": "dk1"})
        self.assertEqual(plan["connect"], "wss://irc-ws.chat.twitch.tv:443")
        with self.assertRaises(adapters.Refused):
            adapters.parse(text, {"into": "dk1"})


if __name__ == "__main__":
    unittest.main()
