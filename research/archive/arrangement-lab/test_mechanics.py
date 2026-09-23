"""Invariant and counterexample tests; no live Agora world or browser is accessed."""

import random
import unittest
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from functools import partial
from itertools import permutations

from fixtures import edit, make_lab
from model import Lab, Refusal, key, sequence
from planners import detach, layer, partition, place, reorder, representative, tile


def accept(lab, builder, request="arrange"):
    plan = builder.finish()
    return lab.commit(plan.digest, actor="alex", request_id=request)


def state(lab):
    return (dict(lab.cells), deepcopy(lab.events), deepcopy(lab.requests))


def intersects(a, b):
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


class Mechanics(unittest.TestCase):
    def test_failed_operator_cannot_leave_a_committable_partial_plan(self):
        lab = make_lab()
        b = lab.builder()
        # Sorted first item succeeds, then a later target fails.
        with self.assertRaises(Refusal):
            tile(b, "desk", ["oas-0", "zz-missing"], [0, 0, 700, 500], 2, "human")
        with self.assertRaisesRegex(Refusal, "failed"):
            b.finish()

    def test_selection_and_reclassification_need_an_explicit_dependency_policy(self):
        lab = make_lab()
        b = lab.builder()
        representative(b)
        # This changes an input used by another operation in the SAME plan.
        # Native stale-read checks alone cannot catch this: nothing committed yet.
        b.effect(key("subject", "subject-other-0", "tags"), ["oas"])
        with self.assertRaisesRegex(Refusal, "read/write dependency"):
            b.finish()

    def test_forty_appearances_one_event_and_exact_undo(self):
        lab = make_lab()
        before = {a: c.value for a, c in lab.cells.items()}
        builder = lab.builder()
        related, pinned, remainder = representative(builder)
        self.assertEqual((len(related), len(pinned), len(remainder)), (8, 1, 31))
        accept(lab, builder)
        self.assertEqual(len(lab.events), 1)
        self.assertEqual(lab.events[0]["actor"], "alex")
        stack = lab.value(key("surface", "desk", "stack:normal"))
        self.assertEqual(stack[-1], "mail")
        self.assertEqual(set(stack[:31]), set(remainder))
        rectangles = [lab.value(key("occurrence", o, "placement"))["rect"] for o in related]
        mail = lab.value(key("occurrence", "mail", "placement"))["rect"]
        for i, rect in enumerate(rectangles):
            self.assertLessEqual(rect[0] + rect[2], 720)
            self.assertFalse(intersects(rect, mail))
            for other in rectangles[i + 1 :]:
                self.assertFalse(intersects(rect, other))
        undo = lab.undo_plan(1)
        lab.commit(undo.digest, actor="alex", request_id="undo")
        self.assertEqual(before, {a: c.value for a, c in lab.cells.items()})
        self.assertEqual(lab.cells, lab.replay())

    def test_preview_is_zero_write(self):
        lab = make_lab()
        original = state(lab)
        b = lab.builder()
        representative(b)
        b.finish()
        self.assertEqual(original, state(lab))

    def test_all_720_operator_arrival_orders_have_identical_plan(self):
        expected = None
        for order in permutations(range(6)):
            lab = make_lab()
            b = lab.builder()
            related, pinned, rest = partition(b, "desk", "oas", "mail")
            actions = [
                partial(tile, b, "desk", related, [20, 20, 700, 1100], 2, "human"),
                partial(place, b, "desk", "mail", [900, 50, 600, 900]),
                partial(layer, b, "desk", rest, "sink"),
                partial(layer, b, "desk", pinned, "raise"),
                partial(reorder, b, "review", ["review-c"], "review-a"),
                partial(place, b, "board", "duplicate-a", [500, 500, 300, 240]),
            ]
            for action in order:
                actions[action]()
            plan = b.finish()
            if expected is None:
                expected = plan.digest
            self.assertEqual(expected, plan.digest)
            lab.commit(plan.digest, actor="alex", request_id="permutation")
            self.assertEqual(lab.cells, lab.replay())

    def test_same_subject_two_occurrences_and_independent_arrangements(self):
        lab = make_lab()
        before = {a: c.value for a, c in lab.cells.items()}
        b = lab.builder()
        place(b, "board", "duplicate-a", [500, 500, 300, 240])
        accept(lab, b)
        affected = key("occurrence", "duplicate-a", "placement")
        for address, value in before.items():
            if address != affected:
                self.assertEqual(lab.value(address), value)

    def test_camera_change_does_not_change_saved_placements(self):
        lab = make_lab()
        b = lab.builder()
        representative(b)
        plan = b.finish()
        edit(lab, {key("session", "window-b", "camera"): [200, 100, 2]}, "zoom")
        lab.commit(plan.digest, actor="alex", request_id="arrange")
        self.assertEqual(lab.value(key("session", "window-a", "camera")), [0, 0, 1])

    def test_unrelated_text_edit_does_not_invalidate_layout_preview(self):
        lab = make_lab()
        b = lab.builder()
        representative(b)
        plan = b.finish()
        edit(lab, {key("subject", "subject-oas-0", "text"): "A newer paragraph"}, "text")
        lab.commit(plan.digest, actor="alex", request_id="arrange")
        self.assertEqual(lab.value(key("subject", "subject-oas-0", "text")), "A newer paragraph")

    def test_classification_change_invalidates_exact_scene(self):
        lab = make_lab()
        b = lab.builder()
        representative(b)
        plan = b.finish()
        edit(lab, {key("subject", "subject-other-0", "tags"): ["oas"]}, "tag")
        before = state(lab)
        with self.assertRaisesRegex(Refusal, "Stale"):
            lab.commit(plan.digest, actor="alex", request_id="arrange")
        self.assertEqual(before, state(lab))

    def test_negative_selection_membership_phantom_is_guarded(self):
        lab = make_lab()
        b = lab.builder()
        representative(b)
        plan = b.finish()
        members = lab.value(key("surface", "desk", "members"))
        stack = lab.value(key("surface", "desk", "stack:normal"))
        # Close an unselected occurrence; it remains retained but is no longer in this desk.
        edit(
            lab,
            {
                key("surface", "desk", "members"): members[1:],
                key("surface", "desk", "stack:normal"): [x for x in stack if x != members[0]],
            },
            "close",
        )
        before = state(lab)
        with self.assertRaisesRegex(Refusal, "Stale"):
            lab.commit(plan.digest, actor="alex", request_id="arrange")
        self.assertEqual(before, state(lab))

    def test_new_member_not_in_preview_is_detected_even_without_old_cell_edits(self):
        base = make_lab()
        initial = {a: c.value for a, c in base.cells.items()}
        for field in ("binding", "placement", "minimum", "stratum"):
            initial[key("occurrence", "newcomer", field)] = deepcopy(
                initial[key("occurrence", "other-0", field)]
            )
        lab = Lab(initial)
        lab.permissions = deepcopy(base.permissions)
        lab.observations = dict(base.observations)
        b = lab.builder()
        representative(b)
        plan = b.finish()
        edit(
            lab,
            {
                key("surface", "desk", "members"): lab.value(key("surface", "desk", "members"))
                + ["newcomer"],
                key("surface", "desk", "stack:normal"): lab.value(
                    key("surface", "desk", "stack:normal")
                )
                + ["newcomer"],
            },
            "open",
        )
        with self.assertRaisesRegex(Refusal, "Stale"):
            lab.commit(plan.digest, actor="alex", request_id="arrange")

    def test_pinned_mail_wins_even_when_it_is_oas_related(self):
        lab = make_lab()
        b = lab.builder()
        related, mail, other = partition(b, "desk", "oas", "mail")
        self.assertEqual(mail, ["mail"])
        self.assertNotIn("mail", related + other)
        self.assertEqual(set(related + mail + other), set(b.surface("desk")))

    def test_conflicting_rectangles_refuse_regardless_of_order(self):
        for first, second in ((100, 200), (200, 100)):
            lab = make_lab()
            before = state(lab)
            b = lab.builder()
            place(b, "desk", "oas-0", [first, 0, 240, 200])
            with self.assertRaisesRegex(Refusal, "Contradictory effects"):
                place(b, "desk", "oas-0", [second, 0, 240, 200])
            self.assertEqual(before, state(lab))

    def test_identical_effects_coalesce(self):
        lab = make_lab()
        b = lab.builder()
        for _ in range(3):
            place(b, "desk", "oas-0", [100, 0, 240, 200])
        receipt = accept(lab, b)
        self.assertEqual(receipt["changed"], 1)

    def test_two_individually_valid_sinks_can_be_incompatible(self):
        lab = make_lab()
        before = state(lab)
        b = lab.builder()
        layer(b, "desk", ["oas-0"], "sink")
        layer(b, "desk", ["oas-1"], "sink")
        with self.assertRaisesRegex(Refusal, "cycle"):
            b.finish()
        self.assertEqual(before, state(lab))

    def test_stacking_and_reading_order_are_independent(self):
        lab = make_lab()
        original = lab.value(key("surface", "review", "reading_order"))
        b = lab.builder()
        layer(b, "review", ["review-a"], "sink")
        accept(lab, b)
        self.assertEqual(original, lab.value(key("surface", "review", "reading_order")))

    def test_sink_preserves_relative_order_within_both_groups(self):
        lab = make_lab()
        original = lab.value(key("surface", "desk", "stack:normal"))
        selected = ["oas-1", "other-7", "mail"]
        b = lab.builder()
        layer(b, "desk", selected, "sink")
        accept(lab, b)
        self.assertEqual(
            lab.value(key("surface", "desk", "stack:normal")),
            [x for x in original if x in selected] + [x for x in original if x not in selected],
        )

    def test_strata_are_not_flattened_by_raise(self):
        base = make_lab()
        initial = {a: c.value for a, c in base.cells.items()}
        initial[key("occurrence", "other-0", "stratum")] = "overlay"
        initial[key("surface", "desk", "stack:normal")].remove("other-0")
        initial[key("surface", "desk", "stack:overlay")] = ["other-0"]
        lab = Lab(initial)
        lab.permissions = deepcopy(base.permissions)
        b = lab.builder()
        layer(b, "desk", ["mail"], "raise")
        accept(lab, b)
        self.assertEqual(lab.value(key("surface", "desk", "stack:overlay")), ["other-0"])
        self.assertNotIn("other-0", lab.value(key("surface", "desk", "stack:normal")))

    def test_undo_preserves_later_content_and_other_arrangement_edits(self):
        lab = make_lab()
        b = lab.builder()
        representative(b)
        receipt = accept(lab, b)
        edit(
            lab,
            {
                key("subject", "subject-oas-0", "text"): "Keep this text",
                key("subject", "subject-oas-0", "tags"): ["changed-project"],
            },
            "content",
        )
        other = lab.builder()
        place(other, "board", "duplicate-a", [700, 20, 300, 250])
        accept(lab, other, "board")
        undo = lab.undo_plan(receipt["event"])
        lab.commit(undo.digest, actor="alex", request_id="undo")
        self.assertEqual(lab.value(key("subject", "subject-oas-0", "text")), "Keep this text")
        self.assertEqual(lab.value(key("occurrence", "duplicate-a", "placement"))["rect"][0], 700)

    def test_undo_conflict_refuses_whole_compensation(self):
        lab = make_lab()
        b = lab.builder()
        representative(b)
        accept(lab, b)
        later = lab.builder()
        place(later, "desk", "oas-0", [800, 800, 300, 250])
        accept(lab, later, "later")
        before = state(lab)
        with self.assertRaisesRegex(Refusal, "later edit"):
            lab.undo_plan(1)
        self.assertEqual(before, state(lab))

    def test_undo_detects_aba_even_when_value_matches_again(self):
        lab = make_lab()
        b = lab.builder()
        representative(b)
        accept(lab, b)
        address = key("occurrence", "oas-0", "placement")
        arranged = lab.value(address)
        edit(lab, {address: {"mode": "free", "rect": [800, 800, 300, 250]}}, "away")
        edit(lab, {address: arranged}, "back")
        with self.assertRaisesRegex(Refusal, "ABA"):
            lab.undo_plan(1)

    def test_undo_checks_intervening_constraints(self):
        lab = make_lab()
        b = lab.builder()
        representative(b)
        accept(lab, b)
        edit(lab, {key("occurrence", "oas-0", "minimum"): [300, 250]}, "larger-minimum")
        undo = lab.undo_plan(1)
        before = state(lab)
        with self.assertRaisesRegex(Refusal, "minimum size"):
            lab.commit(undo.digest, actor="alex", request_id="undo")
        self.assertEqual(before, state(lab))

    def test_reused_occurrence_identity_does_not_receive_old_undo(self):
        lab = make_lab()
        b = lab.builder()
        representative(b)
        accept(lab, b)
        address = key("occurrence", "oas-0", "binding")
        binding = lab.value(address)
        binding["incarnation"] += 1
        edit(lab, {address: binding}, "rebind")
        with self.assertRaisesRegex(Refusal, "identity"):
            lab.undo_plan(1)

    def test_contract_change_invalidates_preview_and_undo(self):
        lab = make_lab()
        b = lab.builder()
        representative(b)
        plan = b.finish()
        edit(lab, {key("surface", "desk", "contract"): "arrangement-v2"}, "upgrade")
        with self.assertRaisesRegex(Refusal, "Stale"):
            lab.commit(plan.digest, actor="alex", request_id="arrange")

    def test_revocation_invalidates_prepared_plan(self):
        lab = make_lab()
        b = lab.builder()
        representative(b)
        plan = b.finish()
        lab.grant("alex", {"board"})
        before = state(lab)
        with self.assertRaisesRegex(Refusal, "authority"):
            lab.commit(plan.digest, actor="alex", request_id="arrange")
        self.assertEqual(before, state(lab))

    def test_one_unauthorized_surface_refuses_multi_surface_plan(self):
        lab = make_lab()
        b = lab.builder()
        representative(b)
        reorder(b, "review", ["review-c"], "review-a")
        plan = b.finish()
        lab.grant("alex", {"desk"})
        before = state(lab)
        with self.assertRaisesRegex(Refusal, "authority"):
            lab.commit(plan.digest, actor="alex", request_id="arrange")
        self.assertEqual(before, state(lab))

    def test_another_caller_cannot_use_prepared_plan(self):
        lab = make_lab()
        b = lab.builder()
        representative(b)
        plan = b.finish()
        lab.grant("jeff", {"desk"})
        with self.assertRaisesRegex(Refusal, "another caller"):
            lab.commit(plan.digest, actor="jeff", request_id="arrange")

    def test_preview_bound_to_measurement_generation(self):
        lab = make_lab()
        b = lab.builder()
        representative(b)
        plan = b.finish()
        frame = lab.observations[key("measurement", "human", "frame")].value
        frame["width"] = 1100
        lab.observe("human", frame)
        before = state(lab)
        with self.assertRaisesRegex(Refusal, "Stale"):
            lab.commit(plan.digest, actor="alex", request_id="arrange")
        self.assertEqual(before, state(lab))

    def test_unknown_measurements_do_not_get_default_viewport(self):
        lab = make_lab()
        b = lab.builder()
        with self.assertRaisesRegex(Refusal, "Missing address"):
            tile(b, "desk", ["oas-0"], [0, 0, 500, 500], 1, "closed-view")

    def test_infeasible_layout_refuses_without_shrinking_below_minimum(self):
        lab = make_lab()
        before = state(lab)
        b = lab.builder()
        with self.assertRaisesRegex(Refusal, "cannot fit"):
            tile(b, "desk", b.surface("desk"), [0, 0, 400, 300], 2, "human")
        self.assertEqual(before, state(lab))

    def test_literal_move_cannot_silently_compete_with_maintained_placement(self):
        lab = make_lab()
        address = key("occurrence", "oas-0", "placement")
        edit(lab, {address: {"mode": "managed", "rule": "grid-1", "slot": 0}}, "managed")
        before = state(lab)
        b = lab.builder()
        with self.assertRaisesRegex(Refusal, "maintained"):
            place(b, "desk", "oas-0", [800, 800, 300, 250])
        self.assertEqual(before, state(lab))
        b = lab.builder()
        detach(b, "desk", "oas-0", [800, 800, 300, 250])
        accept(lab, b)
        undo = lab.undo_plan(2)
        lab.commit(undo.digest, actor="alex", request_id="undo-detach")
        self.assertEqual(lab.value(address)["mode"], "managed")

    def test_domain_invariant_refuses_combined_container_cycle(self):
        lab = make_lab()
        b = lab.builder()
        b.effect(key("surface", "board", "parent"), "review")
        b.effect(key("surface", "review", "parent"), "board")
        before = state(lab)
        with self.assertRaisesRegex(Refusal, "Container cycle"):
            accept(lab, b)
        self.assertEqual(before, state(lab))

    def test_response_loss_retry_and_restart_do_not_repeat_effects(self):
        lab = make_lab()
        b = lab.builder()
        representative(b)
        plan = b.finish()
        first = lab.commit(plan.digest, actor="alex", request_id="arrange")
        lab.restart()
        self.assertEqual(lab.issued, {})
        second = lab.commit(plan.digest, actor="alex", request_id="arrange")
        self.assertEqual(first, second)
        self.assertEqual(len(lab.events), 1)
        self.assertEqual(lab.cells, lab.replay())

    def test_request_id_collision_refuses_different_plan(self):
        lab = make_lab()
        b = lab.builder()
        representative(b)
        accept(lab, b)
        b = lab.builder()
        place(b, "board", "duplicate-a", [500, 500, 300, 250])
        plan = b.finish()
        with self.assertRaisesRegex(Refusal, "different accepted plan"):
            lab.commit(plan.digest, actor="alex", request_id="arrange")

    def test_concurrent_conflicting_plans_have_one_winner(self):
        lab = make_lab()
        plans = []
        for x in (200, 400):
            b = lab.builder()
            place(b, "desk", "oas-0", [x, 0, 300, 250])
            plans.append(b.finish())

        def attempt(plan):
            try:
                return lab.commit(plan.digest, actor="alex", request_id=plan.digest)
            except Refusal:
                return None

        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(attempt, plans))
        self.assertEqual(sum(x is not None for x in results), 1)
        self.assertEqual(len(lab.events), 1)
        self.assertEqual(lab.cells, lab.replay())

    def test_disjoint_surface_plans_can_both_commit(self):
        lab = make_lab()
        first, second = lab.builder(), lab.builder()
        place(first, "desk", "oas-0", [500, 0, 300, 250])
        place(second, "board", "duplicate-a", [500, 0, 300, 250])
        p, q = first.finish(), second.finish()
        lab.commit(p.digest, actor="alex", request_id="one")
        lab.commit(q.digest, actor="alex", request_id="two")
        self.assertEqual(len(lab.events), 2)

    def test_explicit_stages_resolve_dataflow_without_intermediate_commits(self):
        lab = make_lab()

        def classify(b):
            b.effect(key("subject", "subject-other-0", "tags"), ["oas"])
            b.describe("tag", "subject", ["subject-other-0"], project="oas")

        plan = sequence(lab, "alex", [classify, representative])
        self.assertEqual(len(lab.events), 0)
        self.assertEqual(len(lab.issued), 1)
        lab.commit(plan.digest, actor="alex", request_id="classify-and-arrange")
        self.assertEqual(len(lab.events), 1)
        self.assertLess(lab.value(key("occurrence", "other-0", "placement"))["rect"][0], 720)
        self.assertEqual(lab.value(key("subject", "subject-other-0", "tags")), ["oas"])
        undo = lab.undo_plan(1)
        lab.commit(undo.digest, actor="alex", request_id="undo")
        self.assertEqual(lab.cells.keys(), lab.genesis.keys())
        self.assertEqual(
            {a: c.value for a, c in lab.cells.items()},
            {a: c.value for a, c in lab.genesis.items()},
        )

    def test_later_stage_failure_leaves_no_issued_partial_plan(self):
        lab = make_lab()

        def bad_stage(b):
            place(b, "desk", "missing", [0, 0, 300, 250])

        before = state(lab)
        with self.assertRaises(Refusal):
            sequence(lab, "alex", [representative, bad_stage])
        self.assertEqual(before, state(lab))
        self.assertEqual(lab.issued, {})

    def test_later_stage_reads_previous_proposed_value(self):
        lab = make_lab()
        address = key("occurrence", "oas-0", "placement")

        def first(b):
            place(b, "desk", "oas-0", [400, 0, 300, 250])

        def second(b):
            placement = b.read(address)
            placement["rect"][0] += 10
            b.effect(address, placement)
            b.describe("translate", "desk", ["oas-0"], dx=10)

        plan = sequence(lab, "alex", [first, second])
        lab.commit(plan.digest, actor="alex", request_id="staged")
        self.assertEqual(lab.value(address)["rect"][0], 410)
        self.assertEqual(len(lab.events), 1)

    def test_staged_plan_still_guards_original_external_inputs(self):
        lab = make_lab()
        address = key("occurrence", "oas-0", "placement")
        plan = sequence(
            lab,
            "alex",
            [
                lambda b: place(b, "desk", "oas-0", [400, 0, 300, 250]),
                lambda b: place(b, "desk", "oas-0", [500, 0, 300, 250]),
            ],
        )
        edit(lab, {address: {"mode": "free", "rect": [800, 0, 300, 250]}}, "intervening")
        with self.assertRaisesRegex(Refusal, "Stale"):
            lab.commit(plan.digest, actor="alex", request_id="staged")

    def test_500_seeded_valid_layouts_respect_bounds_minima_and_no_overlap(self):
        rng = random.Random(16092026)
        for case in range(500):
            lab = make_lab()
            b = lab.builder()
            targets = [f"oas-{i}" for i in range(rng.randint(1, 8))]
            columns = rng.randint(1, min(4, len(targets)))
            rows = math_ceil(len(targets), columns)
            width = columns * 220 + (columns - 1) * 12 + rng.randint(0, 100)
            height = rows * 180 + (rows - 1) * 12 + rng.randint(0, 100)
            frame = lab.observations[key("measurement", "human", "frame")].value
            frame.update(width=max(width + 40, 1600), height=max(height + 40, 1200))
            lab.observe("human", frame)
            # Construct after the current observation, just as a real plan must.
            b = lab.builder()
            tile(b, "desk", targets, [20, 20, width, height], columns, "human")
            accept(lab, b, str(case))
            rects = [lab.value(key("occurrence", x, "placement"))["rect"] for x in targets]
            for i, r in enumerate(rects):
                self.assertGreaterEqual(r[2], 220)
                self.assertGreaterEqual(r[3], 180)
                self.assertLessEqual(r[0] + r[2], width + 20 + 1e-9)
                self.assertLessEqual(r[1] + r[3], height + 20 + 1e-9)
                for s in rects[i + 1 :]:
                    self.assertFalse(intersects(r, s))


def math_ceil(n, d):
    return (n + d - 1) // d


if __name__ == "__main__":
    unittest.main(verbosity=2)
