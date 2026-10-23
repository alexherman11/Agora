"""Run frozen regressions against actual integrated imports, without generating a candidate."""
import contextlib
import importlib
import io
import json
import sys
from pathlib import Path
from types import ModuleType
import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
OUTPUT = HERE
LAB = HERE.parent / "text-desk-lab" / "notation"
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "window-lab"))
import agora_tmp
agora_tmp.configure()
import task_flow
import house
import rooms
import replay

legacy = ModuleType("baseline_task_flow")
legacy.__file__ = str(HERE / "integration-base-task_flow.py.txt")
exec(compile(Path(legacy.__file__).read_text(), legacy.__file__, "exec"), legacy.__dict__)
actual = {"task_flow": task_flow, "house": house, "rooms": rooms}
replay.task_flow = legacy
replay.modules = lambda: actual
import test_candidate
test_candidate.legacy = legacy


class PolicyOffIntegration(unittest.TestCase):
    def test_full_news_state_matches_prepared_baseline(self):
        # Compare real news(), not just the notice dictionaries; no providers.
        baseline = {"task_flow": legacy}
        with patch.dict(sys.modules, baseline):
            for name in ("rooms", "house"):
                module = ModuleType("baseline_" + name)
                module.__file__ = str(LAB / (name + ".py"))
                exec(compile((HERE / ("integration-base-" + name + ".py.txt")).read_text(),
                             module.__file__, "exec"), module.__dict__)
                baseline[name] = module
        baseline["house"].task_flow = legacy
        for policy_state in ("absent", "off"):
            fixture = test_candidate.CandidateTests()
            fixture.setUp()
            if policy_state == "absent":
                del fixture.w.subjects["test-policy"]
            else:
                fixture.w.subjects["test-policy"]["props"]["enabled"] = "off"
            start = len(fixture.w.events)
            for state in ("working", "waiting", "ready", "failed", "landed", "done"):
                fixture.change("pike", "commission=" + state)
            fixture.change("juniper", "lead=sable")
            fixture.run_line("alex", "read " + fixture.card)
            fixture.run_line("alex", 'do comment ' + fixture.card + ' line="Fixture question" mark=ask')
            fixture.run_line("pike", "read " + fixture.card)
            fixture.run_line("pike", 'do comment ' + fixture.card +
                             ' line="Fixture direct request" mark=ask to=sable')
            for actor in ("juniper", "sable", "pike"):
                for resting in (False, True):
                    states = []
                    for implementation, modules in ((baseline["house"], baseline), (house, actual)):
                        state = {"cursor": start, "pending": {"fate": "unknown", "delivered": True}}
                        r = SimpleNamespace(rid=fixture.r.corner[actor], state=state, save=lambda: None)
                        h = object.__new__(implementation.House)
                        with patch.dict(sys.modules, modules):
                            urgent = h.news(fixture.w, r, actor, resting=resting)
                        states.append((urgent, deepcopy(state)))
                    self.assertEqual(states[0], states[1], (policy_state, actor, resting))


def main():
    log = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(test_candidate.CandidateTests)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(PolicyOffIntegration))
    for name in ("test_timed_rests", "test_house_restart"):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module(name)))
    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    (OUTPUT / "integration-tests.log").write_text(log.getvalue(), encoding="utf-8")
    replay_log = io.StringIO()
    with contextlib.redirect_stdout(replay_log):
        replay.main()
    (OUTPUT / "integration-replay.log").write_text(replay_log.getvalue(), encoding="utf-8")
    rows, events = replay.replay()
    report = {"tests": result.testsRun, "failures": len(result.failures),
              "errors": len(result.errors), "success": result.wasSuccessful(),
              "captured_records": len(rows),
              "before": sum(len(e["before"]) for e in events),
              "after": sum(len(e["after"]) for e in events),
              "modules": {k: v.__file__ for k, v in actual.items()}}
    (OUTPUT / "integration-results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if not result.wasSuccessful():
        print(log.getvalue()[-14000:])
        raise SystemExit(1)


if __name__ == "__main__":
    main()
