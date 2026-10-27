from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from engine import Rect,valid
from manager import Manager,DEFAULTS
from wm_module import WMModule,offers


def row(key='a',box=(16,16,800,600),managed=True):
    return {'key':key,'app':'Browser' if key=='a' else 'Terminal','exe':'C:/fixture/app.exe','icon':'C:/fixture/app.exe',
        'agora':None,'state':'normal','focused':key=='a','rect':list(box),'space':'primary','managed':managed,
        'why':'' if managed else 'elevated','ref':SimpleNamespace(hwnd=ord(key))}


class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.native=Mock();self.native.mutating=False;self.gates=[]
        self.native.needs_restore.return_value=False
        self.m=Manager(self.native,self.temp.name,allow_live=True,gate_fn=lambda:self.gates)

    def test_shadow_zero_mutations_privacy_and_determinism(self):
        rows=[row(),row('b',(400,100,900,700))];saved=deepcopy(rows)
        result=self.m.ingest(rows,Rect(0,0,2000,1200))
        self.assertTrue(result['valid']);self.assertFalse(self.native.mutating)
        self.assertEqual(self.native.mock_calls,[]);self.assertEqual(rows,saved)
        self.assertNotIn('title',Path(self.m.log_path).read_text().lower())
        self.assertNotIn('ref',self.m.reading()[0]);self.assertEqual(self.m.reading()[0]['icon'],'C:/fixture/app.exe')
        placements={k:w.rect for k,w in self.m.state.windows.items()}
        self.m.ingest(rows,Rect(0,0,2000,1200));self.assertEqual(placements,{k:w.rect for k,w in self.m.state.windows.items()})
        with self.assertRaises(PermissionError):self.m.action('minimise','a')

    def test_gating_skips_move_and_reports_apps(self):
        self.gates.append('full-screen');self.m.mode='live';self.m.lease=Mock()
        result=self.m.ingest([row()],Rect(0,0,2000,1200),[{'type':'drag-start','hwnd':97}])
        self.assertEqual(result['plan'],[]);self.assertEqual(result['observed_apps'],['Browser'])
        self.assertEqual(self.native.mock_calls,[]);self.assertIsNone(self.m.gesture)

    def test_discovering_minimised_app_does_not_minimise_visible_apps(self):
        self.m.ingest([row()],Rect(0,0,2000,1200));before=deepcopy(self.m.state.windows['a'])
        minimised=row('b',(-32000,-32000,160,28));minimised['state']='minimised';minimised['_preferred']=[900,700]
        self.m.ingest([row(),minimised],Rect(0,0,2000,1200))
        self.assertEqual(self.m.state.windows['a'],before)
        self.assertEqual(self.m.state.windows['b'].preferred,(900,700))
        self.assertTrue(self.m.state.windows['b'].minimised)

    def test_live_capability_and_off_same_release(self):
        self.m.allow_live=False
        with self.assertRaises(PermissionError):self.m.switch('live')
        lease=Mock();self.m.allow_live=True;self.m.lease_factory=lambda _:lease
        self.m.switch('live');self.assertTrue(self.native.mutating);lease.acquire.assert_called_once()
        self.m.switch('off');lease.release.assert_called_once();self.assertFalse(self.native.mutating)

    def test_ghost_defers_neighbours_until_release(self):
        lease=Mock();ghost=Mock();self.m.lease_factory=lambda _:lease;self.m.ghost_factory=lambda:ghost
        rows=[row(),row('b',(832,16,700,600))]
        self.m.ingest(rows,Rect(0,0,2400,1400));self.m.switch('live');self.native.reset_mock()
        self.m.ingest(rows,Rect(0,0,2400,1400),[{'type':'drag-start','hwnd':97}])
        dragged=deepcopy(rows);dragged[0]['rect']=[300,16,800,600]
        self.m.ingest(dragged,Rect(0,0,2400,1400))
        self.native.place.assert_not_called();self.native.minimise.assert_not_called();ghost.update.assert_called()
        self.m.ingest(dragged,Rect(0,0,2400,1400),[{'type':'drag-end','hwnd':97}])
        self.native.place.assert_called();self.assertTrue(valid(self.m.state))

    def test_refused_size_becomes_learned_minimum_then_obstacle(self):
        self.m.ingest([row()],Rect(0,0,2400,1400))
        self.m.mode='live';self.m.lease=Mock();self.native.mutating=True
        self.m.pending['a']={'rect':Rect(16,16,240,160),'at':0}
        self.m.ingest([row(box=(16,16,500,350))],Rect(0,0,2400,1400))
        self.assertEqual(self.m.state.windows['a'].minimum,(500,350))
        self.m.failures['a']=3
        self.m.ingest([row(box=(16,16,500,350))],Rect(0,0,2400,1400))
        self.assertFalse(self.m.state.windows['a'].managed)

    def test_overlapping_unmanageable_obstacles_allowed(self):
        result=self.m.ingest([row('b',(300,300,500,350),False),row('c',(400,300,500,350),False),row()],Rect(0,0,2400,1400))
        self.assertTrue(result['valid']);self.assertEqual(self.m.state.windows['b'].rect,Rect(300,300,500,350))

    def test_settings_validate_before_live(self):
        for settings in ({'drag':'live'},{'when_full':'magic'},{'never':42}):
            with self.assertRaises(ValueError):self.m.configure(settings)


class ModuleIntentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.wm=WMModule(headless=True);self.wm.owner='owner';self.wm.manager=Manager(Mock(),self.temp.name,gate_fn=lambda:[])
        self.settings={'id':'t1','rev':3,**DEFAULTS};self.wm.read_intent=lambda use=None:self.settings
    def call(self,word,words='',person='owner'):
        return self.wm.call({'word':word,'args':{'words':words},'caller':{'person':person},'use':'u'})
    def test_contract_help_and_owner(self):
        self.assertEqual({w['word'] for w in offers()},{'wm.windows','wm.focus','wm.minimise','wm.restore','wm.close',
            'wm.pin','wm.unpin','wm.arrange','wm.mode','wm.leave-alone','wm.manage'})
        self.assertTrue(all(w['help'] for w in offers()))
        self.assertIn('refused',self.call('wm.windows',person='stranger'))
    def test_modes_are_fenced_intent_and_live_disabled(self):
        answer=self.call('wm.mode','off');self.assertEqual(answer['saw'],{'t1':3})
        self.assertIn('mode=off',answer['lines'][0]);self.assertNotIn('external',answer)
        self.assertIn('refused',self.call('wm.mode','live'))
    def test_leave_alone_and_manage_are_undoable_world_lines(self):
        answer=self.call('wm.leave-alone','Browser');self.assertIn('Browser',answer['lines'][0]);self.assertEqual(answer['saw'],{'t1':3})


if __name__=='__main__':unittest.main()
