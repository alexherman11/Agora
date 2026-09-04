"""The shell renders and forwards: a tree, a verb endpoint, a chat endpoint, a change stream."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

from jeff.agent import Agent
from kernel import verbs
from shell.server import changes, create_app
from tests.fakes import FakeClient, text


def test_empty_desk_renders(world_path: Path) -> None:
    app = create_app(world_path, jeff=None)
    with TestClient(app) as client:
        tree = client.get("/tree").json()
    assert tree["exists"] is True and tree["nodes"] == [] and tree["scene"] == "ent_desk"


def test_verb_endpoint_forwards_and_refuses(world_path: Path) -> None:
    with TestClient(create_app(world_path)) as client:
        minted = client.post(
            "/verb", json={"verb": "mint", "args": {"facets": {"core.name": {"name": "todo"}}}}
        ).json()
        entity = minted["result"]["entity"]
        placed = client.post(
            "/verb",
            json={
                "verb": "place",
                "args": {"entity": entity, "mode": "summary", "transform": {"x": 5}},
            },
        ).json()
        assert placed["result"]["mode"] == "summary" and placed["revision"] > minted["revision"]
        [node] = client.get("/tree").json()["nodes"]
        assert node["label"] == "todo" and node["transform"]["x"] == 5
        refused = client.post("/verb", json={"verb": "place", "args": {"entity": "ent_nope"}})
        assert refused.status_code == 400 and "no entity" in refused.json()["error"]
        unknown = client.post("/verb", json={"verb": "find", "args": {}})
        assert unknown.status_code == 400 and "no verb" in unknown.json()["error"]
        bad = client.post("/verb", json={"verb": "mint", "args": {"bogus": 1}})
        assert bad.status_code == 400 and "bad arguments" in bad.json()["error"]


def test_chat_goes_through_jeff(world_path: Path) -> None:
    world = verbs.open_world(world_path)
    jeff = Agent(world, client=FakeClient([[text("Nothing to do.")]]))
    with TestClient(create_app(world_path, jeff=jeff)) as client:
        reply = client.post("/chat", json={"message": "hello"}).json()
        assert reply["reply"] == "Nothing to do." and reply["calls"] == []
        assert client.post("/chat", json={"message": "  "}).status_code == 400


def test_page_is_served(world_path: Path) -> None:
    with TestClient(create_app(world_path)) as client:
        page = client.get("/")
    assert page.status_code == 200 and "EventSource" in page.text


def test_change_stream_notices_verbs(world_path: Path) -> None:
    world = verbs.open_world(world_path)

    async def scenario() -> list[str]:
        stream = changes(world, poll=0.01, limit=2)
        first = await asyncio.wait_for(anext(stream), 2)
        verbs.mint(world, "alex")
        second = await asyncio.wait_for(anext(stream), 2)
        return [first["data"], second["data"]]

    first, second = asyncio.run(scenario())
    assert int(second) == int(first) + 1
