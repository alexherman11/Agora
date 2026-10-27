"""General kernel contracts found by the word-only board. No desktop or live world."""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kernel.kernel import Kernel, Tx
from kernel.painter import Facade
from test_painter import quoted, walk


@pytest.fixture
def world(tmp_path):
    k = Kernel(tmp_path / 'world', {'tag': 'mw', 'name': 'Words',
        'steward': {'account': 'alex', 'name': 'Alex'}, 'invites_counted_by': 'kernel',
        'invites': [{'code': 'x', 'uses': 5}], 'groups': [{'name': 'Private'}]})
    a = k.actor_for(k.accounts['alex'])
    person = k.join('bea', 'Bea', invite='x')['person']
    b = k.actor_for(person)
    return k, a, b


def say(k, actor, line, ok=True):
    out = k.run(actor, line)
    assert out['ok'] == ok, out
    return out


def edit(k, a, word, values):
    eid = k.find_entry(word)
    say(k, a, 'look ' + eid)
    return say(k, a, 'word-set ' + eid + ' ' + values)


def wait_for(test):
    end = time.monotonic() + 3
    while time.monotonic() < end:
        if test():
            return
        time.sleep(.01)
    assert test()


def test_steward_edits_are_fenced_atomic_and_undoable(world):
    k, a, b = world
    eid = k.find_entry('set')
    n = len(k.log.records)
    say(k, b, f'word-set {eid} undo=external', False)
    say(k, a, f'word-set {eid} undo=external', False)
    assert len(k.log.records) == n
    result = edit(k, a, 'set', 'undo=external help="Change a thing" aliases="editar"')
    assert k.state.get(eid, 'undo') == 'external'
    assert k.find_entry('editar') == eid
    say(k, a, 'undo ' + result['records'][0])
    assert k.state.get(eid, 'undo') == 'yes'
    assert k.find_entry('editar') is None
    for values in ('undo=maybe', 'help=""', 'may=everyone', 'from=module:evil', 'steps=post', 'sealed=perhaps'):
        before = k.state.snapshot(), len(k.log.records)
        say(k, a, f'word-set {eid} {values}', False)
        assert before == (k.state.snapshot(), len(k.log.records))
    edit(k, a, 'look', 'status=hidden may=nobody')
    say(k, a, 'look ' + a.person)  # the steward's recovery floor survives metadata edits
    say(k, b, 'look ' + b.person, False)


def test_translations_share_identity_help_permissions_and_undo(world):
    k, a, b = world
    eid = k.find_entry('set')
    edit(k, a, 'set', 'label.es=cambiar help.es="Cambiar los datos"')
    say(k, b, 'language es')
    bot = k.actor_for(b.person, 'helper')
    for actor in (b, bot):
        assert k.find_entry('cambiar') == eid
        assert say(k, actor, 'help cambiar')['text'].startswith('Cambiar los datos')
        assert 'cambiar' in say(k, actor, 'help all')['text']      # the full listing; bare help is a short first screen
    thing = say(k, b, 'make kind=note title=Before')['made'][0]
    say(k, bot, 'look ' + thing)
    result = say(k, bot, f'cambiar {thing} title=Después')
    assert k.log.records[-1]['parts'][0]['entry'] == eid
    assert k.log.records[-1]['for'] == b.person
    say(k, b, 'undo ' + result['records'][0])
    assert k.state.get(thing, 'title') == 'Before'
    other = k.find_entry('post')
    say(k, a, 'look ' + other)
    say(k, a, f'word-set {other} label.es=cambiar', False)
    assert len([e for e in k.entries() if k.state.get(e, 'label.es') == 'cambiar']) == 1


def test_saved_lines_keep_ids_after_alias_reuse_and_replay(world):
    k, a, _ = world
    eid = k.find_entry('set')
    edit(k, a, 'set', 'aliases=editar')
    verb = say(k, a, 'verb update takes="<id>" steps="editar $1 title=After" help="Update"')['made'][0]
    assert eid in k.state.get(verb, 'steps_bound')
    edit(k, a, 'set', 'aliases=')
    say(k, a, 'verb editar steps="post Wrong" help="A new meaning"')
    say(k, a, 'look ' + eid)
    say(k, a, f'word-rename {eid} to=change')
    thing = say(k, a, 'make kind=note title=Before')['made'][0]
    say(k, a, 'update ' + thing)
    assert k.state.get(thing, 'title') == 'After'
    assert not k.things('post')
    replay = Kernel(k.dir)
    assert replay.state.snapshot() == k.state.snapshot()
    say(replay, a, f'change {thing} title=Again', False)  # replay has no look marks
    say(replay, a, 'look ' + thing)
    say(replay, a, 'update ' + thing)
    assert replay.state.get(thing, 'title') == 'After'


def test_dotted_names_stay_with_the_implementing_module(world):
    k, a, _ = world
    verb = say(k, a, 'verb finish steps="post Done" help="Finish"')['made'][0]
    for line in (f'word-rename {verb} to=task.done', f'rename {verb} word=task.done',
                 f'word-set {verb} aliases=task.done', f'word-set {verb} label.es=task.hecho'):
        say(k, a, 'look ' + verb)
        say(k, a, line, False)
    module = say(k, a, 'module media run=' + quoted('["unused"]') + ' grants=""')['made'][0]
    k.on_offer(module, [{'word': 'media.play', 'kind': 'do', 'takes': '', 'help': 'Play', 'undo': 'external'}])
    eid = k.find_entry('media.play')
    assert k.state.get(eid, 'undo') == 'external'
    say(k, a, 'look ' + eid)
    say(k, a, f'word-rename {eid} to=other.play', False)
    say(k, a, f'word-rename {eid} to=media.toggle')
    assert k.state.get(eid, 'bound') == 'media.play'
    edit(k, a, 'media.toggle', 'undo=external label.es=reproducir')
    assert k.find_entry('reproducir') == eid


def test_external_entry_records_effect_even_if_answer_omits_flag(world):
    k, a, _ = world
    mid = say(k, a, 'module media run=' + quoted('["unused"]') + ' grants=""')['made'][0]
    k.on_offer(mid, [{'word': 'media.play', 'kind': 'do', 'help': 'Play', 'undo': 'external'}])
    class Module:
        def running(self, mid): return True
        def call(self, *args, **kw): return {'text': 'Pressed'}
        def deliver(self, happening): pass
        def reconcile(self): pass
        def done(self, *args): pass
    k.modules = Module()
    out = say(k, a, 'media.play')
    assert k.log.records[-1]['external'] is True
    say(k, a, 'undo ' + out['records'][0], False)
    say(k, a, 'verb play steps="media.play" help="Play through a composed word"')
    out = say(k, a, 'play')
    assert k.log.records[-1]['by'] == mid
    assert k.log.records[-1]['entry'] == k.find_entry('play')
    assert len([h for h in k.happenings if h.get('record') == int(out['records'][0][1:]) and h['word'] == 'play']) == 1
    say(k, a, 'undo ' + out['records'][0], False)
    say(k, a, 'verb play-and-note steps="media.play; make kind=note text=Played" help="Play and record"')
    out = say(k, a, 'play-and-note')
    assert k.log.records[-1]['external'] is True
    assert out['made'] and k.state.get(out['made'][0], 'text') == 'Played'
    say(k, a, 'undo ' + out['records'][0], False)


def test_composed_happening_and_kind_filter_survive_rename(world):
    k, a, _ = world
    eid = say(k, a, 'verb finish takes="<id>" steps="set $1 status=done" help="Finish"')['made'][0]
    rule = say(k, a, 'rule on=finish kind=task do="make kind=announcement about=$target"')['made'][0]
    assert k.state.get(rule, 'kind') == 'rule' and k.state.get(rule, 'of_kind') == 'task'
    say(k, a, f'word-rename {eid} to=complete')
    task = say(k, a, 'make kind=task')['made'][0]
    other = say(k, a, 'make kind=note')['made'][0]
    say(k, a, 'complete ' + other)
    say(k, a, 'complete ' + task)
    wait_for(lambda: len(k.things('announcement')) == 1)
    assert k.state.get(k.things('announcement')[0], 'about') == task
    own = [h for h in k.happenings if h.get('entry') == eid]
    assert len(own) == 2 and all(h['word'] == 'complete' for h in own)
    assert len([h for h in k.happenings if h['word'] == 'set' and h.get('target') == task]) == 1
    assert Kernel(k.dir).state.snapshot() == k.state.snapshot()


def test_history_lists_direct_edits_agent_and_undo_with_real_record_time(world):
    k, a, b = world
    t = say(k, b, 'make kind=task title=Before')['made'][0]
    bot = k.actor_for(b.person, 'helper')
    say(k, bot, 'look ' + t)
    result = say(k, bot, f'set {t} title=After')
    say(k, b, 'undo ' + result['records'][0])
    before = len(k.log.records)
    trail = say(k, a, 'history ' + t)['rows']
    assert len(k.log.records) == before
    assert [r['word'] for r in trail] == ['make', 'set', 'undo']
    assert trail[1]['by'] == 'agent for Bea'
    assert trail[1]['facts'] == [{'aspect': 'title', 'value': 'After'}]
    assert trail[-1]['facts'] == [{'aspect': 'title', 'value': 'Before'}]
    assert all(r['at'] == k.log.records[int(r['record'][1:]) - 1]['at'] for r in trail)


def test_history_filters_things_fields_old_private_values_and_seals(world):
    k, a, b = world
    private = say(k, a, 'make kind=note sees=me text=Hidden')['made'][0]
    say(k, b, 'history ' + private, False)
    post = say(k, a, 'post A public question')['made'][0]
    say(k, b, 'like ' + post)
    sealed = [r for r in say(k, a, 'history ' + post)['rows'] if r['sealed']]
    assert len(sealed) == 1
    assert sealed[0]['by'] == 'sealed' and sealed[0]['facts'] == []
    assert b.person not in json.dumps(sealed) and 'Bea' not in json.dumps(sealed)
    car = say(k, a, 'make kind=carpool seats=2')['made'][0]
    say(k, b, f'claim {car} phone=555-secret')
    assert '555-secret' in json.dumps(say(k, a, 'history ' + car)['rows'])
    c = k.actor_for(k.join('c', 'Chris', invite='x')['person'])
    assert '555-secret' not in json.dumps(say(k, c, 'history ' + car)['rows'])
    # A later public value cannot make the earlier private value public.
    tx = Tx(k)
    tx.part('publication', private, '')
    tx.set(private, 'sees', 'place')
    tx.set(private, 'text', 'Published')
    k._commit(tx, by=a.id, words='publication')
    assert 'Hidden' not in json.dumps(say(k, b, 'history ' + private)['rows'])
    assert 'Published' in json.dumps(say(k, b, 'history ' + private)['rows'])


def test_drop_checks_both_participants_and_their_read_aspects(world):
    k, a, _ = world
    facade = Facade(k)
    card = say(k, a, 'make kind=task lane=Backlog title=Card')['made'][0]
    lane = say(k, a, 'make kind=lane title=Now')['made'][0]
    def observation(t, field):
        sid = 's' + str(facade.num(t))
        return {'item': sid, 'rev': k.state.rev[t], 'reads': [[sid, k.state.rev[t], ['prop:' + field]]]}
    observed = {'carried': observation(card, 'lane'), 'receiver': observation(lane, 'title')}
    body = {'line': 'set $carried lane=Now', 'observed': observed}
    say(k, a, f'set {lane} title=Changed')
    before = len(k.log.records)
    assert 'stale' in facade.do(a, body)['error']
    assert k.state.get(card, 'lane') == 'Backlog' and len(k.log.records) == before
    observed['receiver'] = observation(lane, 'title')
    say(k, a, f'set {card} unread=Unrelated')
    assert facade.do(a, body)['error'] is None  # an unrelated field does not stale a drag
    before = len(k.log.records)
    assert 'stale' in facade.do(a, body)['error']
    assert len(k.log.records) == before
    assert facade.do(a, {'line': 'set $carried lane=Done'})['error']


def test_clock_dates_and_same_history_rows_are_available_to_lenses(world):
    k, a, _ = world
    k.clock = lambda: datetime(2030, 5, 6, 12, tzinfo=timezone.utc)
    t = say(k, a, 'make kind=task title=Date')['made'][0]
    made = k.log.records[-1]['at']
    k.clock = lambda: datetime(2030, 5, 7, 13, tzinfo=timezone.utc)
    say(k, a, f'set {t} title=Changed')
    changed = k.log.records[-1]['at']
    assert k.shown(a.person, t)['made'] == made
    assert k.shown(a.person, t)['changed'] == changed
    lens = ('root : column\n  today : text "$today"\n  tasks : column, of tag:task as task, each card\n'
            'card : column\n  dates : text "$made_at $changed_at"\n'
            '  trail : column, of history:$task.id as event, each event\n'
            'event : text "$word $at $changes"')
    say(k, a, 'make kind=lens name=dates text=' + quoted(lens))
    facade = Facade(k)
    scene = facade.scene(a.person, {'lens': 'dates', 'text': '1'})
    assert 'refused' not in scene, scene
    text = scene['text']
    assert '2030-05-07' in text and made in text and changed in text
    dates = next(node for node in walk(scene['scene']) if node.get('key', '').endswith('/dates'))
    assert made in dates['text'] and changed in dates['text'], dates
    assert 'title=Changed' in text
    for fact in ('made=pretend', 'changed=pretend', 'made_at=pretend', 'changed_at=pretend',
                 'steps_bound=pretend', 'do_bound=pretend'):
        say(k, a, f'set {t} {fact}', False)


def test_older_saved_lines_bind_before_dictionary_edits(world):
    k, a, _ = world
    edit(k, a, 'set', 'aliases=editar')
    eid = say(k, a, 'verb update takes="<id>" steps="editar $1 title=Kept" help="Update"')['made'][0]
    # An older world has only the authored text, with no bound representation.
    tx = Tx(k)
    tx.part('old-world-fixture', eid, '')
    tx.set(eid, 'steps_bound')
    k._commit(tx, by='kernel', words='old-world-fixture')
    edit(k, a, 'set', 'aliases=')
    say(k, a, 'verb editar steps="post Wrong" help="Different meaning"')
    t = say(k, a, 'make kind=task')['made'][0]
    say(k, a, 'update ' + t)
    assert k.state.get(t, 'title') == 'Kept'
    assert not k.things('post')
    assert Kernel(k.dir).state.snapshot() == k.state.snapshot()


def test_translations_and_bound_lines_travel_in_kits(world):
    k, a, _ = world
    group = k.things('group')[0]
    word = say(k, a, f'verb greet in={group} steps="make kind=note title=Hello" help="Greet"')['made'][0]
    say(k, a, 'look ' + word)
    say(k, a, f'word-set {word} label.es=saludar help.es="Crear una nota"')
    kit = say(k, a, 'kit ' + group)['made'][0]
    bundle = say(k, a, 'look ' + kit)['rows'][0]['bundle']
    facts = next(d['facts'] for d in bundle['definitions'] if d['id'] == word)
    assert facts['label.es'] == 'saludar' and facts['help.es'] == 'Crear una nota'
    assert k.find_entry('make') in facts['steps']
    invalid = json.loads(json.dumps(bundle))
    invalid['definitions'][0]['facts']['aliases'] = 'task.hidden'
    before = k.state.snapshot(), len(k.log.records)
    say(k, a, 'take in=' + k.place + ' bundle=' + quoted(json.dumps(invalid)), False)
    assert before == (k.state.snapshot(), len(k.log.records))
    copied = say(k, a, 'take ' + kit + ' in=' + k.place)['made']
    new = next(t for t in copied if k.state.get(t, 'kind') == 'word')
    assert k.find_entry('saludar') == new
    say(k, a, 'saludar')
    assert any(k.state.get(t, 'title') == 'Hello' for t in k.things('note'))
    say(k, a, 'verb pin2 steps="make kind=note title=Digits" help="A plain word with digits"')
    say(k, a, 'pin2')


def test_grant_adds_one_more_grant_and_undo_takes_it_back(world):
    k, a, b = world
    mid = say(k, a, 'module media run=' + quoted('["unused"]') + ' grants="rows"')['made'][0]
    say(k, b, 'grant ' + mid + ' words="look"', ok=False)          # stewards only
    out = say(k, a, 'grant ' + mid + ' words="look set" only=kind:note')
    g = out['made'][0]
    assert k.state.get(g, 'to') == mid and k.state.get(g, 'words') == 'look set'
    assert k.state.get(g, 'only') == 'kind:note'
    say(k, a, 'undo')
    assert k.state.get(g, 'to') is None
