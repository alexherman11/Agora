# health: room test
"""Offline engine/actual patched Desk and House tests; no runtime or sessions loaded."""
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "desktop"))
os.environ["DESKD"] = "off"
os.environ.setdefault("HOUSE_CLAUDE", "claude")
import agora_tmp
import followups
import house
import desk
import roomworld

STAGE = HERE.parents[1] / "followups" / "staging.py"
loader = importlib.util.spec_from_file_location("followup_staging", STAGE)
staging = importlib.util.module_from_spec(loader)
loader.loader.exec_module(staging)
SOURCES = staging.texts()


def patched(module, relative):
    """Compile exact reviewed whole-file hunks, preserving real dispatch code."""
    ns = dict(module.__dict__, __name__="followup_test_" + module.__name__)
    exec(compile(SOURCES[relative], str(staging.ROOT / relative), "exec"), ns)
    return SimpleNamespace(**ns)


PATCHED_DESK = patched(desk, staging.LAB + "desk.py")
PATCHED_HOUSE = patched(house, staging.LAB + "house.py")


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(agora_tmp.directory("followups-test-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))
        self.d, self.r = roomworld.build()
        self.w = self.d.world
        self.target = self.r.NOTE
        self.s = followups.subject(self.w, self.target)
        self.clock = 0.
        self.f = followups.Followups(self.tmp / "followups.json", lambda: self.clock)
        self.send = []
        self.f.observe(self.w)
        # Use the real Desk command parser/mutation path, not a fake prop backend.
        self.patcher = patch.object(desk.Desk, "repl", PATCHED_DESK.Desk.repl)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        for name in ("subprocess.Popen", "urllib.request.urlopen", "socket.socket"):
            guard = patch(name, side_effect=AssertionError("offline test attempted " + name))
            guard.start()
            self.addCleanup(guard.stop)

    def act(self, line, who="jeff"):
        self.w.me = who
        self.d.cmd_read(self.target, full=True)
        r = self.d.dispatch("desk", {"line": line, "whole": True, "reply": uuid.uuid4().hex})
        return (r.get("text") or "") + (r.get("error") or "")

    def attach(self, key="one", recipient="pike", seconds=10, observe=True):
        p = dict(key=key, revision=self.s["rev"], recipient=recipient,
                 next_action="Review the delivery; route a capability blocker if necessary",
                 source=self.w.events[-1]["id"], awake_seconds=seconds,
                 when=[dict(field="commission", values=["landed", "failed"], kind="completion"),
                       dict(field="usage_state", values=[], kind="quota"),
                       dict(field="capability_state", values=["available"], kind="capability")])
        result = self.act(f"followups attach {self.target} '{json.dumps(p)}'")
        self.assertIn("ok ", result, result)
        if not observe:
            return p
        self.f.observe(self.w)
        self.assertFalse(self.f.state["refused"], self.f.state["refused"])
        return next(o for o in self.f.state["obligations"].values() if o["key"] == key)

    def prop(self, **values):
        text = " ".join(k + "=" + json.dumps(v) for k, v in values.items())
        self.assertIn("ok ", self.act("do prop " + self.target + " " + text))
        e = self.w.events[-1]["id"]
        self.f.observe(self.w)
        return e

    def resident(self, name="pike", busy=False, write="yes"):
        rid = self.r.corner[name]
        r = object.__new__(house.Resident)
        r.rid, r.house, r.dir = rid, SimpleNamespace(load=lambda: self.w, plans=None), self.tmp
        r.state_path, r.state = self.tmp / (name + ".json"), {"session": "fixture"}
        r.busy, r.reply, r.failed = busy, [], False
        r.proc = SimpleNamespace(stdin=io.StringIO(), poll=lambda: None)
        r.log = lambda *a: None
        original = r.send

        def send(*args):
            self.send.append(args)
            if write == "crash":
                raise RuntimeError("fake broken pipe")
            original(*args)  # actual Resident.send writes the fixture pipe and durable pending
        r.send = send
        return r

    def receipt(self):
        return list(self.f.state["receipts"].values())[-1]

    def ack(self, row=None, who="pike"):
        row = row or self.receipt()
        result = self.act(f"followups ack {self.target} '{json.dumps({'receipt': row['id']})}'", who)
        self.assertIn("ok ", result)
        self.f.observe(self.w)

    def test_busy_coalesces_exact_facts_and_no_duplicate(self):
        o = self.attach()
        r = self.resident(busy=True)
        a = self.prop(commission="landed")
        self.f.dispatch(self.w, {r.rid: r})
        b = self.prop(usage_state="quota blocked")
        self.f.dispatch(self.w, {r.rid: r})
        self.f.observe(self.w)
        self.assertEqual([], self.send)
        self.assertEqual([a, b], [f["event"] for f in o["facts"]])
        self.assertIn("coalesced", [x["state"] for x in self.f.state["receipts"].values()])
        r.busy = False
        self.f.dispatch(self.w, {r.rid: r})
        self.f.dispatch(self.w, {r.rid: r})
        self.assertEqual(1, len(self.send))
        self.assertEqual("pipe-written", self.receipt()["state"])
        for event in (a, b):
            self.assertIn(event, self.send[0][0])
        self.assertFalse(o["settled"])

    def test_rest_and_disabled_resident(self):
        self.attach()
        r = self.resident()
        r.state["at_rest"] = True
        self.prop(commission="failed")
        props = self.w.nodes[r.rid]["props"]
        props["want"] = "rest"
        self.f.dispatch(self.w, {r.rid: r})
        self.assertFalse(self.send)
        props["want"] = "awake"
        self.f.dispatch(self.w, {r.rid: r})
        self.assertEqual(1, len(self.send))
        self.assertNotIn("at_rest", r.state)

    def test_restart_recovers_queue_without_offline_time(self):
        self.attach()
        self.prop(commission="landed")
        self.f.dispatch(self.w, {})
        self.clock = 9000
        f = followups.Followups(self.f.path, lambda: self.clock)
        f.observe(self.w)
        self.assertEqual(0, f.state["awake"])
        r = self.resident()
        f.dispatch(self.w, {r.rid: r})
        self.assertEqual(1, len(self.send))
        f = followups.Followups(self.f.path, lambda: self.clock)
        f.observe(self.w)
        f.dispatch(self.w, {r.rid: r})
        self.assertEqual(1, len(self.send))

    def test_unknown_write_and_crash_never_blindly_replay(self):
        self.attach()
        r = self.resident(write="crash")
        self.prop(commission="failed")
        self.f.dispatch(self.w, {r.rid: r})
        self.assertEqual("unknown", self.receipt()["state"])
        self.f.dispatch(self.w, {r.rid: r})
        self.assertEqual(1, len(self.send))
        self.receipt()["state"] = "attempted"
        self.f.save()
        f = followups.Followups(self.f.path, lambda: self.clock)
        self.assertEqual("unknown", list(f.state["receipts"].values())[-1]["state"])
        f.dispatch(self.w, {r.rid: r})
        self.assertEqual(1, len(self.send))

    def test_deadline_once_escalates_unavailable_handoff(self):
        o = self.attach(recipient="codex")
        self.prop(commission="failed")
        self.f.dispatch(self.w, {})
        self.clock = 9
        self.f.observe(self.w)
        self.assertFalse(o["deadline_fired"])
        self.clock = 10
        self.f.observe(self.w)
        self.assertTrue(o["deadline_fired"])
        # Owner stands in the existing pike corner, no process/model started.
        r = self.resident()
        self.w.nodes[r.rid]["props"]["actor"] = "jeff"
        self.f.dispatch(self.w, {r.rid: r})
        self.assertEqual("jeff", self.receipt()["recipient"])
        self.assertEqual(2, len(self.receipt()["facts"]))
        for n in range(20, 200, 10):
            self.clock = n
            self.f.observe(self.w)
            self.f.dispatch(self.w, {r.rid: r})
        self.assertEqual(1, len(self.send))

    def test_ack_settles_only_obligation_not_work_or_other_obligation(self):
        one = self.attach()
        two = self.attach(key="two")
        self.prop(commission="landed")
        r = self.resident()
        self.f.dispatch(self.w, {r.rid: r})
        first = next(x for x in self.f.state["receipts"].values() if x["obligation"] == one["id"])
        self.ack(first)
        self.assertTrue(one["settled"])
        self.assertFalse(two["settled"])
        self.assertEqual("unverified", one["work_state"])
        self.assertEqual("landed", self.s["props"]["commission"])

    def test_old_ack_does_not_swallow_new_fact_and_forged_ack_refused(self):
        o = self.attach()
        self.prop(commission="landed")
        r = self.resident()
        self.f.dispatch(self.w, {r.rid: r})
        first = self.receipt()
        self.prop(usage_state="blocked")
        self.ack(first, who="sable")
        self.assertEqual("pipe-written", first["state"])
        self.assertTrue(self.f.state["refused"])
        self.ack(first)
        self.assertFalse(o["settled"])

    def test_stale_revision_and_nonissuer_and_invalid_contract(self):
        p = dict(key="stale", revision=1, recipient="pike", next_action="read",
                 source=self.w.events[-1]["id"], awake_seconds=10,
                 when=[dict(field="commission", values=[], kind="completion")])
        p["revision"] = self.s["rev"] + 1
        n = len(self.w.events)
        self.assertIn("stale", self.act(f"followups attach {self.target} '{json.dumps(p)}'"))
        self.assertEqual(n, len(self.w.events))
        p["revision"] = self.s["rev"]
        self.assertIn("only JEFF", self.act(f"followups attach {self.target} '{json.dumps(p)}'", "pike"))
        p["awake_seconds"] = float("inf")
        self.assertIn("finite", self.act(f"followups attach {self.target} '{json.dumps(p)}'"))

    def test_attach_then_transition_before_poll_and_repeated_state(self):
        self.attach(observe=False)
        self.prop(usage_state="blocked")
        o = next(iter(self.f.state["obligations"].values()))
        self.assertEqual(1, len(o["facts"]))
        self.f.observe(self.w)
        self.assertEqual(1, len(o["facts"]))
        self.assertNotEqual(o["revision"], self.s["rev"])

    def test_pause_clock_never_counts_stopped_runtime(self):
        o = self.attach()
        self.clock = 5
        self.f.observe(self.w)
        self.f.observe(self.w, running=False)
        self.clock = 5000
        self.f.observe(self.w)
        self.assertFalse(o["deadline_fired"])
        self.clock = 5005
        self.f.observe(self.w)
        self.assertTrue(o["deadline_fired"])

    def test_read_only_pending_and_receipts_uses_actual_desk_parser(self):
        self.attach()
        self.prop(capability_state="available")
        self.f.dispatch(self.w, {})
        base = self.tmp / "house-state" / "roomworld-inmemory"
        base.mkdir(parents=True)
        (base / "followups.json").write_text(json.dumps(self.f.state), encoding="utf-8")
        n, snapshot = len(self.w.events), copy.deepcopy(self.w.subjects)
        with patch.object(followups, "HERE", self.tmp):
            self.assertIn("next_action", self.act("followups pending"))
            self.assertIn("queued", self.act("followups receipts"))
            self.assertEqual([], json.loads(self.act("followups pending", "sable"))["pending"])
        self.assertEqual(n, len(self.w.events))
        self.assertEqual(snapshot, self.w.subjects)

    def test_actual_house_pass_defers_busy_then_sends_while_resting(self):
        self.attach()
        self.prop(commission="landed")
        r = self.resident(busy=True)
        r.state.update(woke=True, at_rest=True, cursor=len(self.w.events))
        r.turns_ended = lambda: []
        h = object.__new__(PATCHED_HOUSE.House)
        h.dir = self.tmp
        h.world, h.fake, h.followups = "inmemory", True, self.f
        h.residents, h.load = {r.rid: r}, lambda: self.w
        h.corners = lambda w: {r.rid: self.w.nodes[r.rid]}
        h.settings = lambda w: dict(house.DEFAULTS, timers="off")
        h.record_knocks = lambda w, c: w
        h.toasts = lambda w: None
        h.set_status = lambda *a: None
        h.workshop = SimpleNamespace(restart_wanted=False, step=lambda *a: None)
        h.beat = lambda *a: None
        h.feeds = SimpleNamespace(step=lambda *a: None)
        h.usage = SimpleNamespace(step=lambda: None)
        h.plans = SimpleNamespace(publish=lambda: None)
        h.scripts = SimpleNamespace(step=lambda *a: None)
        with patch.object(house.feeds, "house_states", return_value={}):
            h.step()
            self.assertEqual([], self.send)
            r.busy = False
            h.step()
            self.assertEqual(1, len(self.send))
            self.assertTrue(r.busy)
            self.assertNotIn("at_rest", r.state)
            h.step()
            self.assertEqual(1, len(self.send))
        self.assertIn("followups", PATCHED_HOUSE.COMMANDS)

    def test_world_revision_is_verified_from_real_event_not_claimed_json(self):
        self.attach()
        raw = copy.deepcopy(next(iter(self.f.state["obligations"].values()))["spec"])
        raw.update(key="forged", revision=self.s["rev"] + 100)
        # Even a direct property bypass of the convenience command is checked.
        self.act("do prop " + self.target + " followup_request=" + json.dumps(json.dumps(raw)))
        self.f.observe(self.w)
        self.assertEqual(1, len(self.f.state["obligations"]))
        self.assertIn("stale", self.f.state["refused"][-1]["reason"])

    def test_staged_files_are_inert_and_baselines_are_not_edited(self):
        for relative in staging.HUNKS:
            text = (staging.ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("import followups", text)
        self.assertNotIn("followups", house.COMMANDS)
        self.assertNotEqual(PATCHED_HOUSE.House.step, house.House.step)

    def test_history_replacement_freezes_followups_not_ordinary_house(self):
        self.attach()
        self.prop(commission="failed")
        bridge = followups.HouseBridge(self.f.path, lambda: self.clock)
        self.w.events[-1]["args"]["commission"] = "different"
        with patch("builtins.print") as receipt:
            bridge.observe(self.w)
            bridge.dispatch(self.w, {})
        self.assertTrue(bridge.failed)
        self.assertTrue(receipt.called)
        self.assertTrue(self.f.path.with_suffix(".error.json").exists())
        # No task operation blocked by a broken follow-up projection.
        self.assertIn("ok ", self.act("do prop " + self.target + " status=working"))

    def test_corrupt_journal_retained_no_silent_new_baseline(self):
        self.f.path.write_text("not json", encoding="utf-8")
        with patch("builtins.print"):
            bridge = followups.HouseBridge(self.f.path, lambda: self.clock)
        self.assertTrue(bridge.failed)
        self.assertEqual("not json", self.f.path.read_text(encoding="utf-8"))

    def test_deadline_acknowledgment_leaves_task_unfinished(self):
        o = self.attach(recipient="codex")
        self.prop(usage_state="unavailable")
        self.clock = 10
        self.f.observe(self.w)
        r = self.resident()
        self.w.nodes[r.rid]["props"]["actor"] = "jeff"
        self.f.dispatch(self.w, {r.rid: r})
        self.ack(who="jeff")
        self.assertTrue(o["settled"])
        self.assertEqual("unavailable", self.s["props"]["usage_state"])
        self.assertEqual("unverified", o["work_state"])

    def test_denied_rule_request_and_malformed_request_do_not_consume_following_event(self):
        self.attach()
        first = copy.deepcopy(self.w.events[-1])
        first["id"], first["via"] = "e90000", "a-rule"
        self.w.events.append(first)
        self.f.observe(self.w)
        self.assertEqual(1, len(self.f.state["obligations"]))
        self.assertIn("direct", self.f.state["refused"][-1]["reason"])
        self.prop(capability_state="available")
        self.assertEqual("capability", next(iter(self.f.state["obligations"].values()))["facts"][-1]["kind"])

    def test_delivery_blocker_and_admission_are_exact_property_transitions(self):
        p = self.attach(observe=False)
        p["key"], p["revision"] = "delivery", self.s["rev"]
        p["when"] = [
            dict(field="delivery_state", values=["blocked"], kind="blocker"),
            dict(field="admission_state", values=["refused"], kind="admission"),
            dict(field="landed", values=[], kind="delivery"),
        ]
        self.assertIn("ok ", self.act(f"followups attach {self.target} '{json.dumps(p)}'"))
        self.f.observe(self.w)
        events = [self.prop(delivery_state="blocked"),
                  self.prop(admission_state="refused"), self.prop(landed="fixture-tree")]
        o = next(o for o in self.f.state["obligations"].values() if o["key"] == "delivery")
        self.assertEqual(events, [f["event"] for f in o["facts"]])
        self.assertEqual(["blocker", "admission", "delivery"], [f["kind"] for f in o["facts"]])
        self.prop(delivery_state="reviewing")
        self.assertEqual(3, len(o["facts"]))
        self.assertEqual("reviewing", o["current"]["delivery_state"])

    def test_failed_attempt_persistence_prevents_pipe_write(self):
        self.attach()
        self.prop(commission="landed")
        r = self.resident()
        bridge = followups.HouseBridge(self.f.path, lambda: self.clock)
        with patch.object(bridge.engine, "save", side_effect=OSError("fixture disk failure")):
            with patch("builtins.print"):
                bridge.dispatch(self.w, {r.rid: r})
        self.assertTrue(bridge.failed)
        self.assertEqual([], self.send)
        self.assertTrue(self.f.path.with_suffix(".error.json").exists())

    def test_malformed_event_does_not_skip_later_material_fact(self):
        o = self.attach()
        self.assertIn("ok ", self.act("do prop " + self.target + " followup_request=not-json"))
        self.prop(usage_state="quota")
        self.assertTrue(self.f.state["refused"])
        self.assertEqual("quota", o["facts"][-1]["new"])

    def test_undo_keeps_historical_fact_but_projects_real_current_state(self):
        o = self.attach()
        event = self.prop(usage_state="quota")
        self.assertIn("ok ", self.act("undo " + event))
        self.f.observe(self.w)
        self.assertEqual("", o["current"]["usage_state"])
        self.assertEqual(event, o["facts"][0]["event"])
        self.assertEqual("quota", o["facts"][0]["new"])
        self.assertTrue(o["target_exists"])


if __name__ == "__main__":
    unittest.main()
