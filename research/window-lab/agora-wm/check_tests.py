"""House unittest entry point using the shared Windows scratch allocator.

No native/browser proof is launched. Pass a repository-relative test directory
and discovery pattern. All disposable fixtures stay in the shared scratch area.
"""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/kernel-lab'))
from kernel import scratch


if __name__=='__main__':
    if len(sys.argv)!=3:
        raise SystemExit('usage: check_tests.py <test-directory> <pattern>')
    tempfile.mkdtemp=scratch.mkdtemp
    tempfile.TemporaryDirectory=scratch.TemporaryDirectory
    suite=unittest.defaultTestLoader.discover(str(ROOT/sys.argv[1]),pattern=sys.argv[2])
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    raise SystemExit(not result.wasSuccessful())
