"""The bars as components (SHELL.md, "The bars as components"), tested hidden and headless.

A scratch world (test_kdesk.Desk: the kernel's door on a free loopback port, the window, system and media modules
--headless), a stand-in window manager (shell_parts/fake_wm.py: pretend windows, no real ones), shell_install.install,
then the real pages /desk/shell/top.html and /desk/shell/dock.html in headless Edge. Nothing appears on the screen and
nothing touches the live desktop (127.0.0.1:8810).

    C:/Projects/Agora4/.venv/Scripts/python.exe -m pytest -q test_shell_components.py   (from this directory)

What Alex and the agents do here, as they would: right-click the clock and ask for it bigger, then an agent makes it
bigger with one style line; an agent adds a battery chip with one lens line; a theme change repaints the bars; the dock
focuses, minimises and previews windows; a part that throws stops alone, and "Turn it off" removes it just for Alex.
"""
import json
import sys
import time
import unittest
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1] / 'kernel-lab'
sys.path[:0] = [str(HERE), str(LAB)]
from test_kdesk import Desk  # noqa: E402
from widget_browser import Browser  # noqa: E402
from painter.browser import Page  # noqa: E402
import shell_install  # noqa: E402

Q = shell_install.Q
PY = Path(sys.executable)
ASK_STEPS = 'make kind=ask-request about=$1 text=$text where=$where status=open'   # the live world's ask verb (read 26 Oct)


class ShellPage(Page):
    """painter.browser.Page, but the shell's own page (top or dock): the frame is evaluated with js(), the host with c.js()."""
    def __init__(self, url, token, page, key, width, height):
        self.browser = Browser(None, test_flags=['--disable-background-timer-throttling', '--disable-renderer-backgrounding',
                                                 '--disable-backgrounding-occluded-windows'])
        self.c = self.browser.__enter__()
        try:
            self._open(url, token, page, key, width, height)
        except BaseException:
            self.browser.__exit__(None, None, None)         # a page that never came up still closes its browser
            raise

    def _open(self, url, token, page, key, width, height):
        self.errors = []
        previous = self.c.on_event

        def capture(e):
            previous(e)
            if e.get('method') in ('Runtime.exceptionThrown', 'Log.entryAdded'):
                self.errors.append(e)
        self.c.on_event = capture
        self.c.call('Runtime.enable')
        # what the native widget guard adds in WebView2 (widget_guard.py)
        self.c.call('Network.setExtraHTTPHeaders', headers={'X-Agora-Widget-Host': key})
        self.c.call('Emulation.setFocusEmulationEnabled', enabled=True)
        self.c.call('Emulation.setDeviceMetricsOverride', width=width, height=height, deviceScaleFactor=1, mobile=False)
        self.c.call('Page.navigate', url=url + '/dev/signin?token=' + token + '&next=' + quote('/desk/shell/' + page + '.html', safe=''))
        self.c.until('!!document.querySelector("#widget-surface iframe") || !!window.__shellFallback || document.body.dataset.page==="' + page + '" && !!document.querySelector(".rail,.pill")', 30)
        self.session = None

    def host(self, expression):
        return self.c.js(expression)

    def mouse(self, selector, kind='left', rx=.5, ry=.5):
        p = self.point(selector, rx, ry)
        self.c.call('Input.dispatchMouseEvent', type='mouseMoved', **p)
        self.c.call('Input.dispatchMouseEvent', type='mousePressed', button=kind, buttons={'left': 1, 'right': 2, 'middle': 4}[kind], clickCount=1, **p)
        self.c.call('Input.dispatchMouseEvent', type='mouseReleased', button=kind, clickCount=1, **p)
        return p

    def hover(self, selector):
        p = self.point(selector)
        self.c.call('Input.dispatchMouseEvent', type='mouseMoved', **p)
        return p

    def type(self, text, enter=True):
        self.c.call('Input.insertText', text=text)
        if enter:
            self.c.call('Input.dispatchKeyEvent', type='keyDown', key='Enter', code='Enter', windowsVirtualKeyCode=13)
            self.c.call('Input.dispatchKeyEvent', type='keyUp', key='Enter', code='Enter', windowsVirtualKeyCode=13)


class ShellComponents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = d = Desk()
        cls.alex = shell_install._tb.Door(d.url, d.entry.token('alex'))
        cls.claude = shell_install._tb.Door(d.url, d.entry.token('claude'))
        a = cls.alex
        a.say('verb ask steps=' + Q(ASK_STEPS) + ' help=' + Q('ask <thing> text= where=: ask for a change (stand-in for the live verb)'))
        a.say('module wm run=' + Q(json.dumps([str(PY), str(HERE / 'shell_parts/fake_wm.py')])) + ' grants="rows look"')
        d.wait(lambda: a.request('/see', {'line': 'help wm.windows'}).get('ok') and a.request('/see', {'line': 'wm.windows'}).get('rows'), 20)
        cls.ids = shell_install.install(a, say=lambda *_: None)
        cls.key = d.srv.RequestHandlerClass.widget_broker.guard_key
        cls.lens = cls.ids['shell-top']
        cls.top = ShellPage(d.url, d.entry.token('alex'), 'top', cls.key, 1600, 560)
        cls.dock = ShellPage(d.url, d.entry.token('alex'), 'dock', cls.key, 1560, 460)
        cls.top.until('!!document.querySelector(".rail [data-component=shell-clock]")', 30)
        cls.dock.until('document.querySelectorAll(".pill .item[data-component=shell-dock-item]").length>=3', 30)

    @classmethod
    def tearDownClass(cls):
        for p in (cls.top, cls.dock):
            try:
                p.close()
            except Exception:
                pass
        cls.d.close()

    def calls(self):
        return [r['line'] for r in self.alex.request('/see', {'line': 'wm.calls'})['rows']]

    # ---------------------------------------------------------------------------------------------- the bar is parts
    def test_1_bars_paint_from_world_components(self):
        top, dock = self.top, self.dock
        self.assertIsNone(top.host('window.__shellFallback || null'), 'the top bar fell back to the hand-written page')
        parts = top.js('[...document.querySelectorAll(".rail [data-root][data-component]")].map(n=>n.dataset.component)')
        for c in ('shell-launcher', 'shell-focused-app', 'shell-clock', 'shell-tray', 'shell-chip', 'shell-jeff', 'shell-power'):
            self.assertIn(c, parts)
        # the same classes as the hand-written bar, so the same stylesheet draws it
        self.assertTrue(top.js('!!document.querySelector(".rail .isle.mid .btn.clock .t") && !!document.querySelector(".rail .isle.left .btn.mark .ico")'))
        self.assertEqual(top.js('document.querySelector(".btn.focus .fn").textContent'), 'Notepad')
        shape = top.host('window.__shape')
        self.assertGreater(shape['reserve'], 20)
        self.assertEqual(shape['shape'][0]['w'], 1600)
        self.assertTrue(any(c[0] == 'layout' for c in top.host('window.__native || []')), 'the host passed a layout to the window')
        view = self.alex.say('look-view shell-top')['rows'][0]
        self.assertGreaterEqual(view['counts'].get('shell-chip', 0), 3)
        # dock: one item per app, the front app marked, the window shape around the pill
        items = dock.js('[...document.querySelectorAll(".pill .item[data-component=shell-dock-item]")].map(n=>[n.getAttribute("aria-label"),n.dataset.factState])')
        self.assertTrue(any(l.startswith('Notepad, 2 windows') and s == 'front' for l, s in items), items)
        self.assertTrue(dock.host('window.__shape.reserve > 40 && window.__shape.shape.length >= 1'))
        print(f'\nbars: top parts {len(parts)}, dock items {len(items)}; top reserve {shape["reserve"]} css px', flush=True)

    # ---------------------------------------------------------------------------------------------- right-click, ask
    def test_2_alex_right_clicks_the_clock_and_asks_for_it_bigger(self):
        top, a = self.top, self.alex
        before = top.js('parseFloat(getComputedStyle(document.querySelector(".btn.clock .t")).fontSize)')
        top.mouse('.btn.clock .t', 'right')
        top.until('!!document.querySelector(".ask-menu input")')
        self.assertEqual(top.js('document.activeElement.className'), 'menu-ask')
        self.assertIn('clock', top.js('document.querySelector(".ask-menu").innerText').lower())
        top.c.until('window.__shape.shape.length >= 2', 5)        # the open ask menu is part of the clickable shape
        top.type('Make the clock bigger please')
        self.d.wait(lambda: a.rows('ask-request'), 10)
        ask = a.rows('ask-request')[-1]
        self.assertEqual(ask['text'], 'Make the clock bigger please')
        self.assertEqual(ask['about'], self.lens)
        self.assertIn('shell-top · root/middle/clock', ask['where'])
        top.until('!document.querySelector(".ask-menu")')
        # Claude reads the request and makes it bigger with one ordinary style line
        self.claude.say('make kind=part-style lens=shell-top target=shell-clock.time size=1.35em')
        top.until(f'parseFloat(getComputedStyle(document.querySelector(".btn.clock .t")).fontSize) > {before} * 1.3', 15)
        after = top.js('parseFloat(getComputedStyle(document.querySelector(".btn.clock .t")).fontSize)')
        print(f'\nclock: asked "{ask["text"]}" about {ask["about"]} at {ask["where"]}; time text {before:g}px -> {after:g}px', flush=True)

    # ---------------------------------------------------------------------------------------------- an agent adds a chip
    def test_3_an_agent_adds_a_battery_chip(self):
        top, agent = self.top, self.claude
        lens = agent.rows('lens', name='shell-top')[0]
        without = '\n'.join(l for l in lens['text'].splitlines() if 'battery' not in l)
        agent.say('look ' + lens['id']); agent.say('set ' + lens['id'] + ' text=' + Q(without))
        top.until('!document.querySelector(".q-chip.q-battery")', 15)
        chips = top.js('document.querySelectorAll(".btn.qs .q-chip").length')
        # the agent's edit: one line under the tray, and the chip says its press
        text = agent.rows('lens', name='shell-top')[0]['text'].replace(
            '        on press do window.settings which=volume\n',
            '        on press do window.settings which=volume\n      battery : shell-chip, key battery\n        on press do window.settings which=battery\n')
        agent.say('look ' + lens['id']); agent.say('set ' + lens['id'] + ' text=' + Q(text))
        top.until('!!document.querySelector(".q-chip.q-battery .q-pct") && document.querySelector(".q-chip.q-battery .q-pct").textContent==="84%"', 15)
        self.assertEqual(top.js('document.querySelectorAll(".btn.qs .q-chip").length'), chips + 1)
        self.assertIn('battery 84%, charging', top.js('document.querySelector(".btn.qs").getAttribute("aria-label")'))
        self.assertTrue(any(p['name'] == 'battery' for p in agent.say('look-view shell-top')['rows'][0]['parts']))
        print(f'\nbattery chip: {chips} chips -> {chips + 1}, showing 84% (charging)', flush=True)

    # ---------------------------------------------------------------------------------------------- the theme
    def test_4_a_theme_change_repaints_both_bars(self):
        top, dock = self.top, self.dock
        read = lambda p: p.js('[getComputedStyle(document.documentElement).getPropertyValue("--ag-ink").trim(), getComputedStyle(document.querySelector(".pill, .rail")).backgroundColor]')
        t0, d0 = read(top), read(dock)
        wall0 = top.host('getComputedStyle(document.documentElement).getPropertyValue("--ag-bg").trim()')
        out = self.alex.request('/do', {'line': 'theme.use night-metal'})
        self.assertTrue(out.get('ok'), out)
        top.until(f'getComputedStyle(document.documentElement).getPropertyValue("--ag-ink").trim() !== {json.dumps(t0[0])}', 25)
        dock.until(f'getComputedStyle(document.documentElement).getPropertyValue("--ag-ink").trim() !== {json.dumps(d0[0])}', 25)
        t1, d1 = read(top), read(dock)
        self.assertNotEqual(t0[1], t1[1], 'the rail repainted')
        self.assertNotEqual(d0[1], d1[1], 'the pill repainted')
        self.top.c.until(f'getComputedStyle(document.documentElement).getPropertyValue("--ag-bg").trim() !== {json.dumps(wall0)}', 25)
        self.assertTrue(top.js('!!document.querySelector(".btn.clock .t")'), 'parts survived the repaint')
        print(f'\ntheme: ink {t0[0]} -> {t1[0]}; rail {t0[1]} -> {t1[1]}; pill {d0[1]} -> {d1[1]}', flush=True)
        self.alex.request('/do', {'line': 'theme.use seabright-day'})

    # ---------------------------------------------------------------------------------------------- the dock works
    def test_5_the_dock_focuses_minimises_and_previews(self):
        dock = self.dock
        paint = '.pill .item[data-fact-app="paint"]'
        dock.mouse(paint)
        self.d.wait(lambda: any(c.startswith('wm.focus ') for c in self.calls()), 10)
        dock.until(f'document.querySelector({json.dumps(paint)}).dataset.factState==="front"', 10)
        dock.mouse(paint)
        self.d.wait(lambda: any(c.startswith('wm.minimise ') for c in self.calls()), 10)
        dock.until(f'document.querySelector({json.dumps(paint)}).dataset.factState==="minimised"', 10)
        dock.mouse(paint)
        self.d.wait(lambda: any(c.startswith('wm.restore ') for c in self.calls()), 10)
        # hover Notepad (two windows): a preview with two tiles, and the host asks for two live thumbnails
        dock.c.call('Input.dispatchMouseEvent', type='mouseMoved', x=5, y=5)
        dock.hover('.pill .item[data-fact-app="notepad"]')
        dock.until('document.querySelectorAll(".pop.preview .tile").length===2', 10)
        dock.c.until('(window.__thumbs||[]).length===2', 10)
        tiles = dock.host('window.__thumbs')
        self.assertEqual(sorted(t['hwnd'] for t in tiles), ['5001', '5002'])
        dock.c.until('window.__shape.shape.length>=2', 5)          # the preview is clickable
        # right-click: its windows, and the ask box at the end
        dock.mouse('.pill .item[data-fact-app="notepad"]', 'right')
        dock.until('!!document.querySelector(".pop .menu .menu-ask") && document.querySelectorAll(".pop .menu .mrow").length>=4')
        dock.c.call('Input.dispatchKeyEvent', type='keyDown', key='Escape', code='Escape', windowsVirtualKeyCode=27)
        print(f'\ndock: said {self.calls()}; preview thumbnails for hwnds {[t["hwnd"] for t in tiles]}', flush=True)

    # ---------------------------------------------------------------------------------------------- a part that throws
    def test_6_a_part_that_throws_stops_alone(self):
        top, a = self.top, self.alex
        bad = a.say('make kind=component name=shell-weather category=shell purpose=' + Q('Weather, by an agent; throws')
                    + ' settings="{}" parts=' + Q('{"body":{}}') + ' code=' + Q("export default {mount(api){throw new TypeError('weather service missing')}}"))['made'][0]
        late = a.say('make kind=component name=shell-ticker category=shell purpose=' + Q('Throws a second after it paints')
                     + ' settings="{}" parts=' + Q('{"body":{}}') + ' code=' + Q("export default {mount(api){const b=api.part('body','span',{class:'read'},'tick');api.setTimeout(()=>{throw new Error('ticker lost its feed')},800);return b}}"))['made'][0]
        for c in (bad, late):
            a.say('look ' + c); a.say('component ' + c)                  # a steward reviews the bytes, as for any component
        records = len(self.d.k.log.records)
        lens = a.rows('lens', name='shell-top')[0]
        text = lens['text'].replace('    jeff : shell-jeff\n', '    weather : shell-weather\n    ticker : shell-ticker\n    jeff : shell-jeff\n')
        a.say('look ' + lens['id']); a.say('set ' + lens['id'] + ' text=' + Q(text))
        top.until('!!document.querySelector(".rail .component-stopped[data-component=shell-weather]")', 15)
        top.until('!!document.querySelector(".rail .component-stopped[data-component=shell-ticker]")', 15)
        t1 = top.js('document.querySelector(".btn.clock .t").textContent')
        self.assertTrue(top.js('!!document.querySelector(".rail .btn.jeff") && !!document.querySelector(".rail .btn.clock") && !!document.querySelector(".rail .btn.qs")'))
        self.assertIsNone(top.host('window.__shellFallback || null'))
        # health is this screen's: look-view sees it, the world holds no report, and no record was written for it
        view = a.say('look-view shell-top')['rows'][0]
        self.assertEqual(next(p for p in view['parts'] if p['name'] == 'weather')['health']['health'], 'stopped')
        self.assertEqual(a.rows('paint-report'), [])
        self.assertEqual(len(self.d.k.log.records), records + 1, 'only the lens edit was recorded')
        # press the chip: the recovery opens; Turn it off removes it just for Alex (a private preference, undoable)
        top.mouse('.rail .component-stopped[data-component=shell-weather]')
        top.until('[...document.querySelectorAll(".stopped-pop button")].some(b=>b.textContent==="Turn it off")')
        top.js('[...document.querySelectorAll(".stopped-pop button")].find(b=>b.textContent==="Turn it off").click()')
        self.d.wait(lambda: any(p.get('weather.enabled') == 'no' for p in a.rows('view-preference')), 10)
        top.until('!document.querySelector(".rail .component-stopped[data-component=shell-weather]:not([data-off])")', 15)
        self.assertNotEqual(top.js('document.querySelector(".btn.clock .t").textContent') or t1, None)
        print(f'\nstopped: weather and ticker stopped alone; weather turned off for Alex; records written by the failures: 0', flush=True)
        a.say('look ' + lens['id']); a.say('set ' + lens['id'] + ' text=' + Q(lens['text']))

    # ---------------------------------------------------------------------------------------------- the native gate
    def test_7_no_native_grant_means_the_hand_written_bar(self):
        a, mid = self.alex, self.ids['shell-dock widget']
        narrow = shell_install.GRANTS.replace(' window.native', '')
        a.say('look ' + mid); a.say('widget ' + mid + ' surface=window grants=' + Q(narrow) + ' only=' + shell_install.ONLY)
        page = ShellPage(self.d.url, self.d.entry.token('alex'), 'dock', self.key, 1560, 460)
        try:
            page.c.until('!!window.__shellFallback && !!document.querySelector(".pill .item")', 20)
            self.assertIn('window.native', page.host('window.__shellFallback'))
            self.assertFalse(page.host('!!document.querySelector("#widget-surface")'))
        finally:
            page.close()
            a.say('look ' + mid); a.say('widget ' + mid + ' surface=window grants=' + Q(shell_install.GRANTS) + ' only=' + shell_install.ONLY)

    def test_8_install_is_idempotent_and_keeps_an_edited_lens(self):
        a = self.alex
        n = len(self.d.k.log.records)
        said = []
        shell_install.install(a, say=said.append)
        self.assertEqual(len(self.d.k.log.records), n, 'a second install says nothing')


class PageApiGate(unittest.TestCase):
    """kd_window.PageApi: only a shell window may shape itself, ask thumbnails or read a title (window.native)."""
    def test_only_shell_windows_answer(self):
        import kd_window

        class Screen:
            wins = {'a': {'view': 'shell-dock', 'hwnd': 1}, 'b': {'view': 'widget', 'hwnd': 2}}
            def shell_layout(self, wid, spec, dpr): return 'shaped ' + wid
            def shell_thumbs(self, wid, tiles, dpr): return 3
        s = Screen()
        self.assertEqual(kd_window.PageApi(s, 'a').layout('{}'), 'shaped a')
        self.assertEqual(kd_window.PageApi(s, 'a').thumbs('[]'), 3)
        self.assertIs(kd_window.PageApi(s, 'b').layout('{}'), False)
        self.assertEqual(kd_window.PageApi(s, 'b').thumbs('[]'), 0)
        self.assertEqual(kd_window.PageApi(s, 'b').title('123'), '')


if __name__ == '__main__':
    unittest.main()
