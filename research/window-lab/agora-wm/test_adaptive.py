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
