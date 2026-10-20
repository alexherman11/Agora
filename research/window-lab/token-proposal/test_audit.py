"""Synthetic counter validation only. No runtime/model requests."""
import io
import json
import unittest
from types import SimpleNamespace
from audit import audit


class Receipt:
    def __init__(self, name, records):
        self.parent = SimpleNamespace(name=name)
        self.records = records

    def __lt__(self, other):
        return self.parent.name < other.parent.name

    def open(self, **kwargs):
        return io.StringIO("".join(json.dumps(r) + "\n" for r in self.records))


def event(at, data):
    return dict(at=at, kind="event", data=data)


def result(at, count):
    return event(at, dict(type="result", session_id="same",
        modelUsage={"model": dict(cacheReadInputTokens=count)}))


class AuditTests(unittest.TestCase):
    def test_cumulative_deltas_and_duplicate_messages(self):
        message = event(12, dict(type="assistant", message=dict(
            id="message", usage=dict(cache_read_input_tokens=20),
            content=[dict(type="text", text="PRIVATE_SENTINEL")])))
        root = SimpleNamespace(glob=lambda _: [
            Receipt("worker-a", [result(5, 100), result(11, 130), message]),
            Receipt("builder-1", [result(11, 130), result(13, 150), message])])
        out = audit(root, 10, 20)
        group = out["groups"]["workers"]
        self.assertEqual(group["result_counter_deltas"]["cacheReadInputTokens"], 50)
        self.assertEqual(group["unique_assistant_messages"], 1)
        self.assertEqual(group["message_usage_totals"]["cache_read_input_tokens"], 20)
        self.assertNotIn("PRIVATE_SENTINEL", json.dumps(out))

    def test_missing_baseline_counter_reset_and_quota(self):
        limit = event(12, dict(type="rate_limit_event", rate_limit_info=dict(
            unifiedWindows={"five_hour": dict(utilization=1, resetsAt=100)})))
        root = SimpleNamespace(glob=lambda _: [Receipt("f5189",
            [result(11, 100), result(12, 90), result(13, 95), limit])])
        out = audit(root, 10, 20)
        self.assertEqual(out["result_session_models_missing_baseline"]["JEFF"], 1)
        self.assertEqual(out["result_counter_decreases_skipped"], 1)
        self.assertEqual(out["groups"]["JEFF"]["result_counter_deltas"]["cacheReadInputTokens"], 5)
        window = next(iter(out["quota_windows"].values()))
        self.assertIsNotNone(window["first_full"])


if __name__ == "__main__":
    unittest.main()
