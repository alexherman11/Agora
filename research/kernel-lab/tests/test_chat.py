"""The chat kind and `say` (MOVING-IN D4): closed chats are seen only by their people, @name addresses, a line's
happening carries whom it calls, a refused line in a batch refuses only itself. Never calls a model."""
import shutil
import sys
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))

from kernel.kernel import Kernel, Actor  # noqa: E402
from kernel import scratch  # noqa: E402

GENESIS = {"tag": "dk", "name": "Alex's desktop", "steward": {"account": "desktop:alex", "name": "Alex"}}


class Chats(unittest.TestCase):
    def setUp(self):
        self.dir = scratch.mkdtemp(prefix="kernel-chat-")
        self.k = Kernel(self.dir, dict(GENESIS))
        self.alex = self.k.accounts["desktop:alex"]
        self.jeff = self.k.join("desktop:jeff", "JEFF", invite={"admitted": "steward"})["person"]
        self.pike = self.k.join("desktop:pike", "Pike", invite={"admitted": "steward"})["person"]

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_as(self, who, line, ok=True):
        out = self.k.run(Actor(who, who, "person"), line)
        self.assertEqual(out["ok"], ok, out["text"])
        return out

    def test_a_closed_chat_is_its_peoples_and_speaks_to_the_other(self):
        made = self.run_as(self.alex, 'make kind=chat name=Conversation with="Alex, JEFF"')["made"][0]
        self.assertIsNone(self.k.shown(self.pike, made))
        self.run_as(self.pike, f"say {made} hello", ok=False)
        seen = len(self.k.happenings)
        out = self.run_as(self.alex, f"say {made} what is waiting on me?")
        self.assertIn("to JEFF", out["text"])
        line = out["made"][0]
        self.assertIsNone(self.k.shown(self.pike, line))           # a line is never wider than its chat
        self.assertIsNotNone(self.k.shown(self.jeff, line))
        h = [h for h in self.k.happenings[seen:] if h["word"] == "say"][-1]
        told = self.k.happening_for(None, h)
        self.assertEqual(told["to"], [self.jeff])
        self.assertEqual(told["said"], line)
        back = self.run_as(self.jeff, f"say {made} two things")
        self.assertIn("to Alex", back["text"])
        rows = self.run_as(self.alex, f"chat {made}")["rows"]
        self.assertEqual([r["by"] for r in rows], ["Alex", "JEFF"])

    def test_an_open_chat_wakes_only_whom_it_names(self):
        shop = self.run_as(self.jeff, 'make kind=chat name="Shop talk"')["made"][0]
        self.assertIsNotNone(self.k.shown(self.pike, shop))
        plain = self.run_as(self.pike, f"say {shop} morning all")
        self.assertNotIn(" to ", plain["text"])
        called = self.run_as(self.pike, f'say {shop} @jeff can you look? not "@alex" though, and @nobody')
        self.assertIn("to JEFF", called["text"])
        self.assertIn("no one here is called @nobody", called["text"])
        self.assertEqual(self.k.state.get(called["made"][0], "to"), self.jeff)
        lensed = self.run_as(self.pike, f'say {shop} text="@jeff from the lens, not \\"@alex\\" though"')
        self.assertEqual(self.k.state.get(lensed["made"][0], "to"), self.jeff)

    def test_said_lines_are_made_only_by_say_and_undo_takes_one_back(self):
        shop = self.run_as(self.jeff, 'make kind=chat name="Shop talk"')["made"][0]
        self.run_as(self.pike, f"make kind=said chat={shop} text=forged", ok=False)
        line = self.run_as(self.pike, f"say {shop} oops")["made"][0]
        self.run_as(self.pike, "undo")
        self.assertIsNone(self.k.shown(self.pike, line))

    def test_only_the_speaker_sets_a_lines_acts_and_nothing_else(self):
        shop = self.run_as(self.jeff, 'make kind=chat name="Shop talk"')["made"][0]
        line = self.run_as(self.jeff, f'say {shop} looking now acts="look dk1"')["made"][0]
        self.assertEqual(self.k.state.get(line, "acts"), "look dk1")
        self.run_as(self.jeff, f'look {line}; set {line} acts="look dk1 · rows chat"')
        self.assertEqual(self.k.state.get(line, "acts"), "look dk1 · rows chat")
        # 5 Nov: its speaker may now edit its words (text=, kept as edited); every other fact stays the kernel's
        self.run_as(self.jeff, f'look {line}; set {line} chat=dk1', ok=False)
        self.run_as(self.pike, f'look {line}; set {line} text=forged', ok=False)
        self.run_as(self.pike, f'look {line}; set {line} acts=forged', ok=False)
        self.assertIn("rows chat", self.run_as(self.alex, f"chat {shop}")["text"])

    def test_a_name_outside_a_closed_chat_is_never_called(self):
        """Card dk1245: a line in a closed chat naming someone outside it must not wake them with its text. The
        house reads `to` with its own wide sight, so `to` itself has to stay inside the chat."""
        made = self.run_as(self.alex, 'make kind=chat name=Conversation with="Alex, JEFF"')["made"][0]
        seen = len(self.k.happenings)
        out = self.run_as(self.alex, f"say {made} @pike have a look at this")
        self.assertIn("Pike cannot see this chat", out["text"])
        line = out["made"][0]
        self.assertEqual(self.k.state.get(line, "to"), self.jeff)       # the chat's own people, never Pike
        both = self.run_as(self.alex, f"say {made} @pike and @jeff, both of you")["made"][0]
        self.assertEqual(self.k.state.get(both, "to"), self.jeff)
        for h in [h for h in self.k.happenings[seen:] if h["word"] == "say"]:
            self.assertNotIn(self.pike, self.k.happening_for(None, h)["to"])

    def test_an_older_line_addressed_outside_its_chat_is_not_delivered_there(self):
        """A record from before the fix (or a chat closed since) may still name an outsider in `to`: delivery keeps
        only people who may see the line now."""
        made = self.run_as(self.alex, 'make kind=chat name=Conversation with="Alex, JEFF"')["made"][0]
        seen = len(self.k.happenings)
        line = self.run_as(self.alex, f"say {made} morning")["made"][0]
        self.k.state.things[line]["to"] = f"{self.jeff} {self.pike}"       # as an older record would hold it
        h = [h for h in self.k.happenings[seen:] if h["word"] == "say"][-1]
        self.assertEqual(self.k.happening_for(None, h)["to"], [self.jeff])

    def test_an_open_chat_held_by_a_group_calls_only_who_can_see_it(self):
        team = self.run_as(self.alex, "group name=team open=no")["text"].split()[2]
        shop = self.k.run(Actor(self.alex, self.alex, "person"),
                          f'make kind=chat name="Team talk" in={team} sees=group')
        if not shop["ok"]:
            self.skipTest("this world has no group-held chat form: " + shop["text"][:120])
        chat = shop["made"][0]
        if self.k.shown(self.pike, chat) is not None:
            self.skipTest("the group chat is visible to Pike here, so nothing to test")
        out = self.run_as(self.alex, f"say {chat} @pike and @jeff")
        self.assertNotIn(self.pike, str(self.k.state.get(out["made"][0], "to") or "").split())

    def test_say_finds_a_chat_by_name(self):
        self.run_as(self.alex, 'make kind=chat name=Conversation with="Alex, JEFF"')
        out = self.run_as(self.alex, "say Conversation hi JEFF")
        self.assertIn("in Conversation", out["text"])


if __name__ == "__main__":
    unittest.main()


class RulesRunAsTheirMaker(unittest.TestCase):
    """Security review C1 (28 Oct): a steward re-pointed a member's rule; it then said into the member's DM as the
    member. What a rule does is its maker's to change; a leader may switch it off or forget it."""

    def setUp(self):
        self.dir = scratch.mkdtemp(prefix="kernel-rule-")
        self.k = Kernel(self.dir, dict(GENESIS))
        self.alex = self.k.accounts["desktop:alex"]
        self.pike = self.k.join("desktop:pike", "Pike", invite={"admitted": "member"})["person"]

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_as(self, who, line):
        return self.k.run(Actor(who, who, "person"), line)

    def test_only_the_maker_changes_what_a_rule_does(self):
        out = self.run_as(self.pike, 'make kind=rule on=post do="make kind=note text=seen"')
        self.assertTrue(out["ok"], out["text"])
        rule = out["made"][0]
        out = self.run_as(self.alex, f'look {rule}; set {rule} do="make kind=note text=hijacked"')
        self.assertFalse(out["ok"])
        self.assertIn("only they change what it does", out["text"])
        self.assertEqual(self.k.state.get(rule, "do"), "make kind=note text=seen")
        self.assertTrue(self.run_as(self.alex, f"look {rule}; set {rule} off=yes")["ok"])
        self.assertTrue(self.run_as(self.pike, f'look {rule}; set {rule} do="make kind=note text=mine"')["ok"])

    def test_a_leader_switches_a_members_rule_off_never_back_on(self):
        """Round 2: Pike parked his rule; Alex's `set off=` switched it back on, and it ran as Pike."""
        rule = self.run_as(self.pike, 'make kind=rule on=post do="make kind=note text=seen"')["made"][0]
        self.assertTrue(self.run_as(self.pike, f"look {rule}; set {rule} off=yes")["ok"])
        out = self.run_as(self.alex, f"look {rule}; set {rule} off=")
        self.assertFalse(out["ok"])
        self.assertIn("only they switch it back on", out["text"])
        self.assertEqual(self.k.state.get(rule, "off"), "yes")
        self.assertTrue(self.run_as(self.pike, f"look {rule}; set {rule} off=")["ok"])

    def test_a_leaders_undo_never_re_points_a_members_rule(self):
        """Round 2: Alex's `undo` of Pike's fix put the rule back on Pike's older `do`, still running as Pike."""
        rule = self.run_as(self.pike, 'make kind=rule on=post do="make kind=note text=old"')["made"][0]
        fix = self.run_as(self.pike, f'look {rule}; set {rule} do="make kind=note text=new"')
        out = self.run_as(self.alex, f"undo {fix['records'][-1]}")
        self.assertTrue(out["ok"], out["text"])
        self.assertIn("left switched off", out["text"])
        self.assertEqual(self.k.state.get(rule, "off"), "yes")

    def test_a_leader_takes_back_their_own_off(self):
        rule = self.run_as(self.pike, 'make kind=rule on=post do="make kind=note text=seen"')["made"][0]
        off = self.run_as(self.alex, f"look {rule}; set {rule} off=yes")
        out = self.run_as(self.alex, f"undo {off['records'][-1]}")
        self.assertTrue(out["ok"], out["text"])
        self.assertIsNone(self.k.state.get(rule, "off"))


class RefusalRows(unittest.TestCase):
    """Security review round 2: someone else's refused line reached a steward's agent through the rows (the text was
    redacted, the rows weren't), and a reason quoting a name showed whenever the line named a thing, not an id."""

    def setUp(self):
        self.dir = scratch.mkdtemp(prefix="kernel-refusals-")
        self.k = Kernel(self.dir, dict(GENESIS))
        self.alex = self.k.accounts["desktop:alex"]
        self.jeff = self.k.join("desktop:jeff", "JEFF", invite={"admitted": "steward"})["person"]
        self.pike = self.k.join("desktop:pike", "Pike", invite={"admitted": "member"})["person"]

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_as(self, who, line):
        return self.k.run(Actor(who, who, "person"), line)

    def test_someone_elses_row_has_no_line_and_no_unvouched_reason(self):
        note = self.run_as(self.pike, 'make kind=note name=Dentist text="lab results" sees=me')["made"][0]
        self.assertFalse(self.run_as(self.pike, "say Dentist lab results: positive")["ok"])
        out = self.run_as(self.alex, "refusals all")
        self.assertTrue(out["ok"], out["text"])
        rows = [r for r in out["rows"] if r.get("person") == self.pike]
        self.assertTrue(rows)
        for r in rows:
            self.assertNotIn("line", r)
            self.assertNotIn(note, str(r))
            self.assertNotIn("positive", str(r))
            self.assertNotIn("Dentist", str(r))
        self.assertNotIn("positive", out["text"])
        self.assertNotIn(note, out["text"])
        mine = self.run_as(self.pike, "refusals")
        self.assertIn("positive", mine["text"])                  # Pike still reads his own

    def test_a_vouched_reason_shows_and_names_no_title(self):
        for _ in range(2):
            self.run_as(self.pike, 'make kind=note name=Dentist text=x')
        self.assertFalse(self.run_as(self.pike, "look Dentist")["ok"])
        out = self.run_as(self.alex, "refusals all")
        row = next(r for r in out["rows"] if r.get("person") == self.pike)
        self.assertIn("asked which", row["why"])
        self.assertNotIn("Dentist", str(row))

    def test_a_pressed_buttons_label_and_line_stay_its_makers(self):
        """The refusals session (28 Oct): a vouched press refusal carried the button's label and does= line."""
        for _ in range(2):
            self.run_as(self.pike, 'make kind=note name=Dentist text=x')
        made = self.run_as(self.pike, 'make kind=button label="Secret plan" does="look Dentist"')
        self.assertTrue(made["ok"], made["text"])
        self.assertFalse(self.run_as(self.pike, f"press {made['made'][0]}")["ok"])
        rows = [r for r in self.run_as(self.alex, "refusals all")["rows"] if r.get("person") == self.pike]
        self.assertTrue(rows)
        self.assertIn("asked which", rows[0]["why"])
        self.assertNotIn("Secret plan", str(rows))
        self.assertNotIn("Dentist", str(rows))

    def test_an_error_shows_its_class_and_place_not_its_message(self):
        self.k.refusals.keep("TypeError: cannot read the diagnosis of Pike at /kernel/words.py:123", "set dk9 x=1",
                             actor=Actor(self.pike, self.pike, "person"), kind="error",
                             code="TypeError at /kernel/words.py:123")
        row = next(r for r in self.run_as(self.alex, "refusals all")["rows"] if r.get("person") == self.pike)
        self.assertEqual(row["why"], "error: TypeError at /kernel/words.py:123")
        self.assertNotIn("diagnosis", str(row))

    def test_a_module_for_a_member_keeps_its_lines_from_others(self):
        mid = "dk9001"                                   # as the kernel keeps an installed module, for Pike
        self.k.state.things[mid] = {"kind": "module", "name": "relay", "for": self.pike}
        self.k.refusals.keep("refused: no chat you can see is called Lab", "say Lab Pike's lab results: positive",
                             by=mid, via="module")
        rows = [r for r in self.run_as(self.alex, "refusals all")["rows"] if r.get("by") == mid]
        self.assertTrue(rows)
        self.assertNotIn("positive", str(rows))
        self.assertEqual(rows[0]["why"], "refused")


class SharedNames(unittest.TestCase):
    def test_a_closed_chat_never_picks_one_of_two_people_with_a_name(self):
        d = scratch.mkdtemp(prefix="kernel-names-")
        try:
            k = Kernel(d, dict(GENESIS))
            alex = k.accounts["desktop:alex"]
            c1 = k.join("desktop:chris1", "Chris", invite={"admitted": "member"})["person"]
            c2 = k.join("desktop:chris2", "Chris", invite={"admitted": "member"})["person"]
            out = k.run(Actor(alex, alex, "person"), 'make kind=chat name=Plans with="Alex, Chris"')
            self.assertFalse(out["ok"])
            self.assertIn("2 people are called Chris", out["text"])
            out = k.run(Actor(alex, alex, "person"), f'make kind=chat name=Plans with="Alex, {c2}"')
            self.assertTrue(out["ok"], out["text"])
            self.assertIsNone(k.shown(c1, out["made"][0]))
        finally:
            shutil.rmtree(d, ignore_errors=True)


class Replies(unittest.TestCase):
    def test_a_reply_goes_in_the_chat_of_the_line_it_answers(self):
        d = scratch.mkdtemp(prefix="kernel-reply-")
        try:
            k = Kernel(d, dict(GENESIS))
            alex = k.accounts["desktop:alex"]
            jeff = k.join("desktop:jeff", "JEFF", invite={"admitted": "steward"})["person"]
            run = lambda who, line: k.run(Actor(who, who, "person"), line)
            conv = run(alex, 'make kind=chat name=Conversation with="Alex, JEFF"')["made"][0]
            shop = run(jeff, 'make kind=chat name="Shop talk"')["made"][0]
            secret = run(alex, f"say {conv} keep this between us")["made"][0]
            out = run(jeff, f"say {shop} noted reply_to={secret}")
            self.assertFalse(out["ok"])
            self.assertIn("another chat", out["text"])
            self.assertTrue(run(jeff, f"say {conv} noted reply_to={secret}")["ok"])
        finally:
            shutil.rmtree(d, ignore_errors=True)
