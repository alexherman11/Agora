"""Executable design counterexamples for Agora; Python standard library only.

These are bounded models, not an OS, a CRDT implementation, a security proof,
or power-loss tests. Each experiment exhibits a tempting implementation's
failure and checks a proposed constraint under the same simplified scenario.
Run: python toy_models.py [--json PATH]
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory


CASES = []


def case(fn):
    CASES.append(fn)
    return fn


def require(condition, explanation):
    if not condition:
        raise AssertionError(explanation)


class FacetStore:
    """Atomic in-memory commits with optional validation of the complete read set."""

    def __init__(self, values):
        self.values = deepcopy(values)
        self.revisions = dict.fromkeys(values, 0)

    def commit(self, updates, expected):
        if any(self.revisions.get(k) != v for k, v in expected.items()):
            return False
        for key, value in updates.items():
            self.values[key] = deepcopy(value)
            self.revisions[key] = self.revisions.get(key, -1) + 1
        return True


@case
def rollback_resolution():
    snapshot = {"note": {"text": "try caching"}}
    world = deepcopy(snapshot)
    world["prototype"] = {"spec": "serve"}
    journal = {"prototype": {"branch": "A", "genesis": "event-2"}}
    memory_reference = "prototype"
    world = deepcopy(snapshot)
    naive = world.get(memory_reference)
    fixed = world.get(memory_reference) or {
        "resolution": "absent_on_branch",
        "origin": journal[memory_reference],
    }
    require(naive is None, "snapshot-only resolver should lose the object")
    require(fixed["origin"]["genesis"] == "event-2", "outside journal resolves history")
    return {"naive": "dangling reference", "constrained": fixed}


@case
def grant_resurrection():
    checkpoint_grants = {"worker": "write"}
    live_grants = deepcopy(checkpoint_grants)
    del live_grants["worker"]
    world_grants_after_restore = deepcopy(checkpoint_grants)
    broker_epoch = 8  # outside snapshot domain; was 7 when grant was issued
    old_grant = {"principal": "worker", "epoch": 7}
    naive_allowed = old_grant["principal"] in world_grants_after_restore
    fixed_allowed = naive_allowed and old_grant["epoch"] == broker_epoch
    require(naive_allowed and not fixed_allowed, "rollback must not undo revocation")
    return {"naive": "revoked worker regains write", "constrained": "old grant rejected"}


@case
def revision_aba_after_rollback():
    stale_worker = {"branch": "A", "epoch": 4, "revision": 3}
    # Restoring rev 2 then accepting a new edit produces rev 3 on another future.
    current = {"branch": "B", "epoch": 5, "revision": 3}
    require(stale_worker["revision"] == current["revision"], "numeric revision repeats")
    require(stale_worker != current, "branch and authority epoch prevent ABA acceptance")
    return {"naive": "revision 3 accepted on wrong future", "constrained": "stale context rejected"}


@case
def observed_status_fencing():
    current = {"epoch": 5, "generation": 10, "lease": 9}
    candidates = [
        {"epoch": 4, "generation": 10, "lease": 9},
        {"epoch": 5, "generation": 9, "lease": 9},
        {"epoch": 5, "generation": 10, "lease": 8},
        dict(current),
    ]
    naive = [True for _ in candidates]  # all writers have the reconciler role
    fixed = [candidate == current for candidate in candidates]
    require(sum(naive) == 4 and fixed == [False, False, False, True], "role alone lacks freshness")
    return {"naive_accepted": 4, "constrained_accepted": 1, "stale_rejected": 3}


class Receiver:
    def __init__(self, deduplicates):
        self.deduplicates = deduplicates
        self.receipts = {}
        self.effects = 0

    def send(self, operation_id, payload):
        if self.deduplicates and operation_id in self.receipts:
            previous_payload, receipt = self.receipts[operation_id]
            if previous_payload != payload:
                raise ValueError("operation ID reused with different arguments")
            return receipt
        self.effects += 1
        receipt = f"receipt-{self.effects}"
        self.receipts[operation_id] = (payload, receipt)
        return receipt


@case
def external_effects():
    totals = {}
    for cause in ("rollback_erases_local_receipt", "crash_before_receipt_recorded"):
        for deduplicates in (False, True):
            service = Receiver(deduplicates)
            local_receipts = {}
            service.send("publish-17", "artifact-v1")
            # Either failure leaves the caller without the successful receipt.
            if "publish-17" not in local_receipts:
                local_receipts["publish-17"] = service.send("publish-17", "artifact-v1")
            totals[f"{cause}/dedupe={deduplicates}"] = service.effects
            require(service.effects == (1 if deduplicates else 2), "receiver contract matters")
    # A broker's durable pending marker cannot distinguish success from no effect.
    observed = []
    for effect_happened in (False, True):
        broker = {"publish-18": "pending"}
        observed.append((broker, int(effect_happened)))
    require(observed[0][0] == observed[1][0], "same caller state, different external facts")
    return {"effect_counts": totals, "without_receiver_support": "outcome_unknown; inspect before retry"}


@case
def cross_facet_write_skew():
    violations = 0
    guarded_conflicts = 0
    for order in permutations(("a", "b")):
        naive = FacetStore({"a": 40, "b": 40})
        fixed = FacetStore({"a": 40, "b": 40})
        read_set = dict(fixed.revisions)
        # Both proposals read the initial state, and each independently sums to 100.
        for facet in order:
            require(60 + 40 <= 100, "proposal was valid against its read snapshot")
            require(naive.commit({facet: 60}, {facet: 0}), "disjoint writes both commit")
            guarded_conflicts += not fixed.commit({facet: 60}, read_set)
        violations += sum(naive.values.values()) > 100
        require(sum(fixed.values.values()) <= 100, "read-set validation preserves the bound")
    require(violations == 2 and guarded_conflicts == 2, "exercise both commit orders")
    return {"orders": 2, "naive_invalid_totals": 2, "constrained_conflicts": 2}


@case
def unknown_facet_preservation():
    store = FacetStore({
        "text": "approved wording",
        "unknown.signature.v2": {"signed_revision": 0, "opaque": "bytes-to-preserve"},
    })
    original = deepcopy(store.values["unknown.signature.v2"])
    store.commit({"text": "different wording"}, {"text": 0})
    require(store.values["unknown.signature.v2"] == original, "unknown data survives")
    naive_current = "unknown.signature.v2" in store.values
    fixed_current = original["signed_revision"] == store.revisions["text"]
    require(naive_current and not fixed_current, "preservation does not preserve validity")
    return {"unknown_bytes_preserved": True, "naive": "signature still shown as current", "constrained": "dependency stale"}


@case
def file_history():
    with TemporaryDirectory(prefix="agora-object-review-") as directory:
        file = Path(directory) / "note.txt"
        file.write_text("version one", encoding="utf-8")
        old_bytes = file.read_bytes()
        digest = sha256(old_bytes).hexdigest()
        blob_store = {digest: old_bytes}
        event = {"path": str(file), "revision_hash": digest}
        file.write_text("version two", encoding="utf-8")
        naive_replay = Path(event["path"]).read_bytes()
        fixed_replay = blob_store[event["revision_hash"]]
        require(naive_replay != old_bytes and fixed_replay == old_bytes, "paths cannot reconstruct old bytes")
    return {"naive_replay": naive_replay.decode(), "constrained_replay": fixed_replay.decode()}


@case
def derived_visibility():
    inputs = [
        {"text": "public project", "readers": {"alex", "room"}},
        {"text": "private budget 123", "readers": {"alex"}},
    ]
    naive_summary = "public project; private budget 123"
    derived_readers = set.intersection(*(item["readers"] for item in inputs))
    shared_summary = " ".join(item["text"] for item in inputs if "room" in item["readers"])
    require("123" in naive_summary, "post-hoc labeling would leak source content")
    require("room" not in derived_readers and "123" not in shared_summary, "filter inputs before projection")
    return {"naive": "summary leaks a private facet", "constrained": shared_summary}


def project(facts, summary, budget):
    # Whitespace units deliberately are NOT claimed to be LLM tokenizer tokens.
    envelope = f"id={facts['id']} revision={facts['revision']} state={facts['state']} trust={facts['trust']}"
    cost = len(envelope.split())
    if budget < cost:
        return {"omitted": True, "required_units": cost, "text": ""}
    tail = " ".join(summary.split()[: max(0, budget - cost)])
    return {"omitted": False, "required_units": cost, "text": envelope + (" " + tail if tail else "")}


@case
def projection_budget():
    facts = {"id": "p1", "revision": 7, "state": "conflicted", "trust": "untrusted"}
    summary = "healthy safe ready for release"
    checked = 0
    for budget in range(13):
        result = project(facts, summary, budget)
        require(len(result["text"].split()) <= budget, "bounded display")
        if not result["omitted"]:
            require("state=conflicted" in result["text"], "safety state cannot be truncated")
            require("trust=untrusted" in result["text"], "source trust cannot be truncated")
        checked += 1
    return {"budgets_checked": checked, "example": project(facts, summary, 6), "limitation": "does not test an LLM or prevent prompt injection"}


@case
def spec_write_is_effect_authority():
    grant = {"facets": {"spec"}, "effects": {"run-local"}, "epoch": 3}
    malicious_spec = {"effect": "publish-external", "path": "/allowed/project"}
    naive = "spec" in grant["facets"]
    authorized = naive and malicious_spec["effect"] in grant["effects"]
    require(naive and not authorized, "declarative writes must be checked for induced effects")
    discovery_epoch, execution_epoch = 3, 4
    require(discovery_epoch != execution_epoch, "discoverable action is not an enduring authorization")
    return {"naive": "reconciler launders a local grant into publish", "constrained": "broker rejects induced effect"}


def is_acyclic(edges):
    children = {}
    for source, target in edges:
        children.setdefault(source, []).append(target)

    def walk(node, active, complete):
        if node in active:
            return False
        if node in complete:
            return True
        active.add(node)
        for child in children.get(node, []):
            if not walk(child, active, complete):
                return False
        active.remove(node)
        complete.add(node)
        return True

    complete = set()
    return all(walk(node, set(), complete) for node in children)


@case
def semantic_merge_is_not_validity():
    a, b = {("job-a", "job-b")}, {("job-b", "job-a")}
    require(is_acyclic(a) and is_acyclic(b), "each replica has a valid DAG")
    merged = a | b
    require(merged == b | a, "set union converges in either order")
    require(not is_acyclic(merged), "convergence can create a dependency cycle")
    # A scheduler rejects execution until the graph is repaired, or uses a
    # serialized authority to prevent accepting the conflicting second edge.
    executable = is_acyclic(merged)
    require(not executable, "a merge conflict must stop execution")
    return {"naive": "converged dependency graph has cycle", "constrained": "conflicted graph cannot execute"}


@case
def lifecycle_and_multiple_views():
    object_state = {"id": "dataset", "salience": 0.001, "pinned": False, "leases": {"analysis-job"}}
    naive_tombstone = object_state["salience"] < 0.01
    can_tombstone = naive_tombstone and not object_state["pinned"] and not object_state["leases"]
    require(naive_tombstone and not can_tombstone, "invisible does not mean unused")
    placements = {("dataset", "private-view"): (10, 20), ("dataset", "room-view"): (90, 80)}
    placements[("dataset", "private-view")] = (30, 40)
    require(placements[("dataset", "room-view")] == (90, 80), "moving a view need not move every view")
    return {"naive": "low attention destroys a running dependency", "constrained": "lease retains data; layouts scoped per view"}


@case
def event_replay_must_not_execute():
    events = [{"type": "PublishRequested", "operation_id": "publish-1"}]
    external = Receiver(False)

    def bad_fold():
        state = {}
        for event in events:
            state[event["operation_id"]] = external.send(event["operation_id"], "artifact")
        return state

    bad_fold()
    bad_fold()
    require(external.effects == 2, "rebuilding a cache must not reissue external commands")

    def pure_fold():
        return {event["operation_id"]: "requested" for event in events}

    require(pure_fold() == pure_fold(), "pure replay is stable")
    require(external.effects == 2, "pure replay has no additional effects")
    return {"naive_effects_after_two_replays": 2, "constrained_additional_effects": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    results = []
    for experiment in CASES:
        try:
            detail = experiment()
            results.append({"case": experiment.__name__, "passed": True, "detail": detail})
        except Exception as exc:
            results.append({"case": experiment.__name__, "passed": False, "error": str(exc)})
    output = {
        "python": sys.version.split()[0],
        "scope": "bounded counterexamples; no production implementation or security/performance proof",
        "passed": sum(result["passed"] for result in results),
        "total": len(results),
        "experiments": results,
        "illustrative_scale": {
            "assumptions": "20,000 objects; 12 facets/object; 1,024 bytes/facet; excludes indexes/history",
            "facet_payload_MiB": 20000 * 12 * 1024 / 1024**2,
            "presence_assumptions": "60 samples/s; 8 h/day; 160 bytes/sample; excludes indexes/replication",
            "presence_MiB_per_day": 60 * 8 * 3600 * 160 / 1024**2,
            "projection_assumptions": "20,000 objects at 15 tokens per one-line description",
            "all_object_projection_tokens": 20000 * 15,
        },
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))
    return 0 if output["passed"] == output["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
