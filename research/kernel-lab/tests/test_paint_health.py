"""Paint health is screen state (Alex, 26 Oct: "visual state should not live in the world").

A painter's failures and quarantine are kept in the kernel process's memory, never in the log; turning a part off is the
viewer's own private preference; old paint-report things go in one steward act (paint-clear). Builder draft, 26 Oct 2026.
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))

from kernel.kernel import Kernel, Tx          # noqa: E402
from kernel.inpage import Principal            # noqa: E402


def Q(text):
    return '"' + str(text).replace('\\', '\\\\').replace('"', '\\"') + '"'


class PaintHealth(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix='paint-health-')
        self.k = k = Kernel(self.dir, {'tag': 'ph', 'name': 'Paint health', 'steward': {'account': 'test:alex', 'name': 'Alex'}})
        self.alex = k.actor_for(k.accounts['test:alex'])
        self.member = k.join('test:maya', 'Maya', invite={'admitted': True})['person']
        self.say('make kind=component name=chip code=' + Q("export default {mount(api){return api.part('body','span',{},'chip')}}")
                 + ' settings="{}" parts=' + Q('{"body":{}}'))
        chip = self.k.things('component')[-1]
        self.say('look ' + chip); self.say('component ' + chip)
        self.lens = self.say('make kind=lens name=bar painter=components text=' + Q('root : column\n  clock : chip\n  battery : chip'))['made'][0]
        self.widget = self.say('make kind=widget name=bar code="//" component_lens=bar')['made'][0]
        self.say('look ' + self.widget)
        self.say('widget ' + self.widget + ' grants="window.surface look-view component-health component-action"')
        self.painter = Principal(k, self.widget, self.alex, 'test')

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def say(self, line, actor=None):
        out = self.k.run(actor or self.alex, line)
        self.assertTrue(out['ok'], out)
        return out

    def report(self, path, health='stopped', error='weather service missing'):
        return self.painter.run('component-health ' + self.lens + ' data=' + Q(json.dumps([dict(path=path, health=health, last_error=error, elapsed_ms=3)])))

    def part(self, name, actor=None):
        from painter.arrangement import compile_view
        plan = compile_view(self.k, actor or self.alex, self.lens)['rows'][0]
        return next(p for p in plan['parts'] if p['name'] == name), plan

    def test_failures_are_kept_on_the_screen_not_in_the_world(self):
        n, happened = len(self.k.log.records), len(self.k.happenings)
        self.assertTrue(self.report('root/clock')['ok'])
        self.assertTrue(self.report('root/clock')['ok'])
        self.assertEqual(len(self.k.log.records), n, 'no record')
        self.assertEqual(len(self.k.happenings), happened, 'no happening')
        self.assertEqual(self.k.things('paint-report'), [], 'no thing')
        part, _ = self.part('clock')
        self.assertEqual(part['health']['health'], 'stopped')
        self.assertTrue(part['health']['quarantined'], 'two failures quarantine, locally')
        self.assertNotIn('painted', part['health'])
        maya = self.k.actor_for(self.member)
        self.assertNotIn('weather service missing', json.dumps(self.part('clock', maya)[0]), 'private to the viewer')
        # a repeated slot (api.child with a key) reports against the slot it repeats
        self.assertTrue(self.report('root/battery#app:lines')['ok'])
        self.assertFalse(self.report('root/elsewhere')['ok'])
        # a restart forgets screen state
        again = Kernel(self.dir)
        from painter.arrangement import compile_view
        plan = compile_view(again, again.actor_for(again.accounts['test:alex']), self.lens)['rows'][0]
        self.assertEqual(next(p for p in plan['parts'] if p['name'] == 'clock')['health']['health'], 'unobserved')

    def test_turn_it_off_is_a_private_preference_and_retry_turns_it_on(self):
        self.report('root/battery')
        n = len(self.k.log.records)
        off = self.painter.run('component-action ' + self.lens + ' path=root/battery action=off')
        self.assertTrue(off['ok'], off)
        self.assertEqual(len(self.k.log.records), n + 1, 'off is one recorded act')
        prefs = [p for p in self.k.things('view-preference') if self.k.state.get(p, 'battery.enabled') == 'no']
        self.assertEqual(len(prefs), 1)
        self.assertEqual(self.k.state.get(prefs[0], 'sees'), 'person:' + self.alex.person)
        _, plan = self.part('battery')
        node = next(c for c in plan['tree']['children'] if c['name'] == 'battery')
        self.assertTrue(node['disabled'])
        maya = self.k.actor_for(self.member)
        self.assertFalse(next(c for c in self.part('battery', maya)[1]['tree']['children'] if c['name'] == 'battery')['disabled'])
        self.assertTrue(self.painter.run('component-action ' + self.lens + ' path=root/battery action=retry')['ok'])
        self.assertFalse(next(c for c in self.part('battery')[1]['tree']['children'] if c['name'] == 'battery')['disabled'])
        self.assertTrue(self.painter.run('component-action ' + self.lens + ' path=root/battery action=off')['ok'])
        self.say('undo')
        self.assertFalse(next(c for c in self.part('battery')[1]['tree']['children'] if c['name'] == 'battery')['disabled'], 'undo turns it on')

    def test_clear_is_steward_only_and_local(self):
        self.report('root/clock'); self.report('root/clock')
        n = len(self.k.log.records)
        self.assertTrue(self.painter.run('component-action ' + self.lens + ' path=root/clock action=clear')['ok'])
        self.assertEqual(len(self.k.log.records), n)
        self.assertFalse(self.part('clock')[0]['health']['quarantined'])

    def test_paint_clear_forgets_old_reports_in_one_act(self):
        with self.k.lock:
            tx = Tx(self.k)
            tx.part('legacy', None, 'old paint reports, as the painter wrote them before 26 Oct')
            for i in range(313):
                t = tx.mint()
                for key, value in dict(kind='paint-report', viewer=self.alex.person, lens=self.lens, path=f'root/p{i}',
                                       painted=[{'text': 'secret painted text'}], sees='person:' + self.alex.person).items():
                    tx.set(t, key, value)
            self.k._commit(tx, by='kernel', words='legacy paint reports')
        refused = self.k.run(self.k.actor_for(self.member), 'paint-clear')
        self.assertFalse(refused['ok'], 'stewards only')
        n = len(self.k.log.records)
        out = self.say('paint-clear')
        self.assertIn('313 old paint reports', out['text'])
        self.assertEqual(len(self.k.log.records), n + 1, 'one record')
        self.assertTrue(all(self.k.state.get(t, 'forgotten') for t in self.k.things('paint-report')))
        self.assertEqual(self.say('rows paint-report')['rows'], [])
        self.assertIn('no paint reports left', self.say('paint-clear')['text'])
        self.say('undo r' + str(n + 1))
        self.assertEqual(sum(1 for t in self.k.things('paint-report') if not self.k.state.get(t, 'forgotten')), 313, 'undo brings them back')


if __name__ == '__main__':
    unittest.main()
