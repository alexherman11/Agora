# health: room test
"""Offline house-context admission checks; no live Win32 call or publication."""
import json
import ctypes
from pathlib import Path
import sys
import unittest
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import guard_context as g
sys.path.insert(0,str(Path(__file__).resolve().parents[2] / "window-lab"))
import agora_tmp


class ContextTests(unittest.TestCase):
    def clear(self):
        return dict(schema=g.SCHEMA, issuer="house", issuer_pid=42,
                    observed_at=100.0, uptime_ms=100000,
                    notification_result=0, notification_state=5,
                    foreground_known=True, input_desktop="Default",
                    full_screen=False, game=False, admitted=True)

    def test_fresh(self):
        self.assertTrue(g.validate(self.clear(), 102, 102000))

    def test_stale_future_reboot_clock_drift(self):
        for wall, tick in [(106,106000),(99,99000),(101,50),(102,100000)]:
            self.assertFalse(g.validate(self.clear(), wall, tick))

    def test_unknown_and_unsafe(self):
        for key, values in {
            "schema": ["worker"], "issuer": ["worker"], "issuer_pid": [0,True],
            "notification_result": [1], "notification_state": [1,2,3,4,6,7],
            "foreground_known": [False,None,1], "input_desktop": ["Winlogon","unknown"],
            "full_screen": [True,None], "game": [True,None], "admitted": [False],
        }.items():
            for val in values:
                self.assertFalse(g.validate({**self.clear(), key:val}, 101,101000),
                                 (key,val))

    def test_missing_or_malformed_fields(self):
        for key in self.clear():
            data=self.clear()
            del data[key]
            self.assertFalse(g.validate(data,101,101000), key)
        for data in [None, [], {}, {"observed_at":"nan"}, {"observed_at":1e500}]:
            self.assertFalse(g.validate(data,101,101000))

    def test_worktree_house_cannot_publish(self):
        with patch.object(g, "main_root", return_value=Path("not-the-checkout")):
            with patch.object(g,"observe") as probe:
                self.assertFalse(g.publish())
                probe.assert_not_called()

    def test_actual_observer_with_fake_windows(self):
        user, kernel, shell = Mock(), Mock(), Mock()
        user.GetForegroundWindow.return_value=123
        user.OpenInputDesktop.return_value=1
        def desktop(handle, index, buf, size, needed):
            buf.value="Default"
            return True
        def pid(hwnd, ptr):
            ptr._obj.value=77
            return 1
        def state(ptr):
            ptr._obj.value=5
            return 0
        user.GetUserObjectInformationW.side_effect=desktop
        user.GetWindowThreadProcessId.side_effect=pid
        shell.SHQueryUserNotificationState.side_effect=state
        kernel.GetTickCount64.return_value=100000
        dlls={"user32":user,"kernel32":kernel,"shell32":shell}
        with patch.object(ctypes,"WinDLL",side_effect=lambda name,**kw:dlls[name]), \
             patch.object(g.time,"time",return_value=100):
            self.assertTrue(g.validate(g.observe(),100,100000))
            user.GetForegroundWindow.return_value=0
            self.assertFalse(g.observe()["admitted"])
            user.GetForegroundWindow.return_value=123
            for n in (1,2,3,4,6,7):
                def blocked(ptr, value=n):
                    ptr._obj.value=value
                    return 0
                shell.SHQueryUserNotificationState.side_effect=blocked
                observation=g.observe()
                self.assertFalse(observation["admitted"])
                if n==3:
                    self.assertTrue(observation["game"])
            self.assertTrue(user.CloseDesktop.called)

    def test_fixed_non_worker_location(self):
        self.assertNotIn(".worktrees",str(g.location()))
        self.assertEqual(g.location().name,"guard-context.json")
        self.assertEqual(g.location().parent.name,"frontier")

    def test_house_loop_calls_only_live_frontier(self):
        # Exercise the real loop boundary on a stub runtime; no House constructor,
        # models, live world or native probe.
        import house
        class Stub:
            world="frontier"
            fake=False
            claude_version="stub"
            claude="stub"
            residents={}
            workshop=type("Workshop",(),{"workers":{},"restart_wanted":False})()
            another_house=lambda self:None
            act=lambda *a,**k:None
            def step(self):
                raise KeyboardInterrupt()
        with patch.object(house.subprocess,"run") as git:
            git.return_value.returncode=0
            git.return_value.stdout="test"
            for world,fake,expected in [("frontier",False,1),("copy",False,0),
                                        ("frontier",123,0)]:
                s=Stub()
                s.world,s.fake=world,fake
                with patch.object(g,"publish") as pub:
                    house.House.run(s)
                    self.assertEqual(pub.call_count,expected)

    def test_publish_atomic_failure_and_read_refusals(self):
        root=Path(agora_tmp.directory("guard-context-offline-"))
        here=root/"research/text-desk-lab/notation"
        target=root/"context.json"
        try:
            with patch.object(g,"HERE",here), patch.object(g,"main_root",return_value=root):
                with patch.object(g,"location",return_value=target):
                    with patch.object(g,"observe",return_value=self.clear()):
                        self.assertTrue(g.publish())
                    self.assertEqual(json.loads(target.read_bytes()),self.clear())
                    previous=target.read_bytes()
                    with patch.object(g,"observe",return_value=self.clear()):
                        with patch.object(g.os,"replace",side_effect=OSError("test")):
                            self.assertRaises(OSError,g.publish)
                    self.assertEqual(target.read_bytes(),previous)
                    with patch.object(g,"observe",side_effect=RuntimeError("private details")):
                        g.publish()
                    self.assertFalse(json.loads(target.read_bytes())["admitted"])
                    self.assertNotIn("private details",target.read_text())
            kernel=Mock()
            kernel.GetTickCount64.return_value=101000
            with patch.object(g,"location",return_value=target), \
                 patch.object(ctypes,"WinDLL",return_value=kernel), \
                 patch.object(g.time,"time",return_value=101):
                self.assertFalse(g.read()["admitted"])
                target.write_text(json.dumps(self.clear()))
                self.assertTrue(g.read()["admitted"])
                for text in ["broken", "x"*8193, json.dumps({})]:
                    target.write_text(text)
                    self.assertFalse(g.read()["admitted"])
                target.unlink()
                self.assertFalse(g.read()["admitted"])
        finally:
            import shutil
            shutil.rmtree(root)

    def test_fake_check_has_no_effect_on_refused_house_context(self):
        import check_sandbox_birth_guarded as check
        with patch.object(check.guard_context,"read",return_value={"admitted":False}), \
             patch.object(check.sb,"alex",return_value={"input desktop":"Default"}), \
             patch.object(check.sb.os,"makedirs"), \
             patch.object(check,"write") as write, \
             patch.object(check.sb,"start") as start, \
             patch.object(check.sb,"Guard") as guard, \
             patch.object(check.sb.ctypes.windll.shell32,"SHQueryUserNotificationState",return_value=0):
            self.assertEqual(check.main(),2)
            start.assert_not_called()
            guard.assert_not_called()
            self.assertFalse(write.call_args.args[1]["child_started"])


if __name__ == "__main__":
    unittest.main()
