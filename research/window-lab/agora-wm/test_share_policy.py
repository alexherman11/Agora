"""Pure policy checks; no native windows, input, processes or filesystem fixtures.

Run alongside the controller/dock tests after House resolves fixture admission.
These do not establish native Electron fullscreen or owner acceptance.
"""
from itertools import permutations
import json
from pathlib import Path
import unittest

from engine import Rect, State, Window, solve, valid
from size_policy import dimensions, resolve

RULES=json.loads(Path(__file__).with_name('size-policies.json').read_text(encoding='utf-8'))


class SharePolicy(unittest.TestCase):
    def window(self,key,work):
        preferred,minimum=dimensions({'exe':key+'.exe','agora':key=='chat'},work,RULES,(700,600),(16,16))
        return Window(key,preferred=preferred,minimum=minimum,rect=Rect(16,16,*preferred))

    def assert_usable(self,state):
        self.assertTrue(valid(state))
        for key,w in state.windows.items():
            self.assertFalse(w.minimised,key)
            self.assertGreaterEqual(w.rect.w,w.minimum[0],key)
            self.assertGreaterEqual(w.rect.h,w.minimum[1],key)
            if key in ('claude','chrome'):
                self.assertGreaterEqual(w.rect.w,(state.bounds.w-state.gap_inner)//2)

    def test_three_apps_all_six_bar_orders_at_common_screen_sizes(self):
        for width,height in ((1920,1080),(2560,1440),(3840,2160)):
            for order in permutations(('claude','spotify','chat')):
                with self.subTest(screen=(width,height),order=order):
                    state=State(work=Rect(0,0,width,height))
                    for key in order:
                        state.windows[key]=self.window(key,state.work)
                        state=solve(state,{'type':'share','key':key}).state
                        self.assert_usable(state)
                    # A settled read is not another arrangement request.
                    self.assertEqual(solve(state,{'type':'noop'}).state,state)

    def test_close_grows_remaining_then_last_app_fills_screen(self):
        state=State(work=Rect(0,0,1920,1080))
        for key in ('claude','spotify','chat'):
            state.windows[key]=self.window(key,state.work)
            state=solve(state,{'type':'share','key':key}).state
        for closing in ('claude','spotify','chat'):
            with self.subTest(closing=closing):
                before=sum(w.rect.w*w.rect.h for k,w in state.windows.items() if k!=closing)
                remaining=solve(state,{'type':'close','key':closing}).state
                self.assert_usable(remaining)
                self.assertGreater(sum(w.rect.w*w.rect.h for w in remaining.windows.values()),before)
        state=solve(state,{'type':'close','key':'chat'}).state
        state=solve(state,{'type':'close','key':'spotify'}).state
        self.assertEqual(state.windows['claude'].rect,state.bounds)

    def test_requested_window_survives_and_true_lru_steps_aside(self):
        state=State(work=Rect(0,0,1200,800))
        for key,used in (('old',1),('recent',5),('request',0)):
            state.windows[key]=Window(key,(900,650),(900,650),
                Rect(16,16,900,650),last_used=used)
        state.clock=5
        result=solve(state,{'type':'share','key':'request'})
        self.assertFalse(result.state.windows['request'].minimised)
        self.assertEqual(result.minimise,['old','recent'])
        self.assertTrue(valid(result.state))

    def test_only_oldest_is_evicted_when_one_slot_is_needed(self):
        state=State(work=Rect(0,0,1920,1080))
        for key,used in (('old',1),('recent',9),('request',0)):
            state.windows[key]=Window(key,(900,700),(900,700),
                Rect(16,16,900,700),last_used=used)
        state.clock=9
        result=solve(state,{'type':'share','key':'request'})
        self.assertEqual(result.minimise,['old'])
        self.assertFalse(result.state.windows['request'].minimised)
        self.assertTrue(valid(result.state))

    def test_fixed_fullscreen_is_retained_request_gets_foreground_plan(self):
        state=State(work=Rect(0,0,1920,1080))
        state.windows['fixed']=Window('fixed',rect=state.bounds,managed=False)
        state.windows['request']=self.window('request',state.work)
        result=solve(state,{'type':'share','key':'request'})
        self.assertEqual(result.state.windows['fixed'].rect,state.bounds)
        self.assertNotIn('request',result.minimise)
        self.assertIn('request',result.placements)
        self.assertTrue(result.notes)
        self.assertTrue(valid(result.state))

    def test_hidden_apps_stay_hidden_and_pins_keep_bounds(self):
        state=State(work=Rect(0,0,3840,2160))
        pin=Rect(16,16,600,700)
        state.windows['pin']=Window('pin',rect=pin,pinned=True,home=pin)
        state.windows['asleep']=Window('asleep',rect=Rect(800,16,700,600),minimised=True)
        state.windows['claude']=self.window('claude',state.work)
        result=solve(state,{'type':'share','key':'claude'})
        self.assertEqual(result.state.windows['pin'].rect,pin)
        self.assertTrue(result.state.windows['asleep'].minimised)
        self.assertTrue(valid(result.state))

    def test_browser_classification_including_generic_electron_and_small_apps(self):
        for exe in ('Chrome.exe','Claude.exe','ChatGPT.exe','firefox.exe'):
            self.assertEqual(resolve({'exe':'C:/Apps/'+exe},RULES)['min_width'],.5)
        self.assertEqual(resolve({'exe':'other.exe','browser_class':True},RULES)['min_width'],.5)
        self.assertTrue(resolve({'exe':'Spotify.exe','browser_class':True},RULES)['compact'])
        self.assertTrue(resolve({'exe':'python.exe','browser_class':True,'agora':'chat'},RULES)['compact'])

    def test_chrome_keeps_half_width_through_pressure_and_close(self):
        state=State(work=Rect(0,0,1921,1080))
        for key in ('chrome','spotify','chat','extra','last'):
            state.windows[key]=self.window(key,state.work)
            state=solve(state,{'type':'share','key':key}).state
            self.assertTrue(valid(state))
            self.assertFalse(state.windows[key].minimised)
            if key in ('chrome','spotify','chat'):
                self.assertFalse(state.windows['chrome'].minimised)
            if not state.windows['chrome'].minimised:
                self.assertGreaterEqual(state.windows['chrome'].rect.w,(state.bounds.w-state.gap_inner)//2)
        state=solve(state,{'type':'close','key':'last'}).state
        self.assertTrue(valid(state))
        if not state.windows['chrome'].minimised:
            self.assertGreaterEqual(state.windows['chrome'].rect.w,(state.bounds.w-state.gap_inner)//2)

    def test_fullscreen_participant_is_never_lru_fallback(self):
        state=State(work=Rect(0,0,1200,800))
        for key,used in (('fullscreen',1),('recent',5),('request',0)):
            state.windows[key]=Window(key,(900,650),(900,650),
                Rect(16,16,900,650),last_used=used,no_evict=key=='fullscreen')
        result=solve(state,{'type':'share','key':'request'})
        self.assertEqual(result.minimise,[])
        self.assertFalse(result.state.windows['fullscreen'].minimised)
        self.assertFalse(result.state.windows['recent'].minimised)
        self.assertFalse(result.state.windows['request'].minimised)
        self.assertTrue(result.notes)
        self.assertTrue(valid(result.state))
        self.assertEqual(result.state.windows['request'].rect.w,900)
        self.assertEqual(result.state.windows['request'].rect.h,650)


if __name__=='__main__':
    unittest.main()
