"""House-only focused checks; pure fixture objects, no Win32 mutation or service.

Run separately from generic review suites. These tests do not admit native/UI
validation and must not be used as owner acceptance.
"""
from copy import deepcopy
from pathlib import Path
import queue
import tempfile
import threading
import time
from types import ModuleType, SimpleNamespace as NS
import unittest
from unittest.mock import Mock

from engine import Rect, State, Window
from policy_reload import PolicyReload, POLICY, FIXED, MAX_SOURCE_BYTES, digest
from wm_module import WMModule


MANAGER = b'''
class Manager:
    def __init__(self): pass
    def switch(self, mode): raise AssertionError("must never release")
    def reading(self): return ["before"]
'''
NATIVE = b'''
class Native:
    def __init__(self): pass
    def windows(self): return self.rows
    def release(self): raise AssertionError("must never release")
'''


class PolicyHandoff(unittest.TestCase):
    def setUp(self):
        # Independent House owns the test temp lifecycle. Worker does not run it.
        self.tmp = tempfile.TemporaryDirectory(prefix='dk1706-policy-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'wm'
        self.root.mkdir()
        for name in POLICY + FIXED:
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(MANAGER if name == 'manager.py' else NATIVE if name == 'win32_host.py' else b'# fixed\n')
        self.mm, self.nm = ModuleType('fixture_manager'), ModuleType('fixture_native')
        exec(MANAGER, vars(self.mm))
        exec(NATIVE, vars(self.nm))
        self.gates = []
        self.nm.gate = lambda: list(self.gates)
        self.nm.reload_context = lambda: {'foreground': 'fixture', 'input_desktop': 'Default'}
        self.nm.work_area = lambda: Rect(0, 0, 2000, 1200)
        m = self.mm.Manager()
        m.native = self.nm.Native()
        m.native.rows = [{'key': 'a', 'rect': [16, 16, 800, 600], 'state': 'normal',
                          '_normal': [16, 16, 800, 600], '_preferred': [800, 600],
                          'ref': NS(record=lambda: {'hwnd': 7, 'created': 11})}]
        m.native.mutating = True
        m.state = State(work=self.nm.work_area(),
                        windows={'a': Window('a', preferred=(800, 600),
                                             rect=Rect(16, 16, 800, 600), pinned=True)})
        m.rows = deepcopy(m.native.rows)
        m.actual = deepcopy(m.rows)
        m.refs = {'a': m.rows[0]['ref']}
        m.pins = {'a'}
        m.adopted = {'a'}
        m.borderless = {'b'}
        m.pending = {}
        m.gesture = m.preview = m.share = None
        m.boot = m.gated = False
        m.gate_fn = self.nm.gate
        m.lease = Mock()
        m.mode = 'live'
        self.owner = NS(manager=m, held=False, stop=threading.Event(),
                        latest=None, backlog=[], requests=queue.Queue())
        self.r = PolicyReload(self.owner, self.mm, self.nm, self.root)
        self.r.bind()

    def candidate(self, old=b'["before"]', new=b'["after"]'):
        p = self.root / 'manager.py'
        p.write_bytes(p.read_bytes().replace(old, new))
        return digest(self.r.read())

    def apply(self, sha=None, **kw):
        return self.r.apply(sha or self.candidate(), time.monotonic() + 2, **kw)

    def test_same_objects_bounds_refs_claims_and_rollback(self):
        m = self.owner.manager
        objects = {k: id(v) for k, v in vars(m).items()}
        before = self.r.loaded
        self.apply()
        self.assertEqual(m.reading(), ['after'])
        self.assertIs(self.owner.manager, m)
        self.assertEqual(objects, {k: id(v) for k, v in vars(m).items()})
        self.assertEqual(m.state.windows['a'].preferred, (800, 600))
        self.assertEqual(m.rows[0]['_normal'], [16, 16, 800, 600])
        self.assertEqual(m.pins, {'a'})
        self.assertEqual(m.adopted, {'a'})
        self.apply(before, rollback=True)
        self.assertEqual(m.reading(), ['before'])
        self.assertIsNone(self.r.previous)
        self.assertEqual(objects, {k: id(v) for k, v in vars(m).items()})
        self.assertEqual({c[0] for c in m.lease.mock_calls}, {'heartbeat'})

    def test_wrong_hash_syntax_and_abi_keep_old_code(self):
        self.candidate()
        for name, data in (
                ('manager.py', b'class Manager:\n def reading(:\n'),
                ('manager.py', MANAGER.replace(b'def __init__(self): pass', b'def __init__(self): self.extra=1')),
                ('manager.py', MANAGER.replace(b'def reading(self)', b'@print("must not run")\n    def reading(self)')),
                ('engine.py', b'# incompatible\n')):
            with self.subTest(name=name, data=data):
                original = (self.root / name).read_bytes()
                (self.root / name).write_bytes(data)
                with self.assertRaises((SyntaxError, PermissionError)):
                    self.apply(digest(self.r.read()))
                self.assertIs(type(self.owner.manager), self.mm.Manager)
                self.assertEqual(self.owner.manager.reading(), ['before'])
                (self.root / name).write_bytes(original)
        with self.assertRaises(PermissionError):
            self.apply('0' * 64)

    def test_busy_gaming_unknown_and_expired_never_stage(self):
        m = self.owner.manager
        for field, value in [('pending', {'a': {}}), ('gesture', object()),
                             ('share', {'until': 1}), ('boot', True), ('gated', True)]:
            old = getattr(m, field)
            setattr(m, field, value)
            with self.subTest(field=field), self.assertRaises(PermissionError):
                self.apply()
            setattr(m, field, old)
        self.gates.append('notification gate 3')
        with self.assertRaises(PermissionError):
            self.apply()
        self.gates.clear()
        self.r.context = Mock(side_effect=PermissionError('unknown foreground'))
        with self.assertRaises(PermissionError):
            self.apply()
        with self.assertRaises(TimeoutError):
            self.r.apply('0' * 64, time.monotonic() - 1)
        self.assertIs(type(m), self.mm.Manager)
        m.lease.release.assert_not_called()
        m.lease.acquire.assert_not_called()
        m.lease.save.assert_not_called()

    def test_foreground_change_and_failed_commit_restore_previous_classes(self):
        sha = self.candidate()
        original_context = self.r.context
        self.r.context = Mock(side_effect=[{'front': 1}, {'front': 2}])
        with self.assertRaises(PermissionError):
            self.apply(sha)
        self.assertIs(type(self.owner.manager), self.mm.Manager)
        self.r.context = original_context
        observe = self.r.observe
        count = [0]
        def changed(deadline):
            count[0] += 1
            if count[0] == 3:
                raise PermissionError('lost admission after class swap')
            return observe(deadline)
        self.r.observe = changed
        with self.assertRaises(PermissionError):
            self.apply(sha)
        self.assertIs(type(self.owner.manager), self.mm.Manager)
        self.assertIs(type(self.owner.manager.native), self.nm.Native)
        self.assertIsNone(self.r.previous)

    def test_changed_identity_normal_bounds_workarea_and_owner_thread_refuse(self):
        for field, value in [('rect', [17, 16, 800, 600]), ('_normal', [16, 16, 900, 600])]:
            old = self.owner.manager.native.rows[0][field]
            self.owner.manager.native.rows[0][field] = value
            with self.subTest(field=field), self.assertRaises(PermissionError):
                self.apply()
            self.owner.manager.native.rows[0][field] = old
        self.owner.manager.native.rows[0]['ref'] = NS(record=lambda: {'hwnd': 7, 'created': 99})
        with self.assertRaises(PermissionError):
            self.apply()
        self.owner.manager.native.rows = deepcopy(self.owner.manager.rows)
        self.r.work_area = lambda: Rect(0, 0, 1900, 1200)
        with self.assertRaises(PermissionError):
            self.apply()
        self.r.thread = -1
        with self.assertRaises(PermissionError):
            self.apply()

    def test_queued_intent_and_lost_watchdog_refuse_without_release(self):
        self.owner.latest = ({'mode': 'off'}, [])
        with self.assertRaises(PermissionError):
            self.apply()
        self.owner.latest = None
        self.owner.requests.put(object())
        with self.assertRaises(PermissionError):
            self.apply()
        self.owner.requests.get_nowait()
        self.owner.manager.lease.heartbeat.side_effect = RuntimeError('watchdog unavailable')
        with self.assertRaises(RuntimeError):
            self.apply()
        self.assertIs(type(self.owner.manager), self.mm.Manager)
        self.owner.manager.lease.release.assert_not_called()

    def test_unacknowledged_policy_geometry_refuses_even_without_pending_marker(self):
        self.owner.manager.state.windows['a'].rect = Rect(30, 40, 900, 700)
        with self.assertRaises(PermissionError):
            self.apply()
        self.assertIs(type(self.owner.manager), self.mm.Manager)
        self.owner.manager.lease.release.assert_not_called()

    def test_oversized_source_refuses_without_swapping_or_releasing(self):
        (self.root / 'manager.py').write_bytes(b'#' * (MAX_SOURCE_BYTES + 1))
        with self.assertRaisesRegex(PermissionError, 'bounded staging size'):
            self.r.apply('a' * 64, time.monotonic() + 2)
        self.assertIs(type(self.owner.manager), self.mm.Manager)
        self.assertIsNone(self.r.previous)
        self.owner.manager.lease.release.assert_not_called()
        self.owner.manager.lease.save.assert_not_called()

    def test_source_change_after_staging_keeps_old_generation(self):
        sha = self.candidate()
        stage = self.r.stage
        def changed(sources):
            result = stage(sources)
            path = self.root / 'manager.py'
            path.write_bytes(path.read_bytes() + b'\n# changed after review\n')
            return result
        self.r.stage = changed
        with self.assertRaisesRegex(PermissionError, 'source changed during staging'):
            self.apply(sha)
        self.assertIs(type(self.owner.manager), self.mm.Manager)
        self.assertIs(type(self.owner.manager.native), self.nm.Native)
        self.assertEqual(self.owner.manager.reading(), ['before'])
        self.assertIsNone(self.r.previous)
        self.owner.manager.lease.release.assert_not_called()


class ControllerAdmission(unittest.TestCase):
    def test_only_steward_dispatches_policy_with_deadline_and_pinned_hash(self):
        w = WMModule(headless=True)
        w.owner = 'alex'
        w.stewards = {'jeff'}
        w.policy_reload = object()
        w._request = Mock(return_value={'text': 'queued'})
        msg = {'word': 'wm.reload', 'args': {'kv': {'sha256': 'a' * 64}},
               'caller': {'person': 'alex'}}
        self.assertIn('refused', w.call(msg))
        w._request.assert_not_called()
        msg['caller']['person'] = 'jeff'
        w.call(msg)
        op, sha, rollback, deadline = w._request.call_args.args
        self.assertEqual((op, sha, rollback), ('policy', 'a' * 64, False))
        self.assertGreater(deadline, time.monotonic())

    def test_policy_success_and_refusal_end_tick_without_ingest(self):
        for error in (None, PermissionError('game')):
            w = WMModule(headless=True)
            w.manager = Mock(lease=None)
            w.latest = ({'mode':'off'}, [])
            w.policy_reload = Mock()
            if error:
                w.policy_reload.apply.side_effect = error
            else:
                w.policy_reload.apply.return_value = {'text': 'loaded'}
            answer = queue.Queue()
            deadline = time.monotonic() + 2
            w.requests.put(('policy', ('a' * 64, False, deadline), answer))
            w.tick()
            self.assertEqual('refused' in answer.get_nowait(), error is not None)
            w.manager.ingest.assert_not_called()
            w.manager.switch.assert_not_called()
            self.assertIsNotNone(w.latest, 'handoff consumed unrelated pending settings')
            w.policy_reload.apply.assert_called_once_with('a' * 64, deadline, rollback=False)

    def test_thread_binding_failure_returns_before_settings_or_shutdown(self):
        w = WMModule(headless=True)
        w.manager = Mock()
        w.latest = ({'mode': 'off'}, [])
        w.policy_reload = Mock()
        w.policy_reload.bind.side_effect = PermissionError('wrong owner thread')
        w.tick()
        w.manager.switch.assert_not_called()
        w.manager.ingest.assert_not_called()
        w.policy_reload.apply.assert_not_called()
        self.assertIsNotNone(w.latest)

    def test_policy_collects_unread_native_events_for_refusal(self):
        w = WMModule(headless=True)
        w.manager = Mock()
        w.policy_reload = Mock()
        event = {'type': 'drag-start', 'hwnd': 7}
        feed = Mock()
        feed.drain.return_value = [event]
        def apply(*args, **kw):
            self.assertEqual(w.backlog, [event])
            raise PermissionError('queued native event')
        w.policy_reload.apply.side_effect = apply
        answer = queue.Queue()
        w.requests.put(('policy', ('a' * 64, False, time.monotonic() + 2), answer))
        w.tick(feed)
        self.assertIn('refused', answer.get_nowait())
        w.manager.ingest.assert_not_called()
        w.manager.switch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
