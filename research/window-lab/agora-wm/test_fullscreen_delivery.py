"""Production controller/solver with deterministic fake native acknowledgements.

House-only; no real windows, processes, input or world are used. This checks
behavior beyond JS line construction, but is not guarded native acceptance.
"""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

from engine import Rect, valid
from manager import Manager
from wm_module import WMModule


WORK = Rect(0, 0, 3840, 2160)


def row(key, box, **kw):
    return dict(key=key, app=key, exe='C:/fixture/' + key + '.exe', icon='',
                agora=None, state='normal', focused=False, rect=list(box),
                space='primary', managed=True, why='', owned=False,
                maximised=False, _normal=None, _preferred=list(box[2:]),
                ref=NS(hwnd=1 if key == 'claude' else 2), **kw)


class NativeFixture:
    mutating = True
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def windows(self):
        return deepcopy(self.rows)

    def find(self, ref):
        return next(r for r in self.rows if r['ref'].hwnd == ref.hwnd)

    def scale(self):
        return 1

    def needs_restore(self, ref):
        r = self.find(ref)
        return r['maximised'] or r['state'] == 'minimised'

    def restore(self, ref):
        r = self.find(ref)
        self.calls.append(('restore', r['key']))
        r['state'] = 'normal'
        r['maximised'] = False
        r['rect'] = list(r['_normal'] or [16, 16, *r['_preferred']])

    def focus(self, ref):
        self.calls.append(('focus', self.find(ref)['key']))
        for r in self.rows:
            r['focused'] = r['ref'].hwnd == ref.hwnd
        return True

    def place(self, ref, target):
        r = self.find(ref)
        self.calls.append(('place', r['key']))
        r['rect'] = target.values()

    def minimise(self, ref):
        r = self.find(ref)
        self.calls.append(('minimise', r['key']))
        r['state'] = 'minimised'


class FullscreenController(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='dk1706-fullscreen-')
        self.addCleanup(self.tmp.cleanup)
        self.clock = 1000.
        self.gates = ['full-screen foreground application', 'notification gate 2']
        self.time_patch = patch('manager.time', NS(monotonic=lambda: self.clock, time=lambda: 1))
        self.time_patch.start()
        self.addCleanup(self.time_patch.stop)

    def setup_case(self, borderless=False, new=False):
        claude = row('claude', (0, 0, 3840, 2160))
        claude.update(focused=True, maximised=not borderless,
                      _normal=None if borderless else [16, 16, 1200, 800],
                      _preferred=[3840, 2160] if borderless else [1200, 800])
        if borderless:
            claude.update(managed=False, why='frameless; no app rule', share_candidate=True)
        music = row('music', (16, 16, 950, 700))
        music.update(state='minimised', _normal=[16, 16, 950, 700])
        self.native = NativeFixture([claude] if new else [claude, music])
        self.music = music
        self.m = Manager(self.native, self.tmp.name, allow_live=True, gate_fn=lambda: self.gates)
        self.m.mode = 'live'
        self.m.lease = Mock()
        self.m.ingest(self.native.windows(), WORK)
        self.w = WMModule(headless=False)
        self.w.owner = 'owner'
        self.w.manager = self.m
        # Importing the controller's work-area dependency uses this fixed fake.
        self.modules_patch = patch.dict(sys.modules, {'win32_host': NS(work_area=lambda: WORK)})
        self.modules_patch.start()
        self.addCleanup(self.modules_patch.stop)

    def tick(self):
        self.clock += .4
        self.w.tick()

    def dispatch(self, word, target=None, **kv):
        answers = []
        def call():
            answers.append(self.w.call({'word': word, 'args': {'target': target, 'kv': kv},
                                        'caller': {'person': 'owner'}}))
        t = threading.Thread(target=call)
        t.start()
        # Wait on the actual controller queue, rather than a polling sleep.
        op, args, answer = self.w.requests.get(timeout=2)
        self.w.requests.put((op, args, answer))
        self.tick()
        t.join(2)
        self.assertFalse(t.is_alive())
        return answers[0]

    def assert_shared(self, remembered):
        for _ in range(6):
            self.tick()
        rows = self.native.windows()
        self.assertEqual([r['state'] for r in rows], ['normal', 'normal'])
        a, b = [Rect(*r['rect']) for r in rows]
        self.assertFalse(a.near(b))
        self.assertTrue(WORK.contains(a) and WORK.contains(b))
        self.assertTrue(valid(self.m.state))
        self.assertEqual(self.m.state.windows['music'].preferred, (950, 700))
        self.assertEqual((b.w, b.h), (950, 700))
        if remembered:
            self.assertEqual((a.w, a.h), (1200, 800))
        before = [r['rect'] for r in rows]
        mutations = len(self.native.calls)
        for _ in range(4):
            self.tick()
        self.assertEqual([r['rect'] for r in self.native.windows()], before)
        self.assertEqual(len(self.native.calls), mutations, 'settled layout oscillated')
        self.m.lease.release.assert_not_called()
        self.m.lease.acquire.assert_not_called()

    def test_dock_restore_maximized_and_borderless_remembered_bounds(self):
        for borderless in (False, True):
            with self.subTest(borderless=borderless):
                self.setup_case(borderless=borderless)
                result = self.dispatch('wm.restore', 'music', share='yes')
                self.assertNotIn('refused', result)
                self.assert_shared(remembered=not borderless)

    def test_new_executable_waits_then_joins_scoped_arrangement(self):
        self.setup_case(new=True)
        result = self.dispatch('wm.arrange', expect=self.music['exe'])
        self.assertNotIn('refused', result)
        self.assertEqual(self.native.calls, [], 'arming alone must not move a maximized app')
        self.music['state'] = 'normal'
        self.native.rows.append(self.music)
        self.assert_shared(remembered=True)

    def test_exclusive_unknown_pin_and_dialog_refuse_without_native_actions(self):
        self.setup_case()
        for reason in ('notification gate 3', 'notification gate 7',
                       'notification state unavailable', 'process inspection failed'):
            self.gates[:] = [reason]
            result = self.dispatch('wm.restore', 'music', share='yes')
            self.assertIn('refused', result)
            self.assertEqual(self.native.calls, [])
            self.assertIsNone(self.m.share)
        self.gates[:] = []
        self.m.pins = {'music'}
        self.assertIn('refused', self.dispatch('wm.focus', 'music', share='yes'))
        self.assertEqual(self.native.calls, [])
        self.m.pins.clear()
        self.native.rows[1]['owned'] = True
        self.m.rows = self.native.windows()
        self.assertIn('refused', self.dispatch('wm.focus', 'music', share='yes'))
        self.assertEqual(self.native.calls, [])

    def test_expiration_and_gate_change_cancel_without_moving_or_restoring(self):
        self.setup_case(new=True)
        self.dispatch('wm.arrange', expect=self.music['exe'])
        self.clock += 6
        self.native.rows.append(self.music)
        self.tick()
        self.assertIsNone(self.m.share)
        self.assertEqual(self.native.calls, [])
        # A second explicit request is a separate synthetic case, not a native retry.
        self.setup_case(new=True)
        self.dispatch('wm.arrange', expect=self.music['exe'])
        self.gates[:] = ['notification gate 3']
        self.m.gate_cache = (None, -1)
        self.native.rows.append(self.music)
        self.tick()
        self.assertEqual(self.native.calls, [])


if __name__ == '__main__':
    unittest.main()
