"""The walking skeleton, over real HTTP on loopback (SHAPE section 14).

Each test makes a fresh world in a temporary folder, starts the kernel's door and a stand-in for the entry service on
free loopback ports, and starts the tally module (Node) as the world says. People and agents act only through HTTP.
A few tests reach into the kernel directly where HTTP cannot stage the case (a module answer read before a change).

    C:/Projects/Agora4/.venv/Scripts/python.exe -m unittest discover -s tests -v      (from research/kernel-lab)
"""
import json
import secrets
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))

from kernel.door import serve                     # noqa: E402
from kernel.kernel import Kernel, Refused, Actor   # noqa: E402
from kernel.store import Log, BrokenLog, canon     # noqa: E402

NODE = shutil.which("node")
INVITE = "seabright-flyer-oct"


class StandInEntry:
    """The entry service's half of the seam, as it is built (research/community-app/site/SEAM.md, 23 Oct): it proves
    accounts and holds sessions; it tells the kernel about a new account (/keep/account) and answers who a session is
    (POST /internal/session/check, Bearer secret, the account as a record). The class below runs the real one."""

    def __init__(self, secret):
        self.secret, self.sessions, self.kernel_url = secret, {}, None
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
                if self.path != "/internal/session/check" or self.headers.get("X-Kernel-Secret") != outer.secret:
                    self.send_response(403)
                    self.end_headers()
                    return
                s = outer.sessions.get(body.get("token"))
                ans = {"account": s["account"], "method": s["method"], "agent": s.get("agent"),
                       "record": {"account_id": s["account"], "disabled": False}} if s else \
                    {"account": None, "method": None, "agent": None, "record": None}
                data = json.dumps(ans).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.srv.daemon_threads = True
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"

    def sign_in(self, account, name, invite=INVITE, answers=None, agent=None):
        """A verified sign-in: tell the kernel, then hand out a session token. -> (token, kernel's answer)."""
        out = post(f"{self.kernel_url}/keep/account", {"account": account, "name": name, "invite": invite,
                                                       "answers": answers or {}, "agent": agent},
                   headers={"X-Kernel-Secret": self.secret})
        if out[0] != 200:
            return None, out[1]
        token = secrets.token_urlsafe(24)
        self.sessions[token] = {"account": account, "method": "google", **({"agent": agent} if agent else {})}
        return token, out[1]


def post(url, body, headers=None, token=None):
    h = {"Content-Type": "application/json", **(headers or {})}
    if token:
        h["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, json.dumps(body).encode(), h)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


class Skeleton(unittest.TestCase):
    GRANTS = "look pin"

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="kernel-test-")
        self.secret = secrets.token_hex(16)
        self.entry = StandInEntry(self.secret)
        # this world counts its own invites (the seam's later phase); the real-entry tests below use the first
        genesis = {"tag": "sb", "name": "Seabright", "steward": {"account": "google:alex", "name": "Alex"},
                   "invites_counted_by": "kernel", "invites": [{"code": INVITE, "channel": "flyers", "uses": 20}],
                   "groups": [{"name": "Organizers"}],
                   "modules": [{"name": "tally", "run": [NODE, "modules/tally/tally.js"], "publishes": "tally.*",
                                "grants": self.GRANTS}]}
        self.k = Kernel(self.dir, genesis)
        self.srv, self.host = serve(self.k, self.entry.url, self.secret, 0, LAB)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        self.entry.kernel_url = self.url
        self.tally = self.k.module_named("tally")
        self.assertTrue(self.host.wait_offered(self.tally), "tally did not offer its words")
        self.alex = "alex-session"
        self.entry.sessions[self.alex] = {"account": "google:alex", "method": "google"}
        self.maya, _ = self.entry.sign_in("google:maya", "Maya", answers={"street": "Murray St"})
        self.maya_bot, _ = self.entry.sign_in("google:maya", "Maya", agent="helper")
        self.bea, _ = self.entry.sign_in("email:bea@example.org", "Bea")
        self.group = self.k.things("group")[0]

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.host.stop_all()
        self.entry.srv.shutdown()
        self.entry.srv.server_close()
        shutil.rmtree(self.dir, ignore_errors=True)

    # helpers
    def do(self, token, line, path="/do", **body):
        code, out = post(self.url + path, {"line": line, **body}, token=token)
        self.assertEqual(code, 200, out)
        return out

    def ok(self, token, line, path="/do", **body):
        out = self.do(token, line, path, **body)
        self.assertTrue(out["ok"], out["text"])
        return out

    def refused(self, token, line, says, path="/do"):
        before = len(self.k.log.records)
        out = self.do(token, line, path)
        self.assertFalse(out["ok"], out["text"])
        self.assertIn(says, out["text"])
        self.assertEqual(len(self.k.log.records), before, "a refusal wrote a record")
        return out

    def replays(self):
        again = Log(self.dir).replay()
        self.assertEqual(canon(again.snapshot()), canon(self.k.state.snapshot()), "the log does not rebuild memory")

    def person(self, account):
        return self.k.accounts[account]

    # ------------------------------------------------------------------ tests
    def test_person_and_agent_use_it_over_http(self):
        p = self.ok(self.maya, "post Meeting at Galt Elementary, Thursday 7pm")["made"][0]
        q = self.ok(self.maya_bot, "post Flyers are in the porch box")["made"][0]
        feed = self.ok(self.bea, "look")
        self.assertIn("Maya: Meeting at Galt", feed["text"])
        self.assertIn("agent for Maya: Flyers", feed["text"])
        by_agent = self.k.log.records[-1]
        self.assertEqual(by_agent["for"], self.person("google:maya"))
        self.assertEqual(by_agent["via"], "agent")
        self.assertNotEqual(by_agent["by"], self.person("google:maya"))
        self.assertEqual(self.k.state.get(q, "kind"), "post")
        self.assertEqual(self.k.state.get(p, "made_by"), self.person("google:maya"))
        self.replays()

    def test_every_word_has_an_entry_with_help(self):
        words = {self.k.state.get(e, "word"): self.k.entry(e) for e in self.k.entries()}
        for w in ("look", "help", "post", "like", "pin", "tally.top", "tally.pin-top"):
            self.assertIn(w, words)
            self.assertTrue(words[w].get("help", "").strip(), w)
        self.assertEqual((words["tally.top"]["from"], words["tally.top"]["bound"]), ("module:tally", "tally.top"))
        self.assertEqual((words["look"]["from"], words["look"]["bound"]), ("kernel", "look"))
        out = self.ok(self.maya, "help pin", path="/see")
        self.assertIn("who may: leaders", out["text"])
        listing = self.ok(self.maya, "help", path="/see")["text"]
        self.assertIn("not yours here:", listing)
        self.assertIn("pin (leaders)", listing)
        said = self.k.on_offer(self.tally, [{"word": "tally.quiet", "kind": "see", "help": ""},
                                            {"word": "pin2", "kind": "do", "help": "pins twice"}])
        self.assertIn("no help, so it is not published", said[0])
        self.assertIn("outside tally's namespace", said[1])
        self.assertIsNone(self.k.find_entry("tally.quiet"))
        self.assertIsNone(self.k.find_entry("pin2"))

    def test_pin_is_for_leaders_and_needs_a_look(self):
        p = self.ok(self.maya, "post Bring signs on Saturday")["made"][0]
        self.refused(self.maya, f"look {p}; pin {p}", "pin is for leaders of Seabright")
        self.refused(self.maya_bot, f"pin {p}", "pin is for leaders of Seabright")
        self.refused(self.alex, f"pin {p}", "you have not looked at")
        out = self.ok(self.alex, f"look {p}; pin {p}")
        self.assertEqual(len(out["records"]), 1)
        self.assertIn("pinned by Alex", self.ok(self.maya, f"look {p}", path="/see")["text"])
        self.assertIn("already pinned", self.ok(self.alex, f"pin {p}")["text"])
        self.replays()

    def test_like_is_sealed_and_once_each(self):
        p = self.ok(self.maya, "post Who can drive Saturday?")["made"][0]
        self.ok(self.maya, f"like {p}")
        self.refused(self.maya_bot, f"like {p}", "you already like")
        self.ok(self.bea, f"like {p}")
        self.assertIn("2 likes", self.ok(self.alex, f"look {p}", path="/see")["text"])
        maya, bea = self.person("google:maya"), self.person("email:bea@example.org")
        log_text = Path(self.dir, "log", "0001.jsonl").read_text(encoding="utf-8")
        sealed = [l for l in log_text.splitlines() if '"by":"sealed"' in l]
        self.assertEqual(len(sealed), 2)
        for line in sealed:
            self.assertNotIn(maya, line)
            self.assertNotIn(bea, line)
        shown = self.k.shown(self.person("google:alex"), p)
        self.assertFalse([a for a in shown if a.startswith("like:")], "who liked is shown")
        self.ok(self.maya, "undo")
        self.assertIn("1 like", self.ok(self.alex, f"look {p}", path="/see")["text"])
        self.assertEqual(self.k.log.records[-1]["by"], "sealed", "undoing a sealed like said who")
        self.ok(self.maya_bot, f"like {p}")           # hers again, through her agent
        self.replays()

    def test_who_sees_applies_at_every_read(self):
        q = self.ok(self.alex, f"post Organizers meet at 6 in={self.group}")["made"][0]
        self.assertIn("Organizers meet", self.ok(self.alex, "look", path="/see")["text"])
        self.assertNotIn("Organizers meet", self.ok(self.maya, "look", path="/see")["text"])
        hidden = self.refused(self.maya, f"like {q}", "no thing called")["text"]
        missing = self.refused(self.maya, "like sb999", "no thing called")["text"]
        self.assertEqual(hidden.replace(q, "X"), missing.replace("sb999", "X"))
        self.ok(self.alex, f"like {q}")
        top = self.ok(self.maya, "tally.top", path="/see")
        self.assertNotIn(q, top["text"])
        self.assertIn(q, self.ok(self.alex, "tally.top", path="/see")["text"])
        maya = self.person("google:maya")
        self.assertIn("street=Murray St", self.ok(self.maya, f"look {maya}", path="/see")["text"])
        self.assertIn("street=Murray St", self.ok(self.alex, f"look {maya}", path="/see")["text"])
        self.assertNotIn("Murray", self.ok(self.bea, f"look {maya}", path="/see")["text"])

    def test_undo_has_its_own_may(self):
        p = self.ok(self.maya, "post a post Maya will regret")["made"][0]
        self.ok(self.alex, f"look {p}; pin {p}")
        pin_rec = self.k.log.records[-1]["seq"]
        self.refused(self.maya, f"undo r{pin_rec}", "is Alex's")
        self.refused(self.bea, f"undo r{pin_rec}", "is Alex's")
        self.ok(self.bea, f"like {p}")
        post_rec = next(r["seq"] for r in self.k.log.records if r.get("words", "").startswith("post a post"))
        self.refused(self.alex, f"undo r{post_rec}", "changed since")      # it has a pin and a like now
        r = self.ok(self.maya, "post a second regret")
        self.ok(self.alex, f"undo {r['records'][0]}")                        # a steward may undo anyone's act
        self.assertNotIn("second regret", self.ok(self.bea, "look", path="/see")["text"])
        undo_rec = self.k.log.records[-1]["seq"]
        self.refused(self.alex, f"undo r{undo_rec}", "there is no redo")
        self.refused(self.alex, "undo r1", "cannot be undone")
        self.replays()

    def test_the_feed_takes_a_few_posts_a_day(self):
        for i in range(3):
            self.ok(self.maya, f"post note {i}")
        self.ok(self.maya_bot, "post note 3")
        self.ok(self.maya, "post note 4")
        self.refused(self.maya_bot, "post note 5", "you have posted 5 times today")
        self.ok(self.bea, "post Bea is not limited by Maya")
        self.ok(self.maya, "undo")
        self.ok(self.maya, "post note 5, after an undo")

    def test_module_publishes_and_answers_with_lines(self):
        a = self.ok(self.maya, "post Rally at the corner")["made"][0]
        b = self.ok(self.bea, "post Letters to the council")["made"][0]
        self.ok(self.bea, f"like {b}")
        self.ok(self.alex, f"like {b}")
        self.ok(self.maya, f"like {a}")
        top = self.ok(self.bea, "tally.top 2", path="/see")
        self.assertLess(top["text"].index(b), top["text"].index(a))
        # the module holds a pin grant, but Maya cannot pin: both must allow it
        self.refused(self.maya, "tally.pin-top", "pin is for leaders")
        before = len(self.k.log.records)
        out = self.ok(self.alex, "tally.pin-top")
        self.assertEqual(len(self.k.log.records), before + 1, "one use, one record")
        rec = self.k.log.records[-1]
        self.assertEqual((rec["by"], rec["for"], rec["via"]), (self.tally, self.person("google:alex"), "module"))
        self.assertEqual(rec["words"], "tally.pin-top")
        self.assertEqual(rec["parts"][0]["words"], f"pin {b}")
        self.assertIn(f"pinned by Alex", self.ok(self.bea, f"look {b}", path="/see")["text"])
        self.assertIn("by tally for Alex", out["text"])
        # it answered three calls (tally.top, Maya's pin-top that the kernel then refused, Alex's): the module cannot
        # know what the kernel admitted unless it is told, and it is not
        self.assertIn("3 calls answered", self.ok(self.bea, "status tally", path="/see")["text"])
        self.ok(self.alex, f"undo r{rec['seq']}")
        self.assertNotIn("pinned", self.ok(self.bea, f"look {b}", path="/see")["text"])
        self.replays()

    def test_a_renamed_module_word_still_reaches_its_module(self):
        # the world renames tally.top to `best` with an alias `top` (no word edits entries yet, so the steward's
        # change is written as a record directly); the module still knows only `tally.top`
        from kernel.kernel import Tx
        e = self.k.find_entry("tally.top")
        with self.k.lock:
            tx = Tx(self.k)
            tx.part("rename", e, "rename tally.top to best")
            tx.set(e, "word", "best")
            tx.set(e, "aliases", "top")
            self.k._commit(tx, by=self.person("google:alex"), words="rename tally.top to best")
        p = self.ok(self.maya, "post Renamed words keep working")["made"][0]
        self.ok(self.bea, f"like {p}")
        # the new word, its alias, and the bound name (a word that worked keeps working: DICTIONARY-ENTRY.md)
        for said in ("best", "top", "tally.top"):
            self.assertIn(p, self.ok(self.bea, said, path="/see")["text"])
        self.ok(self.alex, "off tally; undo")           # restarted, it offers tally.top again: bound, not re-published
        self.assertTrue(self.host.wait_offered(self.tally))
        self.assertEqual(self.k.find_entry("tally.top"), e)
        self.assertEqual(len([x for x in self.k.things("word") if self.k.state.get(x, "from") == "module:tally"]), 2)
        self.assertIn(p, self.ok(self.bea, "best", path="/see")["text"])

    def test_off_takes_every_grant_and_undo_turns_it_on(self):
        self.refused(self.maya, "off tally", "off is for stewards")
        self.ok(self.alex, "off tally")
        self.assertFalse(self.host.running(self.tally))
        self.refused(self.bea, "tally.top", "is unbound", path="/see")
        self.assertIn("grants: none", self.ok(self.bea, "look tally", path="/see")["text"])
        self.ok(self.alex, "undo")
        self.assertTrue(self.host.wait_offered(self.tally))
        self.ok(self.bea, "tally.top", path="/see")
        self.replays()

    def test_a_module_answer_is_admitted_only_if_what_it_read_still_holds(self):
        p = self.ok(self.maya, "post Read before acting")["made"][0]
        self.ok(self.bea, f"like {p}")
        rev = self.k.state.rev[p]
        self.ok(self.maya, f"like {p}")                     # changes p after the module would have read it
        alex = self.k.actor_for(self.person("google:alex"))
        entry = self.k.entry(self.k.find_entry("tally.pin-top"))
        before = len(self.k.log.records)
        with self.assertRaisesRegex(Refused, "stale"):
            self.k.admit(self.tally, alex, "tally.pin-top", entry, {"lines": [f"pin {p}"], "saw": {p: rev}})
        with self.assertRaisesRegex(Refused, "not among what was read"):
            self.k.admit(self.tally, alex, "tally.pin-top", entry, {"lines": [f"pin {p}"], "saw": {}})
        with self.assertRaisesRegex(Refused, "may hold only acts"):
            self.k.admit(self.tally, alex, "tally.pin-top", entry, {"lines": ["look"], "saw": {}})
        self.assertEqual(len(self.k.log.records), before)
        self.k.admit(self.tally, alex, "tally.pin-top", entry, {"lines": [f"pin {p}"], "saw": {p: self.k.state.rev[p]}})
        self.assertEqual(self.k.state.get(p, "pinned"), self.person("google:alex"))

    def test_the_seam_and_the_door_trust_only_the_session(self):
        code, out = post(self.url + "/keep/account", {"account": "google:mallory", "name": "M", "invite": INVITE})
        self.assertEqual(code, 403)
        tok, said = self.entry.sign_in("google:zed", "Zed", invite="wrong-code")
        self.assertIsNone(tok)
        self.assertIn("no invite", said["refused"])
        self.assertEqual(post(self.url + "/do", {"line": "look"})[0], 401)
        self.assertEqual(post(self.url + "/do", {"line": "look"}, token="made-up")[0], 401)
        code, _ = post(self.url + "/do", {"line": "look"}, token=self.maya, headers={"Origin": "http://evil.example"})
        self.assertEqual(code, 403)
        p = self.ok(self.maya, "post as myself", **{"as": "alex"})["made"][0]
        self.assertEqual(self.k.state.get(p, "made_by"), self.person("google:maya"))
        once = self.ok(self.maya, "post pressed once", press="g-123")
        again = self.ok(self.maya, "post pressed once", press="g-123")
        self.assertIn("already done, as", again["text"])
        self.assertEqual(once["records"][0], again["text"].split("as ")[1])

    def test_replay_checks_the_chain_and_survives_redaction(self):
        p = self.ok(self.maya, "post my address is 12 Example Lane")["made"][0]
        self.ok(self.bea, f"like {p}")
        path = Path(self.dir, "log", "0001.jsonl")
        lines = path.read_text(encoding="utf-8").splitlines()
        i = next(n for n, l in enumerate(lines) if "Example Lane" in l)
        rec = json.loads(lines[i])
        tampered = list(lines)
        tampered[i] = lines[i].replace("12 Example Lane", "13 Example Lane")
        path.write_text("\n".join(tampered) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(BrokenLog, "digest"):
            Log(self.dir).replay()
        from kernel.store import h
        for f in rec["parts"][0]["facts"]:
            if f[1] == "text":
                f[3] = {"redacted": h(f[3]), "by": "steward", "why": "a home address"}
        redacted = list(lines)
        redacted[i] = canon(rec)
        path.write_text("\n".join(redacted) + "\n", encoding="utf-8")
        state = Log(self.dir).replay()
        self.assertEqual(state.get(p, "text")["why"], "a home address")
        self.assertEqual(sum(1 for a in state.things[p] if a.startswith("like:")), 1)

    def test_a_cut_short_last_line_never_happened(self):
        self.ok(self.maya, "post one")
        n = len(self.k.log.records)
        path = Path(self.dir, "log", "0001.jsonl")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write('{"v":1,"seq":99,"by":"half')
        log = Log(self.dir)
        log.replay()
        self.assertEqual(len(log.records), n)


class RealUse(Skeleton):
    """Cases from use rather than from the code: many people at once, a restart, a module that dies mid-call."""

    def test_many_people_at_once(self):
        tokens = [self.entry.sign_in(f"google:n{i}", f"Neighbour {i}")[0] for i in range(8)]
        first = self.ok(self.alex, "post The council meets Tuesday")["made"][0]
        errors = []

        def neighbour(tok, i):
            try:
                for j in range(4):
                    out = self.do(tok, f"post n{i} says thing {j}, it's going well")
                    if not out["ok"]:
                        errors.append(out["text"])
                out = self.do(tok, f"like {first}")
                if not out["ok"]:
                    errors.append(out["text"])
            except Exception as exc:          # noqa: BLE001
                errors.append(repr(exc))
        threads = [threading.Thread(target=neighbour, args=(t, i)) for i, t in enumerate(tokens)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(60)
        self.assertEqual(errors, [])
        self.assertIn("8 likes", self.ok(self.alex, f"look {first}", path="/see")["text"])
        self.assertEqual(sum(1 for t in self.k.things("post")), 1 + 8 * 4)
        self.replays()

    def test_a_restart_rebuilds_from_the_log(self):
        p = self.ok(self.maya, "post Before the restart")["made"][0]
        self.ok(self.maya, f"like {p}")
        self.ok(self.alex, f"look {p}; pin {p}")
        feed = self.ok(self.bea, "look", path="/see")["text"]
        self.srv.shutdown()
        self.srv.server_close()
        self.host.stop_all()
        self.k = Kernel(self.dir)                      # no genesis: the log is the whole world
        self.srv, self.host = serve(self.k, self.entry.url, self.secret, 0, LAB)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        self.entry.kernel_url = self.url
        self.assertTrue(self.host.wait_offered(self.tally))
        self.assertEqual(self.ok(self.bea, "look", path="/see")["text"], feed)
        self.ok(self.maya, "undo")                     # her sealed like is still hers: the seal secret is in the keep
        self.assertIn("0 likes", self.ok(self.bea, f"look {p}", path="/see")["text"])
        self.ok(self.alex, f"look {p}")                # seen marks are beside the world: a restart forgets them
        self.assertIn("already pinned", self.ok(self.alex, f"pin {p}")["text"])

    def test_a_module_that_dies_mid_call(self):
        crashy = Path(self.dir) / "crashy.py"
        crashy.write_text(
            "import json, sys\n"
            "for line in sys.stdin:\n"
            "    m = json.loads(line)\n"
            "    if m['t'] == 'hello':\n"
            "        print(json.dumps({'t': 'offer', 'words': [{'word': 'crashy.go', 'kind': 'do', 'takes': '',\n"
            "              'help': 'crashy.go: falls over.'}]}), flush=True)\n"
            "    elif m['t'] == 'call':\n"
            "        sys.stderr.write('crashy: out of luck\\n'); sys.stderr.flush(); sys.exit(3)\n",
            encoding="utf-8")
        # installed the way genesis installs one: a module thing, on, with a grant by the steward
        from kernel.kernel import Tx
        with self.k.lock:
            tx = Tx(self.k)
            tx.part("install", None, "install crashy")
            m = tx.mint()
            for a, v in (("kind", "module"), ("name", "crashy"), ("run", [sys.executable, str(crashy)]),
                         ("publishes", "crashy.*"), ("on", True)):
                tx.set(m, a, v)
            self.k._commit(tx, by=self.person("google:alex"), words="install crashy")
        self.host.reconcile()
        self.assertTrue(self.host.wait_offered(m))
        out = self.refused(self.alex, "crashy.go", "stopped while answering")
        self.assertIn("out of luck", out["text"])
        # it is on in the world, but it died: it rests before it is started again, and the refusal says so
        again = self.refused(self.alex, "crashy.go", "is not running: it stopped at")
        self.assertIn("will be started again in", again["text"])
        self.assertFalse(self.host.running(m))
        self.ok(self.alex, "look")


for _name in [n for n in dir(Skeleton) if n.startswith("test_")]:
    setattr(RealUse, _name, None)


class WithoutAPinGrant(Skeleton):
    """The other half of the intersection: Alex may pin, but a module granted only `look` may not pin for him."""
    GRANTS = "look"

    def test_a_module_holds_only_its_grants(self):
        p = self.ok(self.maya, "post Liked but unpinnable")["made"][0]
        self.ok(self.bea, f"like {p}")
        self.refused(self.alex, "tally.pin-top", "tally holds no grant for pin")
        self.ok(self.alex, "tally.top", path="/see")


# the tests of the parent class run once, not twice
for _name in [n for n in dir(Skeleton) if n.startswith("test_")]:
    setattr(WithoutAPinGrant, _name, None)


SITE = LAB.parent / "community-app" / "site"


class WithTheRealEntryService(unittest.TestCase):
    """The kernel against the sign-in story's own entry service (research/community-app/site, a13313), run in test
    mode on a free loopback port with its own data in a temporary folder. It is told to read no .env file, so no real
    key is ever loaded. The entry service does not call /keep/account itself yet (SEAM.md section 4), so this test
    makes that call where the entry service will."""

    def setUp(self):
        try:
            sys.path.insert(0, str(SITE))
            from agora_entry import config as entry_config
            from agora_entry.service import INVITE_EXPIRY_DAYS
            from agora_entry.web import App
        except Exception as exc:          # noqa: BLE001
            self.skipTest(f"the entry service could not be imported: {exc!r}")
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        self.tmp = tempfile.mkdtemp(prefix="kernel-entry-")
        self.secret = secrets.token_hex(16)
        env = {"SITE_MODE": "test", "SITE_DATA_DIR": str(Path(self.tmp, "entry")), "GOOGLE_STAND_IN": "off",
               "SITE_SECRET_KEY": secrets.token_hex(32), "KERNEL_SHARED_SECRET": self.secret,
               "SITE_LEADERS": "alex@example.com", "SITE_PORT": "0"}
        cfg = entry_config.from_env(env, dotenv=Path(self.tmp, "no.env"))
        self.app = App(cfg)

        class Quiet(WSGIRequestHandler):
            def log_message(self, *a):
                pass
        self.entry_srv = make_server("127.0.0.1", 0, self.app, handler_class=Quiet)
        threading.Thread(target=self.entry_srv.serve_forever, daemon=True).start()
        entry_url = f"http://127.0.0.1:{self.entry_srv.server_address[1]}"
        svc = self.app.service
        self.alex_tok, alex = svc.finish_google({"sub": "g-alex", "email": "alex@example.com", "name": "Alex"}, None)
        invite = svc.make_invite(alex["id"], "flyers", "link", 3, sorted(INVITE_EXPIRY_DAYS)[0])
        self.maya_tok, self.maya_acct = svc.finish_google(
            {"sub": "g-maya", "email": "maya@example.com", "name": "Maya R."}, invite["id"])
        self.invite = invite
        self.k = Kernel(Path(self.tmp, "world"), {"tag": "sb", "name": "Seabright", "invites_counted_by": "entry",
                                                  "steward": {"account": alex["id"], "name": "Alex"}})
        self.srv, self.host = serve(self.k, entry_url, self.secret, 0, LAB, cache_s=0)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"

    def tearDown(self):
        for s in (self.srv, self.entry_srv):
            s.shutdown()
            s.server_close()
        self.host.stop_all()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def cookie_do(self, token, line):
        req = urllib.request.Request(self.url + "/do", json.dumps({"line": line}).encode(),
                                     {"Content-Type": "application/json",
                                      "Cookie": "; ".join(f"{c}={token}" for c in ("agora_session", "entry_sid"))})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    def test_a_real_session_reaches_the_kernel(self):
        code, said = self.cookie_do(self.maya_tok, "look")
        self.assertEqual((code, said.get("error")), (401, "this account has not joined the place yet"))
        # the record, as the entry service's own seam hands it over
        entry_url = f"http://127.0.0.1:{self.entry_srv.server_address[1]}"
        code, said = post(entry_url + "/internal/session/check", {"token": self.maya_tok},
                          headers={"X-Kernel-Secret": self.secret, "Authorization": f"Bearer {self.secret}"})
        self.assertEqual(code, 200, said)
        record = said.get("record") or said.get("account")
        joined = post(self.url + "/keep/account",
                      {"account": record["account_id"], "name": record.get("display_name") or "Maya R.",
                       "invite": record.get("invited_through"), "answers": record.get("answers") or {}},
                      headers={"X-Kernel-Secret": self.secret})
        self.assertEqual(joined[0], 200, joined)
        self.assertTrue(joined[1]["new"])
        person = joined[1]["person"]
        self.assertEqual(self.k.state.get(person, "joined_via")["invite_id"], self.invite["id"])
        self.assertEqual(self.k.state.get(self.k.place, "member:" + person), None)   # a member, not a leader
        code, out = self.cookie_do(self.maya_tok, "post Hello from a real session")
        self.assertEqual(code, 200, out)
        self.assertTrue(out["ok"], out["text"])
        self.assertEqual(out["as"], "Maya R.")
        code, out = self.cookie_do(self.alex_tok, "look")
        self.assertIn("Maya R.: Hello from a real session", out["text"])
        self.app.service.sign_out(self.maya_tok)
        code, out = self.cookie_do(self.maya_tok, "look")
        self.assertEqual(code, 401, "a signed-out session still acted")

    def test_no_invite_from_the_entry_service_means_no_person(self):
        code, out = post(self.url + "/keep/account", {"account": "acct_nobody", "name": "Nobody", "invite": None},
                         headers={"X-Kernel-Secret": self.secret})
        self.assertEqual(code, 403)
        self.assertIn("no invite", out["refused"])


if __name__ == "__main__":
    unittest.main()
