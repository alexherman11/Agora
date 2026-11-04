"""Ask reaches JEFF (Alex, 3 Nov 2026: "Yes, fix both"). A right-click ask is kept as an ask-request and said, in
Alex's own words, as his line in the Conversation, so it wakes JEFF and Alex sees it there. Before this the ask-request
waited for a relay that had pointed at the archived old desk since 27 Oct; four asks were never read.

The live change is in the world (hide the old `ask`, make a new verb); this proves those same steps in a scratch
kernel. Never calls a model."""
import shutil
import sys
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))

from kernel.kernel import Kernel, Actor  # noqa: E402
from kernel import scratch  # noqa: E402

GENESIS = {"tag": "dk", "name": "Alex's desktop", "steward": {"account": "desktop:alex", "name": "Alex"}}

OLD_STEPS = "make kind=ask-request about=$1 text=$text where=$where status=open"


def new_steps(convo):
    return ("make kind=ask-request about=$1 text=$text where=$where status=sent as=ask; "
            f"say {convo} text=$text about=$ask")


def quoted(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


class AskReachesJeff(unittest.TestCase):
    def setUp(self):
        self.dir = scratch.mkdtemp(prefix="kernel-ask-")
        self.k = Kernel(self.dir, dict(GENESIS))
        self.alex = self.k.accounts["desktop:alex"]
        self.jeff = self.k.join("desktop:jeff", "JEFF", invite={"admitted": "steward"})["person"]
        self.pike = self.k.join("desktop:pike", "Pike", invite={"admitted": "steward"})["person"]
        self.convo = self.run_as(self.alex, 'make kind=chat name=Conversation with="Alex, JEFF"')["made"][0]
        self.doc = self.run_as(self.alex, 'make kind=document title="Why the agents stall"')["made"][0]
        # the world as it was: ask only makes the request
        self.run_as(self.alex, f'verb ask steps={quoted(OLD_STEPS)} help="ask <thing> text=…: old" takes="<id> text=<words> where=<text>"')

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_as(self, who, line, ok=True):
        out = self.k.run(Actor(who, who, "person"), line)
        self.assertEqual(out["ok"], ok, out["text"])
        return out

    def replace_ask(self):
        self.run_as(self.alex, "word-set ask status=hidden")
        self.run_as(self.alex, f'verb ask steps={quoted(new_steps(self.convo))} help="ask <thing>: new" '
                               f'takes="<id> text=<words> where=<text>"')

    def test_the_old_ask_reaches_nobody(self):
        seen = len(self.k.happenings)
        self.run_as(self.alex, f'ask {self.doc} text="edit in place" where="Writing"')
        says = [h for h in self.k.happenings[seen:] if h["word"] == "say"]
        self.assertEqual(says, [])

    def test_an_ask_is_alexs_line_to_jeff_in_the_conversation(self):
        self.replace_ask()
        seen = len(self.k.happenings)
        n = len(self.k.log.records)
        words = 'clicking should not change the view; it should "edit in place" $1'
        out = self.run_as(self.alex, f'ask {self.doc} text={quoted(words)} where="Why the agents stall · Writing"')
        self.assertEqual(len(self.k.log.records), n + 1, "one act: one undo takes the request and the line back")
        made = out["made"]
        req = next(m for m in made if self.k.state.get(m, "kind") == "ask-request")
        line = next(m for m in made if self.k.state.get(m, "kind") == "said")
        self.assertEqual(self.k.state.get(req, "about"), self.doc)
        self.assertEqual(self.k.state.get(req, "where"), "Why the agents stall · Writing")
        self.assertEqual(self.k.state.get(line, "text"), words, "his words, unchanged: quotes, ; and $1 stay data")
        self.assertEqual(self.k.state.get(line, "chat"), self.convo)
        self.assertEqual(self.k.state.get(line, "about"), req)
        h = [h for h in self.k.happenings[seen:] if h["word"] == "say"][-1]
        self.assertEqual(self.k.happening_for(None, h)["to"], [self.jeff], "the house wakes JEFF on this")
        self.run_as(self.alex, "undo")
        self.assertTrue(self.k.state.get(line, "forgotten") or self.k.shown(self.alex, line) is None)

    def test_someone_outside_the_conversation_is_refused_whole(self):
        self.replace_ask()
        n = len(self.k.log.records)
        out = self.run_as(self.pike, f'ask {self.doc} text="hi" where="x"', ok=False)
        self.assertTrue(out["text"].startswith("refused"))
        self.assertEqual(len(self.k.log.records), n)


if __name__ == "__main__":
    unittest.main()
