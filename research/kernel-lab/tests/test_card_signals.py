"""Hidden local worlds, fake House residents, no desktop or model processes."""
import importlib.util
import json
import os
import sys
import threading
import time
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
sys.path.insert(0, str(LAB))
from kernel.kernel import Kernel


class CardRules(unittest.TestCase):
    def setUp(self):
        self.folder = Path(os.environ.get("TEMP", ROOT / ".tmp")) / "card-rules" / uuid.uuid4().hex
        self.folder.mkdir(parents=True)
        self.k = Kernel(self.folder, {
            "tag": "cr", "name": "Hidden card rules",
            "steward": {"account": "alex", "name": "Alex"},
            "invites_counted_by": "kernel", "invites": [{"code": "x", "uses": 5}],
        })
        self.a = self.k.actor_for(self.k.accounts["alex"])
        self.j = self.k.actor_for(self.k.join("jeff", "JEFF", invite="x")["person"])
        self.w = self.k.actor_for(self.k.join("worker", "Worker", invite="x")["person"])
        self.say('verb task.done steps="set $target lane=Done" help="hidden completion"')
        self.say('verb house.land steps="set $target build=landed" help="hidden publication receipt"')
        for line in (LAB / "apps/taskboard/card-rules.lines").read_text(encoding="utf-8").splitlines():
            self.say(line)

    def say(self, line, actor=None):
        out = self.k.run(actor or self.a, line)
        self.assertTrue(out["ok"], out)
        return out

    def card(self, actor=None, **facts):
        facts = dict(kind="taskboard-task", title="Dependency") | facts
        return self.say("make " + " ".join(f"{key}={json.dumps(value)}" for key, value in facts.items()),
                        actor)["made"][0]

    def notes(self):
        return [t for t in self.k.things("taskboard-event") if self.k.state.get(t, "card_signal")]

    def settle(self):
        # Join the actual rules queue, including any chained happenings, without
        # a timer-based production scheduler.
        end = time.monotonic() + 5
        while time.monotonic() < end:
            with self.k.lock:
                q = self.k._rules_q
                if q is None or (q.empty() and not getattr(self.k._local, "rule", None)):
                    count = len(self.k.log.records)
                else:
                    count = None
            time.sleep(.03)
            with self.k.lock:
                if count is not None and (q is None or q.empty()) and len(self.k.log.records) == count:
                    return
        self.fail("rule queue did not settle")

    def complete(self, source, event="house.land", actor=None):
        out = self.say(f"{event} {source}", actor)
        self.settle()
        return out

    def test_landing_wakes_only_dependents_and_is_idempotent(self):
        source = self.card()
        dependent = self.card(waiting_on=source, owner="Worker", lead="JEFF")
        self.card(waiting_on="unrelated", owner="Worker")
        self.complete(source)
        self.assertEqual(len(self.notes()), 1)
        note = self.k.state.things[self.notes()[0]]
        self.assertEqual((note["about"], note["to"], note["text"]),
                         (dependent, self.w.person, "Unblocked: Dependency has landed"))
        self.complete(source)
        self.complete(source, "task.done")
        self.assertEqual(len(self.notes()), 1)

    def test_done_by_another_person_wakes_lead(self):
        # Exercise by=anyone using an independently owned card, without
        # granting the Worker edit authority over Alex's fixtures.
        source = self.card(actor=self.w)
        dependent = self.card(waiting_on=source, lead="Worker")
        self.complete(source, "task.done", self.w)
        note = self.k.state.things[self.notes()[0]]
        self.assertEqual((note["about"], note["to"], note["text"]),
                         (dependent, self.w.person, "Unblocked: Dependency is done"))

    def test_alex_ask_routes_to_jeff(self):
        source = self.card()
        dependent = self.card(waiting_on=source, alex_ask="original-ask", owner="Alex")
        self.complete(source)
        note = self.k.state.things[self.notes()[0]]
        self.assertEqual((note["about"], note["to"]), (dependent, self.j.person))

    def test_without_a_route_the_kernel_routes_nobody(self):
        # Who an asked card reaches is the world's rule (route=alex_ask:JEFF in card-rules.lines), not the kernel's.
        self.assertNotIn("JEFF", (LAB / "kernel/card_signals.py").read_text(encoding="utf-8"))
        source = self.card()
        dependent = self.card(waiting_on=source, alex_ask="original-ask", owner="Worker")
        self.say(f"task.signal {source} mode=waiting event=done")
        self.assertEqual(self.notes(), [])
        self.say(f"look {source}; set {source} lane=Done")
        self.say(f"task.signal {source} mode=waiting event=done")
        note = self.k.state.things[self.notes()[0]]
        self.assertEqual((note["about"], note["to"]), (dependent, self.w.person))
        self.assertFalse(self.k.run(self.a, f"task.signal {source} mode=waiting event=done route=alex_ask")["ok"])

    def test_notify_on_land_and_reporter_once(self):
        source = self.card(notify_on_land="Worker", reporter="JEFF")
        self.card(notify_on_land="JEFF", reporter="Worker")
        self.complete(source)
        self.complete(source)
        self.assertEqual(len(self.notes()), 2)
        self.assertEqual({self.k.state.get(t, "to") for t in self.notes()}, {self.w.person, self.j.person})
        self.assertTrue(all(self.k.state.get(t, "about") == source for t in self.notes()))

    def test_old_curing_via_reporter_and_late_curing(self):
        source = self.card()
        issue = self.say(f'make kind=note family=bug status=curing curing_via={source} text="Found it"',
                         self.w)["made"][0]
        other = self.say('make kind=note family=bug status=curing curing_via=other', self.w)["made"][0]
        self.complete(source)
        self.assertEqual(len(self.notes()), 1)
        self.assertEqual(self.k.state.get(self.notes()[0], "about"), issue)
        self.assertEqual(self.k.state.get(self.notes()[0], "to"), self.w.person)
        self.assertNotEqual(self.k.state.get(self.notes()[0], "about"), other)
        late = self.say(f'make kind=note family=bug curing_via={source}', self.w)["made"][0]
        self.say(f"look {late}")
        self.say(f"set {late} status=curing")
        self.settle()
        self.assertEqual(len(self.notes()), 2)

    def test_no_notification_for_noncard_or_unpublished_card(self):
        source = self.card(build="landing", notify_on_land="Worker")
        self.say(f"task.signal {source} mode=notify event=landed")
        note = self.say('make kind=note title=Unrelated')["made"][0]
        self.complete(note, "task.done")
        self.assertEqual(self.notes(), [])

    def test_async_publication_set_is_the_delivery_event(self):
        source = self.card(build="landing", notify_on_land="Worker")
        self.say(f"look {source}")
        self.say(f"set {source} build=landed")
        self.settle()
        self.assertEqual(len(self.notes()), 1)
        self.say(f"look {source}")
        self.say(f"set {source} build_detail=bookkeeping")
        self.settle()
        self.assertEqual(len(self.notes()), 1)

    def test_undo_removes_notes_and_deduplication(self):
        source = self.card(notify_on_land="Worker", reporter="JEFF")
        self.card(waiting_on=source, owner="Worker")
        out = self.complete(source)
        self.assertEqual(len(self.notes()), 3)
        self.say("undo " + out["records"][0])
        self.settle()
        self.assertEqual(self.notes(), [])
        self.assertIsNone(self.k.state.get(source, "build"))
        self.complete(source)
        self.assertEqual(len(self.notes()), 3)

    def test_done_undo_and_recompletion(self):
        source = self.card()
        self.card(waiting_on=source, owner="Worker")
        out = self.complete(source, "task.done")
        self.assertEqual(len(self.notes()), 1)
        self.say("undo " + out["records"][0])
        self.settle()
        self.assertEqual(self.notes(), [])
        self.complete(source, "task.done")
        self.assertEqual(len(self.notes()), 1)

    def test_private_source_or_destination_does_not_leak(self):
        source = self.card(sees="me", notify_on_land="Worker")
        self.card(waiting_on=source, owner="Worker")
        self.complete(source)
        self.assertEqual(self.notes(), [])
        public = self.card()
        self.card(waiting_on=public, owner="Worker", sees="me")
        self.complete(public)
        self.assertEqual(self.notes(), [])

    def test_field_private_title_uses_recipient_projection(self):
        source = self.card()
        self.k.state.things[source]["sees.title"] = f"person:{self.a.person}"
        self.card(waiting_on=source, owner="Worker")
        self.complete(source)
        text = self.k.state.get(self.notes()[0], "text")
        self.assertEqual(text, "Unblocked: the dependency has landed")

    def house(self):
        path = LAB / "modules/house/house.py"
        spec = importlib.util.spec_from_file_location("card_rules_house", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        h = mod.House.__new__(mod.House)
        h.m = SimpleNamespace(see=lambda line: self.k.run(self.a, line, mode="see"))
        h.agents = {}
        for actor in (self.j, self.w):
            agent = SimpleNamespace(person=actor.person, state={"cursor": 0}, inbox=[], lock=threading.RLock())
            def wake(text, record=None, card_notes=None, agent=agent):
                agent.inbox.append({"text": text, "record": record, "card_signal_notes": card_notes or []})
            agent.wake = Mock(side_effect=wake)
            h.agents[actor.person] = agent
        h.line_for = lambda a, sid: self.k.shown(a.person, sid)
        return h

    def test_house_delivers_one_packet_per_recipient_and_undo_retracts_queue(self):
        source = self.card()
        self.card(waiting_on=source, owner="Worker")
        self.card(waiting_on=source, owner="Worker")
        out = self.complete(source, "task.done")
        h = self.house()
        agent = h.agents[self.w.person]
        h.card_signals(notice=self.notes()[0])
        h.card_signals(notice=self.notes()[1])
        self.assertEqual(agent.wake.call_count, 1)
        self.assertEqual(agent.inbox[0]["text"].count("Unblocked:"), 2)
        self.assertEqual(h.agents[self.j.person].wake.call_count, 0)
        self.say("undo " + out["records"][0])
        self.settle()
        h.retract_card_signals()
        self.assertEqual(agent.inbox, [])

    def test_house_catchup_acknowledged_record_and_visibility(self):
        source = self.card(notify_on_land="Worker")
        self.complete(source)
        h = self.house()
        a = h.agents[self.w.person]
        h.card_signals(a)
        self.assertEqual(a.wake.call_count, 1)
        rec = a.inbox[0]["record"]
        a.inbox.clear()
        a.state["cursor"] = rec
        a.state["card_signals_seen"] = self.notes()
        h.card_signals(a, cursor=rec)
        self.assertEqual(a.wake.call_count, 1)
        a.state["cursor"] = 0
        self.k.state.things[source]["sees"] = f"person:{self.a.person}"
        h.card_signals(a)
        self.assertEqual(a.wake.call_count, 1)

    def test_chat_cursor_does_not_acknowledge_card_notes(self):
        source = self.card(notify_on_land="Worker")
        self.complete(source)
        h = self.house()
        a = h.agents[self.w.person]
        a.state["cursor"] = len(self.k.log.records) + 10
        h.card_signals(a, cursor=a.state["cursor"])
        self.assertEqual(a.wake.call_count, 1)

    def test_partial_undo_rebuilds_queued_packet(self):
        source = self.card()
        self.card(waiting_on=source, owner="Worker", title="One")
        other = self.card(waiting_on=source, owner="Worker", title="Two")
        self.complete(source, "task.done")
        h = self.house()
        a = h.agents[self.w.person]
        h.card_signals(a)
        hidden = next(t for t in self.notes() if self.k.state.get(t, "about") == other)
        # A forgotten/undone notice is absent from the recipient's projection.
        self.k.state.things[hidden]["forgotten"] = True
        h.retract_card_signals()
        self.assertEqual(len(a.inbox), 1)
        self.assertEqual(a.inbox[0]["text"].count("Unblocked:"), 1)
        self.assertNotIn(hidden, a.inbox[0]["card_signal_notes"])

    def test_notification_does_not_publish_private_source_into_public_card(self):
        source = self.card(sees="me", title="Private source")
        dependent = self.card(waiting_on=source, owner="Alex")
        self.complete(source)
        self.assertEqual(len(self.notes()), 1)
        note = self.notes()[0]
        self.assertIsNotNone(self.k.shown(self.a.person, note))
        self.assertIsNone(self.k.shown(self.w.person, note))
        self.assertEqual(self.k.state.get(note, "about"), dependent)

    def resident_house(self):
        # Use the real Agent inbox and acknowledgement code, replacing only
        # the model transport. No resident/model processes are started.
        h = self.house()
        spec = importlib.util.spec_from_file_location(
            "card_rules_resident", LAB / "modules/house/house.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        a = mod.Agent.__new__(mod.Agent)
        a.house, a.cfg = h, {"person": self.w.person, "name": "Worker", "next_steps": "off"}
        a.name, a.lock = "Worker", threading.RLock()
        a.state, a.inbox, a.turn, a.busy = {"cursor": 0}, [], {}, True
        a.save, a.log = Mock(), Mock()
        a.child = Mock()
        a.child.alive.return_value = True
        a.child.send.return_value = True
        h.agents = {a.person: a}
        h.publish, h.mark_turn, h.task_changes = Mock(), Mock(), Mock()
        h.ready = threading.Event()
        h.ready.set()
        h.builders = SimpleNamespace(hear=Mock())
        return h, a

    def test_real_inbox_acknowledges_only_accepted_delivery_and_restart_deduplicates(self):
        source = self.card(notify_on_land="Worker")
        self.complete(source)
        h, a = self.resident_house()
        notice = self.notes()[0]
        h.happen({"word": "make", "target": notice})
        h.happen({"word": "make", "target": notice})
        self.assertEqual(len(a.inbox), 1)
        self.assertFalse(a.child.send.called)
        a.child.send.return_value = False
        a.busy = False
        a._begin()
        self.assertEqual(len(a.inbox), 1)
        self.assertEqual(a.state.get("card_signals_seen", []), [])
        a.child.send.return_value = True
        a._begin()
        self.assertEqual(a.inbox, [])
        self.assertEqual(a.state["card_signals_seen"], [notice])
        self.assertIn("Dependency has landed", a.child.send.call_args.args[0])
        h2, restarted = self.resident_house()
        restarted.state = json.loads(json.dumps(a.state))
        h2.card_signals(restarted)
        self.assertEqual(restarted.inbox, [])
        self.assertFalse(restarted.child.send.called)

    def test_real_inbox_undo_before_delivery_sends_nothing(self):
        source = self.card()
        self.card(waiting_on=source, owner="Worker")
        out = self.complete(source, "task.done")
        h, a = self.resident_house()
        h.happen({"word": "make", "target": self.notes()[0]})
        self.assertEqual(len(a.inbox), 1)
        self.say("undo " + out["records"][0])
        self.settle()
        h.happen({"word": "undo"})
        a.busy = False
        a._begin()
        self.assertEqual(a.inbox, [])
        self.assertFalse(a.child.send.called)

    def test_concurrent_make_callbacks_queue_each_notice_once(self):
        source = self.card(notify_on_land="Worker")
        self.complete(source)
        h, a = self.resident_house()
        workers = [threading.Thread(target=h.card_signals) for _ in range(8)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=5)
            self.assertFalse(worker.is_alive())
        self.assertEqual(len(a.inbox), 1)
        self.assertEqual(a.inbox[0]["card_signal_notes"], self.notes())

    def test_card_catchup_cannot_skip_chat_when_restarted_before_its_turn(self):
        chat = self.say('make kind=chat name=Hidden')["made"][0]
        self.say(f"say {chat} @worker Before publication")
        source = self.card(notify_on_land="Worker")
        self.complete(source)
        self.say(f"say {chat} @worker After publication")
        h, a = self.resident_house()
        h.chat_names = {}
        a.busy = False
        h.catch_up(a)
        self.assertIn("Dependency has landed", a.child.send.call_args.args[0])
        self.assertEqual(len(a.inbox), 1)
        self.assertIn("Before publication", a.inbox[0]["text"])
        self.assertIn("After publication", a.inbox[0]["text"])
        h2, restarted = self.resident_house()
        h2.chat_names = {}
        restarted.state = json.loads(json.dumps(a.state))
        restarted.busy = False
        h2.catch_up(restarted)
        sent = restarted.child.send.call_args.args[0]
        self.assertIn("Before publication", sent)
        self.assertIn("After publication", sent)
        self.assertNotIn("Dependency has landed", sent)
        self.assertEqual(restarted.turn["chat"], chat)


if __name__ == "__main__":
    unittest.main()
