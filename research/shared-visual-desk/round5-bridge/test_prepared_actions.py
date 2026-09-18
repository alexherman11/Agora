"""Real Desk + Claude scene compiler, ephemeral fixtures only; no live sessions."""

import sys
import unittest
from pathlib import Path

NOTATION = Path(__file__).resolve().parents[2] / "text-desk-lab" / "notation"
sys.path.insert(0, str(NOTATION))
from explore import fresh  # noqa: E402
from prepared_actions import Bridge, Refused  # noqa: E402

SOURCE = """window : column
  items : free, of kind:note, each card
card : column, at item, on drag do do move $item to=$x,$y
  body : text $text, on edit do do rewrite $id text="$value"
"""


def command(desk, verb, target, **args):
    r = desk.dispatch("do", {"verb": verb, "target": target, "args": args})
    if r.get("error"):
        raise AssertionError(r["error"])
    return r


def create(desk, title, text, tags=""):
    before = set(desk.world.subjects)
    desk.dispatch("look", {"target": desk.world.root})
    command(desk, "create", desk.world.root, kind="note", title=title, text=text, tags=tags)
    sid = (set(desk.world.subjects) - before).pop()
    return sid, next(iter(desk.world.appearances_of(sid)))


def actions(packet):
    def walk(n):
        yield from n["acts"]
        for kid in n["kids"]:
            yield from walk(kid)

    return list(walk(packet["scene"]))


def action(packet, target, gesture="edit", appearance=None):
    return next(
        a
        for a in actions(packet)
        if a["supported"]
        and a["target"] == target
        and a["on"] == gesture
        and (appearance is None or a["appearance"] == appearance)
    )


class PreparedActionChecks(unittest.TestCase):
    def setUp(self):
        d = fresh()
        d.dispatch("look", {"target": d.world.root})
        command(d, "untile", d.world.root)
        self.note, self.appearance = create(d, "Material", "original")
        self.other, _ = create(d, "Other", "unrelated")
        self.lens, self.lens_appearance = create(d, "Lens", SOURCE, "lens")
        d.dispatch("read", {"target": self.note})
        command(d, "place", self.note, into=d.world.root)
        self.appearances = list(d.world.appearances_of(self.note))
        self.bridge = Bridge(d)

    def frame(self, actor="alex"):
        return self.bridge.offer(actor, self.lens)

    def test_exact_literal_and_empty_string_survive_real_native_operation(self):
        for value in ['  print("hi")  ', "", "line one\nline two", r"\n $& $value ; do remove a03"]:
            handle = action(self.frame(), self.note)["handle"]
            result = self.bridge.invoke("alex", handle, {"value": value})
            self.assertEqual(self.bridge.snapshot()["subjects"][self.note]["text"], value)
            self.assertEqual(result["events"][-1]["by"], "alex")

    def test_old_frame_cannot_overwrite_another_actors_edit_even_after_new_frame(self):
        old = action(self.frame(), self.note)["handle"]
        new = action(self.frame("agent"), self.note)["handle"]
        self.bridge.invoke("agent", new, {"value": "agent contribution"})
        self.frame()  # Refreshing observation elsewhere must NOT renew the old handle.
        with self.assertRaisesRegex(Refused, "by agent"):
            self.bridge.invoke("alex", old, {"value": "stale draft"})
        self.assertEqual(
            self.bridge.snapshot()["subjects"][self.note]["text"], "agent contribution"
        )

    def test_definition_change_invalidates_offered_action(self):
        old = action(self.frame(), self.note)["handle"]
        edit_lens = action(self.frame(), self.lens)["handle"]
        self.bridge.invoke("alex", edit_lens, {"value": SOURCE + "# revised definition\n"})
        with self.assertRaisesRegex(Refused, "Definition changed"):
            self.bridge.invoke("alex", old, {"value": "must not apply"})

    def test_unrelated_subject_edit_does_not_expire_content_action(self):
        old = action(self.frame(), self.note)["handle"]
        other = action(self.frame("agent"), self.other)["handle"]
        self.bridge.invoke("agent", other, {"value": "another contribution"})
        self.bridge.invoke("alex", old, {"value": "accepted"})

    def test_move_one_appearance_preserves_second_and_content_action(self):
        frame = self.frame()
        content = action(frame, self.note)["handle"]
        first, second = self.appearances
        drag = action(frame, first, "drag")["handle"]
        before = self.bridge.snapshot()["nodes"][second].copy()
        self.bridge.invoke("alex", drag, {"x": 90, "y": 130})
        after = self.bridge.snapshot()
        self.assertEqual(after["nodes"][first]["x"], 90)
        self.assertEqual(after["nodes"][second], before)
        self.bridge.invoke("alex", content, {"value": "shared through either occurrence"})
        self.assertEqual(
            self.bridge.snapshot()["subjects"][self.note]["text"],
            "shared through either occurrence",
        )

    def test_bad_inputs_cannot_mutate_or_retarget_and_success_is_single_use(self):
        handle = action(self.frame(), self.note)["handle"]
        before = self.bridge.snapshot()
        for payload in [{"value": "x", "target": self.other}, {"value": 42}, {}]:
            with self.assertRaises(Refused):
                self.bridge.invoke("alex", handle, payload)
            self.assertEqual(self.bridge.snapshot(), before)
        with self.assertRaisesRegex(Refused, "another actor"):
            self.bridge.invoke("other", handle, {"value": "wrong actor"})
        self.bridge.invoke("alex", handle, {"value": "once"})
        with self.assertRaisesRegex(Refused, "consumed"):
            self.bridge.invoke("alex", handle, {"value": "twice"})

    def test_cancelled_action_and_unsupported_drop_are_explicit(self):
        h = action(self.frame(), self.note)["handle"]
        self.bridge.cancel(h)
        with self.assertRaises(Refused):
            self.bridge.invoke("alex", h, {"value": "after cancel"})
        h = action(self.frame(), self.lens)["handle"]
        self.bridge.invoke("alex", h, {"value": SOURCE.replace("on drag", "on drop")})
        frame = self.frame()
        self.assertTrue(frame["unsupported"])
        self.assertTrue(any(a["on"] == "drop" and not a["supported"] for a in actions(frame)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
