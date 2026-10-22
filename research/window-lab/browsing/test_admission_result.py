"""Adversarial receipt checks; never opens a browser or queries host state."""

import copy
import unittest

from admission_result import message_boundary_passed


def receipt():
    result = {
        "topBridge": "undefined",
        "childBridge": "undefined",
        "childReady": "complete",
        "topMessage": "sent",
        "childMessage": "sent",
    }
    return {
        "public_navigation": False,
        "phase": "child_exit",
        "events": [
            {"phase": "offline_policy", "messages": True, "host_objects": False},
            {"phase": "navigation_completed", "success": True},
            {"phase": "evaluated", "mode": "positive_control", "result": result.copy()},
            {"phase": "message_delivery", "mode": "positive_control", "received": ["top", "child"]},
            {"phase": "offline_policy", "messages": False, "host_objects": False},
            {"phase": "navigation_completed", "success": True},
            {"phase": "evaluated", "mode": "disabled", "result": result.copy()},
            {"phase": "message_delivery", "mode": "disabled", "received": []},
        ],
    }


class AdmissionVerdictTests(unittest.TestCase):
    def test_silent_message_refusal_counts_as_no_delivery(self):
        self.assertTrue(message_boundary_passed(receipt()))

    def test_dead_listener_is_not_isolation(self):
        report = receipt()
        report["events"][3]["received"] = []
        self.assertFalse(message_boundary_passed(report))

    def test_child_leak_fails(self):
        report = receipt()
        report["events"][-1]["received"] = ["child"]
        self.assertFalse(message_boundary_passed(report))

    def test_positive_control_must_exercise_both_documents(self):
        report = receipt()
        report["events"][3]["received"] = ["top", "top"]
        self.assertFalse(message_boundary_passed(report))

    def test_crash_timeout_and_failed_navigation_do_not_pass(self):
        for event in (
            {"phase": "deadline_fired"},
            {"phase": "process_failed"},
            {"phase": "navigation_completed", "success": False},
        ):
            report = receipt()
            report["events"].append(event)
            self.assertFalse(message_boundary_passed(report))

    def test_stale_child_and_duplicate_receipts_fail(self):
        report = receipt()
        report["events"][6]["result"]["childReady"] = "loading"
        self.assertFalse(message_boundary_passed(report))
        report = receipt()
        report["events"].append(copy.deepcopy(report["events"][-1]))
        self.assertFalse(message_boundary_passed(report))

    def test_malformed_reports_fail(self):
        for report in (None, {}, {"public_navigation": False, "events": [None]}):
            self.assertFalse(message_boundary_passed(report))

    def test_enabled_host_objects_and_unfinished_run_fail(self):
        report = receipt()
        report["events"][4]["host_objects"] = True
        self.assertFalse(message_boundary_passed(report))
        report = receipt()
        report["phase"] = "initialized"
        self.assertFalse(message_boundary_passed(report))


if __name__ == "__main__":
    unittest.main()
