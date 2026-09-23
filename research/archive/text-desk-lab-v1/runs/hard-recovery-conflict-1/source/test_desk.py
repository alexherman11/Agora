"""Invariant tests and hidden feasibility scripts; never passed to the model."""

from copy import deepcopy
import unittest
from scenarios import assess, build


def do(d, verb, target, **args):
    result = d.dispatch(
        "act", dict(verb=verb, target=target, expected=d.get(target)["rev"], args=args)
    )
    if "error" in result:
        raise AssertionError(result)
    return result


class DeskTests(unittest.TestCase):
    def test_context_bounded_and_children_located(self):
        d = build("meeting", "context")
        result = d.look("planning", depth=8, limit=100)["text"]
        self.assertIn("READ BOUNDED", result)
        self.assertIn("xy=(380,340)", result)
        self.assertIn("tile:", result)
        self.assertEqual(d.initial, d.nodes)

    def test_failed_batch_has_no_partial_move(self):
        d = build("meeting")
        before = d.snapshot()
        result = d.dispatch(
            "act",
            dict(
                verb="tile",
                target="planning",
                expected=1,
                args={"items": ["p-risk", "p-agenda"], "columns": 2},
            ),
        )
        self.assertIn("error", result)
        self.assertEqual(before, d.snapshot())
        self.assertFalse(d.events)

    def test_removal_retains_shared_content(self):
        d = build("meeting")
        note = deepcopy(d.get("risk-live"))
        do(d, "remove", "p-risk-alt")
        self.assertEqual(note, d.get("risk-live"))
        self.assertIn("p-risk", d.nodes)
        self.assertIn("r-risk", d.nodes)

    def test_dependency_refusal_atomic(self):
        d = build("release")
        before = d.snapshot()
        result = d.dispatch(
            "act", dict(verb="place", target="card-t-ship", expected=1, args={"container": "done"})
        )
        self.assertIn("error", result)
        self.assertEqual(before, d.snapshot())

    def test_layout_undo_preserves_later_content(self):
        d = build("meeting")
        original = deepcopy(d.get("p-risk"))
        do(d, "tile", "planning", items=["p-risk", "p-risk-alt"], columns=2)
        do(d, "edit", "risk-live", part="fallback", before="3 October", after="10 October")
        d.undo("event-1")
        self.assertEqual(d.get("p-risk")["x"], original["x"])
        self.assertIn("10 October", d.get("risk-live")["parts"][1]["text"])

    def test_stale_edit_retains_external_change(self):
        d = build("proposal")
        result = d.dispatch(
            "act",
            dict(
                verb="edit",
                target="proposal",
                expected=1,
                args={"part": "delivery", "before": "3 October", "after": "10 October"},
            ),
        )
        self.assertIn("Stale", result["error"])
        self.assertIn("$19,500", d.get("proposal")["parts"][2]["text"])
        self.assertIn("3 October", d.get("proposal")["parts"][1]["text"])

    def test_feasible_meeting(self):
        d = build("meeting")
        do(d, "edit", "risk-live", part="fallback", before="3 October", after="10 October")
        do(d, "reference", "questions", source="risk-live")
        do(
            d,
            "create",
            "planning",
            kind="note",
            title="Supplier call checklist",
            parts=[
                {"id": "delivery", "text": "Confirm the 10 October delivery"},
                {"id": "stock", "text": "Ask Maya to verify reserve stock"},
            ],
        )
        do(d, "tile", "planning", items=["p-risk", "appearance-3"], columns=2)
        do(d, "move", "p-risk-alt", x=220, y=340)
        self.assertTrue(assess("meeting", d)["passed"], assess("meeting", d))
        self.check_replay(d)

    def test_feasible_proposal(self):
        d = build("proposal")
        d.dispatch(
            "act",
            dict(
                verb="edit",
                target="proposal",
                expected=1,
                args={"part": "delivery", "before": "3 October", "after": "10 October"},
            ),
        )
        do(d, "edit", "proposal", part="delivery", before="3 October", after="10 October")
        do(
            d,
            "insert",
            "proposal",
            after="delivery",
            id="followup",
            text="Maya will confirm reserve stock before the supplier call.",
        )
        do(d, "reference", "review", source="proposal", part="delivery")
        do(d, "remove", "doc-old")
        do(d, "order", "review", items=["appearance-4", "r-risk"])
        self.assertTrue(assess("proposal", d)["passed"], assess("proposal", d))
        self.check_replay(d)

    def test_feasible_release(self):
        d = build("release")
        do(d, "place", "card-t-sign", container="done")
        do(d, "place", "card-t-smoke", container="done")
        do(
            d,
            "create",
            "todo",
            kind="task",
            title="Fix payment keyboard focus",
            parts=[{"id": "details", "text": "Fix lost keyboard focus in the payment dialog."}],
        )
        do(d, "reference", "questions", source="content-3")
        self.assertTrue(assess("release", d)["passed"], assess("release", d))
        self.check_replay(d)

    def check_replay(self, d):
        rebuilt = deepcopy(d.initial)
        for event in d.events:
            for key, value in event["after"].items():
                if value is None:
                    rebuilt.pop(key, None)
                else:
                    rebuilt[key] = deepcopy(value)
        self.assertEqual(rebuilt, d.nodes)


if __name__ == "__main__":
    unittest.main()
