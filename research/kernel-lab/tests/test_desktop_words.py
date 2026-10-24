"""What the desktop asked of the kernel (desktop proof a13428, kext.py), as the kernel's own words, used the way a
desktop uses them: a personal module installed for Alex, private things, rows, verb notes and rules, with a neighbour,
Sam, in the same world who must see none of Alex's private things.

Everything goes over real HTTP on loopback; the module is Python (modules/reminders/reminders.py).
"""
import json
import secrets
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_skeleton import StandInEntry, post        # noqa: E402
from test_painter import quoted                      # noqa: E402
from kernel import words as KW                       # noqa: E402
from kernel.door import serve                        # noqa: E402
from kernel.kernel import Kernel                     # noqa: E402

GENESIS = {"tag": "dk", "name": "Alex's desktop", "steward": {"account": "google:alex", "name": "Alex"},
           "invites_counted_by": "kernel", "invites": [{"code": "x", "uses": 5}], "groups": [{"name": "Garden"}],
           "modules": [{"name": "reminders", "run": [sys.executable, str(LAB / "modules/reminders/reminders.py")],
                        "publishes": "reminder.*", "for": "steward", "only": "kind:reminder",
                        "grants": "reminder.* make rows hear:make hear:post"}]}


def until(test, s=8.0):
    end = time.time() + s
    while time.time() < end:
        v = test()
        if v:
            return v
        time.sleep(0.1)
    return test()


class DesktopWords(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="kernel-desk-")
        self.secret = secrets.token_hex(16)
        self.entry = StandInEntry(self.secret)
        self.k = Kernel(self.dir, json.loads(json.dumps(GENESIS)))
        self.srv, self.host = serve(self.k, self.entry.url, self.secret, 0, LAB)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        self.entry.kernel_url = self.url
        self.mod = self.k.module_named("reminders")
        self.assertTrue(self.host.wait_offered(self.mod), "reminders did not offer its words")
        self.alex = "alex"
        self.entry.sessions[self.alex] = {"account": "google:alex", "method": "google"}
        self.sam, _ = self.entry.sign_in("google:sam", "Sam", invite="x")
        self.alex_id, self.sam_id = self.k.accounts["google:alex"], self.k.accounts["google:sam"]

    def tearDown(self):
        for s in (self.srv, self.entry.srv):
            s.shutdown()
            s.server_close()
        self.host.stop_all()
        shutil.rmtree(self.dir, ignore_errors=True)

    def do(self, who, line, ok=True):
        code, out = post(self.url + "/do", {"line": line}, token=who)
        self.assertEqual(code, 200, out)
        if ok is not None:
            self.assertEqual(out["ok"], ok, out["text"])
        return out

    def status(self):
        text = self.do(self.alex, "status reminders")["text"]
        return json.loads(text.split(": ", 1)[1])

    def reminders(self, who):
        return {r["text"] for r in self.do(who, "rows reminder")["rows"]}

    def test_a_personal_module_acts_reads_and_hears_as_its_person(self):
        # hello: who it is, whose it is, a folder of its own
        st = until(lambda: (s := self.status()) and s.get("own") and s)
        self.assertEqual((st["id"], st["owner"], st["for"]), (self.mod, self.alex_id, self.alex_id))
        self.assertTrue(Path(st["home"], "started.txt").exists())
        # on its own, at start, it made a reminder only Alex sees; the record is the module's, for no caller
        self.assertTrue(st["own"]["ok"], st["own"])
        own = st["own"]["made"][0]
        self.assertEqual(self.k.state.get(own, "sees"), f"person:{self.alex_id}")
        rec = self.k.log.records[int(st["own"]["record"][1:]) - 1]
        self.assertEqual((rec["by"], rec.get("for")), (self.mod, None))
        self.assertIn("the module started", self.reminders(self.alex))
        self.assertEqual(self.reminders(self.sam), set())
        # answering a call: the kernel tells it what its answer made
        out = self.do(self.alex, "reminder.add buy stamps")
        made = out["made"][0]
        st = until(lambda: (s := self.status()) and any(d.get("made") == [made] for d in s["done"]) and s)
        self.assertTrue(st, "the module never learned what its answer made")
        self.assertEqual(self.reminders(self.alex), {"the module started", "buy stamps"})
        # its grant reaches only reminders: a note is refused, and it is told so
        out = self.do(self.alex, "reminder.note hello", ok=False)
        self.assertIn("reaches only reminder things", out["text"])
        self.assertTrue(until(lambda: any(d.get("ok") is False for d in self.status()["done"])))
        # it hears what Alex may see, and nothing private of Sam's
        sams = self.do(self.sam, "make kind=note text=\"Sam's own\" sees=me")["made"][0]
        alexs = self.do(self.alex, "make kind=note text=\"Alex's own\" sees=me")["made"][0]
        talk = self.do(self.sam, "post Anyone have a ladder?")["made"][0]
        heard = until(lambda: (h := [t for _, t in self.status()["heard"]]) and talk in h and alexs in h and h)
        heard = until(lambda: (h := [t for _, t in self.status()["heard"]]) and talk in h and alexs in h and h) or [t for _, t in self.status()["heard"]]
        self.assertIn(alexs, heard)
        self.assertNotIn(sams, heard)
        # reading on its own as Alex: Sam's private note is not among the rows
        mine = self.do(self.alex, "reminder.mine")
        self.assertEqual({r["text"] for r in mine["rows"]}, {"the module started", "buy stamps"})
        self.assertEqual(self.do(self.alex, "rows note")["text"].count("Sam's own"), 0)
        self.assertEqual(self.do(self.sam, "rows note")["text"].count("Alex's own"), 0)
        self.assertEqual(Kernel(self.dir).state.snapshot(), self.k.state.snapshot())

    def test_sees_on_make_narrows_and_never_widens(self):
        g = self.k.things("group")[0]
        self.do(self.sam, f"make kind=note text=x sees=place in={g}", ok=False)       # Sam is no member of Garden
        out = self.do(self.alex, f"make kind=note text=plans sees=place in={g}", ok=False)
        self.assertIn("is not open", out["text"])
        lead = self.do(self.alex, "make kind=note text=\"for leaders\" sees=leaders")["made"][0]
        self.assertIsNone(self.k.shown(self.sam_id, lead))
        self.assertIsNotNone(self.k.shown(self.alex_id, lead))
        self.do(self.alex, "make kind=note text=x sees=everyone", ok=False)

    def test_a_verb_note_is_one_act_and_never_adds_power(self):
        steps = ('make kind=reminder text="water the plants" sees=me as=a; '
                 'make kind=reminder text="call the plumber" sees=me')
        self.do(self.sam, f"verb morning steps={quoted(steps)} help=\"morning: two reminders\"", ok=False)
        made = self.do(self.alex, f"verb morning steps={quoted(steps)} help=\"morning: two reminders\"")
        self.assertIn("a new word", made["text"])
        self.assertIn("morning: two reminders", self.do(self.sam, "help morning")["text"])
        n = len(self.k.log.records)
        out = self.do(self.alex, "morning")
        self.assertEqual(len(self.k.log.records), n + 1, "a do verb's steps are one record")
        self.assertEqual(len(out["made"]), 2)
        self.assertTrue({"water the plants", "call the plumber"} <= self.reminders(self.alex))
        self.do(self.sam, "morning")                                 # it runs as Sam: Sam's own, private to Sam
        self.assertEqual(self.reminders(self.sam), {"water the plants", "call the plumber"})
        self.do(self.alex, "undo")                                   # Alex's undo takes back his morning, both
        self.assertFalse({"water the plants", "call the plumber"} & self.reminders(self.alex))
        self.assertEqual(len(self.reminders(self.sam)), 2)
        # a step it may not take stops the whole verb, and nothing is written
        self.do(self.alex, 'verb tidy steps="make kind=reminder text=tidy sees=me; pin $1" help="tidy <post>: '
                           'a reminder and a pin"')
        p = self.do(self.sam, "post A post Sam may not pin")["made"][0]
        n = len(self.k.log.records)
        out = self.do(self.sam, f"tidy {p}", ok=False)
        self.assertIn("tidy stopped at 'pin", out["text"])
        self.assertEqual(len(self.k.log.records), n)
        self.do(self.alex, "verb post steps=\"look\" help=\"post: hidden\"", ok=False)   # no word hides another

    def test_module_words_in_verb_notes(self):
        until(lambda: self.status().get("own"))
        # one step that is a module's word: an alias, as if the module's word were said
        self.do(self.alex, 'verb remind steps="reminder.add $*" help="remind <words>: a reminder only you see"')
        out = self.do(self.alex, "remind buy milk")
        rec = self.k.log.records[-1]
        self.assertEqual((rec["by"], rec.get("for")), (self.mod, self.alex_id))
        self.assertIn("buy milk", self.reminders(self.alex))
        # a module step among kernel steps: the module's lines join the verb's one act, and one undo takes it back
        steps = 'reminder.add tidy the desk; make kind=note text="desk tidied" sees=me'
        self.do(self.alex, f"verb tidyup steps={quoted(steps)} help=\"tidyup: a reminder and a note\"")
        n = len(self.k.log.records)
        out = self.do(self.alex, "tidyup")
        self.assertEqual(len(self.k.log.records), n + 1, out["text"])
        self.assertEqual(len(out["made"]), 2)
        self.assertIn("tidy the desk", self.reminders(self.alex))
        self.assertTrue(until(lambda: any(d.get("record") == f"r{n + 1}" for d in self.status()["done"])),
                        "the module was not told its lines joined the verb's act")
        self.do(self.alex, "undo")
        self.assertNotIn("tidy the desk", self.reminders(self.alex))
        self.assertEqual(self.do(self.alex, "rows note")["text"].count("desk tidied"), 0)
        # a module step its grant does not reach stops the whole verb, and nothing is written
        steps = 'make kind=note text="first" sees=me; reminder.note second'
        self.do(self.alex, f"verb both steps={quoted(steps)} help=\"both: two notes\"")
        n = len(self.k.log.records)
        out = self.do(self.alex, "both", ok=False)
        self.assertIn("both stopped at 'reminder.note second'", out["text"])
        self.assertIn("reaches only reminder things", out["text"])
        self.assertEqual(len(self.k.log.records), n)

    def test_a_module_reading_for_you_counts_as_your_look(self):
        own = until(lambda: (s := self.status()).get("own") and s["own"]["made"][0])
        out = self.do(self.alex, f"set {own} text=\"the module started, seen\"", ok=False)
        self.assertIn("you have not looked", out["text"])
        self.do(self.alex, "reminder.mine")                         # the module reads Alex's reminders for him
        self.do(self.alex, f"set {own} text=\"the module started, seen\"")
        log = Path(self.status()["home"], "stderr.log")
        self.assertIn(f"reminders: started for {self.alex_id}", log.read_text(encoding="utf-8"))

    def test_rules_answer_what_their_maker_may_hear(self):
        car = self.do(self.alex, "make kind=carpool pickup=\"Murray & 5th\" seats=2")["made"][0]
        rule = self.do(self.alex, 'make kind=rule on=claim do="make kind=reminder text=\\"a seat was taken on '
                                  '$target\\" sees=me"')["made"][0]
        spy = self.do(self.sam, 'make kind=rule on=make do="post I saw $target being made"')["made"][0]
        n_sam_posts = len([t for t in self.k.things("post") if self.k.state.get(t, "made_by") == self.sam_id])
        self.do(self.sam, f"claim {car}")
        got = until(lambda: f"a seat was taken on {car}" in self.reminders(self.alex))
        self.assertTrue(got, "Alex's rule did not answer Sam's claim")
        recs = [r for r in self.k.log.records if r.get("rule") == rule]
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["by"], self.alex_id)
        # Sam's rule hears makes, but only those Sam may see: Alex's private reminder woke nothing of Sam's
        time.sleep(0.5)
        sam_posts = [t for t in self.k.things("post") if self.k.state.get(t, "made_by") == self.sam_id]
        self.assertEqual(len(sam_posts), n_sam_posts)
        self.do(self.alex, "make kind=note text=\"a public note\"")
        self.assertTrue(until(lambda: len([t for t in self.k.things("post")
                                           if self.k.state.get(t, "made_by") == self.sam_id]) > n_sam_posts))
        # a rule whose act wakes itself stops three deep
        self.do(self.sam, f"forget {spy}")
        self.do(self.alex, 'make kind=rule on=post do="post echo"')
        self.do(self.alex, "post start")
        time.sleep(1.5)
        echoes = [t for t in self.k.things("post") if self.k.state.get(t, "text") == "echo"]
        self.assertEqual(len(echoes), 3)

    def test_a_world_from_before_a_word_gets_it_on_start(self):
        d = tempfile.mkdtemp(prefix="kernel-old-")
        keep = list(KW.KERNEL_ENTRIES)
        try:
            KW.KERNEL_ENTRIES[:] = [e for e in keep if e["word"] not in ("verb", "rows")]
            g = {k: v for k, v in GENESIS.items() if k != "modules"}
            old = Kernel(d, g)
            self.assertIsNone(old.find_entry("verb"))
            KW.KERNEL_ENTRIES[:] = keep
            again = Kernel(d)
            self.assertIsNotNone(again.find_entry("verb"))
            self.assertIsNotNone(again.find_entry("find"))
            self.assertIn("the kernel's new words: rows verb", again.log.records[-1]["words"])
            n = len(again.log.records)
            self.assertEqual(len(Kernel(d).log.records), n)            # and only once
        finally:
            KW.KERNEL_ENTRIES[:] = keep
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
