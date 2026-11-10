"""Historical receipts and log metadata only; no live world or session."""
# health: room test
import unittest
import log_world_accounting as a


def row(seq, at, seconds, count, state="in-step"):
    return dict(records=seq, at=at, observed_seconds=seconds, observed_records=count, state=state)


class AccountingTests(unittest.TestCase):
    def test_self_only_endpoints_cannot_bridge_a_long_idle(self):
        rows = [row(1, 0, 0, 1), row(2, 30, 30, 2), row(3, 60, 60, 3),
                row(4, 90, 90, 4), row(5, 100, 100, 5)]
        seconds, count, correction = a.reconcile(rows, {2, 3, 4})
        self.assertEqual((seconds, count), (0, 2))
        self.assertEqual(correction["removed_self_records"], 3)
        self.assertEqual(correction["removed_seconds"], 100)

    def test_short_independent_interval_survives_intervening_self(self):
        seconds, count, correction = a.reconcile(
            [row(1, 0, 0, 1), row(2, 5, 5, 2), row(3, 10, 10, 3)], {2})
        self.assertEqual((seconds, count), (10, 2))
        self.assertEqual(correction["removed_seconds"], 0)

    def test_rechecks_and_unavailable_do_not_invent_observations(self):
        rows = [row(1, 0, 0, 1), row(1, 10, 10, 1),
                row(1, 20, 10, 1, "unavailable"), row(2, 30, 10, 2)]
        self.assertEqual(a.reconcile(rows, set())[:2], (0, 2))

    def test_missing_prefix_or_metadata_preserves_totals_but_marks_unavailable(self):
        for rows, known in [([row(3, 20, 20, 3)], {3}),
                            ([row(1, 0, 0, 1), row(2, 5, 5, 2)], {1})]:
            seconds, count, correction = a.reconcile(rows, set(), known)
            self.assertEqual((seconds, count), (rows[-1]["observed_seconds"], rows[-1]["observed_records"]))
            self.assertEqual(correction["status"], "unavailable")

    def test_only_house_report_records_are_self(self):
        self.assertTrue(a.self_record(dict(words=a.REPORT_WORDS, by="house")))
        self.assertTrue(a.self_record(dict(words="log-world check", by="house")))
        self.assertFalse(a.self_record(dict(words=a.REPORT_WORDS, by="jeff")))
        self.assertFalse(a.self_record(dict(words="do edit ordinary", by="house")))


if __name__ == "__main__":
    unittest.main()
