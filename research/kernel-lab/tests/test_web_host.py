"""The host's personal geometry and words, tested at the same authenticated door.

Browser input and concurrent phone/laptop proof: proof/web_host.py.
"""
import json
import sys
import unittest
import urllib.error
import urllib.request
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(LAB / 'proof'), str(LAB), str(LAB / 'tests')]
from web_host import World
from hosts.web.layout import HELP, leaves
from kernel.kernel import Kernel
from test_skeleton import post


class WebHost(unittest.TestCase):
    def setUp(self):
        self.w = World()

    def tearDown(self):
        self.w.close()

    def refuse(self, line, token=None, saw=None):
        before = self.w.k.state.snapshot()
        count = len(self.w.k.log.records)
        code, out = post(self.w.url+'/do', {'line':line, **({'saw':saw} if saw is not None else {})}, token=token or self.w.maya)
        self.assertEqual(code, 200)
        self.assertFalse(out['ok'], out)
        self.assertEqual(before, self.w.k.state.snapshot())
        self.assertEqual(count, len(self.w.k.log.records))
        return out

    def test_default_is_a_read_not_shared_geometry(self):
        count = len(self.w.k.log.records)
        row = self.w.layout(self.w.maya)
        self.assertIsNone(row['id'])
        self.assertEqual([p['lens'] for p in leaves(row['layout']['tree'])], ['feed','council','help'])
        self.assertEqual(len(self.w.k.log.records), count)

    def test_words_are_dictionary_entries_with_help(self):
        for name in HELP:
            out = self.w.do(self.w.maya, 'help '+name, mode='see')
            self.assertIn(HELP[name], out['text'])

    def test_personal_layout_is_private_in_rows_look_and_scenes(self):
        self.w.do(self.w.maya, 'pane.move Feed to=Council')
        row = self.w.layout(self.w.maya)
        self.assertIsNone(self.w.k.shown(self.w.k.accounts['google:luis'], row['id']))
        self.assertEqual(self.w.do(self.w.luis, 'rows web-layout', mode='see')['rows'], [])
        self.refuse('look '+row['id'], self.w.luis)
        scene = json.dumps(self.w.get('/api/scene?lens=feed&view=painter',self.w.luis))
        self.assertNotIn('Private draft', scene)
        self.assertEqual(leaves(self.w.layout(self.w.luis)['layout']['tree'])[0]['lens'], 'feed')

    def test_split_close_move_focus_resize_and_undo(self):
        original = self.w.layout(self.w.maya)['layout']
        self.w.do(self.w.maya, 'pane.split Feed lens=Help axis=column')
        row = self.w.layout(self.w.maya)
        self.assertEqual(len(leaves(row['layout']['tree'])), 4)
        self.assertEqual(leaves(row['layout']['tree'])[1]['lens'], 'help')
        self.w.do(self.w.maya, 'pane.resize p4 ratio=70')
        self.assertEqual(self.w.layout(self.w.maya)['layout']['tree']['kids'][0]['ratio'], 70)
        self.w.do(self.w.maya, 'pane.focus Council')
        self.assertEqual(self.w.layout(self.w.maya)['layout']['active'], 'p2')
        self.w.do(self.w.maya, 'pane.move p4 to=Council')
        self.w.do(self.w.maya, 'pane.close p4')
        self.assertEqual(len(leaves(self.w.layout(self.w.maya)['layout']['tree'])), 3)
        self.w.do(self.w.maya, 'undo')
        self.assertEqual(len(leaves(self.w.layout(self.w.maya)['layout']['tree'])), 4)
        self.assertNotEqual(original, self.w.layout(self.w.maya)['layout'])

    def test_stale_tab_cannot_overwrite_layout(self):
        self.w.do(self.w.maya, 'pane.focus Feed')
        old = self.w.layout(self.w.maya)
        self.w.do(self.w.maya, 'pane.move Feed to=Help')
        out = self.refuse('pane.close Council', saw={old['id']: old['rev']})
        self.assertIn('stale', out['text'])

    def test_bad_words_refuse_atomically_and_last_pane_stays(self):
        for line in ['pane.split Feed lens=missing', 'pane.split Feed lens=help axis=diagonal',
                     'pane.close Missing', 'pane.move Feed to=Missing', 'pane.resize Feed ratio=no',
                     'pane.resize Feed ratio=91', 'pane.resize Feed ratio=50 at=9']:
            self.refuse(line)
        self.w.do(self.w.maya, 'pane.close Council')
        self.w.do(self.w.maya, 'pane.close Help')
        self.refuse('pane.close Feed')

    def test_hidden_lens_cannot_be_opened(self):
        self.w.do('dana', 'make kind=lens name=secret sees=me text="root : text hidden"')
        self.refuse('pane.split Feed lens=secret')

    def test_layout_is_kernel_owned_and_cannot_be_forged(self):
        self.refuse('make kind=web-layout owner='+self.w.person)
        self.w.do(self.w.maya, 'pane.focus Council')
        row = self.w.layout(self.w.maya)
        self.refuse('set '+row['id']+' layout=broken')

    def test_replay_preserves_layout_and_private_visibility(self):
        self.w.do(self.w.maya, 'pane.move Feed to=Council')
        before = self.w.layout(self.w.maya)
        restored = Kernel(self.w.temp.name)
        self.assertEqual(restored.state.snapshot(), self.w.k.state.snapshot())
        self.assertEqual(restored.state.get(before['id'], 'layout'), before['layout'])
        self.assertIsNone(restored.shown(restored.accounts['google:luis'], before['id']))

    def test_host_assets_routes_authentication_and_origin(self):
        for path, fragment in [('/web/', b'host.js'),('/web/host.js',b'/lens.html'),('/web/host.css',b'600px')]:
            with urllib.request.urlopen(self.w.url+path) as r:
                self.assertEqual(r.status,200)
                self.assertIn(fragment, r.read())
        for path in ['/web/../layout.py','/web/layout.py']:
            with self.assertRaises(urllib.error.HTTPError):
                urllib.request.urlopen(self.w.url+path)
        self.assertEqual(post(self.w.url+'/do', {'line':'pane.close Feed'})[0], 401)
        self.assertEqual(post(self.w.url+'/do', {'line':'pane.close Feed'}, token=self.w.maya,
                              headers={'Origin':'https://elsewhere.invalid'})[0], 403)

    def test_private_layout_happenings_do_not_reach_another_neighbour(self):
        self.w.do(self.w.maya, 'pane.focus Council')
        self.w.do(self.w.maya, 'pane.move Feed to=Help')
        happenings = [h for h in self.w.k.happenings if h.get('word','').startswith('pane.')]
        self.assertEqual(len(happenings), 2)
        for h in happenings:
            self.assertTrue(self.w.k.may_hear(self.w.person,h))
            self.assertFalse(self.w.k.may_hear(self.w.k.accounts['google:luis'],h))


if __name__ == '__main__':
    unittest.main()
