"""Check the staged five-anchor contract and browser source load wiring."""
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
SHELL = HERE.parents[1] / "text-desk-lab" / "notation" / "desk-shell"
sys.path.insert(0, str(HERE.parent / "slim-dock"))
import partition_hook


class Integration(unittest.TestCase):
    def test_exact_handoff_applied_once(self):
        source = (SHELL / "partition-ui.js").read_text(encoding="utf-8")
        before = source
        for old, new in reversed(partition_hook.HUNKS):
            self.assertEqual(before.count(new), 1, new)
            before = before.replace(new, old, 1)
        self.assertEqual(partition_hook.patched(before), source)

    def test_dependency_loads_before_both_adapters(self):
        html = (SHELL / "lens.html").read_text(encoding="utf-8")
        for module in ("partition-ui.js", "lens.js"):
            self.assertLess(html.index('src="carry-targets.js"'),
                            html.index('src="' + module + '"'))
        lens = (SHELL / "lens.js").read_text(encoding="utf-8")
        self.assertIn("CarryTargets.snapshot(paint, el._n.part)", lens)
        self.assertIn("CarryTargets.submit(send, l, c.n.fence)", lens)
        self.assertIn("if (partitions?.carry(el, e)) return;", lens)


if __name__ == "__main__":
    unittest.main()
