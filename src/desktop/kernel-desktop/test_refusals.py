"""Refusals and errors reach a log (board card dk939), tested hidden on a fresh desktop world: the real kernel door
and its modules (window, guy, house...) running --headless, nothing on the screen. Everything is said as lines, as
Alex's pages, his agent and JEFF say them.

    C:/Projects/Agora4/.venv/Scripts/python.exe -m unittest test_refusals -v      (from src/desktop/kernel-desktop)

The cases are the reports this log exists for: a taskbar close that failed, a button whose line refuses, a bar that
polls a word which is down, a module that dies, a word that breaks, a page whose frame stopped.
"""
import json
import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from test_kdesk import Desk  # noqa: E402


class RefusalsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = Desk()
        k = cls.d.k                          # JEFF is a steward live (since 27 Oct): the same here
        from kernel.kernel import Tx
        jeff = k.accounts["desktop:jeff"]
        with k.lock:
            tx = Tx(k)
            tx.part("set", k.place, "JEFF stewards")
            tx.set(k.place, f"member:{jeff}", "leader")
            k._commit(tx, by="kernel", words="JEFF stewards")

    @classmethod
    def tearDownClass(cls):
        cls.d.close()

    def log(self, who="alex", line="refusals limit=50"):
        return self.d.say(line, who)

    def test_a_failed_close_from_the_taskbar_is_kept_with_who_line_and_why(self):
        d = self.d
        out = d.say("window.close dk99999", "alex")                     # the taskbar's close on a window gone
        self.assertFalse(out["ok"])
        got = self.log()
        self.assertTrue(got.get("ok", True), got)
        row = next(r for r in got["rows"] if r["line"] == "window.close dk99999")
        self.assertEqual(row["who"], "Alex")
        self.assertTrue(row["why"])
        self.assertNotIn("refused:", row["why"])
        self.assertIn("window.close dk99999", got["text"])

    def test_a_pressed_button_whose_line_refuses_is_one_entry_not_two(self):
        d = self.d
        out = d.say('make kind=button bar=taskbar label="Broken" does="window.close dk88888"', "claude")
        self.assertTrue(out["ok"], out["text"])
        before = len(d.k.refusals.rows)
        out = d.say("press Broken", "alex")
        self.assertFalse(out["ok"])
        new = d.k.refusals.rows[before:]
        self.assertEqual(len(new), 1, new)
        self.assertEqual(new[0]["line"], "press Broken")
        self.assertIn("window.close dk88888", new[0]["why"])

    def test_the_same_refusal_polled_again_is_counted_not_repeated(self):
        d = self.d
        for _ in range(5):
            d.say("wm.nosuchword", "alex")                              # a bar polling a word that is down
        rows = [r for r in d.k.refusals.rows if r["line"] == "wm.nosuchword"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["times"], 5)
        self.assertIn("×5", self.log()["text"])

    def test_a_steward_sees_everyones_and_jeff_can_read_them(self):
        d = self.d
        d.say("window.close dk77777", "claude")                         # Alex's agent
        jeff = self.log("jeff")                                         # JEFF, a steward since 27 Oct
        self.assertIn("everyone's", jeff["text"])
        row = next(r for r in jeff["rows"] if r["line"] == "window.close dk77777")
        self.assertIn("Alex", row["who"])
        by_me = self.log("jeff", "refusals by=me")
        self.assertFalse(any(r["line"] == "window.close dk77777" for r in by_me["rows"]))

    def test_someone_who_is_not_a_steward_sees_only_their_own(self):
        d = self.d
        k = d.k
        from kernel.kernel import Actor, Tx
        with k.lock:
            tx = Tx(k)
            tx.part("join", None, "join")
            pid = tx.mint()
            tx.set(pid, "kind", "person")
            tx.set(pid, "name", "Maya")
            k._commit(tx, by=pid, words="join", via="test")
        maya = Actor(pid, pid, "person")
        self.assertFalse(k.run(maya, "window.open lines")["ok"])        # owner only
        got = k.run(maya, "refusals")
        self.assertTrue(got["ok"], got["text"])
        self.assertIn("of yours", got["text"])
        self.assertTrue(got["rows"])
        self.assertTrue(all(r["by"] == pid for r in got["rows"]), got["rows"])

    def test_a_module_that_dies_is_kept(self):
        d = self.d
        mid = d.k.module_named("guy")
        d.host.procs[mid].proc.kill()
        died = lambda: [r for r in d.k.refusals.rows if r["kind"] == "died" and r["by"] == mid]
        d.wait(lambda: d.say("look", "alex") and died(), 15)            # any act reconciles the modules
        rows = died()
        self.assertIn("stopped by itself", rows[-1]["why"])
        self.assertIn("[died]", self.log(line="refusals errors")["text"])

    def test_a_word_that_breaks_is_kept_as_an_error(self):
        d = self.d
        from kernel import words
        real = words.KERNEL["clock"]
        words.KERNEL["clock"] = lambda *a, **kw: 1 / 0
        try:
            d.say("clock", "alex")                                      # the door's request fails
        except OSError:
            pass                                                        # the door drops it, as before
        finally:
            words.KERNEL["clock"] = real
        row = next(r for r in reversed(d.k.refusals.rows) if r["line"] == "clock")
        self.assertEqual(row["kind"], "error")
        self.assertIn("ZeroDivisionError", row["why"])
        self.assertIn("test_refusals.py", row["why"])                   # where it broke

    def test_a_page_says_what_failed_outside_any_line(self):
        d = self.d
        out = d.say('failed why="stopped: This part stopped · its renderer exited." where=dock-bar', "alex")
        self.assertTrue(out["ok"], out["text"])
        self.assertNotIn("record", out)                                 # nothing written in the world
        row = d.k.refusals.rows[-1]
        self.assertEqual((row["kind"], row["where"], d.k.refusals.who(row)), ("failed", "dock-bar", "Alex"))
        self.assertIn("in dock-bar [failed]", self.log()["text"])

    def test_it_survives_a_restart_and_writes_nothing_in_the_world(self):
        d = self.d
        seq = len(d.k.log.records)
        d.say("window.close dk66666", "alex")
        self.assertEqual(len(d.k.log.records), seq)                     # a refusal is not a record
        from kernel.refusals import Refusals
        again = Refusals(d.k)                                           # what a restarted kernel reads back
        self.assertTrue(any(r["line"] == "window.close dk66666" for r in again.rows))
        lines = (d.k.keep_dir / "refusals.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertTrue(all(json.loads(x) for x in lines))

    def test_lines_help_mentions_it(self):
        d = self.d
        first = d.say("help", "alex")["text"]
        self.assertIn("refusals", first)
        self.assertIn("refusals [by=", d.say("help refusals", "alex")["text"])


if __name__ == "__main__":
    unittest.main()
