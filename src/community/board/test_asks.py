"""Asks & offers lens: nesting in the painter, and the lens over a real board world. Hidden; no windows."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1] / 'agora'
sys.path[:0] = [str(LAB)]
from kernel.kernel import Kernel, Refused
from painter.arrangement import compile_view


def Q(value): return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"') + '"'


@pytest.fixture
def world(tmp_path):
    k = Kernel(tmp_path / 'world', dict(tag='ak', name='Asks nesting', steward=dict(account='alex', name='Alex'),
                                       invites_counted_by='kernel', invites=[dict(code='x', uses=3)]))
    a = k.actor_for(k.accounts['alex'])
    b = k.actor_for(k.join('bea', 'Bea', invite='x')['person'])
    def say(actor, command):
        out = k.run(actor, command); assert out['ok'], out; return out
    inner = 'root : column, label "Inner"\n  items : column, of tag:post, prop:side=$view.side as p, each item\nitem : text "$p.text"'
    say(a, 'make kind=lens name=inner painter=components view=' + Q(json.dumps(dict(side='ask', channel='inner-default'))) + ' text=' + Q(inner))
    say(a, 'make kind=lens name=host painter=components view=' + Q(json.dumps(dict(channel='host'))) + ' text='
        + Q('root : column\n  title : text "Board"\n  asks : lens, name inner\n  hidden : lens, name inner, only when $view.channel = never'))
    say(a, 'post text="Need a ladder" side=ask'); say(a, 'post text="Spare soup" side=offer')
    return k, a, b, say


def find(node, name):
    if node['name'] == name: return node
    return next((x for c in node['children'] if (x := find(c, name))), None)


def texts(node): return [c['settings'].get('text') for c in node['children']]


def test_lens_part_paints_another_lens_in_place_with_its_own_templates_and_defaults(world):
    k, a, b, say = world
    alone = compile_view(k, b, 'inner')['rows'][0]
    nested = compile_view(k, b, 'host')['rows'][0]
    asks = find(nested['tree'], 'asks')
    assert asks and asks['path'] == 'root/asks' and find(nested['tree'], 'hidden') is None
    assert texts(find(asks, 'items')) == texts(find(alone['tree'], 'items')) == ['Need a ladder']
    # the nested lens fills a missing view key; the host's own key wins
    assert nested['view']['side'] == 'ask' and nested['view']['channel'] == 'host'
    assert compile_view(k, b, 'host', view=dict(side='offer'))['rows'][0]['tree']['children'][1]['children'][0]['children'][0]['settings']['text'] == 'Spare soup'


def test_personal_views_and_styles_reach_the_nested_lens(world):
    k, a, b, say = world
    say(b, 'personal-view host asks.label=Mine')
    say(b, 'personal-view inner view.side=offer')
    say(a, 'make kind=part-style lens=inner target=tokens accent=#111111 ink=#222222')
    say(a, 'make kind=part-style lens=host target=tokens accent=#333333')
    out = compile_view(k, b, 'host')['rows'][0]
    asks = find(out['tree'], 'asks')
    assert asks['settings']['label'] == 'Mine'
    assert texts(find(asks, 'items')) == ['Spare soup']
    assert out['tokens']['accent'] == '#333333' and out['tokens']['ink'] == '#222222'
    # Alex's view is not Bea's
    assert compile_view(k, a, 'host')['rows'][0]['tree']['children'][1]['settings'].get('label') == 'Inner'
    say(b, 'personal-view inner text=' + Q('root : column\n  only : text "Bea arranged this"'))
    assert texts(find(compile_view(k, b, 'host')['rows'][0]['tree'], 'asks')) == ['Bea arranged this']


def test_missing_hidden_and_cyclic_lens_parts_refuse(world):
    k, a, b, say = world
    say(a, 'make kind=lens name=loop painter=components text=' + Q('root : column\n  again : lens, name loop'))
    with pytest.raises(Refused, match='cyclic'): compile_view(k, b, 'loop')
    say(a, 'make kind=lens name=gone painter=components text=' + Q('root : column\n  x : lens, name nowhere'))
    with pytest.raises(Refused, match='no visible component lens'): compile_view(k, b, 'gone')
    say(a, 'make kind=lens name=secret painter=components sees=me text=' + Q('root : text "SECRET"'))
    say(a, 'make kind=lens name=peek painter=components text=' + Q('root : column\n  x : lens, name secret'))
    assert compile_view(k, a, 'peek')['rows'][0]['tree']['children'][0]['settings']['text'] == 'SECRET'
    with pytest.raises(Refused): compile_view(k, b, 'peek')


def _board_probe():
    """The real lens over a board world with its module processes: standalone, nested, and each gesture line."""
    sys.path[:0] = [str(HERE), str(LAB / 'tests'), str(LAB.parent / 'desktop/kernel-desktop')]
    from proof import Proof, install, line
    from painter.arrangement import resolve_line
    from painter.catalogue import cards
    from asks_install import NAME, VIEW
    from ui_install import upsert
    f = Proof()
    try:
        ids = install(lambda x: f.say('Alex', x), lambda x: f.see('Alex', x))
        f.join('Maya'); f.join('Sam')
        class Door:
            say = staticmethod(lambda x: f.say('Alex', x))
            rows = staticmethod(lambda kind, **kv: f.say('Alex', 'rows ' + kind + ''.join(' ' + k + '=' + Q(v) for k, v in kv.items()))['rows'])
        door = Door()
        for card in cards():
            name = card.pop('name'); path = LAB / 'components' / f'{name}.js'
            tid = upsert(door, 'component', name, **card, code=(path if path.exists() else LAB / 'components/catalogue.js').read_text(encoding='utf-8'))
            door.say('look ' + tid); door.say('component ' + tid)
        channel = ids['channels']['Asks & offers']
        upsert(door, 'lens', NAME, title='Asks & offers', painter='components', text=(HERE / 'asks.lens').read_text(encoding='utf-8'),
               view=json.dumps(dict(VIEW, asks_channel=channel)))
        upsert(door, 'lens', 'probe-board', painter='components', view=json.dumps(dict(channel='')),
               text='root : column\n  feed : text "feed"\n  asks : lens, name ' + NAME)
        person = {n: f.people[n] for n in ('Maya', 'Sam')}
        actor = lambda who: f.k.actor_for(f.k.accounts['alex'] if who == 'Alex' else person[who])
        plan = lambda who, lens=NAME: compile_view(f.k, actor(who), lens, reader=lambda c: f.raw(who, c, 'see'), view={})['rows'][0]
        def gesture(node, event, **values):
            g = next(g for g in node['gestures'] if g['event'] == event)
            return resolve_line(g['line'], dict(g['env'], **values))
        def items(tree): return find(tree, 'entries')['children']
        # add one: the input's own gesture line posts an ask into the Asks & offers channel
        root = plan('Maya')['tree']
        assert find(root, 'heading')['settings']['text'] == 'Find help or share something'
        assert find(root, 'ask')['settings']['commit'] == 'submit'
        assert not any(g['event'] == 'change' for g in find(root, 'ask')['gestures'])
        f.say('Maya', gesture(find(root, 'ask'), 'submit', value='Need a hand moving a sofa'))
        f.at = f.at.replace(minute=5)
        f.say('Sam', gesture(find(plan('Sam')['tree'], 'offer'), 'submit', value='Spare "good" soup'))
        reading = f.see('Sam', 'board.asks')['rows']
        assert [r['what'] for r in reading] == ['Spare "good" soup', 'Need a hand moving a sofa'], reading
        assert all(r['status'] == 'open' and channel in r['groups'] for r in reading)
        # who/what/when/status, and the one-click line, from Sam's side
        sam = items(plan('Sam')['tree'])
        sofa = next(i for i in sam if find(i, 'what')['settings']['value'] == 'Need a hand moving a sofa')
        assert find(sofa, 'who')['settings']['label'] == 'Maya' and find(sofa, 'status')['settings']['label'] == 'Open'
        assert find(sofa, 'when')['formats'] == {'value': 'short-relative'} and find(sofa, 'when')['settings']['value']
        assert find(sofa, 'link')['settings']['label'] == 'I can help' and find(sofa, 'done') is None
        soup = next(i for i in sam if i is not sofa)
        assert find(soup, 'link') is None and find(soup, 'done')  # own offer: no "I need this", but may mark done
        f.say('Sam', gesture(find(sofa, 'link'), 'press'))
        maya = items(plan('Maya')['tree'])
        sofa = next(i for i in maya if find(i, 'side')['settings']['label'] == 'Ask')
        assert find(sofa, 'status')['settings']['label'] == 'Matched' and find(sofa, 'linked')['settings']['value'] == 'Sam'
        assert find(sofa, 'link') is None  # her own ask
        soup = next(i for i in maya if i is not sofa)
        assert find(soup, 'link')['settings']['label'] == 'I need this'
        f.say('Maya', gesture(find(soup, 'link'), 'press'))
        # one seat: once matched, nobody else is offered the button
        assert all(find(i, 'link') is None for i in items(plan('Alex')['tree']))
        f.say('Maya', gesture(find(sofa, 'done'), 'press'))
        assert [r['status'] for r in f.see('Alex', 'board.asks status=all')['rows']] == ['matched', 'done']
        assert len(items(plan('Alex')['tree'])) == 1  # default view shows active ones only
        # nested inside a board: the same parts, the board's own view keys untouched
        nested = plan('Maya', 'probe-board')
        assert len(items(find(nested['tree'], 'asks'))) == 1 and nested['view']['asks_channel'] == channel
        # personal view: Sam keeps only offers, without changing the shared lens
        f.say('Sam', 'personal-view ' + NAME + ' view.asks_side=ask view.asks_status=all')
        assert [find(i, 'status')['settings']['label'] for i in items(plan('Sam')['tree'])] == ['Done']
        assert len(items(plan('Maya')['tree'])) == 1
        for bad in ('side=both', 'status=later'):
            assert not f.raw('Sam', 'board.asks ' + bad, 'see')['ok']
        # the installer: same lens, its own tokens, a widget that is granted but never opened
        from asks_install import install_asks, GRANTS
        made = install_asks(door)
        lens = door.rows('lens', name=NAME)[0]
        assert json.loads(lens['view'])['asks_channel'] == channel and lens['id'] == made['lens']
        assert door.rows('part-style', name=NAME + '-theme')[0]['accent'] == '#315f52'
        assert any(g.get('words') == GRANTS for g in door.rows('grant', to=made['widget']))
        assert install_asks(door) == made  # idempotent
        print('ASKS PROBE OK')
    finally: f.close()


def test_asks_lens_over_a_real_board_world():
    # Like test_polish: the board proof world runs in its own interpreter (other suites have modules named install).
    pinned = sys.executable  # the pinned interpreter running this suite
    result = subprocess.run([str(pinned), '-B', __file__, '--asks-probe'], capture_output=True, text=True, timeout=120)
    assert result.returncode == 0 and 'ASKS PROBE OK' in result.stdout, result.stdout + result.stderr


if __name__ == '__main__' and '--asks-probe' in sys.argv: _board_probe()
