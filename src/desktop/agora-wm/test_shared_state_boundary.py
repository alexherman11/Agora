"""House-only native API seam checks. Never loads Win32 or creates a desktop.

Extract the shipped method rather than import the native DLL bindings. These
checks establish the requested API and guard ordering, not app cooperation.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


class SharedStateBoundary(unittest.TestCase):
    def setUp(self):
        source=ast.parse(Path(__file__).with_name('win32_host.py').read_text(encoding='utf-8'))
        native=next(n for n in source.body if isinstance(n,ast.ClassDef) and n.name=='Native')
        method=next(n for n in native.body if isinstance(n,ast.FunctionDef) and n.name=='restore_shared')
        module=ast.Module(body=[method],type_ignores=[])
        self.api=SimpleNamespace(PostMessageW=Mock(return_value=1))
        scope={'u':self.api,'C':SimpleNamespace(get_last_error=lambda:5)}
        exec(compile(ast.fix_missing_locations(module),'<shipped restore_shared>','exec'),scope)
        self.restore=scope['restore_shared']
        self.owner=SimpleNamespace(check=Mock())
        self.ref=SimpleNamespace(hwnd=71)

    def test_checks_identity_then_posts_only_system_restore(self):
        order=[]
        self.owner.check.side_effect=lambda ref:order.append('check')
        self.api.PostMessageW.side_effect=lambda *args:order.append('post') or 1
        self.restore(self.owner,self.ref)
        self.assertEqual(order,['check','post'])
        self.owner.check.assert_called_once_with(self.ref)
        self.api.PostMessageW.assert_called_once_with(71,0x112,0xF120,0)

    def test_denied_native_boundary_has_no_post_or_alternate_operation(self):
        self.owner.check.side_effect=PermissionError('identity/allowlist refused')
        with self.assertRaises(PermissionError):self.restore(self.owner,self.ref)
        self.api.PostMessageW.assert_not_called()

    def test_post_failure_is_reported_without_retry_or_input_fallback(self):
        self.api.PostMessageW.return_value=0
        with self.assertRaises(OSError):self.restore(self.owner,self.ref)
        self.api.PostMessageW.assert_called_once_with(71,0x112,0xF120,0)


class GlassBoundary(unittest.TestCase):
    def test_shipped_glass_is_click_through_noactivate_tool_window(self):
        source=ast.parse(Path(__file__).with_name('ghost.py').read_text(encoding='utf-8'))
        method=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='_make')
        api=SimpleNamespace(CreateWindowExW=Mock(return_value=17),SetLayeredWindowAttributes=Mock())
        scope={'u':api}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),
                     '<shipped glass boundary>','exec'),scope)
        scope['_make'](70,selected=True)
        args=api.CreateWindowExW.call_args.args
        self.assertEqual(args[0],0x80000|0x20|0x80|0x08000000)
        self.assertEqual(args[3],0x80000000|6)
        api.SetLayeredWindowAttributes.assert_called_once_with(17,0,70,2)
        api.CreateWindowExW.return_value=0
        with self.assertRaises(OSError):scope['_make'](40)


if __name__=='__main__':
    unittest.main()
