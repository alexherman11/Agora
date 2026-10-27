"""Opening a requested board must not falsely report denied keyboard activation."""
import unittest
from unittest.mock import patch
import kd_window as window


class WindowSystem:
    def __init__(self,activate=False,raise_ok=True):
        self.foreground=20;self.order=[20,10];self.activate=activate;self.raise_ok=raise_ok;self.minimized=set()
    def GetForegroundWindow(self):return self.foreground
    def IsIconic(self,h):return h in self.minimized
    def ShowWindow(self,h,how):
        if how==window.SW_MINIMIZE:self.minimized.add(h)
        else:self.minimized.discard(h)
    def SetForegroundWindow(self,h):
        if self.activate:self.foreground=h;self.order=[h]+[n for n in self.order if n!=h]
        return self.activate
    def SetWindowPos(self,h,after,x,y,w,hi,flags):
        assert flags&window.SWP_NOACTIVATE
        assert after is None  # ordinary top, never always-on-top
        if self.raise_ok:self.order=[h]+[n for n in self.order if n!=h]
        return self.raise_ok


class Activation(unittest.TestCase):
    def screen(self):
        screen=window.GuiScreen.__new__(window.GuiScreen);screen.wins={'board':{'hwnd':10}};return screen
    def test_denied_keyboard_activation_still_raises_only_requested_window(self):
        os=WindowSystem()
        with patch.object(window,'user32',os):said=self.screen().focus('board')
        self.assertEqual(os.foreground,20);self.assertEqual(os.order,[10,20]);self.assertIn('without changing keyboard focus',said)
    def test_successful_activation_keeps_existing_focus_contract(self):
        os=WindowSystem(activate=True)
        with patch.object(window,'user32',os):said=self.screen().focus('board')
        self.assertEqual(os.foreground,10);self.assertEqual(said,'brought forward')
    def test_total_os_refusal_is_reported_honestly(self):
        os=WindowSystem(raise_ok=False)
        with patch.object(window,'user32',os):said=self.screen().focus('board')
        self.assertEqual(os.order,[20,10]);self.assertEqual(said,'Windows did not bring this window forward')
    def test_foreground_task_button_still_tucks_window(self):
        os=WindowSystem();os.foreground=10
        with patch.object(window,'user32',os):said=self.screen().focus('board')
        self.assertIn(10,os.minimized);self.assertEqual(said,'tucked away')
