import random
import unittest
from copy import deepcopy
from engine import State, Window, Rect, solve, valid


class EngineTests(unittest.TestCase):
    def test_fuzz(self):
        count=0
        for seed in range(2000):
            rng=random.Random(seed);s=State(work=Rect(0,0,1600,1000),reflow=rng.choice(['none','gentle']),
                when_full=rng.choice(['minimise-oldest','fill','focus']),gap_inner=rng.randint(0,24),gap_outer=rng.randint(0,24),
                obstacles=[Rect(1200,750,200,150)] if seed%3==0 else [])
            for step in range(30):
                keys=list(s.windows);key=rng.choice(keys) if keys else None
                kind=rng.choice(['open','close','minimise','restore','focus','pin','unpin','drag-move','resize-move','arrange','work-area'])
                e={'type':kind,'key':key}
                if not keys or kind=='open':
                    e={'type':'open','key':f'w{step}','window':{'preferred':(rng.randint(250,700),rng.randint(180,550))}}
                elif kind in ('drag-move','resize-move'):
                    e['rect']=[rng.randint(-200,1600),rng.randint(-100,1000),rng.randint(240,800),rng.randint(160,700)]
                elif kind=='work-area':
                    pins=[w.rect for w in s.windows.values() if w.pinned and w.rect and not w.minimised]
                    width=max([rng.randint(1000,1800)]+[r.right+s.gap_outer for r in pins])
                    height=max([rng.randint(700,1200)]+[r.bottom+s.gap_outer for r in pins])
                    e['rect']=[0,0,width,height]  # retain feasible pins; impossible shrink tested separately
                before=deepcopy(s);r=solve(s,e)
                self.assertEqual(before,s)
                s=r.state
                self.assertEqual(r,solve(before,e))
                self.assertTrue(valid(s),(seed,step,e,r.notes))
                old_visible={k:v.rect for k,v in before.windows.items() if v.rect and not v.minimised}
                if kind in ('focus','pin','unpin','arrange') and e['type']!='open':
                    self.assertEqual(old_visible,r.placements,(seed,step,'avoidable movement'))
                if e['type']=='open':
                    for k,box in old_visible.items():
                        if k in r.placements:self.assertEqual(box,r.placements[k],(seed,step,'open shuffled an existing window'))
                for k,w in before.windows.items():
                    if w.pinned and k in s.windows and kind not in ('unpin','close'):
                        self.assertEqual(w.rect,s.windows[k].rect)
                again=solve(s,{'type':'arrange'})
                self.assertEqual(r.placements,again.placements,(seed,step,e))
                self.assertEqual(again,solve(again.state,{'type':'arrange'}))
                count+=1
        print(f'L0 fuzz: 2000 sequences x 30 events = {count} events; invariants passed')

    def test_unaffected_component_and_minimal_zero(self):
        s=State(work=Rect(0,0,2200,1200),windows={k:Window(k,rect=r) for k,r in {
            'a':Rect(16,16,400,300),'b':Rect(450,16,400,300),'far':Rect(1600,800,400,300)}.items()})
        r=solve(s,{'type':'drag-move','key':'a','rect':[100,16,400,300]})
        self.assertEqual(r.placements['far'],s.windows['far'].rect)
        self.assertEqual(r.placements['a'],Rect(100,16,400,300))
        self.assertEqual(r.placements['b'],Rect(516,16,400,300))
        self.assertEqual(solve(s,{'type':'arrange'}).placements,{k:w.rect for k,w in s.windows.items()})

    def test_fixed_obstacle_and_pin_clamp(self):
        s=State(work=Rect(0,0,1000,700),obstacles=[Rect(600,16,300,500)],windows={
            'a':Window('a',rect=Rect(16,16,250,200)), 'pin':Window('pin',rect=Rect(300,16,250,200),pinned=True)})
        r=solve(s,{'type':'drag-end','key':'a','rect':[350,16,250,200]})
        self.assertTrue(valid(r.state));self.assertEqual(r.placements['pin'],s.windows['pin'].rect)
        self.assertTrue(r.notes)

    def test_all_resize_corners(self):
        for box in ([16,16,700,500],[100,16,600,500],[16,100,700,400],[100,100,600,400]):
            s=State(windows={'a':Window('a',rect=Rect(200,200,500,300))})
            self.assertTrue(valid(solve(s,{'type':'resize-end','key':'a','rect':box}).state))

    def test_impossible_fixed_geometry_explicit(self):
        s=State(work=Rect(0,0,100,100),windows={'pin':Window('pin',rect=Rect(0,0,500,500),pinned=True)})
        r=solve(s,{'type':'arrange'})
        self.assertEqual(r.placements['pin'],s.windows['pin'].rect)

    def test_full_policy_only_when_full_and_no_unnecessary_minimise(self):
        s=State(work=Rect(0,0,2000,1200),when_full='focus')
        s=solve(s,{'type':'open','key':'a','window':{'preferred':(400,300)}}).state
        s=solve(s,{'type':'open','key':'b','window':{'preferred':(400,300)}}).state
        self.assertFalse(s.windows['a'].minimised)
        s.when_full='minimise-oldest'
        result=solve(s,{'type':'open','key':'impossible','window':{'preferred':(3000,3000)}})
        self.assertEqual(result.minimise,['impossible'])


if __name__=='__main__':unittest.main()
