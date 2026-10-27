"""Help that teaches (epic: a terminal that teaches itself, 26 Oct 2026). Found by a naive agent's friction study:
research/kernel-lab/terminal/FRICTION-STUDY.md. No desktop or live world."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kernel.kernel import Kernel


@pytest.fixture
def world(tmp_path):
    k = Kernel(tmp_path / 'world', {'tag': 'hw', 'name': 'Helpful',
        'steward': {'account': 'alex', 'name': 'Alex'}, 'invites_counted_by': 'kernel',
        'invites': [{'code': 'x', 'uses': 5}]})
    a = k.actor_for(k.accounts['alex'])
    b = k.actor_for(k.join('bea', 'Bea', invite='x')['person'])
    return k, a, b


def say(k, actor, line, ok=True):
    out = k.run(actor, line)
    assert out['ok'] == ok, out
    return out


def test_bare_help_is_a_short_first_screen_and_rows_stay_whole(world):
    k, a, b = world
    out = say(k, b, 'help')
    lines = out['text'].splitlines()
    assert len(lines) < 40, len(lines)
    assert lines[0].startswith('You are Bea')
    assert 'words worth knowing' in out['text'] and 'help <anything>' in out['text']
    words = {r['word'] for r in out['rows']}
    assert {'look', 'post', 'undo', 'word-set'} <= words          # the Help window still reads every word
    full = say(k, b, 'help all')['text']
    assert 'not yours here:' in full and len(full.splitlines()) > len(lines) - 10


def test_a_topic_answers_to_its_name_aliases_and_plurals_and_is_fixed_with_set(world):
    k, a, b = world
    say(k, a, 'verb tidy steps="look" help="tidy: put two windows side by side"')
    t = say(k, a, 'make kind=topic name=windows aliases="window screen" words="tidy look" '
                  'text="Windows on this desktop."')['made'][0]
    for w in ('windows', 'window', 'Windows', 'screen'):
        page = say(k, b, 'help ' + w)['text']
        assert page.startswith('Windows on this desktop'.split()[0]) or 'Windows on this desktop' in page
        assert page.index('tidy') < page.index('look')              # the topic's order, most useful first
    assert f'ask {t}' in say(k, b, 'help windows')['text'] or 'set ' not in say(k, b, 'help windows')['text']
    assert f'fix this page: set {t}' in say(k, a, 'help windows')['text']
    say(k, a, f'set {t} text="Every window, listed."')
    assert 'Every window, listed.' in say(k, b, 'help window')['text']


def test_help_never_dead_ends(world):
    k, a, b = world
    out = say(k, b, 'help feed')                                     # no word called feed: what mentions it
    assert 'look' in out['text']
    assert 'did you mean' in say(k, b, 'pots hello', ok=False)['text']  # a typo names the nearest words
    nothing = say(k, b, 'help zzqx', ok=False)['text']
    assert 'help' in nothing and 'nothing answers' not in nothing


def test_a_word_name_stands_for_its_entry_and_help_shows_the_fix(world):
    k, a, b = world
    page = say(k, a, 'help set')['text']
    assert 'fix this help: word-set set help=' in page              # the steward sees the line that fixes it
    assert 'word-set' not in say(k, b, 'help set')['text']           # others are not shown a word they may not use
    say(k, a, 'word-set set help="set <thing> key=value: change facts on a thing."')   # help set was the look
    assert say(k, b, 'help set')['text'].startswith('set <thing> key=value')


def test_a_verb_leaves_out_settings_nobody_gave(world):
    k, a, b = world
    say(k, a, 'verb card steps="make kind=card title=$title who=$who note=$note" help="card title=<t> [who=<n>]: a card"')
    made = say(k, b, 'card title=milk')['made'][0]
    facts = k.state.things[made]
    assert facts['title'] == 'milk' and 'who' not in facts and 'note' not in facts
    assert not any('$' in str(v) for v in facts.values())
    say(k, a, 'verb retitle steps="set $target title=$title who=$who" help="retitle <card> title=<t>: rename it"')
    say(k, b, f'look {made}')
    say(k, b, f'set {made} who=Bea')
    say(k, b, f'look {made}')
    say(k, b, f'retitle {made} title=bread')
    assert k.state.things[made]['who'] == 'Bea'                     # a set verb does not erase what it was not given


def test_help_check_finds_help_that_misleads(world):
    k, a, b = world
    say(k, a, 'verb jot steps="look" help="jot.add text=<words>: jot something down"')
    out = say(k, b, 'help check')
    assert 'jot: its example says jot.add, but the word is jot' in out['text']
    assert any(r['word'] == 'jot' for r in out['rows'])


def test_look_by_name_says_which_id_and_help_words_reaches_its_topic(world):
    k, a, b = world
    t = say(k, b, 'make kind=note name=Groceries')['made'][0]
    assert f'Groceries is {t}' in say(k, b, 'look Groceries', ok=False)['text']
    assert 'all ' in say(k, b, 'help words')['text']                 # no topic called words: the full list
    say(k, a, 'make kind=topic name=words text="Making your own words." words="verb"')
    assert say(k, b, 'help words')['text'].startswith('words: Making your own words.')
