"""Append and replay: the only writer of the log, and the keeper of the world directory.
Never: never edits or deletes a line, never touches the store, never logs without an actor."""

from __future__ import annotations

import hashlib
import json
import math
import os
import secrets
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kernel.locking import locked
from kernel.schema import EVENT_KINDS, Event

_BASE32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


class LogError(Exception):
    """An intent the log refuses. Side-effect-free: nothing was written."""


@dataclass(frozen=True)
class World:
    """One world is one directory: log.jsonl, store.db, blobs/. A fork is a copy."""

    path: Path

    @property
    def log(self) -> Path:
        return self.path / "log.jsonl"

    @property
    def db(self) -> Path:
        return self.path / "store.db"

    @property
    def blobs(self) -> Path:
        return self.path / "blobs"


def open_world(path: str | os.PathLike[str]) -> World:
    world = World(Path(path).resolve())
    world.blobs.mkdir(parents=True, exist_ok=True)
    world.log.touch(exist_ok=True)
    return world


def new_id(prefix: str) -> str:
    """A sortable, content-free id: 10 chars of milliseconds, 16 of randomness."""
    ms = int(time.time() * 1000)
    stamp = "".join(_BASE32[(ms >> (5 * i)) & 31] for i in reversed(range(10)))
    noise = "".join(_BASE32[b & 31] for b in secrets.token_bytes(16))
    return f"{prefix}_{stamp}{noise}"


def append(world: World, actor: str, kind: str, payload: dict[str, Any]) -> Event:
    """Record one intent as one line. All-or-nothing: a refused intent writes nothing."""
    if not isinstance(actor, str) or not actor:
        raise LogError("every event needs an actor: a non-empty string naming who acted")
    if kind not in EVENT_KINDS:
        raise LogError(f"unknown event kind {kind!r}; the log accepts {list(EVENT_KINDS)}")
    if not isinstance(payload, dict):
        raise LogError("an event payload must be a JSON object")
    event = Event(id=new_id("evt"), ts=time.time(), actor=actor, kind=kind, payload=payload)
    try:
        line = event.to_line()
    except (TypeError, ValueError) as exc:
        raise LogError(f"payload is not JSON-serializable: {exc}") from exc
    with locked(world.path):
        tail = b""
        if world.log.stat().st_size and not _ends_with_newline(world.log):
            tail = world.log.read_bytes().rsplit(b"\n", 1)[-1]
            from dataclasses import replace

            event = replace(event, sealed_tail=hashlib.sha256(tail).hexdigest())
            line = event.to_line()
        data = (b"\n" if tail else b"") + (line + "\n").encode("utf-8")
        with open(world.log, "ab") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    return event


def replay(world: World, after: int = 0, offset: int = 0) -> Iterator[Event]:
    """Read complete byte-framed records. Only an explicitly sealed gap may be skipped.

    Legacy sealed gaps without evidence now require explicit recovery investigation;
    guessing whether a complete malformed record was once a tail could discard real history.
    """
    if not world.log.exists():
        return
    with locked(world.path), open(world.log, "rb") as handle:
        handle.seek(offset)
        seq = after if offset else 0
        while line := handle.readline():
            if not line.endswith(b"\n"):
                return  # unacknowledged tail, including incomplete UTF-8
            seq += 1
            try:
                event = _decode(line, seq)
            except LogError as exc:
                following = handle.readline()
                if not following.endswith(b"\n"):
                    raise exc
                try:
                    seal = _decode(following, seq + 1)
                except LogError:
                    raise exc from None
                if seal.sealed_tail != hashlib.sha256(line[:-1]).hexdigest():
                    raise exc
                seq += 1
                event = seal
            if seq > after:
                from dataclasses import replace

                yield replace(event, offset=handle.tell())


def _decode(line: bytes, seq: int) -> Event:
    try:
        event = Event.from_line(line.decode("utf-8"), seq)
        if (
            type(event.v) is not int
            or event.v != 1
            or event.kind not in EVENT_KINDS
            or not isinstance(event.payload, dict)
            or not isinstance(event.actor, str)
            or not event.actor
            or not isinstance(event.id, str)
            or type(event.ts) not in (int, float)
            or not math.isfinite(event.ts)
        ):
            raise ValueError("unsupported event version, kind, or envelope")
        p = event.payload
        required = {
            "component-committed": ("changes", "placements", "component", "definition_revision"),
            "entity-minted": ("entity",),
            "facet-attached": ("entity", "type", "body"),
            "text-edited": ("entity", "type", "body"),
            "appearance-placed": ("scene", "entity", "mode", "transform"),
        }
        if any(key not in p for key in required[event.kind]):
            raise ValueError("missing payload fields")
        if event.kind == "component-committed":
            if not isinstance(p["changes"], list) or not isinstance(p["placements"], list):
                raise ValueError("component changes and placements must be lists")
            for change in p["changes"]:
                if (
                    not isinstance(change, dict)
                    or not isinstance(change.get("entity"), str)
                    or not isinstance(change.get("type"), str)
                    or not isinstance(change.get("body"), dict)
                ):
                    raise ValueError("malformed component change")
            for placement in p["placements"]:
                if (
                    not isinstance(placement, dict)
                    or not all(
                        isinstance(placement.get(k), str) for k in ("scene", "entity", "mode")
                    )
                    or not isinstance(placement.get("transform"), dict)
                ):
                    raise ValueError("malformed component placement")
            json.dumps(p, allow_nan=False)
            return event
        if not isinstance(p["entity"], str):
            raise ValueError("payload entity must be a string")
        if event.kind == "entity-minted":
            bodies = p.get("facets", {})
            if not isinstance(bodies, dict) or not all(
                isinstance(b, dict) for b in bodies.values()
            ):
                raise ValueError("minted facets must map types to objects")
        elif event.kind in ("facet-attached", "text-edited"):
            if not isinstance(p["type"], str) or not isinstance(p["body"], dict):
                raise ValueError("attached facet needs a string type and object body")
        elif (
            not isinstance(p["scene"], str)
            or not isinstance(p["mode"], str)
            or not isinstance(p["transform"], dict)
        ):
            raise ValueError("appearance needs string scene/mode and object transform")
        json.dumps(p, allow_nan=False)
        return event
    except (ValueError, TypeError, KeyError, UnicodeError) as exc:
        raise LogError(
            f"corrupt or unsupported log line {seq}: {exc}; preserve the log for recovery"
        ) from exc


def count(world: World) -> int:
    return sum(1 for _ in replay(world))


def copy_log(world: World, destination: World) -> None:
    """Copy a stable history into an empty disposable candidate; never overwrite a world."""
    with locked(world.path):
        if destination.log.stat().st_size or destination.db.exists():
            raise LogError("candidate destination must be an empty new world")
        destination.log.write_bytes(world.log.read_bytes())


def put_blob(world: World, data: bytes) -> str:
    """Store bytes by content hash. Idempotent; the hash is the reference."""
    digest = hashlib.sha256(data).hexdigest()
    target = world.blobs / digest
    if not target.exists():
        world.blobs.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(f".{secrets.token_hex(8)}.part")
        try:
            with tmp.open("xb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            tmp.replace(target)
        finally:
            tmp.unlink(missing_ok=True)
    return digest


def get_blob(world: World, digest: str) -> bytes:
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise LogError("blob reference must be a lowercase SHA-256 digest")
    return (world.blobs / digest).read_bytes()


def _ends_with_newline(path: Path) -> bool:
    with open(path, "rb") as handle:
        handle.seek(-1, os.SEEK_END)
        return handle.read(1) == b"\n"
