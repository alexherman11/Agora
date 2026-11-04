"""Authenticated geometry reads share the WM engine and never mutate the world."""
import unittest
from test_painter import Painter, quoted, walk
from test_skeleton import post


class Tiling(unittest.TestCase):
    setUp = Painter.setUp
    tearDown = Painter.tearDown
    get = Painter.get
    do = Painter.do

    def test_both_compilers_preserve_sorted_landing_after_lane_move(self):
        from painter.arrangement import compile_view
        from kernel.tiling import preview
        source = self.do(self.alex, 'make kind=tiling-fixture title=source lane=Left priority=2')['made'][0]
        a = self.do(self.alex, 'make kind=tiling-fixture title=first lane=Right priority=1')['made'][0]
        b = self.do(self.alex, 'make kind=tiling-fixture title=tie lane=Right priority=2')['made'][0]
        c = self.do(self.alex, 'make kind=tiling-fixture title=last lane=Right priority=3')['made'][0]
        legacy = ('root : row\n'
                  '  left : column, of tag:tiling-fixture,prop:lane=Left as fixture, by priority, each card\n'
                  '  right : column, of tag:tiling-fixture,prop:lane=Right as fixture, by priority, each card\n'
                  'card : column, carry\n  title : text "$title"\n')
        component = legacy.replace('card : column, carry', 'card : column').replace('"$title"', '"$fixture.title"')
        self.do(self.alex, 'make kind=lens name=tiling-legacy text='+quoted(legacy))
        lens = self.do(self.alex, 'make kind=lens name=tiling-components painter=components text='+quoted(component))['made'][0]
        actor = self.k.actor_for(self.k.accounts['google:alex'])
        def readings():
            response = self.get('/api/scene?lens=tiling-legacy&view=painter', self.alex)
            self.assertIn('scene', response, response)
            sc = response['scene']
            old = [n['tiling_order'] for n in walk(sc) if 'tiling_order' in n]
            tree = compile_view(self.k, actor, lens)['rows'][0]['tree']
            def nodes(n):
                yield n
                for child in n['children']:
                    yield from nodes(child)
            new = [n['tiling_order'] for n in nodes(tree) if 'tiling_order' in n]
            return old, new
        before = readings()
        for orders in before:
            self.assertEqual(len(orders), 4)
            self.assertLess(orders[0]['tie'], orders[2]['tie'])
            out = preview(dict(start=[0,180,200,160], moving=[301,180,200,160],
                landing=[300,0,200,160], neighbours=[[300,y,200,160] for y in (0,180,360)],
                orders=orders, gap=20))
            self.assertTrue(out['allowed'])
            self.assertEqual(out['landing'], [300,180,200,160])
        self.do(self.alex, 'look '+source)
        self.do(self.alex, 'set '+source+' lane=Right')
        for old, new in zip(before, readings()):
            self.assertEqual(new, [old[1], old[0], old[2], old[3]])
        self.assertEqual([self.k.state.get(t, 'priority') for t in (a,source,b,c)], ['1','2','2','3'])

    def test_read_only_centre_crossing_route_and_rejections(self):
        settings = self.do(self.alex, 'make kind=wm-settings motion_ms=420')['made'][0]
        before = len(self.k.log.records)
        body = dict(start=[0,0,200,160], moving=[300,0,200,160],
                    landing=[300,0,200,160], neighbours=[[300,0,200,160]])
        code, out = post(self.url+'/api/tiling', body, token=self.alex)
        self.assertEqual(code,200,out)
        self.assertFalse(out['allowed'])
        self.assertEqual(out['motion_ms'],420)
        body['moving'][0] = 301
        code, out = post(self.url+'/api/tiling', body, token=self.alex)
        self.assertEqual(code,200)
        self.assertTrue(out['allowed'])
        code, _ = post(self.url+'/api/tiling', body)
        self.assertEqual(code,401)
        body['moving'][0] = 'bad'
        code, _ = post(self.url+'/api/tiling', body, token=self.alex)
        self.assertEqual(code,400)
        self.assertEqual(len(self.k.log.records),before)
        self.do(self.alex, 'look '+settings)
        self.do(self.alex, 'set '+settings+' motion_ms=180')
        body['moving'][0] = 301
        code, out = post(self.url+'/api/tiling', body, token=self.alex)
        self.assertEqual(out['motion_ms'],180)


if __name__ == '__main__':
    unittest.main()
