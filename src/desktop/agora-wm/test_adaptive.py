import unittest
from copy import deepcopy
from unittest.mock import Mock
from engine import State, Window, Rect, solve, valid
import test_manager
from test_manager import row

def opened(s,key,size=(950,700),minimum=(400,280)):
    return solve(s,{'type':'open','key':key,'window':{'preferred':size,'minimum':minimum}}).state

class AdaptiveTests(unittest.TestCase):
    def test_spotify_chat_claude_fourth_and_repeat_focus(self):
        s=State(work=Rect(0,0,1600,1000),reflow='none')
        for key in ('spotify','chat','claude','fourth'):
            s=opened(s,key)
            self.assertTrue(valid(s));self.assertFalse(any(w.minimised for w in s.windows.values()))
        geometry={k:w.rect for k,w in s.windows.items()}
        for key in ('chat','fourth','spotify'):
            s=solve(s,{'type':'focus','key':key}).state
        self.assertEqual(geometry,{k:w.rect for k,w in s.windows.items()})
        repeated=solve(s,{'type':'open','key':'fourth'}).state
        self.assertEqual(len(repeated.windows),4);self.assertTrue(valid(repeated))

    def test_constrained_minimise_and_restore_on_close(self):
        s=State(work=Rect(0,0,650,450),reflow='none')
        s=opened(s,'spotify',(600,400),(400,280));baseline=deepcopy(s)
        s=opened(s,'chat',(600,400),(400,280))
        self.assertTrue(s.windows['spotify'].minimised)
        self.assertFalse(s.windows['chat'].minimised)
        s=solve(s,{'type':'close','key':'chat'}).state
        self.assertEqual(s.windows['spotify'].rect,baseline.windows['spotify'].rect)
        self.assertFalse(s.windows['spotify'].minimised);self.assertTrue(valid(s))

    def test_reflow_close_restores_exact_geometry(self):
        s=State(work=Rect(0,0,1400,900),reflow='none')
        s=opened(s,'a');before=s.windows['a'].rect
        s=opened(s,'b');self.assertNotEqual(before,s.windows['a'].rect)
        s=solve(s,{'type':'close','key':'b'}).state
        self.assertEqual(s.windows['a'].rect,before);self.assertEqual(s.displacement,{})

    def test_nested_out_of_order_closes_and_independent_close(self):
        for order in (('b','c'),('c','b')):
            s=State(work=Rect(0,0,1600,1000),reflow='none');s=opened(s,'a');before=s.windows['a'].rect
            s=opened(s,'b');s=opened(s,'c')
            for key in order:s=solve(s,{'type':'close','key':key}).state;self.assertTrue(valid(s))
            self.assertEqual(s.windows['a'].rect,before,order)
        s=opened(s,'b');s=solve(s,{'type':'close','key':'a'}).state
        s=solve(s,{'type':'close','key':'b'}).state
        self.assertEqual(s.windows,{});self.assertEqual(s.displacement,{})

    def test_manual_minimise_and_move_cancel_own_memory(self):
        for event in ({'type':'minimise','key':'a'}, {'type':'drag-end','key':'a','rect':[30,30,400,280]}):
            s=State(work=Rect(0,0,1600,1000),reflow='none');s=opened(s,'a');s=opened(s,'b')
            s=solve(s,event).state;before=deepcopy(s.windows['a'])
            s=solve(s,{'type':'close','key':'b'}).state
            self.assertEqual(s.windows['a'],before);self.assertTrue(valid(s))

    def test_pin_obstacle_and_monitor_change(self):
        s=State(work=Rect(0,0,1600,1000),reflow='none',obstacles=[Rect(1400,0,200,200)])
        s.windows['pin']=Window('pin',rect=Rect(16,16,400,280),pinned=True)
        before=s.windows['pin'].rect
        for key in ('a','b','c'):s=opened(s,key)
        self.assertEqual(s.windows['pin'].rect,before);self.assertTrue(valid(s))
        s=solve(s,{'type':'work-area','rect':[0,0,1000,700]}).state
        s=solve(s,{'type':'close','key':'c'}).state
        self.assertTrue(valid(s));self.assertEqual(s.windows['pin'].rect,before)

class RestoreFeedbackTests(unittest.TestCase):
    setUp=test_manager.ManagerTests.setUp
    def test_external_restore_during_pending_minimise_is_not_lost(self):
        from unittest.mock import patch
        rows=[row('a',(16,16,900,700)),row('b',(-32000,-32000,160,28))]
        rows[1]['state']='minimised';rows[1]['_preferred']=(900,700)
        work=Rect(0,0,1600,1000)
        self.m.ingest(rows,work)
        self.m.mode='live';self.m.lease=Mock()
        with patch('manager.time.monotonic',return_value=100):
            self.m.pending['b']={'kind':'minimise','rect':None,'at':99.9}
            restored=deepcopy(rows);restored[1]['state']='normal';restored[1]['rect']=[16,16,900,700]
            self.m.ingest(restored,work)
        self.assertFalse(self.m.state.windows['b'].minimised)
        self.assertTrue(valid(self.m.state))

    def test_dock_restore_replaces_pending_layout_and_updates_recency(self):
        rows=[row('a',(16,16,900,700)),row('b',(-32000,-32000,160,28))]
        rows[1]['state']='minimised';rows[1]['_preferred']=(900,700)
        self.m.ingest(rows,Rect(0,0,1600,1000))
        self.m.mode='live';self.m.lease=Mock()
        self.m.pending['b']={'kind':'minimise','rect':None,'at':0}
        self.m.action('restore','b')
        self.assertFalse(self.m.state.windows['b'].minimised)
        self.assertGreater(self.m.state.windows['b'].last_used,self.m.state.windows['a'].last_used)
        # Supersede the minimise, retaining the native restore settling period.
        self.assertEqual(self.m.pending['b']['kind'],'restore')
        self.native.restore.assert_called_once()

    def test_external_restore_supersedes_pending_before_and_after_timeout(self):
        from unittest.mock import patch
        for kind in ('minimise','placement'):
            for elapsed in (.1,.4):
                with self.subTest(kind=kind,elapsed=elapsed):
                    self.setUp()
                    work=Rect(0,0,1600,1000)
                    rows=[row('a',(16,16,900,700)),row('b',(-32000,-32000,160,28))]
                    rows[1].update(state='minimised',_preferred=(900,700))
                    self.m.ingest(rows,work);self.m.mode='live';self.m.lease=Mock()
                    self.m.pending['b']={'kind':kind,'rect':Rect(16,16,500,350),'at':100-elapsed}
                    restored=deepcopy(rows);restored[1].update(state='normal',rect=[16,16,900,700])
                    with patch('manager.time.monotonic',return_value=100):
                        self.m.ingest(restored,work)
                    self.assertTrue(self.m.state.windows['b'].managed)
                    self.assertFalse(self.m.state.windows['b'].minimised)
                    self.assertNotIn('b',self.m.failures)
                    # Placement settles; no transition remains on the next tick.
                    settled=deepcopy(restored)
                    for r in settled:
                        w=self.m.state.windows[r['key']]
                        r.update(rect=w.rect.values(),state='minimised' if w.minimised else 'normal')
                    with patch('manager.time.monotonic',return_value=101):
                        self.m.ingest(settled,work)
                    self.assertFalse(self.m.state.windows['b'].minimised)
                    self.assertTrue(valid(self.m.state))

    def test_expected_minimise_acknowledgement_keeps_window_minimised(self):
        from unittest.mock import patch
        work=Rect(0,0,1600,1000);rows=[row(),row('b')]
        self.m.ingest(rows,work)
        self.m.state=solve(self.m.state,{'type':'minimise','key':'b'}).state
        self.m.mode='live';self.m.lease=Mock()
        self.m.pending['b']={'kind':'minimise','rect':None,'at':100}
        minimised=deepcopy(rows);minimised[1]['state']='minimised'
        with patch('manager.time.monotonic',return_value=100.1):
            self.m.ingest(minimised,work)
        self.assertTrue(self.m.state.windows['b'].minimised)
        self.assertEqual(self.m.pending['b']['kind'],'minimise')

    def test_explicit_minimise_supersedes_a_pending_restore(self):
        from unittest.mock import patch
        work=Rect(0,0,1600,1000);rows=[row(),row('b')]
        self.m.ingest(rows,work);self.m.mode='live';self.m.lease=Mock()
        with patch('manager.time.monotonic',return_value=100):
            self.m.action('restore','b')
            self.m.action('minimise','b')
        self.assertTrue(self.m.state.windows['b'].minimised)
        self.assertEqual(self.m.pending['b']['kind'],'minimise')
        minimised=deepcopy(rows);minimised[1]['state']='minimised'
        with patch('manager.time.monotonic',return_value=100.4):
            self.m.ingest(minimised,work)
        self.assertTrue(self.m.state.windows['b'].managed)
        self.assertTrue(self.m.state.windows['b'].minimised)
        self.assertNotIn('b',self.m.failures)

    def test_restore_waits_for_native_geometry_before_placement(self):
        from unittest.mock import patch
        work=Rect(0,0,1600,1000)
        rows=[row('a',(16,16,900,700)),row('b',(-32000,-32000,160,28))]
        rows[1].update(state='minimised',_preferred=(900,700))
        self.m.ingest(rows,work);self.m.mode='live';self.m.lease=Mock()
        with patch('manager.time.monotonic',return_value=100):
            self.m.action('restore','b')
        restored=deepcopy(rows);restored[1].update(state='normal',rect=[16,16,900,700])
        with patch('manager.time.monotonic',return_value=100.1):
            self.m.ingest(restored,work)
        # Other windows may reflow; the restored window waits for fresh margins.
        target=rows[1]['ref'].hwnd
        self.assertNotIn(target,[c.args[0].hwnd for c in self.native.place.call_args_list])
        with patch('manager.time.monotonic',return_value=100.4):
            self.m.ingest(restored,work)
        self.assertIn(target,[c.args[0].hwnd for c in self.native.place.call_args_list])
        self.assertTrue(self.m.state.windows['b'].managed)

    def test_restore_geometry_is_not_replayed_as_drag(self):
        rows=[row('a',(16,16,900,700)),row('b',(-32000,-32000,160,28))]
        rows[1]['state']='minimised';rows[1]['_preferred']=(900,700)
        self.m.ingest(rows,Rect(0,0,1600,1000))
        from unittest.mock import patch
        import manager
        restored=deepcopy(rows);restored[1]['state']='normal';restored[1]['rect']=[16,16,1500,900]
        with patch('manager.solve',wraps=manager.solve) as solver:
            result=self.m.ingest(restored,Rect(0,0,1600,1000))
        events=[c.args[1]['type'] for c in solver.call_args_list]
        self.assertIn('restore',events);self.assertNotIn('drag-end',events)
        self.assertTrue(result['valid']);self.assertEqual(result['minimise'],[])

if __name__=='__main__':unittest.main()
