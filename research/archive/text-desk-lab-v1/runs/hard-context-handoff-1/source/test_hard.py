"""Feasibility witnesses and architecture counterexamples; unavailable to Terra."""

from copy import deepcopy
import unittest

from hard_scenarios import build, assess
from test_desk import do


class HardTests(unittest.TestCase):
    def test_procurement_feasible(self):
        d = build('procurement')
        ids = d.ids
        args = dict(supplier='Cedar', quantity=12, unit_price=215, shipping=240, extras=120)
        refusal = d.dispatch('act', dict(verb='set_inputs', target=ids['sheet'], expected=1, args=args))
        self.assertIn('Stale', refusal['error'])
        self.assertEqual(d.get(ids['sheet'])['inputs']['supplier'], 'TBD')
        do(d, 'set_inputs', ids['sheet'], **args)
        for part, value in [('supplier','Cedar'), ('total','$2,940'), ('time','15:00 UTC')]:
            do(d, 'edit', ids['decision'], part=part, before='TBD', after=value)
        do(d, 'schedule', ids['appointment'], start=900)
        do(d, 'compose', ids['purchase-draft'], to='procurement@example.invalid', subject='Review',
           body='Cedar: $2,940; delivery 10 October 2026; review 15:00 UTC.')
        do(d, 'reference', ids['questions'], source=ids['cedar'])
        for i,key in enumerate(['mail','cost-window','decision-window']):
            do(d, 'frame', ids[key], x=i*520, y=0, width=500, height=800)
        self.assertTrue(assess('procurement',d)['passed'], assess('procurement',d))

    def test_calendar_conflict_and_formula_write_atomic(self):
        d = build('impossible')
        before = d.snapshot()
        for key, verb, args in [('appointment','schedule',{'start':870}), ('sheet','set_inputs',{'total':1})]:
            result = d.dispatch('act', dict(verb=verb, target=d.ids[key], expected=1, args=args))
            self.assertIn('error', result)
            self.assertEqual(before,d.snapshot())

    def test_impossible_frame_refusal_atomic(self):
        d = build('impossible')
        before = d.snapshot()
        for args in [dict(x=0,y=0,width=240,height=240), dict(x=0,y=200,width=360,height=240)]:
            result = d.dispatch('act', dict(verb='frame', target=d.ids['mail'], expected=1, args=args))
            self.assertIn('error',result)
            self.assertEqual(before,d.snapshot())
        do(d,'edit',d.ids['decision'],part='status',before='Draft',after='Ready for review')
        self.assertTrue(assess('impossible',d)['passed'])

    def test_visibility_distinguishes_hidden_clipped_and_occluded(self):
        d = build('procurement')
        self.assertEqual(d.visibility(d.get(d.ids['mail'])),'hidden')
        self.assertEqual(d.visibility(d.get(d.ids['cost-window'])),'clipped')
        self.assertIn('occluded',d.visibility(d.get(d.ids['decision-window'])))
        do(d,'frame',d.ids['mail'],x=0,y=0,width=500,height=800)
        self.assertEqual(d.visibility(d.get(d.ids['mail'])),'fully-visible')

    def test_baseline_undo_counterexample(self):
        d = build('handoff')
        do(d,'tile',d.ids['planning'],items=[d.ids['p-risk'],d.ids['p-risk-alt']],columns=2)
        do(d,'create',d.ids['planning'],kind='note',title='Unrelated new note',parts=[dict(id='body',text='Keep me')])
        before = deepcopy(d.nodes)
        result = d.dispatch('act',dict(verb='undo',target='event-1',expected=0,args={}))
        self.assertIn('Undo conflicts',result['error'])
        self.assertEqual(before,d.nodes)


if __name__ == '__main__':
    unittest.main()
