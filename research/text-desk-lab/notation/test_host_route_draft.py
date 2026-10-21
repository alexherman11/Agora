# health: room test
"""Fake-only tests. No imports of house/world or Windows process APIs."""
import os
from pathlib import Path
import sqlite3
import sys
import unittest
import uuid

from host_route_draft import Binding, DisabledRoute, Guards, Issuer, ReferenceModel, Refused


class Crash(BaseException):
    pass


class DraftTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.jeff, self.worker = object(), object()
        self.binding = Binding("card-test", "worker-test", "generation-1")
        self.when = 100
        self.guard = Guards(True, True, True)
        self.calls = []
        self.rows = [{"pid": 123, "parent_pid": 1, "created": "fake-time",
                      "executable": "fake-agora-python", "role": "home-base"}]
        self.model = self.make(self.db)

    def make(self, db):
        return ReferenceModel(
            db, issuer_attestor=lambda source: Issuer("jeff", "parent-session-1")
            if source is self.jeff else None,
            worker_attestor=lambda source: self.binding if source is self.worker else None,
            guards=lambda: self.guard, inventory=self.inventory, clock=lambda: self.when)

    def inventory(self):
        self.calls.append("fake inventory")
        return self.rows

    def grant(self):
        return self.model.issue(self.jeff, self.binding, expires=200)

    def request(self, cap, rid="request-1", **kwargs):
        return self.model.request(self.worker, cap, rid, **kwargs)

    def test_deployment_stub_always_disabled(self):
        self.assertEqual(DisabledRoute().request(as_="jeff")["status"], "refused")
        self.assertEqual(self.calls, [])

    def test_claimed_jeff_cannot_issue(self):
        for forged in ("jeff", {"as": "jeff"}, {"by": "jeff", "via": "prop"},
                       Issuer("jeff", "parent-session-1"), self.worker):
            with self.assertRaises(Refused):
                self.model.issue(forged, self.binding, expires=200)
        self.assertEqual(self.db.execute("SELECT count(*) FROM grants").fetchone()[0], 0)

    def test_copied_world_grant_is_not_capability(self):
        copied_world = {"as": "jeff", "card": "card-test", "generation": "generation-1",
                        "operation": "agora.processes.read", "extra_tools": "approved"}
        with self.assertRaises(Refused):
            self.model.issue(copied_world, self.binding, expires=200)
        self.assertEqual(self.request(copied_world)["status"], "refused")
        self.assertEqual(self.request(object())["status"], "refused")
        self.assertEqual(self.calls, [])

    def test_ungranted_destructive_operation_never_runs(self):
        cap = self.grant()
        for command in ("taskkill /PID 123 /F", "agora.processes.stop", "shell"):
            self.assertEqual(self.request(cap, operation=command)["status"], "refused")
        self.assertEqual(self.calls, [])

    def test_no_caller_supplied_wql_script_pid_or_cwd(self):
        cap = self.grant()
        for arguments in ({"pid": 123}, {"wql": "SELECT *"}, {"cwd": "."},
                          {"script": "fake stop"}, {"as": "jeff"}):
            self.assertEqual(self.request(cap, arguments=arguments)["status"], "refused")
        self.assertEqual(self.calls, [])

    def test_wrong_worker_channel_refused(self):
        cap = self.grant()
        self.assertEqual(self.model.request({"as": "worker-test"}, cap, "r")["status"], "refused")
        self.assertEqual(self.calls, [])

    def test_binding_card_worker_generation_each_checked(self):
        cap = self.grant()
        for binding in (Binding("other", "worker-test", "generation-1"),
                        Binding("card-test", "other", "generation-1"),
                        Binding("card-test", "worker-test", "generation-2")):
            self.binding = binding
            self.assertEqual(self.request(cap)["status"], "refused")
        self.assertEqual(self.calls, [])

    def test_revocation(self):
        cap = self.grant()
        self.model.revoke(self.jeff, cap)
        self.assertEqual(self.request(cap)["status"], "refused")
        self.assertEqual(self.calls, [])

    def test_forged_revocation_refused(self):
        cap = self.grant()
        with self.assertRaises(Refused):
            self.model.revoke({"as": "jeff"}, cap)
        self.assertEqual(self.request(cap)["status"], "succeeded")

    def test_expiration_and_lifetime_bound(self):
        with self.assertRaises(Refused):
            self.model.issue(self.jeff, self.binding, expires=401)
        cap = self.grant()
        self.when = 200
        self.assertEqual(self.request(cap)["status"], "refused")
        self.assertEqual(self.calls, [])

    def test_all_guards_fail_closed_without_wake(self):
        cap = self.grant()
        for guard in (Guards(False, True, True), Guards(True, False, True),
                      Guards(True, True, False), Guards(None, True, True),
                      Guards(True, None, True), Guards(True, True, None),
                      Guards(1, True, True), None):
            self.guard = guard
            self.assertEqual(self.request(cap)["status"], "refused")
        self.assertEqual(self.calls, [])

    def test_guard_failure_refuses(self):
        self.model.guards = lambda: (_ for _ in ()).throw(RuntimeError("fake"))
        self.assertEqual(self.request(self.grant())["status"], "refused")
        self.assertEqual(self.calls, [])

    def test_success_receipt_and_single_use(self):
        cap = self.grant()
        receipt = self.request(cap)
        self.assertEqual(receipt["processes"], self.rows)
        self.assertEqual(self.request(cap), receipt)
        self.assertEqual(self.request(cap, "second")["status"], "refused")
        self.assertEqual(len(self.calls), 1)
        actions = [r[0] for r in self.db.execute("SELECT action FROM audit ORDER BY sequence")]
        self.assertEqual(actions, ["issued", "admitted", "terminal", "refused"])

    def test_access_denial_is_not_empty_success(self):
        self.model.inventory = lambda: (_ for _ in ()).throw(PermissionError("private details"))
        receipt = self.request(self.grant())
        self.assertEqual(receipt["status"], "denied")
        self.assertNotIn("processes", receipt)
        self.assertNotIn("private details", str(receipt))

    def test_unrelated_output_is_not_disclosed(self):
        self.rows[0]["command_line"] = "private fake unrelated command"
        receipt = self.request(self.grant())
        self.assertEqual(receipt["status"], "unknown")
        self.assertNotIn("private fake", str(receipt))

    def test_identity_collision_refuses(self):
        cap = self.grant()
        self.request(cap)
        other = self.grant()
        self.assertEqual(self.request(other)["status"], "refused")
        self.assertEqual(len(self.calls), 1)

    def test_second_connection_cannot_overlap_card(self):
        # Shared in-memory database, independently constructed policy model.
        name = "file:host-draft-" + uuid.uuid4().hex + "?mode=memory&cache=shared"
        first_db = sqlite3.connect(name, uri=True)
        second_db = sqlite3.connect(name, uri=True)
        try:
            first, second = self.make(first_db), self.make(second_db)
            first_cap = first.issue(self.jeff, self.binding, expires=200)
            second_cap = second.issue(self.jeff, self.binding, expires=200)
            overlapping = []

            def during_inventory():
                overlapping.append(second.request(self.worker, second_cap, "fallback"))
                return self.inventory()

            first.inventory = during_inventory
            self.assertEqual(first.request(self.worker, first_cap, "first")["status"], "succeeded")
            self.assertEqual(overlapping[0]["status"], "refused")
            # Once terminal, an explicitly new grant can run the read-only op.
            self.assertEqual(second.request(self.worker, second_cap, "later")["status"], "succeeded")
            self.assertEqual(len(self.calls), 2)
        finally:
            first_db.close()
            second_db.close()

    def test_crash_keeps_card_lease_and_never_replays(self):
        cap = self.grant()
        self.model.inventory = lambda: (_ for _ in ()).throw(Crash())
        with self.assertRaises(Crash):
            self.request(cap)
        self.model.inventory = self.inventory
        self.assertEqual(self.request(cap)["status"], "unknown")
        self.assertEqual(self.request(self.grant(), "fallback")["status"], "refused")
        self.assertEqual(self.calls, [])

    def test_persistent_journal_and_restart_invalidates_channels(self):
        # Plain mkdir inherits the workspace ACL; no tempfile owner-only ACL.
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "window-lab"))
        import agora_tmp
        directory = Path(agora_tmp.configure()) / ("host-draft-" + uuid.uuid4().hex)
        os.makedirs(directory)
        path = directory / "journal.sqlite"
        db = sqlite3.connect(path)
        model = self.make(db)
        cap = model.issue(self.jeff, self.binding, expires=200)
        model.inventory = lambda: (_ for _ in ()).throw(Crash())
        try:
            with self.assertRaises(Crash):
                model.request(self.worker, cap, "persistent")
        finally:
            db.close()
        db = sqlite3.connect(path)
        try:
            restarted = self.make(db)
            self.assertEqual(restarted.request(self.worker, cap, "persistent")["status"], "refused")
            new_cap = restarted.issue(self.jeff, self.binding, expires=200)
            self.assertEqual(restarted.request(self.worker, new_cap, "fallback")["status"], "refused")
            self.assertEqual(db.execute("SELECT state FROM requests").fetchone()[0], "running")
            self.assertEqual(self.calls, [])
        finally:
            db.close()
            path.unlink()
            directory.rmdir()


if __name__ == "__main__":
    unittest.main()
