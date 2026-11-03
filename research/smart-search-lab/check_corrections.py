"""New correction contracts only; in-memory mocks, no pytest/temp/live telemetry."""
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/kernel-lab/modules/model"))
import model as M
import smart_search as S
import search_resources as R


def fixture():
    return dict(id="ss1", rev=1, kind="note", title="Larch",
                text="Extracts a foreground silhouette entirely on device.")


class CorrectionContracts(unittest.TestCase):
    def test_idle_threshold_and_invalid_telemetry(self):
        for value in [None, True, -1, "30000", 0, 29999]:
            with self.subTest(value=value), patch.object(R, "idle_milliseconds", return_value=value):
                with self.assertRaises(ValueError):
                    R.require_idle()
        with patch.object(R, "idle_milliseconds", side_effect=OSError("unavailable")):
            with self.assertRaises(ValueError):
                R.require_idle()
        with patch.object(R, "idle_milliseconds", return_value=30000):
            R.require_idle()

    def test_admission_at_generation_under_lock_fail_closed_no_post(self):
        def deny():
            self.assertTrue(M.inference_lock.locked())
            raise ValueError("input active")
        with patch.object(M, "local") as transport:
            with self.assertRaises(ValueError):
                M.generate("synthetic", "synthetic", admission=deny)
            transport.assert_not_called()
        self.assertFalse(M.inference_lock.locked())

    def test_busy_lock_never_admits_or_queues(self):
        M.inference_lock.acquire()
        try:
            with patch.object(M, "local") as transport, patch.object(R, "require_idle") as admission:
                with self.assertRaises(ValueError):
                    M.generate("synthetic", "synthetic", admission=admission)
                admission.assert_not_called()
                transport.assert_not_called()
        finally:
            M.inference_lock.release()

    def test_search_admission_orders_gaming_memory_then_fresh_idle(self):
        events = []
        gate = types.ModuleType("gaming_gate")
        gate.reasons = lambda: events.append("gaming") or []
        with patch.dict(sys.modules, gaming_gate=gate), \
                patch.object(M, "local", side_effect=lambda *a, **k: events.append("metadata") or {}), \
                patch.object(R, "reason", side_effect=lambda *a: events.append("memory")), \
                patch.object(R, "require_idle", side_effect=lambda: events.append("idle")):
            M.search_admission("synthetic")
        self.assertEqual(events, ["gaming", "metadata", "memory", "idle"])

    def test_unavailable_idle_inside_search_admission_blocks(self):
        gate = types.ModuleType("gaming_gate")
        gate.reasons = lambda: []
        with patch.dict(sys.modules, gaming_gate=gate), patch.object(M, "local", return_value={}), \
                patch.object(R, "reason", return_value=None), \
                patch.object(R, "require_idle", side_effect=OSError("unavailable")):
            with self.assertRaises(ValueError):
                M.search_admission("synthetic")

    def test_semantic_requires_confirmation_before_budget_or_inference(self):
        for kv in [{}, {"confirmed": "yes", "filters": '["local"]'}]:
            message = dict(use="synthetic", caller=dict(person="ss2"),
                           args=dict(kv=dict(q="cut the subject free", mode="semantic", **kv)))
            with patch.object(M, "read", return_value=[fixture()]), \
                    patch.object(M, "generate") as generation, patch.object(M, "limit") as budget:
                out = M.search(message)["rows"][0]
                self.assertEqual(out["hits"], [])
                generation.assert_not_called()
                budget.assert_not_called()

    def test_synthetic_semantic_path_has_admission_callback_and_no_alias_gate(self):
        events = []
        r = fixture()
        raw = json.dumps(dict(intent="tools", constraints=[],
                              hits=[dict(id="ss1", evidence="foreground silhouette")]))
        def generation(*args, **kwargs):
            self.assertEqual(kwargs["tokens"], 256)
            kwargs["admission"]()
            return raw
        def read(use, line):
            return [] if "model-settings" in line else [r]
        message = dict(use="synthetic", caller=dict(person="ss2"),
                       args=dict(kv=dict(q="isolate the person", mode="semantic",
                                         confirmed="yes", filters="[]")))
        with patch.object(M, "read", side_effect=read), patch.object(M, "limit") as budget, \
                patch.object(M, "search_admission", side_effect=lambda m: events.append(m)), \
                patch.object(M, "generate", side_effect=generation):
            result = M.search(message)["rows"][0]
        self.assertFalse(S.lexical("isolate the person", S.descriptors([r])))
        self.assertEqual([h["id"] for h in result["hits"]], ["ss1"])
        self.assertEqual(result["capabilities"], "unverified")
        self.assertEqual(len(events), 1)
        budget.assert_called_once()

    def test_missing_or_omitted_natural_language_constraints_cannot_certify(self):
        r = fixture()
        records = S.descriptors([r])
        semantic = ("tools", set(), [dict(records[0], evidence="silhouette", match="semantic")])
        self.assertEqual(S.merge("an arbitrary private requirement", records, [r], semantic)["hits"], [])
        result = S.merge("arbitrary wording", records, [r], semantic, confirmed={"local"})
        self.assertEqual(result["hits"], [])
        self.assertIn("unverified", result["constraint_status"])

    def test_unresolved_revoked_or_self_asserted_evidence_never_certifies(self):
        for evidence in ["manual", "ss999", {"id": "ss2", "rev": 1}, "https://example.invalid"]:
            r = dict(fixture(), search_evidence=evidence, search_processing="local",
                     search_network="none", search_decision="yes",
                     downloaded_at="2026-10-29T18:00:00+00:00")
            for filter_ in S.CONSTRAINTS:
                self.assertFalse(S.eligible(r, {filter_}, None))

    def test_suggested_filter_requires_confirmation_and_no_results(self):
        r = fixture()
        records = S.descriptors([r])
        semantic = ("tools", {"offline"}, [dict(records[0], evidence="silhouette", match="semantic")])
        result = S.merge("Larch", records, [r], semantic, confirmed=set())
        self.assertEqual(result["hits"], [])
        self.assertIn("Confirm suggested", result["constraint_status"])

    def test_explicit_filters_reject_unknown_and_wrong_shapes(self):
        for value in ['"offline"', '{}', '["unsupported"]', '[true]', 'null']:
            with self.assertRaises(ValueError):
                S.confirmed_filters(dict(confirmed="yes", filters=value))
        self.assertIsNone(S.confirmed_filters({}))
        self.assertEqual(S.confirmed_filters(dict(confirmed="yes", filters="[]")), set())


if __name__ == "__main__":
    unittest.main(verbosity=2)
