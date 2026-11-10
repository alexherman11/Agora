"""Contract checks for the read-only dashboard; no live desk or models used."""
import json
import time
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import preview


def snapshot():
    return dict(house={}, plans={}, usage={}, names={}, queued="Unknown",
                stamp="test observation", beat="unknown", stale=True)


class PreviewTests(unittest.TestCase):
    def render(self, data, name="observatory"):
        desk = preview.build(data)
        node, words = preview.scene.scene_for(desk, name)
        return json.dumps(node, ensure_ascii=False), words

    def test_missing_is_unknown_and_stale(self):
        painted, words = self.render(snapshot())
        self.assertIn("STALE", words)
        self.assertIn("Unknown", words)
        self.assertIn("No context observation available", painted)
        self.assertIn("No quota observations available", painted)

    def test_zero_is_measured_without_private_transcript(self):
        data = snapshot()
        data["house"] = dict(residents={}, workers={}, said="SECRET TRANSCRIPT")
        data["queued"] = "0"
        painted, words = self.render(data)
        self.assertIn("workers 0/0 active", painted)
        self.assertNotIn("SECRET TRANSCRIPT", painted + words)

    def test_expired_quota_not_still_reported_exact(self):
        data = snapshot()
        data["plans"] = dict(windows=dict(test=dict(provider="sample", label="window", percent=93,
                                                     resets=time.time()-10, asof=time.time()-30)))
        painted, _ = self.render(data)
        self.assertIn("unknown %", painted)
        self.assertNotIn("93 %", painted)

    def test_real_status_and_unknown_model_are_separate(self):
        data = snapshot()
        data["house"] = dict(residents=dict(jeff=dict(actor="jeff", doing="stopped")), workers={})
        painted, _ = self.render(data)
        self.assertIn("stopped", painted)
        self.assertIn("Current configured model: unknown", painted)
        self.assertIn("recovery needed: unknown", painted)

    def test_contrasting_example_uses_same_source(self):
        painted, words = self.render(snapshot(), "studio")
        for evidence in ("illustrative", "unassigned 20", "No observations", "1 unknown", "Workshop table: 0"):
            self.assertIn(evidence, painted + words)

    def test_worker_selection_change_keeps_existing_person_identity(self):
        data = snapshot()
        data["crew_order"] = ["workerA", "workerB"]
        data["names"] = dict(workerA="First task", workerB="Second task")
        data["house"] = dict(residents={}, workers=dict(workerA=dict(doing="working"), workerB=dict(doing="stopped")))
        def identity():
            desk = preview.build(data)
            return {desk.world.subjects[n["subject"]]["title"]: item
                    for item, n in desk.world.nodes.items()
                    if set(desk.world.subjects.get(n.get("subject"), {}).get("tags", [])) & {"watch-resident", "watch-worker", "watch-inactive"}}
        before = identity()
        data["house"]["workers"]["workerA"]["doing"] = "stopped"
        data["house"]["workers"]["workerB"]["doing"] = "working"
        self.assertEqual(before, identity())

    def test_terminal_rows_bind_real_context_and_square_geometry(self):
        data = snapshot()
        data["house"] = dict(residents=dict(jeff=dict(actor="jeff", doing="working", model="gpt-6-astra", reasoning="low")),
                             workers=dict(job=dict(doing="working", builder="codex-builder-2")))
        data["names"] = dict(job="A long active task " * 12)
        data["usage"] = dict(rows=[dict(kind="agent", actor="jeff", corner="jeff", tokens=0, window=100),
                                   dict(kind="agent", actor="worker-job", corner="job", tokens=100, window=100)])
        painted, _ = self.render(data)
        self.assertNotIn("Chart unavailable", painted)
        self.assertIn("0%", painted)
        self.assertIn("100%", painted)
        self.assertIn("Codex 2", painted)
        self.assertIn("astra/low", painted)
        def visit(node):
            if isinstance(node, dict):
                for value in node.values():
                    yield from visit(value)
            elif isinstance(node, list):
                for value in node:
                    yield from visit(value)
            elif isinstance(node, str) and node.startswith("<svg"):
                yield node
        for svg in visit(json.loads(painted)):
            rects = [e for e in ET.fromstring(svg).iter() if e.tag.endswith("rect")]
            self.assertTrue(all(e.get("rx") == "0" and e.get("ry") == "0" for e in rects))

    def test_worker_unknown_context_never_borrows_account_quota(self):
        data = snapshot()
        data["house"] = dict(residents={}, workers=dict(job=dict(doing="working")))
        data["names"] = dict(job="Unknown context task")
        data["plans"] = dict(windows=dict(sample=dict(provider="Sample", percent=100, resets=time.time()+60, asof=time.time())))
        painted, _ = self.render(data)
        self.assertIn("Unknown context task: unknown % of capacity", painted)
        self.assertIn("100 %", painted)

    def test_runtime_whitelist_drops_private_transcripts(self):
        runtime = preview.Runtime()
        runtime.names_at = time.time()
        house = dict(beat=time.time(), residents=dict(jeff=dict(actor="jeff", said="private", model="gpt-6-astra")), workers={})
        usage = dict(rows=[dict(kind="agent", tokens=0, said="private", text="private")], said="private")
        with patch.object(preview, "load", side_effect=[house,dict(windows={})]), patch.object(preview.witnessed, "read", return_value=usage):
            data = runtime.read()
        self.assertNotIn("private", json.dumps(data))
        self.assertEqual(data["usage"]["rows"][0]["tokens"], 0)


if __name__ == "__main__":
    unittest.main()
