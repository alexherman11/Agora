"""Actual offline event wiring with fake native args, not engine enforcement."""
from types import SimpleNamespace as NS
import unittest

from admission_policy import configure, install


class Event:
    def __init__(self):
        self.handlers = []

    def __iadd__(self, handler):
        self.handlers.append(handler)
        return self

    def fire(self, args):
        for handler in self.handlers:
            handler(None, args)


class Tests(unittest.TestCase):
    def setUp(self):
        names = ("NavigationStarting FrameNavigationStarting WebResourceRequested "
                 "NewWindowRequested PermissionRequested DownloadStarting "
                 "LaunchingExternalUriScheme").split()
        self.core = NS(**{name: Event() for name in names})
        self.filters, self.refusals = [], []
        self.core.Environment = NS(CreateWebResourceResponse=lambda *args: args)
        self.core.AddWebResourceRequestedFilter = lambda *args: self.filters.append(args)
        install(self.core, self.refusals.append, "DENY", "ALL_CONTEXT", "ALL_SOURCE")

    def test_top_frame_redirect_external_local_and_script_navigation_refused(self):
        for event in ("NavigationStarting", "FrameNavigationStarting"):
            for uri in ("https://example.invalid/", "http://127.0.0.1/",
                        "file:///C:/private", "javascript:alert(1)", "data:text/html,x",
                        "mailto:x@example.invalid", "agora://do", "about:blank#spoof"):
                with self.subTest(event=event, uri=uri):
                    args = NS(Uri=uri, Cancel=False, IsRedirected=True)
                    getattr(self.core, event).fire(args)
                    self.assertTrue(args.Cancel)

    def test_fixture_blank_and_srcdoc_allowed(self):
        for uri in ("about:blank", "about:srcdoc"):
            args = NS(Uri=uri, Cancel=False)
            self.core.NavigationStarting.fire(args)
            self.assertFalse(args.Cancel)

    def test_all_resource_sources_including_worker_are_denied(self):
        self.assertEqual(self.filters, [("*", "ALL_CONTEXT", "ALL_SOURCE")])
        for source in ("top", "frame", "dedicated_worker", "shared_worker", "service_worker"):
            args = NS(Response=None, source=source)
            self.core.WebResourceRequested.fire(args)
            self.assertEqual(args.Response[1], 403)

    def test_popups_permissions_downloads_and_external_schemes(self):
        for event, field, expected in (
                ("NewWindowRequested", "Handled", True),
                ("PermissionRequested", "State", "DENY"),
                ("DownloadStarting", "Cancel", True),
                ("LaunchingExternalUriScheme", "Cancel", True)):
            with self.subTest(event=event):
                args = NS(Handled=False, State="DEFAULT", Cancel=False)
                getattr(self.core, event).fire(args)
                self.assertEqual(getattr(args, field), expected)

    def test_missing_native_policy_api_fails_installation(self):
        del self.core.LaunchingExternalUriScheme
        with self.assertRaises(AttributeError):
            install(self.core, self.refusals.append, "DENY", "ALL", "ALL")

    def test_host_objects_and_privileged_features_disabled_in_both_phases(self):
        for positive in (True, False):
            settings = NS()
            configure(settings, positive_control=positive)
            self.assertIs(settings.IsWebMessageEnabled, positive)
            for field in ("AreHostObjectsAllowed", "AreDevToolsEnabled",
                          "IsGeneralAutofillEnabled", "IsPasswordAutosaveEnabled",
                          "AreDefaultContextMenusEnabled", "AreBrowserAcceleratorKeysEnabled",
                          "AreDefaultScriptDialogsEnabled"):
                self.assertIs(getattr(settings, field), False, field)


if __name__ == "__main__":
    unittest.main()
