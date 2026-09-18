"""Final integration regressions for retained transitive definitions."""
import unittest

from activation import DefinitionLifecycle
from compiler_bridge import CompilerBridge
from explore import fresh
from test_bridge_contract import command, create, offered


class ClosureIntegrationChecks(unittest.TestCase):
    def test_invalid_inner_draft_preserves_active_projection_and_fresh_material(self):
        desk = fresh()
        material, _ = create(desk, "Material", "before", "material")
        inner, _ = create(desk, "Inner", "body : column, of tag:material, each row\nrow : text $text, on edit do rewrite $id text=\"$value\"", "lens")
        outer, _ = create(desk, "Outer", "root : column\n  inside : lens Inner\n  authors : column, of tag:lens, each author\nauthor : text $text, on edit do rewrite $id text=\"$value\"", "lens")
        bridge = CompilerBridge(desk, outer)
        frame = bridge.offer("alex")
        bridge.invoke("alex", offered(bridge, frame, inner), {"value": "invalid inner draft"})
        frame = bridge.offer("alex")
        bridge.invoke("alex", offered(bridge, frame, material), {"value": "fresh material"})
        current = bridge.offer("alex")
        self.assertIn("fresh material", current["text"])
        self.assertEqual(bridge.snapshot()["subjects"][inner]["text"], "invalid inner draft")
        self.assertEqual(bridge.lifecycle_state()["activation_revision"], 1)

    def test_dynamic_new_definition_requires_deliberate_activation(self):
        desk = fresh()
        create(desk, "InnerA", "body : text A", "lens")
        create(desk, "InnerB", "body : text B", "lens")
        selector, _ = create(desk, "InnerA", "", "selector")
        outer, _ = create(desk, "Outer", "root : column, of tag:selector, each slot\nslot : lens $title", "lens")
        life = DefinitionLifecycle(desk, outer)
        candidate = life.propose(desk.world.subjects[outer]["text"], 0)
        self.assertTrue(candidate["ok"], candidate)
        self.assertTrue(life.activate(candidate["candidate_id"], 0)["ok"])
        desk.dispatch("read", {"target": selector})
        command(desk, "retitle", selector, title="InnerB")
        with self.assertRaisesRegex(ValueError, "unpinned definition"):
            life.compile_active()
        self.assertEqual(life.activation_revision, 1)


if __name__ == "__main__":
    unittest.main()
