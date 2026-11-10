"""Visitors, guests and chat lines that work like a chat app's (5 Nov 2026, for a world read by a neighbourhood
meeting's QR code). General words, tested on a fixture world:

  visitors on|off, seen-by <thing> everyone|place     signed-out readers read only what is shown to everyone
  /keep/account guest=true guest_until=<epoch>       a guest person fact, cleared on upgrade; guests share no files
  set <said> text=, forget <said>, react, pin <said>, chat ... before= pinned=yes   (kernel/chat.py)

    C:/Projects/Agora4/.venv/Scripts/python.exe -m pytest research/kernel-lab/tests/test_visitors_guests_chat.py -q
"""
import json
import secrets
import shutil
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))

from kernel.kernel import Kernel, Actor  # noqa: E402
from kernel import scratch  # noqa: E402

GENESIS = {"tag": "sb", "name": "Seabright", "steward": {"account": "google:alex", "name": "Alex"},
           "groups": [{"name": "Announcements", "open": True}, {"name": "Legal"}]}


class World(unittest.TestCase):
    genesis = GENESIS

    def setUp(self):
        self.dir = scratch.mkdtemp(prefix="kernel-visitors-")
        self.k = Kernel(self.dir, json.loads(json.dumps(self.genesis)))
        self.alex = self.k.accounts["google:alex"]
        self.maya = self.k.join("google:maya", "Maya", invite={"admitted": "steward"})["person"]
        self.sam = self.k.join("google:sam", "Sam", invite={"admitted": "steward"})["person"]
        groups = {self.k.name(g): g for g in self.k.things("group")}
        self.news, self.legal = groups["Announcements"], groups["Legal"]

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_as(self, who, line, ok=True):
        out = self.k.run(self.k.actor_for(who), line)
        self.assertEqual(out["ok"], ok, out["text"])
        return out

    def made(self, who, line):
        return self.run_as(who, line)["made"][0]


class Visitors(World):
    def test_no_visitor_until_a_steward_says_so(self):
        self.assertIsNone(self.k.visitor())
        self.run_as(self.maya, "visitors on", ok=False)              # stewards only
        self.run_as(self.alex, "visitors on")
        v = self.k.visitor()
        self.assertTrue(self.k.is_visitor(v))
        self.run_as(self.alex, "visitors off")
        self.assertIsNone(self.k.visitor())
        self.run_as(self.alex, "undo")
        self.assertEqual(self.k.visitor(), v)                        # the same visitor comes back

    def test_visitor_reads_only_what_is_shown_to_everyone(self):
        self.run_as(self.alex, "visitors on")
        v = self.k.visitor()
        plain = self.made(self.alex, 'make kind=note title="members only" in=' + self.news)
        self.assertIsNone(self.k.shown(v, plain))                    # the place's things stay the place's
        self.run_as(self.maya, f"seen-by {self.news} everyone", ok=False)   # leaders open things
        self.run_as(self.alex, f"seen-by {self.news} everyone")
        self.assertIsNotNone(self.k.shown(v, self.news))
        self.assertIsNotNone(self.k.shown(v, plain))                 # its place-wide things follow the group
        narrowed = self.made(self.alex, f"make kind=note title=draft sees=leaders in={self.news}")
        self.assertIsNone(self.k.shown(v, narrowed))                 # a narrowed thing stays narrowed
        secret = self.made(self.alex, f"make kind=note title=strategy in={self.legal}")
        self.assertIsNone(self.k.shown(v, secret))
        self.run_as(self.alex, f"seen-by {self.legal} everyone", ok=False)  # a closed group never opens this way
        loose = self.made(self.maya, "make kind=event title=Potluck")
        self.assertIsNone(self.k.shown(v, loose))
        self.run_as(self.alex, f"seen-by {loose} everyone")
        self.assertIsNotNone(self.k.shown(v, loose))
        self.assertIsNotNone(self.k.shown(self.sam, loose))         # members still see it
        chat = self.made(self.alex, "make kind=chat name=General")
        self.assertIsNone(self.k.shown(v, chat))                     # chats stay members-only
        self.run_as(self.alex, "make kind=note title=Wide sees=everyone", ok=False)   # make only narrows
        # readings through the kernel: rows and look give only the opened things
        rows = self.run_as(v, "rows note")["rows"]
        self.assertEqual([r["id"] for r in rows], [plain])
        self.run_as(self.alex, f"seen-by {self.news} place")
        self.assertIsNone(self.k.shown(v, plain))

    def test_visitor_acts_are_refused_sign_in_to_send(self):
        self.run_as(self.alex, "visitors on")
        v = self.k.visitor()
        before = len(self.k.log.records)
        out = self.run_as(v, "make kind=note title=spam", ok=False)
        self.assertIn("sign in to send", out["text"])
        chat = self.made(self.alex, "make kind=chat name=Lobby")
        self.run_as(self.alex, f"seen-by {chat} everyone")
        self.assertIn("sign in to send", self.run_as(v, f"say {chat} hi", ok=False)["text"])
        self.assertEqual(len(self.k.log.records), before + 2)        # only the leader's chat and seen-by were written
        self.assertEqual(self.run_as(v, f"chat {chat}")["rows"], [])  # but the visitor reads it
        self.assertFalse(self.k.is_member(v, self.k.place))
        # a visitor is no one to address or to put in a closed chat
        self.run_as(self.alex, f'make kind=chat name=X with="{self.k.name(v)}"', ok=False)


class Guests(World):
    def test_guest_fact_set_and_cleared_and_no_files(self):
        until = int(time.time()) + 3600
        g = self.k.join("guest:abc", "Robin", invite={"admitted": "meeting"}, guest=True, guest_until=until)
        self.assertTrue(g["guest"])
        p = g["person"]
        self.assertEqual(self.k.state.get(p, "guest"), "yes")
        self.assertEqual(self.k.state.get(p, "guest_until"), until)
        self.assertTrue(self.k.is_member(p, self.k.place))
        chat = self.made(self.alex, "make kind=chat name=General")
        line = self.made(p, f"say {chat} hello from the meeting")
        row = self.run_as(self.maya, f"chat {chat}")["rows"][-1]
        self.assertTrue(row["guest"])
        self.assertEqual(row["by_id"], p)
        self.k._local.upload_bytes = b"hello"
        try:
            out = self.run_as(p, "upload name=a.txt", ok=False)
        finally:
            self.k._local.upload_bytes = None
        self.assertIn("guests can't share files", out["text"])
        self.run_as(p, f"set {p} guest=no", ok=False)                # a person's facts are the kernel's
        # the guest makes an account: the entry service calls again with guest false
        again = self.k.join("guest:abc", "Robin", guest=False)
        self.assertFalse(again["guest"])
        self.assertIsNone(self.k.state.get(p, "guest"))
        self.assertIsNone(self.k.state.get(p, "guest_until"))
        self.assertFalse(self.run_as(self.maya, f"chat {chat}")["rows"][-1]["guest"])
        self.assertEqual(line, self.run_as(self.maya, f"chat {chat}")["rows"][-1]["id"])

    def test_an_ended_guest_pass_reads_but_does_not_act(self):
        p = self.k.join("guest:old", "Lee", invite={"admitted": "meeting"}, guest=True,
                        guest_until=int(time.time()) - 5)["person"]
        chat = self.made(self.alex, "make kind=chat name=General")
        out = self.run_as(p, f"say {chat} am I late", ok=False)
        self.assertIn("sign in to keep talking", out["text"])
        self.run_as(p, f"chat {chat}")


class ChatLines(World):
    def setUp(self):
        super().setUp()
        self.chat = self.made(self.alex, "make kind=chat name=General")

    def say(self, who, words, **kv):
        extra = "".join(f" {a}={v}" for a, v in kv.items())
        return self.made(who, f'say {self.chat} text="{words}"{extra}')

    def rows(self, who, extra=""):
        return self.run_as(who, f"chat {self.chat} {extra}".strip())["rows"]

    def test_edit_own_line_others_refused(self):
        line = self.say(self.maya, "see you at 7")
        self.rows(self.maya)
        self.run_as(self.maya, f'set {line} text="see you at 7:30"')
        row = self.rows(self.sam)[-1]
        self.assertEqual(row["text"], "see you at 7:30")
        self.assertIsInstance(row["edited"], int)
        self.rows(self.alex)
        out = self.run_as(self.alex, f'set {line} text="steward rewrite"', ok=False)   # not even a steward
        self.assertIn("only whoever said the line", out["text"])
        self.run_as(self.maya, f'set {line} text=""', ok=False)
        self.run_as(self.maya, "undo")
        self.assertEqual(self.rows(self.sam)[-1]["text"], "see you at 7")

    def test_remove_by_speaker_or_leader_and_stub_only_when_answered(self):
        a = self.say(self.maya, "first")
        b = self.say(self.sam, "second")
        reply = self.say(self.sam, "replying", reply_to=a)
        self.rows(self.sam)
        self.run_as(self.sam, f"forget {a}", ok=False)               # not Sam's line, Sam leads nothing
        self.run_as(self.sam, f"forget {b}")                          # his own
        self.rows(self.alex)
        self.run_as(self.alex, f"forget {a}")                         # a leader (the steward) removes Maya's
        rows = self.rows(self.maya)
        ids = [r["id"] for r in rows]
        self.assertNotIn(b, ids)                                      # unanswered: gone
        stub = rows[ids.index(a)]
        self.assertTrue(stub["removed"])
        self.assertEqual(stub["text"], "")
        self.assertEqual(stub["by_id"], "")
        r = rows[ids.index(reply)]
        self.assertEqual(r["reply"], {"id": a, "name": "", "text": "", "removed": True})
        self.run_as(self.alex, "undo")
        self.assertFalse(self.rows(self.maya)[0]["removed"])

    def test_react_toggles_and_shows_names(self):
        line = self.say(self.maya, "potluck friday?")
        self.run_as(self.sam, f"react {line} emoji=👍")
        self.run_as(self.maya, f"react {line} emoji=👍")
        self.run_as(self.sam, f"react {line} emoji=🎉")
        row = self.rows(self.sam)[-1]
        self.assertEqual(row["reactions"][0], {"emoji": "👍", "count": 2, "mine": True, "names": ["Sam", "Maya"]})
        self.assertEqual(row["reactions"][1]["emoji"], "🎉")
        self.run_as(self.sam, f"react {line} emoji=👍")              # again: takes it back
        row = self.rows(self.sam)[-1]
        self.assertEqual(row["reactions"][0], {"emoji": "👍", "count": 1, "mine": False, "names": ["Maya"]})
        self.run_as(self.sam, f'react {line} emoji="two words"', ok=False)
        self.run_as(self.sam, f"react {line} emoji={'x' * 17}", ok=False)
        self.run_as(self.sam, f"set {line} react:{self.sam}:👍=yes", ok=False)   # only react writes reactions

    def test_row_shape(self):
        first = self.say(self.maya, "hello")
        line = self.say(self.alex, "hi @Maya welcome", reply_to=first)
        row = self.rows(self.sam)[-1]
        for key in ("id", "chat", "by", "by_id", "name", "guest", "badge", "mine", "text", "at", "ts", "reply_to",
                    "reply", "edited", "removed", "pinned", "reactions", "mentions", "files", "rev"):
            self.assertIn(key, row)
        self.assertEqual(row["id"], line)
        self.assertEqual((row["by_id"], row["name"], row["badge"]), (self.alex, "Alex", "steward"))
        self.assertEqual(row["mentions"], [self.maya])
        self.assertEqual(row["reply"], {"id": first, "name": "Maya", "text": "hello", "removed": False})
        self.assertIsInstance(row["ts"], int)
        self.assertIsNone(row["edited"])
        self.assertFalse(row["mine"])
        self.assertTrue(self.rows(self.alex)[-1]["mine"])
        self.assertEqual(self.rows(self.sam)[0]["badge"], "")

    def test_before_and_since_pages(self):
        lines = [self.say(self.maya, f"line {i}") for i in range(7)]
        last3 = self.rows(self.sam, "limit=3")
        self.assertEqual([r["id"] for r in last3], lines[-3:])
        older = self.rows(self.sam, f"limit=3 before={last3[0]['id']}")
        self.assertEqual([r["id"] for r in older], lines[1:4])
        self.assertEqual([r["id"] for r in self.rows(self.sam, f"since={lines[4]}")], lines[5:])
        self.run_as(self.sam, f"chat {self.chat} before=dk99999", ok=False)

    def test_pins_by_leaders(self):
        line = self.say(self.maya, "meeting moved to Thursday")
        self.say(self.sam, "ok")
        self.rows(self.maya)
        self.run_as(self.maya, f"pin {line}", ok=False)              # leaders pin
        self.rows(self.alex)
        self.run_as(self.alex, f"pin {line}")
        pinned = self.rows(self.sam, "pinned=yes")
        self.assertEqual([r["id"] for r in pinned], [line])
        self.assertTrue(pinned[0]["pinned"])
        self.run_as(self.alex, f"pin {line} off=yes")
        self.assertEqual(self.rows(self.sam, "pinned=yes"), [])

    def test_every_change_is_a_record_the_stream_wakes_on(self):
        line = self.say(self.maya, "hello")
        self.rows(self.maya)
        steps = [(self.maya, f'set {line} text="hello all"'), (self.sam, f"react {line} emoji=👋"),
                 (self.maya, f"forget {line}")]
        for who, step in steps:
            n, h = len(self.k.log.records), len(self.k.happenings)
            self.run_as(who, step)
            self.assertEqual(len(self.k.log.records), n + 1)          # one record: /stream sends `world` for it
            self.assertTrue(self.k.happenings[h:], step)              # and a happening for hear


class Door(unittest.TestCase):
    """Over HTTP: no session reads as the visitor; its /do is refused 'sign in to send'; /keep/account carries guests."""

    def setUp(self):
        from kernel.door import serve
        self.dir = scratch.mkdtemp(prefix="kernel-door-visitors-")
        self.secret = secrets.token_hex(8)
        self.k = Kernel(self.dir, dict(GENESIS, visitors=True))
        # an entry service that is away: no session is ever signed in
        self.srv, self.host = serve(self.k, "http://127.0.0.1:9", self.secret, 0, LAB, cache_s=0)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.host.stop_all()
        shutil.rmtree(self.dir, ignore_errors=True)

    def post(self, path, body, headers=None):
        req = urllib.request.Request(self.url + path, json.dumps(body).encode(),
                                     {"Content-Type": "application/json", **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    def test_signed_out_reads_as_visitor_and_cannot_act(self):
        alex = self.k.accounts["google:alex"]
        note = self.k.run(Actor(alex, alex, "person"), "make kind=note title=Welcome")["made"][0]
        self.k.run(Actor(alex, alex, "person"), f"seen-by {note} everyone")
        hidden = self.k.run(Actor(alex, alex, "person"), "make kind=note title=Members")["made"][0]
        code, out = self.post("/see", {"line": f"look {note}"})
        self.assertEqual(code, 200, out)
        self.assertTrue(out["visitor"])
        self.assertIn("Welcome", out["text"])
        code, out = self.post("/see", {"line": f"look {hidden}"})
        self.assertFalse(out["ok"])
        code, out = self.post("/do", {"line": "make kind=note title=spam"}, {"Cookie": "agora_session=ended"})
        self.assertEqual(code, 200)
        self.assertFalse(out["ok"])
        self.assertIn("sign in to send", out["text"])
        code, out = self.post("/upload", {})
        self.assertEqual(code, 401)

    def test_keep_account_carries_guest(self):
        h = {"X-Kernel-Secret": self.secret}
        code, out = self.post("/keep/account", {"account": "guest:1", "name": "Robin", "invite": {"admitted": "qr"},
                                                "guest": True, "guest_until": 4102444800}, h)
        self.assertEqual(code, 200, out)
        self.assertTrue(out["guest"])
        self.assertEqual(self.k.state.get(out["person"], "guest_until"), 4102444800)
        code, out = self.post("/keep/account", {"account": "guest:1", "name": "Robin", "guest": False}, h)
        self.assertFalse(out["guest"])
        self.assertIsNone(self.k.state.get(out["person"], "guest"))


if __name__ == "__main__":
    unittest.main()
