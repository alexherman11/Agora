"""The dock reads its apps from the world (4 Nov): an `app` thing names what a dock_apps entry is called and opens.

Real components, headless Edge and a disposable kernel (the shell components fixture). No live desktop is touched.
"""
import unittest
import test_shell_components as fixture

import importlib.util
from pathlib import Path
_spec = importlib.util.spec_from_file_location("dock_apps_painter", Path(__file__).resolve().parents[2]
                                               / "kernel-lab/painter/install.py")
PAINTER = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PAINTER)
ITEM = 'document.querySelector("[data-id=\\"app:{}\\"]")'


class DockApps(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.ShellComponents.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        fixture.ShellComponents.tearDownClass.__func__(cls)

    def test_an_app_thing_puts_a_new_app_on_the_dock(self):
        a, p = self.alex, self.dock
        a.say('make kind=lens name=jukebox text=' + fixture.Q('root : text "scratch"'))
        shells = a.rows('shell-settings')
        if shells:
            a.say('look ' + shells[0]['id'])
            a.say('set ' + shells[0]['id'] + ' dock_apps="lines,jukebox,help"')
        else:
            a.say('make kind=shell-settings dock_apps="lines,jukebox,help"')
        p.js('ShellKit.poke("settings")')
        p.until('!!' + ITEM.format('help'), 15)
        self.assertFalse(p.js('!!' + ITEM.format('jukebox')), 'no app thing yet, so jukebox is not an app')
        a.say('make kind=app name=jukebox label=Jukebox does="window.open jukebox"')
        # someone's thing for a name the host already has does not change it
        a.say('make kind=app name=lines label=Hijack does="window.open jukebox"')
        p.js('ShellKit.poke("apps")')
        p.until('!!' + ITEM.format('jukebox'), 20)
        self.assertTrue(p.js(ITEM.format('jukebox') + '.getAttribute("aria-label").startsWith("Jukebox")'))
        self.assertTrue(p.js(ITEM.format('lines') + '.getAttribute("aria-label").startsWith("Lines")'))
        self.assertEqual(p.js('ShellKit.AGORA_APPS.jukebox[1]'), 'window.open jukebox')
        self.assertEqual(p.js('ShellKit.appOf("jukebox")'), 'jukebox')

    def test_installed_apps_come_from_their_app_things(self):
        # What every installer does (painter/install.py app(): taskboard, appearance, work, writing, music): one
        # app thing naming the lens it opens, made once.
        a, p = self.alex, self.dock
        a.say('make kind=lens name=taskboard-components text=' + fixture.Q('root : text "scratch"'))
        for _ in range(2):
            PAINTER.app(a, 'taskboard', 'Task board', 'taskboard-components')
        self.assertEqual([(x['label'], x['does']) for x in a.rows('app', name='taskboard')],
                         [('Task board', 'window.open taskboard-components')])
        shells = a.rows('shell-settings')
        line = ' dock_apps="lines,taskboard,board"'
        if shells:
            a.say('look ' + shells[0]['id'])
            a.say('set ' + shells[0]['id'] + line)
        else:
            a.say('make kind=shell-settings' + line)
        p.js('ShellKit.poke("lenses"); ShellKit.poke("settings"); ShellKit.poke("apps")')
        p.until('!!' + ITEM.format('taskboard'), 20)
        self.assertTrue(p.js(ITEM.format('taskboard') + '.getAttribute("aria-label").startsWith("Task board")'))
        self.assertFalse(p.js('!!' + ITEM.format('board')), 'board is no app: nothing opens a lens called board')
        self.assertEqual(sorted(p.js('Object.keys(ShellKit.AGORA_APPS)')),
                         sorted(['viewer', 'lines', 'help', 'thing', 'tasks'] + [x['name'] for x in a.rows('app')
                                                                                   if x['name'] not in ('lines',)]))


if __name__ == "__main__":
    unittest.main()
