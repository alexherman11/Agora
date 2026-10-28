"""Narrow NVIDIA selection, bar ownership, and hidden browser layout/recreation."""
import ctypes as C
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import performance_overlay as perf

HERE = Path(__file__).resolve().parent


class Selection(unittest.TestCase):
    def test_only_covering_topmost_nvidia_cef_surfaces(self):
        import native_shell
        from ctypes import wintypes as W
        u = Mock()
        boxes = {10: (0, 0, 3840, 840), 20: (0, 0, 3840, 2160),
                 30: (0, 0, 3840, 2160), 40: (3840, 0, 7680, 2160),
                 50: (0, 0, 3840, 2160), 60: (0, 0, 3840, 2160)}
        def rect(h, ptr):
            r = C.cast(ptr, C.POINTER(W.RECT)).contents
            r.left, r.top, r.right, r.bottom = boxes[h]
            return 1
        u.GetWindowRect.side_effect = rect
        u.IsWindowVisible.return_value = True
        def cls(h, buf, n):
            buf.value = 'Other' if h == 60 else 'CEF-OSC-WIDGET'
            return len(buf.value)
        u.GetClassNameW.side_effect = cls
        u.GetWindowLongPtrW.side_effect = lambda h, _: 0 if h == 50 else 8
        u.EnumWindows.side_effect = lambda cb, _: [cb(h, 0) for h in boxes]
        with patch.object(perf.C, 'WinDLL', return_value=u), patch.object(
                native_shell, 'program_path', side_effect=lambda h:
                r'C:\NVIDIA Overlay.exe' if h != 30 else r'C:\other.exe'):
            self.assertEqual(perf.surfaces(10), [20])

    def test_only_our_bar_is_lowered_without_moving_or_focusing_any_window(self):
        u = Mock()
        with patch.object(perf, 'surfaces', return_value=[20, 30]), patch.object(
                perf.C, 'WinDLL', return_value=u):
            self.assertEqual(perf.accommodate(10), dict(width=520, height=52))
        u.SetWindowPos.assert_called_once_with(10, 30, 0, 0, 0, 0, 0x13)

    def test_absent_overlay_and_native_refusal_make_no_fallback_change(self):
        u = Mock()
        with patch.object(perf.C, 'WinDLL', return_value=u):
            with patch.object(perf, 'surfaces', return_value=[]):
                self.assertEqual(perf.accommodate(10), {})
                u.SetWindowPos.assert_not_called()
            with patch.object(perf, 'surfaces', return_value=[20]):
                u.SetWindowPos.return_value = False
                self.assertEqual(perf.accommodate(10), {})
                self.assertEqual(u.SetWindowPos.call_count, 1)

    def test_recreated_window_module_reports_slot_only_for_top_bar(self):
        import kd_window
        import shell_native
        with patch.object(shell_native, 'set_shape', return_value=True), patch.object(
                perf, 'accommodate', return_value=dict(width=520, height=52)) as adjust:
            for _ in range(2):  # fresh screen, like module re-creation; no saved slot state
                screen = kd_window.GuiScreen.__new__(kd_window.GuiScreen)
                screen.wins = {'top': dict(hwnd=10, view='shell-top'),
                               'dock': dict(hwnd=11, view='shell-dock')}
                screen.bars = {'top': Mock(), 'dock': Mock()}
                spec = dict(shape=[dict(x=0, y=0, w=2560, h=52)], reserve=52)
                self.assertEqual(screen.shell_layout('top', spec, 1.5),
                                 dict(ok=True, readout=dict(width=520, height=52)))
                self.assertIs(screen.shell_layout('dock', spec, 1.5), True)
                screen.bars['top'].resize.assert_called_once_with(78)
            self.assertEqual(adjust.call_args_list, [unittest.mock.call(10)] * 2)


class HiddenLayout(unittest.TestCase):
    @unittest.skip("Browser fixture startup/cleanup denied in this worker; see BUILD-RESULT.md. Repair fixture permissions before enabling.")
    def test_component_and_fallback_keep_strip_inside_bar_after_page_recreation(self):
        import widget_browser
        scratch = HERE.parents[2] / '.scratch' / 'readout-browser'
        # All browser profiles live under a top-level dot folder in this worktree.
        (scratch / 'state').mkdir(parents=True, exist_ok=True)
        browser = widget_browser.Browser()
        with patch.object(widget_browser, 'HERE', scratch):
            c = browser.__enter__()
        try:
            c.call('Emulation.setDeviceMetricsOverride', width=2560, height=560,
                   deviceScaleFactor=1.5, mobile=False)
            for fallback in (False, True):
                for restart in range(2):
                    c.call('Page.navigate', url='about:blank')
                    c.until('document.readyState==="complete"')
                    c.js("""document.body.dataset.page='top';
                        document.body.innerHTML='<header class="rail"><div class="isle left">Agora</div><div class="isle mid">Clock</div><div class="isle right">Media · WiFi · JEFF</div></header>';
                        window.activeSlot={width:520,height:52};window.calls=0;
                        window.pywebview={api:{layout:async()=>({ok:true,readout:activeSlot})}};
                        window.agora={native:async()=>{calls++;return {ok:true,readout:activeSlot}},see:async()=>({rows:[]})};
                        window.nativeTimers=window;
                        window.css=s=>{let e=document.createElement('style');e.textContent=s;document.head.append(e)};
                        """)
                    css = (HERE / 'pages/shell/shell.css').read_text(encoding='utf-8')
                    c.js('css(' + json.dumps(css) + ')')
                    if fallback:
                        source = (HERE / 'pages/shell/shell.js').read_text(encoding='utf-8')
                        c.js(source)
                        c.js('Shell.Native.layout({reserve:36,shape:[]})')
                    else:
                        source = (HERE / 'shell_parts/shell-kit.js').read_text(encoding='utf-8')
                        c.js('const SHELL_CSS="";\n' + source)
                        c.js("""ShellKit.shape=()=>{let r=document.querySelector('.rail').getBoundingClientRect();return {reserve:r.bottom,shape:[{x:0,y:0,w:innerWidth,h:r.bottom}]}}""")
                    c.until("document.querySelector('.rail').getBoundingClientRect().height===52")
                    geometry = c.js("""(()=>{
                      const rail=document.querySelector('.rail').getBoundingClientRect();
                      const right=document.querySelector('.right').getBoundingClientRect();
                      return {height:rail.height,right:right.right,reserve:window.__shape?.reserve,calls:window.calls};
                    })()""")
                    self.assertLessEqual(geometry['right'], 2560 - 520)
                    # Observed NVIDIA glyphs end at ~65 device pixels at 150%;
                    # the strip now ends at 78, fully enclosing the readout.
                    self.assertGreaterEqual(geometry['height'] * 1.5, 70)
                    if not fallback:
                        self.assertEqual(geometry['reserve'], 52)
                        self.assertLess(geometry['calls'], 8, 'layout feedback loop')
                    c.js("window.activeSlot={};" + (
                        "Shell.Native.layout({reserve:52,shape:[]})" if fallback
                        else "dispatchEvent(new Event('resize'))"))
                    c.until("document.querySelector('.rail').getBoundingClientRect().height===36")
        finally:
            # Graceful close of this test browser only; never terminate a process.
            try:
                c.call('Browser.close')
            except (EOFError, OSError):
                pass
            browser.process.wait(timeout=10)
            c.s.close()


if __name__ == '__main__':
    unittest.main()
