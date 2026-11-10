"""The entry service's own store: accounts, invites, sign-in requests, sessions.

SQLite, one file under the data folder. This holds who you are, never what you
may do inside the place; that is the kernel's (see SEAM.md). The one exception
is the `roles` table, a stand-in for the kernel's answer until it exists.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id              TEXT PRIMARY KEY,
    email           TEXT UNIQUE,
    email_verified  INTEGER NOT NULL DEFAULT 1,
    google_sub      TEXT UNIQUE,
    display_name    TEXT,
    suggested_name  TEXT,
    invite_id       TEXT,
    created_at      INTEGER NOT NULL,
    updated_at      INTEGER NOT NULL,
    onboarded_at    INTEGER,
    disabled_at     INTEGER,
    kernel_person   TEXT,
    kernel_refused  TEXT,
    guest_until     INTEGER,
    guest_claim_hash TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS answers (
    account_id      TEXT NOT NULL,
    key             TEXT NOT NULL,
    value           TEXT NOT NULL,
    questions_version INTEGER NOT NULL,
    answered_at     INTEGER NOT NULL,
    PRIMARY KEY (account_id, key)
);
CREATE TABLE IF NOT EXISTS invites (
    id              TEXT PRIMARY KEY,
    code            TEXT NOT NULL UNIQUE,
    maker_id        TEXT NOT NULL,
    channel         TEXT NOT NULL,
    kind            TEXT NOT NULL DEFAULT 'link',
    max_uses        INTEGER,
    uses            INTEGER NOT NULL DEFAULT 0,
    expires_at      INTEGER NOT NULL,
    frozen_at       INTEGER,
    frozen_by       TEXT,
    created_at      INTEGER NOT NULL,
    guest_ok        INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS invite_uses (
    invite_id       TEXT NOT NULL,
    account_id      TEXT NOT NULL UNIQUE,
    at              INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS email_requests (
    id              TEXT PRIMARY KEY,
    email           TEXT NOT NULL,
    token_hash      TEXT UNIQUE,
    code_hash       TEXT,
    invite_id       TEXT,
    created_at      INTEGER NOT NULL,
    expires_at      INTEGER NOT NULL,
    used_at         INTEGER,
    attempts        INTEGER NOT NULL DEFAULT 0,
    guest_id        TEXT
);
CREATE INDEX IF NOT EXISTS email_requests_email ON email_requests(email);
CREATE TABLE IF NOT EXISTS oidc_flows (
    id              TEXT PRIMARY KEY,
    state           TEXT NOT NULL,
    nonce           TEXT NOT NULL,
    verifier        TEXT NOT NULL,
    invite_id       TEXT,
    created_at      INTEGER NOT NULL,
    used_at         INTEGER
);
CREATE TABLE IF NOT EXISTS sessions (
    id_hash         TEXT PRIMARY KEY,
    account_id      TEXT NOT NULL,
    method          TEXT NOT NULL,
    created_at      INTEGER NOT NULL,
    last_seen       INTEGER NOT NULL,
    expires_at      INTEGER NOT NULL,
    revoked_at      INTEGER,
    user_agent      TEXT
);
CREATE INDEX IF NOT EXISTS sessions_account ON sessions(account_id);
CREATE TABLE IF NOT EXISTS rate (
    key             TEXT PRIMARY KEY,
    window          INTEGER NOT NULL,
    count           INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS roles (
    account_id      TEXT NOT NULL,
    role            TEXT NOT NULL,
    granted_at      INTEGER NOT NULL,
    granted_by      TEXT NOT NULL,
    PRIMARY KEY (account_id, role)
);
CREATE TABLE IF NOT EXISTS settings (
    key             TEXT PRIMARY KEY,
    value           TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    seq             INTEGER PRIMARY KEY AUTOINCREMENT,
    at              INTEGER NOT NULL,
    kind            TEXT NOT NULL,
    account_id      TEXT,
    data            TEXT NOT NULL
);
"""


class Store:
    """One SQLite file, one connection per thread."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._raw().executescript(SCHEMA)
        self._add_columns("accounts", {"kernel_person": "TEXT", "kernel_refused": "TEXT",
                                       "guest_until": "INTEGER"})
        self._add_columns("invites", {"guest_ok": "INTEGER NOT NULL DEFAULT 0"})
        self._add_columns("email_requests", {"guest_id": "TEXT"})
        self._rename_column("sessions", "agent", "user_agent")
        self._email_may_be_empty()
        self._raw().execute("CREATE UNIQUE INDEX IF NOT EXISTS accounts_guest_claim"
                            " ON accounts(guest_claim_hash)")

    def _email_may_be_empty(self) -> None:
        """Guests (5 Nov) have no email: rebuild a store made when `email` was NOT NULL.

        SQLite cannot drop NOT NULL in place, so the table is copied in one transaction.
        """
        conn = self._raw()
        cols = {r["name"]: r for r in conn.execute("PRAGMA table_info(accounts)")}
        if not cols["email"]["notnull"]:
            return
        if "guest_claim_hash" not in cols:
            conn.execute("ALTER TABLE accounts ADD COLUMN guest_claim_hash TEXT")
        create = SCHEMA.split("CREATE TABLE IF NOT EXISTS accounts", 1)[1].split(");", 1)[0] + ")"
        names = ", ".join(r["name"] for r in conn.execute("PRAGMA table_info(accounts)"))
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute("CREATE TABLE accounts_new" + create)
            conn.execute(f"INSERT INTO accounts_new({names}) SELECT {names} FROM accounts")
            conn.execute("DROP TABLE accounts")
            conn.execute("ALTER TABLE accounts_new RENAME TO accounts")
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

    def _add_columns(self, table: str, columns: dict[str, str]) -> None:
        have = {r["name"] for r in self._raw().execute(f"PRAGMA table_info({table})")}
        for name, kind in columns.items():
            if name not in have:
                self._raw().execute(f"ALTER TABLE {table} ADD COLUMN {name} {kind}")

    def _rename_column(self, table: str, old: str, new: str) -> None:
        have = {r["name"] for r in self._raw().execute(f"PRAGMA table_info({table})")}
        if old in have and new not in have:
            self._raw().execute(f"ALTER TABLE {table} RENAME COLUMN {old} TO {new}")

    def _raw(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.path, timeout=10, isolation_level=None)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=10000")
            self._local.conn = conn
        return conn

    def connect(self) -> _Tx:
        return _Tx(self._raw())

    def one(self, sql: str, args: tuple = ()) -> sqlite3.Row | None:
        return self._raw().execute(sql, args).fetchone()

    def all(self, sql: str, args: tuple = ()) -> list[sqlite3.Row]:
        return self._raw().execute(sql, args).fetchall()

    def run(self, sql: str, args: tuple = ()) -> int:
        return self._raw().execute(sql, args).rowcount

    def event(self, conn: sqlite3.Connection | None, at: int, kind: str,
              account_id: str | None, /, **data) -> None:
        target = conn if conn is not None else self._raw()
        target.execute(
            "INSERT INTO events(at, kind, account_id, data) VALUES (?,?,?,?)",
            (at, kind, account_id, json.dumps(data, sort_keys=True)),
        )


class _Tx:
    """`with store.connect() as conn:` runs one IMMEDIATE transaction."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def __enter__(self) -> sqlite3.Connection:
        self.conn.execute("BEGIN IMMEDIATE")
        return self.conn

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is None:
            self.conn.execute("COMMIT")
        else:
            self.conn.execute("ROLLBACK")
