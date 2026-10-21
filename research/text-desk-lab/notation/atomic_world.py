"""Internal, bounded data mutations; no Desk command or HTTP endpoint enables this.

Admission belongs to deskd.Session, under its ordinary writer lock. Preparation
uses actual Desk mutation checks on a private candidate, never rollback callbacks.
Rules outside the data-only subset refuse this operation (ordinary rules and
batches retain their existing semantics). See atomic-world/ARCHITECTURE.md.
"""
from copy import deepcopy
import hashlib
import json
import os
import re
from types import MethodType

import store
from world import Refusal

MAX_STEPS = 16
MAX_BYTES = 32768
MAX_RECORD_BYTES = 262144
PROPS = frozenset({"target", "lens", "workspace", "panel_state", "layout_state", "panel_order"})
PANEL_PROPS = frozenset({"shows", "lens", "shelf"})
IDENT = re.compile(r"(?:[af]\d+|@[a-z][a-z0-9_]{0,23})\Z")
OP_ID = re.compile(r"[a-zA-Z0-9_-]{16,80}\Z")


class UnknownCommit(RuntimeError):
    """Do not repeat a create: reopen the writer Session and reconcile this ID."""


class UnsafePreparation(RuntimeError):
    pass


def _json(value):
    return json.dumps(store.plain(value), sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))


def capture(desk):
    """A conservative read fence, not authentication or an authority token."""
    w = desk.world
    value = [w.me, getattr(desk, "_window", "") or "",
             sorted(store.flatten(w).items()), w.events,
             getattr(w, "_ids", 0), getattr(w, "_eseq", 0),
             sorted((i, n["rev"]) for i, n in w.nodes.items()),
             sorted((i, s["rev"]) for i, s in w.subjects.items())]
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _validate(verb, target, args):
    if not isinstance(target, str) or not IDENT.fullmatch(target):
        raise Refusal("atomic targets are literal surface/appearance IDs or earlier local aliases")
    if not isinstance(args, dict) or not args or any(
            not isinstance(k, str) or not isinstance(v, str) for k, v in args.items()):
        raise Refusal("atomic arguments are nonempty string maps")
    if len(_json(args).encode("utf-8")) > MAX_BYTES:
        raise Refusal("atomic action arguments are too large")
    if verb == "create":
        if args.get("kind") == "surface":
            if set(args) - {"kind", "title", "layout"}:
                raise Refusal("atomic surface create takes only kind, title and layout")
            if args.get("layout", "column") not in {"free", "row", "column"}:
                raise Refusal("atomic surface layout must be free/row/column")
        elif args.get("kind") == "note":
            if (set(args) - (PANEL_PROPS | {"kind", "title", "role", "actor"}) or
                    args.get("role") != "home-panel" or not args.get("actor") or not args.get("lens")):
                raise Refusal("atomic note create only makes an actor-owned home-panel with a lens")
        else:
            raise Refusal("atomic create only makes surfaces or typed home-panel notes")
        if not args.get("title"):
            raise Refusal("atomic create needs title")
    elif verb == "prop":
        if set(args) - (PROPS | PANEL_PROPS):
            raise Refusal("atomic prop only writes declared panel/layout data fields")
    elif verb == "move":
        if set(args) != {"into"} or not IDENT.fullmatch(args["into"]):
            raise Refusal("atomic move takes one literal into surface")
    else:
        raise Refusal("atomic operations are create, prop and move, never command text")
    if "shelf" in args and args["shelf"] not in {"yes", "no"}:
        raise Refusal("atomic shelf is yes or no")
    if "shows" in args and not re.fullmatch(r"[af]\d+", args["shows"]):
        raise Refusal("atomic shows needs one literal existing appearance or surface")


def _request(observed, steps):
    if not isinstance(observed, str) or not re.fullmatch(r"[0-9a-f]{64}", observed):
        raise Refusal("atomic operation needs its observed world fence")
    if not isinstance(steps, list) or not 1 <= len(steps) <= MAX_STEPS:
        raise Refusal(f"atomic operation needs 1..{MAX_STEPS} typed steps")
    for step in steps:
        if not isinstance(step, dict) or set(step) - {"verb", "target", "args", "as"}:
            raise Refusal("unknown atomic step field")
        _validate(step.get("verb"), step.get("target"), step.get("args"))
        if "as" in step and (step["verb"] != "create" or
                             not isinstance(step["as"], str) or
                             not re.fullmatch(r"[a-z][a-z0-9_]{0,23}", step["as"])):
            raise Refusal("only create may name a local alias")
    body = _json({"observed": observed, "steps": steps})
    if len(body.encode("utf-8")) > MAX_BYTES:
        raise Refusal("atomic request is too large")
    return json.loads(body), hashlib.sha256(body.encode("utf-8")).hexdigest()


def restore_metadata(desk, record):
    """Called by ordinary log recovery, not by an external caller."""
    meta = record.get("atomic_world")
    if not meta:
        return
    desk._rulestate = deepcopy(meta["rule_state"])
    for rule in desk._rulestate.values():
        # _rules_sync compares a native signature tuple. JSON's list would
        # otherwise look like a changed rule and silently re-arm its cursor.
        rule["sig"] = tuple(rule["sig"])
        rule["done"] = set(rule["done"]["$set"])
    for eid in meta.get("undone_events", []):
        event = desk.world.event_by_id(eid)
        if event:
            event["undone"] = True


def _recover(session, log):
    # A full line may exist after an ambiguous fsync failure. Establish durability
    # before replay/receipt lookup; a further failure admits no operation.
    _outside_command(session.desk)
    try:
        with open(log.path, "r+b") as stream:
            stream.flush()
            os.fsync(stream.fileno())
        candidate = deepcopy(session.desk)
        store.catch_up(candidate, session.path)
        flat, _, state = log.flat()
        if store.flatten(candidate.world) != flat or store.digest(flat) != state:
            raise UnknownCommit("atomic journal and loaded world differ; repair/reload before admission")
        _publish(session, candidate)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise UnknownCommit("journal durability unavailable; reconcile before another write") from exc


def receipt(desk, log, actor, window, operation_id, digest=None):
    """Internal lookup after recovery; use Session.atomic_status for reconciliation."""
    found = log.find(lambda r: (r.get("atomic_world") or {}).get("key") ==
                     [actor, window, operation_id])
    if found is None:
        return None
    meta = found["atomic_world"]
    if digest is not None and meta["request"] != digest:
        raise Refusal("operation ID already belongs to a different request")
    result = deepcopy(meta["result"])
    result["record"] = found["seq"]
    events = [desk.world.event_by_id(e) for e in result["events"]]
    if any(e and e.get("undone") for e in events):
        result["status"] = "undone"
    return result


def status(session, operation_id):
    """Reconcile only: never admit a create, even when the receipt is absent."""
    if not isinstance(operation_id, str) or not OP_ID.fullmatch(operation_id):
        raise Refusal("atomic status needs a stable operation ID")
    desk = session.desk
    if desk.world.me != session.actor:
        raise Refusal("writer actor changed during atomic reconciliation")
    log = store.Log(store.log_path(session.path))
    if not log.exists() or not log.head() or not getattr(desk, "_snap_at", None):
        raise Refusal("atomic reconciliation requires an established recoverable journal")
    _recover(session, log)
    return receipt(desk, log, session.actor, getattr(desk, "_window", "") or "",
                   operation_id) or {"status": "absent", "operation": operation_id}


def _outside_command(desk):
    if (getattr(desk, "_store", None) is not None or getattr(desk, "_in_rules", False)
            or getattr(desk, "_verb_depth", 0) or getattr(desk, "_ctxs", None)):
        raise Refusal("atomic admission must be outside an ordinary command/rule context")


def _candidate(desk, steps, undo_event=None, log=None):
    if desk.hooks:
        raise Refusal("custom mutation hooks need a reviewed data-only effects boundary")
    _outside_command(desk)
    candidate = deepcopy(desk)
    candidate.__dict__.pop("_store", None)
    saved_hooks = candidate.hooks
    candidate.hooks = []
    native = candidate.cmd_do_knife
    fire = candidate._fire
    calls = 0

    def bounded(self, verb, positional, args):
        nonlocal calls
        if len(positional) != 1:
            raise UnsafePreparation("atomic actions need one literal target")
        try:
            _validate(verb, positional[0], args)
        except Refusal as exc:
            raise UnsafePreparation(str(exc)) from exc
        target = positional[0]
        node = self.world.nodes.get(target) or {}
        if node.get("type") != "surface":
            subject = self.world.subjects.get(node.get("subject")) or {}
            props = subject.get("props") or {}
            if (verb == "create" or subject.get("kind") != "note" or subject.get("tags") or
                    props.get("role") != "home-panel" or props.get("actor") != self.world.me):
                raise UnsafePreparation("atomic mutations only change surfaces or own untagged home-panel notes")
            if verb == "prop" and set(args) - PANEL_PROPS:
                raise UnsafePreparation("atomic panel prop only changes shows, lens and shelf")
        if verb == "create" and args["kind"] == "note" and args["actor"] != self.world.me:
            raise UnsafePreparation("atomic panel actor must be the current writer")
        if "shows" in args:
            source = args["shows"]
            if source not in self.world.nodes or source not in self.seen:
                raise UnsafePreparation("atomic panel source has not been looked at")
            self.world.fence(source, self.seen[source])
        calls += 1
        if calls > MAX_STEPS:
            raise UnsafePreparation("atomic mutation/rule budget exhausted")
        return native(verb, positional, dict(args))

    def safe_fire(self, rule, item):
        if rule.get("world"):
            raise UnsafePreparation("world-verb rules need a separately reviewed effects boundary")
        return fire(rule, item)

    def safe_stopped(self, active, chain, cause):
        if any(self._rule_pending(rule) for rule in active):
            raise UnsafePreparation("atomic rule chain did not settle")

    candidate.cmd_do_knife = MethodType(bounded, candidate)
    candidate._fire = MethodType(safe_fire, candidate)
    candidate._rules_stopped = MethodType(safe_stopped, candidate)
    try:
        candidate._rules_sync(say=False)
        failed0 = sum(r.get("failed", 0) for r in (candidate._rulestate or {}).values())
        aliases = {}

        def resolve(value):
            if not value.startswith("@"):
                return value
            if value[1:] not in aliases:
                raise Refusal("atomic alias has not been created")
            return aliases[value[1:]]

        n0 = len(candidate.world.events)
        if undo_event:
            flat = store.flatten(candidate.world)
            candidate._store = store.Ctx(log, flat, store.digest(flat), n0, {})
            candidate.cmd_undo(undo_event)
        for step in steps:
            args = {k: resolve(v) if k == "into" else v for k, v in step["args"].items()}
            bounded(candidate, step["verb"], [resolve(step["target"])], args)
            if "as" in step:
                if step["as"] in aliases:
                    raise Refusal("atomic alias is already used")
                aliases[step["as"]] = candidate.world.last_created
        # Rules see only final explicit placement, on the isolated real world.
        if len(candidate.world.events) > n0:
            candidate._run_rules(cause=candidate.world.events[-1]["id"])
        failed1 = sum(r.get("failed", 0) for r in (candidate._rulestate or {}).values())
        if failed1 != failed0:
            raise Refusal("an atomic rule action refused; nothing admitted")
    except UnsafePreparation as exc:
        raise Refusal(f"atomic preparation refused: {exc}") from exc
    finally:
        candidate.__dict__.pop("cmd_do_knife", None)
        candidate.__dict__.pop("_fire", None)
        candidate.__dict__.pop("_rules_stopped", None)
        candidate.__dict__.pop("_store", None)
        candidate.hooks = saved_hooks
    return candidate, aliases


def _publish(session, candidate):
    # Preserve the Desk object held by Session and its caller. No event observer
    # can run between these updates: the ordinary writer lock is still held.
    session.desk.__dict__.clear()
    session.desk.__dict__.update(candidate.__dict__)
    session.per = session.desk._per


def execute(session, operation_id, observed, steps):
    """Called ONLY by Session.atomic while its ordinary writer lock is held."""
    body, request_hash = _request(observed, steps)
    return _admit(session, operation_id, body, request_hash)


def undo(session, operation_id, observed, original_operation):
    if not isinstance(original_operation, str) or not OP_ID.fullmatch(original_operation):
        raise Refusal("atomic undo needs the original operation ID")
    if not isinstance(observed, str) or not re.fullmatch(r"[0-9a-f]{64}", observed):
        raise Refusal("atomic undo needs its observed world fence")
    body = {"observed": observed, "undo_of": original_operation, "steps": []}
    request_hash = hashlib.sha256(_json(body).encode("utf-8")).hexdigest()
    return _admit(session, operation_id, body, request_hash)


def _admit(session, operation_id, body, request_hash):
    if not isinstance(operation_id, str) or not OP_ID.fullmatch(operation_id):
        raise Refusal("atomic operation needs a stable 16..80 character ID")
    desk = session.desk
    actor, window = session.actor, getattr(desk, "_window", "") or ""
    if desk.world.me != actor:
        raise Refusal("writer actor changed during atomic admission")
    log = store.Log(store.log_path(session.path))
    if not log.exists() or not log.head() or not getattr(desk, "_snap_at", None):
        raise Refusal("atomic admission requires an established recoverable journal")
    _recover(session, log)
    old = receipt(desk, log, actor, window, operation_id, request_hash)
    if old:
        return old
    if capture(desk) != body["observed"]:
        raise Refusal("stale atomic source/layout/membership/receiver fence; read again")
    flat0 = store.flatten(desk.world)
    n0 = len(desk.world.events)
    undo_event = None
    if body.get("undo_of"):
        original = receipt(desk, log, actor, window, body["undo_of"])
        if not original or original["status"] != "committed":
            raise Refusal("original atomic operation is missing or already undone")
        undo_event = original["events"][0]
    candidate, aliases = _candidate(desk, body["steps"], undo_event, log)
    # No awaits/callbacks/lock release between revalidation, preparation and log.
    if capture(desk) != body["observed"] or desk.world.me != actor:
        raise Refusal("world changed during atomic preparation")
    events = candidate.world.events[n0:]
    if not events:
        raise Refusal("atomic request changed nothing")
    for event in events:
        event["atomic_world"] = [actor, window, operation_id]
        # Whole undo reads the journal's before-facts, never a primitive undo
        # copy. Keep create identity because native event rules use it.
        deleted = (event.get("undo") or {}).get("delete")
        event["undo"] = {"delete": deleted} if deleted else {}
    flat1 = store.flatten(candidate.world)
    facts = store.diff(flat0, flat1)
    parts = [{"cause": event.get("via", "") if event.get("via", "").startswith("rule ") else "act",
              "e": event["id"], "verb": event["verb"],
              "target": event["target"], "args": store.plain(event.get("args") or {}),
              "event": store.plain(event), "facts": []} for event in events]
    parts[0]["facts"] = store._enc(facts, flat0)
    result = {"status": "committed", "operation": operation_id, "aliases": aliases,
              "events": [e["id"] for e in events]}
    record = {"state": store.digest(flat1), "at": store._now(), "by": actor,
              "words": "atomic data mutation", "parts": parts,
              "ids": candidate.world._ids, "eseq": candidate.world._eseq,
              "atomic_world": {"key": [actor, window, operation_id],
                               "request": request_hash, "result": result,
                               "rule_state": store.plain(candidate._rulestate or {}),
                               "undone_events": [
                                   new["id"] for old, new in zip(desk.world.events, candidate.world.events)
                                   if new.get("undone") and not old.get("undone")]}}
    wire = {"seq": log.head()[0] + 1, "shape": store.SHAPE, **record}
    if len((json.dumps(wire, ensure_ascii=False) + "\n").encode("utf-8", "surrogatepass")) > MAX_RECORD_BYTES:
        raise Refusal("atomic result exceeds its bounded journal record size")
    try:
        seq = log.append(record, flat1)  # strict: never safe_commit
        candidate._snap_at = (seq, log.path.stat().st_size)
        _publish(session, candidate)
    except Exception as exc:
        # The complete record may already exist. Evict/reload rather than saving
        # the old world over it or treating the failure as a refused create.
        session._atomic_unknown = True
        raise UnknownCommit("atomic outcome unknown; reopen Session and reconcile the same operation ID") from exc
    return {**deepcopy(result), "record": seq}
