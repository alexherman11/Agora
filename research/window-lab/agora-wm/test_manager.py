from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
from engine import Rect,valid
from manager import Manager,DEFAULTS
from wm_module import WMModule,offers


def acts(native):
    """Native calls other than the read-only DPI query."""
    return [c for c in native.mock_calls if c[0]!='scale']


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
        self.assertEqual(acts(self.native),[]);self.assertEqual(rows,saved)
        self.assertNotIn('title',Path(self.m.log_path).read_text().lower())
        self.assertNotIn('ref',self.m.reading()[0]);self.assertEqual(self.m.reading()[0]['icon'],'C:/fixture/app.exe')
        placements={k:w.rect for k,w in self.m.state.windows.items()}
        self.m.ingest(rows,Rect(0,0,2000,1200));self.assertEqual(placements,{k:w.rect for k,w in self.m.state.windows.items()})
        with self.assertRaises(PermissionError):self.m.action('minimise','a')

    def test_gating_skips_move_and_reports_apps(self):
        self.gates.append('full-screen');self.m.mode='live';self.m.lease=Mock()
        result=self.m.ingest([row()],Rect(0,0,2000,1200),[{'type':'drag-start','hwnd':97}])
        self.assertEqual(result['plan'],[]);self.assertEqual(result['observed_apps'],['Browser'])
        self.assertEqual(acts(self.native),[]);self.assertIsNone(self.m.gesture)

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
            'wm.pin','wm.unpin','wm.arrange','wm.mode','wm.leave-alone','wm.manage','wm.policy','wm.reload','wm.rollback'})
        self.assertTrue(all(w['help'] for w in offers()))
        self.assertIn('refused',self.call('wm.windows',person='stranger'))
    def test_modes_are_fenced_intent_and_live_disabled(self):
        answer=self.call('wm.mode','off');self.assertEqual(answer['saw'],{'t1':3})
        self.assertIn('mode=off',answer['lines'][0]);self.assertNotIn('external',answer)
        self.assertIn('refused',self.call('wm.mode','live'))
    def test_leave_alone_and_manage_are_undoable_world_lines(self):
        answer=self.call('wm.leave-alone','Browser');self.assertIn('Browser',answer['lines'][0]);self.assertEqual(answer['saw'],{'t1':3})


WORK=Rect(0,57,3840,1977)     # Alex's work area (ran, 26 Oct); State's default gaps are 16


def app(key,box,app_name='App',**extra):
    return {'key':key,'app':app_name,'exe':'C:/fixture/'+app_name+'.exe','icon':'C:/fixture/'+app_name+'.exe','agora':None,
        'state':'normal','focused':False,'rect':list(box),'space':'primary','managed':True,'why':'',
        'ref':SimpleNamespace(hwnd=sum(map(ord,key))*7),**extra}


class LiveFeel(unittest.TestCase):
    """The manager driving a drag the way the module does: hook events, the 60 Hz drag path, release."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.native=Mock();self.native.mutating=False;self.native.needs_restore.return_value=False
        self.ghost=Mock();self.lease=Mock();self.now=1000.0
        clock=patch('manager.time.monotonic',lambda:self.now);clock.start();self.addCleanup(clock.stop)
        self.m=Manager(self.native,self.temp.name,allow_live=True,gate_fn=lambda:[],
            lease_factory=lambda _:self.lease,ghost_factory=lambda:self.ghost)
        self.browser=app('browser',(16,73,1800,1300),'chrome');self.chat=app('chat',(1832,73,1992,1300),'Discord')
        self.notes=app('notes',(16,1389,1000,629),'Notepad')

    def rows(self,**moved):
        out=[]
        for r in (self.browser,self.chat,self.notes):
            r=deepcopy(r)
            if r['key'] in moved:r['rect']=list(moved[r['key']])
            out.append(r)
        return out

    def live(self):
        self.m.ingest(self.rows(),WORK);self.m.switch('live');self.native.reset_mock()

    def drag(self,path,ms_per_step=16):
        for box in path:
            self.now+=ms_per_step/1000;self.m.drag_tick(Rect(*box))

    def placed(self):
        return {c.args[0].hwnd:c.args[1] for c in self.native.place.call_args_list}

    def test_shallow_drop_moves_only_the_dragged_window_back_to_the_gap(self):
        self.live();hwnd=self.notes['ref'].hwnd
        self.m.ingest(self.rows(),WORK,[{'type':'drag-start','hwnd':hwnd}])
        path=[(16+20*i,1389-4*i,1000,629) for i in range(1,11)]           # up and right, 24 px into the browser's gap
        self.drag(path)
        self.now+=.016;self.m.ingest(self.rows(notes=path[-1]),WORK,[{'type':'drag-end','hwnd':hwnd}])
        self.assertEqual(self.placed(),{hwnd:Rect(216,1389,1000,629)})
        self.ghost.clear.assert_called()

    def test_hover_then_back_away_moves_nothing(self):
        self.live();hwnd=self.notes['ref'].hwnd
        self.m.ingest(self.rows(),WORK,[{'type':'drag-start','hwnd':hwnd}])
        there=[(16,1389-30*i,1000,629) for i in range(1,11)];back=list(reversed(there))[1:]+[(16,1389,1000,629)]
        self.drag(there);self.drag([there[-1]]*12);self.drag(back)   # rests 192 ms, less than the 350 ms dwell
        self.now+=.016;self.m.ingest(self.rows(),WORK,[{'type':'drag-end','hwnd':hwnd}])
        self.native.place.assert_not_called();self.native.minimise.assert_not_called()

    def test_ghost_shows_a_yielding_neighbour_and_real_windows_wait_for_release(self):
        self.live();hwnd=self.notes['ref'].hwnd
        self.m.ingest(self.rows(),WORK,[{'type':'drag-start','hwnd':hwnd}])
        into=(16,1100,1000,629)
        self.drag([(16,1389-29*i,1000,629) for i in range(1,11)]);self.drag([into]*40)
        rects,landing=self.ghost.update.call_args.args
        self.assertTrue(rects,'the browser gave way after the dwell')
        self.native.place.assert_not_called()
        self.now+=.016;self.m.ingest(self.rows(notes=into),WORK,[{'type':'drag-end','hwnd':hwnd}])
        self.assertTrue(valid(self.m.state))
        self.assertIn(self.browser['ref'].hwnd,self.placed())

    def test_maximised_and_owned_windows_float(self):
        maxed=app('video',(0,57,3840,1977),'vlc',maximised=True);dialog=app('save',(900,600,800,600),'chrome',owned=True)
        rows=self.rows()+[maxed,dialog]
        self.m.ingest(rows,WORK);self.m.switch('live');self.native.reset_mock()
        self.m.ingest(rows,WORK)
        self.native.restore.assert_not_called();self.native.minimise.assert_not_called();self.native.place.assert_not_called()
        self.assertNotIn('video',self.m.state.windows);self.assertNotIn('save',self.m.state.windows)
        self.assertEqual({r['key'] for r in self.m.reading()},{'browser','chat','notes','video','save'})

    def test_pinned_spotify_stays_put_when_other_tiles_can_shrink(self):
        # Spotify pinned wide: with the browser minimised, 1600 px remain, under 60 % of the editor's 3000.
        browser=app('browser',(16,73,1600,1945),'chrome');spotify=app('spotify',(1632,73,2192,1945),'Spotify')
        self.m.configure(DEFAULTS,['spotify']);self.m.ingest([browser,spotify],WORK);self.m.switch('live');self.native.reset_mock()
        editor=app('editor',(300,200,3000,1800),'Code',_preferred=(3000,1800))
        self.m.ingest([browser,spotify,editor],WORK)
        placed=self.placed();pin=placed.get(spotify['ref'].hwnd)
        self.assertIsNone(pin,'the pin needs no movement');self.assertTrue(valid(self.m.state))
        minimised=[c.args[0].hwnd for c in self.native.minimise.call_args_list]
        self.assertEqual(minimised,[],'reflow keeps all three visible')


class Quiet(unittest.TestCase):
    """Nothing per tick: the shadow log changes only with the plan; stderr hears a refusal once."""
    def test_shadow_log_writes_on_change_only(self):
        with tempfile.TemporaryDirectory() as folder:
            m=Manager(Mock(),folder,gate_fn=lambda:[])
            rows=[row(),row('b',(900,100,700,600))]
            for _ in range(50):m.ingest(rows,Rect(0,0,2000,1200))
            self.assertEqual(len(m.log_path.read_text().splitlines()),1)
            moved=deepcopy(rows);moved[1]['rect']=[1000,100,700,600]
            for _ in range(50):m.ingest(moved,Rect(0,0,2000,1200))
            self.assertEqual(len(m.log_path.read_text().splitlines()),2)

    def test_refusal_said_once_and_pins_from_screen_json(self):
        with tempfile.TemporaryDirectory() as folder:
            wm=WMModule(headless=True);gates=['notification gate 3']
            wm.manager=Manager(Mock(),folder,allow_live=True,gate_fn=lambda:gates,lease_factory=lambda _:Mock())
            settings={**DEFAULTS,'mode':'live','mode_request':'r1'};wm.intent_seen=True;wm.last_mode_request='r0'
            with patch('wm_module.log') as said:
                for _ in range(30):
                    wm.latest=(settings,['k1']);wm.manager.gate_cache=(None,-1);wm.tick()
                self.assertEqual(said.call_count,1,said.call_args_list)
                self.assertIn('gate',said.call_args.args[0])
                self.assertEqual(wm.manager.pins,{'k1'},'pins are window keys from screen.json')
                gates.clear();wm.latest=(settings,['k1']);wm.manager.gate_cache=(None,-1);wm.tick()
                self.assertEqual(wm.manager.mode,'live');self.assertEqual(said.call_count,2)   # one 'clear' line

    def test_standing_live_survives_restarts_but_not_the_panic_chord(self):
        """28 Oct, Alex: 'the window manager keeps booting into non-live mode'. The world's mode is the standing choice."""
        with tempfile.TemporaryDirectory() as folder:
            home=Path(folder);leases=[]
            def lease(_):
                leases.append(Mock());return leases[-1]
            def module():
                wm=WMModule(headless=True);wm.home=home
                wm.manager=Manager(Mock(),folder,allow_live=True,gate_fn=lambda:[],lease_factory=lease);return wm
            def tick(wm,settings):
                wm.latest=(settings,[]);wm.manager.gate_cache=(None,-1)
                with patch('wm_module.log'):wm.tick()
            live={**DEFAULTS,'mode':'live','mode_request':'r1'}
            wm=module();tick(wm,live)
            self.assertEqual(wm.manager.mode,'live','a restarted module arms from the standing choice')
            # the lease ends without the panic chord (a missed heartbeat): live again next second
            (home/'lease.json').write_text(json.dumps({'released':True,'reason':'heartbeat expired'}))
            leases[-1].heartbeat.side_effect=RuntimeError('guard gone');tick(wm,live)
            tick(wm,live);self.assertEqual(wm.manager.mode,'live')
            # the panic chord holds live off, through a restart too, until a new request
            (home/'lease.json').write_text(json.dumps({'released':True,'reason':'panic'}))
            leases[-1].heartbeat.side_effect=RuntimeError('panic');tick(wm,live)
            tick(wm,live);self.assertEqual(wm.manager.mode,'shadow')
            wm=module();tick(wm,live);self.assertEqual(wm.manager.mode,'shadow','panic outlives a restart')
            tick(wm,{**live,'mode_request':'r2'});self.assertEqual(wm.manager.mode,'live','a new wm.mode live lifts it')
            # wm.mode off is a standing off
            tick(wm,{**live,'mode':'off','mode_request':'r3'});wm2=module();tick(wm2,{**live,'mode':'off','mode_request':'r3'})
            self.assertEqual((wm.manager.mode,wm2.manager.mode),('off','off'))


if __name__=='__main__':unittest.main()
