"""Source/in-memory provenance checks; no temp dirs, Win32 or live service.

Does not establish fullscreen/native acceptance. Safe to run source-only with -B.
"""
from pathlib import Path
from types import CodeType, FunctionType, ModuleType
import unittest
from unittest.mock import Mock, patch

from policy_reload import PolicyStatus, REFUSAL, compiled_manifest, runtime_manifest
import manager as manager_module
from wm_module import WMModule


MANAGER = '''
def helper():
    return lambda: "original"
class Manager:
    def __init__(self): pass
    def reading(self): return ["original"]
'''
NATIVE = '''
def gate(): raise AssertionError("native observation forbidden")
class Native:
    def __init__(self): pass
    def windows(self): raise AssertionError("native observation forbidden")
'''


def modules():
    result = {}
    for label, source in (('manager.py', MANAGER), ('win32_host.py', NATIVE)):
        module = ModuleType('fixture_' + label[:-3])
        exec(compile(source, 'imported/' + label, 'exec', dont_inherit=True), vars(module))
        result[label] = module
    return result


class ImportedCodeProvenance(unittest.TestCase):
    def setUp(self):
        self.modules = modules()

    def status(self):
        return PolicyStatus(self.modules['manager.py'], self.modules['win32_host.py'])

    def test_imported_objects_match_independently_compiled_reviewed_bytes(self):
        expected = compiled_manifest({'manager.py': MANAGER, 'win32_host.py': NATIVE})
        self.assertEqual(runtime_manifest(self.modules), expected)
        self.assertEqual(dict(self.status().manifest), expected)

    def test_production_definitions_match_full_source_offline_compilation(self):
        sources = {label: Path(__file__).with_name(label).read_bytes()
                   for label in ('manager.py', 'win32_host.py')}
        # Compare the actually imported pure Manager. For native, build only
        # function objects from whole-module compiler output, without executing
        # module/class initialization, defaults, decorators or method bodies.
        module = ModuleType('native_code_fixture')
        root = compile(sources['win32_host.py'], 'win32_host.py', 'exec', dont_inherit=True)
        for code in root.co_consts:
            if not isinstance(code, CodeType):
                continue
            if code.co_name == 'Native':
                methods = {}
                for method in code.co_consts:
                    if isinstance(method, CodeType):
                        self.assertFalse(method.co_freevars)
                        methods[method.co_name] = FunctionType(method, vars(module))
                module.Native = type('Native', (), methods)
            elif code.co_flags & 2:
                self.assertFalse(code.co_freevars)
                setattr(module, code.co_name, FunctionType(code, vars(module)))
        imported = {'manager.py': manager_module, 'win32_host.py': module}
        self.assertEqual(runtime_manifest(imported), compiled_manifest(sources))

    def test_changed_disk_candidate_cannot_be_reported_as_loaded(self):
        reviewed = {'manager.py': MANAGER.replace('original', 'changed'), 'win32_host.py': NATIVE}
        expected = compiled_manifest(reviewed)
        actual = runtime_manifest(self.modules)
        self.assertNotEqual(actual, expected)
        self.assertNotEqual(actual['manager.py:Manager.reading'], expected['manager.py:Manager.reading'])
        self.assertNotEqual(actual['manager.py:helper'], expected['manager.py:helper'])
        self.assertEqual(dict(self.status().manifest), actual)

    def test_replaced_imported_method_changes_actual_fingerprint(self):
        before = self.status().runtime_code_sha256
        module = self.modules['manager.py']
        exec(compile('def replacement(self): return ["different"]', 'elsewhere.py', 'exec'), vars(module))
        module.Manager.reading = module.replacement
        del module.replacement
        self.assertNotEqual(before, self.status().runtime_code_sha256)

    def test_snapshot_and_read_never_open_source_or_call_native(self):
        with patch('builtins.open', side_effect=AssertionError('source read forbidden')), \
             patch.object(Path, 'open', side_effect=AssertionError('source read forbidden')):
            status = self.status()
            result = status.reading()
        row = result['rows'][0]
        self.assertFalse(row['reload_supported'])
        self.assertFalse(row['rollback_supported'])
        self.assertNotIn('sha256', row, 'must not mislabel source bytes as loaded')
        row['code_manifest'].clear()
        self.assertTrue(status.reading()['rows'][0]['code_manifest'])
        self.assertIn('not full process attestation', row['provenance'])


class ReloadRefusal(unittest.TestCase):
    def setUp(self):
        self.w = WMModule(headless=True)
        self.w.owner = 'alex'
        self.w.stewards = {'jeff'}
        self.w.manager = Mock()
        self.w.latest = ({'mode': 'off'}, ['pinned-window'])
        self.w.backlog = [{'type': 'drag-start', 'hwnd': 7}]
        self.w.policy_reload = PolicyStatus(modules()['manager.py'], modules()['win32_host.py'])
        self.w._request = Mock(side_effect=AssertionError('must not queue handoff'))

    def call(self, word, sha='a' * 64, person='jeff'):
        return self.w.call({'word': word, 'args': {'kv': {'sha256': sha}},
                            'caller': {'person': person}})

    def test_reload_and_rollback_refuse_before_every_side_effect(self):
        manager_vars = dict(vars(self.w.manager))
        before = (self.w.manager, self.w.latest, self.w.backlog)
        with patch('builtins.open', side_effect=AssertionError('file access')), \
             patch.object(Path, 'open', side_effect=AssertionError('file access')), \
             patch('policy_reload.compiled_manifest', side_effect=AssertionError('staging')), \
             patch('wm_module.time.monotonic', side_effect=AssertionError('waiting')), \
             patch.object(self.w, 'lock', Mock(side_effect=AssertionError('owner-thread lock'))):
            for word in ('wm.reload', 'wm.rollback'):
                for sha in ('a' * 64, None, 'not-a-digest'):
                    with self.subTest(word=word, sha=sha):
                        self.assertEqual(self.call(word, sha), {'refused': REFUSAL})
        self.assertIs(self.w.manager, before[0])
        self.assertIs(self.w.latest, before[1])
        self.assertIs(self.w.backlog, before[2])
        self.assertEqual(vars(self.w.manager), manager_vars)
        self.assertEqual(self.w.manager.mock_calls, [])
        self.assertTrue(self.w.requests.empty())
        self.w._request.assert_not_called()
        self.assertFalse(self.w.stop.is_set())

    def test_owner_and_unrelated_principal_have_no_reload_authority(self):
        for person in ('alex', 'unrelated'):
            with self.subTest(person=person):
                self.assertIn('refused', self.call('wm.reload', person=person))
        self.assertEqual(self.w.manager.mock_calls, [])
        self.w._request.assert_not_called()

    def test_policy_read_returns_snapshot_without_native_calls_or_rehash(self):
        with patch('policy_reload.runtime_manifest', side_effect=AssertionError('rehash')):
            result = self.call('wm.policy')
        self.assertFalse(result['rows'][0]['reload_supported'])
        self.assertEqual(self.w.manager.mock_calls, [])
        self.w._request.assert_not_called()


if __name__ == '__main__':
    unittest.main()
