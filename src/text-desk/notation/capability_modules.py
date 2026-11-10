"""Explicit, stateless composition of reviewed Python capabilities.

This is a contract, NOT a Python sandbox. Only the host constructs the registry.
World documents select pinned entries and bind their declared child slots; they
cannot supply imports, executable code, permissions, or effect executors.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from jsonschema import Draft202012Validator

STATUSES = frozenset({"ready", "empty", "partial", "unknown", "stale", "error"})
_SEVERITY = {s: n for n, s in enumerate(("ready", "empty", "partial", "stale", "unknown", "error"))}
_NAME = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,95}\Z")


class ContractError(ValueError):
    """An unsupported or invalid capability contract."""


def plain(value: Any, depth: int = 0) -> Any:
    """Copy JSON, accepting our frozen tuples/mappings but no object adapters."""
    if depth > 40:
        raise ContractError("JSON nesting exceeds 40")
    if isinstance(value, Mapping):
        if not all(isinstance(k, str) for k in value):
            raise ContractError("JSON object keys must be strings")
        return {k: plain(v, depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v, depth + 1) for v in value]
    if value is None or type(value) in (str, bool, int, float):
        return value
    raise ContractError(f"not a JSON value: {type(value).__name__}")


def canonical(value: Any, limit: int = 262_144) -> str:
    try:
        text = json.dumps(plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (ValueError, RecursionError) as exc:
        raise ContractError(str(exc)) from exc
    if len(text.encode("utf-8")) > limit:
        raise ContractError(f"JSON exceeds {limit} bytes")
    return text


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({k: freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(v) for v in value)
    return value


@dataclass(frozen=True)
class Port:
    """A named schema; connections require its exact schema fingerprint."""

    name: str
    schema_json: str

    @classmethod
    def of(cls, name: str, schema: dict) -> Port:
        Draft202012Validator.check_schema(schema)

        # Remote references are not a supported contract or a hidden network read.
        def check(v):
            if isinstance(v, dict):
                if "$ref" in v or "$dynamicRef" in v:
                    raise ContractError("schema references are unsupported; supply a closed schema")
                for child in v.values():
                    check(child)
            elif isinstance(v, list):
                for child in v:
                    check(child)

        check(schema)
        return cls(name, canonical(schema))

    @property
    def identity(self) -> str:
        return fingerprint([self.name, self.schema_json])

    def validate(self, value: Any) -> None:
        error = next(
            Draft202012Validator(json.loads(self.schema_json)).iter_errors(plain(value)), None
        )
        if error:
            raise ContractError(f"{self.name}: {error.message[:300]}")


@dataclass(frozen=True)
class Slot:
    input: Port
    output: Port
    ceiling: frozenset[str] = frozenset()

    def __post_init__(self):
        object.__setattr__(self, "ceiling", frozenset(self.ceiling))


@dataclass(frozen=True)
class Output:
    value: Any = None
    status: str = "ready"
    detail: str = ""


@dataclass(frozen=True)
class Definition:
    name: str
    version: str
    artifact: str
    input: Port
    output: Port
    run: Callable[[Context, Any], Output]
    requires: frozenset[str] = frozenset()
    slots: Mapping[str, Slot] = field(default_factory=dict)

    def __post_init__(self):
        if not _NAME.fullmatch(self.name) or not _NAME.fullmatch(self.version):
            raise ContractError("invalid module name or exact version")
        if not re.fullmatch(r"[0-9a-f]{64}", self.artifact):
            raise ContractError("artifact must identify reviewed source with SHA-256")
        if not all(_NAME.fullmatch(s) for s in self.slots):
            raise ContractError("invalid slot name")
        object.__setattr__(self, "requires", frozenset(self.requires))
        object.__setattr__(self, "slots", MappingProxyType(dict(self.slots)))

    @property
    def ref(self) -> str:
        return f"{self.name}@{self.version}"

    @property
    def pin(self) -> str:
        return fingerprint(
            dict(
                ref=self.ref,
                artifact=self.artifact,
                input=self.input.identity,
                output=self.output.identity,
                requires=sorted(self.requires),
                slots={
                    k: [v.input.identity, v.output.identity, sorted(v.ceiling)]
                    for k, v in self.slots.items()
                },
            )
        )


@dataclass(frozen=True)
class Limits:
    nodes: int = 32
    depth: int = 8
    calls: int = 64
    value_bytes: int = 262_144
    total_bytes: int = 2_097_152

    def __post_init__(self):
        if any(type(v) is not int or v < 1 for v in vars(self).values()):
            raise ContractError("limits must be positive integers")


@dataclass(frozen=True)
class Node:
    identity: str
    definition: Definition
    grants: frozenset[str]
    children: Mapping[str, str]


@dataclass(frozen=True)
class Prepared:
    root: str
    nodes: Mapping[str, Node]
    identity: str
    limits: Limits


class Registry:
    """A host-owned immutable allowlist, not a plugin-directory scanner."""

    def __init__(self, definitions, *, grants=(), limits=None):
        entries = {}
        for definition in definitions:
            if definition.ref in entries:
                raise ContractError(f"duplicate module: {definition.ref}")
            entries[definition.ref] = definition
        self.entries = MappingProxyType(entries)
        self.grants = frozenset(grants)
        self.limits = limits or Limits()

    def describe(self) -> list[dict]:
        return [
            dict(
                module=d.ref,
                pin=d.pin,
                artifact=d.artifact,
                execution="reviewed-python/stateless-v1",
                input=d.input.name,
                output=d.output.name,
                input_schema=json.loads(d.input.schema_json),
                output_schema=json.loads(d.output.schema_json),
                requires=sorted(d.requires),
                slots={
                    k: dict(input=s.input.name, output=s.output.name, ceiling=sorted(s.ceiling))
                    for k, s in d.slots.items()
                },
            )
            for d in self.entries.values()
        ]

    def binding(self, ref: str, *, grants=(), children=None) -> dict:
        d = self.entries[ref]
        return dict(module=ref, pin=d.pin, grants=sorted(grants), children=children or {})

    def prepare(self, document: Mapping) -> Prepared:
        doc = json.loads(canonical(document, self.limits.value_bytes))
        if (
            not isinstance(doc, dict)
            or set(doc) != {"root", "nodes"}
            or not isinstance(doc["nodes"], dict)
        ):
            raise ContractError(
                "expected only root and nodes; state/migrations/imports are unsupported"
            )
        if not 1 <= len(doc["nodes"]) <= self.limits.nodes:
            raise ContractError("node budget exceeded")
        nodes = {}
        for identity, spec in doc["nodes"].items():
            if not _NAME.fullmatch(identity) or not isinstance(spec, dict):
                raise ContractError("invalid node")
            if set(spec) != {"module", "pin", "grants", "children"}:
                raise ContractError("a node requires module, pin, grants and children only")
            if not isinstance(spec["module"], str):
                raise ContractError("module must be an exact registered reference")
            d = self.entries.get(spec["module"])
            if d is None or d.pin != spec["pin"]:
                raise ContractError(f"unavailable or changed module: {spec['module']}")
            if not isinstance(spec["grants"], list) or not all(
                isinstance(g, str) for g in spec["grants"]
            ):
                raise ContractError("grants must be strings")
            grants = frozenset(spec["grants"])
            if not d.requires <= grants <= self.grants:
                raise ContractError(
                    f"host grant ceiling or required capability violated: {identity}"
                )
            if not isinstance(spec["children"], dict) or set(spec["children"]) != set(d.slots):
                raise ContractError(f"bind exactly the declared slots: {identity}")
            nodes[identity] = Node(identity, d, grants, MappingProxyType(dict(spec["children"])))
        reached = set()
        walked = 0

        def visit(identity, path):
            nonlocal walked
            walked += 1
            if walked > self.limits.calls:
                raise ContractError("composition expansion budget exceeded")
            if not isinstance(identity, str) or identity not in nodes:
                raise ContractError(f"missing child: {identity}")
            if identity in path:
                raise ContractError("dependency cycle: " + " -> ".join((*path, identity)))
            if len(path) >= self.limits.depth:
                raise ContractError("composition depth exceeded")
            reached.add(identity)
            n = nodes[identity]
            for name, child_id in n.children.items():
                if not isinstance(child_id, str) or child_id not in nodes:
                    raise ContractError(f"missing child in slot: {name}")
                child, slot = nodes[child_id], n.definition.slots[name]
                if (child.definition.input.identity, child.definition.output.identity) != (
                    slot.input.identity,
                    slot.output.identity,
                ):
                    raise ContractError(f"typed slot mismatch: {identity}.{name}")
                if not child.grants <= n.grants & slot.ceiling:
                    raise ContractError(f"child exceeds parent or slot ceiling: {identity}.{name}")
                visit(child_id, (*path, identity))

        visit(doc["root"], ())
        if reached != set(nodes):
            raise ContractError("unreachable nodes are not admitted")
        identity = fingerprint(
            dict(contract="agora-modules/stateless-1", plan=doc, limits=vars(self.limits))
        )
        return Prepared(doc["root"], MappingProxyType(nodes), identity, self.limits)


@dataclass(frozen=True)
class Evidence:
    source: str
    revision: str
    status: str = "ready"
    detail: str = ""

    def __post_init__(self):
        if self.status not in STATUSES:
            raise ContractError("unknown observation status")
        if not all(isinstance(s, str) for s in (self.source, self.revision, self.detail)):
            raise ContractError("observation source, revision and detail must be strings")


@dataclass(frozen=True)
class Invocation:
    node: str
    module: str
    pin: str
    input_revision: str
    output_revision: str
    status: str
    detail: str
    children: tuple[Invocation, ...] = ()


@dataclass(frozen=True)
class Evaluation:
    result: Output
    interpretation: str
    observations: tuple[Evidence, ...]
    trace: Invocation | None


class Context:
    """Only declared child slots. This deliberately contains no Desk or executor."""

    def __init__(self, node, invoke, input_status):
        self._node, self._invoke = node, invoke
        self._input_status = input_status
        self._children = []

    @property
    def input_status(self):
        """Explicit upstream observation status, including retained stale input."""
        return self._input_status

    def child(self, slot: str, value: Any) -> Output:
        if slot not in self._node.children:
            raise ContractError(f"undeclared child slot: {slot}")
        result, trace = self._invoke(self._node.children[slot], value)
        self._children.append(trace)
        return result


def evaluate(prepared: Prepared, value: Any, observations=()) -> Evaluation:
    """No cache, clock, world lookup or effects. Caller supplies every observation."""
    evidence = tuple(observations)
    upstream = max((e.status for e in evidence), key=_SEVERITY.get, default="ready")
    if upstream in ("unknown", "error"):
        return Evaluation(
            Output(None, upstream, "; ".join(e.detail for e in evidence if e.detail)),
            prepared.identity,
            evidence,
            None,
        )
    calls, transferred = 0, 0

    def check(value):
        nonlocal transferred
        raw = canonical(value, prepared.limits.value_bytes)
        transferred += len(raw.encode())
        if transferred > prepared.limits.total_bytes:
            raise ContractError("aggregate data budget exceeded")
        return freeze(json.loads(raw)), hashlib.sha256(raw.encode()).hexdigest()

    def invoke(identity, incoming):
        nonlocal calls
        calls += 1
        if calls > prepared.limits.calls:
            raise ContractError("invocation budget exceeded")
        node = prepared.nodes[identity]
        context = Context(node, invoke, upstream)
        input_hash = "invalid"
        try:
            incoming, input_hash = check(incoming)
            node.definition.input.validate(incoming)
            result = node.definition.run(context, incoming)
            if (
                not isinstance(result, Output)
                or result.status not in STATUSES
                or not isinstance(result.detail, str)
            ):
                raise ContractError("module returned an invalid observation")
            data, output_hash = check(result.value)
            if data is not None or result.status not in ("unknown", "error"):
                node.definition.output.validate(data)
            # A composite cannot erase a failed, stale or incomplete child observation.
            statuses = [
                upstream,
                result.status,
                *(t.status for t in context._children if t.status != "empty"),
            ]
            status = max(statuses, key=_SEVERITY.get)
            result = Output(data, status, result.detail[:2000])
        except Exception as exc:
            result, output_hash = (
                Output(None, "error", f"{type(exc).__name__}: {exc}"[:2000]),
                fingerprint(None),
            )
        trace = Invocation(
            identity,
            node.definition.ref,
            node.definition.pin,
            input_hash,
            output_hash,
            result.status,
            result.detail,
            tuple(context._children),
        )
        return result, trace

    result, trace = invoke(prepared.root, value)
    status = max((result.status, upstream), key=_SEVERITY.get)
    return Evaluation(
        Output(result.value, status, result.detail), prepared.identity, evidence, trace
    )


@dataclass(frozen=True)
class Interpretation:
    session: str
    generation: int
    plan: str


class Installation:
    """In-memory stateless activation. Rollback restores a plan, never effects."""

    def __init__(self):
        self._session, self._generation = uuid.uuid4().hex, 0
        self.current = self.previous = None

    @property
    def interpretation(self) -> Interpretation | None:
        if self.current is None:
            return None
        return Interpretation(self._session, self._generation, self.current.identity)

    def activate(self, prepared: Prepared, *, expected: Interpretation | None) -> Interpretation:
        if self.interpretation != expected:
            raise ContractError("active interpretation changed")
        if not isinstance(prepared, Prepared):
            raise ContractError("activate a prepared stateless plan")
        self.previous, self.current = self.current, prepared
        self._generation += 1
        return self.interpretation

    def rollback(self, *, expected: Interpretation) -> Interpretation:
        if self.previous is None:
            raise ContractError("no previous stateless plan")
        return self.activate(self.previous, expected=expected)


@dataclass(frozen=True)
class Operation:
    name: str
    input: Port
    capability: str


@dataclass(frozen=True)
class AdmittedRequest:
    operation: str
    parameters: Any
    interpretation: Interpretation
    observations: tuple[Evidence, ...]
    status: str = "admitted-not-executed"


class Offers:
    """Host-owned one-use offers. Admission is NOT commit, delivery or execution.

    A future executor must recheck its native fence atomically at commit, then own
    durable outcome/uncertainty/recovery. No executor is supplied by this module.
    """

    def __init__(self, operations):
        operations = tuple(operations)
        self._operations = {op.name: op for op in operations}
        if len(self._operations) != len(operations):
            raise ContractError("duplicate operation")
        self._offers = {}

    def offer(self, operation, parameters, *, installed, observations, grants):
        if len(self._offers) >= 128:
            raise ContractError("pending offer budget exceeded; revoke unused offers")
        op = self._operations.get(operation)
        if op is None or op.capability not in grants or installed.interpretation is None:
            raise ContractError("operation is not offered under this authority")
        if op.capability not in installed.current.nodes[installed.current.root].grants:
            raise ContractError("operation exceeds the installed module ceiling")
        op.input.validate(parameters)
        evidence = tuple(observations)
        if any(e.status != "ready" for e in evidence):
            raise ContractError("actions require fresh, known observations")
        token = uuid.uuid4().hex
        self._offers[token] = (
            op,
            freeze(json.loads(canonical(parameters))),
            installed.interpretation,
            evidence,
        )
        return token

    def admit(self, token, *, installed, observations, grants) -> AdmittedRequest:
        offer = self._offers.pop(token, None)
        if offer is None:
            raise ContractError("unknown, revoked or consumed offer")
        op, params, interpretation, evidence = offer
        if installed.interpretation != interpretation:
            raise ContractError("stale interpretation")
        if tuple(observations) != evidence or any(e.status != "ready" for e in observations):
            raise ContractError("observations changed or are not ready")
        if op.capability not in grants:
            raise ContractError("operation authority revoked")
        return AdmittedRequest(op.name, params, interpretation, evidence)

    def revoke(self, token):
        self._offers.pop(token, None)
