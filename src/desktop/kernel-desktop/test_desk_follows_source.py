"""Things the desktop expects that have gone, or were never granted, tested hidden on a fresh desktop world (28 Oct:
the House was refused `turn` 9 times, rules asked the switched-off guy to hop every few minutes, a JEFF window showed
the archived old desk's page as blank white).

    C:/Projects/Agora4/.venv/Scripts/python.exe -m unittest test_desk_follows_source -v      (from kernel-desktop)
"""
import socket
import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kdesk  # noqa: E402
from test_kdesk import Desk  # noqa: E402
from kd_window import page_answers  # noqa: E402


def dead_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()                       # nothing listens there now
    return port


class FollowsSourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = Desk()

    @classmethod
    def tearDownClass(cls):
        cls.d.close()

    def grants(self, name):
        k = self.d.k
        m = k.module_named(name)
        with k.lock:
            return [set(str(k.state.get(g, "words") or "").split()) for g in k._grants_to(m)]

    def reconcile_with(self, name, extra):
        """kdesk starting again after its source asked module `name` for `extra` words too."""
        real = kdesk.module_specs

        def specs(headless=False):
            out = real(headless)
            for s in out:
                if s["name"] == name:
                    s["grants"] = s["grants"] + " " + extra
            return out
        kdesk.module_specs = specs
        try:
            kdesk.after_genesis(self.d.k, headless=True)
        finally:
            kdesk.module_specs = real

    def test_a_word_the_source_now_needs_is_granted_once_on_start(self):
        before = len(self.d.k.log.records)
        self.reconcile_with("house", "zz.new")
        self.assertTrue(any("zz.new" in g for g in self.grants("house")))
        words = " ".join(str(r.get("words", "")) for r in self.d.k.log.records[before:])
        self.assertIn("grant", words)
        self.assertIn("zz.new", words)
        n = len(self.d.k.log.records)
        self.reconcile_with("house", "zz.new")                 # a second start says nothing
        self.assertEqual(n, len(self.d.k.log.records))
        self.assertGreater(n, before)

    def test_a_word_taken_back_stays_back(self):
        self.reconcile_with("house", "zz.back")
        k = self.d.k
        seq = len(k.log.records)
        g = next(g for g in k._grants_to(k.module_named("house")) if "zz.back" in str(k.state.get(g, "words")))
        out = self.d.say(f"undo r{seq}", "alex")                # Alex takes the new grant back
        self.assertTrue(out["ok"], out["text"])
        self.assertNotIn(g, k._grants_to(k.module_named("house")))
        self.reconcile_with("house", "zz.back")
        self.assertFalse(any("zz.back" in w for w in self.grants("house")))

    def test_a_module_that_is_off_gets_nothing_back(self):
        d = self.d
        self.assertTrue(d.say("off media", "alex")["ok"])
        try:
            self.reconcile_with("media", "zz.off")
            self.assertFalse(any("zz.off" in w for w in self.grants("media")))
            self.assertEqual([], self.grants("media"))
        finally:
            d.say("undo", "alex")

    def test_the_house_holds_turn_around_nearby(self):
        words = set().union(*self.grants("house"))
        self.assertTrue({"turn", "around", "nearby"} <= words, words)

    def test_a_rule_rests_while_its_module_is_off(self):
        d = self.d
        out = d.say('make kind=rule on=window.opened do="guy.hop $target"')
        self.assertTrue(out["ok"], out["text"])
        rule = out["made"][0]
        self.assertTrue(d.say("off guy", "alex")["ok"])
        try:
            before = len(d.k.refusals.rows)
            d.say("window.open help")
            d.wait(lambda: any(r == rule for r, _, _ in d.k.rules_fired), 15)
            said = [s for r, _, s in d.k.rules_fired if r == rule]
            self.assertTrue(all(s.startswith("resting: guy is off") for s in said), said)
            time.sleep(0.5)
            new = [r for r in d.k.refusals.rows[before:] if "guy.hop" in str(r.get("line"))]
            self.assertEqual([], new)
        finally:
            d.say("undo", "alex")
            d.say(f"forget {rule}")

    def test_a_page_window_whose_door_is_gone_says_so_once_and_stays_shut(self):
        d = self.d
        port = dead_port()
        self.assertFalse(page_answers(f"http://127.0.0.1:{port}/x"))
        self.assertTrue(page_answers(d.url + "/health"))
        out = d.say(f'window.open url="http://127.0.0.1:{port}/lens.html" name=Gone')
        self.assertTrue(out["ok"], out["text"])
        got = d.wait(lambda: [r for r in d.k.refusals.rows if "not answering" in str(r.get("why"))], 15)
        time.sleep(2.5)                                          # the window host's clock comes round again
        again = [r for r in d.k.refusals.rows if "not answering" in str(r.get("why"))]
        self.assertEqual(1, len(again), again)
        self.assertIn("Gone", got[0]["why"])
        self.assertEqual(1, int(again[0].get("times") or again[0].get("count") or 1))


if __name__ == "__main__":
    unittest.main()
