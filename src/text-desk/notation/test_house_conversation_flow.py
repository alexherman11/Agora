"""Turn-boundary conversation behavior against disposable native worlds."""
import json
import queue
from unittest.mock import Mock, patch

import house
import host_route_parent
import pytest
import roomworld


@pytest.fixture
def flow(tmp_path):
    desk, refs = roomworld.build()
    world = desk.world
    slots = {}

    def act(actor, line, whole=False, as_of=None, **kwargs):
        slots[world.me] = (desk.seen, desk.open, desk.last_event_seen)
        desk.seen, desk.open, desk.last_event_seen = slots.get(actor, ({}, {world.root}, 0))
        world.me = actor
        desk._as_of = as_of
        try:
            reply = desk.dispatch("desk", {"line": line, "whole": whole})
            return reply.get("error") or reply.get("text") or ""
        finally:
            desk._as_of = None

    act("alex", f"look {refs.DESKTOP} :1")
    act("alex", f"do prop {refs.DESKTOP} person=alex")
    act("alex", f"look {world.root} :1")
    act("alex", f'do create {world.root} kind=chat title="Flow conversation" '
        'members=alex,pike reply_policy=queue')
    chat = next(s for s in world.subjects.values() if s["title"] == "Flow conversation")
    nid = next(iter(world.appearances_of(chat["id"])))
    act("pike", f"read {nid}")
    h = house.House.__new__(house.House)
    h.load = lambda: world
    h.act = Mock(side_effect=act)
    h.rest = Mock()
    r = house.Resident.__new__(house.Resident)
    r.house, r.rid = h, refs.corner["pike"]
    r.state_path = tmp_path / "state.json"
    r.state = {"cursor": len(world.events)}
    r.log = Mock()
    r.send = Mock()
    r.events = queue.Queue()
    r.reply = []
    r.reply_source = None
    r.busy = True
    return h, r, world, chat, nid, act


def test_ordinary_followups_arrive_after_current_reply_in_order(flow):
    h, r, w, chat, nid, act = flow
    act("alex", f'do append {nid} line="Also support keyboard navigation"')
    act("alex", f'do append {nid} line="And use a light theme"')
    h.act.reset_mock()
    h.after_turn(w, r, w.nodes[r.rid], "pike", f'> do append {nid} line="The first answer"')
    assert chat["lines"][-1]["text"].endswith("The first answer")
    sent = r.send.call_args.args[0]
    assert "queued for your next turn" in sent
    assert sent.index("Also support keyboard") < sent.index("And use a light theme")
    assert r.state["cursor"] == len(w.events)


def test_interrupt_discards_all_stale_commands_and_delivers_new_direction(flow):
    h, r, w, chat, nid, act = flow
    act("alex", f'do append {nid} line="/stop do not change the task"')
    h.act.reset_mock()
    before = len(w.events)
    h.after_turn(w, r, w.nodes[r.rid], "pike",
                 f'> do prop {r.rid} unwanted=yes\n> do append {nid} line="Done"\n> rest')
    h.act.assert_not_called()
    h.rest.assert_not_called()
    assert len(w.events) == before
    assert "unwanted" not in w.nodes[r.rid]["props"]
    assert "pending commands were not executed" in r.send.call_args.args[0]
    assert "/stop do not change" in r.send.call_args.args[0]
    assert r.state["cursor"] == len(w.events)
    assert r.log.call_args.args[0] == "turn_interrupted"
    assert json.loads(r.state_path.read_text())["cursor"] == len(w.events)


def test_interrupt_prevents_host_intent_dispatch_before_after_turn(flow):
    h, r, w, _, nid, act = flow
    act("alex", f'do append {nid} line="Stop"')
    source = object()
    h.host_route = Mock()
    h.host_route.current.return_value = True
    r.reply = ['> host-route {"action":"artifact-view"}']
    r.reply_source = source
    r.events.put(host_route_parent.ChildEvent(source, {"type": "result", "is_error": False}))
    with patch.object(house.charter, "drain_channel"):
        output = r.turns_ended()
    h.host_route.intercept.assert_not_called()
    assert len(output) == 1 and "host-route" in output[0]
    h.after_turn(w, r, w.nodes[r.rid], "pike", output[0])
    h.host_route.intercept.assert_not_called()
    assert "pending commands were not executed" in r.send.call_args.args[0]
