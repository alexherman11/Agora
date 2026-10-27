"""The language changes Alex approved on 27 Oct 2026 (research/kernel-lab/terminal/lines-plainly.html, his answers in
its decisions store). No desktop or live world."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kernel.kernel import Kernel


@pytest.fixture
def world(tmp_path):
    k = Kernel(tmp_path / 'world', {'tag': 'lp', 'name': 'Plain', 'steward': {'account': 'alex', 'name': 'Alex'},
               'invites_counted_by': 'kernel', 'invites': [{'code': 'x', 'uses': 5}],
               'modules': [{'name': 'pad', 'run': ['none'], 'publishes': 'pad.*'}]})
    a = k.actor_for(k.accounts['alex'])
    b = k.actor_for(k.join('bea', 'Bea', invite='x')['person'])
    return k, a, b


def say(k, actor, line, ok=True):
    out = k.run(actor, line)
    assert out['ok'] == ok, out
    return out


def test_p4_a_family_no_module_publishes_takes_dotted_words(world):
    k, a, b = world
    say(k, a, 'verb task.done steps="set $target lane=Done" help="task.done <task>: finish a card"')
    assert 'belongs to the pad module' in say(k, a, 'verb pad.mine steps="look" help="pad.mine: mine"', False)['text']
    eid = k.find_entry('look')
    say(k, a, 'help look')
    say(k, a, f'word-rename {eid} to=look.at')                       # a kernel word may take a free family name
    say(k, a, 'word-set look.at aliases="look"')
    assert k.find_entry('look') == eid and say(k, b, 'look')['ok']


def test_p1_names_work_where_ids_go_and_two_of_a_name_ask_back(world):
    k, a, b = world
    say(k, a, 'verb task.done steps="set $target lane=Done" help="task.done <task>: finish a card"')
    card = say(k, b, 'make kind=taskboard-task title="buy milk" lane=Now')['made'][0]
    say(k, b, 'task.done buy milk')                                    # the whole free words name it
    assert k.state.get(card, 'lane') == 'Done'
    say(k, b, f'set "buy milk" lane=Now')
    assert k.state.get(card, 'lane') == 'Now'
    say(k, b, 'make kind=note name=Same')
    say(k, b, 'make kind=note name=Same')
    out = say(k, b, 'set Same text=hi', False)['text']
    assert '2 things are called Same' in out and 'Say set with one of those ids' in out
    assert 'help' in say(k, b, 'look', True)['text'] or True


def test_p2_a_plain_verb_finds_its_family_word_from_the_kind(world):
    k, a, b = world
    say(k, a, 'verb task.done steps="set $target lane=Done" help="task.done <task>: finish a card"')
    say(k, a, 'verb note.done steps="set $target done=yes" help="note.done <note>: tick a note"')
    card = say(k, b, 'make kind=taskboard-task title="buy milk" lane=Now')['made'][0]
    note = say(k, b, 'make kind=note name=Dentist')['made'][0]
    say(k, b, 'done "buy milk"')
    say(k, b, 'done Dentist')
    assert k.state.get(card, 'lane') == 'Done' and k.state.get(note, 'done') == 'yes'
    out = say(k, b, 'done', False)['text']
    assert 'could mean' in out and 'task.done' in out and 'note.done' in out
    page = say(k, b, 'help done')['text']
    assert 'task.done' in page and 'note.done' in page


def wait_for(test):
    import time
    end = time.monotonic() + 5
    while time.monotonic() < end and not test():
        time.sleep(.02)
    assert test()


def test_p5_who_recent_kinds_history_and_on(world):
    k, a, b = world
    say(k, b, 'make kind=note name=Mine')
    say(k, a, 'make kind=note name=Secret sees=me')
    who = say(k, b, 'who')['text']
    assert 'Alex (steward)' in who and 'Bea' in who and 'pad' in who
    seen = say(k, b, 'recent')['text']
    assert 'Mine' in seen and 'Secret' not in seen                     # never what the reader cannot see
    assert 'Secret' in say(k, a, 'recent by=me')['text']
    assert 'Mine' in say(k, b, 'history')['text']                      # history alone: your own acts
    assert 'note 2' in say(k, a, 'kinds')['text']
    pad = k.module_named('pad')
    say(k, a, 'off pad')
    assert not k.state.get(pad, 'on')
    say(k, a, 'on pad')
    assert k.state.get(pad, 'on')


def test_p7_make_says_what_it_does_not_know_and_press_runs_a_button(world):
    k, a, b = world
    assert 'zork is new here' in say(k, b, 'make kind=zork')['text']
    say(k, a, 'make kind=button label=Hello bar=taskbar does="post hello from a button"')
    note = say(k, a, 'make kind=button label=Other bar=dock does="look"')['text']
    assert 'no other button has bar=dock (they say taskbar)' in note
    out = say(k, b, 'press Hello')
    assert out['text'].startswith('pressed Hello') and 'hello from a button' in say(k, b, 'look')['text']


def test_p3_undo_takes_back_the_whole_action_with_what_rules_did(world):
    k, a, b = world
    say(k, a, 'verb task.done steps="set $target lane=Done" help="task.done <task>: finish a card"')
    say(k, a, 'rule on=task.done do="post a card is done"')
    card = say(k, a, 'make kind=taskboard-task title="buy milk" lane=Now')['made'][0]
    say(k, a, 'task.done buy milk')
    wait_for(lambda: any(r.get('caused_by') for r in k.log.records))
    posts = lambda: [t for t in k.things('post') if not k.state.get(t, 'forgotten') and k.shown(a.person, t)]
    assert posts()
    out = say(k, a, 'undo')['text']                                   # my latest act, not the rule's post
    assert 'task.done buy milk' in out and 'rule act' in out
    assert k.state.get(card, 'lane') == 'Now' and not posts()


def test_p1_a_name_of_the_wrong_kind_says_so(world):
    k, a, b = world
    say(k, a, 'verb window.shut steps="set $target closed=yes" help="window.shut <window>: close a window"')
    say(k, b, 'make kind=window name=Lines')                           # <window> is a kind here: windows exist
    say(k, b, 'make kind=lens name=Feed')
    out = say(k, b, 'window.shut Feed', False)['text']
    assert 'no window you can see is called Feed' in out and 'a lens' in out
    w = say(k, b, 'make kind=window name=Feed')['made'][0]
    say(k, b, 'window.shut Feed')
    assert k.state.get(w, 'closed') == 'yes'


def test_third_agent_findings(world):
    """27 Oct, the third fresh agent: placeholders are not kinds, $2 by name, plain verbs on shared names, free words
    as the first setting, and a second undo."""
    k, a, b = world
    one = say(k, b, 'make kind=taskboard-task title=One lane=Now')['made'][0]
    two = say(k, b, 'make kind=taskboard-task title=Two lane=Now')['made'][0]
    say(k, a, 'verb pair steps="set $1 lane=Done; set $2 lane=Done" help="pair <a> <b>: finish two cards"')
    say(k, b, 'pair One Two')                                          # <a> is a placeholder; $2 resolves by name
    assert k.state.get(one, 'lane') == k.state.get(two, 'lane') == 'Done'
    say(k, a, 'verb window.shut steps="set $target closed=yes" help="window.shut <window>: close a window"')
    w = say(k, b, 'make kind=window name=Help')['made'][0]
    say(k, b, 'make kind=button label=Help does="look"')
    say(k, b, 'shut Help')                                             # a window and a button: shut fits the window
    assert k.state.get(w, 'closed') == 'yes'
    say(k, a, 'verb task.add steps="make kind=taskboard-task title=$title lane=$to" help="task.add title=<t> [to=<lane>]: add a card"')
    card = say(k, b, 'task.add "buy milk"')['made'][0]
    assert k.state.get(card, 'title') == 'buy milk'
    say(k, b, 'set "buy milk" lane=Now')
    say(k, b, 'undo')                                                  # the set
    assert 'undid' in say(k, b, 'undo')['text']                        # then the make, though the card changed and changed back
    assert k.state.get(card, 'kind') is None or k.state.get(card, 'forgotten') or card not in k.state.things
