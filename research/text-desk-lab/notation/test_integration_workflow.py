# health: room test
"""Offline cache, source gate and diagnostic regressions; never use a live world."""

import gzip
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import deployment_preflight as preflight
import fixture_cleanup

HERE = Path(__file__).resolve().parent


def receipt(lenses=(), failures=()):
    return dict(
        ok=not failures,
        failure_details=list(failures),
        failed=[x[1] for x in failures],
        failed_checks=sorted({x[0] for x in failures}),
        lenses_ok=list(lenses),
        lenses_bad=[],
        ran=[
            "python",
            "scripts",
            "test_code",
            "test_store",
            "lenses",
            "styles",
            "help notes",
        ],
        text="fixture health",
        partial=False,
        stopped=False,
        world_at="fixture",
    )


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.gettempdir()) / ("workflow-check-" + uuid.uuid4().hex)
        self.root.mkdir()
        self.addCleanup(lambda: self.assertEqual(fixture_cleanup.remove_tree(self.root), []))
        with patch.dict(os.environ, {"LANDING_LIVE": str(self.root)}):
            spec = importlib.util.spec_from_file_location("isolated_landing", HERE / "landing.py")
            self.landing = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.landing)
        self.landing.ROOM = self.root / "room"
        self.landing.STATE = self.root / "state"
        self.landing.log = lambda *a, **kw: None
        self.landing.git = lambda *a, **kw: SimpleNamespace(stdout="commit", returncode=0)
        self.real_copy_world = self.landing.copy_world
        self.landing.copy_world = lambda *a, **kw: "revision-one"

    def test_world_identity_changes_for_same_size_same_mtime_content(self):
        import explore

        source = self.root / "source"
        source.mkdir()
        path = source / "fixture.pickle"
        desk = explore.fresh()
        desk.world.nodes[desk.world.root]["title"] = "first"
        explore.save_desk(path, desk)
        original = path.stat()
        first = self.real_copy_world("fixture", self.root / "one", source=source)
        desk.world.nodes[desk.world.root]["title"] = "other"
        explore.save_desk(path, desk)
        os.utime(path, ns=(original.st_atime_ns, original.st_mtime_ns))
        self.assertEqual(path.stat().st_size, original.st_size)
        self.assertEqual(path.stat().st_mtime_ns, original.st_mtime_ns)
        second = self.real_copy_world("fixture", self.root / "two", source=source)
        self.assertNotEqual(first, second)

    def test_same_code_and_world_reuses_complete_judgment(self):
        kept = {}
        with patch.object(self.landing, "health", return_value=receipt(["old"])) as run:
            self.landing.judged("fixture", "commit", kept)
            self.landing.judged("fixture", "commit", kept)
        self.assertEqual(run.call_count, 1)

    def test_world_change_refreshes_world_checks_without_repeating_code_suite(self):
        kept = {}
        old = receipt(["removed"], [("test_code", "existing code failure")])
        current = receipt(["new"], [("lenses", "lens new: missing selector")])
        current["partial"] = True  # selected checks alone never constitute a full judgment
        with patch.object(self.landing, "health", side_effect=[old, current]) as run:
            before = self.landing.judged("fixture", "commit", kept)
            self.landing.copy_world = lambda *a, **kw: "revision-two"
            after = self.landing.judged("fixture", "commit", kept)
        self.assertEqual(run.call_args.kwargs, {"only": sorted(self.landing.WORLD_CHECKS)})
        self.assertEqual(after["lenses_ok"], ["new"])
        self.assertEqual(after["failed"], ["existing code failure", "lens new: missing selector"])
        self.assertTrue(after["reused_code_checks"])
        self.assertFalse(after["partial"])
        self.assertEqual(before["world_version"], "revision-one")
        self.assertEqual(after["world_version"], "revision-two")

    def test_incomplete_refresh_falls_back_to_full_judgment(self):
        kept = {}
        with patch.object(self.landing, "health", return_value=receipt()):
            self.landing.judged("fixture", "commit", kept)
        self.landing.copy_world = lambda *a, **kw: "new-world"
        incomplete = receipt()
        incomplete.update(ran=["python"], partial=True)
        bad = receipt(failures=[("test_new", "new regression")])
        with patch.object(self.landing, "health", side_effect=[incomplete, bad]) as run:
            after = self.landing.judged("fixture", "commit", kept)
        self.assertEqual(run.call_count, 2)
        self.assertFalse(after["ok"])
        self.assertIn("new regression", after["failed"])

    def test_legacy_receipt_cannot_hide_world_drift(self):
        kept = {"health": {"fixture:commit": dict(ok=True, failed=[], lenses_ok=["old"])}}
        with patch.object(self.landing, "health", return_value=receipt(["new"])) as run:
            after = self.landing.judged("fixture", "commit", kept)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(after["lenses_ok"], ["new"])

    def test_selected_pass_is_never_cached_as_complete(self):
        kept = {}
        with patch.object(self.landing, "health", return_value=receipt()):
            result = self.landing.judged("fixture", "commit", kept, only=["lenses"])
        self.assertTrue(result["partial"])
        self.assertNotIn("fixture:commit", kept.get("health", {}))

    def test_comparison_uses_one_snapshot_even_if_live_world_changes(self):
        copies, live = [], ["first-world"]

        def copy(world, into, source=None):
            copies.append(source)
            return live[0]

        self.landing.copy_world = copy

        def compare(branches, world, who, why, depth, snapshot):
            with patch.object(self.landing, "health", return_value=receipt()):
                first = self.landing.judged(world, "commit", {}, snapshot=snapshot)
                live[0] = "changed-live-world"
                second = self.landing.judged(world, "commit", {}, snapshot=snapshot)
            self.assertEqual(first["world_version"], second["world_version"])
            return {"snapshot": str(snapshot["source"])}

        self.landing._land_snapshot = compare
        result = self.landing._land(["candidate"], "fixture", "tester", "fixture", 0)
        self.assertIsNone(copies[0])
        self.assertEqual(copies[1], copies[2])
        self.assertFalse(Path(result["snapshot"]).parent.exists())

    def test_cleanup_output_bounded_full_error_evidence_retained(self):
        errors = [f"fixture-{i}/.git/object: PermissionError: {'x' * 400}" for i in range(21000)]
        with (
            patch.object(fixture_cleanup, "remove_tree", return_value=errors) as remove,
            patch.object(self.landing, "log") as log,
            patch("sys.stderr", new_callable=io.StringIO) as err,
        ):
            self.landing.clean_room()
        remove.assert_called_once_with(
            self.landing.ROOM / "research/window-lab/.tmp-agora", attempts=1
        )
        data = log.call_args.kwargs
        self.assertLess(len(json.dumps(data)), 5000)
        self.assertLess(len(err.getvalue()), 5000)
        self.assertEqual(data["error_count"], len(errors))
        payload = gzip.decompress(Path(data["evidence"]).read_bytes())
        self.assertEqual(json.loads(payload), errors)
        self.assertEqual(hashlib.sha256(payload).hexdigest(), data["sha256"])
        again = fixture_cleanup.diagnostic(errors, self.landing.STATE / "cleanup-evidence")
        self.assertEqual(again["evidence"], data["evidence"])
        self.assertEqual(len(list((self.landing.STATE / "cleanup-evidence").iterdir())), 1)

    def test_interrupted_evidence_publication_never_leaves_final_name(self):
        directory = self.root / "reports"
        with patch.object(fixture_cleanup.os, "replace", side_effect=OSError("interrupted")):
            with self.assertRaisesRegex(OSError, "interrupted"):
                fixture_cleanup.diagnostic(["retained fixture"], directory)
        self.assertEqual(list(directory.glob("*.json.gz")), [])
        report = fixture_cleanup.diagnostic(["retained fixture"], directory)
        self.assertEqual(
            json.loads(gzip.decompress(Path(report["evidence"]).read_bytes())), ["retained fixture"]
        )

    def test_post_promotion_diagnostic_or_log_failure_preserves_receipt(self):
        for failing in ("diagnostic", "log"):
            with self.subTest(failing=failing):
                promoted = {"landed": ["candidate"], "head": "published"}
                self.landing._land_snapshot = lambda *a, result=promoted: result
                target = fixture_cleanup if failing == "diagnostic" else self.landing
                with (
                    patch.object(fixture_cleanup, "remove_tree", return_value=["retained"]),
                    patch.object(target, failing, side_effect=OSError("evidence disk full")),
                    patch("sys.stderr", new_callable=io.StringIO) as err,
                ):
                    result = self.landing._land(["candidate"], "fixture", "tester", "test", 0)
                self.assertIs(result, promoted)
                self.assertEqual(result["head"], "published")
                self.assertIn("disk full", result["warnings"][0]["report_error"])
                self.assertLess(len(err.getvalue()), 5000)

    def test_cleanup_report_failure_preserves_original_landing_exception(self):
        with (
            patch.object(
                self.landing, "_land_snapshot", side_effect=ValueError("original judge error")
            ),
            patch.object(fixture_cleanup, "remove_tree", return_value=["retained"]),
            patch.object(fixture_cleanup, "diagnostic", side_effect=OSError("disk full")),
            patch("sys.stderr", new_callable=io.StringIO),
        ):
            with self.assertRaisesRegex(ValueError, "original judge error"):
                self.landing._land(["candidate"], "fixture", "tester", "test", 0)

    def test_cleanup_warning_reaches_the_queued_callers_success_receipt(self):
        warning = {"snapshot": "owned-fixture", "report_error": "disk full"}
        outcome = {
            "landed": ["candidate"],
            "refused": [],
            "head": "published",
            "heads": {"candidate": "published"},
            "parked": [],
            "text": "passed",
            "texts": {},
            "warnings": [warning],
        }
        queue = {
            "waiting": [
                {
                    "id": "caller",
                    "world": "fixture",
                    "branches": ["candidate"],
                    "who": "tester",
                    "why": {},
                }
            ],
            "done": {},
        }
        with (
            patch.object(self.landing, "_queue", side_effect=lambda fn: fn(queue)),
            patch.object(self.landing, "_land", return_value=outcome),
        ):
            self.landing._serve()
        self.assertEqual(queue["done"]["caller"]["landed"], ["candidate"])
        self.assertEqual(queue["done"]["caller"]["warnings"], [warning])

    def test_cleanup_evidence_write_failure_does_not_claim_success_or_print_full_list(
        self,
    ):
        errors = ["blocked " * 100] * 5000
        with (
            patch.object(fixture_cleanup, "remove_tree", return_value=errors),
            patch.object(
                fixture_cleanup,
                "diagnostic",
                side_effect=OSError("evidence unavailable"),
            ),
            patch("sys.stderr", new_callable=io.StringIO) as err,
        ):
            with self.assertRaisesRegex(OSError, "evidence unavailable"):
                self.landing.clean_room()
        self.assertLess(len(err.getvalue()), 1000)


class SourceGateTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.gettempdir()) / ("source-gate-" + uuid.uuid4().hex)
        self.root.mkdir()
        self.addCleanup(lambda: self.assertEqual(fixture_cleanup.remove_tree(self.root), []))
        self.path = self.root / "helper.py"
        self.path.write_bytes(b"reviewed source\n")
        self.digest = hashlib.sha256(self.path.read_bytes()).hexdigest()

    def git(self, root, *args):
        if args[0] == "show":
            return subprocess.CompletedProcess(args, 0, b"reviewed source\n", b"")
        data = b"commit\ncommit\n" if len(args) == 3 and args[1] == "HEAD" else b"commit\n"
        return subprocess.CompletedProcess(args, 0, data, b"")

    def test_exact_committed_dependency_passes_without_claiming_runtime_activation(
        self,
    ):
        with patch.object(preflight, "_git", side_effect=self.git):
            result = preflight.require_sources(self.root, {"helper.py": self.digest})
        self.assertTrue(result["ok"])
        self.assertFalse(result["runtime_verified"])

    def test_uncommitted_changed_or_missing_dependencies_refuse(self):
        def missing(root, *args):
            if args[0] == "show":
                return subprocess.CompletedProcess(args, 1, b"", b"missing")
            return self.git(root, *args)

        with patch.object(preflight, "_git", side_effect=missing):
            with self.assertRaises(preflight.SourceNotIntegrated):
                preflight.require_sources(self.root, {"helper.py": self.digest})
        self.path.write_bytes(b"new uncommitted source")
        with patch.object(preflight, "_git", side_effect=self.git):
            self.assertFalse(preflight.inspect_sources(self.root, {"helper.py": self.digest})["ok"])

    def test_main_movement_and_path_escape_refuse(self):
        def drift(root, *args):
            if args == ("rev-parse", "HEAD", "refs/heads/main"):
                return subprocess.CompletedProcess(args, 0, b"new\nnew\n", b"")
            return self.git(root, *args)

        with patch.object(preflight, "_git", side_effect=drift):
            self.assertFalse(preflight.inspect_sources(self.root, {"helper.py": self.digest})["ok"])
            with self.assertRaises(preflight.SourceNotIntegrated):
                preflight.inspect_sources(self.root, {"../outside": self.digest})

    def test_runtime_revision_and_startup_bytes_are_both_required(self):
        manifest = {"revision": "commit", "files": {"helper.py": self.digest}}
        with patch.object(preflight, "_git", side_effect=self.git):
            self.assertTrue(
                preflight.require_activation(self.root, manifest, "commit", manifest["files"])[
                    "runtime_verified"
                ]
            )
            for startup in ({}, {"helper.py": "uncommitted-at-startup"}):
                with self.assertRaisesRegex(preflight.SourceNotIntegrated, "startup"):
                    preflight.require_activation(self.root, manifest, "commit", startup)
            with self.assertRaises(preflight.SourceNotIntegrated):
                preflight.require_activation(self.root, None, "commit", manifest["files"])

        def old_runtime(root, *args):
            if args == ("rev-parse", "--verify", "old^{commit}"):
                return subprocess.CompletedProcess(args, 0, b"old\n", b"")
            return self.git(root, *args)

        with patch.object(preflight, "_git", side_effect=old_runtime):
            with self.assertRaisesRegex(preflight.SourceNotIntegrated, "answering backend"):
                preflight.require_activation(self.root, manifest, "old", manifest["files"])

    def backend(self):
        spec = importlib.util.spec_from_file_location("workflow_deskd", HERE / "deskd.py")
        server = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(server)
        return server

    def handler(self, server, body):
        data = json.dumps(body).encode()
        handler = server.Handler.__new__(server.Handler)
        handler.path = "/api/deploy"
        handler.headers = {"Content-Length": str(len(data))}
        handler.rfile, handler._json = io.BytesIO(data), Mock()
        return handler

    def test_mandatory_install_route_refuses_before_opening_world(self):
        server = self.backend()
        handler = self.handler(server, {"line": "do create f1 kind=note title=No"})
        with patch.object(server, "Session") as session:
            handler._post()
        session.assert_not_called()
        self.assertFalse(handler._json.call_args.args[0]["source_verified"])
        self.assertEqual(handler._json.call_args.args[1], 409)

    def test_verified_install_route_runs_normal_world_command(self):
        import explore

        server = self.backend()
        desk = explore.fresh()
        path = self.root / "workflow-fixture.pickle"
        explore.save_desk(path, desk)
        manifest = {"revision": "commit", "files": {"helper.py": self.digest}}
        line = (
            f"look {desk.world.root}; do create {desk.world.root} "
            'kind=note title="Installed fixture"'
        )
        handler = self.handler(
            server,
            {"session": path.stem, "as": "tester", "line": line, "source_dependencies": manifest},
        )
        with (
            patch.object(preflight, "_git", side_effect=self.git),
            patch.object(server, "_SOURCE_ROOT", self.root),
            patch.object(server, "_STARTUP_SOURCES", manifest["files"]),
            patch.object(server, "CODE_VERSION", "commit"),
            patch.object(server, "SESSIONS", self.root),
            patch.object(server, "_DESKS", {}),
            patch.object(server, "_trace"),
        ):
            handler._post()
        result = handler._json.call_args.args[0]
        self.assertIsNone(result["error"], result)
        self.assertTrue(result["source_verified"])
        self.assertTrue(result["events"])
        self.assertIn(
            "Installed fixture",
            [s.get("title") for s in explore.load_desk(path).world.subjects.values()],
        )


if __name__ == "__main__":
    unittest.main()
