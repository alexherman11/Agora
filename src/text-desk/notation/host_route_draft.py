"""DISABLED review draft, not an authenticated service or a host executor.

ReferenceModel exercises policy with fake attestors and a fake inventory.
There is deliberately no house/MCP/HTTP hook, process API, shell, or production
enable switch. A caller-supplied Python object is not OS authentication.
See src/codex/host-route-review.md for integration prerequisites.
"""
from dataclasses import dataclass
import json
import sqlite3
import threading
import uuid


OPERATION = "agora.processes.read"


@dataclass(frozen=True)
class Binding:
    card: str
    worker: str
    generation: str


@dataclass(frozen=True)
class Issuer:
    resident: str
    session: str


@dataclass(frozen=True)
class Guards:
    awake: bool | None
    interactive_session: bool | None
    game_absent: bool | None


class Refused(Exception):
    pass


class DisabledRoute:
    """The only deployment-facing stub: always refuses, without side effects."""

    def request(self, *args, **kwargs):
        return {"status": "refused", "reason": "host route disabled pending review"}


class ReferenceModel:
    """Nondeployable policy model. All authority/OS seams MUST be test doubles.

    The supplied SQLite connection models a host-private journal. Its path,
    ACLs, process ownership and the two attestors are NOT established here.
    Opaque object handles model private parent-owned channels; none is emitted
    into a world, MCP argument, environment variable, log or receipt.
    """

    def __init__(self, db, *, issuer_attestor, worker_attestor, guards, inventory, clock):
        self.db = db
        self.issuer_attestor = issuer_attestor
        self.worker_attestor = worker_attestor
        self.guards = guards
        self.inventory = inventory
        self.clock = clock
        self.handles = {}
        self.lock = threading.RLock()
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS grants (
                id TEXT PRIMARY KEY, card TEXT, worker TEXT, generation TEXT,
                issuer_session TEXT, expires REAL, revoked INTEGER DEFAULT 0,
                used INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS requests (
                id TEXT PRIMARY KEY, grant_id TEXT, card TEXT, worker TEXT,
                generation TEXT, operation TEXT, state TEXT, receipt TEXT);
            CREATE UNIQUE INDEX IF NOT EXISTS one_active_card
                ON requests(card) WHERE state = 'running';
            CREATE UNIQUE INDEX IF NOT EXISTS one_active_inventory
                ON requests(state) WHERE state = 'running';
            CREATE TABLE IF NOT EXISTS audit (
                sequence INTEGER PRIMARY KEY, at REAL, action TEXT, detail TEXT);
        """)

    def _audit(self, action, detail):
        self.db.execute("INSERT INTO audit(at,action,detail) VALUES(?,?,?)",
                        (self.clock(), action, json.dumps(detail, sort_keys=True)))

    def _grant_id(self, handle):
        # A copied JSON/world object is not an opaque parent-owned handle.
        try:
            return self.handles.get(handle)
        except TypeError:
            return None

    def issue(self, source, binding, *, expires):
        issuer = self.issuer_attestor(source)
        if not isinstance(issuer, Issuer) or issuer.resident != "jeff" or not issuer.session:
            raise Refused("issuer is not an attested JEFF resident session")
        if not isinstance(binding, Binding) or not all(
                isinstance(x, str) and x for x in (binding.card, binding.worker, binding.generation)):
            raise Refused("card/worker/generation required")
        if not self.clock() < expires <= self.clock() + 300:
            raise Refused("grant lifetime must be at most 300 seconds")
        handle, gid = object(), uuid.uuid4().hex
        with self.lock, self.db:
            self.db.execute("INSERT INTO grants(id,card,worker,generation,issuer_session,expires) "
                            "VALUES(?,?,?,?,?,?)",
                            (gid, binding.card, binding.worker, binding.generation, issuer.session, expires))
            self._audit("issued", {"grant": gid, "card": binding.card,
                                  "issuer_session": issuer.session})
        self.handles[handle] = gid
        return handle

    def revoke(self, source, handle):
        issuer = self.issuer_attestor(source)
        if not isinstance(issuer, Issuer) or issuer.resident != "jeff" or not issuer.session:
            raise Refused("revocation requires attested JEFF session")
        gid = self._grant_id(handle)
        if not gid:
            raise Refused("unknown capability")
        with self.lock, self.db:
            self.db.execute("UPDATE grants SET revoked=1 WHERE id=?", (gid,))
            self._audit("revoked", {"grant": gid, "issuer_session": issuer.session})

    def _deny(self, request, reason):
        receipt = {"request": request, "status": "refused", "reason": reason}
        with self.db:
            self._audit("refused", receipt)
        return receipt

    def request(self, source, handle, request, *, operation=OPERATION, arguments=None):
        """No dispatch to arbitrary commands; inventory is a fake callback."""
        with self.lock:
            binding = self.worker_attestor(source)
            if not isinstance(binding, Binding):
                return self._deny(request, "caller is not an attested worker session")
            if (not isinstance(request, str) or not 0 < len(request) <= 80
                    or operation != OPERATION or arguments not in (None, {})):
                return self._deny(str(request)[:80], "operation or arguments not granted")
            gid = self._grant_id(handle)
            if not gid:
                return self._deny(request, "unknown capability")
            grant = self.db.execute(
                "SELECT card,worker,generation,expires,revoked,used FROM grants WHERE id=?",
                (gid,)).fetchone()
            if not grant or tuple(grant[:3]) != (binding.card, binding.worker, binding.generation):
                return self._deny(request, "capability binding mismatch")
            old = self.db.execute(
                "SELECT grant_id,card,worker,generation,operation,state,receipt "
                "FROM requests WHERE id=?", (request,)).fetchone()
            if old:
                if old[:5] != (gid, binding.card, binding.worker, binding.generation, operation):
                    return self._deny(request, "request identity collision")
                if old[5] == "running":
                    return {"request": request, "status": "unknown",
                            "reason": "admitted request has no terminal receipt; never replay"}
                return json.loads(old[6])
            if grant[4] or grant[3] <= self.clock() or grant[5]:
                return self._deny(request, "grant revoked, expired or already used")
            # BEGIN IMMEDIATE plus the unique partial index also fences other
            # connections using this same journal. No stale lease auto-expiry.
            try:
                self.db.execute("BEGIN IMMEDIATE")
                current = self.db.execute(
                    "SELECT revoked,used,expires FROM grants WHERE id=?", (gid,)).fetchone()
                if current[0] or current[1] or current[2] <= self.clock():
                    self.db.rollback()
                    return self._deny(request, "grant changed before admission")
                # Observe guards AFTER obtaining the executor's write fence,
                # not before a potentially blocking journal acquisition.
                try:
                    guard = self.guards()
                except Exception:
                    self.db.rollback()
                    return self._deny(request, "guard unavailable")
                if not isinstance(guard, Guards) or any(x is not True for x in (
                        guard.awake, guard.interactive_session, guard.game_absent)):
                    self.db.rollback()
                    return self._deny(request, "awake/session/no-game admission not established")
                self.db.execute("INSERT INTO requests VALUES(?,?,?,?,?,?,?,NULL)",
                                (request, gid, binding.card, binding.worker,
                                 binding.generation, operation, "running"))
                self.db.execute("UPDATE grants SET used=1 WHERE id=?", (gid,))
                self._audit("admitted", {"request": request, "card": binding.card,
                                        "operation": operation, "grant": gid,
                                        "guards": "awake/session/no-game"})
                self.db.commit()
            except sqlite3.IntegrityError:
                self.db.rollback()
                return self._deny(request, "executor/card lease or request already held")
            except sqlite3.Error:
                self.db.rollback()
                # Admission cannot be confirmed; never query or retry blindly.
                # The failed journal cannot be relied upon to record this.
                return {"request": request, "status": "unknown",
                        "reason": "journal admission unavailable; no inventory attempted"}
            try:
                result = self.inventory()
                # Fixed projected fields; do not disclose unrelated argv/output.
                fields = {"pid", "parent_pid", "created", "executable", "role"}
                if (not isinstance(result, list) or len(result) > 100
                        or any(not isinstance(row, dict) or set(row) != fields for row in result)):
                    raise ValueError("inventory did not return fixed identity fields")
                if len(json.dumps(result)) > 32768:
                    raise ValueError("inventory output too large")
                receipt = {"request": request, "status": "succeeded", "processes": result}
            except PermissionError:
                receipt = {"request": request, "status": "denied", "reason": "host access denied"}
            except Exception:
                receipt = {"request": request, "status": "unknown",
                           "reason": "inventory failed; do not infer an empty process list"}
            receipt.update(card=binding.card, worker=binding.worker,
                           generation=binding.generation, operation=operation,
                           at=self.clock(), guards="awake/session/no-game")
            # A BaseException simulates process death: the durable running entry
            # remains unknown, and no subsequent request may steal this lease.
            with self.db:
                self.db.execute("UPDATE requests SET state='terminal',receipt=? WHERE id=?",
                                (json.dumps(receipt, sort_keys=True), request))
                self._audit("terminal", receipt)
            return receipt
