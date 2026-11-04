"""Council night (proof card a13431) as a test: the whole evening, run end to end over real HTTP, passes only when
every one of its checks does. The run is proof/council_night.py; its evidence goes to a temporary folder here."""
import shutil
import sys
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB / "proof"))

import council_night  # noqa: E402
from kernel import scratch  # noqa: E402


@unittest.skipUnless(shutil.which("node"), "the agenda and tally modules need Node")
class CouncilNight(unittest.TestCase):
    def test_the_evening_works_as_a_whole(self):
        out = scratch.mkdtemp(prefix="council-evidence-")
        try:
            self.assertEqual(council_night.main(["--out", out]), 0, "a check failed; see the lines above")
        finally:
            shutil.rmtree(out, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
