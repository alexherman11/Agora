"""In-memory installer contracts. No live Door, disk fixture, GUI or activation."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/kernel-lab"))
from kernel.lines import parse

spec = importlib.util.spec_from_file_location(
    "search_entry_install", ROOT / "research/kernel-lab/apps/smart-search/install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class MemoryDoor:
    """Records authoring requests; not evidence of host execution or authority."""
    def __init__(self):
        self.things, self.calls = {}, []

    def rows(self, kind, **filters):
        return [dict(row, id=tid) for tid, row in self.things.items()
                if row["kind"] == kind and all(row.get(k) == v for k, v in filters.items())]

    def say(self, line):
        self.calls.append(line)
        step = parse(line)
        if step.word == "make":
            tid = "sx" + str(len(self.things) + 1)
            self.things[tid] = dict(step.kv)
            return {"made": [tid]}
        if step.word == "look":
            return {}
        if step.word == "set":
            self.things[step.target].update(step.kv)
            return {}
        raise AssertionError("Unexpected effect: " + line)


class SearchEntry(unittest.TestCase):
    def test_one_named_entry_and_window_without_activation(self):
        door = MemoryDoor()
        ids = installer.install(door)
        button = installer.entry(door)
        self.assertEqual(len(door.things), 4)
        self.assertEqual(door.things[button]["label"], "Search")
        self.assertEqual(door.things[button]["does"], "window.open smart-search")
        self.assertEqual(door.things[ids["widget"]]["title"], "Search")
        self.assertEqual(door.things[ids["lens"]]["title"], "Search")
        self.assertEqual(door.things[ids["lens"]]["text"].strip(),
                         "root : smart-search\n  on evidence do window.open thing $id")
        code = door.things[ids["component"]]["code"]
        self.assertEqual(code, (installer.HERE / "lexical.js").read_text(encoding="utf-8"))
        self.assertNotIn("model.", code)
        self.assertNotIn("model.", installer.REQUIRED_GRANTS)
        self.assertTrue(all(parse(line).word == "make" for line in door.calls))

    def test_repeat_install_keeps_one_entry_and_existing_draft_objects(self):
        door = MemoryDoor()
        installer.install(door)
        installer.entry(door)
        before = dict(door.things)
        door.calls.clear()
        installer.install(door)
        installer.entry(door)
        self.assertEqual(door.things, before)
        self.assertEqual(door.calls, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
