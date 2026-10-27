"""The chat kind and `say` (MOVING-IN D4): closed chats are seen only by their people, @name addresses, a line's
happening carries whom it calls, a refused line in a batch refuses only itself. Never calls a model."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))

from kernel.kernel import Kernel, Actor  # noqa: E402

GENESIS = {"tag": "dk", "name": "Alex's desktop", "steward": {"account": "desktop:alex", "name": "Alex"}}


class Chats(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="kernel-chat-")
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

    def test_said_lines_are_made_only_by_say_and_undo_takes_one_back(self):
        shop = self.run_as(self.jeff, 'make kind=chat name="Shop talk"')["made"][0]
        self.run_as(self.pike, f"make kind=said chat={shop} text=forged", ok=False)
        line = self.run_as(self.pike, f"say {shop} oops")["made"][0]
        self.run_as(self.pike, "undo")
        self.assertIsNone(self.k.shown(self.pike, line))

    def test_say_finds_a_chat_by_name(self):
        self.run_as(self.alex, 'make kind=chat name=Conversation with="Alex, JEFF"')
        out = self.run_as(self.alex, "say Conversation hi JEFF")
        self.assertIn("in Conversation", out["text"])


if __name__ == "__main__":
    unittest.main()
