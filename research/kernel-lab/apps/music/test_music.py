"""Adapter regression checks: fake session only, no media keys or real player."""
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

DESK = Path(__file__).resolve().parents[3] / "window-lab/kernel-desktop"
sys.path.insert(0, str(DESK))
import kd_media


class MusicTest(unittest.TestCase):
    def setUp(self):
        self.session = {"title": "Song", "artist": "Artist", "status": "Playing",
                        "position": 17, "end": 200, "can": {"shuffle": True, "repeat": True},
                        "shuffle": False, "repeat": "None"}
        self.fake = types.SimpleNamespace(
            SESSION=Mock(), ART=Path(__file__).parent, player_of=lambda _: "Fixture", press=Mock(return_value="session"))
        self.fake.SESSION.state.side_effect = lambda: {"ok": True, "s": self.session}
        self.fake.SESSION.start.return_value = True
        self.adapter = kd_media.Media()
        self.enterContext(patch.dict(sys.modules, media=self.fake))
        self.enterContext(patch.object(kd_media, "HEADLESS", False))
        self.enterContext(patch.object(kd_media.threading, "Timer"))

    def test_windows_status_is_play_state(self):
        self.assertTrue(self.adapter.now()["playing"])
        self.session["status"] = "Paused"
        self.assertFalse(self.adapter.now()["playing"])

    def test_time_is_reported_without_extrapolation(self):
        self.assertEqual(17, self.adapter.now()["position"])
        self.assertEqual(17, self.adapter.now()["position"])
        self.session["position"] = 23
        self.assertEqual(23, self.adapter.now()["position"])

    def test_transport_capabilities_and_modes_are_preserved(self):
        row = self.adapter.now()
        self.assertEqual(self.session["can"], row["can"])
        self.assertIs(False, row["shuffle"])
        self.assertEqual("None", row["repeat"])

    def test_unsupported_modes_never_press_anything(self):
        self.session["can"] = {}
        for word in ("media.shuffle", "media.repeat"):
            self.assertIn("refused", self.adapter.call({"word": word}))
        self.fake.press.assert_not_called()

    def test_supported_modes_reach_session(self):
        for action in ("shuffle", "repeat"):
            self.assertTrue(self.adapter.call({"word": "media." + action})["external"])
            self.fake.press.assert_called_with(action)

    def test_no_session_does_not_toggle_modes(self):
        self.session = None
        for action in ("shuffle", "repeat", "pause", "resume", "play"):
            self.assertIn("refused", self.adapter.call({"word": "media." + action}))
        self.fake.press.assert_not_called()

    def test_pause_resume_are_honest_noops(self):
        self.assertIn("refused", self.adapter.call({"word": "media.resume"}))
        self.fake.press.assert_not_called()
        self.assertTrue(self.adapter.call({"word": "media.pause"})["external"])
        self.fake.press.assert_called_once_with("play")
        self.fake.press.reset_mock()
        self.session["status"] = "Paused"
        self.assertIn("refused", self.adapter.call({"word": "media.pause"}))
        self.fake.press.assert_not_called()
        self.assertTrue(self.adapter.call({"word": "media.resume"})["external"])
        self.fake.press.assert_called_once_with("play")

    def test_missing_song_clears_reading(self):
        self.session["title"] = ""
        self.assertEqual([], self.adapter.call({"word": "media.now"})["rows"])


class MusicInstallTest(unittest.TestCase):
    def test_painter_preserves_session_capabilities_and_play_state(self):
        from test_kdesk import Desk
        from proof import load_app
        from kernel.kernel import Actor
        from painter.arrangement import compile_view
        desk = Desk()
        self.addCleanup(desk.close)
        app = load_app()
        door = app.board.Door(desk.url, desk.entry.token("alex"))
        app.install(door)
        person = next(p for p in desk.k.things("person") if desk.k.name(p) == "Alex")
        actor = Actor(person, person, "person")
        session = dict(kind="media", title="Song", playing=True, shuffle=True,
                       position=30, duration=180, repeat="None",
                       can={key: True for key in ("play", "pause", "prev", "next", "shuffle", "repeat")})
        def reading(command):
            self.assertEqual("media.now", command)
            return {"ok": True, "rows": [session]}
        def settings():
            plan = compile_view(desk.k, actor, "music", reader=reading)["rows"][0]
            part = next(p for p in plan["parts"] if p["component"] == "music-song")
            self.assertNotEqual("stopped", part["health"]["health"], part["health"])
            return part["settings"]
        projected = settings()
        self.assertEqual(session["can"], projected["can"])
        self.assertIs(True, projected["playing"])
        session.update(playing=False, can={"play": True, "pause": False})
        projected = settings()
        self.assertIs(False, projected["playing"])
        self.assertEqual(session["can"], projected["can"])
        session.update(can={})
        self.assertEqual({}, settings()["can"])

    def test_window_open_music_opens_its_lens(self):
        from test_kdesk import Desk
        from proof import load_app
        desk = Desk()
        self.addCleanup(desk.close)
        app = load_app()
        door = app.board.Door(desk.url, desk.entry.token("alex"))
        app.install(door)
        self.assertIsNone(desk.window("music"), "install must not open a window")
        reply = door.say("window.open music")
        self.assertTrue(reply["ok"], reply)
        window = desk.wait(lambda: desk.window("music"), 15)
        self.assertEqual("music", window["shows"])
        self.assertEqual("Music", window["name"])
        self.assertEqual("Music", door.rows("lens", name=window["shows"])[0]["title"])

    def test_dock_membership_in_fresh_and_customized_world(self):
        from test_kdesk import Desk
        from proof import load_app
        desk = Desk()
        self.addCleanup(desk.close)
        app = load_app()
        door = app.board.Door(desk.url, desk.entry.token("alex"))
        self.assertEqual([], door.rows("shell-settings"))
        ids = app.install(door)
        shells = door.rows("shell-settings")
        self.assertEqual(1, len(shells), "fresh installs must create dock settings")
        self.assertEqual(["lines", "help", "board", "taskboard", "appearance", "feed", "music"],
                         shells[0]["dock_apps"].split(","))
        self.assertEqual("Music", door.rows("lens", name="music")[0]["title"])
        self.assertTrue(door.rows("widget", name="music")[0]["on"])
        self.assertEqual(ids, app.install(door))
        self.assertEqual(shells, door.rows("shell-settings"), "reinstall must leave dock settings unchanged")
        # The same installer must retain Alex's app order and unrelated settings.
        shell = shells[0]["id"]
        door.say("look " + shell)
        door.say("set " + shell + ' dock_apps="writing,work,lines" show_cpu=yes')
        app.install(door)
        customized = door.rows("shell-settings")[0]
        self.assertEqual("writing,work,lines,music", customized["dock_apps"])
        self.assertEqual("yes", customized["show_cpu"])
        app.install(door)
        self.assertEqual([customized], door.rows("shell-settings"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
