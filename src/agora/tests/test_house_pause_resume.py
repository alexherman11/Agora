"""A House restart pauses each agent and continues it after (Alex, 5 Nov 2026). The case that made it: Alex said
"bro activate please" at 08:27, the House took the line off JEFF's inbox, spent seconds building the message, looked
idle while it did, restarted itself, and the cut turn was never said again. Fresh temporary worlds, a fake child;
never a model."""
import time

from test_next_steps import load_house, resident, world  # noqa: F401  (pytest fixture)


def fresh_house(k, j, mod):
    h, agent = resident(k, j, mod)
    agent.state.pop("welcome_due", None)
    agent.state["cursor"] = 0
    h.card_signals = lambda *a, **kw: None
    h.refresh_card_signals = lambda a: None
    h.mark_turn = lambda *a: None
    h.sees_line = lambda *a: True
    return h, agent


def test_an_agent_is_busy_while_its_message_is_built(world):
    """The race: lines had left the inbox but busy was still unset while the task list was read."""
    k, a, j, w = world
    mod = load_house()
    h, agent = fresh_house(k, j, mod)
    seen = {}
    real = h.next_steps
    h.next_steps = lambda ag: (seen.setdefault("busy", ag.busy), seen.setdefault("inbox", list(ag.inbox)), real(ag))[2]
    agent.wake("~ Alex in Conversation: bro activate please", chat="conversation", record=6325)
    assert seen == {"busy": True, "inbox": []}          # what the restart check would have read mid-build


def test_a_restart_mid_turn_says_the_turn_again(world):
    """The 08:27 case, end to end: the line is said, the House goes off mid-turn, a new House starts."""
    k, a, j, w = world
    mod = load_house()
    h, agent = fresh_house(k, j, mod)
    agent.wake("~ Alex in Conversation: bro activate please", chat="conversation", record=6325)
    assert agent.busy and agent.state["cursor"] == 6325
    assert agent.state["in_flight"][0]["record"] == 6325
    # the House goes off: the model reports an interrupted turn, which is a pause, not a failure
    h.stopping = True
    agent._event({"e": "result", "ok": False, "detail": "interrupted"})
    assert "error" not in agent.state and agent.state["in_flight"]
    # a new House: the same saved state, a fresh process
    h2, again = fresh_house(k, j, mod)
    again.state = dict(agent.state)
    h2.m.see = lambda line, use=None: {"rows": []} if line == "rows said" else k.run(j, line, mode="see")
    h2.catch_up(again)
    sent = again.child.send.call_args.args[0]
    assert "bro activate please" in sent and "said again: the House restarted" in sent
    again._event({"e": "result", "ok": True, "detail": ""})
    assert "in_flight" not in again.state


def test_waiting_wakes_with_no_record_survive_a_restart(world):
    """house.wake, worker reports and task wakes have no said line behind them, so catch-up can't bring them back."""
    k, a, j, w = world
    mod = load_house()
    h, agent = fresh_house(k, j, mod)
    agent.busy = True
    agent.wake("~ Your worker Codex finished a turn and says: done", chat=None)
    h.builders = None
    h.agents = {j.person: agent}
    agent.stop = lambda why="": None
    import os
    real_exit, mod.os._exit = os._exit, lambda code: None
    try:
        h.off()
    finally:
        mod.os._exit = real_exit
    assert agent.state["paused"][0]["text"].endswith("finished a turn and says: done")
    h2, again = fresh_house(k, j, mod)
    again.state = dict(agent.state)
    h2.m.see = lambda line, use=None: {"rows": []} if line == "rows said" else k.run(j, line, mode="see")
    h2.catch_up(again)
    assert "finished a turn and says: done" in again.child.send.call_args.args[0]
    assert "paused" not in again.state


def test_a_turn_that_dies_twice_is_not_said_a_third_time(world, tmp_path):
    k, a, j, w = world
    mod = load_house()
    h, agent = fresh_house(k, j, mod)
    agent.dir = tmp_path
    agent.wake("~ Pike in Shop talk: ping", chat="shop", record=9)
    for _ in range(2):
        child = agent.child
        agent._event({"e": "exit", "code": 1, "child": child})
        agent.child = child
        agent.child.alive.return_value = True
        agent.busy = False
        if agent.inbox:
            agent._begin()
    assert agent.inbox == [] and "in_flight" not in agent.state
    sends = [c.args[0] for c in agent.child.send.call_args_list]
    assert sum("ping" in s for s in sends) == 2               # said once, said again once, then dropped


def test_the_task_list_is_sent_only_when_it_changed(world):
    k, a, j, w = world
    mod = load_house()
    h, agent = fresh_house(k, j, mod)
    h.next_steps = lambda ag: "Next steps\n- the same three cards"
    agent.wake("~ one", chat="shop", record=1)
    assert "the same three cards" in agent.child.send.call_args.args[0]
    agent._event({"e": "result", "ok": True, "detail": ""})
    agent.wake("~ two", chat="shop", record=2)
    assert "the same three cards" not in agent.child.send.call_args.args[0]
    agent._event({"e": "result", "ok": True, "detail": ""})
    h.next_steps = lambda ag: "Next steps\n- a new card"
    agent.wake("~ three", chat="shop", record=3)
    assert "a new card" in agent.child.send.call_args.args[0]
    agent._event({"e": "result", "ok": True, "detail": ""})
    agent.state["welcome_due"] = "the conversation was compacted"   # a compaction forgets it: sent again
    agent.wake("~ four", chat="shop", record=4)
    assert "a new card" in agent.child.send.call_args.args[0]


def test_the_fallback_ends_at_the_reset_the_provider_named():
    mod = load_house()
    since = time.mktime(time.strptime("2026-11-04T17:00:34", "%Y-%m-%dT%H:%M:%S"))
    at = mod.plan_resets_at("You've hit your session limit · resets 6:30pm (America/Los_Angeles)", since)
    assert time.strftime("%Y-%m-%d %H:%M", time.localtime(at)) == "2026-11-04 18:30"
    late = time.mktime(time.strptime("2026-11-04T19:00:00", "%Y-%m-%dT%H:%M:%S"))
    assert time.strftime("%m-%d %H:%M", time.localtime(mod.plan_resets_at("resets 6:30pm", late))) == "11-05 18:30"
    assert time.strftime("%m-%d %H:%M", time.localtime(mod.plan_resets_at("resets Nov 6, 3pm", since))) == "11-06 15:00"
    assert mod.plan_resets_at("rate limited, try later", since) is None

    a = mod.Agent.__new__(mod.Agent)
    a.cfg = {"provider": "claude", "model": "claude-fable-5-1", "fallback_provider": "codex", "fallback_model": "gpt-6-astra"}
    a.log = lambda *x: None
    a.state = {"on_fallback": "2026-11-04T17:00:34", "fallback_from": ["claude", "claude-fable-5-1"],
               "quota": "You've hit your session limit · resets 6:30pm (America/Los_Angeles)"}
    assert a.provider()[:2] == ("claude", "claude-fable-5-1")       # it is 5 Nov now: long past 6:30pm on the 4th
    assert "on_fallback" not in a.state
    a.state = {"on_fallback": time.strftime("%Y-%m-%dT%H:%M:%S"), "fallback_from": ["claude", "claude-fable-5-1"],
               "quota": "plan used up"}                               # no reset named: it holds, as before
    assert a.provider()[:2] == ("codex", "gpt-6-astra")
