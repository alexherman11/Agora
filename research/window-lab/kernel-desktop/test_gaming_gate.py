"""gaming_gate's lists: Windows' own facts in code, Alex's games from the world's mirror (4 Nov). Never reads or writes
the machine's real games.json: every test points AGORA_GAMES_FILE at a scratch file."""
import os
import sys
import unittest
from pathlib import Path

import gaming_gate as g

sys.path.append(str(Path(__file__).resolve().parents[2] / "kernel-lab"))
from kernel import scratch  # noqa: E402


class GameLists(unittest.TestCase):
    def setUp(self):
        self.tmp = scratch.TemporaryDirectory()
        self.was = os.environ.get("AGORA_GAMES_FILE")
        os.environ["AGORA_GAMES_FILE"] = str(Path(self.tmp.name) / "games.json")

    def tearDown(self):
        if self.was is None:
            os.environ.pop("AGORA_GAMES_FILE", None)
        else:
            os.environ["AGORA_GAMES_FILE"] = self.was
        self.tmp.cleanup()

    def test_with_nothing_from_the_world_only_the_name_test_and_windows_facts_hold(self):
        self.assertEqual((frozenset(), frozenset()), g.world_lists())
        self.assertFalse(g.is_game("RocketLeague.exe"), "a game the world never named and without 'game' in its name")
        self.assertTrue(g.is_game("SomeGame.exe"))
        self.assertFalse(g.is_game("GameBar.exe"), "Game Bar is Windows, not a game")
        self.assertTrue(g.never_game("TextInputHost.exe"))
        self.assertFalse(g.never_game("NVIDIA Overlay.exe"), "NVIDIA's overlay is Alex's machine, so the world says it")

    def test_the_world_names_games_and_programs_that_never_count(self):
        g.write_mirror({"rocketleague.exe", "both.exe"}, {"nvidia overlay.exe", "gamecapture.exe", "both.exe"}, "dk1")
        self.assertTrue(g.is_game("RocketLeague.exe"))
        self.assertFalse(g.is_game("GameCapture.exe"), "a not_game with 'game' in its name")
        self.assertTrue(g.never_game("NVIDIA Overlay.exe"))
        self.assertTrue(g.is_game("both.exe"), "named in both lists it is a game: the careful answer")

    def test_a_changed_mirror_is_read_again_and_a_broken_one_counts_as_nothing(self):
        g.write_mirror({"a.exe"}, set(), "dk1")
        self.assertTrue(g.is_game("a.exe"))
        g.write_mirror({"b.exe"}, set(), "dk1")
        os.utime(g.mirror_path(), (1, 1))                 # a new mtime even inside one clock tick
        self.assertTrue(g.is_game("b.exe"))
        self.assertFalse(g.is_game("a.exe"))
        g.mirror_path().write_text("{not json", encoding="utf-8")
        os.utime(g.mirror_path(), (2, 2))
        self.assertEqual((frozenset(), frozenset()), g.world_lists())


if __name__ == "__main__":
    unittest.main()
