"""$ fill-ins (dk1368): an as= name lasts for the sign-in, the old desk's plain fills ($me $here $today $now $new)
work in any line, a $name nothing fills is refused saying why, and `help $` lists every fill-in. Fresh temporary
worlds; one test goes through the real door and MCP adapter, hidden (no window)."""
import shutil
import sys
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB))
from kernel.kernel import Kernel  # noqa: E402
from kernel import helping  # noqa: E402
from kernel import scratch  # noqa: E402

GENESIS = {"tag": "fi", "name": "Fills", "steward": {"account": "alex", "name": "Alex"},
           "invites_counted_by": "kernel", "invites": [{"code": "x", "uses": 5}]}


class FillIns(unittest.TestCase):
    def setUp(self):
        self.dir = scratch.mkdtemp(prefix="kernel-fill-ins-")
        self.k = Kernel(self.dir, dict(GENESIS))
        self.alex = self.k.actor_for(self.k.accounts["alex"])
        self.alex.session = "s-alex-1"
        self.pike = self.k.actor_for(self.k.join("pike", "Pike", invite="x")["person"])
        self.pike.session = "s-pike-1"

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def say(self, who, line, ok=True):
        out = self.k.run(who, line)
        self.assertEqual(out["ok"], ok, out["text"])
        return out

    def again(self, who, session=None):
        """The same sign-in in a later request: the door makes a fresh Actor each time."""
        a = self.k.actor_for(who.person, None)
        a.session = session or who.session
        return a

    # ---------------------------------------------------------------- as= across batches
    def test_a_name_made_with_as_lasts_into_the_next_batch(self):
        made = self.say(self.alex, "make kind=note title=Shopping as=sb")["made"][-1]
        later = self.again(self.alex)
        self.say(later, "set $sb title=Groceries")
        self.assertEqual(self.k.state.get(made, "title"), "Groceries")
        self.say(self.again(self.alex), "look $sb")                    # and the one after

    def test_a_later_as_with_the_same_name_wins(self):
        self.say(self.alex, "make kind=note title=One as=n")
        two = self.say(self.again(self.alex), "make kind=note title=Two as=n")["made"][-1]
        self.say(self.again(self.alex), "set $n text=hi")
        self.assertEqual(self.k.state.get(two, "text"), "hi")

    def test_names_belong_to_their_sign_in(self):
        self.say(self.alex, "make kind=note title=Mine as=sb")
        other = self.say(self.again(self.alex, "s-alex-2"), "set $sb title=x", ok=False)
        self.assertIn("$sb names nothing", other["text"])
        self.assertIn("as= names last for your sign-in", other["text"])
        theirs = self.say(self.pike, "look $sb", ok=False)
        self.assertIn("$sb names nothing", theirs["text"])

    def test_an_unknown_name_is_refused_saying_why_and_listing_yours(self):
        self.say(self.alex, "make kind=note title=Kept as=card")
        out = self.say(self.again(self.alex), "set $sb title=x", ok=False)
        self.assertIn("no earlier line of this sign-in said as=sb", out["text"])
        self.assertIn("$card", out["text"])
        self.assertIn("help $", out["text"])

    def test_a_quoted_name_keeps_its_words(self):
        self.say(self.alex, "make kind=note title=Kept as=card")
        note = self.say(self.again(self.alex), 'make kind=note text="ask about $card and $today"')["made"][-1]
        self.assertEqual(self.k.state.get(note, "text"), "ask about $card and $today")

    def test_a_verb_made_in_a_later_batch_keeps_its_own_dollar_words(self):
        self.say(self.alex, "make kind=note title=Kept as=card")
        # a verb's steps are quoted, so a sign-in name of the same spelling never leaks into them
        line = 'make kind=note text="steps: make kind=note as=card; set $card x=1"'
        note = self.say(self.again(self.alex), line)["made"][-1]
        self.assertIn("set $card x=1", self.k.state.get(note, "text"))

    def test_as_cannot_take_a_fill_ins_name(self):
        out = self.say(self.alex, "make kind=note title=x as=me", ok=False)
        self.assertIn("as=me", out["text"])
        self.assertIn("fill-in", out["text"])
        self.assertEqual([t for t in self.k.things("note") if self.k.state.get(t, "title") == "x"], [])

    def test_the_same_batch_still_works(self):
        out = self.say(self.alex, "make kind=note title=A as=a; set $a text=one")
        self.assertEqual(self.k.state.get(out["made"][0], "text"), "one")

    def test_a_rules_line_does_not_keep_names_into_its_makers_sign_in(self):
        self.k._local.rule = "r1"
        try:
            self.assertIsNone(self.k.session_names(self.alex))
        finally:
            self.k._local.rule = None

    def test_names_are_capped(self):
        names = self.k.session_names(self.alex)
        for i in range(self.k.SESSION_NAMES + 5):
            names[f"n{i}"] = f"x{i}"
        self.assertEqual(len(names), self.k.SESSION_NAMES)
        self.assertNotIn("n0", names)
        self.assertIn(f"n{self.k.SESSION_NAMES + 4}", names)

    # ---------------------------------------------------------------- the old desk's plain fills
    def test_me_here_today_now_fill_where_a_thing_goes(self):
        note = self.say(self.alex, "make kind=note title=Plain owner=$me due=$today at=$now home=$here")["made"][-1]
        get = lambda a: self.k.state.get(note, a)                      # noqa: E731
        self.assertEqual(get("owner"), self.alex.id)
        self.assertEqual(get("due"), self.k.now().date().isoformat())
        self.assertRegex(get("at"), r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertEqual(get("home"), self.k.place)

    def test_new_is_the_last_thing_made_in_the_batch_and_the_sign_in(self):
        first = self.say(self.alex, "make kind=note title=First; set $new text=a")["made"][0]
        self.assertEqual(self.k.state.get(first, "text"), "a")
        self.say(self.again(self.alex), "set $new text=b")
        self.assertEqual(self.k.state.get(first, "text"), "b")

    def test_new_with_nothing_made_says_so(self):
        out = self.say(self.pike, "set $new text=x", ok=False)
        self.assertIn("nothing was made yet", out["text"])

    def test_a_verb_fills_me_today_and_this(self):
        self.say(self.alex, 'verb stake steps="set $this owner=$me on=$today" help="stake <thing>: mine, today"')
        note = self.say(self.alex, "make kind=note title=Claimable")["made"][-1]
        self.say(self.alex, f"stake {note}")
        self.assertEqual(self.k.state.get(note, "owner"), self.alex.id)
        self.assertEqual(self.k.state.get(note, "on"), self.k.now().date().isoformat())

    # ---------------------------------------------------------------- help $
    def test_help_dollar_lists_every_fill_in(self):
        out = self.say(self.alex, "help $")
        for fill in ("$<name>", "$new", "$me", "$here", "$today", "$now", "$1", "$*", "$target", "$this",
                     "$<setting>", "$item", "$by", "$carried", "$view"):
            self.assertIn(fill, out["text"], fill)
        self.assertIn("not carried", out["text"])
        self.assertNotIn("no word called", out["text"])
        self.assertEqual(len([r for r in out["rows"] if "fill" in r]), len(helping.FILL_INS))

    def test_help_dollar_shows_your_names_by_name(self):
        self.say(self.alex, "make kind=note title=Shopping as=sb")
        out = self.say(self.again(self.alex), "help $")
        self.assertIn("$sb = Shopping", out["text"])
        self.assertIn("$me", self.say(self.alex, "help fill-ins")["text"])
        self.assertIn("$today", self.say(self.alex, "help $today")["text"])

    def test_every_supplied_name_has_a_help_row(self):
        listed = " ".join(f for f, *_ in helping.FILL_INS)
        for name in self.k.SUPPLIED:
            self.assertIn("$" + name, listed, name)


class OverTheDoor(unittest.TestCase):
    """JEFF's case: the MCP adapter sends each call on its own; a name made in one call is used in the next."""

    def setUp(self):
        sys.path.insert(0, str(LAB / "proof"))
        sys.path.insert(0, str(LAB / "mcp"))
        import byo_agent
        self.folder = scratch.TemporaryDirectory(prefix="fill-ins-wire-")
        self.place = byo_agent.Place(self.folder.name)
        self.client = byo_agent.MCP(self.place.url, self.place.agent_token)

    def tearDown(self):
        self.client.close()
        self.place.close()
        self.folder.cleanup()

    def test_as_in_one_call_and_dollar_in_the_next(self):
        import json
        self.client.initialize()

        def call(lines):
            got = self.client.request("tools/call", {"name": "lines", "arguments": {"lines": lines}})
            return json.loads(got["result"]["content"][0]["text"])
        first = call(['post "from one call" as=sb'])
        self.assertTrue(first["ok"], first)
        second = call(["look $sb"])
        self.assertTrue(second["ok"], second)
        self.assertIn("from one call", second["receipts"][0]["text"])
        third = call(["look $nope"])
        self.assertFalse(third["ok"])
        self.assertIn("$nope names nothing", json.dumps(third))


if __name__ == "__main__":
    unittest.main()
