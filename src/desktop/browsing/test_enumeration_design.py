"""Offline candidate enumeration regressions, not a native run.

Original characterization preserved byte-for-byte in
ENUMERATION-DESIGN-BASELINE-a9231.txt. All Windows APIs here are synthetic.
"""
import ctypes
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from native_run_verify import EnumerationIncomplete, Native, enumeration_error


def proposed_verdict(ok, callback_failed=False):
    # A zero BOOL, including error 0 or 18, cannot certify an empty desktop.
    return "observed" if ok and not callback_failed else "unknown"


class EnumerationDesign(unittest.TestCase):
    def current(self, ok, error, visited=0, owner_fails=False, callback_raises=False):
        closed = []
        def enumerate_windows(handle, callback, _):
            for _ in range(visited):
                callback(100, 0)
            ctypes.set_last_error(error)
            return ok
        def owner(hwnd, pid):
            if callback_raises:
                raise OSError("private text must not be retained")
            if owner_fails:
                return 0
            pid._obj.value = 42
            return 1
        native = object.__new__(Native)  # never initialize any Windows library
        native.enum_type = lambda callback: callback
        native.u = SimpleNamespace(
            OpenDesktopW=lambda *args: 1,
            EnumDesktopWindows=enumerate_windows,
            GetWindowThreadProcessId=owner,
            IsWindowVisible=lambda hwnd: True,
            CloseDesktop=lambda handle: (closed.append(handle), ctypes.set_last_error(999)),
        )
        # Only thread-local ctypes error bookkeeping; no Windows library calls.
        incoming_error = ctypes.get_last_error()
        try:
            return native.desktop_window_owners("fake-only")
        finally:
            self.assertEqual(closed, [1])
            ctypes.set_last_error(incoming_error)

    def test_retained_error_shape_is_unknown_not_empty(self):
        with self.assertRaises(OSError):
            self.current(False, 18)
        self.assertEqual(proposed_verdict(False), "unknown")

    def test_partial_failure_cannot_return_partial_list(self):
        with self.assertRaises(EnumerationIncomplete) as caught:
            self.current(False, 18, visited=1)
        self.assertEqual(caught.exception.enumeration,
                         {"api": "EnumDesktopWindows", "complete": False,
                          "error": 18, "visited": 1, "callback_failed": False})
        self.assertEqual(proposed_verdict(False), "unknown")

    def test_zero_error_failure_is_unknown(self):
        with self.assertRaises(EnumerationIncomplete):
            self.current(False, 0)
        self.assertEqual(proposed_verdict(False), "unknown")

    def test_success_empty_is_distinct_from_failure(self):
        self.assertEqual(self.current(True, 0), [])
        self.assertEqual(proposed_verdict(True), "observed")

    def test_success_ignores_stale_error(self):
        self.assertEqual(self.current(True, 18), [])
        self.assertEqual(proposed_verdict(True), "observed")

    def test_callback_failure_cannot_certify_completion(self):
        for kwargs in ({"owner_fails": True}, {"callback_raises": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(EnumerationIncomplete) as caught:
                self.current(True, 0, visited=1, **kwargs)
            metadata = enumeration_error(caught.exception)
            self.assertTrue(metadata["enumeration"]["callback_failed"])
            self.assertNotIn("private text", str(metadata))
        self.assertEqual(proposed_verdict(True, callback_failed=True), "unknown")

    def test_success_populated_is_preserved(self):
        self.assertEqual(self.current(True, 0, visited=2), [(42, True), (42, True)])

    def test_toolhelp_completion_is_not_desktop_completion(self):
        for ending in (18, 0, 5):
            for populated in (True, False):
                closed = []
                def first(handle, entry, ending=ending, populated=populated):
                    ctypes.set_last_error(ending)
                    if populated:
                        entry._obj.th32ProcessID = 42
                        entry._obj.th32ParentProcessID = 1
                        entry._obj.szExeFile = "fake.exe"
                    return populated
                def following(handle, entry, ending=ending):
                    ctypes.set_last_error(ending)
                    return False
                native = object.__new__(Native)
                native.k = SimpleNamespace(CreateToolhelp32Snapshot=lambda *a: 1,
                                           Process32FirstW=first, Process32NextW=following,
                                           CloseHandle=lambda h, closed=closed: (closed.append(h),
                                                                  ctypes.set_last_error(999)))
                with self.subTest(ending=ending, populated=populated):
                    if ending == 18:
                        result = native.processes()
                        self.assertEqual(result, [(42, 1, "fake.exe")] if populated else [])
                    else:
                        with self.assertRaises(EnumerationIncomplete) as caught:
                            native.processes()
                        self.assertEqual(caught.exception.enumeration["error"], ending)
                    self.assertEqual(closed, [1])


if __name__ == "__main__":
    unittest.main()
