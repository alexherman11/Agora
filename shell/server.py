"""The tree server: GET /tree, POST /verb, POST /chat, and a change stream; one page on GET /.
Never: never interprets the world, never mutates except through a verb, never hides an error."""

from __future__ import annotations

import asyncio
import dataclasses
import getpass
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse

from jeff.agent import Agent
from kernel import scene, verbs
from kernel.verbs import VerbError

PAGE = Path(__file__).with_name("index.html")


def create_app(
    world_path: str | os.PathLike[str],
    *,
    jeff: Agent | None = None,
    viewer: str | None = None,
    poll: float = 0.5,
) -> FastAPI:
    # The person at the page is the same person as at the terminal: one name, one viewer.
    viewer = viewer or os.environ.get("AGORA_ACTOR") or getpass.getuser()
    world = verbs.open_world(world_path)
    verbs.ensure_desk(world)
    agent = jeff if jeff is not None else Agent(world)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        world.close()  # a killed shell leaves nothing behind; the log is the truth

    app = FastAPI(title="agora shell", lifespan=lifespan)
    app.state.world, app.state.agent, app.state.viewer, app.state.poll = world, agent, viewer, poll

    @app.get("/", response_class=HTMLResponse)
    async def page() -> str:
        return PAGE.read_text(encoding="utf-8")

    @app.get("/tree")
    async def tree() -> dict[str, Any]:
        return scene.tree(world, viewer)

    @app.post("/verb")
    async def verb(request: Request) -> JSONResponse:
        body = await request.json()
        name, args = body.get("verb"), body.get("args") or {}
        actor = body.get("actor") or viewer
        fn = verbs.VERBS.get(name)
        if fn is None:
            return JSONResponse(
                {"error": f"no verb {name!r}; verbs are {sorted(verbs.VERBS)}"}, 400
            )
        try:
            result = fn(world, actor, **args)
        except VerbError as exc:
            return JSONResponse({"error": str(exc)}, 400)
        except TypeError as exc:
            return JSONResponse({"error": f"bad arguments for {name}: {exc}"}, 400)
        return JSONResponse({"result": plain(result), "revision": verbs.revision(world)})

    @app.post("/chat")
    async def chat(request: Request) -> JSONResponse:
        body = await request.json()
        message = str(body.get("message", "")).strip()
        if not message:
            return JSONResponse({"error": "say something"}, 400)
        try:
            turn = await asyncio.to_thread(agent.turn, message)
        except Exception as exc:  # the model is outside the world; report, never mask
            return JSONResponse({"error": f"JEFF is unavailable: {exc}"}, 502)
        return JSONResponse(
            {"reply": turn.reply, "calls": turn.calls, "revision": verbs.revision(world)}
        )

    @app.get("/events")
    async def events() -> EventSourceResponse:
        return EventSourceResponse(changes(world, poll))

    return app


async def changes(
    world: Any, poll: float, limit: int | None = None
) -> AsyncIterator[dict[str, str]]:
    """Yield the world's revision whenever it moves. The page reloads the tree on each one."""
    last = None
    sent = 0
    while limit is None or sent < limit:
        current = verbs.revision(world)
        if current != last:
            last = current
            sent += 1
            yield {"event": "changed", "data": str(current)}
            continue
        await asyncio.sleep(poll)


def plain(value: Any) -> Any:
    """Kernel records as JSON: the page never sees a Python type; a minted id is {"entity"}."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.asdict(value)
    if isinstance(value, str):
        return {"entity": value}
    return value


def load_env(path: str | os.PathLike[str] = ".env") -> None:
    """KEY=VALUE lines into the environment, never overriding what is already set."""
    env = Path(path)
    if not env.is_file():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def main() -> None:
    import uvicorn

    load_env()
    world = os.environ.get("AGORA_WORLD", os.path.join("worlds", "default"))
    port = int(os.environ.get("AGORA_PORT", "8787"))
    uvicorn.run(create_app(world), host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
