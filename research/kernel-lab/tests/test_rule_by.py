"""Whose acts a rule hears (Alex, 28 Oct 2026: "You, your agents, leaders"). A rule runs as its maker, so by default it
hears its maker, the maker's agents and the leaders of its group; `by=anyone` hears everyone, said on purpose. A sealed
act is heard only by `by=anyone`. Fresh temporary worlds; rules fire on the kernel's rule thread, so tests wait."""
import shutil
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kernel.kernel import Kernel, Actor  # noqa: E402
from kernel import scratch  # noqa: E402

GENESIS = {"tag": "rb", "name": "Rules", "steward": {"account": "alex", "name": "Alex"},
           "invites_counted_by": "kernel", "invites": [{"code": "x", "uses": 5}]}


def until(test, s=4.0):
    end = time.time() + s
    while time.time() < end:
        if test():
            return True
        time.sleep(0.05)
    return test()


class RulesHear(unittest.TestCase):
    def setUp(self):
        self.dir = scratch.mkdtemp(prefix="kernel-rule-by-")
        self.k = Kernel(self.dir, dict(GENESIS))
        self.alex = self.k.actor_for(self.k.accounts["alex"])
        self.pike = self.k.actor_for(self.k.join("pike", "Pike", invite="x")["person"])

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def say(self, who, line, ok=True):
        out = self.k.run(who, line)
        self.assertEqual(out["ok"], ok, out["text"])
        return out

    def notes(self, text):
        return [t for t in self.k.things("note") if self.k.state.get(t, "text") == text]

    def test_a_new_rule_hears_its_maker_not_a_member(self):
        rule = self.say(self.alex, 'make kind=rule on=post do="make kind=note text=heard"')["made"][0]
        self.assertEqual(self.k.state.get(rule, "by"), "maker")
        self.say(self.pike, "post from Pike")
        time.sleep(0.6)
        self.assertEqual(self.notes("heard"), [])                      # a member's act: not heard
        self.say(self.alex, "post from Alex")
        self.assertTrue(until(lambda: len(self.notes("heard")) == 1))

    def test_by_anyone_hears_everyone(self):
        self.say(self.alex, 'make kind=rule on=post by=anyone do="make kind=note text=heard"')
        self.say(self.pike, "post from Pike")
        self.assertTrue(until(lambda: len(self.notes("heard")) == 1))

    def test_a_members_rule_hears_the_places_leaders_and_the_makers_agent(self):
        self.say(self.pike, 'make kind=rule on=post do="make kind=note text=pike-heard"')
        self.say(self.alex, "post from the steward")
        self.assertTrue(until(lambda: len(self.notes("pike-heard")) == 1))
        helper = self.k.actor_for(self.pike.person, agent="Helper")
        self.say(helper, "post from Pike's agent")
        self.assertTrue(until(lambda: len(self.notes("pike-heard")) == 2))

    def test_a_sealed_act_is_heard_only_by_anyone(self):
        thing = self.say(self.alex, "post likeable")["made"][0]
        self.say(self.alex, 'make kind=rule on=like do="make kind=note text=like-heard"')
        self.say(self.alex, 'make kind=rule on=like by=anyone do="make kind=note text=like-heard-anyone"')
        self.say(self.alex, f"look {thing}")
        self.say(self.alex, f"like {thing}")
        self.assertTrue(until(lambda: len(self.notes("like-heard-anyone")) == 1))
        self.assertEqual(self.notes("like-heard"), [])                # matching on who would unseal the like

    def test_by_is_the_makers_to_change(self):
        rule = self.say(self.pike, 'make kind=rule on=post do="make kind=note text=x"')["made"][0]
        self.say(self.alex, f"look {rule}")
        out = self.say(self.alex, f"set {rule} by=anyone", ok=False)
        self.assertIn("only they change what it does", out["text"])
        out = self.say(self.pike, f"look {rule}; set {rule} by=everyone", ok=False)
        self.assertIn("by= is maker", out["text"])
        self.say(self.pike, f"look {rule}; set {rule} by=anyone")

    def test_a_rule_from_before_by_still_hears_everyone(self):
        rule = self.say(self.alex, 'make kind=rule on=post do="make kind=note text=old-rule"')["made"][0]
        del self.k.state.things[rule]["by"]                          # as a rule made before by= existed
        self.say(self.pike, "post from Pike")
        self.assertTrue(until(lambda: len(self.notes("old-rule")) == 1))

    def test_a_chain_is_judged_by_the_act_that_started_it(self):
        """Approved-builds review M4: a member's act reached a by=maker rule through a leader's by=anyone rule."""
        self.say(self.alex, 'make kind=rule on=post by=anyone do="make kind=note text=relay"')
        self.say(self.alex, 'make kind=rule on=make do="set $target seen=yes"')
        self.say(self.pike, "post from Pike")
        self.assertTrue(until(lambda: len(self.notes("relay")) == 1))
        time.sleep(0.6)
        self.assertIsNone(self.k.state.get(self.notes("relay")[0], "seen"))     # started by Pike: not heard
        self.say(self.alex, "post from Alex")
        self.assertTrue(until(lambda: any(self.k.state.get(t, "seen") == "yes" for t in self.notes("relay"))))

    def test_undoing_a_makers_forget_leaves_the_rule_off(self):
        """Review M6: Alex undid Pike's forget of Pike's rule, and it ran again as Pike."""
        rule = self.say(self.pike, 'make kind=rule on=post do="make kind=note text=x"')["made"][0]
        gone = self.say(self.pike, f"look {rule}; forget {rule}")
        out = self.say(self.alex, f"undo {gone['records'][-1]}")
        self.assertIn("left switched off", out["text"])
        self.assertEqual(self.k.state.get(rule, "off"), "yes")

    def test_by_with_nothing_is_refused(self):
        rule = self.say(self.alex, 'make kind=rule on=post do="make kind=note text=x"')["made"][0]
        out = self.say(self.alex, f"look {rule}; set {rule} by=", ok=False)
        self.assertIn("by= is maker", out["text"])
        self.assertEqual(self.k.state.get(rule, "by"), "maker")

    def test_a_kit_rule_hears_its_taker_by_default(self):
        """Review H1: a kit dropped by=, and a taken rule heard every member, as its taker."""
        import json
        g = self.say(self.alex, "group name=crew open=no")["text"].split()[2]
        self.say(self.alex, f'make kind=rule on=post do="make kind=note text=kit-heard" in={g}')
        kit = self.say(self.alex, f"kit {g}")["made"][0]
        bundle = self.k.run(self.alex, f"look {kit}", mode="see")["rows"][0]["bundle"]
        for d in bundle["definitions"]:
            d["facts"].pop("by", None)                       # as a kit made before by= existed
        out = self.k.run(self.alex, "take in=" + self.k.place + " bundle=" + json.dumps(json.dumps(bundle)))
        self.assertTrue(out["ok"], out["text"])
        taken = [t for t in out["made"] if self.k.state.get(t, "kind") == "rule"]
        self.assertEqual([self.k.state.get(t, "by") for t in taken], ["maker"])

    def test_own_is_whom_a_thing_was_made_for(self):
        """Review H2: a thing a module or agent made for Pike counted as Alex's own."""
        helper = self.k.actor_for(self.pike.person, agent="Helper")
        t = self.say(helper, "make kind=note text=pikes")["made"][0]
        self.assertTrue(self.k.own(self.pike.person, t))
        self.assertFalse(self.k.own(self.alex.person, t))
