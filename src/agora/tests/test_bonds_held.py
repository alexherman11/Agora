"""around, nearby and preview: HELD 28 Oct 2026 with the graph work (Alex: "hold the graph and trail work"). The words
left the dictionary (round 5 found privacy leaks in around and nearby); these tests come back with them.
docs/design/kinds/fresh-kinds-and-bonds.md, fresh-words-reach-kinds.md."""
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skip(reason="graph held 28 Oct: around, nearby, preview are out of the dictionary")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kernel.kernel import Kernel


@pytest.fixture
def world(tmp_path):
    k = Kernel(tmp_path / 'world', {'tag': 'kb', 'name': 'Bonds',
        'steward': {'account': 'alex', 'name': 'Alex'}, 'invites_counted_by': 'kernel',
        'invites': [{'code': 'x', 'uses': 5}], 'groups': [{'name': 'Meeting group'}, {'name': 'Private'}]})
    a = k.actor_for(k.accounts['alex'])
    b = k.actor_for(k.join('bea', 'Bea', invite='x')['person'])
    return k, a, b


def say(k, actor, line, ok=True):
    out = k.run(actor, line)
    assert out['ok'] == ok, out
    return out


def made(k, actor, line):
    return say(k, actor, line)['made'][0]


def group(k, name):
    return next(g for g in k.things('group') if k.state.get(g, 'name') == name)


# ---------------------------------------------------------------------- around
def test_around_finds_bonds_nobody_typed(world):
    k, a, b = world
    jeff = k.actor_for(k.accounts['alex'], 'jeff')
    chat = made(k, a, 'make kind=chat name=Conversation')
    lane = made(k, a, 'make kind=lane name=Now')
    rl = made(k, a, 'make kind=program name="Rocket League"')
    task = made(k, a, 'make kind=task title="It will not open" lane=Now text="Rocket League gives a window error"')
    rec = say(k, a, f'say {chat} "@jeff look at the task"')['records'][0]
    say(k, a, f'turn {jeff.id} {rec} work={task}')
    note = made(k, jeff, f'make kind=note title=Diagnosis about={task}')
    rows = say(k, a, f'around {task} limit=10')['rows']
    why = {(r['id'], r['toward']): r['why'] for r in rows}
    assert 'its lane says Now' in why[(lane, 'company')]
    assert 'it mentions rocket league' in why[(rl, 'company')]
    assert 'about this' in why[(note, 'company')]
    assert 'worked on for it' in why[(note, 'consequence')]
    rows = say(k, a, f'around {note} toward=origin limit=10')['rows']
    assert any(r['id'] == chat and 'because of it' in r['why'] for r in rows)
    strongest = say(k, a, f'around {task} toward=strongest limit=3')['rows']
    assert strongest[0]['id'] == note                               # about it, worked on for it, and made because


def test_around_never_shows_what_the_reader_cannot_see(world):
    k, a, b = world
    g = group(k, 'Private')
    task = made(k, a, 'make kind=task title="Shared plan"')
    secret = made(k, a, f'make kind=note title="Secret" about={task} in={g}')
    post = made(k, a, 'post "a public post about the plan"')
    say(k, b, f'like {post}')
    assert secret in {r['id'] for r in say(k, a, f'around {task} limit=20')['rows']}
    assert secret not in {r['id'] for r in say(k, b, f'around {task} limit=20')['rows']}
    assert all(r['id'] != b.person or r['toward'] == 'audience' for r in say(k, a, f'around {post} limit=20')['rows'])
    say(k, b, f'around {secret}', ok=False)


# ---------------------------------------------------------------------- nearby
def test_nearby_tells_agents_they_are_on_the_same_thing(world):
    k, a, b = world
    jeff = k.actor_for(k.accounts['alex'], 'jeff')
    builder = k.actor_for(k.accounts['alex'], 'builder')
    card = made(k, a, 'make kind=task title="Fix the game gate"')
    other = made(k, a, f'make kind=note title="Gate notes" about={card}')
    say(k, jeff, f'look {card}')
    say(k, builder, f'look {card}')
    say(k, builder, f'set {card} lane=Now')
    rows = say(k, jeff, 'nearby')['rows']
    assert any(r['who_id'] == builder.id and r['how'] == 'is changing what you read' for r in rows)
    say(k, jeff, f'look {other}')
    say(k, jeff, f'set {other} text="the gate list is hard-coded"')
    rows = say(k, builder, 'nearby')['rows']
    assert any(r['who_id'] == jeff.id and r['id'] == other and 'bound up with' in r['how'] for r in rows)
    assert 'no one else' in say(k, b, 'nearby')['text']


# ---------------------------------------------------------------------- preview and renames
def test_preview_says_what_a_rename_would_break_and_writes_nothing(world):
    k, a, b = world
    lane = made(k, a, 'make kind=lane name=Now')
    for i in range(3):
        made(k, a, f'make kind=task title=T{i} lane=Now')
    made(k, a, 'make kind=lens name=work painter=components text="root : column, of tag:task, prop:lane=Now as t, each r\n'
               'r : text \\"$t.title\\""')
    say(k, a, f'look {lane}')
    n = len(k.log.records)
    out = say(k, a, f'preview set {lane} name=Doing')
    assert len(k.log.records) == n and k.state.get(lane, 'name') == 'Now'
    assert '3 tasks say lane=Now' in out['text'] and 'filters by =Now' in out['text']
    done = say(k, a, f'set {lane} name=Doing')
    assert '3 things still say lane=Now' in done['text']


def test_preview_shows_a_broken_promise_and_kinds_joined(world):
    k, a, b = world
    say(k, a, 'make kind=kind name=event needs="start title"')
    say(k, a, 'make kind=kind name=pamphlet promise="num(field(\'panels\')) <= 6" promise_says="six panels"')
    p = made(k, a, 'make kind=pamphlet title=Tides panels=6')
    say(k, a, f'look {p}')
    assert 'would be refused: six panels' in say(k, a, f'preview set {p} panels=8')['text']
    assert 'become a event too' in say(k, a, f'preview set {p} start=2026-11-01')['text'] or \
        'become an event too' in say(k, a, f'preview set {p} start=2026-11-01')['text']
    assert 'is a reading' in say(k, a, f'preview look {p}')['text']


