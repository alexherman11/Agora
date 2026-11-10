"""Each app's installer makes its own `app` thing, once (4 Nov: the dock reads its apps from the world).

A hidden desktop world (test_kdesk.Desk) and the real installers; no window opens.
"""
import importlib.util
import unittest
from pathlib import Path

from test_kdesk import Desk

LAB = Path(__file__).resolve().parents[2] / "agora"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class AppThings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.desk = Desk()
        cls.painter = load("app_things_painter", LAB / "painter/install.py")
        cls.door = cls.painter.taskboard.Door(cls.desk.url, cls.desk.entry.token("alex"))

    @classmethod
    def tearDownClass(cls):
        cls.desk.close()

    def apps(self, name):
        return [(a["label"], a["does"]) for a in self.door.rows("app", name=name)]

    def twice(self, install):
        install()
        install()

    def test_work(self):
        work = load("app_things_work", LAB / "apps/work/install.py")
        self.twice(lambda: work.install(self.door))
        self.assertEqual(self.apps("work"), [("Work", "window.open work")])
        settings = self.door.rows("work-settings")
        self.assertEqual(len(settings), 1)
        self.assertEqual(settings[0]["word_blocked"], "Blocked")

    def test_appearance(self):
        theme = load("app_things_theme", LAB / "theme/install.py")
        self.twice(lambda: theme.install(self.door))
        self.assertEqual(self.apps("appearance"), [("Appearance", "window.open appearance")])

    def test_writing(self):
        writing = load("app_things_writing", LAB / "apps/writing/install.py")
        self.twice(lambda: writing.install(self.door, docs=False))
        self.assertEqual(self.apps("writing"), [("Writing", "window.open writing")])

    def test_feed(self):
        import restyle
        self.twice(lambda: restyle.install(self.desk.entry.token("alex"), self.desk.srv.server_address[1]))
        self.assertEqual(self.apps("feed"), [("Feed", "window.open feed")])

    def test_a_changed_label_stays(self):
        self.painter.app(self.door, "jukebox", "Jukebox", "jukebox")
        a = self.door.rows("app", name="jukebox")[0]["id"]
        self.door.say("look " + a)
        self.door.say("set " + a + " label=Records")
        self.painter.app(self.door, "jukebox", "Jukebox", "jukebox")
        self.assertEqual(self.apps("jukebox"), [("Records", "window.open jukebox")])


if __name__ == "__main__":
    unittest.main()
