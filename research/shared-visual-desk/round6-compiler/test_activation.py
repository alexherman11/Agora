"""Disposable actual-compiler checks; no persistent Desk or source writes."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json
import sys
import unittest

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1] / "text-desk-lab" / "notation"
sys.path.insert(0, str(ENGINE))
from explore import fresh
from activation import DefinitionLifecycle
from frame_contract import compile_frame, check_frame

A = "reading : column, role sheet\n  stories : column, of tag:essay, each article\narticle : text $text, role body"
B = "index : column, role window\n  entries : column, of tag:essay, each entry\nentry : text $title, role title, on click do read $item"
BAD = "reading : impossible raw-css"
HOSTS = [ENGINE / p for p in ("scene.py", "desk-shell/lens.js", "desk-shell/lens.html", "desk-shell/style/style.js", "desk-shell/style/calm.style")]

def hashes():
    return {str(p.relative_to(ENGINE)): sha256(p.read_bytes()).hexdigest() for p in HOSTS}

def cmd(desk, line):
    result = desk.dispatch("desk", {"line": line})
    if result.get("error") or result.get("text", "").startswith("ERR"):
        raise AssertionError((line, result))
    return result

def create(desk, title, text, tags):
    before = set(desk.world.subjects)
    cmd(desk, "look f01")
    cmd(desk, f"do create f01 kind=note title={json.dumps(title)} tags={tags} text={json.dumps(text)}")
    sid = (set(desk.world.subjects) - before).pop()
    aid = next(n["id"] for n in desk.world.nodes.values() if n.get("subject") == sid)
    return sid, aid

class ActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host_before = hashes()

    @classmethod
    def tearDownClass(cls):
        if hashes() != cls.host_before:
            raise AssertionError("independent host source changed during bounded activation tests")
        print("Host source SHA256 unchanged:", json.dumps(cls.host_before, sort_keys=True))

    def setUp(self):
        self.desk = fresh()
        self.desk.world.me = "editing"
        self.material, self.appearance = create(self.desk, "First essay", '  She said "yes".\n', "essay")
        self.definition, self.definition_appearance = create(self.desk, "Reading", A, "lens")
        self.lifecycle = DefinitionLifecycle(self.desk, self.definition)
        self.local = {"draft": '  print("hi")\n$&  ', "selection": {"anchor": 3, "focus": 7}, "composition": "ongoing"}
        self.lifecycle.set_view_state("editor/alex", self.local)

    def activate(self, source):
        result = self.lifecycle.propose(source, self.lifecycle.activation_revision)
        self.assertTrue(result["ok"], result)
        activated = self.lifecycle.activate(result["candidate_id"], self.lifecycle.activation_revision)
        self.assertTrue(activated["ok"], activated)
        return activated

    def test_invalid_first_candidate_keeps_empty_active_and_exact_local_work(self):
        before = self.lifecycle.snapshot()
        result = self.lifecycle.propose(BAD, 0)
        self.assertFalse(result["ok"])
        self.assertEqual(before, self.lifecycle.snapshot())

    def test_refused_candidate_preserves_last_good_and_local_state(self):
        self.activate(A)
        before = self.lifecycle.snapshot()
        for source in (BAD, "reading : role missing-component-role", "reading : column, each reading"):
            self.assertFalse(self.lifecycle.propose(source, 1)["ok"])
            self.assertEqual(before, self.lifecycle.snapshot())

    def test_success_changes_only_activation_not_world_or_local_work(self):
        world = deepcopy(self.desk.world.__dict__)
        self.activate(A)
        self.activate(B)
        self.assertEqual(world, self.desk.world.__dict__)
        self.assertEqual(self.local, self.lifecycle.view_states["editor/alex"])
        self.assertEqual(B, self.lifecycle.active_source)
        self.assertEqual(2, self.lifecycle.activation_revision)

    def test_candidate_and_view_return_values_cannot_mutate_retained_records(self):
        candidate = self.lifecycle.propose(A, 0)
        candidate["frame"]["scene"]["text"] = "FORGED PREVIEW"
        views = self.lifecycle.view_states
        views["editor/alex"]["draft"] = "LOST"
        self.assertTrue(self.lifecycle.activate(candidate["candidate_id"], 0)["ok"])
        self.assertNotEqual("FORGED PREVIEW", self.lifecycle.active_frame["scene"]["text"])
        self.assertEqual(self.local, self.lifecycle.view_states["editor/alex"])
        frame = self.lifecycle.active_frame
        frame["scene"]["text"] = "FORGED ACTIVE"
        self.assertNotEqual("FORGED ACTIVE", self.lifecycle.active_frame["scene"]["text"])

    def test_world_change_invalidates_candidate_but_not_active_or_draft(self):
        self.activate(A)
        candidate = self.lifecycle.propose(B, 1)
        before = self.lifecycle.snapshot()
        cmd(self.desk, "read " + self.appearance)
        cmd(self.desk, f"do rewrite {self.appearance} text=Changed")
        result = self.lifecycle.activate(candidate["candidate_id"], 1)
        self.assertFalse(result["ok"])
        self.assertEqual(before, self.lifecycle.snapshot())
        self.assertEqual("Changed", self.desk.world.subjects[self.material]["text"])

    def test_definition_anchor_change_invalidates_candidate(self):
        self.activate(A)
        candidate = self.lifecycle.propose(B, 1)
        cmd(self.desk, "read " + self.definition_appearance)
        cmd(self.desk, f"do rewrite {self.definition_appearance} text={json.dumps(B)}")
        self.assertFalse(self.lifecycle.activate(candidate["candidate_id"], 1)["ok"])
        self.assertEqual(A, self.lifecycle.active_source)

    def test_restore_recompiles_current_world_and_advances_aba_generation(self):
        self.activate(A)
        old_candidate = self.lifecycle.propose(B, 1)
        self.activate(B)
        cmd(self.desk, "read " + self.appearance)
        cmd(self.desk, f"do rewrite {self.appearance} text=Fresh")
        world = deepcopy(self.desk.world.__dict__)
        result = self.lifecycle.restore(1, 2)
        self.assertTrue(result["ok"], result)
        self.assertEqual(3, self.lifecycle.activation_revision)
        self.assertEqual(A, self.lifecycle.active_source)
        self.assertEqual(world, self.desk.world.__dict__)
        self.assertIn("Fresh", json.dumps(self.lifecycle.active_frame["scene"]))
        self.assertFalse(self.lifecycle.activate(old_candidate["candidate_id"], 3)["ok"])
        self.assertFalse(self.lifecycle.activate(old_candidate["candidate_id"], 1)["ok"])
        self.assertEqual(self.local, self.lifecycle.view_states["editor/alex"])

    def test_restore_validation_failure_retains_active_without_replaying_effects(self):
        self.activate(A)
        self.activate(B)
        before = self.lifecycle.snapshot()
        actual_compiler = self.lifecycle._compiler
        def missing_capability(*args, **kwargs):
            raise ValueError("controlled unavailable installed capability")
        self.lifecycle._compiler = missing_capability
        self.assertFalse(self.lifecycle.restore(1, 2)["ok"])
        self.assertEqual(before, self.lifecycle.snapshot())
        self.lifecycle._compiler = actual_compiler

    def test_checker_dependency_change_refuses_without_mutation(self):
        self.activate(A)
        candidate = self.lifecycle.propose(B, 1)
        before = self.lifecycle.snapshot()
        self.lifecycle._checker = lambda desk, frame: {"ok": False, "reasons": ["controlled compiler/style dependency changed"]}
        self.assertFalse(self.lifecycle.activate(candidate["candidate_id"], 1)["ok"])
        self.assertEqual(before, self.lifecycle.snapshot())

    def test_rebind_uses_current_owner_without_overwriting_it(self):
        candidate = self.lifecycle.propose(A, 0)
        replacement = deepcopy(self.desk)
        cmd(replacement, "read " + self.appearance)
        cmd(replacement, f"do rewrite {self.appearance} text=Rebound")
        self.lifecycle.set_desk(replacement)
        self.assertFalse(self.lifecycle.activate(candidate["candidate_id"], 0)["ok"])
        self.assertEqual("Rebound", replacement.world.subjects[self.material]["text"])

    def test_active_closure_survives_invalid_nested_source_with_fresh_material(self):
        inner, inner_aid = create(self.desk, "inner", A, "lens")
        outer = "outer : column\n  slot : lens inner"
        self.activate(outer)
        original = self.lifecycle.active_definition_records
        cmd(self.desk, "read " + inner_aid)
        cmd(self.desk, f"do rewrite {inner_aid} text={json.dumps(BAD)}")
        cmd(self.desk, "read " + self.appearance)
        cmd(self.desk, f"do rewrite {self.appearance} text=FreshMaterial")
        world = deepcopy(self.desk.world.__dict__)
        active = self.lifecycle.compile_active(actor="editing")
        self.assertIn("FreshMaterial", json.dumps(active["scene"]))
        self.assertEqual(world, self.desk.world.__dict__)
        self.assertEqual(self.local, self.lifecycle.view_states["editor/alex"])
        self.assertEqual(original, self.lifecycle.active_definition_records)
        self.assertFalse(self.lifecycle.propose(outer, 1)["ok"])
        # Failure to activate current broken authoring does not poison display.
        self.assertIn("FreshMaterial", json.dumps(self.lifecycle.compile_active()["scene"]))

    def test_nested_valid_change_requires_deliberate_activation_to_adopt(self):
        inner, inner_aid = create(self.desk, "inner", "inner : text First edition, on click do read f01", "lens")
        outer = "outer : column\n  slot : lens inner"
        self.activate(outer)
        cmd(self.desk, "read " + inner_aid)
        cmd(self.desk, f"do rewrite {inner_aid} text={json.dumps('inner : text Second edition, on click do look f01')}")
        self.assertIn("First edition", json.dumps(self.lifecycle.compile_active()["scene"]))
        self.assertNotIn("Second edition", json.dumps(self.lifecycle.compile_active()["scene"]))
        self.assertIn("read f01", json.dumps(self.lifecycle.compile_active()["scene"]))
        self.assertNotIn("look f01", json.dumps(self.lifecycle.compile_active()["scene"]))
        self.activate(outer)
        self.assertIn("Second edition", json.dumps(self.lifecycle.compile_active()["scene"]))
        self.assertIn("look f01", json.dumps(self.lifecycle.compile_active()["scene"]))
        self.assertEqual(2, self.lifecycle.activation_revision)

    def test_closure_record_copies_cannot_change_retained_source_or_properties(self):
        self.activate(A)
        records = self.lifecycle.active_definition_records
        records[self.definition]["text"] = BAD
        records[self.definition]["props"]["poison"] = True
        frame = self.lifecycle.compile_active()
        self.assertEqual("reading", frame["scene"]["part"])
        self.assertNotIn("poison", self.lifecycle.active_definition_records[self.definition]["props"])

    def test_revision_and_candidate_admission_and_one_time_activation(self):
        for invalid in (True, -1, 0.0, "0"):
            self.assertFalse(self.lifecycle.propose(A, invalid)["ok"])
        self.assertFalse(self.lifecycle.activate([], 0)["ok"])
        self.assertFalse(self.lifecycle.restore(99, 0)["ok"])
        candidate = self.lifecycle.propose(A, 0)
        self.assertTrue(self.lifecycle.activate(candidate["candidate_id"], 0)["ok"])
        self.assertFalse(self.lifecycle.activate(candidate["candidate_id"], 1)["ok"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
