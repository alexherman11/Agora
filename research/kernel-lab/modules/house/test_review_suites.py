"""Review the card's own suites and retain evidence on every failure. No desktop or live world."""
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
from kernel import scratch
import builders as B
import review_suites as S
from test_builders import manager as manager_fixture, state


class Suites(unittest.TestCase):
    def setUp(self):
        self.scratch = scratch.TemporaryDirectory(prefix='house-suites-')
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.manager = manager_fixture.__wrapped__(self.root)
        self.manager.repo.mkdir()
        (self.manager.repo / 'suite.py').write_text('print("card suite executed")\n', encoding='utf-8')
        self.s = state(self.manager)
        self.manager.session = lambda _: self.manager.fixture_door
        self.manager.commit_worker = lambda *_: None
        self.manager.git = lambda cwd, *args: 'a' if args[0] == 'rev-parse' else ''
        (self.manager.repo / 'BUILD-RESULT.md').write_text('fixture', encoding='utf-8')
        self.patch = patch.object(B, 'CHECKS', [])
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.python = patch.object(B.T, 'PY', Path(sys.executable))
        self.python.start()
        self.addCleanup(self.python.stop)

    def select(self, **changes):
        spec = dict(name='Card suite', runner='python', paths=['suite.py'], timeout=20)
        spec.update(changes)
        self.manager.fixture_door.task['test_suites'] = json.dumps([spec])
        return spec

    def test_real_card_script_runs_and_receipt_is_named_and_hashed(self):
        self.select()
        self.manager.review(self.s)
        self.assertEqual(self.s['phase'], 'reviewed')
        receipt, = self.s['checks']
        self.assertEqual((receipt['name'], receipt['status'], receipt['returncode']), ('Card suite', 'passed', 0))
        self.assertIn('card suite executed', Path(receipt['evidence']).read_text())
        self.assertEqual(len(receipt['sha256']), 64)
        self.assertIn('Card suite: passed', S.summary(self.s['checks']))

    def test_failure_does_not_hide_the_second_suite(self):
        spec = self.select()
        (self.manager.repo / 'bad.py').write_text('raise SystemExit(7)\n')
        bad = dict(spec, name='Broken', paths=['bad.py'])
        self.manager.fixture_door.task['test_suites'] = [bad, spec]
        with self.assertRaisesRegex(RuntimeError, 'independent check failed: Broken'):
            self.manager.review(self.s)
        self.assertEqual([c['returncode'] for c in self.s['checks']], [7, 0])
        self.assertEqual([c['status'] for c in self.s['checks']], ['failed', 'passed'])

    def test_timeouts_and_spawn_errors_leave_receipts(self):
        self.select()
        for error in (subprocess.TimeoutExpired('fixture', 20), OSError('runner missing')):
            with self.subTest(error=error), patch.object(B.subprocess, 'run', side_effect=error):
                with self.assertRaisesRegex(RuntimeError, 'independent check failed'):
                    self.manager.review(self.s)
                receipt, = self.s['checks']
                self.assertEqual(receipt['status'], 'failed')
                self.assertIn(type(error).__name__, receipt['error'])
                self.assertTrue(Path(receipt['evidence']).is_file())

    def test_gaming_blocks_desktop_before_any_process(self):
        self.select(desktop=True)
        with patch.dict(sys.modules, {'gaming_gate': unittest.mock.Mock(spec=['assert_clear'])}):
            import gaming_gate
            gaming_gate.assert_clear.side_effect = RuntimeError('Gaming gate: fixture game')
            with patch.object(B.subprocess, 'run') as run:
                with self.assertRaisesRegex(RuntimeError, 'independent check failed'):
                    self.manager.review(self.s)
                run.assert_not_called()
        self.assertEqual(self.s['checks'][0]['status'], 'blocked')

    def test_changed_suite_invalidates_review_and_prevents_publication(self):
        self.select()
        self.manager.review(self.s)
        self.assertTrue(self.manager.suites_current(self.s))
        self.select(name='New requirement')
        self.assertFalse(self.manager.suites_current(self.s))
        with self.assertRaisesRegex(RuntimeError, 'suites changed after review'):
            self.manager.publish(self.s)

    def test_land_rechecks_after_card_suite_changes(self):
        self.select()
        self.manager.review(self.s)
        self.select(name='New requirement')
        self.s['land_from'] = 'reviewed'
        calls = []
        with patch.object(self.manager, 'publish', side_effect=lambda _: calls.append('publish')), \
                patch.object(self.manager, 'activate', side_effect=lambda _: calls.append('activate')):
            self.manager.land_all(self.s)
        self.assertEqual(self.s['checks'][0]['name'], 'New requirement')
        self.assertEqual(calls, ['publish', 'activate'])

    def test_change_during_check_is_not_reusable(self):
        self.select()
        def changed(*args, **kwargs):
            self.select(name='Changed mid-run')
            return subprocess.CompletedProcess(args[0], 0)
        with patch.object(B.subprocess, 'run', side_effect=changed):
            with self.assertRaisesRegex(RuntimeError, 'suites changed during review'):
                self.manager.review(self.s)

    def test_repeated_review_keeps_distinct_evidence(self):
        self.select()
        self.manager.review(self.s)
        first = dict(self.s['checks'][0])
        self.manager.review(self.s)
        second = self.s['checks'][0]
        self.assertNotEqual(first['artifacts'], second['artifacts'])
        self.assertNotEqual(first['evidence'], second['evidence'])
        self.assertTrue(Path(first['evidence']).exists())

    def test_legacy_review_with_new_suite_must_run_it(self):
        self.assertTrue(self.manager.suites_current(self.s))
        self.select()
        self.assertFalse(self.manager.suites_current(self.s))

    def test_invalid_json_and_nonlists_refuse(self):
        for value in ('not json', '{}', 'false', False, {'paths': ['suite.py']}):
            with self.subTest(value=value):
                self.manager.fixture_door.task['test_suites'] = value
                with self.assertRaises(ValueError):
                    self.manager.review_plan(self.s)

    def test_owner_and_landing_receipt_report_each_suite(self):
        from test_workers import Agent
        agent = Agent()
        self.manager.h.agents = {'dk99': agent}
        self.select()
        self.manager.review(self.s)
        self.s.update(phase='landed', land_attempt='fixture-landing', landed_commit='a',
                      detail='source landed', land_step='activation')
        self.manager.outcome(self.s)
        self.assertIn('Card suite: passed', agent.woken[-1][0])
        self.assertEqual(self.s['land_receipt']['checks'], self.s['checks'])

    def test_invalid_suite_never_becomes_shell_or_outside_path(self):
        bad_specs = [
            dict(runner='powershell'), dict(paths=['../suite.py']), dict(paths=['C:/suite.py']),
            dict(paths=['--override-ini']), dict(paths=['suite.py::test']), dict(paths=['missing.py']),
            dict(paths=['suite.py'], timeout=0), dict(desktop='yes'), dict(command='anything'),
            dict(paths=['suite.py', 'suite.py']), dict(paths=['.']),
        ]
        for changes in bad_specs:
            with self.subTest(changes=changes):
                self.select(**changes)
                with self.assertRaises(ValueError):
                    self.manager.review_plan(self.s)

    def test_python_pytest_and_node_are_distinct_argv(self):
        for runner, prefix in [('python', ['pin', '-B']), ('pytest', ['pin', '-B', '-m', 'pytest', '-q']),
                               ('node', ['node'])]:
            self.select(runner=runner)
            suite, = self.manager.review_plan(self.s)
            self.assertEqual(S.command(suite, 'pin'), prefix + ['suite.py'])


if __name__ == '__main__':
    unittest.main()
