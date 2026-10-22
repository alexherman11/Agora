# health: room test
"""a10269: a restart asked for from the world, on in-memory worlds only. No house, keeper, guard or process is run:
the house is a stand-in that runs its desk lines on the world, and the guard is a function the test chooses."""
import re
import unittest
from pathlib import Path
from types import SimpleNamespace

import house_restart as HR
import roomworld

VERB = (Path(__file__).resolve().parent / "restart-house.verb").read_text(encoding="utf-8")
CFG = {"restart_by": "jeff,alex", "guard_nongame": ""}


class House:
    """What Restarts uses of the house: act() on the world, and the workshop's drain flag."""
    def __init__(self, d):
        self.d, self.workshop, self.lines = d, SimpleNamespace(restart_wanted=False), []

    def act(self, who, line, whole=False):
        self.lines.append(line)
        self.d.world.me = who
        self.d._window = ""
        r = self.d.dispatch("desk", {"line": line, "whole": whole})
        assert not r.get("error") and not r.get("batch_error"), (line, r)
        return r.get("text", "")


class Base(unittest.TestCase):
    def setUp(self):
        self.d, self.r = roomworld.build(say=False)
        self.w = self.d.world
        corner = self.make(self.r.HOME, 'kind=surface title="JEFF\'s corner"')
        self.run_line(f"look {corner}")
        self.run_line(f"do prop {corner} role=resident actor=jeff")
        self.make(self.r.HOME, "kind=note title=restart-house tags=verb on=house text=" + _q(VERB))
        self.house = House(self.d)
        self.game = ""
        self.restarts = self.fresh(pid=111)

    def fresh(self, pid):
        return HR.Restarts(self.house, game=lambda nongame: self.game, clock=lambda: 1000.0, pid=pid)

    def run_line(self, line, who="jeff"):
        self.w.me = who
        self.d._window = ""
        r = self.d.dispatch("desk", {"line": line, "whole": True})
        self.assertFalse(r.get("error"), r)
        return r.get("text", "")

    def make(self, parent, fields, who="jeff"):
        self.run_line(f"look {parent}", who)
        return re.search(r"created ([af]\d+)", self.run_line(f"do create {parent} {fields}", who))[1]

    def ask(self, why="Mica's 6a31bd9 needs the house to reimport", who="jeff"):
        text = self.run_line(f"restart-house {why}", who)
        return re.search(r"created (a\d+)", text)[1]

    def props(self, aid):
        return self.w.subjects[self.w.nodes[aid]["subject"]].get("props") or {}


class Restart(Base):
    def test_the_verb_records_the_request_and_its_reason(self):
        aid = self.ask()
        p = self.props(aid)
        self.assertEqual((p["role"], p["state"]), ("house-restart", "asked"))
        self.assertIn("6a31bd9", p["why"])
        self.assertEqual(HR.maker(self.w, self.w.nodes[aid]["subject"]), "jeff")

    def test_waits_for_idle_says_what_is_in_flight_and_never_cuts(self):
        aid = self.ask()
        self.restarts.step(self.w, CFG, ["a5191", "a9000"])
        self.assertEqual(self.props(aid)["state"], "waiting")
        self.assertEqual(self.props(aid)["in_flight"], "a5191, a9000")
        self.assertTrue(self.house.workshop.restart_wanted)          # the drain: no new turn starts
        self.assertTrue(self.restarts.owns)
        for waited in (10, 90, 3600):                                # never cut, however long it takes
            self.assertFalse(HR.should_exit(self.restarts.owns, ["a9000"], waited, 90))
        self.restarts.step(self.w, CFG, ["a9000"])
        self.assertEqual(self.props(aid)["in_flight"], "a9000")
        self.restarts.step(self.w, CFG, [])
        self.assertTrue(HR.should_exit(self.restarts.owns, [], 0, 90))
        self.assertTrue(self.restarts.leaving(CFG))
        self.assertEqual((self.props(aid)["state"], self.props(aid)["old_pid"]), ("restarting", "111"))

    def test_a_landing_restart_still_cuts_after_its_grace(self):
        self.assertFalse(HR.should_exit(False, ["a9000"], 30, 90))
        self.assertTrue(HR.should_exit(False, ["a9000"], 90, 90))

    def test_one_restart_only_and_the_new_pid_is_reported(self):
        aid = self.ask()
        self.restarts.step(self.w, CFG, [])
        self.assertTrue(self.restarts.leaving(CFG))
        self.house.workshop.restart_wanted = False                   # a new process starts with no drain
        after = self.fresh(pid=222)                                  # the house the keeper started
        after.started_up(self.w)
        p = self.props(aid)
        self.assertEqual((p["state"], p["new_pid"]), ("done", "222"))
        self.assertTrue(p["started"])
        comments = self.w.subjects[self.w.nodes[aid]["subject"]].get("comments", [])
        self.assertIn("new pid 222", comments[-1]["text"])
        after.step(self.w, CFG, [])
        self.assertFalse(self.house.workshop.restart_wanted)         # a done note never drains again
        n = len(comments)
        self.fresh(pid=333).started_up(self.w)                       # nor is it reported twice
        self.assertEqual(len(self.w.subjects[self.w.nodes[aid]["subject"]].get("comments", [])), n)

    def test_two_requests_ride_one_restart(self):
        one, two = self.ask(), self.ask("a second reason")
        self.restarts.step(self.w, CFG, [])
        self.assertTrue(self.restarts.leaving(CFG))
        self.fresh(pid=222).started_up(self.w)
        self.assertEqual({self.props(one)["state"], self.props(two)["state"]}, {"done"})

    def test_refused_while_the_guard_sees_a_game(self):
        self.game = "the guard sees a game (full-screen Direct3D)"
        aid = self.ask()
        self.restarts.step(self.w, CFG, [])
        self.assertEqual(self.props(aid)["state"], "refused")
        self.assertIn("game", self.props(aid)["refused"])
        self.assertFalse(self.house.workshop.restart_wanted)

    def test_a_game_at_the_last_moment_refuses_and_stays(self):
        aid = self.ask()
        self.restarts.step(self.w, CFG, ["a9000"])
        self.game = "the guard sees a game (full-screen Direct3D)"
        self.assertFalse(self.restarts.leaving(CFG))
        self.assertEqual(self.props(aid)["state"], "refused")
        self.assertFalse(self.house.workshop.restart_wanted)
        self.fresh(pid=222).started_up(self.w)
        self.assertEqual(self.props(aid)["state"], "refused")        # no restart happened, none is reported

    def test_only_named_askers_with_a_reason(self):
        other = self.make(self.r.HOME, 'kind=note title="House restart asked" role=house-restart state=asked why=because',
                          who="pike")
        empty = self.ask(why="")
        self.restarts.step(self.w, CFG, [])
        self.assertEqual(self.props(other)["state"], "refused")
        self.assertIn("restart_by", self.props(other)["refused"])
        self.assertEqual(self.props(empty)["state"], "refused")
        self.assertFalse(self.house.workshop.restart_wanted)

    def test_without_the_keeper_nothing_would_start_it_again(self):
        aid = self.ask()
        self.restarts.step(self.w, CFG, [], keeper=False)
        self.assertEqual(self.props(aid)["state"], "refused")
        self.assertFalse(self.house.workshop.restart_wanted)

    def test_cancelled_while_draining_ends_the_drain(self):
        aid = self.ask()
        self.restarts.step(self.w, CFG, ["a9000"])
        self.run_line(f"look {aid}")
        self.run_line(f"do prop {aid} state=cancelled")
        self.restarts.step(self.w, CFG, ["a9000"])
        self.assertFalse(self.house.workshop.restart_wanted)
        self.assertFalse(self.restarts.owns)

    def test_a_landing_drain_is_not_undone_by_a_request(self):
        self.house.workshop.restart_wanted = True                    # a landing asked first
        self.ask()
        self.restarts.step(self.w, CFG, ["a9000"])
        self.assertFalse(self.restarts.owns)                         # so the landing's grace still applies
        self.assertTrue(self.restarts.leaving(CFG))                  # and the request rides its restart


class RunLoop(Base):
    """House.run itself, on the in-memory world: no model, keeper, guard or git call reaches anything real (the
    house's step, load, settings and act are the stand-ins; HOUSE_KEEPER is set only inside the test)."""

    def real_house(self, passes_busy, stop_after=None):
        import house as H
        h = H.House.__new__(H.House)
        h.world, h.fake, h.claude, h.claude_version = "inmemory", "stand-in", "", ""
        resident = SimpleNamespace(rid="a5191", busy=True, proc=None, stop=lambda: None)
        h.residents = {"a5191": resident}
        h.workshop = SimpleNamespace(restart_wanted=False, workers={}, landing={})
        h.another_house, h.load, h.settings = (lambda: None), (lambda: self.w), (lambda w: CFG)
        h.act = House(self.d).act
        self.passes = 0

        def step():
            self.passes += 1
            resident.busy = self.passes <= passes_busy
            if stop_after and self.passes > stop_after:
                raise KeyboardInterrupt
        h.step = step
        return h

    def run_house(self, h):
        import os
        from unittest.mock import patch
        import house as H
        with patch.dict(os.environ, {"HOUSE_KEEPER": "1"}), patch.object(H.time, "sleep", lambda s: None), \
                patch.object(H.house_restart, "game_seen", lambda nongame="": self.game):
            return h.run()

    def test_run_waits_for_the_busy_resident_then_exits_75_once(self):
        aid = self.ask()
        h = self.real_house(passes_busy=5)
        code = self.run_house(h)
        self.assertEqual(code, 75)
        self.assertEqual(self.passes, 6)                             # five passes waiting on the busy turn, never cut
        p = self.props(aid)
        self.assertEqual(p["state"], "restarting")
        said = [e for e in self.w.events if (e.get("args") or {}).get("in_flight") == "a5191"]   # said while it waited
        self.assertTrue(said)

    def test_run_a_game_at_the_last_moment_keeps_the_house_running(self):
        aid = self.ask()
        h = self.real_house(passes_busy=2, stop_after=6)

        def step():
            self.passes += 1
            h.residents["a5191"].busy = self.passes <= 2
            if self.passes == 2:
                self.game = "the guard sees a game (full-screen Direct3D)"
            if self.passes > 6:
                raise KeyboardInterrupt
        h.step = step
        code = self.run_house(h)
        self.assertEqual(code, 0)                                    # stopped by the test, not restarted
        self.assertEqual(self.props(aid)["state"], "refused")
        self.assertFalse(h.workshop.restart_wanted)


def _q(text):
    import json
    return json.dumps(text, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
