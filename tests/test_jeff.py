"""JEFF is a client: derived tools, verb calls as jeff, refusals fed back, the desk in context."""

from __future__ import annotations

from pathlib import Path

from jeff.agent import Agent
from jeff.tools import derive_tools
from kernel import events, store, verbs
from kernel.schema import DESK
from tests.fakes import FakeClient, import_notes_script, text, tool_use


def test_tools_are_a_projection_of_the_verb_registry() -> None:
    tools = derive_tools()
    assert [t["name"] for t in tools] == [v.name for v in verbs.REGISTRY]
    attach = next(t for t in tools if t["name"] == "attach")
    assert attach["input_schema"]["required"] == ["entity", "facet_type", "body"]
    assert "core.text {" in attach["description"]  # facet shapes travel with the tool


def test_jeff_acts_as_jeff_and_only_through_verbs(world: store.Store, notes_file: Path) -> None:
    client = FakeClient(import_notes_script(str(notes_file)))
    jeff = Agent(world, client=client)
    turn = jeff.turn("Put my notes file into the world.")
    assert turn.reply == "Done: your notes are on the desk."
    assert [c["verb"] for c in turn.calls] == ["mint", "place"]
    assert all("error" not in c for c in turn.calls)
    entity = turn.calls[0]["result"]["entity"]
    assert {f.type for f in world.facets(entity)} == {"core.name", "core.text", "core.file-backing"}
    assert [a.entity for a in world.appearances(DESK)] == [entity]
    actors = {e.actor for e in events.replay(world.world) if e.payload.get("entity") != DESK}
    assert actors == {"jeff"}


def test_jeff_sees_the_desk_and_the_vocabulary(world: store.Store) -> None:
    note = verbs.mint(world, "alex", {"core.name": {"name": "grocery list"}})
    verbs.place(world, "alex", note)
    client = FakeClient([[text("I see it.")]])
    Agent(world, client=client).turn("What is on the desk?")
    system = client.requests[0]["system"]
    assert "grocery list" not in system
    assert "grocery list (by alex)" in client.requests[0]["messages"][0]["content"]
    assert "core.file-backing" in system and "- place:" in system
    assert [t["name"] for t in client.requests[0]["tools"]] == [v.name for v in verbs.REGISTRY]


def test_a_refusal_comes_back_as_an_error_result(world: store.Store) -> None:
    note = verbs.mint(world, "alex")
    client = FakeClient(
        [
            [tool_use("attach", {"entity": note, "facet_type": "core.name", "body": {"nom": "x"}})],
            lambda req: [text(req["messages"][-1]["content"][0]["content"])],
        ]
    )
    turn = Agent(world, client=client).turn("Name it x.")
    assert turn.calls[0]["error"].startswith("core.name expects")
    assert client.requests[1]["messages"][-1]["content"][0]["is_error"] is True
    assert "core.name expects" in turn.reply
    assert world.facet(note, "core.name") is None


def test_unknown_tool_and_bad_arguments_are_data_not_crashes(world: store.Store) -> None:
    jeff = Agent(world, client=FakeClient([]))
    assert "no verb 'find'" in jeff.call("find", {})["error"]
    assert "bad arguments for mint" in jeff.call("mint", {"bogus": 1})["error"]


def test_history_is_the_only_memory(world: store.Store) -> None:
    client = FakeClient([[text("hi")], [text("again")]])
    jeff = Agent(world, client=client)
    jeff.turn("one")
    jeff.turn("two")
    roles = [m["role"] for m in client.requests[1]["messages"]]
    assert roles == ["user", "user", "assistant", "user"]
    assert Agent(world, client=FakeClient([])).history == []
