"""The dock reads its apps from the world (4 Nov): an `app` thing names what a dock_apps entry is called and opens.

Real components, headless Edge and a disposable kernel (the shell components fixture). No live desktop is touched.
"""
import unittest
import test_shell_components as fixture

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


if __name__ == "__main__":
    unittest.main()
