"""Centre crossings, glass destinations and continuous native motion. No UI."""
import tempfile
import unittest
from unittest.mock import Mock

from engine import Rect, State, Window, crossed_centre, card_drop, valid, drop_spaces, choose_space
from feel import Gesture, Feel
from manager import Manager


def scene():
    s = State(work=Rect(0, 0, 1600, 900), gap_inner=16, gap_outer=16)
    for key, rect in [('a', Rect(16, 16, 776, 868)), ('b', Rect(808, 16, 776, 868))]:
        s.windows[key] = Window(key, (rect.w, rect.h), (240, 160), rect)
    return s


class CentreDrops(unittest.TestCase):
    def test_boundary_and_one_pixel_crossing_in_both_directions(self):
        for source, other, sign in [(Rect(0,0,200,200),Rect(300,0,200,200),1),
                                    (Rect(600,0,200,200),Rect(300,0,200,200),-1)]:
            self.assertFalse(crossed_centre(source,Rect(300,0,200,200),other))
            self.assertTrue(crossed_centre(source,Rect(300+sign,0,200,200),other))
            self.assertFalse(crossed_centre(source,Rect(300-sign,0,200,200),other))
            self.assertFalse(crossed_centre(source,Rect(300+sign,220,200,200),other))

    def test_stationary_overlap_never_yields_even_after_long_dwell(self):
        s=scene();g=Gesture(s,'a',s.windows['a'].rect,0)
        for t in (16,500,10000):
            f=g.step(Rect(700,16,776,868),t)
            self.assertEqual(f.ghosts,{})
            self.assertEqual(g.plan[0].windows['b'].rect,s.windows['b'].rect)

    def test_crossing_starts_at_home_then_glides_and_release_matches_box(self):
        s=scene();g=Gesture(s,'a',s.windows['a'].rect,0)
        target=Rect(809,16,776,868)
        first=g.step(target,16)
        self.assertEqual(first.ghosts,{})
        midway=g.step(target,80)
        self.assertTrue(16<midway.ghosts['b'].x<808)
        last=g.step(target,300)
        self.assertEqual(last.ghosts['b'],s.windows['a'].rect)
        result=g.release(target,300)
        self.assertTrue(valid(result.state))
        self.assertEqual(result.placements['a'],last.landing)
        self.assertEqual(result.placements['b'],s.windows['a'].rect)

    def test_pickup_exposes_half_and_column_then_drop_fills_selected_space(self):
        s=scene();del s.windows['b']
        g=Gesture(s,'a',s.windows['a'].rect,0)
        f=g.step(s.windows['a'].rect,0)
        self.assertTrue(any(q.w==776 for q in f.spaces))
        self.assertTrue(any(q.w<600 for q in f.spaces))
        f=g.step(Rect(1100,16,776,868),16)
        self.assertLess(f.landing.w,600)
        self.assertEqual(g.release(Rect(1100,16,776,868),16).placements['a'],f.landing)

    def test_cursor_selects_half_or_column_independently_of_carried_centre(self):
        s=scene();del s.windows['b']
        spaces=drop_spaces(s.bounds,[],s.gap_inner,(240,160))
        moving=Rect(500,16,776,868)
        side=choose_space(moving,spaces,s.bounds,(1196,35))
        column=choose_space(moving,spaces,s.bounds,(1510,35))
        self.assertEqual(side,Rect(808,16,776,868))
        self.assertLess(column.w,600)
        self.assertGreater(column.x,side.x)
        g=Gesture(s,'a',s.windows['a'].rect,0)
        f=g.step(moving,16,(1196,35))
        self.assertEqual(f.landing,side)
        self.assertEqual(g.release(moving,16,(1196,35)).placements['a'],side)

    def test_pointer_past_neighbour_cannot_bypass_carried_centre_threshold(self):
        s=scene();g=Gesture(s,'a',s.windows['a'].rect,0)
        for t in (16,500,10000):
            f=g.step(Rect(700,16,776,868),t,(1510,35))
            self.assertEqual(f.ghosts,{})
            self.assertEqual(g.plan[0].windows['b'].rect,s.windows['b'].rect)

    def test_blocked_show_never_constructs_glass_even_during_share(self):
        with tempfile.TemporaryDirectory() as folder:
            native=Mock();native.scale.return_value=1;factory=Mock()
            m=Manager(native,folder,gate_fn=lambda:['example-game.exe'],ghost_factory=factory)
            m.mode='live';m.share={'target':'a'}
            m.gesture=Gesture(scene(),'a',scene().windows['a'].rect,0)
            frame=m.gesture.step(Rect(809,16,776,868),16)
            m._show(frame,Rect(809,16,776,868))
            factory.assert_not_called();native.place.assert_not_called()
            self.assertIsNone(m.gesture)

    def test_foreground_change_invalidates_cached_clear_before_drawing(self):
        with tempfile.TemporaryDirectory() as folder:
            native=Mock();native.scale.return_value=1;native.gate_token.return_value=(1,0,5,False)
            gate=Mock(return_value=[]);glass=Mock()
            m=Manager(native,folder,gate_fn=gate,ghost_factory=Mock(return_value=glass))
            m.mode='live';m.lease=Mock()
            m.gesture=Gesture(scene(),'a',scene().windows['a'].rect,0)
            m._show(m.gesture.step(Rect(16,16,776,868),0),Rect(16,16,776,868))
            self.assertEqual(gate.call_count,1)
            glass.reset_mock();native.gate_token.return_value=(2,0,3,True)
            gate.return_value=['example-game.exe']
            m._show(m.gesture.frame,Rect(16,16,776,868))
            self.assertEqual(gate.call_count,2)
            glass.update.assert_not_called();glass.clear.assert_called_once()
            native.place.assert_not_called()

    def test_browser_uses_same_exact_boundary(self):
        body=dict(start=[0,0,200,200],moving=[300,0,200,200],
                  landing=[300,0,200,200],neighbours=[[300,0,200,200]],gap=12)
        self.assertFalse(card_drop(body)['allowed'])
        body['moving'][0]+=1
        result=card_drop(body)
        self.assertTrue(result['allowed'])
        self.assertEqual(result['placements'],[[300,212,200,200]])
        for value in (float('nan'),True,'x'):
            body['moving'][0]=value
            with self.assertRaises(ValueError):card_drop(body)

    def test_release_native_motion_has_intermediate_frames_and_no_focus(self):
        with tempfile.TemporaryDirectory() as folder:
            native=Mock();native.scale.return_value=1;lease=Mock()
            m=Manager(native,folder,allow_live=True,gate_fn=lambda:[],ghost_factory=Mock)
            m.mode='live';m.lease=lease;m.state=scene()
            m.rows=[dict(key=k,ref=Mock(hwnd=i),rect=w.rect.values(),managed=True,
                         app=k,state='normal',focused=False)
                    for i,(k,w) in enumerate(m.state.windows.items())]
            m.gesture=Gesture(m.state,'a',m.state.windows['a'].rect,0)
            m.drag_tick(Rect(809,16,776,868),.016)
            m.drag_tick(Rect(809,16,776,868),.080)
            before=m.drift['b']
            self.assertTrue(16<before.x<808)
            m._release(Rect(809,16,776,868),80)
            native.reset_mock()
            m.motion_tick(.080)
            native.place.assert_not_called()
            m.motion_tick(.112)
            b=m.rows[1]['ref']
            middle=[c.args[1] for c in native.place.call_args_list if c.args[0] is b][-1]
            self.assertTrue(16<middle.x<before.x)
            m.motion_tick(.400)
            self.assertFalse(m.motion)
            native.focus.assert_not_called();native.restore.assert_not_called()

    def test_sorted_card_landing_matches_priority_and_stable_ties(self):
        def order(priority, tie):
            return dict(keys=['priority'], values=[[0, priority, '']], tie=tie)
        body = dict(start=[0,180,200,160], moving=[301,180,200,160],
                    landing=[300,0,200,160], neighbours=[
                        [300,0,200,160], [300,180,200,160], [300,360,200,160]], gap=20,
                    orders=[order(2,3),order(1,1),order(2,4),order(3,2)])
        result = card_drop(body)
        self.assertTrue(result['allowed'])
        self.assertEqual(result['landing'],[300,180,200,160])
        self.assertEqual(result['placements'],[
            [300,0,200,160],[300,360,200,160],[300,540,200,160]])
        # A later equal-priority card belongs after the earlier one.
        body['orders'][0]['tie'] = 5
        body['moving'][1] = 360
        result = card_drop(body)
        self.assertEqual(result['landing'],[300,360,200,160])
        self.assertEqual(result['placements'][1],[300,180,200,160])
        # Descending and missing-last use the compiler's rule too.
        body['orders'] = [dict(keys=['-date'],values=[v],tie=i) for i,v in
                          enumerate([[0,2,''],[0,3,''],[0,1,''],[2,0,'']])]
        body['moving'][1] = 180
        self.assertEqual(card_drop(body)['landing'],[300,180,200,160])

    def test_gate_and_off_discard_motion_without_replaying_it(self):
        with tempfile.TemporaryDirectory() as folder:
            native=Mock();native.scale.return_value=1
            m=Manager(native,folder,gate_fn=lambda:['fullscreen'])
            m.mode='live';m.lease=Mock()
            m.motion={'a':(Rect(0,0,300,200),Rect(400,0,300,200),0)}
            m.motion_tick(.1)
            self.assertFalse(m.motion);self.assertTrue(m.gated)
            native.place.assert_not_called()
            m.motion={'a':(Rect(0,0,300,200),Rect(400,0,300,200),0)}
            m.switch('off')
            self.assertFalse(m.motion)


if __name__ == '__main__':
    unittest.main()
