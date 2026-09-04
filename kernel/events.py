"""Append and replay: the only writer of the log, and the keeper of the world directory.
Never: never edits or deletes a line, never touches the store, never logs without an actor."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
    world = World(Path(path))
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
    data = (line + "\n").encode("utf-8")
    with open(world.log, "ab") as handle:
        if handle.tell() > 0 and not _ends_with_newline(world.log):
            handle.write(b"\n")  # seal a torn tail; replay skips the torn line
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    return event


def replay(world: World, after: int = 0) -> Iterator[Event]:
    """Yield events in order with their seq.

    A line that is not JSON can only be a torn write (an append that died mid-line, sealed by
    the next append); it keeps its seq and is skipped. A JSON line missing fields is corruption.
    """
    if not world.log.exists():
        return
    with open(world.log, encoding="utf-8") as handle:
        lines = handle.read().split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    for seq, line in enumerate(lines, start=1):
        if seq <= after:
            continue
        try:
            json.loads(line)
        except json.JSONDecodeError:
            continue  # a torn write; see above
        try:
            yield Event.from_line(line, seq)
        except KeyError as exc:
            raise LogError(f"corrupt log line {seq}: missing {exc}") from exc


def count(world: World) -> int:
    return sum(1 for _ in replay(world))


def put_blob(world: World, data: bytes) -> str:
    """Store bytes by content hash. Idempotent; the hash is the reference."""
    digest = hashlib.sha256(data).hexdigest()
    target = world.blobs / digest
    if not target.exists():
        world.blobs.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".part")
        tmp.write_bytes(data)
        tmp.replace(target)
    return digest


def get_blob(world: World, digest: str) -> bytes:
    return (world.blobs / digest).read_bytes()


def _ends_with_newline(path: Path) -> bool:
    with open(path, "rb") as handle:
        handle.seek(-1, os.SEEK_END)
        return handle.read(1) == b"\n"
