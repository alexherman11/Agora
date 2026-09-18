"""Executable counterexamples, not an Agora implementation or browser test.
Run: python research/shared-visual-desk/media/counterexamples.py
"""
import unittest
from dataclasses import dataclass


@dataclass(frozen=True)
class Mapping:
    origin: float
    scale: float

    def content(self, screen):
        return (screen - self.origin) / self.scale


@dataclass(frozen=True)
class Frame:
    session: str
    generation: int
    sequence: int
    media_time: float
    observed_at: float


def paint(old, pigment, opacity):
    return old * (1 - opacity) + pigment * opacity


class Counterexamples(unittest.TestCase):
    def test_gesture_coordinate_mapping_requires_policy(self):
        original = Mapping(100, 2)
        samples = [120, 140, 160]
        intended = [10, 20, 30]
        self.assertEqual([original.content(x) for x in samples], intended)
        for changed in [Mapping(80, 2), Mapping(100, 4), Mapping(20, 0.5)]:
            with self.subTest(changed=changed):
                switched = [original.content(samples[0])]
                switched += [changed.content(x) for x in samples[1:]]
                self.assertNotEqual(switched, intended)
        # Pinning interpretation is one policy. Deferring geometry is another.
        # No assertion here establishes which feels best to a person.

    def test_visible_prediction_is_not_accepted_input(self):
        confirmed = [(0, 0), (1, 1)]
        predicted = [(2, 2), (3, 3)]
        visible_preview = confirmed + predicted
        actual_next = [(2, 0), (3, -1)]
        accepted = confirmed + actual_next
        self.assertNotEqual(visible_preview, accepted)
        self.assertNotEqual(visible_preview + actual_next, accepted)
        self.assertEqual(len(accepted), 4)

    def test_playback_clock_does_not_prove_presented_frame(self):
        frame = Frame("player-a", 1, 90, 3.0, 10.0)
        now, rate = 11.0, 1.0
        estimate = frame.media_time + (now - frame.observed_at) * rate
        stalled_frame = frame
        moving_frame = Frame("player-a", 1, 120, 4.0, now)
        self.assertEqual(estimate, moving_frame.media_time)
        self.assertNotEqual(estimate, stalled_frame.media_time)
        # Same old sample admits both histories. More clever extrapolation cannot
        # decide which occurred without an observation from the media runtime.

    def test_frame_receipt_must_include_session_generation(self):
        old = Frame("player-a", 1, 90, 3.0, 10.0)
        new = Frame("player-a", 2, 90, 3.0, 20.0)
        naive_old = (old.sequence, old.media_time)
        naive_new = (new.sequence, new.media_time)
        self.assertEqual(naive_old, naive_new)
        self.assertNotEqual(old, new)

    def test_selective_undo_of_raster_stroke_is_not_snapshot_restore(self):
        initial = 0.0
        after_alex = paint(initial, 1.0, 0.5)
        after_jeff = paint(after_alex, 0.2, 0.5)
        without_alex = paint(initial, 0.2, 0.5)
        self.assertAlmostEqual(after_jeff, 0.35)
        # Alex's old snapshot loses Jeff's operation; subtracting Alex's earlier
        # delta produces an impossible negative channel. Retained later operations
        # permit recomputation, but smudge/clone sampling needs further policy.
        self.assertNotEqual(after_jeff - after_alex, without_alex)
        self.assertLess(after_jeff - after_alex, 0)
        self.assertNotEqual(without_alex, initial)
        # Pixel equality alone would not preserve Jeff's authorship; identity
        # and retained operations matter even when output happens to match.

    def test_fixed_summary_cannot_imply_pixel_understanding(self):
        first = {"id": "image", "size": [2, 2], "layers": 1}
        second = dict(first)
        pixels_first = [0, 0, 0, 0]
        pixels_second = [0, 1, 1, 0]
        self.assertEqual(first, second)
        self.assertNotEqual(pixels_first, pixels_second)
        # Adding pixel bytes makes reconstruction possible, but not an automatic
        # semantic assertion that the agent understands the depicted subject.

    def test_temporal_selection_requires_coordinate_space(self):
        # A clip uses source seconds 100..110 at timeline seconds 20..30.
        source_start, timeline_start, offset = 100, 20, 5
        source_marker = source_start + offset
        timeline_marker = timeline_start + offset
        self.assertNotEqual(source_marker, timeline_marker)
        # Inserting ten seconds before the clip changes timeline position only.
        self.assertEqual(source_marker, 105)
        self.assertEqual(timeline_marker + 10, 35)


if __name__ == "__main__":
    unittest.main(verbosity=2)
