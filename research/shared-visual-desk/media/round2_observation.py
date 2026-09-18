"""Round-two observation policy fixture; no real media or browser is involved."""
from dataclasses import dataclass, field
import unittest


@dataclass
class Watch:
    dependencies: frozenset = frozenset()
    max_age: float = 1.0
    sampled_at: float | None = None
    reported_status: str = "unknown"
    frame_time: float | None = None
    notices: list = field(default_factory=list)
    event_cursor: int = 0
    coverage_gap: bool = False

    def sample(self, now, status, frame_time):
        if self.sampled_at is not None and now < self.sampled_at:
            raise ValueError("out-of-order observation")
        if status != self.reported_status:
            self.notices.append((now, "status", status))
        self.sampled_at = now
        self.reported_status = status
        self.frame_time = frame_time

    def semantic_event(self, now, sequence, kind):
        if sequence != self.event_cursor + 1:
            self.coverage_gap = True
        self.event_cursor = sequence
        self.notices.append((now, "semantic event", kind))

    def changed(self, now, resource):
        if resource in self.dependencies:
            self.notices.append((now, "dependency changed", resource))

    def look(self, now):
        fresh = self.sampled_at is not None and now - self.sampled_at <= self.max_age
        return {
            "observed_status": self.reported_status if fresh else "unknown: stale observer",
            "sampled_at": self.sampled_at,
            "last_frame_time": self.frame_time,
            "frame_claim": "submitted for composition, not physical-view proof",
            "fresh": fresh,
            "event_coverage": "gap: resync required" if self.coverage_gap else "contiguous",
        }


class ObservationTests(unittest.TestCase):
    def test_five_minutes_of_frames_do_not_flood_agent(self):
        watch = Watch()
        for tick in range(18000):
            watch.sample(tick / 60, "playing", tick / 60)
        self.assertEqual(len(watch.notices), 1)
        self.assertAlmostEqual(watch.look(300)["last_frame_time"], 17999 / 60)
        self.assertTrue(watch.look(300)["fresh"])

    def test_silence_does_not_establish_current_playback(self):
        watch = Watch()
        watch.sample(0, "playing", 82)
        quiet_log = list(watch.notices)
        self.assertEqual(watch.look(2)["observed_status"], "unknown: stale observer")
        self.assertEqual(watch.notices, quiet_log)
        self.assertEqual(watch.look(2)["last_frame_time"], 82)

    def test_relevance_is_work_specific_not_global_style_content_partition(self):
        watch = Watch(dependencies=frozenset({"layer/mask@3", "instrument/brush@2"}))
        watch.changed(0.1, "toolbar/color")
        watch.changed(0.2, "layer/mask@3")
        watch.changed(0.3, "instrument/brush@2")
        self.assertEqual([notice[2] for notice in watch.notices],
                         ["layer/mask@3", "instrument/brush@2"])

    def test_fresh_sample_does_not_prove_complete_event_delivery(self):
        watch = Watch()
        watch.sample(0.2, "playing", 82.2)
        # Event 1 (a seek) was lost; event 2 arrives while the sample is fresh.
        watch.semantic_event(0.3, 2, "volume changed")
        self.assertTrue(watch.look(0.3)["fresh"])
        self.assertEqual(watch.look(0.3)["event_coverage"], "gap: resync required")

    def test_discontinuity_and_late_sample_are_not_silent(self):
        watch = Watch()
        watch.sample(0, "playing", 82)
        watch.sample(0.2, "stalled", 82)
        self.assertEqual(watch.notices[-1], (0.2, "status", "stalled"))
        with self.assertRaises(ValueError):
            watch.sample(0.1, "playing", 82.1)
        self.assertEqual(watch.look(0.3)["observed_status"], "stalled")


if __name__ == "__main__":
    unittest.main(verbosity=2)
