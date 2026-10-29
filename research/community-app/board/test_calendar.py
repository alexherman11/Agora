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


def test_calendar_world_contract():
    # Proof imports a module named install; keep it in its own interpreter like the board's other probes.
    result = subprocess.run([sys.executable, '-B', __file__, '--probe'], capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr


if __name__ == '__main__' and '--probe' in sys.argv:
    _probe()
