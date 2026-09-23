"""Executable design model, not an Agora runtime or security boundary.

Native semantic registers, pinned plans, serial admission, and compensating undo.
All persistent writes use Lab.commit; observations and current grants stay outside replay.
"""

from __future__ import annotations

import json
import math
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from functools import wraps
from hashlib import sha256
from threading import RLock


class Refusal(ValueError):
    pass


def operation(function):
    """A failed contribution poisons this plan; app adapters do not commit as they go."""

    @wraps(function)
    def wrapped(builder, *args, **kwargs):
        with builder.contribution(function.__name__):
            return function(builder, *args, **kwargs)

    return wrapped


def wire(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def key(kind, identity, field):
    return (kind, identity, field)


@dataclass(frozen=True)
class Cell:
    payload: str
    version: int

    @property
    def value(self):
        return json.loads(self.payload)


@dataclass(frozen=True)
class Plan:
    actor: str
    guards: tuple
    effects: tuple
    operations: tuple
    diagnostics: tuple

    @property
    def digest(self):
        return sha256(wire(self.__dict__).encode()).hexdigest()


class Builder:
    """One immutable input snapshot, with tracked reads and disjoint effect joins."""

    def __init__(self, lab, actor):
        self.lab, self.actor = lab, actor
        with lab.lock:
            self.snapshot = {**lab.cells, **lab.observations}
        self.guards, self.effects, self.orders = {}, {}, {}
        self.operations, self.diagnostics = [], []
        self.failed = False
        self.loose = {
            "name": "explicit-change",
            "reads": set(),
            "writes": set(),
            "joins": set(),
        }
        self.traces, self.active = [self.loose], self.loose

    @contextmanager
    def contribution(self, name):
        trace = {"name": name, "reads": set(), "writes": set(), "joins": set()}
        previous, self.active = self.active, trace
        try:
            yield
        except BaseException:
            self.failed = True
            raise
        finally:
            self.traces.append(trace)
            self.active = previous

    def read(self, address):
        if address not in self.snapshot:
            raise Refusal(f"Missing address: {address}")
        cell = self.snapshot[address]
        self.guards[address] = cell.version
        self.active["reads"].add(address)
        return cell.value

    def surface(self, identity):
        self.read(key("surface", identity, "contract"))
        return self.read(key("surface", identity, "members"))

    def occurrence(self, surface, identity):
        if identity not in self.surface(surface):
            raise Refusal(f"{identity} is not a member of {surface}")
        binding = self.read(key("occurrence", identity, "binding"))
        if binding["surface"] != surface:
            raise Refusal("Occurrence belongs to another surface")
        return binding

    def effect(self, address, value):
        self.read(address)  # Write/write checks cannot be omitted by a planner.
        if address[0] == "measurement":
            raise Refusal("An observation is not a native write destination")
        if address in self.orders:
            raise Refusal("Cannot mix whole-order replacement and order constraints")
        encoded = wire(value)
        if address in self.effects and self.effects[address] != encoded:
            raise Refusal(f"Contradictory effects on {address}")
        self.effects[address] = encoded
        self.active["writes"].add(address)

    def ordering(self, address, edges):
        original = self.read(address)
        if address in self.effects:
            raise Refusal("Cannot mix order constraints and whole-order replacement")
        if len(set(original)) != len(original):
            raise Refusal("Duplicate order members")
        vertices = set(original)
        for a, b in edges:
            if a not in vertices or b not in vertices or a == b:
                raise Refusal("Invalid ordering edge")
        self.orders.setdefault(address, set()).update(edges)
        self.active["joins"].add(address)

    def describe(self, operation, surface, targets, **parameters):
        self.operations.append(
            wire(
                {
                    "operation": operation,
                    "surface": surface,
                    "targets": sorted(targets),
                    "parameters": parameters,
                }
            )
        )

    def finish(self, *, register=True):
        if self.failed:
            raise Refusal("A contribution failed; discard the whole plan and prepare again")
        effects = dict(self.effects)
        for address, edges in self.orders.items():
            original = self.snapshot[address].value
            pending, result = set(original), []
            # Stable topological order. Existing stack order breaks unconstrained ties.
            while pending:
                ready = [
                    v
                    for v in original
                    if v in pending and not any(b == v and a in pending for a, b in edges)
                ]
                if not ready:
                    raise Refusal("Contradictory ordering constraints form a cycle")
                chosen = ready[0]
                result.append(chosen)
                pending.remove(chosen)
            effects[address] = wire(result)
        # No-op reads remain guards, but unchanged cells acquire no false authorship.
        effects = {a: v for a, v in effects.items() if v != self.snapshot[a].payload}
        for reader in self.traces:
            for writer in self.traces:
                if reader is writer:
                    continue
                overlap = reader["reads"] & (writer["writes"] | writer["joins"]) & effects.keys()
                # Equal replacement effects already coalesced; order constraints have
                # their own checked join. Other dataflow needs explicit sequencing.
                overlap -= reader["writes"] & writer["writes"]
                overlap -= reader["joins"] & writer["joins"]
                if overlap:
                    raise Refusal(
                        f"Undeclared read/write dependency: {writer['name']} -> {reader['name']}: {sorted(overlap)}"
                    )
        plan = Plan(
            self.actor,
            tuple(sorted(self.guards.items())),
            tuple(sorted(effects.items())),
            tuple(sorted(self.operations)),
            tuple(self.diagnostics),
        )
        if register:
            self.lab.issue(plan)
        return plan


def validate(candidate):
    """Domain invariants apply to the entire candidate, independently of action names."""

    def value(address):
        return candidate[address].value

    surfaces = [a[1] for a in candidate if a[0] == "surface" and a[2] == "members"]
    for surface in surfaces:
        members = value(key("surface", surface, "members"))
        if len(set(members)) != len(members):
            raise Refusal("Occurrence membership is unique; duplicate subjects are allowed")
        for item in members:
            binding = value(key("occurrence", item, "binding"))
            if binding["surface"] != surface:
                raise Refusal("Membership and occurrence ownership disagree")
            placement = value(key("occurrence", item, "placement"))
            if placement["mode"] == "free":
                rect = placement["rect"]
                if len(rect) != 4 or any(
                    type(n) not in (int, float) or not math.isfinite(n) for n in rect
                ):
                    raise Refusal("Placement requires four finite numbers")
                minimum = value(key("occurrence", item, "minimum"))
                if rect[2] < minimum[0] or rect[3] < minimum[1]:
                    raise Refusal("Placement violates current minimum size")
            elif placement["mode"] != "managed":
                raise Refusal("Unknown placement mode")
        stacks = [
            a for a in candidate if a[:2] == ("surface", surface) and a[2].startswith("stack:")
        ]
        covered = []
        for address in stacks:
            stack = value(address)
            for item in stack:
                if item not in members:
                    raise Refusal("Stack contains a nonmember")
                if value(key("occurrence", item, "stratum")) != address[2][6:]:
                    raise Refusal("Stack crosses a stratum")
            covered.extend(stack)
        if sorted(covered) != sorted(members):
            raise Refusal("Every member must occur in exactly one stack")
        order_address = key("surface", surface, "reading_order")
        if order_address in candidate and sorted(value(order_address)) != sorted(members):
            raise Refusal("Reading order must be a permutation of members")
        visited, current = set(), surface
        while current is not None:
            if current in visited:
                raise Refusal("Container cycle")
            visited.add(current)
            current = value(key("surface", current, "parent"))


class Lab:
    """In-memory transaction model. No durability, browser, VM or package execution claim."""

    def __init__(self, initial):
        self.lock = RLock()
        self.genesis = {a: Cell(wire(v), 0) for a, v in initial.items()}
        self.cells = dict(self.genesis)
        self.observations, self.permissions, self.issued = {}, {}, {}
        self.events, self.requests = [], {}
        validate(self.cells)

    def builder(self, actor="alex"):
        return Builder(self, actor)

    def observe(self, identity, value):
        with self.lock:
            address = key("measurement", identity, "frame")
            old = self.observations.get(address)
            self.observations[address] = Cell(wire(value), old.version + 1 if old else 1)

    def grant(self, actor, scopes):
        with self.lock:
            self.permissions[actor] = set(scopes)

    def scope(self, address):
        if address[0] == "surface":
            return address[1]
        if address[0] == "occurrence":
            return self.cells[key("occurrence", address[1], "binding")].value["surface"]
        return f"{address[0]}:{address[1]}"

    def issue(self, plan):
        with self.lock:
            self.issued[plan.digest] = plan

    def commit(self, plan_id, *, actor, request_id):
        with self.lock:
            previous = self.requests.get((actor, request_id))
            if previous:
                if previous[0] != plan_id:
                    raise Refusal("Request ID already names a different accepted plan")
                event = self.events[previous[1]["event"] - 1]
                if not set(event["scopes"]) <= self.permissions.get(actor, set()):
                    raise Refusal("Current authority does not cover this receipt")
                return deepcopy(previous[1])
            if plan_id not in self.issued:
                raise Refusal("Unknown or altered plan; prepare again")
            plan = self.issued[plan_id]
            if actor != plan.actor:
                raise Refusal("Plan belongs to another caller")
            # Real transport must authenticate this caller; the model assumes that step.
            scopes = {self.scope(a) for a, _ in plan.effects}
            if not scopes <= self.permissions.get(actor, set()):
                raise Refusal("Current authority does not cover the complete effect set")
            current = {**self.cells, **self.observations}
            for address, expected in plan.guards:
                if address not in current or current[address].version != expected:
                    raise Refusal(f"Stale dependency: {address}")
            seq = len(self.events) + 1
            candidate = dict(self.cells)
            for address, payload in plan.effects:
                candidate[address] = Cell(payload, seq)
            validate(candidate)
            event = {
                "seq": seq,
                "actor": actor,
                "request_id": request_id,
                "scopes": sorted(scopes),
                "plan": plan.digest,
                "operations": list(plan.operations),
                "changes": [(a, self.cells[a].payload, payload) for a, payload in plan.effects],
                "identity_guards": [
                    (a, v) for a, v in plan.guards if a[2] in ("binding", "contract")
                ],
            }
            # One logical commit, including request receipt, while holding one lock.
            self.cells = candidate
            self.events.append(event)
            receipt = {"event": seq, "plan": plan.digest, "changed": len(plan.effects)}
            self.requests[(actor, request_id)] = (plan_id, deepcopy(receipt))
            return receipt

    def undo_plan(self, seq, actor="alex"):
        with self.lock:
            event = deepcopy(self.events[seq - 1])
            builder = self.builder(actor)
        # Do not guard original semantic selection: changing tags need not prevent undo.
        # Do guard identity, contract generation, and exact last writer of restored cells.
        for address, expected in event["identity_guards"]:
            builder.read(address)
            if builder.guards[address] != expected:
                raise Refusal("Undo target identity or operation contract changed")
        for address, before, after in event["changes"]:
            current = builder.read(address)
            if builder.guards[address] != seq or wire(current) != after:
                raise Refusal("Undo would overwrite a later edit, including an ABA edit")
            builder.effect(address, json.loads(before))
        builder.describe("undo", "intent", [], event=seq)
        return builder.finish()

    def replay(self):
        cells = dict(self.genesis)
        for event in self.events:
            for address, _before, after in event["changes"]:
                cells[address] = Cell(after, event["seq"])
        return cells

    def restart(self):
        """Simulated recovery: reconstruct cells and dedup receipts without running planners."""
        self.cells = self.replay()
        self.issued = {}  # Prepared-but-unaccepted previews do not survive this model's restart.
        self.requests = {
            (e["actor"], e["request_id"]): (
                e["plan"],
                {"event": e["seq"], "plan": e["plan"], "changed": len(e["changes"])},
            )
            for e in self.events
        }

    def value(self, address):
        return self.cells[address].value


def sequence(lab, actor, stages):
    """Explicit dataflow: evaluate stages in memory; admit ONE final native transaction.

    All keys already exist in this prototype. Later stages see earlier proposals;
    external guards still name the original snapshot. No stage plan is published.
    """
    with lab.lock:
        original = {**lab.cells, **lab.observations}
    virtual = dict(original)
    guards, effects, descriptions, diagnostics = {}, {}, [], []
    for index, stage in enumerate(stages):
        builder = lab.builder(actor)
        builder.snapshot = dict(virtual)
        stage(builder)
        fragment = builder.finish(register=False)
        for address, _version in fragment.guards:
            guards[address] = original[address].version
        for address, payload in fragment.effects:
            virtual[address] = Cell(payload, original[address].version)
            effects[address] = payload
        validate({a: c for a, c in virtual.items() if a[0] != "measurement"})
        descriptions.extend(
            wire({"stage": index, "operation": json.loads(op)}) for op in fragment.operations
        )
        diagnostics.extend(fragment.diagnostics)
    effects = {a: v for a, v in effects.items() if v != original[a].payload}
    plan = Plan(
        actor,
        tuple(sorted(guards.items())),
        tuple(sorted(effects.items())),
        tuple(descriptions),
        tuple(diagnostics),
    )
    lab.issue(plan)
    return plan
