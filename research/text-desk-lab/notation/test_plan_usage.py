# health: room test
"""Fake quota feed, real native facts; no browser, credentials or model calls."""
import json
import copy
import os
import queue
import sys
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

os.environ["DESKD"] = "off"
os.environ.setdefault("HOUSE_CLAUDE", "claude")
import roomworld
import house
import workshop
import plan_usage
import scene

RESOURCES = Path(__file__).resolve().parents[2] / "window-lab" / "plan-usage"
FILES = {p.name: p.read_text(encoding="utf-8") for p in RESOURCES.glob("*") if p.suffix in (".lens", ".style")}


def claude(percent, reset=2000, week=20):
    return {"type": "rate_limit_event", "rate_limit_info": {"unifiedWindows": {
        "five_hour": {"utilization": percent / 100, "resetsAt": reset},
        "seven_day": {"utilization": week / 100, "resetsAt": 9000}}}}


class Quotas(unittest.TestCase):
    def setUp(self):
        self.now = 1000
        self.saved = {}
        self.atomic = patch.object(workshop, "atomic_state", side_effect=self.persist).start()
        self.addCleanup(patch.stopall)
        self.d, self.r = roomworld.build(say=False)
        self.w = self.d.world
        self.h = SimpleNamespace(dir=Path("fake-house"), load=lambda: self.w, act=self.act)
        self.calls = []
        with patch.object(Path, "read_text", side_effect=FileNotFoundError):
            self.p = plan_usage.Plans(self.h, clock=lambda: self.now)
        self.h.plans = self.p
        self.act("house", f'look {self.w.root}; do create {self.w.root} kind=chat '
                 'title="Notifications sent" role=notifications members=all')
        self.act("house", f'look {self.w.root}; do create {self.w.root} kind=note '
                 'title=notify tags=verb on=house text=' +
                 plan_usage.q('do append prop:role=notifications line="$*"'))
        self.act("house", f'look {self.w.root}; do create {self.w.root} kind=task title="First"')
        self.card = next(s["id"] for s in self.w.subjects.values() if s["title"] == "First")

    def persist(self, path, state):
        self.saved[str(path)] = json.loads(json.dumps(state))

    def act(self, who, line):
        from desk import split_batch
        self.calls.append(line)
        self.w.me = who
        for part in split_batch(line):
            result = self.d.dispatch("desk", {"line": part, "whole": True})
            if result.get("error") or (result.get("text") or "").startswith(("MISS ", "ERR ")):
                self.fail(f"{part}: {result.get('error') or result.get('text')}")
        return result.get("text", "")

    def codex_read(self, percent=11, reset=9000):
        return {"type": "codex_event", "method": "account/rateLimits/read", "data": {
            "rateLimitsByLimitId": {"codex": {"primary": {
                "usedPercent": percent, "resetsAt": reset, "windowDurationMins": 10080}}}}}

    def hold_codex(self):
        self.p.observe(self.codex_read(100))
        self.p.paused("codex", self.card, 9060)

    def test_fresh_quota_read_reconciles_hold_without_claiming_task_recovery(self):
        self.hold_codex()
        before = copy.deepcopy(self.p.state["pauses"]["codex"])
        self.p.observe(self.codex_read())
        after = self.p.state["pauses"]["codex"]
        self.assertEqual(self.p.wait_until("codex"), 0)
        self.assertEqual(after["targets"], before["targets"])
        self.assertEqual(after["notices"], before["notices"])
        self.assertFalse(after["resumed"])
        self.assertEqual(after["quota_reconciled"]["previous_retry_at"], 9060)

    def test_incomplete_stale_notification_exhausted_or_invalid_read_stays_held(self):
        for kind in ["partial", "stale", "notification", "exhausted", "invalid", "expired"]:
            with self.subTest(kind=kind):
                self.hold_codex()
                event = self.codex_read()
                at = self.now
                if kind == "partial":
                    event["data"] = {}
                elif kind == "stale":
                    at -= 1
                elif kind == "notification":
                    event["method"] = "account/rateLimits/updated"
                elif kind == "exhausted":
                    event = self.codex_read(100)
                elif kind == "invalid":
                    event = self.codex_read(-1)
                elif kind == "expired":
                    event = self.codex_read(reset=999)
                self.p.observe(event, at=at)
                self.assertEqual(self.p.wait_until("codex"), 9060)

    def test_an_unreported_exhausted_window_keeps_the_hold(self):
        self.hold_codex()
        old = copy.deepcopy(self.p.state["windows"]["codex_codex_primary"])
        self.p.state["windows"]["codex_other_primary"] = old
        self.p.observe(self.codex_read())
        self.assertEqual(self.p.wait_until("codex"), 9060)

    def test_startup_read_is_bounded_once_and_only_for_a_hold(self):
        run = Mock(return_value=SimpleNamespace(returncode=0, stdout=json.dumps(self.codex_read())))
        self.assertFalse(self.p.refresh_held_codex(run))
        run.assert_not_called()
        self.hold_codex()
        self.assertTrue(self.p.refresh_held_codex(run))
        run.assert_called_once()
        self.assertEqual(run.call_args.kwargs["timeout"], 15)
        self.assertIn("read_plan_usage.py", run.call_args.args[0][-1])
        self.assertFalse(self.p.refresh_held_codex(run))
        run.assert_called_once()

    def test_startup_read_unknown_results_preserve_hold(self):
        import subprocess
        cases = [SimpleNamespace(returncode=1, stdout=""),
                 SimpleNamespace(returncode=0, stdout="bad json"),
                 SimpleNamespace(returncode=0, stdout='{"type":"plan_usage_unavailable"}'),
                 SimpleNamespace(returncode=0, stdout="x" * 65537),
                 subprocess.TimeoutExpired("quota", 15), PermissionError("denied")]
        for result in cases:
            with self.subTest(result=type(result).__name__):
                self.hold_codex()
                run = (Mock(side_effect=result) if isinstance(result, Exception)
                       else Mock(return_value=result))
                self.assertFalse(self.p.refresh_held_codex(run))
                self.assertEqual(self.p.wait_until("codex"), 9060)

    def test_threshold_crossings_and_expiry(self):
        self.p.observe(claude(69))
        cfg = {"claude_start_threshold": "70"}
        self.assertFalse(self.p.fuel_reason("claude", cfg))
        self.p.observe(claude(70))
        self.assertIn("Queued", self.p.fuel_reason("claude", cfg))
        self.assertFalse(self.p.fuel_reason("codex", cfg))
        self.assertFalse(self.p.fuel_reason("claude", {}))
        self.p.observe(claude(68))
        self.assertFalse(self.p.fuel_reason("claude", cfg))
        self.p.observe(claude(95))
        self.now = 2001
        self.assertFalse(self.p.fuel_reason("claude", cfg))

    def test_native_usage_and_expired_unknown(self):
        self.p.observe(claude(13))
        self.p.publish()
        rows = [s for s in self.w.subjects.values() if (s.get("props") or {}).get("role") == "usage-window"]
        self.assertEqual(len(rows), 3)
        five = next(s for s in rows if s["props"]["usage_key"] == "claude_five_hour")
        self.assertEqual(str(five["props"]["percent"]), "13.0")
        self.assertIn("Source: Claude CLI", five["text"])
        self.assertTrue(any("unavailable" in s["text"] and "Codex" in s["text"] for s in rows))
        self.now = 2001
        self.p.publish()
        self.assertIn("unavailable", five["text"])
        self.assertEqual(five["props"]["percent"], "")

    def test_context_is_not_plan_and_codex_windows(self):
        self.p.observe({"type": "codex_event", "method": "thread/tokenUsage/updated",
                        "data": {"tokenUsage": {"last": {"totalTokens": 200000}}}})
        self.assertFalse(self.p.state["windows"])
        event = {"type": "codex_event", "method": "account/rateLimits/read", "data": {
            "rateLimitsByLimitId": {"codex": {"primary": {"usedPercent": 72, "windowDurationMins": 300,
                                                       "resetsAt": 3000},
                                             "secondary": {"usedPercent": 9, "windowDurationMins": 10080,
                                                           "resetsAt": 10000}}}}}
        self.p.observe(event)
        self.assertEqual([r["percent"] for r in self.p.current("codex")], [72, 9])
        self.assertEqual([r["label"] for r in self.p.current("codex")], ["5 hours", "7 days"])

    def test_pause_two_cards_two_providers_restart_dedup(self):
        self.act("house", f'look {self.w.root}; do create {self.w.root} kind=task title="Second"')
        other = next(s["id"] for s in self.w.subjects.values() if s["title"] == "Second")
        self.p.paused("claude", self.card, 2060)
        self.p.paused("claude", other, 2060)
        self.p.paused("codex", other, 3060)
        self.assertEqual(sum(line.startswith("notify ") for line in self.calls), 2)
        state = json.dumps(self.p.state)
        with patch.object(Path, "read_text", return_value=state):
            self.p = plan_usage.Plans(self.h, clock=lambda: self.now)
        self.p.paused("claude", self.card, 2060)
        self.assertEqual(sum(line.startswith("notify ") for line in self.calls), 2)
        self.assertIn("Paused until", self.w.subjects[self.card]["props"]["usage_state"])
        self.now = 2060
        self.p.resumed("claude", self.card)
        self.p.resumed("claude", self.card)
        self.assertEqual(sum(line.startswith("notify ") for line in self.calls), 3)
        self.now = 3060
        self.p.resumed("codex", other)
        self.assertEqual(sum(line.startswith("notify ") for line in self.calls), 4)
        self.assertEqual(self.w.subjects[self.card]["props"]["usage_state"], "")

    def test_real_resident_failure_preserves_delivered_pending(self):
        r = house.Resident.__new__(house.Resident)
        r.rid, r.house = self.card, self.h
        r.state = {"session": "kept", "session_provider": "claude",
                   "pending": {"delivered": True, "carry": "the question", "kind": "news"}}
        r.failed, r.save, r.log = False, Mock(), Mock()
        r.alive, r.lost_conversation = lambda: False, lambda: False
        self.h.set_status = Mock()
        self.p.observe(claude(100))
        with patch.object(house, "limit_reset", return_value=None), patch.object(house, "now", return_value=1000):
            house.House.failed(self.h, r, {}, {"detail": "usage limit reached"})
        self.assertEqual(r.state["retry_at"], 2060)
        self.assertEqual(r.state["retry_kind"], "limit")
        self.assertEqual(r.state["unanswered"], 1)
        self.assertNotIn("undelivered", r.state)
        self.assertEqual(r.state["session"], "kept")
        self.h.set_status.assert_called_with(r, {}, "paused")

    def test_repeated_limit_keeps_other_pending_targets(self):
        self.act("house", f'look {self.w.root}; do create {self.w.root} kind=task title="Second"')
        other = next(s["id"] for s in self.w.subjects.values() if s["title"] == "Second")
        self.p.paused("claude", self.card, 2060)
        self.p.paused("claude", other, 2060)
        self.now = 2060
        self.p.resumed("claude", self.card)
        self.p.paused("claude", self.card, 3060)
        self.assertEqual(set(self.p.state["pauses"]["claude"]["targets"]), {self.card, other})
        self.assertIn("Paused until", self.w.subjects[other]["props"]["usage_state"])
        self.now = 3060
        self.p.resumed("claude", other)
        self.assertEqual(self.w.subjects[other]["props"]["usage_state"], "")
        self.assertEqual(sum(line.startswith("notify ") for line in self.calls), 2)

    def test_worker_limit_keeps_work_and_provider_cooldown(self):
        wk = SimpleNamespace(state={"session": "kept", "session_provider": "claude"}, stop=Mock(), save=Mock())
        shop = workshop.Workshop.__new__(workshop.Workshop)
        shop.house, shop.workers, shop.say = self.h, {self.card: wk}, Mock()
        self.p.observe(claude(100))
        with patch.object(workshop, "limit_reset", return_value=None):
            workshop.Workshop.failed(shop, self.card, wk, {"detail": "usage limit"})
        self.assertEqual(wk.state["retry_at"], 2060)
        self.assertEqual(wk.state["session"], "kept")
        self.assertNotIn("failures", wk.state)
        self.assertIn("Paused until", self.w.subjects[self.card]["props"]["usage_state"])

    def test_reset_margin_and_result_hook_confirm_resume(self):
        self.p.observe(claude(100))
        self.p.paused("claude", self.card, self.p.reset("claude") + 60)
        self.now = 2059
        self.assertGreater(self.p.wait_until("claude"), self.now)
        self.now = 2060
        self.assertLessEqual(self.p.wait_until("claude"), self.now)
        r = house.Resident.__new__(house.Resident)
        r.rid, r.house = self.card, self.h
        r.state = {"session_provider": "claude", "pending": {"delivered": True}, "retry_kind": "limit"}
        r.save, r.log, r.reply = Mock(), Mock(), []
        r.events = queue.Queue()
        r.events.put({"type": "result", "is_error": True, "result": "usage limit"})
        house.Resident.turns_ended(r)
        self.assertEqual(sum(line.startswith("notify ") for line in self.calls), 1)
        self.p.restarting(self.card)
        self.assertEqual(self.w.subjects[self.card]["props"]["usage_state"], "Resuming")
        r.events.put({"type": "result", "is_error": False})
        self.assertEqual(house.Resident.turns_ended(r), [""])
        self.assertEqual(sum(line.startswith("notify ") for line in self.calls), 2)
        self.assertEqual(self.w.subjects[self.card]["props"]["usage_state"], "")
        self.assertNotIn("retry_kind", r.state)

    def test_worker_resume_runs_only_after_reset_margin(self):
        self.h.world = "inmemory"
        wk = SimpleNamespace(state={"session": "kept", "retry_at": 2060,
                                    "pending": {"carry": "pending lines"}},
                             start=Mock(), log=Mock(), builder=None)
        shop = workshop.Workshop.__new__(workshop.Workshop)
        shop.house, shop.workers = self.h, {}
        shop.real_tree, shop.asked_by = lambda *a: True, lambda *a: "jeff"
        shop.provider_of, shop.provider_wait = lambda *a: "claude", lambda *a: 2060
        shop.carry_on = Mock()
        with patch.object(workshop, "Worker", return_value=wk), patch.object(workshop.time, "time", return_value=2059):
            self.assertIsNone(shop.resume(self.w, self.card, {"props": {}}, {"model": "fake"}))
        wk.start.assert_not_called()
        with patch.object(workshop, "Worker", return_value=wk), patch.object(workshop.time, "time", return_value=2060):
            self.assertIs(shop.resume(self.w, self.card, {"props": {}}, {"model": "fake"}), wk)
        wk.start.assert_called_once()
        shop.carry_on.assert_called_once()
        self.assertEqual(wk.state["pending"]["carry"], "pending lines")

    def test_failed_publication_cannot_drop_completed_turn(self):
        r = house.Resident.__new__(house.Resident)
        r.rid, r.house, r.reply = self.card, self.h, ["the answer"]
        r.state, r.save, r.log = {}, Mock(), Mock()
        r.events = queue.Queue()
        r.events.put({"type": "result", "is_error": False})
        with patch.object(self.p, "publish", side_effect=RuntimeError("desk not ready")):
            self.assertEqual(house.Resident.turns_ended(r), ["the answer"])
        self.assertEqual(r.state["turns"], 1)

    def test_notice_recovers_lost_ack_without_duplicate_append(self):
        self.p.paused("claude", self.card, 2060)
        entry = self.p.state["pauses"]["claude"]
        self.assertTrue(entry["notices"][0]["sent"])
        entry["notices"][0]["sent"] = False  # crash after world append, before state acknowledgement
        with patch.object(Path, "read_text", return_value=json.dumps(self.p.state)):
            restarted = plan_usage.Plans(self.h, clock=lambda: self.now)
        before = len(self.calls)
        restarted.flush_notices()
        self.assertEqual(len(self.calls), before)
        self.assertTrue(restarted.state["pauses"]["claude"]["notices"][0]["sent"])

    def test_notice_unknown_delivery_does_not_blindly_retry(self):
        real_act = self.h.act
        def refused(who, line):
            if line.startswith("notify "):
                return "ERR temporarily unavailable"
            return real_act(who, line)
        self.h.act = refused
        self.p.paused("claude", self.card, 2060)
        self.assertFalse(self.p.state["pauses"]["claude"]["notices"][0]["sent"])
        self.h.act = real_act
        self.p.flush_notices()
        notice = self.p.state["pauses"]["claude"]["notices"][0]
        self.assertFalse(notice["sent"])
        self.assertEqual(notice["delivery"], "unknown")
        self.assertEqual(sum(line.startswith("notify ") for line in self.calls), 0)

    def test_stale_snapshot_three_flushes_append_once(self):
        # Production House.load keys its cache by pickle mtime. The writer can
        # acknowledge a logged append before its background pickle changes.
        stale = copy.deepcopy(self.w)
        reader = house.House.__new__(house.House)
        reader.world, reader.mtime, reader.desk = "inmemory", 12, SimpleNamespace(world=stale)
        fake_path = MagicMock()
        fake_path.__truediv__.return_value = fake_path
        fake_path.stat.return_value.st_mtime = 12
        self.h.load = reader.load
        with patch.object(house, "HERE", fake_path), patch.object(house.export_docs, "load") as reload:
            self.p.paused("claude", self.card, 2060)
            self.p.flush_notices()
            self.p.flush_notices()
            reload.assert_not_called()
        sent = next(s for s in self.w.subjects.values()
                    if s.get("props", {}).get("role") == "notifications")
        self.assertEqual(len(sent["lines"]), 1)
        notice = self.p.state["pauses"]["claude"]["notices"][0]
        self.assertTrue(notice["sent"])
        self.assertRegex(notice["receipt"], r"e\d+")
        with patch.object(Path, "read_text", return_value=json.dumps(self.p.state)):
            restarted = plan_usage.Plans(self.h, clock=lambda: self.now)
        with patch.object(house, "HERE", fake_path):
            restarted.flush_notices()
        self.assertEqual(len(sent["lines"]), 1)

    def test_resume_result_and_publications_preserve_historical_line(self):
        self.p.paused("claude", self.card, 2060)
        sent = next(s for s in self.w.subjects.values()
                    if s.get("props", {}).get("role") == "notifications")
        historical = copy.deepcopy(sent["lines"])
        stale = copy.deepcopy(self.w)
        self.h.load = lambda: stale
        self.now = 2060
        r = house.Resident.__new__(house.Resident)
        r.rid, r.house, r.reply = self.card, self.h, []
        r.state = {"session_provider": "codex", "pending": {"delivered": True}, "retry_kind": "limit"}
        r.save, r.log, r.events = Mock(), Mock(), queue.Queue()
        r.events.put({"type": "result", "is_error": False})
        self.assertEqual(house.Resident.turns_ended(r), [""])
        self.p.publish()  # the end-of-step publication after the turn publication
        self.assertEqual(len(sent["lines"]), 2)
        self.assertEqual(sent["lines"][:1], historical)
        self.assertIn("work resumed with Codex", sent["lines"][-1]["text"])

    def test_lost_ack_stale_snapshot_restart_reconciles_without_resend(self):
        stale = copy.deepcopy(self.w)
        self.h.load = lambda: stale
        act = self.h.act
        def lost(who, line):
            result = act(who, line)
            if line.startswith("notify "):
                raise TimeoutError("response lost after commit")
            return result
        self.h.act = lost
        self.p.paused("claude", self.card, 2060)
        self.h.act = act
        with patch.object(Path, "read_text", return_value=json.dumps(self.p.state)):
            restarted = plan_usage.Plans(self.h, clock=lambda: self.now)
        restarted.flush_notices()
        self.assertFalse(restarted.state["pauses"]["claude"]["notices"][0]["sent"])
        self.h.load = lambda: self.w
        restarted.flush_notices()
        self.assertTrue(restarted.state["pauses"]["claude"]["notices"][0]["sent"])
        self.assertEqual(sum(line.startswith("notify ") for line in self.calls), 1)

    def test_pool_uses_other_lane_at_threshold(self):
        shop = workshop.Workshop.__new__(workshop.Workshop)
        shop.house = self.h
        shop.provider_of = lambda *args: None
        shop.provider_wait = lambda *args: 0
        self.p.observe(claude(91))
        cfg = {"worker_pool": "2 claude, 2 codex", "claude_start_threshold": "90"}
        self.assertEqual(shop.lane(self.card, {}, cfg, [])["provider"], "codex")
        shop.saved_provider = lambda *args: "claude"
        self.assertIs(shop.lane(self.card, {}, cfg, []), False)

    def test_gauge_scene_and_threshold_settings(self):
        self.p.observe(claude(91))
        self.p.publish()
        self.act("house", f'look {self.w.root}; do create {self.w.root} kind=note '
                 'title="My viewer" role=home-view actor=house')
        self.act("house", f'look {self.w.root}; do create {self.w.root} kind=note '
                 'title="The house" role=house-settings model=fake')
        for name, text in FILES.items():
            title = "plan-usage-style" if name.endswith(".style") else name[:-5]
            tags = "style" if name.endswith(".style") else "lens"
            props = "" if tags == "style" else "style=plan-usage-style"
            self.act("house", f'look {self.w.root}; do create {self.w.root} kind=note '
                     f'title={plan_usage.q(title)} tags={tags} {props} text={plan_usage.q(text)}')
        for title in ("home-usage", "plan-usage-reader", "plan-usage-glance"):
            sc, text = scene.scene_for(self.d, title)
            self.assertEqual(sc["def"]["status"], "current")
            self.assertNotIn("ERR", text)
            if title == "home-usage":
                encoded = json.dumps(sc)
                self.assertIn("pufill.red", encoded)
                self.assertIn("Claude 91%", encoded)
                self.assertIn("Codex unavailable", encoded)
            if title == "plan-usage-reader":
                self.assertIn("90%", text)
        # Inspect evaluated roles, not just role names in the style definition.
        # At 90% both predicates match; the first conditional role must win.
        def walk(node):
            yield node
            for child in node.get("kids", []):
                yield from walk(child)
        for percent, expected in ((69, "pufill"), (70, "pufill.amber"),
                                  (89, "pufill.amber"), (90, "pufill.red"),
                                  (100, "pufill.red")):
            self.p.observe(claude(percent))
            self.p.publish()
            sc, _ = scene.scene_for(self.d, "home-usage")
            fills = [n["role"] for n in walk(sc)
                     if n.get("part") == "used" and not n.get("absent")]
            self.assertEqual(fills, [expected, "pufill"], (percent, fills))

    def test_codex_adapter_sanitizes_account_metadata(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "codex-residents"))
        from codex_resident import emit_plan_usage
        response = SimpleNamespace(model_dump=lambda **kwargs: {
            "rateLimits": {"limitId": "codex", "credits": {"secret": "excluded"},
                           "primary": {"usedPercent": 71, "resetsAt": 3000, "windowDurationMins": 300}},
            "account": "excluded"})
        client, emitted = Mock(), []
        client.request.return_value = response
        emit_plan_usage(client, emitted.append)
        self.assertEqual(client.request.call_args.args, ("account/rateLimits/read", None))
        self.assertNotIn("excluded", json.dumps(emitted))
        self.assertEqual(plan_usage.readings(emitted[0], 1000)[0]["percent"], 71)
        client.request.side_effect = RuntimeError("excluded credential detail")
        emit_plan_usage(client, emitted.append)
        self.assertEqual(emitted[-1]["type"], "plan_usage_unavailable")
        self.assertNotIn("excluded", json.dumps(emitted))

    def test_codex_quota_read_cannot_block_or_accumulate_requests(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "codex-residents"))
        from codex_resident import emit_plan_usage
        release, entered = threading.Event(), threading.Event()
        def slow_read(*args, **kwargs):
            entered.set()
            release.wait()
            raise RuntimeError("unavailable")
        client, emitted = Mock(), []
        client.request.side_effect = slow_read
        try:
            emit_plan_usage(client, emitted.append, timeout=0.01)
            self.assertTrue(entered.is_set())
            self.assertEqual(emitted[-1]["type"], "plan_usage_unavailable")
            emit_plan_usage(client, emitted.append, timeout=0.01)
            client.request.assert_called_once()
        finally:
            release.set()
            client._agora_usage_job.join(1)


if __name__ == "__main__":
    unittest.main()
