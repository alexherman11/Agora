"""Synthetic conversation delivery tests; never load a saved/live world."""

from types import SimpleNamespace
from unittest.mock import Mock

import conversation_policy as policy
import pytest
import roomworld


@pytest.fixture
def chat():
    desk, refs = roomworld.build()
    w = desk.world
    slots = {}

    def run(actor, command, at=None):
        slots[w.me] = (desk.seen, desk.open, desk.last_event_seen)
        desk.seen, desk.open, desk.last_event_seen = slots.get(actor, ({}, {w.root}, 0))
        w.me = actor
        desk._as_of = at
        try:
            return desk.dispatch("desk", {"line": command})
        finally:
            desk._as_of = None

    assert not run("alex", f"look {refs.DESKTOP} :1").get("error")
    assert not run("alex", f"do prop {refs.DESKTOP} person=alex").get("error")
    assert not run("alex", f"look {w.root} :1").get("error")
    assert not run("alex", f'do create {w.root} kind=chat title="Queue test" '
                   'members=alex,pike reply_policy=queue').get("error")
    subject = next(s for s in w.subjects.values() if s["title"] == "Queue test")
    nid = next(iter(w.appearances_of(subject["id"])))
    run("pike", f"read {nid}", len(w.events))
    return desk, subject, nid, run


def test_followups_do_not_suppress_current_answer_or_mark_them_read(chat):
    desk, subject, nid, run = chat
    cursor = len(desk.world.events)
    run("alex", f'do append {nid} line="Also add a keyboard shortcut"')
    run("alex", f'do append {nid} line="And a light theme"')
    reads = dict(getattr(desk, "_chat_reads", {}))
    result = run("pike", f'do append {nid} line="Here is the first answer"', cursor)
    assert not result.get("error"), result
    assert "2 human follow-up message(s) queued" in result["text"]
    assert subject["lines"][-1]["text"].endswith("Here is the first answer")
    assert desk._chat_reads == reads
    assert policy.queued_interrupts(desk.world, "pike", cursor) == []
    assert [line["text"] for line in subject["lines"]][-3:-1] == [
        "Alex: Also add a keyboard shortcut", "Alex: And a light theme"
    ]


@pytest.mark.parametrize("words", ["Stop", "/cancel", "Correction: use the other file",
                                  "@pike: wait, don't deploy", "Please stop that"])
def test_interrupts_hold_reply_and_produce_stable_batch_guard_records(chat, words):
    desk, subject, nid, run = chat
    cursor = len(desk.world.events)
    run("alex", f'do append {nid} line="{words}"')
    result = run("pike", f'do append {nid} line="Old answer"', cursor)
    assert "held, not sent" in str(result.get("error")), result
    records = policy.queued_interrupts(desk.world, "pike", cursor)
    assert len(records) == 1
    assert records[0]["message"] == subject["lines"][-1]["id"]
    assert records[0]["event"] == subject["lines"][-1]["ev"]
    assert records == policy.queued_interrupts(desk.world, "pike", cursor)
    assert policy.queued_interrupts(desk.world, "pike", len(desk.world.events)) == []


@pytest.mark.parametrize("value", ["hold", "future-policy"])
def test_other_and_unknown_policies_keep_old_guard(chat, value):
    desk, _, nid, run = chat
    run("alex", f"look {nid} :1")
    run("alex", f"do prop {nid} reply_policy={value}")
    cursor = len(desk.world.events)
    run("alex", f'do append {nid} line="One more request"')
    result = run("pike", f'do append {nid} line="Old answer"', cursor)
    assert "held, not sent" in str(result.get("error")), result


def test_worker_and_comment_updates_still_hold(chat):
    desk, subject, nid, run = chat
    cursor = len(desk.world.events)
    run("worker-test", f'do append {nid} line="The build failed"')
    result = run("pike", f'do append {nid} line="Done"', cursor)
    assert "held, not sent" in str(result.get("error")), result
    run("pike", f"look {nid} :1")
    run("pike", f'do comment {nid} line="Ship?"')
    cid = subject["comments"][-1]["id"]
    cursor = len(desk.world.events)
    run("alex", f"look {nid} :1")
    run("alex", f'do comment {nid} id={cid} line="No, do not ship"')
    result = run("pike", f'do comment {nid} id={cid} line="Shipping"', cursor)
    assert "held, not sent" in str(result.get("error")), result


def test_unrelated_conversation_does_not_interrupt_resident(chat):
    desk, _, nid, run = chat
    run("alex", f"look {nid} :1")
    run("alex", f"do prop {nid} members=alex,sable")
    cursor = len(desk.world.events)
    run("alex", f'do append {nid} line="Stop"')
    assert policy.queued_interrupts(desk.world, "pike", cursor) == []
    assert len(policy.queued_interrupts(desk.world, "sable", cursor)) == 1


def test_reply_target_cannot_bypass_an_unseen_interruption(chat):
    desk, subject, nid, run = chat
    cursor = len(desk.world.events)
    run("alex", f'do append {nid} line="/interrupt use the other plan"')
    mid = subject["lines"][-1]["id"]
    result = run("pike", f'do append {nid} line="Old answer" reply_to={mid}', cursor)
    assert "held, not sent" in str(result.get("error")), result


def test_message_to_another_resident_keeps_normal_guard(chat):
    desk, _, nid, run = chat
    run("alex", f"look {nid} :1")
    run("alex", f"do prop {nid} members=all")
    cursor = len(desk.world.events)
    run("alex", f'do append {nid} line="@sable: add another feature"')
    result = run("pike", f'do append {nid} line="Old answer"', cursor)
    assert "held, not sent" in str(result.get("error")), result


def test_typed_human_signature_does_not_impersonate_human(chat):
    desk, _, nid, run = chat
    cursor = len(desk.world.events)
    run("worker-test", f'do append {nid} line="Alex: ordinary request"')
    result = run("pike", f'do append {nid} line="Old answer"', cursor)
    assert "held, not sent" in str(result.get("error")), result
    run("worker-test", f'do append {nid} line="Alex: /stop"')
    assert policy.queued_interrupts(desk.world, "pike", cursor) == []


def test_queue_policy_does_not_relax_stale_nonchat_edits(chat):
    desk, _, nid, run = chat
    run("pike", f"read {nid}")
    cursor = len(desk.world.events)
    run("alex", f'do append {nid} line="Additional request"')
    result = run("pike", f'do edit {nid} text="Overwrite the conversation"', cursor)
    assert "stale" in str(result.get("error")), result


def test_interruption_committed_before_dispatch_prevents_all_effects(chat):
    desk, _, nid, run = chat
    cursor = len(desk.world.events)
    # Model/house could have inspected a snapshot before this line committed.
    run("alex", f'do append {nid} line="/stop do not create anything"')
    before = len(desk.world.events)
    desk.batch = True
    result = run("pike", f'look {desk.world.root} :1; do create {desk.world.root} '
                 'kind=note title="Should never exist"', cursor)
    assert "No command in this call ran" in result.get("error", ""), result
    assert len(desk.world.events) == before
    assert not any(s["title"] == "Should never exist" for s in desk.world.subjects.values())
    # The next model turn can act after receiving the direction.
    result = run("pike", f'look {desk.world.root} :1', len(desk.world.events))
    assert not result.get("error"), result
    result = run("pike", f"read {nid}", len(desk.world.events))
    assert not result.get("error"), result
    assert "/stop do not create anything" in result["text"]


@pytest.mark.parametrize("policy_value,actor,words,wakes", [
    ("queue", "alex", "Another request", True),
    ("queue", "alex", "/stop", True),
    ("hold", "alex", "Another request", False),
    ("queue", "worker-test", "Routine progress", False),
    ("queue", "alex", "@sable: another request", False),
])
def test_queued_shared_conversation_wakes_once_without_address(
    chat, policy_value, actor, words, wakes
):
    import house
    import rooms

    desk, _, nid, run = chat
    w = desk.world
    run("alex", f"look {nid} :1")
    run("alex", f"do prop {nid} reply_policy={policy_value} members=all")
    r = SimpleNamespace(rid=rooms.corner_of(w, "pike"),
                        state={"cursor": len(w.events), "at_rest": True}, save=Mock())
    run(actor, f'do append {nid} line="{words}"')
    h = house.House.__new__(house.House)
    h.load = lambda: w
    assert h.news(w, r, "pike", resting=True) is wakes
    assert len(r.state["inbox"]) == 1
    assert bool(r.state.get("knocked_by")) is wakes
    assert not h.news(w, r, "pike", resting=True)
    assert len(r.state["inbox"]) == 1


def test_queue_receipt_and_native_routing_agree_without_claiming_delivery(chat, monkeypatch):
    import rooms
    import scene

    desk, _, nid, run = chat
    w = desk.world
    monkeypatch.setattr(scene, "house_rows", lambda _desk: [
        {"corner": rooms.corner_of(w, "pike"), "doing": "resting"},
        {"corner": rooms.corner_of(w, "sable"), "doing": "resting"},
    ])
    reply = run("alex", f'do append {nid} line="One more thing"')
    event = w.events[-1]
    assert rooms.reached(w, event) == {"pike": "call"}
    assert "Pike: queued for the next turn; wake requested" in reply["text"]
    assert "Pike: woken" not in reply["text"]
    assert "Sable:" not in reply["text"]
    run("alex", f"look {nid} :1")
    run("alex", f"do prop {nid} members=all")
    reply = run("alex", f'do append {nid} line="@sable: another request"')
    assert rooms.reached(w, w.events[-1]) == {"sable": "call"}
    assert "Sable: queued for the next turn" in reply["text"]
    assert "Pike:" not in reply["text"]


@pytest.mark.parametrize("text", ["Can you correct the title?", "Also add cancellation",
                                 'The button says "stop"', "`/stop` is the label", '"stop"'])
def test_mentions_of_controls_are_not_interrupts(text):
    assert not policy.interrupts(text)
