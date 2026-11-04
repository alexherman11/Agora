"""House regression fixtures: all memory-only, no desktop/input."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from engine import Rect, State, Window, solve, valid
from manager import Manager
from size_policy import dimensions, resolve, validate

RULES=json.loads(Path(__file__).with_name('size-policies.json').read_text(encoding='utf-8'))


class SizePolicyTests(unittest.TestCase):
    def test_editable_matching_not_application_constants(self):
        row={'exe':'C:/Apps/new-player.exe','browser_class':True}
        rules=deepcopy(RULES)
        rules['my-player']={'match':{'exe':'new-*.exe'},'width':.23,'height':.4,'min_width':.1}
        work=Rect(0,0,1920,1080)
        pref,minimum=dimensions(row,work,validate(rules),(900,700),(16,16))
        self.assertEqual(pref,(431,419))
        self.assertEqual(minimum[0],187)
        self.assertEqual(resolve(row,rules)['kind'],'my-player')
        for value in (float('nan'),0,-.5,1.1,True):
            bad=deepcopy(rules);bad['my-player']['width']=value
            with self.assertRaises(ValueError):validate(bad)

    def test_two_windows_columns_on_landscape_portrait_and_odd_width(self):
        for width,height in ((1920,1080),(1080,1920),(1923,1080)):
            s=State(work=Rect(0,0,width,height))
            for key in ('a','b'):
                pref,floor=dimensions({'browser_class':True},s.work,RULES,(900,700),(16,16))
                s.windows[key]=Window(key,pref,floor,Rect(16,16,*pref))
            result=solve(s,{'type':'share','key':'b'})
            a,b=(result.state.windows[k].rect for k in ('a','b'))
            self.assertTrue(valid(result.state))
            self.assertEqual(result.minimise,[])
            self.assertEqual(a.y,b.y)
            self.assertEqual(a.h,b.h)
            self.assertEqual(a.right+s.gap_inner,b.x)

    def test_compact_arrival_uses_free_space_without_touching_neighbours(self):
        s=State(work=Rect(0,0,1920,1080))
        s.windows['browser']=Window('browser',(936,1048),(936,180),Rect(16,16,936,1048))
        s.windows['chat']=Window('chat',(460,480),(200,180),Rect(968,16,460,480))
        before={k:w.rect for k,w in s.windows.items()}
        pref,floor=dimensions({'exe':'spotify.exe'},s.work,RULES,(1200,800),(16,16))
        s.windows['music']=Window('music',pref,floor,Rect(20,20,*pref))
        result=solve(s,{'type':'share','key':'music'})
        self.assertTrue(valid(result.state))
        self.assertEqual(result.minimise,[])
        self.assertEqual({k:result.state.windows[k].rect for k in before},before)
        self.assertEqual(result.state.windows['music'].rect.w,pref[0])

    def test_compact_kind_stays_small_when_browser_must_make_room(self):
        s=State(work=Rect(0,0,1920,1080))
        s.windows['browser']=Window('browser',(936,1048),(936,180),s.bounds)
        pref,floor=dimensions({'exe':'spotify.exe'},s.work,RULES,(1200,800),(16,16))
        s.windows['music']=Window('music',pref,floor,Rect(20,20,*pref),compact=True)
        result=solve(s,{'type':'share','key':'music'})
        self.assertTrue(valid(result.state));self.assertEqual(result.minimise,[])
        browser,music=(result.state.windows[k].rect for k in ('browser','music'))
        self.assertLessEqual(browser.right+s.gap_inner,music.x)
        self.assertEqual((music.w,music.h),pref)
        self.assertGreater(browser.h,music.h)

    def test_manager_reads_live_facts_and_remembers_dragged_size(self):
        with tempfile.TemporaryDirectory() as folder:
            native=Mock();native.scale.return_value=1;native.cursor.return_value=None
            m=Manager(native,folder,gate_fn=lambda:[])
            work=Rect(0,0,1920,1080)
            row=dict(key='a',app='Music',exe='spotify.exe',agora=None,state='normal',
                     focused=False,rect=[16,16,600,700],managed=True,why='',
                     ref=SimpleNamespace(hwnd=1))
            m.configure({'sizes':json.dumps(RULES)})
            m.ingest([row],work)
            self.assertEqual(m.state.windows['a'].preferred,(468,524))
            changed=deepcopy(RULES);changed['compact-app']['width']=.3
            m.configure({'sizes':json.dumps(changed)});m.ingest([row],work)
            self.assertEqual(m.state.windows['a'].preferred,(562,524))
            from feel import Gesture
            m.gesture=Gesture(m.state,'a',Rect(*row['rect']),0)
            m._release(Rect(900,16,600,700),16)
            remembered=m.remembered['a']
            m.ingest([row],work)
            self.assertEqual(m.state.windows['a'].preferred,remembered)
            self.assertIn('a',m.user_sized)
            native.place.assert_not_called()

    def test_restart_repairs_old_top_bottom_pair(self):
        with tempfile.TemporaryDirectory() as folder:
            native=Mock();native.scale.return_value=1
            m=Manager(native,folder,gate_fn=lambda:[])
            rows=[dict(key=k,app=k,exe='fixture.exe',agora=None,state='normal',
                       focused=False,rect=[16,y,1000,400],managed=True,why='',
                       ref=SimpleNamespace(hwnd=i+1))
                  for i,(k,y) in enumerate((('a',16),('b',432)))]
            m.ingest(rows,Rect(0,0,1920,1080))
            a,b=(m.state.windows[k].rect for k in ('a','b'))
            self.assertTrue(valid(m.state))
            self.assertEqual(a.y,b.y)
            self.assertLessEqual(a.right+m.state.gap_inner,b.x)


if __name__=='__main__':unittest.main()
