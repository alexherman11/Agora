"""Live-adapter fixtures; never call a live API or save a world."""

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import explore
import scene

LAB = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("crew_test_source", LAB / "sources/crew.py")
crew = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crew)
sys.path.insert(0, str(LAB.parents[2] / "research/module-lab"))
import integration_bundle  # noqa: E402


def snapshot():
    return dict(
        house=dict(
            beat=999,
            residents=dict(alex=dict(actor="alex", doing="resting")),
            workers=dict(job=dict(builder="codex-builder-1", doing="working")),
        ),
        usage=dict(
            at=998,
            rows=[
                dict(kind="agent", corner="alex", tokens=0, window=100),
                dict(kind="agent", corner="job", tokens=50, window=100, model="gpt-6-astra"),
            ],
        ),
        plans=dict(
            windows=dict(
                codex=dict(provider="codex", label="5 hours", percent=72, resets=2000, asof=990)
            )
        ),
        names=dict(alex="Alex", job="Measured task"),
        queued=1,
        now=1000,
    )


class CrewTests(unittest.TestCase):
    def test_legacy_builder_names_remain_readable(self):
        for name, expected in (("builder-1", "Worker 1"), ("builder-2", "Worker 2"),
                               ("codex-builder-1", "Codex 1"), (None, "Worker"),
                               ("builder-", "Worker")):
            with self.subTest(name=name):
                data = snapshot()
                data["house"]["workers"]["job"]["builder"] = name
                self.assertEqual(crew.compose(**data)["workers"][0]["worker_name"], expected)

    def test_workers_dock_uses_existing_hud_navigation(self):
        entries = integration_bundle.manifest()["dock"]
        workers = next(e for e in entries if e["title"] == "Workers")
        self.assertEqual(workers["opens"], "@crew@")
        self.assertNotIn("window", workers)
        modules = next(e for e in entries if e["title"] == "Modules")
        self.assertEqual(modules["window"], "composition-workshop")

    def test_context_and_quota_are_different_measurements(self):
        rows = crew.compose(**snapshot())
        self.assertEqual(rows["residents"][0]["percent"], "0%")
        self.assertEqual(rows["workers"][0]["percent"], "50%")
        self.assertEqual(rows["quota"][0]["percent"], "72%")
        self.assertEqual(rows["workers"][0]["model"], "~astra")

    def test_missing_worker_context_never_borrows_quota(self):
        data = snapshot()
        data["usage"]["rows"].pop()
        row = crew.compose(**data)["workers"][0]
        self.assertEqual((row["status"], row["percent"]), ("unknown", "unknown"))

    def test_bad_group_and_unknown_query_are_explicit(self):
        data = snapshot()
        data["house"]["workers"] = {"broken": None}
        rows = crew.compose(**data)
        self.assertEqual(rows["workers"][0]["status"], "unknown")
        self.assertIn("workers ?/?", rows["summary"][0]["counts"])
        with self.assertRaises(crew.Refusal):
            crew.rows(None, "unsupported", "frontier")

    def test_stale_keeps_value_but_not_current_activity_or_picture_label(self):
        data = snapshot()
        data["house"]["beat"] = 960
        row = crew.compose(**data)["workers"][0]
        self.assertEqual((row["status"], row["state"], row["percent"]), ("stale", "stale", "50%"))
        self.assertIn("stale", row["picture"])
        self.assertNotIn("ready", row["picture"])

    def test_expired_or_future_quota_unknown(self):
        data = snapshot()
        data["plans"]["windows"]["codex"]["resets"] = 1000
        self.assertEqual(crew.compose(**data)["quota"][0]["percent"], "unknown")
        data["plans"]["windows"]["codex"].update(resets=2000, asof=3000)
        self.assertEqual(crew.compose(**data)["quota"][0]["percent"], "unknown")

    def test_absent_producer_is_unknown_not_zero_or_stale_measurement(self):
        data = snapshot()
        data["usage"] = None
        row = crew.compose(**data)["workers"][0]
        self.assertEqual((row["status"], row["percent"]), ("unknown", "unknown"))
        rows = crew.compose({}, None, {}, {}, "unknown", 1000)
        self.assertIn("residents ?", rows["summary"][0]["counts"])
        self.assertEqual(rows["residents"][0]["status"], "unknown")

    def test_invalid_capacity_and_quota_not_clamped_to_real_measurement(self):
        data = snapshot()
        data["usage"]["rows"][1]["window"] = 0
        data["plans"]["windows"]["codex"]["percent"] = 150
        rows = crew.compose(**data)
        self.assertEqual(rows["workers"][0]["percent"], "unknown")
        self.assertEqual(rows["quota"][0]["status"], "error")

    def test_private_fields_not_projected_and_inputs_unchanged(self):
        data = snapshot()
        data["house"]["said"] = "SECRET"
        data["house"]["workers"]["job"]["last_reply"] = "SECRET"
        before = copy.deepcopy(data)
        self.assertNotIn("SECRET", json.dumps(crew.compose(**data)))
        self.assertEqual(data, before)

    def test_waiting_is_active_not_hidden_as_stopped(self):
        data = snapshot()
        data["house"]["workers"]["job"]["doing"] = "waiting"
        rows = crew.compose(**data)
        self.assertEqual(rows["workers"][0]["state"], "waiting")
        self.assertEqual(rows["inactive"], [])

    def test_same_count_change_and_insert_keep_row_identity(self):
        data = snapshot()
        before = crew.compose(**data)["workers"][0]
        data["usage"]["rows"][1]["tokens"] = 75
        data["house"]["workers"]["earlier"] = dict(builder="builder-2", doing="working")
        after = next(r for r in crew.compose(**data)["workers"] if r["key"] == "job")
        self.assertEqual(before["rid"], after["rid"])
        self.assertNotEqual(before["picture"], after["picture"])

    def test_world_bundle_compiles_without_live_mutation(self):
        desk = explore.fresh()
        desk._session = "crew-integration-memory"
        refs, _ = integration_bundle.install_memory(desk)
        data = snapshot()
        projected = crew.compose(**data)
        with patch.dict(
            scene.SOURCE_FILES,
            {"crew": dict(arg="needed", open=False, rows=lambda d, a, s: projected[a])},
        ):
            for title in (
                "crew-observatory",
                "composition-workshop",
                "composition-catalog",
                "composition-trace",
            ):
                node, words = scene.scene_for(desk, title)
                self.assertNotIn("!!", words)
                self.assertIn("kids", node)
            node, words = scene.scene_for(desk, "crew-observatory")
            self.assertIn("Measured task", words)
            self.assertIn("50%", words)
            self.assertEqual(len(refs), 10)
        with self.assertRaisesRegex(ValueError, "collision"):
            integration_bundle.install_memory(desk)
        desk._session = "frontier"
        with self.assertRaisesRegex(ValueError, "fixture"):
            integration_bundle.install_memory(desk)

    def test_compiled_worker_fold_identity_survives_live_data_changes(self):
        desk = explore.fresh()
        desk._session = "crew-integration-memory"
        integration_bundle.install_memory(desk)
        data = snapshot()

        def visit(node):
            yield node
            for child in node.get("kids", []):
                yield from visit(child)

        def render():
            node, words = scene.scene_for(desk, "crew-observatory")
            match = [n for n in visit(node) if n.get("part") == "worker" and n.get("item") == "job"]
            self.assertEqual(len(match), 1)
            return match[0]["key"], words

        with patch.dict(
            scene.SOURCE_FILES,
            {"crew": dict(arg="needed", open=False, rows=lambda d, a, s: crew.compose(**data)[a])},
        ):
            key, words = render()
            self.assertIn("50%", words)
            data["usage"]["rows"][1]["tokens"] = 75
            changed_key, words = render()
            self.assertEqual(key, changed_key)
            self.assertIn("75%", words)
            data["house"]["workers"]["earlier"] = dict(builder="builder-2", doing="working")
            inserted_key, _ = render()
            self.assertEqual(key, inserted_key)


if __name__ == "__main__":
    unittest.main()
