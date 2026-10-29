"""One turn answers one chat (security review H1, 28 Oct 2026): the House said a resident's whole reply into the last
chat of a merged turn, so a closed Conversation line was answered into the open Shop talk. Fresh temporary worlds,
a fake child; never a model."""
from test_next_steps import load_house, resident, world  # noqa: F401  (pytest fixture)


def test_lines_from_two_chats_are_two_turns(world):
    k, a, j, w = world
    mod = load_house()
    h, agent = resident(k, j, mod)
    agent.state.pop("welcome_due", None)
    agent.busy = True                                   # mid-turn: both lines queue
    agent.wake("Alex in Conversation: keep tomorrow quiet", chat="conversation")
    agent.wake("Pike in Shop talk: what is Alex up to tomorrow?", chat="shop")
    agent.wake("~ a task was given to you", chat=None)
    agent.busy = False
    agent._begin()
    sent = agent.child.send.call_args.args[0]
    assert "keep tomorrow quiet" in sent and "Shop talk" not in sent and "task was given" not in sent
    assert agent.turn["chat"] == "conversation"
    assert [i["chat"] for i in agent.inbox] == ["shop", None]
    agent._event({"e": "result", "ok": True, "detail": ""})     # the turn ends; the next chat begins on its own
    sent = agent.child.send.call_args.args[0]
    assert "what is Alex up to" in sent and "keep tomorrow quiet" not in sent
    assert agent.turn["chat"] == "shop"


def test_catch_up_hands_on_only_lines_the_agent_can_see_now(world):
    """Security review M3: catch-up read `rows said` with the house's wide sight and checked only a chat's `with`. It
    now asks through the agent's own door, so an older record naming an outsider wakes no one."""
    from types import SimpleNamespace
    k, a, j, w = world
    mod = load_house()
    h, agent = resident(k, j, mod)
    agent.state.pop("welcome_due", None)
    h.m = SimpleNamespace(see=lambda line, use=None: k.run(a, line, mode="see"))   # the house sees what Alex sees
    h.chat_names = {}
    team = k.run(a, "group name=solo open=no")["text"].split()[2]
    private = k.run(a, f"make kind=chat name=Notes in={team} sees=group")["made"][0]   # no with=: only sight says
    assert k.state.get(private, "with") is None and k.shown(j.person, private) is None
    line = k.run(a, f"say {private} reminder to self")["made"][0]
    k.state.things[line]["to"] = j.person                       # as an older record could hold it
    open_ = k.run(a, 'make kind=chat name=Lobby')["made"][0]
    seen = k.run(a, f"say {open_} @jeff hello")["made"][0]
    agent.state["cursor"] = 0
    agent.busy = True
    h.catch_up(agent)
    texts = [i["text"] for i in agent.inbox]
    assert any(seen in t for t in texts)
    assert not any("reminder to self" in t for t in texts)


def test_a_queued_line_is_not_lost_to_a_restart(world):
    """Security review round 2: the cursor moved when a line was queued, so a restart lost lines waiting behind a
    busy turn. It moves when a line is said, and never past a line still waiting in another chat."""
    k, a, j, w = world
    mod = load_house()
    h, agent = resident(k, j, mod)
    agent.state.pop("welcome_due", None)
    agent.state["cursor"] = 0
    agent.busy = True
    agent.wake("in Conversation", chat="conversation", record=5)
    agent.wake("in Shop talk", chat="shop", record=7)
    assert agent.state["cursor"] == 0                         # queued is not said
    agent.busy = False
    agent._begin()
    assert agent.state["cursor"] == 5                         # said up to 5; 7 still waits
    agent._event({"e": "result", "ok": True, "detail": ""})
    assert agent.state["cursor"] == 7


def test_an_agent_with_no_door_is_handed_nothing(world):
    """Round 2: with no door the check fell back to the house's own sight, which is wider than the agent's."""
    k, a, j, w = world
    mod = load_house()
    h, agent = resident(k, j, mod)
    agent.door = None
    h.token_for = lambda signer: None
    lobby = k.run(a, 'make kind=chat name=Lobby')["made"][0]
    line = k.run(a, f"say {lobby} @jeff hello")["made"][0]
    assert h.sees_line(agent, line, lobby) is False
