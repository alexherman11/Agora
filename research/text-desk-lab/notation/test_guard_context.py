# health: room test
"""Offline house-context admission checks; no live Win32 call or publication."""
import json
import ctypes
from pathlib import Path
import sys
import threading
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
                    foreground_exe="chatgpt.exe",
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
        def image(handle, flags, buf, size):
            buf.value=r"C:\private\path\pythonw.exe"
            return True
        user.GetUserObjectInformationW.side_effect=desktop
        user.GetWindowThreadProcessId.side_effect=pid
        shell.SHQueryUserNotificationState.side_effect=state
        kernel.GetTickCount64.return_value=100000
        kernel.OpenProcess.return_value=1
        kernel.QueryFullProcessImageNameW.side_effect=image
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
                self.assertEqual(observation["foreground_exe"],"pythonw.exe")
                self.assertNotIn("private",json.dumps(observation))
                if n==3:
                    self.assertTrue(observation["game"])
                if n==2:
                    with patch.object(g,"executable_name",return_value="chatgpt.exe"):
                        allowed=g.observe("ChatGPT.exe")
                        self.assertTrue(g.validate(allowed,100,100000))
                        self.assertIsNone(allowed["game"])  # raw fact stays unknown
                        self.assertTrue(allowed["full_screen"])
                        self.assertFalse(g.observe("")["admitted"])
                        user.GetForegroundWindow.side_effect=[123,456]
                        self.assertFalse(g.observe("chatgpt.exe")["admitted"])
                        user.GetForegroundWindow.side_effect=None
                        values=iter([2,3])
                        def game_during_query(ptr):
                            ptr._obj.value=next(values)
                            return 0
                        shell.SHQueryUserNotificationState.side_effect=game_during_query
                        self.assertFalse(g.observe("chatgpt.exe")["admitted"])
                        shell.SHQueryUserNotificationState.side_effect=blocked
                        desktops=iter(["Default","Winlogon"])
                        def lock_during_query(handle,index,buf,size,needed):
                            buf.value=next(desktops)
                            return True
                        user.GetUserObjectInformationW.side_effect=lock_during_query
                        self.assertFalse(g.observe("chatgpt.exe")["admitted"])
                        user.GetUserObjectInformationW.side_effect=desktop
                    with patch.object(g,"foreground_is_hud",return_value=True) as hud:
                        self.assertTrue(g.observe("pythonw.exe")["admitted"])
                        hud.assert_called_once_with(77)
                        hud.return_value=False
                        self.assertFalse(g.observe("pythonw.exe")["admitted"])
            self.assertTrue(user.CloseDesktop.called)

    def test_executable_diagnostics_never_grant_hud_or_game_exception(self):
        for exe in ("pythonw.exe","python.exe","agora_start.exe","game.exe","unknown"):
            for state in (2,3,7):
                data={**self.clear(),"foreground_exe":exe,"notification_state":state,
                      "full_screen":True,"game":None,"admitted":True}
                self.assertFalse(g.validate(data,101,101000))

    def test_executable_denial_and_zero_pid_are_unknown(self):
        kernel=Mock()
        kernel.OpenProcess.return_value=None
        with patch.object(ctypes,"WinDLL",return_value=kernel):
            self.assertEqual(g.executable_name(0),"unknown")
            kernel.OpenProcess.assert_not_called()
            self.assertEqual(g.executable_name(77),"unknown")
            kernel.CloseHandle.assert_not_called()
            kernel.OpenProcess.return_value=123
            kernel.QueryFullProcessImageNameW.return_value=False
            self.assertEqual(g.executable_name(77),"unknown")
            kernel.CloseHandle.assert_called_once_with(123)

    def test_fixed_non_worker_location(self):
        self.assertNotIn(".worktrees",str(g.location()))
        self.assertEqual(g.location().name,"guard-context.json")
        self.assertEqual(g.location().parent.name,"frontier")

    def test_house_loop_calls_only_live_frontier(self):
        # Exercise the real loop boundary on a stub runtime; no House constructor,
        # models, live world or native probe.
        import house
        class Stub:
            # The real public entry now acquires its lifetime lease first.
            # Keep that behavior in this test, using only a private fixture.
            dir=Path(agora_tmp.directory("guard-house-loop-"))
            _run_owned=house.House._run_owned
            world="frontier"
            fake=False
            claude_version="stub"
            claude="stub"
            residents={}
            load=lambda self:None
            settings=lambda self,w:{"guard_nongame":"Example.exe"}
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
                with patch.object(g,"Publisher") as publisher:
                    house.House.run(s)
                    self.assertEqual(publisher.call_count,expected)
                    if expected:
                        publisher.return_value.start.assert_called_once_with()
                        publisher.return_value.update.assert_called_with("Example.exe")
                        publisher.return_value.close.assert_called_once_with()
            s = Stub()
            s.load = Mock(side_effect=OSError("private"))
            with patch.object(g, "Publisher") as publisher:
                house.House.run(s)
                publisher.return_value.update.assert_called_once_with("")
                publisher.return_value.close.assert_called_once_with()

    def test_sampler_continues_while_house_thread_is_blocked(self):
        first, second = threading.Event(), threading.Event()
        sampler = g.Publisher()
        calls = []
        def capture(policy):
            calls.append(policy)
            (first if len(calls) == 1 else second).set()
        with patch.object(g, "publish", side_effect=capture):
            sampler.update("first.exe")
            sampler.start()
            try:
                self.assertTrue(first.wait(2))
                sampler.update("second.exe")
                # Main thread waits instead of running another House.step.
                self.assertTrue(second.wait(2))
            finally:
                sampler.close()
        self.assertFalse(sampler.thread.is_alive())
        self.assertEqual(calls, ["first.exe", "second.exe"])

    def test_sampler_waits_after_failure_and_stops_without_extra_publish(self):
        sampler = g.Publisher()
        sampler.stopped = Mock()
        sampler.stopped.is_set.return_value = False
        sampler.stopped.wait.side_effect = [False, True]
        with patch.object(g.time, "monotonic", return_value=0), \
             patch.object(g, "publish", side_effect=[OSError("private"), True]) as pub:
            sampler.run()
        self.assertEqual(pub.call_count, 2)
        self.assertEqual(sampler.stopped.wait.call_args_list,
                         [((1.0,),), ((1.0,),)])

    def test_closed_sampler_does_not_publish(self):
        sampler = g.Publisher()
        sampler.stopped.set()
        with patch.object(g, "publish") as pub:
            sampler.run()
        pub.assert_not_called()

    def test_slow_sample_does_not_add_another_second_of_staleness(self):
        sampler = g.Publisher()
        sampler.stopped = Mock()
        sampler.stopped.is_set.return_value = False
        sampler.stopped.wait.return_value = True
        with patch.object(g.time, "monotonic", side_effect=[0, 3]), \
             patch.object(g, "publish"):
            sampler.run()
        sampler.stopped.wait.assert_called_once_with(0.0)

    def fullscreen(self, exe="chatgpt.exe", names="chatgpt.exe"):
        return {**self.clear(), "notification_state":2, "full_screen":True,
                "game":None, "foreground_exe":exe,
                "guard_nongame":g.nongame_names(names)}

    def test_world_list_is_exact_editable_case_insensitive_and_no_default(self):
        for exe in ("chatgpt.exe","codex.exe","msedge.exe","chrome.exe",
                    "firefox.exe","code.exe","explorer.exe","an-editor.exe"):
            self.assertTrue(g.validate(self.fullscreen(exe,exe.upper()),101,101000))
            self.assertFalse(g.validate(self.fullscreen(exe,""),101,101000))
            self.assertFalse(g.validate(self.fullscreen(exe,exe+".other.exe"),101,101000))
        for value in (None, ["chatgpt.exe"], "*.exe", r"C:\chatgpt.exe", "x"*1025):
            self.assertEqual(g.nongame_names(value),[])

    def test_allowlist_never_admits_game_locked_stale_unknown_or_wrong_desktop(self):
        data=self.fullscreen()
        for key, values in {
            "notification_state":[1,3,4,6,7,None],
            "notification_result":[1],
            "foreground_exe":["unknown",r"C:\chatgpt.exe","game.exe",""],
            "foreground_known":[False,None],
            "input_desktop":["Winlogon","unknown","Other"],
            "full_screen":[False,None], "game":[True,False],
            "guard_nongame":[None, ["*"], [None], ["ChatGPT.exe"]],
            "admitted":[False],
        }.items():
            for value in values:
                self.assertFalse(g.validate({**data,key:value},101,101000),(key,value))
        for wall,tick in [(106,106000),(99,99000),(101,0),(102,100000)]:
            self.assertFalse(g.validate(data,wall,tick))

    def test_pythonw_requires_verified_hud_even_when_world_lists_it(self):
        data=self.fullscreen("pythonw.exe","pythonw.exe")
        self.assertFalse(g.validate(data,101,101000))
        self.assertTrue(g.validate({**data,"foreground_hud":True},101,101000))
        self.assertFalse(g.validate({**data,"foreground_hud":True,
                                     "guard_nongame":[]},101,101000))
        self.assertFalse(g.validate({**data,"foreground_hud":True,
                                     "notification_state":3,"game":True},101,101000))

    def test_scoped_hud_query_matches_birth_script_scope_and_denial(self):
        import hud_lifecycle as life
        native=Mock()
        image=life.path_key(r"C:\pythonw.exe")
        native.identity.return_value=(100000,image)
        hud=str(g.main_root()/"research/window-lab/hud.py")
        native.argv.return_value=(image,hud)
        row={"pid":77,"exe":image,"created":100000,"command":"private command"}
        result=Mock(returncode=0,stdout=json.dumps(row))
        with patch.object(life,"Windows",return_value=native), \
             patch.object(g.subprocess,"run",return_value=result) as run:
            self.assertTrue(g.foreground_is_hud(77))
            self.assertIn("ProcessId=77",run.call_args.args[0][-1])
            self.assertNotIn("Name like",run.call_args.args[0][-1])
            self.assertEqual(run.call_args.kwargs["creationflags"],0x08000000)
            native.argv.return_value=(image,"-c",hud)
            self.assertFalse(g.foreground_is_hud(77))
            native.argv.return_value=(image,hud,"--world","copy")
            self.assertFalse(g.foreground_is_hud(77))
            native.argv.return_value=(image,hud)
            native.identity.side_effect=[(100000,image),(100001,image)]
            self.assertFalse(g.foreground_is_hud(77))
            native.identity.side_effect=None
            for field,value in [("pid",88),("created",100100),("exe",r"C:\other.exe")]:
                result.stdout=json.dumps({**row,field:value})
                self.assertFalse(g.foreground_is_hud(77))
            result.stdout=json.dumps(row)
            result.returncode=1
            self.assertFalse(g.foreground_is_hud(77))
            result.returncode=0
            run.side_effect=OSError("Access denied")
            self.assertFalse(g.foreground_is_hud(77))

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
