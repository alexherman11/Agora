"""In-memory contract and actual scene tests; no live world, process or model."""

import copy
import hashlib
import json
import re
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import explore
import scene
from capability_modules import (
    ContractError,
    Definition,
    Evidence,
    Installation,
    Limits,
    Offers,
    Operation,
    Output,
    Port,
    Registry,
    Slot,
    evaluate,
    plain,
)
from module_examples import (
    BOTH,
    COMPUTE,
    coverage_document,
    definitions,
    registry,
)

ARTIFACT = "a" * 64
SCALAR = Port.of("scalar.v1", {"type": "integer"})
SAMPLE = dict(intervals=[dict(start=0, end=5), dict(start=3, end=8)], unit="hours")


def leaf(run=lambda ctx, v: Output(v), **kw):
    return Definition("leaf", "1", ARTIFACT, SCALAR, SCALAR, run, **kw)


def single(reg, name="leaf@1", grants=()):
    return reg.prepare(dict(root="root", nodes={"root": reg.binding(name, grants=grants)}))


def q(value):
    return (
        '"'
        + str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("$", "\\$")
        .replace("\n", "\\n")
        + '"'
    )


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.reg = registry()
        self.doc = coverage_document(self.reg)

    def test_distinct_capabilities_and_nested_slots_without_host_edits(self):
        lab = Path(__file__).parent
        hosts = [
            lab / name
            for name in (
                "capability_modules.py",
                "scene.py",
                "lens_ir.py",
                "desk-shell/lens.js",
                "desk-shell/lens.html",
            )
        ]
        before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in hosts]
        result = evaluate(self.reg.prepare(self.doc), SAMPLE)
        self.assertEqual(result.result.status, "ready")
        self.assertIn("Covered: 8 hours", result.result.value[0]["summary"])
        self.assertEqual(result.result.value[0]["detail"].count("Framed composition."), 2)
        view = result.trace.children[0].children[0]
        self.assertEqual(
            [c.module for c in view.children], ["intervals.union@1", "graphics.draw@1"]
        )
        # Supply a new definition after the host is frozen, with another schema
        # and behavior. Existing composition code accepts it without source edits.
        doubled = leaf(lambda ctx, v: Output(v * 2))
        fresh_registry = Registry((*definitions(), doubled), grants=BOTH)
        self.assertEqual(evaluate(single(fresh_registry), 7).result.value, 14)
        self.assertEqual(before, [hashlib.sha256(path.read_bytes()).hexdigest() for path in hosts])

    def test_same_count_changes_change_value_and_input_revision(self):
        plan = self.reg.prepare(self.doc)
        first = evaluate(plan, SAMPLE)
        changed = copy.deepcopy(SAMPLE)
        changed["intervals"][1]["end"] = 12
        second = evaluate(plan, changed)
        self.assertIn("Covered: 12 hours", second.result.value[0]["summary"])
        self.assertNotEqual(first.trace.input_revision, second.trace.input_revision)

    def test_empty_input_is_known_but_missing_producer_is_unknown(self):
        plan = self.reg.prepare(self.doc)
        self.assertEqual(evaluate(plan, dict(intervals=[])).result.status, "empty")
        result = evaluate(
            plan, SAMPLE, [Evidence("clock", "none", "unknown", "producer unavailable")]
        )
        self.assertEqual(result.result.status, "unknown")
        self.assertIsNone(result.trace)
        self.assertIsNone(result.result.value)

    def test_stale_input_remains_stale_with_retained_values(self):
        result = evaluate(
            self.reg.prepare(self.doc), SAMPLE, [Evidence("calendar", "old", "stale")]
        )
        self.assertEqual(result.result.status, "stale")
        self.assertIsNotNone(result.result.value)
        self.assertIn("stale", result.result.value[0]["picture"])
        self.assertNotIn("ready", result.result.value[0]["picture"])
        self.assertEqual(result.trace.children[0].status, "stale")

    def test_invalid_input_output_and_nonfinite_values_are_visible_errors(self):
        for value in (True, 2.5, float("nan"), {"wrong": "shape"}):
            reg = Registry([leaf()])
            self.assertEqual(evaluate(single(reg), value).result.status, "error")
        for fn in (
            lambda c, v: Output("wrong"),
            lambda c, v: {},
            lambda c, v: Output(1, "success"),
        ):
            reg = Registry([leaf(fn)])
            self.assertEqual(evaluate(single(reg), 1).result.status, "error")

    def test_input_is_immutable_and_outputs_detached(self):
        object_port = Port.of("object.v1", {"type": "object"})
        original = {"nested": [1]}

        def mutation(c, v):
            v["nested"][0] = 7
            return Output(v)

        reg = Registry([Definition("leaf", "1", ARTIFACT, object_port, object_port, mutation)])
        self.assertEqual(evaluate(single(reg), original).result.status, "error")
        self.assertEqual(original, {"nested": [1]})
        shared = {"nested": [1]}
        reg = Registry(
            [
                Definition(
                    "leaf", "1", ARTIFACT, object_port, object_port, lambda c, v: Output(shared)
                )
            ]
        )
        result = evaluate(single(reg), {})
        shared["nested"][0] = 9
        self.assertEqual(plain(result.result.value), {"nested": [1]})

    def test_cycle_and_depth_are_rejected_but_repeated_definition_is_allowed(self):
        doc = copy.deepcopy(self.doc)
        doc["nodes"]["frame0"]["children"]["body"] = "frame1"
        with self.assertRaisesRegex(ContractError, "cycle"):
            self.reg.prepare(doc)
        reg = Registry(definitions(), grants=BOTH, limits=Limits(depth=3))
        with self.assertRaisesRegex(ContractError, "depth"):
            reg.prepare(self.doc)

    def test_pins_slot_types_unreachable_nodes_and_code_in_world_are_rejected(self):
        bad = copy.deepcopy(self.doc)
        bad["nodes"]["measure"]["pin"] = "obsolete"
        with self.assertRaisesRegex(ContractError, "changed module"):
            self.reg.prepare(bad)
        bad = copy.deepcopy(self.doc)
        bad["nodes"]["view"]["children"]["measure"] = "graphic"
        with self.assertRaisesRegex(ContractError, "typed slot"):
            self.reg.prepare(bad)
        bad = copy.deepcopy(self.doc)
        bad["nodes"]["unused"] = self.reg.binding("intervals.union@1", grants=COMPUTE)
        with self.assertRaisesRegex(ContractError, "unreachable"):
            self.reg.prepare(bad)
        for key in ("state", "migration", "import", "exec"):
            with self.assertRaisesRegex(ContractError, "unsupported"):
                self.reg.prepare({**self.doc, key: "anything"})

    def test_host_parent_and_slot_capability_ceilings(self):
        for mutate in (
            lambda d: d["nodes"]["measure"]["grants"].append("network"),
            lambda d: d["nodes"]["frame1"].update(grants=[]),
            lambda d: d["nodes"]["measure"]["grants"].append("render.graphics"),
        ):
            doc = copy.deepcopy(self.doc)
            mutate(doc)
            with self.assertRaisesRegex(ContractError, "ceiling"):
                self.reg.prepare(doc)

    def test_all_child_calls_share_budget(self):
        def repeat(ctx, value):
            for _ in range(10):
                ctx.child("child", value)
            return Output(value)

        parent = Definition(
            "parent", "1", ARTIFACT, SCALAR, SCALAR, repeat, slots={"child": Slot(SCALAR, SCALAR)}
        )
        reg = Registry([parent, leaf()], limits=Limits(calls=3))
        plan = reg.prepare(
            dict(
                root="p",
                nodes={
                    "p": reg.binding("parent@1", children={"child": "c"}),
                    "c": reg.binding("leaf@1"),
                },
            )
        )
        result = evaluate(plan, 1)
        self.assertEqual(result.result.status, "error")
        self.assertIn("budget", result.result.detail)

    def test_data_budgets(self):
        any_port = Port.of("text.v1", {"type": "string"})
        d = Definition("leaf", "1", ARTIFACT, any_port, any_port, lambda c, v: Output(v * 200))
        reg = Registry([d], limits=Limits(value_bytes=1000))
        self.assertIn("bytes", evaluate(single(reg), "longlong").result.detail)
        reg = Registry([leaf()], limits=Limits(total_bytes=1))
        self.assertIn("aggregate", evaluate(single(reg), 12).result.detail)

    def test_unknown_children_cannot_be_relabelled_ready(self):
        parent = Definition(
            "parent",
            "1",
            ARTIFACT,
            SCALAR,
            SCALAR,
            lambda c, v: (c.child("child", v), Output(5))[1],
            slots={"child": Slot(SCALAR, SCALAR)},
        )
        reg = Registry([parent, leaf(lambda c, v: Output(None, "unknown", "missing"))])
        plan = reg.prepare(
            dict(
                root="p",
                nodes={
                    "p": reg.binding("parent@1", children={"child": "c"}),
                    "c": reg.binding("leaf@1"),
                },
            )
        )
        result = evaluate(plan, 1)
        self.assertEqual(result.result.status, "unknown")
        self.assertEqual(result.trace.children[0].detail, "missing")

    def test_no_remote_schema_references_or_duplicate_versions(self):
        with self.assertRaisesRegex(ContractError, "references"):
            Port.of("unsafe", {"$ref": "https://example.invalid/schema"})
        with self.assertRaisesRegex(ContractError, "duplicate"):
            Registry([leaf(), leaf()])
        changed = replace(leaf(), artifact="b" * 64)
        self.assertNotEqual(changed.pin, leaf().pin)

    def test_malformed_plans_node_limits_and_invalid_intervals(self):
        for document in ([], None, {"root": "x", "nodes": []}, {"root": "x", "nodes": {}}):
            with self.assertRaises(ContractError):
                self.reg.prepare(document)
        small = Registry(definitions(), grants=BOTH, limits=Limits(nodes=2))
        with self.assertRaisesRegex(ContractError, "node budget"):
            small.prepare(self.doc)
        result = evaluate(self.reg.prepare(self.doc), dict(intervals=[dict(start=8, end=3)]))
        self.assertEqual(result.result.status, "error")
        self.assertIn("precedes", result.result.detail)

    def test_schema_changes_change_pins_and_limits_change_interpretation(self):
        changed_port = Port.of("scalar.v1", {"type": "integer", "maximum": 5})
        self.assertNotEqual(leaf().pin, replace(leaf(), input=changed_port).pin)
        one = Registry([leaf()], limits=Limits(calls=5))
        two = Registry([leaf()], limits=Limits(calls=6))
        self.assertNotEqual(single(one).identity, single(two).identity)

    def test_repeated_shared_dependencies_cannot_explode_admission(self):
        fork = Definition(
            "fork",
            "1",
            ARTIFACT,
            SCALAR,
            SCALAR,
            lambda c, v: Output(v),
            slots={"left": Slot(SCALAR, SCALAR), "right": Slot(SCALAR, SCALAR)},
        )
        reg = Registry([fork, leaf()], limits=Limits(calls=8))
        nodes = {"end": reg.binding("leaf@1")}
        child = "end"
        for n in range(4):
            name = f"fork{n}"
            nodes[name] = reg.binding("fork@1", children={"left": child, "right": child})
            child = name
        with self.assertRaisesRegex(ContractError, "expansion budget"):
            reg.prepare(dict(root=child, nodes=nodes))


class OfferTests(unittest.TestCase):
    def setUp(self):
        self.reg = Registry([leaf()], grants={"note.edit"})
        self.plan = single(self.reg, grants={"note.edit"})
        self.install = Installation()
        self.install.activate(self.plan, expected=None)
        self.book = Offers([Operation("note.replace-number", SCALAR, "note.edit")])
        self.evidence = (Evidence("target", "revision-1"),)

    def offer(self, **kw):
        return self.book.offer(
            "note.replace-number",
            4,
            installed=self.install,
            observations=kw.get("observations", self.evidence),
            grants=kw.get("grants", {"note.edit"}),
        )

    def admit(self, token, **kw):
        return self.book.admit(
            token,
            installed=self.install,
            observations=kw.get("observations", self.evidence),
            grants=kw.get("grants", {"note.edit"}),
        )

    def test_admission_is_one_use_and_never_claims_execution(self):
        token = self.offer()
        result = self.admit(token)
        self.assertEqual(result.status, "admitted-not-executed")
        with self.assertRaisesRegex(ContractError, "consumed"):
            self.admit(token)

    def test_changed_observation_stale_status_and_revoked_authority(self):
        for changes in (
            dict(observations=(Evidence("target", "revision-2"),)),
            dict(observations=(Evidence("target", "revision-1", "stale"),)),
            dict(grants=set()),
        ):
            with self.assertRaises(ContractError):
                self.admit(self.offer(), **changes)
        with self.assertRaisesRegex(ContractError, "fresh"):
            self.offer(observations=(Evidence("target", "old", "unknown"),))

    def test_rollback_does_not_revive_old_offers_or_old_interpretations(self):
        token = self.offer()
        old = self.install.interpretation
        self.install.activate(self.plan, expected=old)
        self.install.rollback(expected=self.install.interpretation)
        self.assertEqual(self.install.current.identity, old.plan)
        self.assertNotEqual(self.install.interpretation, old)
        with self.assertRaisesRegex(ContractError, "stale interpretation"):
            self.admit(token)
        with self.assertRaisesRegex(ContractError, "changed"):
            self.install.activate(self.plan, expected=old)

    def test_module_ceiling_and_unoffered_operations(self):
        self.install.activate(single(self.reg), expected=self.install.interpretation)
        with self.assertRaisesRegex(ContractError, "ceiling"):
            self.offer()
        with self.assertRaisesRegex(ContractError, "not offered"):
            self.book.offer(
                "exec", 4, installed=self.install, observations=(), grants={"note.edit"}
            )

    def test_pending_offers_are_bounded_and_revoke_releases_capacity(self):
        tokens = [self.offer() for _ in range(128)]
        with self.assertRaisesRegex(ContractError, "budget"):
            self.offer()
        self.book.revoke(tokens[0])
        self.offer()
        with self.assertRaisesRegex(ContractError, "revoked"):
            self.admit(tokens[0])


class SceneTests(unittest.TestCase):
    def setUp(self):
        self.desk = explore.fresh()
        self.desk._session = "modules-in-memory"
        self.reg = registry()
        self.config = dict(plan=coverage_document(self.reg), input=copy.deepcopy(SAMPLE))

    def line(self, text):
        result = self.desk.dispatch("desk", dict(line=text, whole=True))
        self.assertFalse(result.get("error"), result)
        self.assertFalse(result.get("text", "").startswith("ERR"), result)
        return result.get("text", "")

    def note(self, title, text, tag=None):
        self.line("look " + self.desk.world.root)
        receipt = self.line(
            f"do create {self.desk.world.root} kind=note title={q(title)} text={q(text)}"
        )
        item = re.search(r"created (a\d+)", receipt)[1]
        if tag:
            self.line(f"do tag {item} add={tag}")
        return item

    def lens(self, item):
        self.note(
            "module-proof",
            f"root : column\n  results : column\n    of modules:{item} as m\n    each row\n"
            'row : column\n  word : text "$m.summary"\n  note : text "$m.detail"\n'
            '  image : text "$m.picture", picture',
            "lens",
        )

    def test_actual_compiler_uses_nested_modules_and_updates_same_count(self):
        state = [dict(start=0, end=2), dict(start=1, end=3)]
        self.config.update(source="modulecheck", into="intervals")
        with (
            patch.dict(scene.SOURCES, modulecheck=("modulecheck", ("start", "end"))),
            patch.dict(
                scene.SOURCE_FILES,
                modulecheck=dict(arg="none", open=False, rows=lambda *args: list(state)),
            ),
        ):
            item = self.note("Coverage", json.dumps(self.config))
            self.lens(item)
            first = scene.scene_for(self.desk, "module-proof")[1]
            self.assertIn("Covered: 3 hours", first)
            self.assertIn("<svg", first)
            state[1]["end"] = 9
            second = scene.scene_for(self.desk, "module-proof")[1]
            self.assertIn("Covered: 9 hours", second)
            state.clear()
            third = scene.scene_for(self.desk, "module-proof")[1]
            self.assertIn("Module unknown", third)
            self.assertNotIn("Covered: 0", third)

    def test_config_edits_and_stale_labels_reach_compiled_scene(self):
        item = self.note("Coverage", json.dumps(self.config))
        self.lens(item)
        for end in range(9, 14):
            self.config["input"]["intervals"][1]["end"] = end
            self.line("read " + item)
            self.line(f"do edit {item} text={q(json.dumps(self.config))}")
            self.assertIn(f"Covered: {end} hours", scene.scene_for(self.desk, "module-proof")[1])
        self.config["state"] = "stale"
        self.line("read " + item)
        self.line(f"do edit {item} text={q(json.dumps(self.config))}")
        self.assertIn("Stale: Covered", scene.scene_for(self.desk, "module-proof")[1])

    def test_bad_pin_missing_source_and_malformed_note_are_visible(self):
        self.config["source"] = "producer-not-installed"
        self.config["into"] = "intervals"
        item = self.note("Missing", json.dumps(self.config))
        self.assertEqual(scene.rows(self.desk, "modules:" + item)[0]["status"], "unknown")
        self.config["plan"]["nodes"]["measure"]["pin"] = "stale"
        item = self.note("Stale pin", json.dumps(self.config))
        self.assertEqual(scene.rows(self.desk, "modules:" + item)[0]["status"], "error")

    def test_discovery_and_linked_trace_are_world_readable(self):
        catalog = scene.rows(self.desk, "modules")
        self.assertEqual(len(catalog), 4)
        self.assertTrue(all(row["revision"] for row in catalog))
        self.assertIn("input_schema", json.loads(catalog[0]["detail"]))
        item = self.note("Coverage", json.dumps(self.config))
        trace = scene.rows(self.desk, "modules:" + item + "/trace")
        self.assertEqual(len(trace), 6)  # two frames, view, two leaves, input observation
        self.assertTrue(any(row["title"] == "intervals.union@1" for row in trace))
        self.assertTrue(any(row["title"] == "graphics.draw@1" for row in trace))
        item = self.note("Malformed", "[]")
        self.assertEqual(scene.rows(self.desk, "modules:" + item)[0]["status"], "error")


if __name__ == "__main__":
    unittest.main()
