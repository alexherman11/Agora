"""Durable native event journal and its rebuildable projection.
Never execute authored code or accept writes without an authenticated gateway caller.
"""

import json
import re
import sqlite3
import threading
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path


class Refusal(ValueError):
    """An instructive rejection that leaves the native world unchanged."""


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}", value):
        raise Refusal("Use an id of 1–160 letters, numbers, dots, colons, underscores or hyphens.")
    return value


class World:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "world.db"
        self.lock = threading.RLock()
        with self.connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY, version INTEGER NOT NULL,
                    actor TEXT NOT NULL, at TEXT NOT NULL, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS objects (
                    id TEXT PRIMARY KEY, revision INTEGER NOT NULL, body TEXT NOT NULL);
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA synchronous=FULL")
        try:
            yield db
        finally:
            db.close()

    def get(self, object_id):
        identifier(object_id)
        with self.connection() as db:
            row = db.execute("SELECT body FROM objects WHERE id=?", (object_id,)).fetchone()
        if row is None:
            raise Refusal(
                f"Object {object_id!r} does not exist. Create it with expected_revision=0."
            )
        return json.loads(row[0])

    def query(self, facets=None, limit=200, after="", reverse=False):
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise Refusal("Query limit must be an integer from 1 to 1000.")
        if not isinstance(facets or [], list) or not all(isinstance(f, str) for f in facets or []):
            raise Refusal("facets must be a list of facet type names.")
        if type(reverse) is not bool or not isinstance(after, str):
            raise Refusal("reverse must be a boolean and after must be an object id string.")
        with self.connection() as db:
            db.execute("BEGIN")
            watermark = db.execute("SELECT coalesce(max(seq),0) FROM events").fetchone()[0]
            order, comparison = ("DESC", "<") if reverse else ("ASC", ">")
            condition = f" WHERE id{comparison}?" if after else ""
            rows = db.execute(
                f"SELECT body FROM objects{condition} ORDER BY id {order}",
                (after,) if after else (),
            )
            items = []
            for row in rows:
                obj = json.loads(row[0])
                if all(f in obj["facets"] for f in facets or []):
                    items.append(obj)
                    if len(items) > limit:
                        break
        complete = len(items) <= limit
        items = items[:limit]
        return {
            "items": items,
            "watermark": watermark,
            "complete": complete,
            "next_after": None if complete else items[-1]["id"],
        }

    def commit(self, actor, changes, validate, *, guards=None, watermark=None):
        """The gateway's sole mutation primitive: validate the entire batch, then commit once."""
        identifier(actor)
        if not isinstance(changes, list) or not 1 <= len(changes) <= 200:
            raise Refusal("A transaction needs 1–200 object changes.")
        if len(encoded(changes).encode()) > 4_000_000:
            raise Refusal("A transaction is limited to 4 MB of JSON.")
        with self.lock, self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                current_watermark = db.execute(
                    "SELECT coalesce(max(seq),0) FROM events"
                ).fetchone()[0]
                if watermark is not None and watermark != current_watermark:
                    raise Refusal("The candidate's input snapshot is stale; exercise it again.")
                for obj_id, expected in (guards or {}).items():
                    row = db.execute(
                        "SELECT revision FROM objects WHERE id=?", (obj_id,)
                    ).fetchone()
                    if (row[0] if row else 0) != expected:
                        raise Refusal(
                            f"Stale dependency {obj_id}; read the current revision and retry."
                        )
                seen, updated = set(), []
                for change in changes:
                    if not isinstance(change, dict) or set(change) != {
                        "id",
                        "expected_revision",
                        "facets",
                    }:
                        raise Refusal(
                            "Each change requires exactly id, expected_revision and facets."
                        )
                    obj_id = identifier(change["id"])
                    if obj_id in seen:
                        raise Refusal("Change each object at most once in an atomic transaction.")
                    seen.add(obj_id)
                    expected = change["expected_revision"]
                    if type(expected) is not int or expected < 0:
                        raise Refusal("expected_revision must be a nonnegative integer; 0 creates.")
                    row = db.execute("SELECT body FROM objects WHERE id=?", (obj_id,)).fetchone()
                    old = json.loads(row[0]) if row else {"id": obj_id, "revision": 0, "facets": {}}
                    if old["revision"] != expected:
                        raise Refusal(
                            f"Stale write to {obj_id}: expected {expected}, "
                            f"current {old['revision']}."
                        )
                    facets_patch = change["facets"]
                    if not isinstance(facets_patch, dict) or not facets_patch:
                        raise Refusal(
                            "facets must contain at least one facet value; null detaches a facet."
                        )
                    validate(obj_id, old, facets_patch, db)
                    facets = dict(old["facets"])
                    for facet, value in facets_patch.items():
                        identifier(facet)
                        if value is None:
                            facets.pop(facet, None)
                        else:
                            facets[facet] = value
                    updated.append(
                        {
                            "id": obj_id,
                            "revision": expected + 1,
                            "facets": facets,
                            "written_by": actor,
                            "event": current_watermark + 1,
                        }
                    )
                at = datetime.now(UTC).isoformat()
                cursor = db.execute(
                    "INSERT INTO events(version,actor,at,body) VALUES(1,?,?,?)",
                    (actor, at, encoded({"objects": updated})),
                )
                for obj in updated:
                    db.execute(
                        "INSERT OR REPLACE INTO objects VALUES(?,?,?)",
                        (obj["id"], obj["revision"], encoded(obj)),
                    )
                db.commit()
                return {"items": updated, "watermark": cursor.lastrowid}
            except BaseException:
                db.rollback()
                raise

    def replay(self):
        """Read journal alone. No guest, models, UI or external actions participate."""
        objects = {}
        with self.connection() as db:
            for row in db.execute("SELECT version, body FROM events ORDER BY seq"):
                if row[0] != 1:
                    raise Refusal(f"Unsupported journal version {row[0]}; nothing rebuilt.")
                for obj in json.loads(row[1])["objects"]:
                    objects[obj["id"]] = obj
        return objects

    def verify(self):
        replayed = self.replay()
        with self.connection() as db:
            materialized = {
                row[0]: json.loads(row[1]) for row in db.execute("SELECT id,body FROM objects")
            }
        return {"ok": replayed == materialized, "objects": len(replayed)}

    def rebuild(self):
        with self.lock, self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                objects = self.replay()
                db.execute("DELETE FROM objects")
                for obj in objects.values():
                    db.execute(
                        "INSERT INTO objects VALUES(?,?,?)",
                        (obj["id"], obj["revision"], encoded(obj)),
                    )
                db.commit()
            except BaseException:
                db.rollback()
                raise
        return {"objects": len(objects)}
