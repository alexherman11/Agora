"""Synthetic kernel identities only. No native query or interpreter admission."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parent))
from admission_job import HostFence, Refused


class Native:
    def __init__(self):
        self.ids = {10: (100, r"c:\fixture\launcher.exe"),
                    11: (110, r"c:\fixture\python.exe"),
                    12: (120, r"c:\fixture\python.exe"),
                    30: (130, r"c:\fixture\other.exe")}
        self.parents = {10: 1, 11: 10, 12: 11, 30: 1}
        self.closed, self.denied, self.excluded = [], set(), set()
        self.k = self

    def OpenProcess(self, access, inherit, pid):
        return None if pid in self.denied else pid

    def CloseHandle(self, handle):
        self.closed.append(handle)

    def of_handle(self, handle):
        return self.ids.get(handle)

    def processes(self):
        return [(pid, parent, "not-authority.exe") for pid, parent in self.parents.items()]


class Hosts(unittest.TestCase):
    def setUp(self):
        self.native = Native()
        def verify(handle):
            if handle != 900:
                raise RuntimeError("wrong retained Job")
        self.scope = NS(handle=900, descriptor={"id": "job"},
                        snapshot=lambda: {"pids": list(self.native.ids),
                                          "active": len(self.native.ids)},
                        native=NS(verify=verify,
                                  contains=lambda job, handle: handle not in self.native.excluded))
        self.allowed = {r"c:\fixture\python.exe": "synthetic-hash"}
        self.fence = HostFence(self.scope, self.native,
                               {"pid": 10, "created": 100, "exe": r"c:\fixture\launcher.exe"},
                               "token", "desktop", r"C:\fixture\profile",
                               self.allowed, self.native.processes, lambda path: "synthetic-hash")
        self.addCleanup(self.fence.close)

    def envelope(self, pid=12):
        return {"request": "token", "desktop": "desktop",
                "profile": r"C:\fixture\profile", "pid": pid, "phase": "importing"}

    def test_measured_descendant_and_repeat_pin(self):
        binding = self.fence.envelope(self.envelope(), initial=True)
        self.assertEqual(binding["host"]["pid"], 12)
        self.assertEqual(binding["root"]["pid"], 10)
        self.assertEqual(self.fence.pin(12), binding)
        self.assertEqual(len(self.fence.handles), 3)
        self.assertEqual(self.fence.envelope(self.envelope(), initial=True), binding)

    def test_direct_host_needs_its_own_reviewed_image(self):
        with self.assertRaises(Refused):
            self.fence.pin(10)
        self.setUp()
        self.fence.allowed[r"c:\fixture\launcher.exe"] = "synthetic-hash"
        self.assertEqual(self.fence.pin(10)["host"]["pid"], 10)

    def test_empty_allowlist_refuses_without_opening_process(self):
        self.fence.allowed.clear()
        with self.assertRaises(Refused):
            self.fence.pin(12)
        self.assertEqual(self.fence.handles, {})

    def test_wrong_image_and_wrong_hash(self):
        for image, digest in ((r"c:\fixture\other.exe", "synthetic-hash"),
                              (r"c:\fixture\python.exe", "changed")):
            with self.subTest(image=image):
                self.setUp()
                self.native.ids[12] = (120, image)
                self.fence.digest = lambda path, digest=digest: digest
                with self.assertRaises(Refused):
                    self.fence.pin(12)
                self.assertEqual(self.fence.handles, {})

    def test_unrelated_job_member_is_not_provenance(self):
        self.native.ids[30] = (130, r"c:\fixture\python.exe")
        with self.assertRaises(Refused):
            self.fence.pin(30)

    def test_missing_loop_and_birth_order(self):
        for parents, birth in (({12: 11}, 110), ({12: 11, 11: 12}, 110),
                               ({12: 11, 11: 10, 10: 1}, 121)):
            with self.subTest(parents=parents):
                self.setUp()
                self.native.parents = parents
                self.native.ids[11] = (birth, r"c:\fixture\python.exe")
                with self.assertRaises(Refused):
                    self.fence.pin(12)
                self.assertEqual(self.fence.handles, {})

    def test_duplicate_process_snapshot_is_ambiguous(self):
        self.fence.processes = lambda: [(12, 11, "x"), (12, 10, "x")]
        with self.assertRaises(Refused):
            self.fence.pin(12)

    def test_bounded_ancestry_depth(self):
        self.native.parents[12] = 50
        for pid in range(50, 68):
            self.native.ids[pid] = (100, r"c:\fixture\python.exe")
            self.native.parents[pid] = pid + 1
        self.native.parents[67] = 10
        with self.assertRaisesRegex(Refused, "depth"):
            self.fence.pin(12)
        self.assertEqual(self.fence.handles, {})

    def test_post_pin_job_hash_and_membership_races(self):
        self.fence.pin(12)
        self.scope.descriptor["id"] = "changed"
        with self.assertRaises(Refused):
            self.fence.check()
        self.scope.descriptor["id"] = "job"
        self.fence.digest = lambda path: "changed"
        with self.assertRaises(Refused):
            self.fence.check()
        self.fence.digest = lambda path: "synthetic-hash"
        self.native.excluded.add(11)
        with self.assertRaises(Refused):
            self.fence.check()

    def test_unknown_denied_and_outside_job(self):
        for case in ("unknown", "denied", "outside"):
            with self.subTest(case=case):
                self.setUp()
                self.native.ids[12] = None if case == "unknown" else (120, r"c:\fixture\python.exe")
                self.native.denied = {12} if case == "denied" else set()
                self.native.excluded = {12} if case == "outside" else set()
                with self.assertRaises(Refused):
                    self.fence.pin(12)

    def test_reused_root_and_host_and_parent_changes(self):
        self.fence.pin(12)
        for pid in (10, 11, 12):
            old = self.native.ids[pid]
            self.native.ids[pid] = (old[0] + 1, old[1])
            with self.subTest(pid=pid), self.assertRaises(Refused):
                self.fence.check()
            self.native.ids[pid] = old
        self.native.parents[12] = 10
        with self.assertRaises(Refused):
            self.fence.check()

    def test_no_host_replacement_or_dead_handle_reopen(self):
        self.fence.pin(12)
        with self.assertRaises(Refused):
            self.fence.pin(11)
        self.native.ids.pop(12)
        with self.assertRaises(Refused):
            self.fence.check()

    def test_envelope_negative_matrix(self):
        binding = self.fence.pin(12)
        valid = {**self.envelope(), "phase": "host_bound", "binding": binding}
        self.assertEqual(self.fence.envelope(valid), binding)
        for field, value in (("pid", True), ("pid", 11), ("request", "forged"),
                             ("desktop", "other"), ("profile", r"C:\other"),
                             ("binding", None), ("binding", {**binding, "job_id": "other"})):
            with self.subTest(field=field, value=value), self.assertRaises(Refused):
                self.fence.envelope({**valid, field: value})
        # Returned bindings cannot mutate parent-owned state.
        returned = self.fence.check()
        returned["host"]["pid"] = 99
        self.assertEqual(self.fence.check()["host"]["pid"], 12)

    def test_initial_forged_binding_refuses(self):
        with self.assertRaises(Refused):
            self.fence.envelope({**self.envelope(), "binding": {"job_id": "job"}}, initial=True)

    def test_pin_rechecks_ancestry_after_open(self):
        original = self.fence.processes
        calls = []
        def raced():
            calls.append(1)
            if len(calls) > 1:
                self.native.parents[12] = 30
            return original()
        self.fence.processes = raced
        with self.assertRaises(Refused):
            self.fence.pin(12)
        self.assertEqual(self.fence.handles, {})

    def test_close_is_idempotent_and_preserves_failed_handle(self):
        self.fence.pin(12)
        self.fence.close()
        self.fence.close()
        self.assertEqual(sorted(self.native.closed), [10, 11, 12])
        with self.assertRaisesRegex(Refused, "closed"):
            self.fence.pin(12)
        self.setUp()
        self.fence.pin(12)
        original = self.native.CloseHandle
        self.native.CloseHandle = lambda handle: (_ for _ in ()).throw(OSError("fake close"))
        with self.assertRaises(OSError):
            self.fence.close()
        self.assertEqual(len(self.fence.handles), 3)
        self.native.CloseHandle = original

    def test_false_close_result_retains_handle_and_fence_stays_closed(self):
        self.fence.pin(12)
        original = self.native.CloseHandle
        self.native.CloseHandle = lambda handle: 0
        with self.assertRaises(Refused):
            self.fence.close()
        self.assertEqual(len(self.fence.handles), 3)
        with self.assertRaises(Refused):
            self.fence.pin(12)
        self.native.CloseHandle = original


if __name__ == "__main__":
    unittest.main()
