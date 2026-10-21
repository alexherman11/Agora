"""Explicit follow-up obligations; no scheduler, model, host action or background timer.

The house integration is STAGED in research/followups/integration.json.
Nothing imports this module in the running product. State belongs to the single
house parent; Desk only reads its atomic public projection. World requests use
ordinary prop permission/fence checks, not a new authority route.
"""
import copy
import ctypes
import hashlib
import json
import math
import os
import re
import time
import uuid
from pathlib import Path

from world import Refusal

HERE = Path(__file__).resolve().parent
FIELDS = {"commission", "status", "usage_state", "delivery_state", "delivery_blocker",
          "waiting_on", "capability_state", "admission_state", "landed"}
KINDS = {"completion", "blocker", "quota", "admission", "capability", "delivery"}
REQUEST = "followup_request"
ACK = "followup_ack"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()[:24]


def subject(world, target):
    node = world.nodes.get(target, {})
    sid = node.get("subject", target)
    return world.subjects.get(sid) or world.nodes.get(sid)


def same(world, who, name):
    import rooms
    return rooms.same_person(world, who, name)


def issuer(world, who):
    return next((name for name in ("jeff", "alex") if same(world, who, name)), None)


def spec(value):
    keys = {"key", "revision", "recipient", "next_action", "source", "awake_seconds", "when"}
    if not isinstance(value, dict) or set(value) != keys:
        raise Refusal("follow-up needs exact typed fields: " + ", ".join(sorted(keys)))
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,40}", str(value["key"])):
        raise Refusal("follow-up key must be 1..40 letters, digits, _ or -")
    if type(value["revision"]) is not int or value["revision"] < 1:
        raise Refusal("revision must be the observed task revision")
    if not isinstance(value["recipient"], str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,59}", value["recipient"]):
        raise Refusal("recipient must be one named responsible recipient")
    if not isinstance(value["next_action"], str) or not 1 <= len(value["next_action"].strip()) <= 500:
        raise Refusal("next_action must be 1..500 characters")
    if not isinstance(value["source"], str) or not re.fullmatch(r"e[0-9]+", value["source"]):
        raise Refusal("source must name the exact source event")
    seconds = value["awake_seconds"]
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or not 1 <= seconds <= 86400:
        raise Refusal("awake_seconds must be finite, 1..86400")
    if not isinstance(value["when"], list) or not 1 <= len(value["when"]) <= 12:
        raise Refusal("when needs 1..12 property-transition predicates")
    for p in value["when"]:
        if (not isinstance(p, dict) or set(p) != {"field", "values", "kind"}
                or p["field"] not in FIELDS or p["kind"] not in KINDS
                or not isinstance(p["values"], list) or len(p["values"]) > 20
                or any(not isinstance(v, str) or len(v) > 500 for v in p["values"])):
            raise Refusal("invalid property-transition predicate; empty values means any changed value")
    return copy.deepcopy(value)


def command(desk, argv):
    """Desk seam. Writes go ONLY through ordinary cmd_do(prop); reads never run work."""
    if argv and argv[0] in ("pending", "receipts") and len(argv) == 1:
        name = getattr(desk, "_session", "")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
            raise Refusal("follow-up runtime projection unavailable for this session")
        path = HERE / "house-state" / name / "followups.json"
        # Read a snapshot, do not instantiate/recover a writer on a Desk read.
        error = path.with_suffix(".error.json")
        if error.exists():
            return canonical({"unavailable": "follow-up runtime failed; last snapshot is not current"})
        if not path.exists():
            return "followups: runtime not integrated; no delivery claim"
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return canonical({"unavailable": "follow-up journal unreadable; no delivery claim"})
        return canonical({"observed_events": state["cursor"], "world_events": len(desk.world.events),
                          argv[0]: view(state, desk.world, argv[0])})
    if len(argv) != 3 or argv[0] not in ("attach", "ack"):
        raise Refusal("followups pending|receipts OR followups attach|ack <task> '<JSON>'")
    target = desk._resolve(argv[1])
    s = subject(desk.world, target)
    if not s:
        raise Refusal("follow-up target must exist")
    try:
        value = json.loads(argv[2])
    except (TypeError, ValueError):
        raise Refusal("follow-up payload must be JSON")
    if argv[0] == "attach":
        value = spec(value)
        if not issuer(desk.world, desk.world.me):
            raise Refusal("only JEFF or Alex attaches follow-ups")
        if s["rev"] != value["revision"]:
            raise Refusal("stale task revision; read the task again")
        if not any(e["id"] == value["source"] for e in desk.world.events):
            raise Refusal("source event does not exist")
        prop = REQUEST
    else:
        if (not isinstance(value, dict) or set(value) != {"receipt"}
                or not isinstance(value["receipt"], str)
                or not re.fullmatch(r"[a-f0-9]{24}", value["receipt"])):
            raise Refusal("ack needs exactly receipt=<receipt identity>")
        # A refused actor's prop must not turn the real recipient's identical
        # acknowledgment into an ordinary no-op on this shared task.
        value["request"] = uuid.uuid4().hex
        prop = ACK
    return desk.cmd_do("prop", target, {prop: canonical(value)})


def view(state, world, mode):
    """Public operational metadata, restricted to issuer or responsible recipient."""
    visible = {k: o for k, o in state["obligations"].items()
               if same(world, world.me, o["issuer"]) or same(world, world.me, o["recipient"])}
    if mode == "pending":
        return [copy.deepcopy(o) for o in visible.values() if not o.get("settled")]
    rows = []
    for r in state["receipts"].values():
        if r["obligation"] not in visible:
            continue
        o = visible[r["obligation"]]
        rows.append(dict(copy.deepcopy(r), title=o["title"], target=o["target"],
                         source=o["source"], attached=o["attached"], next_action=o["next_action"],
                         current=copy.deepcopy(o["current"]), work_state=o["work_state"],
                         facts=[copy.deepcopy(f) for f in o["facts"] if digest(f) in r["facts"]]))
    return rows


def awake_clock():
    """Elapsed awake time, never a wake timer. Windows monotonic includes sleep."""
    if os.name == "nt":
        ticks = ctypes.c_ulonglong()
        if not ctypes.windll.kernel32.QueryUnbiasedInterruptTime(ctypes.byref(ticks)):
            raise OSError("awake clock unavailable")
        return ticks.value / 10_000_000
    return time.monotonic()


class Followups:
    def __init__(self, path, clock=awake_clock):
        self.path, self.clock = Path(path), clock
        self.state = (json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists()
                      else {"version": 1, "cursor": 0, "awake": 0., "obligations": {}, "receipts": {}, "refused": []})
        if self.state["version"] != 1:
            raise ValueError("unsupported follow-up journal")
        self.last_clock = None  # no time while parent was stopped, including restart
        for r in self.state["receipts"].values():
            if r["state"] == "attempted":
                r["state"] = "unknown"
                r["reason"] = "house ended across pipe write; not replayed"
        self.save()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(canonical(self.state))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.path)

    def fact(self, o, event, kind, field, old, new):
        f = {"event": event, "kind": kind, "field": field, "old": old, "new": new,
             "at_awake": self.state["awake"]}
        if f not in o["facts"]:
            o["facts"].append(f)

    def observe(self, world, *, running=True):
        """Called only by the existing house pass. No thread, polling model or effects."""
        t = self.clock() if running else None
        if t is not None and self.last_clock is not None:
            self.state["awake"] += max(0., t - self.last_clock)
        self.last_clock = t
        events = world.events
        if self.state["cursor"] > len(events):
            raise ValueError("world event history regressed; journal preserved")
        if self.state.get("anchor") and self.state["cursor"]:
            if self.state["anchor"] != event_anchor(events[self.state["cursor"] - 1]):
                raise ValueError("world history changed identity; journal preserved")
        for e in events[self.state["cursor"]:]:
            if e.get("undone"):
                continue
            args = e.get("args") or {}
            s = subject(world, e.get("target"))
            sid = s["id"] if s else e.get("target")
            if e["verb"] == "prop" and REQUEST in args:
                try:
                    self.attach(world, e, sid, json.loads(args[REQUEST]))
                except (Refusal, ValueError, TypeError, KeyError) as exc:
                    self.state["refused"].append({"event": e["id"], "reason": str(exc)[:240]})
            if e["verb"] == "prop" and ACK in args:
                try:
                    self.ack(world, e, sid, json.loads(args[ACK]))
                except (Refusal, ValueError, TypeError, KeyError) as exc:
                    self.state["refused"].append({"event": e["id"], "reason": str(exc)[:240]})
            for o in self.state["obligations"].values():
                if o.get("settled") or o["target"] != sid or e["id"] == o["attached"]:
                    continue
                # Only explicit ordinary property transitions; never infer quota
                # from free-form comments or synthesize capability availability.
                if e["verb"] != "prop":
                    continue
                changes = {k: str(args[k]) for k in FIELDS if k in args}
                changes.update({k: "" for k in str(args.get("remove", "")).split(",") if k in FIELDS})
                before = (e.get("undo") or {}).get("restore_subject") or {}
                previous = ({k: str(before.get("props", {}).get(k, "")) for k in FIELDS}
                            if before.get("id") == sid else dict(o["current"]))
                o["current"].update(changes)
                for p in o["when"]:
                    field = p["field"]
                    if field not in changes:
                        continue
                    old, new = previous.get(field, ""), changes[field]
                    if old != new and (not p["values"] or new in p["values"]):
                        self.fact(o, e["id"], p["kind"], field, old, new)
        self.state["cursor"] = len(events)
        self.state["anchor"] = event_anchor(events[-1]) if events else None
        for o in self.state["obligations"].values():
            # Current state is a real projection, even after undo or removal.
            # Historical receipt facts are retained; they do not imply that a
            # past transition is still the task's current condition.
            current = subject(world, o["target"])
            o["target_exists"] = current is not None
            o["current"] = ({k: str(current.get("props", {}).get(k, "")) for k in FIELDS}
                            if current else {})
            if current:
                o["title"] = current.get("title", o["title"])
            if not o.get("settled") and not o["deadline_fired"] and self.state["awake"] >= o["due"]:
                o["deadline_fired"] = True
                self.fact(o, o["attached"], "deadline", "acknowledgment", "pending",
                          "awake deadline elapsed; acknowledgment absent")
        self.save()

    def attach(self, world, e, sid, payload):
        p = spec(payload)
        who = issuer(world, e.get("by"))
        if not who or e.get("via") not in (None, "prop") or e.get("cause"):
            raise Refusal("follow-up request requires a direct JEFF/Alex property act")
        # A prop's undo stores its actual prior revision. Never trust a claimed
        # revision, and don't reject a valid request merely because later events
        # arrived before this house pass.
        before = (e.get("undo") or {}).get("restore_subject") or {}
        if before.get("id") != sid or before.get("rev") != p["revision"]:
            raise Refusal("stale/unattested task revision")
        if not any(x["id"] == p["source"] for x in world.events[:world.events.index(e) + 1]):
            raise Refusal("source event is absent or in the future")
        key = digest([sid, who, p["key"]])
        previous = self.state["obligations"].get(key)
        if previous:
            if previous["spec"] == p:
                return  # idempotent attach, never reset the deadline
            raise Refusal("key already attached; use a new key for a revised action")
        current = {field: str(before.get("props", {}).get(field, "")) for field in FIELDS}
        self.state["obligations"][key] = dict(
            p, spec=p, id=key, issuer=who, target=sid, attached=e["id"],
            title=before.get("title", sid), current=current, facts=[],
            due=self.state["awake"] + p["awake_seconds"], deadline_fired=False,
            settled=False, work_state="unverified")

    def ack(self, world, e, sid, payload):
        if (not isinstance(payload, dict) or set(payload) != {"receipt", "request"}
                or not isinstance(payload["request"], str)
                or not re.fullmatch("[a-f0-9]{32}", payload["request"])):
            raise Refusal("invalid acknowledgment")
        r = self.state["receipts"].get(payload["receipt"])
        if not r:
            raise Refusal("unknown receipt; acknowledgment is not delivery")
        o = self.state["obligations"][r["obligation"]]
        if (sid != o["target"] or e.get("via") not in (None, "prop") or e.get("cause")
                or not same(world, e.get("by"), r["recipient"])):
            raise Refusal("only the exact addressed recipient acknowledges this receipt")
        # A reply to an earlier batch cannot swallow subsequent material facts.
        if r["state"] != "acknowledged":
            r.update(state="acknowledged", acknowledgment=e["id"])
        acknowledged = set()
        for row in self.state["receipts"].values():
            if row["obligation"] == o["id"] and row["state"] == "acknowledged":
                acknowledged.update(row["facts"])
        if all(digest(f) in acknowledged for f in o["facts"]):
            o["settled"] = True  # only this obligation; task stays untouched

    def dispatch(self, world, residents):
        """Queue while busy/rest=off; pipe-written != recipient acknowledgment.

        Unknown attempts are never blindly replayed. New material facts or the
        one deadline can produce a new batch; facts already attempted stay named
        in receipts. An unavailable outside recipient is NOT treated as delivered.
        """
        for o in self.state["obligations"].values():
            if o.get("settled"):
                continue
            attempted = {fid for r in self.state["receipts"].values()
                         if r["obligation"] == o["id"]
                         and r["state"] in ("attempted", "unknown", "pipe-written", "acknowledged")
                         for fid in r["facts"]}
            facts = [f for f in o["facts"] if digest(f) not in attempted]
            if not facts:
                continue
            # An unacknowledged deadline is an owner follow-through obligation.
            recipient = o["issuer"] if any(f["kind"] == "deadline" for f in facts) else o["recipient"]
            if any(f["kind"] == "deadline" for f in facts):
                facts = list(o["facts"])  # owner sees everything still needing follow-through
            batch = [digest(f) for f in facts]
            key = digest([o["id"], recipient, batch])
            # Retain even superseded queue receipts; never erase delivery history.
            for rid, r in self.state["receipts"].items():
                if r["obligation"] == o["id"] and r["state"] == "queued" and rid != key:
                    r.update(state="coalesced", into=key)
            r = self.state["receipts"].setdefault(
                key, {"id": key, "obligation": o["id"], "recipient": recipient, "facts": batch,
                      "state": "queued", "reason": "recipient unavailable",
                      "at_awake": self.state["awake"]})
            matches = [res for res in residents.values()
                       if same(world, (world.nodes.get(res.rid, {}).get("props") or {}).get("actor", ""), recipient)]
            res = matches[0] if len(matches) == 1 else None
            if res is None:
                self.save()
                continue
            props = world.nodes[res.rid].get("props") or {}
            if props.get("want", "awake") != "awake" or not res.alive() or res.busy:
                r["reason"] = "busy/resting/offline; pending"
                self.save()
                continue
            r.update(state="attempted", reason="saved before pipe write",
                     attempted_awake=self.state["awake"])
            self.save()
            text = ("Follow-up " + key + ": " + o["title"] + "\n"
                    + "Source " + o["source"] + "; attached " + o["attached"] + "\n"
                    + canonical(facts) + "\nTarget exists: " + str(o.get("target_exists", True))
                    + "\nCurrent: " + canonical(o["current"]) + "\n"
                    + "Responsible: " + o["recipient"] + "; pending action: " + o["next_action"] + "\n"
                    + "Acknowledge this receipt explicitly; acknowledgment does not complete the task.")
            try:
                res.send(text, "news")
                # Existing Resident.send only attests a successful pipe flush.
                written = bool((res.state.get("pending") or {}).get("delivered"))
                r.update(state="pipe-written" if written else "unknown",
                         reason="pipe flush only; recipient acknowledgment absent" if written else "write outcome unknown")
            except Exception:
                r.update(state="unknown", reason="send failed; no automatic replay")
            self.save()


def event_anchor(e):
    # Undo can legitimately mark an older event undone; that flag is not identity.
    return digest({k: e.get(k) for k in ("id", "target", "verb", "by", "args")})


class HouseBridge:
    """A follow-up fault freezes ONLY this mechanism, leaving ordinary work alone."""
    def __init__(self, path, clock=awake_clock):
        self.path, self.failed, self.engine = Path(path), False, None
        try:
            self.engine = Followups(path, clock)
            self.path.with_suffix(".error.json").unlink(missing_ok=True)
        except Exception as exc:
            self.fail(exc)

    def fail(self, exc):
        self.failed = True
        # Operational failure class only; never serialize arbitrary exception text.
        print("house: followups unavailable: " + type(exc).__name__, flush=True)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.with_suffix(".error.json").write_text(
                canonical({"state": "unavailable", "reason": type(exc).__name__}), encoding="utf-8")
        except OSError:
            pass  # stdout remains an explicit failure receipt

    def observe(self, world):
        if not self.failed:
            try:
                self.engine.observe(world)
            except Exception as exc:
                self.fail(exc)

    def dispatch(self, world, residents):
        if not self.failed:
            try:
                self.engine.dispatch(world, residents)
            except Exception as exc:
                self.fail(exc)
