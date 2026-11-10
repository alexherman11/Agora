# health: room test
"""Health scheduling must change latency, never the set of required verdicts."""
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import health


class RunnerTests(unittest.TestCase):
    def test_inventory_keeps_discovered_rooms_and_fixed_checks(self):
        checks = health.script_checks()
        keys = [c[0] for c in checks]
        self.assertEqual(len(keys), len(set(keys)), "duplicate keys would overwrite a verdict")
        self.assertTrue({Path(p).stem for p in health.room_tests()} <= set(keys))
        self.assertTrue({"test_scene", "test_store", "test_door", "test_visit", "session prints"} <= set(keys))
        store = next(c for c in checks if c[0] == "test_store")
        self.assertEqual(store[1], ["test_store.py", "--quick"])

    def run_fixture(self, keys, *, failed=(), launch_error=(), jobs=4, first=(), fail_fast=False, excuse=()):
        active, started, overlaps = set(), [], []
        lock = threading.Lock()

        class Process:
            def __init__(self, args, **kwargs):
                self.key, self.returncode = args[1].removesuffix(".py"), None
                if self.key in launch_error:
                    raise PermissionError("fixture launch denied")
                with lock:
                    overlaps.append((self.key, set(active)))
                    active.add(self.key)
                    started.append(self.key)

            def communicate(self, timeout=None):
                time.sleep(.02)
                with lock:
                    active.discard(self.key)
                self.returncode = 1 if self.key in failed else 0
                return ("FAIL deliberate fixture\n1 FAILED" if self.returncode else "all passed"), None

        checks = [(k, [k + ".py"], 300, "room tests") for k in keys]
        with patch.object(health.subprocess, "Popen", Process), patch.object(health, "kill_tree"):
            result, stopped = health.run_scripts(checks, jobs, first, fail_fast, excuse)
        return result, stopped, started, overlaps

    def test_parallel_and_serial_preserve_every_check(self):
        keys = ["test_door", "test_visit"] + [f"test_fixture{i}" for i in range(12)]
        serial, _, _, _ = self.run_fixture(keys, jobs=1)
        parallel, stopped, started, overlaps = self.run_fixture(keys)
        self.assertEqual(set(serial), set(parallel))
        self.assertEqual(len(started), len(set(keys)))
        self.assertFalse(stopped)
        self.assertTrue(any(others for key, others in overlaps if key not in health.QUIET))
        for key, others in overlaps:
            self.assertFalse(key in health.QUIET and others)
            self.assertFalse(set(health.QUIET) & others)

    def test_diff_priority_orders_without_omitting_checks(self):
        result, _, started, _ = self.run_fixture(["far", "near", "direct"], jobs=1, first={"direct": 0, "near": 1})
        self.assertEqual(started, ["direct", "near", "far"])
        self.assertEqual(len(result), 3)

    def test_launch_exception_is_a_failed_verdict(self):
        result, stopped, _, _ = self.run_fixture(["denied", "next"], launch_error={"denied"}, jobs=1)
        self.assertFalse(stopped)
        self.assertEqual(set(result), {"denied", "next"})
        self.assertNotEqual(result["denied"][0], 0)
        self.assertIn("PermissionError", result["denied"][1])
        self.assertIsNotNone(health.verdict("denied", "room tests", *result["denied"][:2])[1])

    def test_fail_fast_and_excused_baseline(self):
        result, stopped, started, _ = self.run_fixture(
            ["bad", "later"], failed={"bad"}, jobs=1, fail_fast=True)
        self.assertTrue(stopped)
        self.assertEqual(started, ["bad"])
        self.assertIn("deliberate fixture", health.verdict("bad", "room tests", *result["bad"][:2])[1])
        result, stopped, started, _ = self.run_fixture(
            ["bad", "later"], failed={"bad"}, jobs=1, fail_fast=True, excuse={"bad"})
        self.assertFalse(stopped)
        self.assertEqual(set(result), {"bad", "later"})
        self.assertNotEqual(result["bad"][0], 0)  # still reported, never hidden


if __name__ == "__main__":
    unittest.main()
