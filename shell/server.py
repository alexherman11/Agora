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
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse

from client_layout import free_slot
from jeff.agent import Agent
from kernel import project, scene, verbs
from kernel.verbs import VerbError
from shell.session import install

PAGE = Path(__file__).with_name("index.html")


def create_app(
    world_path: str | os.PathLike[str],
    *,
    jeff: Agent | None = None,
    viewer: str | None = None,
    poll: float = 0.5,
    import_roots=None,
) -> FastAPI:
    # The person at the page is the same person as at the terminal: one name, one viewer.
    viewer = viewer or os.environ.get("AGORA_ACTOR") or getpass.getuser()
    world = verbs.open_world(world_path, import_roots=import_roots)
    verbs.ensure_desk(world)
    agent = jeff if jeff is not None else Agent(world)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await asyncio.to_thread(agent.close)
        world.close()  # a killed shell leaves nothing behind; the log is the truth

    app = FastAPI(title="agora shell", lifespan=lifespan)
    install(app)
    app.state.world, app.state.agent, app.state.viewer, app.state.poll = world, agent, viewer, poll

    @app.get("/", response_class=HTMLResponse)
    async def page() -> str:
        return PAGE.read_text(encoding="utf-8")

    @app.get("/app.js")
    async def script():
        return FileResponse(PAGE.with_name("app.js"), media_type="text/javascript")

    @app.get("/style.css")
    async def style():
        return FileResponse(PAGE.with_name("style.css"), media_type="text/css")

    @app.get("/components.js")
    async def components():
        return FileResponse(PAGE.with_name("components.js"), media_type="text/javascript")

    @app.get("/lens")
    async def lens(
        entity: str = "", revision: int | None = None, selected: str | None = None, offset: int = 0
    ):
        try:
            return project.lens(world, entity, revision, selected, offset)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, 400)

    @app.get("/tree")
    async def tree() -> dict[str, Any]:
        return scene.tree(world, viewer)

    @app.get("/agent")
    async def agent_status():
        if agent.provider != "openai-account":
            return {"provider": agent.provider, "model": agent.model}
        try:
            return await asyncio.to_thread(agent.account_harness.status)
        except Exception:
            return JSONResponse(
                {"error": "OpenAI account runtime could not start; check AGORA_CODEX_BIN"}, 503
            )

    @app.post("/agent/login")
    async def agent_login():
        if agent.provider != "openai-account":
            return JSONResponse({"error": "Choose the openai-account provider first"}, 409)
        try:
            return await asyncio.to_thread(agent.account_harness.login)
        except Exception:
            return JSONResponse(
                {"error": "OpenAI sign-in could not start; check the Codex runtime"}, 503
            )

    @app.post("/verb")
    async def verb(request: Request) -> JSONResponse:
        try:
            body = await request.json()
            if not isinstance(body, dict):
                raise ValueError("request must be an object")
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, 400)
        name, args = body.get("verb"), body.get("args", {})
        if not isinstance(name, str) or not isinstance(args, dict) or "actor" in body:
            return JSONResponse(
                {"error": "use a verb name and argument object; actor is session-bound"}, 400
            )
        actor = viewer
        fn = verbs.VERBS.get(name)
        if fn is None:
            return JSONResponse(
                {"error": f"no verb {name!r}; verbs are {sorted(verbs.VERBS)}"}, 400
            )
        try:
            if name == "place" and "transform" not in args:
                args = dict(
                    args,
                    transform=free_slot(scene.tree(world, viewer, args.get("scene", scene.DESK))),
                )
            result = await asyncio.to_thread(fn, world, actor, **args)
        except VerbError as exc:
            return JSONResponse({"error": str(exc)}, 400)
        except TypeError as exc:
            return JSONResponse({"error": f"bad arguments for {name}: {exc}"}, 400)
        return JSONResponse({"result": plain(result), "revision": verbs.revision(world)})

    @app.post("/chat")
    async def chat(request: Request) -> JSONResponse:
        try:
            body = await request.json()
            if not isinstance(body, dict) or not isinstance(body.get("message"), str):
                raise ValueError("message must be a string")
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, 400)
        message = body["message"].strip()
        if not message:
            return JSONResponse({"error": "say something"}, 400)
        try:
            selection = body.get("selection")
            if selection is not None:
                verbs.read(world, viewer, selection)
            turn = await asyncio.to_thread(agent.turn, message, selection)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, 409)
        except Exception as exc:  # the model is outside the world; report, never mask
            return JSONResponse(
                {"error": f"JEFF is unavailable ({type(exc).__name__}); check configuration"},
                502,
            )
        return JSONResponse(
            {"reply": turn.reply, "calls": turn.calls, "revision": verbs.revision(world)}
        )

    @app.get("/events")
    async def events() -> EventSourceResponse:
        return EventSourceResponse(changes(world, poll))

    @app.post("/stop")
    async def stop():
        await asyncio.to_thread(agent.cancel)
        return {
            "stopped": True,
            "detail": "No further tool dispatch; an in-flight provider request may still finish.",
        }

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
    roots = os.environ.get("AGORA_IMPORT_ROOTS")
    uvicorn.run(
        create_app(world, import_roots=roots.split(os.pathsep) if roots else None),
        host="127.0.0.1",
        port=port,
    )


if __name__ == "__main__":
    main()
