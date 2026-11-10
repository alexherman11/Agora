"""The reviewed offline recipe: mocks only; never invoke a browser probe."""
from contextlib import ExitStack
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
import urllib.request

LAB = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB))
import hud_lifecycle
import sandbox_window
import test_sandbox_receipts
import test_sandbox_start
import test_sandbox_window


def forbidden(*args, **kwargs):
    raise AssertionError("offline suite reached an unmocked native/process/network boundary")


def main():
    # These tripwires supplement fakes; they are not an OS security sandbox.
    with ExitStack() as stack:
        for module, name in ((subprocess, "run"), (subprocess, "Popen"),
                             (urllib.request, "urlopen"), (hud_lifecycle, "Windows"),
                             (sandbox_window.k32, "CreateProcessW"),
                             (sandbox_window, "owner"), (sandbox_window, "exe")):
            stack.enter_context(patch.object(module, name, forbidden))
        suite = unittest.defaultTestLoader.loadTestsFromModule(test_sandbox_receipts)
        result = unittest.TextTestRunner(verbosity=1).run(suite)
        if not result.wasSuccessful():
            return 1
        test_sandbox_start.main()
        if test_sandbox_window.main():
            return 1
    print("OFFLINE ONLY: receipt tests, startup fakes and 10 Guard cases passed; no probe invoked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
