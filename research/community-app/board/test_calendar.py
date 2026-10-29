"""Meetings & events opens a shared calendar: the world half. Scratch kernel only, no windows.

Alex adds an event the way the calendar's add form does (title, when, where, notes; no seats),
Bea sees it in board.events and RSVPs in one word, and Alex reads who is coming by name.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _probe():
    sys.path.insert(0, str(HERE))
    from proof import Proof, install, line
    f = Proof()
    try:
        ids = install(lambda x: f.say('Alex', x), lambda x: f.see('Alex', x))
        f.join('Bea')
        meetings = ids['channels']['Meetings & events']
        channel = next(r for r in f.see('Alex', 'rows board-channel')['rows'] if r['group'] == meetings)
        f.check('Meetings & events says it opens a calendar', channel.get('opens') == 'calendar' and channel.get('opens_label') == 'Calendar')
        f.check('other channels keep their conversations', all(not r.get('opens') for r in f.see('Alex', 'rows board-channel')['rows'] if r['group'] != meetings))

        # Exactly the line the lens gesture makes: no seats and no separate text.
        made = f.say('Alex', line('board.post', post_kind='event', **{'in': meetings}, title='Garden workday',
                                  start='2026-11-04T17:00:00Z', end='2026-11-04T19:00:00Z', location='Corner garden'))
        event = made['made'][0]
        shown = next(r for r in f.see('Alex', 'rows post')['rows'] if r['id'] == event)
        f.check('a calendar add needs no seats: the kind default fills them', shown.get('seats') in ('500', 500), shown.get('seats'))
        f.check('a title alone is the post text', shown.get('text') == 'Garden workday')
        f.check('the event is a world thing in the channel', meetings in shown.get('groups', []))
        f.check('history records who added it', any(r.get('word') in ('post', 'board.post') for r in f.see('Alex', 'history ' + event)['rows']))

        # Another member sees it; their RSVP is one word, by name, not id.
        rows = f.see('Bea', 'board.events in=' + meetings + ' around=2026-11-01')['rows']
        f.check('Bea sees Alex\'s event on the calendar reading', [r['id'] for r in rows] == [event])
        f.check('the reading names the host, not an id', rows[0]['host'] == 'Alex' and rows[0]['going'] == 0 and rows[0]['your_rsvp'] == '')
        f.see('Bea', 'look ' + event)
        f.say('Bea', 'board.rsvp ' + event + ' status=going')
        bea = f.see('Bea', 'board.events in=' + meetings)['rows'][0]
        alex = f.see('Alex', 'board.events in=' + meetings)['rows'][0]
        f.check('Bea\'s own RSVP reads back as going', bea['your_rsvp'] == 'going')
        f.check('Alex sees Bea coming, by name', alex['coming'] == 'Bea' and alex['going'] == 1 and alex['your_rsvp'] == '')
        f.see('Alex', 'look ' + event)
        f.say('Alex', 'board.rsvp ' + event + ' status=maybe')
        alex = f.see('Alex', 'board.events in=' + meetings)['rows'][0]
        f.check('maybe is counted apart from going', alex['maybe'] == 1 and alex['maybe_coming'] == 'Alex' and alex['going'] == 1)
        f.see('Bea', 'look ' + event)
        f.say('Bea', 'board.rsvp ' + event + ' status=maybe')
        f.check('changing your mind keeps one RSVP, one seat', len([r for r in f.see('Bea', 'rows board-rsvp')['rows'] if r.get('about') == event]) == 2
                and next(r for r in f.see('Alex', 'rows post')['rows'] if r['id'] == event)['seats_left'] == 498)

        # The window: around + weeks keep a long-lived channel's reading small.
        f.say('Alex', line('board.post', post_kind='event', **{'in': meetings}, title='Spring fair', start='2027-04-10T18:00:00Z'))
        f.check('events far from the day shown are left out', len(f.see('Alex', 'board.events in=' + meetings + ' around=2026-11-04')['rows']) == 1)
        f.check('…and appear when the calendar moves there', [r['title'] for r in f.see('Alex', 'board.events in=' + meetings + ' around=2027-04-01')['rows']] == ['Spring fair'])
        f.check('a bad day is refused plainly', not f.raw('Alex', 'board.events around=someday', 'see')['ok'])
        f.check('an explicit seats value still wins over the default', f.say('Alex', line('board.post', post_kind='event', **{'in': meetings}, title='Small supper',
                start='2026-11-06T02:00:00Z', seats='8'))['ok'] and any(r.get('seats') in ('8', 8) for r in f.see('Alex', 'rows post')['rows'] if r.get('title') == 'Small supper'))
        f.check('posts without a title still need text', not f.raw('Alex', line('board.post', post_kind='discussion', **{'in': meetings}))['ok'])

        # 'New since': per channel, only real news, and the oldest unseen thing is named.
        neighbours = ids['channels']['Neighbours']
        catch = lambda who, group: f.see(who, 'board.catch-up in=' + group)['rows']
        from datetime import timedelta

        def later():  # the proof clock stands still; each act gets its own minute
            f.at += timedelta(minutes=1)
        later()
        f.say('Alex', 'board.seen')
        f.check('after marking seen nothing is new in any channel', not catch('Alex', meetings) and not catch('Alex', neighbours))
        later()
        first = f.say('Bea', line('board.post', post_kind='discussion', title='Lost keys', text='Found a set of keys by the bench.', **{'in': neighbours}))['made'][0]
        later()
        f.say('Bea', line('board.post', post_kind='discussion', title='Tool library', text='Anyone want a tool library?', **{'in': neighbours}))
        rows = catch('Alex', neighbours)
        f.check('a neighbour\'s new conversation is new for Alex, in its own channel only', {r['id'] for r in rows if r['category'] == 'new'} >= {first} and not catch('Alex', meetings), catch('Alex', meetings))
        f.check('the oldest unseen is the first one posted', min(rows, key=lambda r: r['at'])['id'] == first, [(r['id'], r['at']) for r in rows])
        f.check('your own posts are never news to you', not [r for r in catch('Bea', neighbours) if r['category'] == 'new'])
        f.see('Alex', 'look ' + first)
        later()
        reply = f.say('Alex', line('board.reply', first, text='Mine! Thank you.'))['made'][0]
        later()
        f.say('Bea', 'board.seen')
        later()
        f.say('Alex', line('board.reply', first, text='On my way.'))
        busy = [r for r in catch('Bea', neighbours) if r['category'] == 'busy']
        f.check('a busy thread names its oldest unseen reply', len(busy) == 1 and busy[0]['first'] != reply and busy[0]['id'] == first, busy)
        later()
        meetings_news = f.say('Bea', line('board.post', post_kind='discussion', title='Agenda ideas', text='What should the November meeting cover?', **{'in': meetings}))['made'][0]
        later()
        f.say('Alex', 'board.seen in=' + neighbours)
        f.check('marking one channel seen clears only that channel', not catch('Alex', neighbours) and [r['id'] for r in catch('Alex', meetings)] == [meetings_news])
        f.check('the whole board still remembers the older marker', any(r['id'] == first for r in f.see('Alex', 'board.catch-up')['rows']))
        print('CALENDAR WORLD ' + json.dumps(dict(checks=f.checks)), flush=True)
    finally:
        f.close()


def _routing_probe():
    """A channel's opens=<name> picks one guarded part of the real board lens; a landed lens (asks & offers)
    drops in by name as a nested lens part. Scratch copy of the board lens only; the shipped one is untouched."""
    lab = HERE.parents[1] / 'kernel-lab'
    sys.path[:0] = [str(HERE), str(lab), str(lab / 'tests'), str(lab.parent / 'window-lab/kernel-desktop')]
    from proof import Proof, install, line
    from painter.arrangement import compile_view
    from painter.catalogue import cards
    from asks_install import NAME, VIEW
    from ui_install import upsert, install_ui, Q
    f = Proof()
    try:
        ids = install(lambda x: f.say('Alex', x), lambda x: f.see('Alex', x))
        f.join('Bea')

        class Door:
            say = staticmethod(lambda x: f.say('Alex', x))
            rows = staticmethod(lambda kind, **kv: f.say('Alex', 'rows ' + kind + ''.join(' ' + k + '=' + Q(v) for k, v in kv.items()))['rows'])
        door = Door()
        for card in cards():
            name = card.pop('name'); path = lab / 'components' / f'{name}.js'
            tid = upsert(door, 'component', name, **card, code=(path if path.exists() else lab / 'components/catalogue.js').read_text(encoding='utf-8'))
            door.say('look ' + tid); door.say('component ' + tid)
        install_ui(door)
        asks_channel = ids['channels']['Asks & offers']
        upsert(door, 'lens', NAME, title='Asks & offers', painter='components', text=(HERE / 'asks.lens').read_text(encoding='utf-8'),
               view=json.dumps(dict(VIEW, asks_channel=asks_channel)))
        board = (HERE / 'board.lens').read_text(encoding='utf-8')
        anchor = '    catchup : board-catchup,'
        assert anchor in board
        drop_in = ('    asks : lens, name ' + NAME + '\n      only when $view.opens = asks and $view.search = "" and $view.queue != yes\n')
        upsert(door, 'lens', 'routing-probe', title='Routing probe', painter='components', text=board.replace(anchor, drop_in + anchor, 1),
               view=next(r for r in door.rows('lens', name='seabright-board'))['view'])
        f.say('Bea', line('board.post', post_kind='ask', seats='1', text='Need a ladder on Saturday', **{'in': asks_channel}))
        bea = f.k.actor_for(f.people['Bea'])

        def tree(**view):
            return compile_view(f.k, bea, 'routing-probe', reader=lambda c: f.raw('Bea', c, 'see'), view=view)['rows'][0]['tree']

        def find(node, name):
            if node['name'] == name: return node
            return next((x for c in node['children'] if (x := find(c, name))), None)

        def text_of(node):
            return ' '.join([str(v) for v in node['settings'].values() if isinstance(v, str)] + [text_of(c) for c in node['children']])

        asks_view = tree(channel=asks_channel, opens='asks')
        f.check('opens=asks shows the nested asks lens and hides the feed and calendar',
                find(asks_view, 'asks') is not None and find(asks_view, 'feed') is None and find(asks_view, 'calendar') is None)
        f.check('the nested lens reads board.asks: the new ask is listed', 'Need a ladder on Saturday' in text_of(find(asks_view, 'asks')))
        meetings = tree(channel=ids['channels']['Meetings & events'], opens='calendar')
        f.check('opens=calendar shows the calendar, not asks or the feed',
                find(meetings, 'calendar') is not None and find(meetings, 'asks') is None and find(meetings, 'feed') is None)
        plain = tree(channel=ids['channels']['Neighbours'], opens='')
        f.check('no opens: the channel stays a feed', find(plain, 'feed') is not None and find(plain, 'asks') is None and find(plain, 'calendar') is None)
        f.check('the shipped board lens is unchanged by the probe', door.rows('lens', name='seabright-board')[0]['text'] == board)
        print('ROUTING ' + json.dumps(dict(checks=f.checks)), flush=True)
    finally:
        f.close()


def test_channel_routing_drops_in_a_lens_by_name():
    result = subprocess.run([sys.executable, '-B', __file__, '--routing-probe'], capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr


def test_calendar_world_contract():
    # Proof imports a module named install; keep it in its own interpreter like the board's other probes.
    result = subprocess.run([sys.executable, '-B', __file__, '--probe'], capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr


if __name__ == '__main__' and '--probe' in sys.argv:
    _probe()
if __name__ == '__main__' and '--routing-probe' in sys.argv:
    _routing_probe()
