"""The host adapter's contract, without native windows or filesystem fixtures."""
import ast
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

import window_profiles


class WindowProfilesTest(unittest.TestCase):
    def platform(self, constructor):
        platform = ModuleType("webview.platforms")
        edge = SimpleNamespace(CoreWebView2CreationProperties=constructor)
        platform.edgechromium = edge
        return platform, edge

    def test_profiles_are_unique_and_install_is_idempotent(self):
        class Properties:
            private_mode = True
            user_data_folder = "existing-folder"

        platform, edge = self.platform(Properties)
        with patch.dict(sys.modules, {"webview.platforms": platform}):
            window_profiles.install()
            factory = edge.CoreWebView2CreationProperties
            window_profiles.install()
            self.assertIs(factory, edge.CoreWebView2CreationProperties)
            props = [factory() for _ in range(100)]
        self.assertEqual(100, len({p.ProfileName for p in props}))
        self.assertTrue(all(p.private_mode for p in props))
        self.assertTrue(all(p.user_data_folder == "existing-folder" for p in props))
        self.assertTrue(all(isinstance(p, Properties) for p in props))

    def test_missing_profile_api_does_not_fall_back_to_shared_cookies(self):
        class UnsupportedProperties:
            __slots__ = ()

        platform, edge = self.platform(UnsupportedProperties)
        with patch.dict(sys.modules, {"webview.platforms": platform}):
            window_profiles.install()
            with self.assertRaises(AttributeError):
                edge.CoreWebView2CreationProperties()

    def test_pinned_runtime_uses_factory_before_private_cookie_clear(self):
        # Read only the installed source, without loading WinForms on this desktop.
        import importlib.util
        spec = importlib.util.find_spec("webview")
        source = Path(spec.origin).parent / "platforms" / "edgechromium.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        edge = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "EdgeChrome")
        methods = {n.name: n for n in edge.body if isinstance(n, ast.FunctionDef)}
        init = ast.unparse(methods["__init__"])
        ready = ast.unparse(methods["on_webview_ready"])
        self.assertLess(init.index("CoreWebView2CreationProperties()"),
                        init.index("EnsureCoreWebView2Async"))
        self.assertIn("props.set_IsInPrivateModeEnabled(_state['private_mode'])", init)
        self.assertIn("CookieManager.DeleteAllCookies()", ready)


if __name__ == "__main__":
    unittest.main()
