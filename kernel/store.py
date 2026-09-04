"""SQLite derived from events via apply(): a cache of replay that knows where it stopped.
Never: never writes a table outside apply(), never appends to the log, never lets a row escape."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from kernel import events
from kernel.events import World
from kernel.schema import Appearance, EntityRecord, Event, FacetRecord

_DDL = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY, minted_by TEXT NOT NULL, minted_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS facets (
    entity TEXT NOT NULL, type TEXT NOT NULL, body TEXT NOT NULL, revision INTEGER NOT NULL,
    written_by TEXT NOT NULL, written_at REAL NOT NULL, PRIMARY KEY (entity, type));
"""


class Store:
    """A world's derived tables. Reads sync the tail of the log first, so they are never stale."""

    def __init__(self, world: World, db: sqlite3.Connection) -> None:
        self.world = world
        self._db = db
        self._db.executescript(_DDL)
        self._db.commit()

    # -- replay -----------------------------------------------------------------

    @property
    def last_applied(self) -> int:
        row = self._db.execute("SELECT value FROM meta WHERE key = 'last_applied'").fetchone()
        return int(row[0]) if row else 0

    def sync(self) -> int:
        """Apply every event after last_applied. Returns the new last_applied."""
        applied = self.last_applied
        for event in events.replay(self.world, after=applied):
            apply(self._db, event)
            applied = event.seq
        return applied

    # -- reads (typed records only) --------------------------------------------

    def entity(self, entity_id: str) -> EntityRecord | None:
        self.sync()
        row = self._db.execute(
            "SELECT id, minted_by, minted_at FROM entities WHERE id = ?", (entity_id,)
        ).fetchone()
        return EntityRecord(*row) if row else None

    def facet(self, entity_id: str, facet_type: str) -> FacetRecord | None:
        self.sync()
        row = self._db.execute(
            "SELECT entity, type, body, revision, written_by, written_at FROM facets "
            "WHERE entity = ? AND type = ?",
            (entity_id, facet_type),
        ).fetchone()
        return _facet(row) if row else None

    def facets(self, entity_id: str) -> list[FacetRecord]:
        self.sync()
        rows = self._db.execute(
            "SELECT entity, type, body, revision, written_by, written_at FROM facets "
            "WHERE entity = ? ORDER BY type",
            (entity_id,),
        ).fetchall()
        return [_facet(row) for row in rows]

    def appearances(self, scene_id: str) -> list[Appearance]:
        scene = self.facet(scene_id, "core.scene")
        if scene is None:
            return []
        return [Appearance.from_dict(a) for a in scene.body.get("appearances", [])]

    def snapshot(self) -> dict[str, Any]:
        """A canonical, order-independent picture of every table, for equality."""
        self.sync()
        entities = self._db.execute(
            "SELECT id, minted_by, minted_at FROM entities ORDER BY id"
        ).fetchall()
        facets = self._db.execute(
            "SELECT entity, type, body, revision, written_by, written_at FROM facets "
            "ORDER BY entity, type"
        ).fetchall()
        return {
            "last_applied": self.last_applied,
            "entities": [list(row) for row in entities],
            "facets": [list(row) for row in facets],
        }

    def close(self) -> None:
        self._db.close()


def open_store(world: World, path: str | Path | None = None) -> Store:
    """Open (or create) a world's store and replay the tail. `:memory:` gives a throwaway store."""
    target = str(path) if path is not None else str(world.db)
    # One store may be read from the shell's event loop and JEFF's worker thread in turn;
    # every access syncs first and SQLite serializes, so sharing the handle is safe.
    db = sqlite3.connect(target, check_same_thread=False)
    store = Store(world, db)
    store.sync()
    return store


def rebuild(world: World, path: str | Path | None = None) -> Store:
    """Derive a fresh store from the log alone. The only legitimate way to make a second store."""
    target = str(path) if path is not None else ":memory:"
    if target != ":memory:":
        Path(target).unlink(missing_ok=True)
    return open_store(world, target)


# -- the one mutation path -------------------------------------------------------


def apply(db: sqlite3.Connection, event: Event) -> None:
    """Fold one event into the tables and advance last_applied, in one transaction.

    Total by construction: every event was validated by a verb before it was logged,
    so apply never refuses; a log written by any past commit must fold on HEAD.
    """
    payload = event.payload
    with db:
        match event.kind:
            case "entity-minted":
                db.execute(
                    "INSERT OR IGNORE INTO entities (id, minted_by, minted_at) VALUES (?, ?, ?)",
                    (payload["entity"], event.actor, event.ts),
                )
                for facet_type, body in payload.get("facets", {}).items():
                    _upsert_facet(db, payload["entity"], facet_type, body, event)
            case "facet-attached" | "text-edited":
                _upsert_facet(db, payload["entity"], payload["type"], payload["body"], event)
            case "appearance-placed":
                _place(db, payload, event)
        db.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('last_applied', ?)",
            (str(event.seq),),
        )


def _upsert_facet(
    db: sqlite3.Connection, entity: str, facet_type: str, body: dict[str, Any], event: Event
) -> None:
    row = db.execute(
        "SELECT revision FROM facets WHERE entity = ? AND type = ?", (entity, facet_type)
    ).fetchone()
    revision = (row[0] + 1) if row else 1
    db.execute(
        "INSERT OR REPLACE INTO facets (entity, type, body, revision, written_by, written_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (entity, facet_type, _canonical(body), revision, event.actor, event.ts),
    )


def _place(db: sqlite3.Connection, payload: dict[str, Any], event: Event) -> None:
    scene = payload["scene"]
    row = db.execute(
        "SELECT body FROM facets WHERE entity = ? AND type = 'core.scene'", (scene,)
    ).fetchone()
    body = json.loads(row[0]) if row else {"appearances": []}
    placed = Appearance(payload["entity"], payload["mode"], payload["transform"]).to_dict()
    kept = [a for a in body.get("appearances", []) if a.get("entity") != payload["entity"]]
    body["appearances"] = kept + [placed]
    _upsert_facet(db, scene, "core.scene", body, event)


def _canonical(body: dict[str, Any]) -> str:
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _facet(row: tuple[Any, ...]) -> FacetRecord:
    entity, facet_type, body, revision, written_by, written_at = row
    return FacetRecord(entity, facet_type, json.loads(body), revision, written_by, written_at)
