# health: room test
"""Pure expressions and actual in-memory world dispatch; no sessions, host, models or browser."""
import json
import re
import unittest
from unittest.mock import patch
import uuid

import expr
import reference_lists as refs
import roomworld
import lens_ir
import scene
import viewer_pin_stage as stage


class ReferenceLists(unittest.TestCase):
    def test_order_and_exact_identity(self):
        self.assertEqual(refs.edit("a1,a11 a2", "a3", "add"), "a1\na11\na2\na3")
        self.assertEqual(refs.edit("a1,a11 a2", "a1", "remove"), "a11\na2")
        self.assertEqual(refs.edit("a1,a11 a2", "a2", "before", "a1"), "a2\na1\na11")
        self.assertEqual(refs.edit("a1\na11\na2", "a1", "before"), "a11\na2\na1")

    def test_empty_and_noops_preserve_spelling(self):
        raw = "a1, a2\ns3"
        self.assertEqual(refs.edit("", "a1", "add"), "a1")
        self.assertEqual(refs.edit("a1", "a1", "remove"), "")
        self.assertEqual(refs.edit(raw, "a2", "add"), raw)
        self.assertEqual(refs.edit(raw, "a9", "remove"), raw)
        self.assertEqual(refs.edit(raw, "a1", "before", "a2"), raw)
        self.assertEqual(refs.edit(raw, "a2", "before", "a2"), raw)

    def test_fail_closed(self):
        for raw in ("a1,a1", "kind:note", "a1,not-an-id", "x" * 17000):
            with self.assertRaises(ValueError):
                refs.edit(raw, "a2", "add")
        for item in ("a1,a2", "", "a1\n", "https://example.org", "a0"):
            with self.assertRaises(ValueError):
                refs.edit("a2", item, "add")
        for item, anchor in (("a9", "a1"), ("a1", "a9")):
            with self.assertRaises(ValueError):
                refs.edit("a1,a2", item, "before", anchor)
        with self.assertRaises(ValueError):
            refs.edit(",".join(f"a{i}" for i in range(1, 257)), "a257", "add")
        with self.assertRaises(ValueError):
            refs.edit("", "a" + "1" * 17000, "add")

    def test_expression_registration(self):
        for name, args, expected in (
            ("refs-add", ["", "a1"], "a1"),
            ("refs-remove", ["a1", "a1"], ""),
            ("refs-before", ["a1,a2", "a2", "a1"], "a2\na1"),
        ):
            self.assertEqual(expr.call(name, [expr.Value("text", v) for v in args]).v, expected)
            expr.parse(f'{name}(' + ", ".join(json.dumps(v) for v in args) + ")")
        self.assertTrue(expr.call("refs-add", [expr.typed(4), expr.typed("a1")]).is_none())
        self.assertTrue(expr.call("refs-add", [expr.typed("bad"), expr.typed("a1")]).is_none())


class WorldPins(unittest.TestCase):
    def setUp(self):
        self.d, r = roomworld.build(say=False)
        self.w = self.d.world
        self.board = r.BOARD
        for name, body in stage.VERBS.items():
            self.create("alex", kind="note", title=name, tags="verb", text=body, on="house")
        self.v = self.create("alex", kind="note", title="My viewer", role="home-view", actor="alex",
                             viewing="a5080", back="a12", with_="doc-page", find="unsent query",
                             draft="keep my words", quote="keep quote")
        self.a = self.create("alex", kind="note", title="Home Board fixture", tags="lens", text='a : text "Home"')
        self.b = self.create("alex", kind="note", title="Other lens", tags="lens", text='a : text "Other"')
        self.c = self.create("alex", kind="note", title="Not a lens", text="plain words")

    def say(self, actor, line):
        self.w.me = actor
        if actor not in self.d._per:
            self.d._per[actor] = ({}, {self.w.root}, len(self.w.events))
        self.d.seen, self.d.open, self.d.last_event_seen = self.d._per[actor]
        self.d._window = ""
        return self.d.dispatch("desk", {"line": line, "whole": True, "reply": uuid.uuid4().hex})

    def ok(self, actor, line):
        result = self.say(actor, line)
        self.assertFalse(result.get("error"), result)
        return result.get("text", "")

    def create(self, signer, **props):
        props = {("with" if k == "with_" else k): v for k, v in props.items()}
        self.ok(signer, f"look {self.board} :1")
        out = self.ok(signer, f"do create {self.board} " + " ".join(f"{k}={json.dumps(v)}" for k, v in props.items()))
        return re.findall(r"created (a\d+)", out)[-1]

    def props(self):
        return self.w.subjects[self.w.nodes[self.v]["subject"]]["props"].copy()

    def act(self, verb, *args, actor="alex", refresh=True):
        if refresh:
            self.ok(actor, f"look {self.v} :3")
            for target in args:
                self.ok(actor, f"look {target} :1")
        return self.say(actor, f"do {verb} {self.v} " + " ".join(args))

    def test_add_remove_reorder_preserve_navigation(self):
        before = self.props()
        for item in (self.a, self.b):
            self.assertFalse(self.act("viewer-pin", item).get("error"))
        self.assertEqual(self.props()["pins"], f"{self.a}\n{self.b}")
        self.assertFalse(self.act("viewer-pin-before", self.b, self.a).get("error"))
        self.assertEqual(self.props()["pins"], f"{self.b}\n{self.a}")
        self.assertFalse(self.act("viewer-unpin", self.b).get("error"))
        self.assertEqual(self.props()["pins"], self.a)
        self.assertEqual({k: v for k, v in self.props().items() if k != "pins"}, before)

    def test_duplicate_add_and_absent_remove_have_no_event(self):
        self.assertFalse(self.act("viewer-pin", self.a).get("error"))
        n = len(self.w.events)
        self.assertFalse(self.act("viewer-pin", self.a).get("error"))
        self.assertFalse(self.act("viewer-unpin", self.b).get("error"))
        self.assertEqual(len(self.w.events), n)

    def test_owner_and_target_policy(self):
        before, n = self.props(), len(self.w.events)
        self.act("viewer-pin", self.a, actor="pike")
        self.act("viewer-pin", self.c)
        self.assertEqual(self.props(), before)
        self.assertEqual(len(self.w.events), n)

    def test_last_remove_and_stale_unrelated_reference_preserved(self):
        self.assertFalse(self.act("viewer-pin", self.a).get("error"))
        self.assertFalse(self.act("viewer-unpin", self.a).get("error"))
        self.assertEqual(self.props().get("pins", ""), "")
        self.ok("alex", f"look {self.v} :3")
        self.ok("alex", f'do prop {self.v} pins="a999999,{self.a}"')
        self.assertFalse(self.act("viewer-pin", self.b).get("error"))
        self.assertEqual(self.props()["pins"], f"a999999\n{self.a}\n{self.b}")

    def test_other_role_and_unknown_target_write_nothing(self):
        wrong = self.create("alex", kind="note", title="Wrong role", actor="alex")
        self.ok("alex", f"look {wrong} :3")
        self.ok("alex", f"look {self.a} :1")
        n = len(self.w.events)
        self.say("alex", f"do viewer-pin {wrong} {self.a}")
        self.act("viewer-pin", "a999999", refresh=False)
        self.assertEqual(len(self.w.events), n)

    def test_patch_inverse_and_compiled_order_active_actions(self):
        # Same lexical frames/anchors as live home-viewer, with inert content in place of nested apps.
        original = '''viewer : column
  of prop:role=home-view,prop:actor=$me as v
  each view
view : column
  pins : row
    of $v.pins as p
    each pin
  content : column
    of $v.viewing as r
    each shown
pin : text "$title"
  role chip
  role chip.on when $item = $v.viewing
  clamp 1
  on click do prop $v viewing=$p back="$v.viewing" find="" with=""
shown : column
  let islens = "yes"
  head : row
    pop : text "Pop out"
      on click host window $title
'''
        patched = stage.patch(original)
        self.assertEqual(stage.patch(patched, reverse=True), original)
        # World-owned appearance tokens come from home-style; use the same roles with a tiny test style.
        roles = {"chip": {}, "chip.on": {}}
        scene.parse(patched, roles=roles)
        self.ok("alex", f"look {self.v} :3")
        self.ok("alex", f'do prop {self.v} pins="{self.a},{self.b}" viewing={self.a}')
        n = len(self.w.events)
        with patch.object(scene, "style_roles", return_value=roles):
            tree = lens_ir.evaluate(self.d, patched)
        def flat(part):
            yield part
            for child in part.get("kids", []):
                yield from flat(child)
        parts = list(flat(tree))
        pin_parts = [p for p in parts if any("viewer-unpin" in str(a) for a in p.get("acts", []))]
        self.assertEqual([p["text"] for p in pin_parts], ["Home Board fixture", "Other lens"], tree)
        self.assertEqual(pin_parts[0]["role"], "chip.on")
        self.assertEqual(pin_parts[1]["role"], "chip")
        self.assertTrue(all(any("viewer-unpin" in str(a) for a in p["acts"]) for p in pin_parts))
        self.assertTrue(all("v.pins" in p.get("freads", {}) for p in pin_parts))
        self.assertEqual(len(self.w.events), n)

    def test_stale_refuses_without_losing_another_pin(self):
        self.ok("alex", f"look {self.v} :3")
        self.ok("pike", f"look {self.v} :3")
        self.ok("pike", f'do prop {self.v} pins="{self.b}"')
        result = self.act("viewer-pin", self.a, refresh=False)
        self.assertTrue(result.get("error"), result)
        self.assertEqual(self.props()["pins"], self.b)

    def test_unpin_ordinary_undo_restores_exact_order(self):
        for item in (self.a, self.b):
            self.assertFalse(self.act("viewer-pin", item).get("error"))
        old = self.props()
        self.assertFalse(self.act("viewer-unpin", self.a).get("error"))
        event = self.w.events[-1]["id"]
        self.ok("alex", f"undo {event}")
        self.assertEqual(self.props(), old)


if __name__ == "__main__":
    unittest.main()
