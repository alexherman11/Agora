"""Kinds all the way down (Alex approved 29 Oct 2026; research/kinds-lab/kinds-all-the-way-down.md).

"kind is what it's made of, state is the values of its parts": a need may say its part's kind (start:time,
likes:upvote); value kinds are the bottom (upvote value=number); a word on upvotes reaches anything with an upvote and is
told which part; synonyms are dictionary names (aliases=); alike and aspects find the same kind and the missing one.
Fresh temporary worlds only; no desktop, no live world."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kernel.kernel import Kernel, Refused


@pytest.fixture
def world(tmp_path):
    k = Kernel(tmp_path / 'world', {'tag': 'pt', 'name': 'Parts',
        'steward': {'account': 'alex', 'name': 'Alex'}, 'invites_counted_by': 'kernel',
        'invites': [{'code': 'x', 'uses': 5}], 'groups': [{'name': 'Crew'}]})
    a = k.actor_for(k.accounts['alex'])
    b = k.actor_for(k.join('bea', 'Bea', invite='x')['person'])
    return k, a, b


def say(k, actor, line, ok=True):
    out = k.run(actor, line)
    assert out['ok'] == ok, out
    return out


def made(k, actor, line):
    return say(k, actor, line)['made'][0]


def decl(k, name):
    return next(t for t in k.things('kind') if k.state.get(t, 'name') == name)


def upvotes(k, a):
    """Three apps that each count approval their own way, as they'd arrive."""
    say(k, a, 'make kind=kind name=upvote value=number aliases="likes"')
    say(k, a, 'make kind=kind name=clip needs="title hearts:upvote"')
    note = made(k, a, 'make kind=note title="Tide pools" upvote=3')
    post = made(k, a, 'make kind=board-item title="Beach cleanup" likes=12')
    clip = made(k, a, 'make kind=clip title="Sunset timelapse" hearts=5')
    plain = made(k, a, 'make kind=note title="Shopping list"')
    say(k, a, 'verb upvote acts_on=upvote steps="set $target $part=$2" help="upvote <thing> <count>: set its upvotes"')
    return note, post, clip, plain


# ---------------------------------------------------------------------- a word reaches parts
def test_a_word_on_upvotes_reaches_anything_with_an_upvote_and_is_told_which(world):
    k, a, b = world
    note, post, clip, plain = upvotes(k, a)
    say(k, a, f'upvote {note} 4')
    say(k, a, f'upvote {post} 13')
    say(k, a, f'upvote {clip} 6')
    assert (k.state.get(note, 'upvote'), k.state.get(post, 'likes'), k.state.get(clip, 'hearts')) == ('4', '13', '6')
    assert k.state.get(post, 'upvote') is None and k.state.get(clip, 'likes') is None     # its own part, no new one
    out = say(k, a, f'upvote {plain} 1', ok=False)
    assert 'acts on an upvote' in out['text'] and 'has no upvote' in out['text']
    assert k.state.get(plain, 'upvote') is None


def test_two_upvote_parts_ask_which_and_a_wrong_part_is_refused(world):
    k, a, b = world
    note, post, clip, plain = upvotes(k, a)
    both = made(k, a, 'make kind=note title="Both" upvote=1 likes=2')
    out = say(k, a, f'upvote {both} 9', ok=False)
    assert '2 upvote parts (upvote, likes)' in out['text'] and 'part=' in out['text']
    say(k, a, f'upvote {both} 9 part=likes')
    assert (k.state.get(both, 'upvote'), k.state.get(both, 'likes')) == ('1', '9')
    out = say(k, a, f'upvote {post} 9 part=title', ok=False)
    assert "title isn't one" in out['text'] and k.state.get(post, 'title') == 'Beach cleanup'


def test_a_value_that_does_not_read_as_the_kind_is_no_part(world):
    k, a, b = world
    upvotes(k, a)
    odd = made(k, a, 'make kind=board-item title="Odd" likes=lots')
    out = say(k, a, f'upvote {odd} 2', ok=False)
    assert 'has no upvote' in out['text'] and k.state.get(odd, 'likes') == 'lots'
    assert "lots isn't an upvote" in say(k, a, f'kinds {odd}')['text']


def test_reaching_a_part_never_widens_who_may_act(world):
    k, a, b = world
    note, post, clip, plain = upvotes(k, a)
    mine = made(k, a, 'make kind=note title="Private" upvote=1 sees=me')
    assert 'no thing' in say(k, b, f'upvote {mine} 7', ok=False)['text'].lower()
    plain_set = say(k, b, f'set {post} likes=99', ok=False)['text']        # Bea may not set Alex's post at all
    via_part = say(k, b, f'upvote {post} 99', ok=False)['text']
    assert k.state.get(post, 'likes') == '12' and k.state.get(mine, 'upvote') == '1'
    assert plain_set.split(':')[0] == via_part.split(':')[0] or 'refused' in via_part


def test_actions_and_rows_show_things_by_their_parts(world):
    k, a, b = world
    note, post, clip, plain = upvotes(k, a)
    acts = say(k, a, f'actions {post}')['text']
    assert 'as an upvote (its likes):' in acts and 'upvote ·' in acts
    assert 'upvote' not in say(k, a, f'actions {plain}')['text'].split('\n')[1]
    rows = say(k, a, 'rows upvote')['rows']
    assert [r['id'] for r in rows] == [note, post, clip]
    assert rows[1]['as'] == 'its likes is an upvote' and rows[2]['as'] == 'its hearts is an upvote'


def test_kinds_of_a_thing_lists_its_parts_and_its_loose_aspects(world):
    k, a, b = world
    note, post, clip, plain = upvotes(k, a)
    say(k, a, f'set {clip} mood=calm link=https://example.org/v/1')
    text = say(k, a, f'kinds {clip}')['text']
    assert 'parts: hearts (an upvote), link (a link)' in text
    assert 'loose (no kind gives them one): mood' in text


# ---------------------------------------------------------------------- typed parts tell values apart
def test_a_typed_part_admits_only_values_of_its_kind(world):
    k, a, b = world
    say(k, a, 'make kind=kind name=happening needs="title start|starts:time"')
    real = made(k, a, 'make kind=board-item title="Council" start=2026-11-02T18:00')
    other = made(k, a, 'make kind=note title="Tide talk" starts=2026-11-03')
    vague = made(k, a, 'make kind=note title="Someday" start=soon')
    assert [r['id'] for r in say(k, a, 'rows happening')['rows']] == [real, other]
    say(k, a, 'verb remind acts_on=happening steps="set $1 reminded=yes" help="remind <happening>"')
    out = say(k, a, f'remind {vague}', ok=False)
    assert 'has no start or starts (a time)' in out['text']


def test_where_on_a_meeting_and_where_on_a_note_are_told_apart(world):
    """The trials' homonyms (README: where, on, about): a part's kind tells them apart, whatever the name."""
    k, a, b = world
    say(k, a, 'make kind=kind name=spot value=text')
    say(k, a, 'make kind=kind name=venue needs="title where:link"')
    meeting = made(k, a, 'make kind=board-item title="Meetup" where=https://maps.example/x')
    note = made(k, a, 'make kind=note title="Keys" where="in my bag"')
    assert [r['id'] for r in say(k, a, 'rows venue')['rows']] == [meeting]
    assert 'where (a link)' in say(k, a, f'kinds {meeting}')['text']
    assert 'where' in say(k, a, f'kinds {note}')['text'].split('loose')[1]


def test_value_kinds_and_typed_parts_are_checked_when_declared(world):
    k, a, b = world
    assert 'declared nowhere here' in say(k, a, 'make kind=kind name=v needs="len:seconds"', ok=False)['text']
    assert 'value kind' in say(k, a, 'make kind=kind name=w value=number needs=title', ok=False)['text']
    assert 'value=' in say(k, a, 'make kind=kind name=x value=feelings', ok=False)['text']
    assert 'is not a need' in say(k, a, 'make kind=kind name=y needs="claim:upvote"', ok=False)['text']
    assert "kernel's own kinds" in say(k, a, 'make kind=kind name=number value=text', ok=False)['text']
    assert 'its leaders declare it' in say(k, b, 'make kind=kind name=stars value=number', ok=False)['text']
    say(k, a, 'make kind=kind name=seconds value=number')
    say(k, a, 'make kind=kind name=v needs="len:seconds"')


def test_typing_a_part_narrows_a_kind_so_it_waits_for_its_users(world):
    k, a, b = world
    say(k, a, 'make kind=kind name=happening needs="title start"')
    say(k, a, 'verb remind acts_on=happening steps="set $1 reminded=yes" help="remind <happening>"')
    out = say(k, a, f'set {decl(k, "happening")} needs="title start:time"', ok=False)
    assert 'only widens' in out['text']


# ---------------------------------------------------------------------- synonyms: one kind, other names
def test_a_synonym_names_the_same_kind(world):
    k, a, b = world
    say(k, a, 'make kind=kind name=task aliases="todo to-do"')
    t1 = made(k, a, 'make kind=task title="Paint fence"')
    t2 = made(k, a, 'make kind=todo title="Buy milk"')
    rows = say(k, a, 'rows task')['rows']
    assert [r['id'] for r in rows] == [t1, t2] and rows[1]['as'] == 'a todo, which is a task'
    assert [r['id'] for r in say(k, a, 'rows todo')['rows']] == [t1, t2]
    assert 'task · a todo, which is a task' in say(k, a, f'kinds {t2}')['text']
    assert 'another name for task' in say(k, a, 'make kind=kind name=todo', ok=False)['text']
    assert 'already names task' in say(k, a, 'make kind=kind name=chore aliases=todo', ok=False)['text']


# ---------------------------------------------------------------------- finding the same kind, telling apart
def test_making_a_kind_made_of_the_same_parts_says_so(world):
    k, a, b = world
    say(k, a, 'make kind=kind name=seconds value=number')
    say(k, a, 'make kind=kind name=video needs="title link:link length:seconds"')
    out = say(k, a, 'make kind=kind name=clip needs="title link:link length:seconds"')['text']
    assert 'clip is made of the same parts as video' in out and 'aliases=' in out
    hits = say(k, a, 'alike clip')['rows']
    assert hits[0]['kind'] == 'video' and hits[0]['score'] == 1.0
    out = say(k, a, 'make kind=kind name=edit-video extends=video needs="tracks:number"')['text']
    assert 'same parts' not in out                                       # extending it is the answer, not a match


def test_the_same_names_with_different_part_kinds_are_told_apart(world):
    k, a, b = world
    say(k, a, 'make kind=kind name=points value=number')
    say(k, a, 'make kind=kind name=rating value=number')
    say(k, a, 'make kind=kind name=game-event needs="title score:points at:time"')
    out = say(k, a, 'make kind=kind name=survey-answer needs="title score:rating at:time"')['text']
    assert 'same parts' not in out                                       # never offered as the same kind
    hit = say(k, a, 'alike survey-answer')['rows'][0]                    # but an agent sees how close, and why not
    assert hit['kind'] == 'game-event' and hit['apart'] == ['score (rating here, points there)']
    assert [r['kind'] for r in say(k, a, 'alike points')['rows']] == ['rating']      # both end in a number


def test_aspects_finds_the_loose_aspect_many_things_share(world):
    k, a, b = world
    upvotes(k, a)
    for i in range(3):
        made(k, a, f'make kind=note title="Day {i}" mood=calm')
    rows = say(k, a, 'aspects loose')['rows']
    mood = next(r for r in rows if r['aspect'] == 'mood')
    assert mood['loose'] == 3 and mood['kinds'] == {'note': 3}
    assert all(r['aspect'] not in ('likes', 'hearts') for r in rows)
    every = say(k, a, 'aspects')['rows']
    likes = next(r for r in every if r['aspect'] == 'likes')
    assert likes['as'] == {'upvote': 1} and likes['loose'] == 0


def test_aspects_counts_only_what_the_reader_sees(world):
    k, a, b = world
    made(k, a, 'make kind=note title="Secret" mood=grim sees=me')
    made(k, b, 'make kind=note title="Open" mood=fine')
    rows = say(k, b, 'aspects loose')['rows']
    assert next(r for r in rows if r['aspect'] == 'mood')['things'] == 1


# ---------------------------------------------------------------------- kits carry it
def test_a_kit_carries_value_kinds_synonyms_and_typed_parts():
    from kernel.kits import validate

    def kit(facts):
        return {'version': 1, 'source': '0' * 24, 'group': 'pt1', 'kernel': {},
                'definitions': [{'id': 'pt900', 'facts': facts}]}
    validate(kit({'kind': 'kind', 'name': 'upvote', 'value': 'number', 'aliases': 'likes hearts'}))
    validate(kit({'kind': 'kind', 'name': 'clip', 'needs': 'title hearts:upvote'}))
    with pytest.raises(Refused, match="isn't a kind name"):
        validate(kit({'kind': 'kind', 'name': 'upvote', 'value': 'Number!'}))


# ---------------------------------------------------------------------- optional parts, and clearing loose aspects
def cards(k, a):
    """Board cards as the live Board writes them: most fields on most cards, none required."""
    ids = []
    for i, (lane, pri, who) in enumerate([('Now', 1, 'Alex'), ('Now', 3, 'JEFF'), ('Done', 2, 'Alex')]):
        ids.append(made(k, a, f'make kind=card title="Card {i}" lane={lane} priority={pri} when=2026-10-2{i}T10:00Z '
                              f'colour=paper note_colour=paper lead={who} '
                              f'acceptance="Alex opens the thing and it does what the card says it does, every time"'))
    made(k, a, 'make kind=card title="Bare card"')
    return ids


def test_optional_parts_type_an_aspect_without_requiring_it(world):
    k, a, b = world
    ids = cards(k, a)
    say(k, a, 'make kind=kind name=card has="priority:number when:time"')
    assert len(say(k, a, 'rows card')['rows']) == 4                       # the bare card is still a card
    text = say(k, a, f'kinds {ids[0]}')['text']
    assert 'priority (a number)' in text and 'when (a time)' in text
    out = say(k, a, f'set {ids[0]} priority=high')['text']
    assert "high isn't a number: still set" in out and k.state.get(ids[0], 'priority') == 'high'
    assert 'marker' in say(k, a, f'set {decl(k, "card")} has="game=yes"', ok=False)['text']
    assert 'declared nowhere' in say(k, a, f'set {decl(k, "card")} has="size:inches"', ok=False)['text']


def test_aspects_counts_settings_and_computed_apart(world):
    k, a, b = world
    cards(k, a)
    made(k, a, 'make kind=dock-settings snap_px=16 dwell_ms=350')
    out = say(k, a, 'aspects')
    first = out['text'].splitlines()[0]
    assert 'said by one thing only' in out['text'] and 'snap_px' in out['text'].split('said by one thing only')[1]
    shared = [r['aspect'] for r in out['rows'] if not r['one_thing']]
    assert 'snap_px' not in shared and 'lane' in shared


def test_suggest_proposes_parts_from_values_and_names_the_judgment_calls(world):
    k, a, b = world
    ids = cards(k, a)
    say(k, a, f'set {ids[1]} parent={ids[0]}')
    say(k, a, f'set {ids[2]} parent={ids[0]}')
    out = say(k, a, 'aspects suggest')
    row = next(r for r in out['rows'] if r['kind'] == 'card')
    typed = {t['aspect']: t['kind'] for t in row['typed']}
    assert typed == {'priority': 'number', 'when': 'time', 'acceptance': 'text', 'parent': 'card'}
    judged = ' | '.join(row['judgment'])
    assert 'lane is one of 2 words (Done, Now)' in judged
    assert 'lead holds people written as names' in judged
    assert 'colour and note_colour say the same on all 3' in judged
    assert row['line'].startswith('make kind=kind name=card has=')
    say(k, a, row['line'])                                     # what it proposes is a line the world accepts
    assert 'priority' not in [r['aspect'] for r in say(k, a, 'aspects loose')['rows']]


def test_kinds_sharing_only_prose_are_not_the_same(world):
    """Live, 29 Oct: making charter said it had soul's parts, because both say where they came from in prose."""
    k, a, b = world
    say(k, a, 'make kind=kind name=soul has="source:text import_reviewed_by:text source_author:text"')
    out = say(k, a, 'make kind=kind name=charter has="source:text import_reviewed_by:text"')['text']
    assert 'same parts' not in out
    say(k, a, 'make kind=kind name=video needs="title" has="link:link"')
    assert 'same parts as video' in say(k, a, 'make kind=kind name=clip needs="title" has="link:link"')['text']
