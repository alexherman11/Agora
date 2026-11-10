"""test_timed_rests (a8980, Alex 21 Oct): a resident's own timed rest wakes it when due; nothing else wakes on a timer.
# health: room test

    python test_timed_rests.py

Offline: an in-memory roomworld, a disposable state folder, a fake wall clock, the adapter's start/send/wake mocked;
process, socket and network creation refused. The real House.step, House.rest, House.settings and Resident (its
constructor and save) run. Written by codex-builder-2 against the staged candidate (research/timed-rests/); moved here
by builder-1 when the candidate was applied to house.py.
"""
import datetime
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace
import unittest
import uuid
from unittest.mock import Mock, patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"
os.environ.setdefault("HOUSE_CLAUDE", "claude")
import house  # noqa: E402
import roomworld  # noqa: E402

House, Resident = house.House, house.Resident


class TimedRests(unittest.TestCase):
    def setUp(self):
        self.tmp = HERE / (".timed-rest-fixture-" + uuid.uuid4().hex)
        self.tmp.mkdir()
        self.addCleanup(lambda: shutil.rmtree(self.tmp))
        for target in ("subprocess.Popen", "socket.socket", "urllib.request.urlopen"):
            guard = patch(target, side_effect=AssertionError("offline fixture only"))
            guard.start()
            self.addCleanup(guard.stop)
        self.at = 10000.
        clock = patch.object(house, "now", lambda: self.at)
        clock.start()
        self.addCleanup(clock.stop)
        self.d, refs = roomworld.build()
        self.w = self.d.world
        self.rid = refs.corner["pike"]
        self.corner = self.w.nodes[self.rid]
        self.corner["props"].update(actor="pike", role="resident", want="awake")
        self.h = object.__new__(House)
        self.h.dir, self.h.world, self.h.fake = self.tmp, "offline-rest-fixture", True
        self.h.load = lambda: self.w
        self.h.corners = lambda w: {self.rid: self.corner}
        self.cfg = dict(house.DEFAULTS)
        self.h.settings = lambda w: self.cfg
        self.h.record_knocks = lambda w, c: w
        self.h.toasts = Mock()
        self.h.act = Mock(return_value="fixture receipt")
        self.h.set_status = Mock()
        self.h.beat = Mock()
        self.h.plans = SimpleNamespace(wait_until=lambda p: 0, publish=lambda: None)
        self.h.workshop = SimpleNamespace(restart_wanted=False, step=Mock(), workers={})
        self.h.feeds = SimpleNamespace(step=Mock())
        self.h.usage = SimpleNamespace(step=Mock())
        self.h.scripts = SimpleNamespace(step=Mock())
        self.h.news = Mock(return_value=False)
        self.h.woken_by = Mock(return_value=[])
        self.h.take = Mock(return_value=["fixture call"])
        self.h.wake = Mock()
        self.h.residents = {}
        self.install_resident()
        self.events_before = len(self.w.events)

    def install_resident(self, restart=False):
        # the real constructor loads the saved rest and its deadline, from this fixture's folder only
        self.r = Resident(self.h, self.rid)
        if not restart:
            self.r.state.update(session="fixture", woke=1, cursor=len(self.w.events),
                                last_turn=self.at - 999999)
            self.r.save()
        self.running = not restart
        self.r.alive = lambda: self.running

        def start(model):
            self.running = True
        self.r.start = Mock(side_effect=start)
        self.r.stop = Mock()
        self.r.log = Mock()
        self.r.turns_ended = Mock(return_value=[])
        self.r.send = Mock()
        self.h.residents[self.rid] = self.r

    def step(self):
        with patch.dict(os.environ, {"HOUSE_KEEPER": ""}):
            self.h.step()
        self.assertEqual(len(self.w.events), self.events_before)

    def rest(self, seconds):
        self.h.rest(self.r, seconds, "fixture choice")
        self.h.act.reset_mock()

    def test_defaults_no_periodic_but_chosen_rest_enabled(self):
        self.assertEqual(self.cfg["timers"], "off")
        self.assertEqual(self.cfg["rest_wakes"], "on")

    def test_pending_deadline_visible_without_early_wake(self):
        self.rest(7200)
        self.at += 7199
        self.step()
        self.h.wake.assert_not_called()
        self.assertEqual(self.r.wakes_at, 17200)

    def test_deadline_wakes_exactly_once_and_removes_deadline(self):
        self.rest(7200)
        self.at += 7200
        self.step()
        self.h.wake.assert_called_once()
        self.assertIn("you rested 2 hours", self.h.wake.call_args.args[3])
        self.assertNotIn("rest_until", self.r.state)
        self.assertIsNone(self.r.wakes_at)
        self.step()
        self.h.wake.assert_called_once()
        self.assertIsNone(self.r.wakes_at)

    def test_until_clock_uses_same_persisted_deadline(self):
        seconds = house.until("until 13:00", datetime.datetime(2026, 10, 21, 11, 0))
        self.assertEqual(seconds, 7201)  # the existing until rounding, kept
        self.rest(seconds)
        self.at += seconds
        self.step()
        self.h.wake.assert_called_once()

    def test_untimed_rest_never_has_a_timer_wake(self):
        self.rest(0)
        self.at += 999999
        self.step()
        self.h.wake.assert_not_called()
        self.assertIsNone(self.r.wakes_at)

    def test_idle_never_wakes_for_wake_every(self):
        for _ in range(3):
            self.at += 999999
            self.step()
        self.h.wake.assert_not_called()
        self.assertIsNone(self.r.wakes_at)

    def test_open_objective_never_wakes_for_breather(self):
        self.w.subjects[next(iter(self.w.subjects))].setdefault("props", {})["objective"] = "open"
        self.at += 999999
        self.step()
        self.h.wake.assert_not_called()
        self.assertIsNone(self.r.wakes_at)

    def test_resume_after_sleep_handles_overdue_rest_next_pass(self):
        self.rest(60)
        # nothing runs in the gap: wall time jumping ahead is the PC suspended
        self.at += 8 * 3600
        self.h.wake.assert_not_called()
        self.step()
        self.h.wake.assert_called_once()

    def test_house_restart_preserves_pending_rest_from_saved_state(self):
        self.rest(7200)
        self.at += 30
        self.install_resident(restart=True)
        self.step()
        self.r.start.assert_called_once()  # the mocked adapter resumes; no model turn
        self.h.wake.assert_not_called()
        self.assertEqual(self.r.state["rest_until"], 17200)
        self.at = 17200
        self.step()
        self.h.wake.assert_called_once()

    def test_restart_after_deadline_keeps_rest_reason_even_legacy_state(self):
        self.rest(60)
        self.r.state.pop("at_rest")
        self.r.save()
        self.at += 100
        self.install_resident(restart=True)
        self.step()
        self.h.wake.assert_called_once()
        self.assertIn("you rested", self.h.wake.call_args.args[3])

    def test_busy_turn_never_interrupted_by_expired_rest(self):
        self.rest(60)
        self.r.busy = True
        self.at += 100
        self.step()
        self.h.wake.assert_not_called()
        self.r.busy = False
        self.step()
        self.h.wake.assert_called_once()

    def test_call_overrides_rest_and_clears_future_deadline(self):
        self.rest(7200)
        self.h.news.return_value = True
        self.step()
        self.r.send.assert_called_once()
        self.assertNotIn("rest_until", self.r.state)
        self.assertIsNone(self.r.wakes_at)
        self.h.news.return_value = False
        self.at += 7200
        self.step()
        self.h.wake.assert_not_called()

    def test_explicit_off_stays_off_even_after_deadline(self):
        self.rest(60)
        self.corner["props"]["want"] = "rest"
        self.at += 100
        self.step()
        self.h.wake.assert_not_called()
        self.r.send.assert_not_called()

    def test_rest_wakes_off_preserves_deadline_without_periodic_fallback(self):
        self.rest(60)
        self.cfg.update(rest_wakes="off", timers="on")
        self.at += 100000
        self.step()
        self.h.wake.assert_not_called()
        self.assertIsNone(self.r.wakes_at)
        self.cfg["rest_wakes"] = "on"
        self.step()
        self.h.wake.assert_called_once()

    def test_settings_reads_separate_world_props(self):
        # the existing world-owned settings (The house's props), not a store of its own
        for line in (f"look {self.w.root} :1",
                     f'do create {self.w.root} kind=note title="The house" timers=off rest_wakes=off'):
            out = self.d.dispatch("desk", {"line": line, "whole": True})
            self.assertFalse(out.get("error"), out)
            self.assertNotIn("ERR", out.get("text", ""), out)
        actual = House.settings(self.h, self.w)
        self.assertEqual(actual["timers"], "off")
        self.assertEqual(actual["rest_wakes"], "off")

    def test_no_os_wake_timer_in_the_house(self):
        src = Path(house.__file__).read_text(encoding="utf-8")
        for word in ("SetWaitableTimer", "CreateWaitableTimer", "SetThreadExecutionState", "powercfg"):
            self.assertNotIn(word, src)


if __name__ == "__main__":
    unittest.main(verbosity=1)
