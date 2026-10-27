"""A painter window that is minimised, tucked or slowed is not a stopped window (27 Oct 2026).

Live bug: boards minimised by the window manager came back as "This part stopped" ("stopped answering for 5000 ms",
"its renderer exited", "no widget instance for this viewer"). Hidden headless Chromium only: a real minimise
(Browser.setWindowBounds), a frozen page (Page.setWebLifecycleState), or a host clock slowed the way Chromium slows a
page hidden for five minutes. Scratch world; no visible window, no live desktop, no 8810.
"""
import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / 'kernel-lab'), str(HERE)]

from painter.fixture import Fixture  # noqa: E402
from painter.browser import Page  # noqa: E402
import kdesk  # noqa: E402

WIDGETS = sys.modules[kdesk.Widgets.__module__]
SURFACE = 'document.querySelector("#widget-surface")'
# Chromium wakes a page hidden for five minutes about once a minute; the host's 250 ms watchdog then ticks late.
# Six seconds between ticks is enough to tell "late clock" from "silent frame" (the old watchdog called it a hang).
SLOW_HOST_CLOCK = "(()=>{const real=window.setInterval;window.setInterval=(fn,ms,...a)=>real(fn,ms===250?6000:ms,...a)})()"


class MinimisedWindows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = Fixture()
        cls.projects = []
        real = WIDGETS.Widgets._call

        def counted(self, actor, i, p, op, body):
            if op == 'project':
                cls.projects.append(time.monotonic())
            return real(self, actor, i, p, op, body)
        cls.real_call = real
        WIDGETS.Widgets._call = counted

    @classmethod
    def tearDownClass(cls):
        WIDGETS.Widgets._call = cls.real_call
        cls.f.close()

    def open(self):
        p = Page(self.f.url, self.f.token, self.f.ids['taskboard-components'])
        self.addCleanup(p.close)
        p.until('document.querySelectorAll(".card").length===25', 40)
        return p

    def host(self, p, expression):
        return p.c.js(expression)

    def state(self, p):
        return self.host(p, 'JSON.stringify({stopped:' + SURFACE + '.dataset.stopped||"",restarts:' + SURFACE +
                         '.dataset.restarts||"0",renewals:' + SURFACE + '.dataset.renewals||"0",text:(' + SURFACE +
                         '.querySelector("section")?.innerText||"").slice(0,200)})')

    def rename(self, i, title):
        t = self.f.tasks[i]
        self.f.door.say('look ' + t)
        self.assertTrue(self.f.door.say(f'set {t} title="{title}" short="{title}"')['ok'])

    def minimise(self, p, state):
        p.c.call('Emulation.setFocusEmulationEnabled', enabled=False)
        win = p.c.call('Browser.getWindowForTarget')['windowId']
        p.c.call('Browser.setWindowBounds', windowId=win, bounds={'windowState': state})
        end = time.monotonic() + 5
        want = 'hidden' if state == 'minimized' else 'visible'
        while self.host(p, 'document.visibilityState') != want and time.monotonic() < end:
            time.sleep(.1)
        self.assertEqual(self.host(p, 'document.visibilityState'), want)

    def test_a_slow_host_clock_is_not_a_hang(self):
        p = self.open()
        p.c.call('Page.addScriptToEvaluateOnNewDocument', source=SLOW_HOST_CLOCK)
        p.c.call('Page.reload')
        time.sleep(1)
        p.session = None
        p.until('document.querySelectorAll(".card").length===25', 40)
        time.sleep(14)    # two late watchdog ticks; the old host stopped the window on the first
        self.assertIn('"stopped":""', self.state(p))
        self.rename(2, 'Seen after a slow clock')
        p.until('document.body.innerText.includes("Seen after a slow clock")', 15)

    def test_a_reaped_instance_is_opened_again_by_itself(self):
        p = self.open()
        before = WIDGETS.REAP_AFTER
        WIDGETS.REAP_AFTER = 1
        try:
            p.c.call('Page.setWebLifecycleState', state='frozen')
            time.sleep(3)
            p.c.call('Page.setWebLifecycleState', state='active')
            end = time.monotonic() + 15
            while '"renewals":"1"' not in self.state(p) and time.monotonic() < end:
                time.sleep(.2)
        finally:
            WIDGETS.REAP_AFTER = before
        s = self.state(p)
        self.assertIn('"stopped":""', s)
        self.assertIn('"renewals":"1"', s)
        self.rename(3, 'Heard after renewal')      # the renewed instance hears make/set again
        p.until('document.body.innerText.includes("Heard after renewal")', 15)

    def test_a_minimised_board_reads_nothing_and_a_lost_frame_restarts_when_seen(self):
        p = self.open()
        self.minimise(p, 'minimized')
        time.sleep(1)
        del self.projects[:]
        self.rename(4, 'Changed while minimised')
        time.sleep(7)     # longer than the default safety reread (5 s)
        self.assertEqual(len(self.projects), 0, 'a minimised board planned the world')
        # Chromium may discard a background frame's renderer: nothing is shown as stopped while hidden.
        self.host(p, "dispatchEvent(new Event('agora-frame-failed'))")
        time.sleep(1)
        self.assertIn('"stopped":""', self.state(p))
        self.assertIn('"restarts":"0"', self.state(p))
        self.minimise(p, 'normal')
        end = time.monotonic() + 15
        while '"restarts":"1"' not in self.state(p) and time.monotonic() < end:
            time.sleep(.2)
        self.assertIn('"restarts":"1"', self.state(p))
        p.session = None
        p.until('document.body.innerText.includes("Changed while minimised")', 20)
        self.assertEqual(self.host(p, 'document.querySelectorAll("header.strip").length'), 1)

    def test_restarts_are_bounded(self):
        p = self.open()
        for n in (1, 2, 3):
            self.host(p, "dispatchEvent(new Event('agora-frame-failed'))")
            end = time.monotonic() + 15
            while f'"restarts":"{n}"' not in self.state(p) and time.monotonic() < end:
                time.sleep(.2)
            self.assertIn(f'"restarts":"{n}"', self.state(p))
            time.sleep(3.2)   # past the quiet moment after a restart
        self.host(p, "dispatchEvent(new Event('agora-frame-failed'))")
        time.sleep(1)
        s = self.state(p)
        self.assertIn('"stopped":"true"', s)
        self.assertIn('three times in two minutes', s)


if __name__ == '__main__':
    unittest.main(verbosity=2)
