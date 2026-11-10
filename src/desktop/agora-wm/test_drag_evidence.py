"""The hidden check cannot pass on simulated movement or missing evidence."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch
from drag_evidence import assess


class DragEvidence(unittest.TestCase):
    def trace(self):
        return dict(input=['down', 'move', 'up'], events=['drag-start', 'location', 'drag-end'],
                    alive=True, visible=True, rings=2, landing=[40, 40, 850, 650], drop=[40, 40, 850, 650],
                    neighbour=[[x, 70, 850, 650] for x in range(900, 39, -40)],
                    input_lag_ms=[12] * 24, tick_ms=[4] * 100)

    def test_complete_trace(self):
        self.assertEqual(assess(self.trace())['input_lag_max_ms'], 12)

    def test_missing_outcomes_fail(self):
        for change in [
            dict(input=['down', 'up']), dict(events=['location']), dict(alive=False), dict(visible=False),
            dict(rings=0), dict(drop=[80, 40, 850, 650]), dict(neighbour=[[900, 70, 850, 650]] * 30),
            dict(neighbour=[[900, 70, 850, 650], [40, 70, 850, 650], [41, 70, 850, 650], [42, 70, 850, 650]]),
            dict(input_lag_ms=[150] * 24), dict(input_lag_ms=[]), dict(tick_ms=[50] * 100),
        ]:
            with self.subTest(change=change), self.assertRaises(AssertionError):
                assess(deepcopy(self.trace()) | change)

    def test_game_refuses_before_importing_or_starting_sandbox(self):
        import hidden_real_drag
        gate = Mock(spec=['assert_clear'])
        gate.assert_clear.side_effect = RuntimeError('Gaming gate: fixture')
        sandbox = Mock()
        with patch.dict(sys.modules, {'gaming_gate': gate, 'sandbox_window': sandbox}), \
                self.assertRaisesRegex(RuntimeError, 'Gaming gate'):
            hidden_real_drag.run(Path('unused'))
        self.assertEqual(sandbox.mock_calls, [])

    def test_direct_fixture_on_default_desktop_refuses_before_browser(self):
        import hidden_real_drag
        sandbox = Mock()
        sandbox.desk_name.return_value = 'Default'
        browser = Mock()
        with patch.dict(sys.modules, {'sandbox_window': sandbox, 'webview': browser}), \
                self.assertRaisesRegex(RuntimeError, 'non-input hidden desktop'):
            hidden_real_drag.fixture(Path('unused'), 'fixture')
        self.assertEqual(browser.mock_calls, [])


if __name__ == '__main__':
    unittest.main()
