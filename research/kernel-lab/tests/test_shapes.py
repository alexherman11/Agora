"""Words reach things that fit (Alex approved 28 Oct 2026; research/kinds-lab/fresh-words-reach-kinds.md).

A kind is a named shape (needs, extends); a word says the shape its code reads (acts_on, needs); one check, in guard,
refuses a thing that lacks it. Fresh temporary worlds only; no desktop, no live world."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kernel.kernel import Kernel, Refused


@pytest.fixture
def world(tmp_path):
    k = Kernel(tmp_path / 'world', {'tag': 'sh', 'name': 'Shapes',
        'steward': {'account': 'alex', 'name': 'Alex'}, 'invites_counted_by': 'kernel',
        'invites': [{'code': 'x', 'uses': 5}], 'groups': [{'name': 'Meeting group'}],
        'modules': [{'name': 'pad', 'run': ['none'], 'publishes': 'pad.*'}]})
    a = k.actor_for(k.accounts['alex'])
    b = k.actor_for(k.join('bea', 'Bea', invite='x')['person'])
    return k, a, b


def say(k, actor, line, ok=True):
    out = k.run(actor, line)
    assert out['ok'] == ok, out
    return out


def made(k, actor, line):
    return say(k, actor, line)['made'][0]


def kind_decl(k, name):
    return next(t for t in k.things('kind') if k.state.get(t, 'name') == name)


def events(k, a):
    say(k, a, 'make kind=kind name=event needs="title start|starts"')
    say(k, a, 'make kind=kind name=meeting extends=event needs=place')
    board = made(k, a, 'make kind=board-item post_kind=event title="Beach cleanup" start=2026-11-01T10:00 seats=20')
    meeting = made(k, a, 'make kind=meeting title="Council prep" start=2026-11-02T18:00 place=Library')
    talk = made(k, a, 'make kind=note title="Tide talk" starts=2026-11-03T09:00')
    task = made(k, a, 'make kind=taskboard-task title="Paint fence" lane=Now when=2026-11-05')
    return board, meeting, talk, task


# ---------------------------------------------------------------------- kinds are named shapes
def test_a_calendar_lists_every_thing_with_the_shape_whatever_app_made_it(world):
    k, a, b = world
    board, meeting, talk, task = events(k, a)
    rows = say(k, a, 'rows event')['rows']
    assert [r['id'] for r in rows] == [board, meeting, talk]          # a task's when is a due date: not an event
    assert rows[0]['as'] == 'has title, start'
    assert rows[1]['as'] == 'a meeting, so an event'
    assert rows[2]['start'] == '2026-11-03T09:00' and 'start as starts' in rows[2]['as']   # read under event's name
    assert [r['id'] for r in say(k, a, 'rows event exact=yes')['rows']] == []
    assert k.state.get(talk, 'start') is None                         # reading never writes


def test_a_lens_tag_draws_what_has_the_shape_under_the_kinds_names(world):
    k, a, b = world
    board, meeting, talk, task = events(k, a)
    from painter.arrangement import compile_view
    lens = made(k, a, 'make kind=lens name=calendar painter=components text="root : column, of tag:event as e, each row\n'
                      'row : text \\"$e.title at $e.start\\""')
    view = str(compile_view(k, a, lens))
    assert 'Beach cleanup at 2026-11-01' in view and 'Council prep' in view and 'Tide talk at 2026-11-03' in view
    assert 'Paint fence' not in view


def test_extends_inherits_needs_and_later_widenings(world):
    k, a, b = world
    events(k, a)
    say(k, a, 'make kind=kind name=class extends=meeting needs=teacher')
    found = say(k, a, 'kinds ' + made(k, a, 'make kind=class title=Pottery start=1 place=Hall teacher=Mo'))['rows']
    assert [r['kind'] for r in found][:3] == ['class', 'meeting', 'event']
    odd = made(k, a, 'make kind=note title=Yoga begins=2026-11-09 place=Beach teacher=Kai')
    assert not say(k, a, 'rows class')['rows'] or odd not in [r['id'] for r in say(k, a, 'rows class')['rows']]
    say(k, a, f'set {kind_decl(k, "event")} needs="title start|starts|begins"')     # event widens...
    assert odd in [r['id'] for r in say(k, a, 'rows event')['rows']]                # ...for the parent, by shape;
    assert odd not in [r['id'] for r in say(k, a, 'rows class')['rows']]            # a child holds what's declared one
    say(k, a, f'mark {odd} class')                                                    # (Alex, 28 Oct)
    assert odd in [r['id'] for r in say(k, a, 'rows class')['rows']]
    assert k.state.get(odd, 'is.class') == 'yes'


def test_a_kind_only_widens_once_something_relies_on_it(world):
    k, a, b = world
    events(k, a)
    ev = kind_decl(k, 'event')
    out = say(k, a, f'set {ev} needs="title start|starts place"', ok=False)['text']
    assert 'need more (place)' in out and 'kind meeting' in out
    say(k, a, f'set {ev} needs="title start|starts|begins"')                       # wider: fine
    assert 'keeps its name' in say(k, a, f'set {ev} name=gathering', ok=False)['text']
    say(k, a, 'make kind=kind name=solo needs="title"')
    say(k, a, f'set {kind_decl(k, "solo")} needs="title text"')                      # nothing relies on it yet


def test_extends_refuses_a_cycle_and_an_unknown_parent(world):
    k, a, b = world
    say(k, a, 'make kind=kind name=loop extends=loop', ok=False)
    say(k, a, 'make kind=kind name=child extends=nobody', ok=False)
    say(k, a, 'make kind=kind name=one needs=title')
    say(k, a, 'make kind=kind name=two extends=one needs=text')
    assert 'extend itself' in say(k, a, f'set {kind_decl(k, "one")} extends=two', ok=False)['text']


def test_only_leaders_declare_a_kind_with_a_shape(world):
    k, a, b = world
    assert 'its leaders declare it' in say(k, b, 'make kind=kind name=event needs="title"', ok=False)['text']
    say(k, b, 'make kind=kind name=recipe')                       # a plain declaration constrains nothing: as before
    assert 'its leaders declare it' in say(k, b, f'set {kind_decl(k, "recipe")} needs=title', ok=False)['text']
    say(k, a, 'make kind=kind name=event needs="title start"')


def test_a_need_must_be_an_aspect_a_line_can_write(world):
    k, a, b = world
    assert 'is not a need' in say(k, a, 'make kind=kind name=x needs="contact:phone"', ok=False)['text']
    assert 'is not a need' in say(k, a, 'make kind=kind name=x needs="title= "', ok=False)['text']


# ---------------------------------------------------------------------- words say the shape they read
def test_a_word_reaches_what_has_its_shape_and_names_what_is_missing(world):
    k, a, b = world
    board, meeting, talk, task = events(k, a)
    say(k, a, 'verb rsvp.go acts_on=event needs=seats steps="set $1 going=yes" help="rsvp.go <event>: going"')
    say(k, a, f'rsvp.go {board}')
    out = say(k, a, f'rsvp.go {meeting}', ok=False)['text']
    assert 'rsvp.go acts on an event with seats' in out and 'has no seats' in out
    assert 'has no start or starts, seats' in say(k, a, f'rsvp.go {task}', ok=False)['text']
    say(k, a, f'set {meeting} seats=12')
    say(k, a, f'rsvp.go {meeting}')                                  # a meeting is an event: the word reaches it


def test_a_word_with_no_shape_reaches_anything_as_before(world):
    k, a, b = world
    board, meeting, talk, task = events(k, a)
    say(k, a, 'verb tag.it steps="set $1 tagged=yes" help="tag.it <thing>: tag it"')
    for t in (board, meeting, talk, task):
        say(k, a, f'tag.it {t}')


def test_the_check_holds_inside_a_verbs_steps(world):
    k, a, b = world
    board, meeting, talk, task = events(k, a)
    k.on_offer(k.module_named('pad'), [{'word': 'pad.rsvp', 'help': 'pad.rsvp <event>: going', 'takes': '<id>',
                                         'acts_on': 'event', 'needs': 'seats'}])
    say(k, a, 'verb plan.it steps="set $1 planned=yes; pad.rsvp $1" help="plan.it <thing>: plan and go"')
    out = say(k, a, f'plan.it {task}', ok=False)['text']
    assert 'pad.rsvp acts on an event' in out
    assert k.state.get(task, 'planned') is None                     # one act: nothing was done


def test_a_module_word_is_checked_before_the_module_is_asked(world):
    k, a, b = world
    board, meeting, talk, task = events(k, a)
    m = k.module_named('pad')
    said = k.on_offer(m, [{'word': 'pad.rsvp', 'help': 'pad.rsvp <event>: going', 'takes': '<id>',
                           'acts_on': 'event', 'needs': 'seats'}])
    assert said[0].startswith('published')
    e = k.find_entry('pad.rsvp')
    assert k.state.get(e, 'acts_on') == 'event' and k.state.get(e, 'needs') == 'seats'
    assert 'has no seats' in say(k, a, f'pad.rsvp {meeting}', ok=False)['text']     # not "pad is not running"
    say(k, a, f'look {e}')
    say(k, a, 'word-set pad.rsvp needs=""')                                     # a steward widens it...
    k.on_offer(m, [{'word': 'pad.rsvp', 'help': 'pad.rsvp <event>: going', 'takes': '<id>',
                    'acts_on': 'event', 'needs': 'seats'}])
    assert not k.state.get(e, 'needs')                                          # ...and a re-offer keeps theirs
    assert 'not a need' in k.on_offer(m, [{'word': 'pad.bad', 'help': 'pad.bad', 'needs': 'a=b='}])[0]


def test_a_steward_widens_what_a_word_reaches_in_one_line_with_no_reload(world):
    # Alex, 28 Oct: "how could the house build something that was a task but was labeled say as task_thing"
    k, a, b = world
    m = k.module_named('pad')
    k.on_offer(m, [{'word': 'pad.build', 'help': 'pad.build <task>: build it', 'takes': '<id>',
                    'needs': 'kind=taskboard-task|task'}])
    odd = made(k, a, 'make kind=task_thing title="Dock request"')
    assert 'has no kind taskboard-task or task' in say(k, a, f'pad.build {odd}', ok=False)['text']
    e = k.find_entry('pad.build')
    say(k, a, f'look {e}')
    say(k, a, 'word-set pad.build needs="kind=taskboard-task|task|task_thing"')
    out = say(k, a, f'pad.build {odd}', ok=False)['text']
    assert 'acts on' not in out and 'pad' in out                   # past the shape: now only "pad is not running"
    k.on_offer(m, [{'word': 'pad.build', 'help': 'pad.build <task>: build it', 'takes': '<id>',
                    'needs': 'kind=taskboard-task|task'}])         # the module starts again and re-offers...
    assert 'task_thing' in k.state.get(e, 'needs')                 # ...and the steward's widening stays


def test_a_plain_word_picks_the_family_word_whose_shape_fits(world):
    k, a, b = world
    say(k, a, 'verb task.done needs="kind=taskboard-task|task" steps="set $1 lane=Done" help="task.done <task>: done"')
    say(k, a, 'verb todo.done needs="kind=todo" steps="set $1 status=closed" help="todo.done <todo>: done"')
    card = made(k, a, 'make kind=taskboard-task title="Paint fence" lane=Now')
    todo = made(k, a, 'make kind=todo title="Buy milk" status=open')
    say(k, a, 'done "Paint fence"')
    say(k, a, 'done "Buy milk"')
    assert k.state.get(card, 'lane') == 'Done' and k.state.get(todo, 'status') == 'closed'
    note = made(k, a, 'make kind=note title=Groceries')
    assert 'done' in say(k, a, f'done {note}', ok=False)['text']


def test_own_kind_first_then_the_shape_needing_most(world):
    k, a, b = world
    say(k, a, 'make kind=kind name=dated needs="title when"')
    say(k, a, 'verb any.done acts_on=dated steps="set $1 finished=yes" help="any.done <thing>: done"')
    say(k, a, 'verb task.done needs="kind=taskboard-task" steps="set $1 lane=Done" help="task.done <task>: done"')
    card = made(k, a, 'make kind=taskboard-task title="Paint fence" lane=Now when=2026-11-05')
    say(k, a, f'done {card}')
    assert k.state.get(card, 'lane') == 'Done' and k.state.get(card, 'finished') is None   # its own kind's word
    other = made(k, a, 'make kind=note title=Dentist when=2026-11-07')
    say(k, a, f'done {other}')
    assert k.state.get(other, 'finished') == 'yes'
    say(k, a, 'verb chore.done acts_on=dated steps="set $1 chored=yes" help="chore.done <thing>: done"')
    assert 'could mean' in say(k, a, f'done {other}', ok=False)['text']           # a tie asks which


def test_a_name_finds_the_thing_the_word_reaches(world):
    k, a, b = world
    board, meeting, talk, task = events(k, a)
    say(k, a, 'verb rsvp.go acts_on=event needs=seats steps="set $1 going=yes" help="rsvp.go <event>: going"')
    made(k, a, 'make kind=note title="Beach cleanup" text="what to bring"')        # same name, not an event
    say(k, a, 'rsvp.go "Beach cleanup"')
    assert k.state.get(board, 'going') == 'yes'


def test_actions_says_what_you_can_do_with_a_thing(world):
    k, a, b = world
    board, meeting, talk, task = events(k, a)
    say(k, a, 'verb rsvp.go acts_on=event needs=seats steps="set $1 going=yes" help="rsvp.go <event>: going"')
    say(k, a, 'verb task.done needs="kind=taskboard-task" steps="set $1 lane=Done" help="task.done <task>: done"')
    made(k, a, 'make kind=lens name=calendar painter=components text="root : column, of tag:event as e"')
    out = say(k, a, f'actions {board}')
    assert 'rsvp.go' in out['text'] and 'task.done' not in out['text'] and 'calendar (as event)' in out['text']
    assert [r['word'] for r in say(k, a, f'actions {task}')['rows']] == ['task.done']


# ---------------------------------------------------------------------- spellings and markers
def test_set_writes_what_it_is_told_and_names_the_other_spelling(world):
    # first built as a refusal; trials 28 Oct: spellings can be vocabularies (lane|status), and the refusal blocked
    # the House's status=paused hold and advised a write that hid the card. Now it writes as said, and says so
    k, a, b = world
    board, meeting, talk, task = events(k, a)
    out = say(k, a, f'set {talk} start=2026-11-04')['text']
    assert 'also says starts, which an event reads as start' in out and f'set {talk} starts=' in out
    assert k.state.get(talk, 'start') == '2026-11-04' and k.state.get(talk, 'starts') == '2026-11-03T09:00'
    assert 'also says' not in say(k, a, f'set {task} start=2026-11-04')['text']   # a task isn't an event


# ---------------------------------------------------------------------- what the trials found (28 Oct)
def test_a_members_verb_never_answers_a_plain_word_for_anyone_else(world):
    k, a, b = world
    say(k, a, 'verb task.done needs="kind=taskboard-task" steps="set $1 lane=Done" help="task.done <task>: done"')
    card = made(k, a, 'make kind=taskboard-task title="Paint fence" lane=Now project=Home estimate=2')
    say(k, a, 'look ' + k.find_entry('verb'))
    say(k, a, 'word-set verb may=members')                       # as on Alex's desk, where members make words
    say(k, b, 'verb tidy.done needs="title lane project estimate" steps="forget $1" help="tidy.done <thing>: tidy"')
    say(k, a, f'done {card}')
    assert k.state.get(card, 'lane') == 'Done' and not k.state.get(card, 'forgotten')
    mine = made(k, b, 'make kind=note title=Mine lane=Now project=X estimate=1')
    say(k, b, f'done {mine}')                                    # it still answers its maker
    assert k.state.get(mine, 'forgotten')                        # (said by its full name, anyone may still use it)


def test_one_declaration_of_a_kind_per_scope(world):
    k, a, b = world
    say(k, a, 'make kind=kind name=issue needs="name status"')
    assert 'declared here already' in say(k, a, 'make kind=kind name=issue needs="name status seats"', ok=False)['text']
    assert 'declared here already' in say(k, b, 'make kind=kind name=issue', ok=False)['text']


def test_the_kernels_own_kinds_take_no_shape(world):
    k, a, b = world
    assert "kernel's own kinds" in say(k, a, 'make kind=kind name=said needs="text|message chat|channel"', ok=False)['text']
    say(k, a, 'make kind=kind name=chatlike needs=text')
    assert "kernel's own kinds" in say(k, a, 'make kind=kind name=line extends=said', ok=False)['text']


def test_acts_on_is_met_by_a_things_own_kind_as_rows_and_lenses_meet_it(world):
    k, a, b = world
    say(k, a, 'make kind=kind name=convo needs="convo=yes"')
    crew = made(k, a, 'make kind=convo name="Stream crew"')
    win = made(k, a, 'make kind=app-window title=ChatGPT convo=yes')
    say(k, a, 'verb convo.star acts_on=convo steps="set $1 starred=yes" help="convo.star <convo>: star it"')
    say(k, a, f'convo.star {crew}')                              # its own kind: reached, though it lacks the marker
    say(k, a, f'convo.star {win}')                               # the marker: reached
    assert 'has no convo yes' in say(k, a, f'convo.star {made(k, a, "make kind=note title=X")}', ok=False)['text']


def test_opening_a_closed_kind_is_widening_but_dropping_a_need_words_read_is_refused(world):
    k, a, b = world
    say(k, a, 'make kind=kind name=event')                       # closed, as the board's event is
    made(k, a, 'make kind=lens name=calendar painter=components text="root : column, of tag:event as e"')
    say(k, a, f'set {kind_decl(k, "event")} needs="title start"')   # opening it only adds what fits: allowed
    say(k, a, 'make kind=kind name=issue needs="name status"')
    say(k, a, 'verb issue.close acts_on=issue steps="set $1 status=closed" help="issue.close <issue>: close it"')
    out = say(k, a, f'set {kind_decl(k, "issue")} needs="name"', ok=False)['text']
    assert 'issue.close act on issue and may read status' in out
    say(k, a, 'look ' + k.find_entry('issue.close'))
    say(k, a, 'word-set issue.close needs=status')
    say(k, a, f'set {kind_decl(k, "issue")} needs="name"')      # now the word says it itself


def test_a_word_made_for_a_things_own_kind_is_not_passed_over_for_a_shaped_one(world):
    k, a, b = world
    say(k, a, 'verb window.shut steps="set $1 shut=yes" help="window.shut <window>: shut it"')
    say(k, a, 'make kind=kind name=convo needs="convo=yes"')
    say(k, a, 'verb convo.shut acts_on=convo steps="set $1 archived=yes" help="convo.shut <convo>: archive it"')
    win = made(k, a, 'make kind=window title=ChatGPT convo=yes')
    say(k, a, f'shut {win}')
    assert k.state.get(win, 'shut') == 'yes' and k.state.get(win, 'archived') is None


def test_a_refusal_counts_what_the_steward_cannot_see_and_never_names_it(world):
    k, a, b = world
    say(k, a, 'make kind=kind name=issue needs="name status"')
    made(k, b, 'make kind=lens name="Bea private board" sees=me painter=components text="root : column, of tag:issue as i"')
    say(k, a, 'verb issue.close acts_on=issue needs=status steps="set $1 status=closed" help="issue.close <issue>"')
    out = say(k, a, f'set {kind_decl(k, "issue")} needs="name status due"', ok=False)['text']
    assert "1 thing you can't see" in out and 'Bea private board' not in out


def test_acts_on_must_name_a_kind_that_is_here(world):
    k, a, b = world
    assert 'no kind isue' in say(k, a, 'verb issue.close acts_on=isue steps="set $1 status=closed" help="x"',
                                 ok=False)['text']


def test_spellings_live_inside_a_kind_so_homonyms_stay_apart(world):
    k, a, b = world
    t = made(k, a, 'make kind=task title=Fence colour=red')
    made(k, a, 'make kind=style name=warm color="#ff0000"')
    assert [r['id'] for r in say(k, a, 'rows task colour=red')['rows']] == [t]
    assert say(k, a, 'rows style colour=red')['rows'] == []


def test_mark_sets_markers_on_what_has_the_other_needs(world):
    k, a, b = world
    say(k, a, 'make kind=kind name=game needs="run game=yes"')
    rl = made(k, a, 'make kind=program name="Rocket League" run=rl.exe')
    note = made(k, a, 'make kind=note title=Groceries')
    assert 'needs run' in say(k, a, f'mark {note} game', ok=False)['text']
    assert say(k, a, 'rows game')['rows'] == []                  # run alone doesn't make a game
    say(k, a, f'mark {rl} game')
    assert k.state.get(rl, 'game') == 'yes' and [r['id'] for r in say(k, a, 'rows game')['rows']] == [rl]
    say(k, a, 'undo')                                            # a mark is a set: undo takes it back
    assert k.state.get(rl, 'game') is None
    say(k, a, 'make kind=kind name=card needs="title kind=taskboard-task"')
    assert 'made as one' in say(k, a, f'mark {note} card', ok=False)['text']


# ---------------------------------------------------------------------- power and privacy
def test_classifying_never_widens_a_grant(world):
    k, a, b = world
    say(k, a, 'make kind=kind name=task needs="title lane"')
    note = made(k, a, 'make kind=note title=Groceries lane=Now')
    from kernel.kernel import Actor
    m = k.module_named('pad')
    say(k, a, f'grant {m} words="set" only=kind:taskboard-task')
    pad = Actor(m, a.person, 'module', module=m, caller=a)
    with pytest.raises(Refused):
        k.reaches(pad, 'set', k.state.get(note, 'kind'), target=note, fields={'lane': 'Done'})


def document_scope_world(world):
    """Fixture-only authority, never a live grant or a running provider."""
    from kernel.kernel import Actor
    k, a, b = world
    library = made(k, a, 'make kind=document-library name=Research')
    other = made(k, a, 'make kind=document-library name=Other')
    mid = k.module_named('pad')
    say(k, a, f'grant {mid} words="make set" '
              f'only="kind:document-folder,document-entry;library:{library}"')
    say(k, a, f'grant {mid} words=look')
    return k, a, b, library, other, Actor(mid, a.person, 'module', module=mid, caller=a)


def test_document_library_scope_admits_metadata_and_preserves_ownership(world):
    k, a, b, library, other, pad = document_scope_world(world)
    folder = made(k, pad, f'make kind=document-folder name=Notes library={library} '
                          f'parent={library} within={library}')
    say(k, pad, f'look {folder}')
    say(k, pad, f'set {folder} name=Minutes')
    assert k.state.get(folder, 'visibility_of') == library
    assert k.state.get(folder, 'for') == a.person
    say(k, a, f'look {folder}')
    say(k, a, f'grant {pad.module} words=set only="kind:document-folder;library:{other}"')
    # A second matching grant must not donate fields or library membership.
    say(k, pad, f'set {folder} library={other}', ok=False)
    assert k.state.get(folder, 'library') == library


@pytest.mark.parametrize('suffix', [
    'sees=place', 'text=payload', 'in=missing', 'about=missing',
    'allows.set=anyone', 'file=missing', 'unexpected=value',
])
def test_document_folder_scope_refuses_extra_creation_power(world, suffix):
    k, a, b, library, other, pad = document_scope_world(world)
    before = len(k.log.records)
    say(k, pad, f'make kind=document-folder name=Notes library={library} '
                f'parent={library} within={library} {suffix}', ok=False)
    assert len(k.log.records) == before


def test_document_scope_refuses_cross_library_cycles_and_uninherited_rows(world):
    k, a, b, library, other, pad = document_scope_world(world)
    folder = made(k, pad, f'make kind=document-folder name=Notes library={library} '
                          f'parent={library} within={library}')
    foreign = made(k, a, f'make kind=document-folder name=Foreign library={other} '
                        f'parent={other} within={other}')
    forged = made(k, a, f'make kind=document-folder name=Legacy library={library} parent={library}')
    say(k, pad, f'look {folder}')
    for change in (f'parent={foreign}', f'parent={folder}', f'parent={other}',
                   f'library={other}', 'sees=place', 'text=payload'):
        before = len(k.log.records)
        say(k, pad, f'set {folder} {change}', ok=False)
        assert len(k.log.records) == before
    say(k, pad, f'look {forged}')
    say(k, pad, f'set {forged} name=Changed', ok=False)
    say(k, pad, f'make kind=document-folder name=NoInheritance library={library} parent={library}', ok=False)


def test_document_scope_does_not_admit_posts_or_unseen_libraries(world):
    k, a, b, library, other, pad = document_scope_world(world)
    # Even a separate post grant must not bypass make's library restriction.
    say(k, a, f'grant {pad.module} words=post')
    say(k, pad, 'make kind=post text=Unexpected', ok=False)
    say(k, a, f'look {library}')
    say(k, a, f'set {library} sees=me')
    pad.person = b.person
    pad.caller = b
    say(k, pad, f'make kind=document-folder name=Hidden library={library} '
                f'parent={library} within={library}', ok=False)


def test_document_scope_indexes_own_upload_but_never_mutates_file(world):
    from kernel.blobs import receive
    k, a, b, library, other, pad = document_scope_world(world)
    file = receive(k, a, b'fixture text', name='notes.txt')['made'][0]
    entry = made(k, pad, f'make kind=document-entry name=Notes file={file} '
                         f'library={library} parent={library} within={library}')
    assert k.state.get(entry, 'file') == file
    assert k.state.get(file, 'attached_to') is None
    say(k, pad, f'look {entry}')
    say(k, pad, f'set {entry} file=missing', ok=False)
    say(k, pad, f'look {file}')
    say(k, pad, f'set {file} name=Changed', ok=False)
    # Raw uploads, blobs and attachments remain outside metadata authority.
    assert k.state.get(file, 'name') == 'notes.txt'
    say(k, pad, f'make kind=document-entry name=Missing file=missing '
                f'library={library} parent={library} within={library}', ok=False)


def test_a_thing_you_cannot_see_is_never_fitted_or_named(world):
    k, a, b = world
    say(k, a, 'make kind=kind name=event needs="title start"')
    hidden = made(k, a, 'make kind=meeting title=Secret start=1 sees=me')
    assert hidden not in [r['id'] for r in say(k, b, 'rows event')['rows']]
    say(k, a, 'verb rsvp.go acts_on=event steps="set $1 going=yes" help="rsvp.go <event>: going"')
    out = say(k, b, f'rsvp.go {hidden}', ok=False)['text']
    assert 'Secret' not in out


def test_replay_matches_memory_after_all_of_it(world):
    k, a, b = world
    board, meeting, talk, task = events(k, a)
    say(k, a, 'make kind=kind name=game needs="run game=yes"')
    rl = made(k, a, 'make kind=program name=RL run=rl.exe')
    say(k, a, f'mark {rl} game')
    say(k, a, 'verb rsvp.go acts_on=event needs=seats steps="set $1 going=yes" help="rsvp.go <event>: going"')
    say(k, a, f'rsvp.go {board}')
    assert Kernel(k.dir).state.snapshot() == k.state.snapshot()


def test_a_kernel_word_the_kernel_no_longer_runs_rests_hidden_and_comes_back(world):
    k, a, b = world
    from kernel import words as W
    e = k.find_entry('mark')
    fn = W.KERNEL.pop('mark')                       # a kernel without mark (as around is held, 28 Oct)
    try:
        k2 = Kernel(k.dir)
        assert k2.find_entry('mark') is None and k2.state.get(e, 'retired') == 'yes'
    finally:
        W.KERNEL['mark'] = fn
    k3 = Kernel(k.dir)
    assert k3.find_entry('mark') == e and k3.state.get(e, 'status') == 'live'


# ---------------------------------------------------------------------- agents' turns (kept live)
def test_an_agents_acts_say_what_they_answer_and_the_card(world):
    k, a, b = world
    jeff = k.actor_for(k.accounts['alex'], 'jeff')
    chat = made(k, a, 'make kind=chat name=Conversation')
    card = made(k, a, 'make kind=task title="Fix the game gate"')
    rec = say(k, a, f'say {chat} "@jeff rocket league still will not open"')['records'][0]
    say(k, b, f'turn {jeff.id} {rec}', ok=False)                   # not Bea's agent
    say(k, a, f'turn {jeff.id} {rec} work={card}')
    note = made(k, jeff, 'make kind=note title="Diagnosis" text="Steam is not signed in"')
    r = k.log.records[k.state.history[(note, 'kind')][0][0] - 1]
    assert r['because'] == int(rec[1:]) and r['work'] == card
    say(k, a, f'turn {jeff.id} done')
    later = made(k, jeff, 'make kind=note title=Later')
    r = k.log.records[k.state.history[(later, 'kind')][0][0] - 1]
    assert 'because' not in r and 'work' not in r
    say(k, a, 'undo ' + rec)                         # because is a bond, not caused_by: JEFF's work stays
    assert k.state.get(note, 'kind') == 'note'


# ---------------------------------------------------------------------- a shape this kernel can't read fails closed
def test_a_shape_this_kernel_cannot_read_reaches_nothing(world):
    """Kernel review C4 (28 Oct): an unreadable stored needs= was read as none, so the word reached everything. A kit
    from a newer world, or a rolled-back kernel, must make the word refuse, not widen it."""
    k, a, b = world
    board, meeting, talk, task = events(k, a)
    say(k, a, 'verb ping needs=title steps="set $1 pinged=yes" help="ping <thing>: ping it"')
    k.state.things[k.find_entry('ping')]['needs'] = 'start:time'          # as a newer world's kit would carry it
    out = say(k, a, f'ping {board}', ok=False)
    assert "can't be read by this kernel" in out['text'] and k.state.get(board, 'pinged') is None
    assert 'ping' not in say(k, a, f'actions {board}')['text'].split()
    # a kind it can't read admits nothing by its shape: only things whose own kind it is
    k.state.things[kind_decl(k, 'meeting')]['needs'] = 'place:point'
    k.kinds._seen = -1
    assert [r['id'] for r in say(k, a, 'rows meeting')['rows']] == [meeting]


def test_a_kit_with_a_shape_this_kernel_cannot_read_is_refused():
    from kernel.kits import validate
    def kit(facts):
        return {'version': 1, 'source': '0' * 24, 'group': 'sh1', 'kernel': {},
                'definitions': [{'id': 'sh900', 'facts': facts}]}
    with pytest.raises(Refused, match="can't read"):
        validate(kit({'kind': 'kind', 'name': 'happening', 'needs': 'start:time'}))
    with pytest.raises(Refused, match="isn't a kind name"):
        validate(kit({'kind': 'kind', 'name': 'happening', 'extends': 'Event!'}))
    validate(kit({'kind': 'kind', 'name': 'happening', 'needs': 'title start|begins'}))


def test_a_shape_refusal_kept_for_stewards_never_names_a_private_title(world):
    """Kernel review H1 (28 Oct): Bea's sees=me note was refused by a shaped word, and Alex's `refusals all` showed its
    title. The caller is told the title; the log keeps the word, the need and the id."""
    k, a, b = world
    note = made(k, b, 'make kind=note title="Therapy with Dr K" sees=me')
    assert k.shown(a.person, note) is None
    say(k, a, 'verb remind needs=start steps="set $1 reminded=yes" help="remind <thing>: remind me"')
    out = say(k, b, f'remind {note}', ok=False)
    assert 'Therapy with Dr K' in out['text']                       # Bea may see her own title
    kept = say(k, a, 'refusals all')['text']
    assert 'remind (a thing you can' in kept                    # the steward sees the word, not the thing
    assert 'Therapy' not in kept and note not in kept
    assert 'Therapy' in say(k, b, 'refusals')['text'] or note in say(k, b, 'refusals')['text']   # Bea sees her own


def test_a_painted_read_of_a_kinds_name_is_fenced_on_the_things_own_spelling(world):
    """Kernel review H2 (28 Oct): a lens of tag:event paints `start` for a thing that says `starts`; the press then said
    it read `start`, whose history is empty, so a change to `starts` after the paint was never stale."""
    k, a, b = world
    board, meeting, talk, task = events(k, a)
    rev = k.state.rev[talk]
    painted = {talk: {'rev': rev, 'aspects': ['start']}}
    k.fence(a, talk, ['title'], painted)                              # nothing changed: admitted
    say(k, a, f'look {talk}; set {talk} starts=2026-11-04T09:00')
    with pytest.raises(Refused, match='stale'):
        k.fence(a, talk, ['title'], painted)


def test_a_name_many_things_share_lists_them_with_what_tells_them_apart(world):
    """Friction 9 (trials 28 Oct): done "Dentist" matched 17 things and the question gave no way to pick."""
    k, a, b = world
    say(k, a, 'make kind=kind name=event needs="title start"')
    ids = [made(k, a, f'make kind=meeting title=Dentist start=2026-11-{d:02d}T09:00') for d in range(1, 10)]
    say(k, a, 'verb visit.go acts_on=event steps="set $1 went=yes" help="visit.go <event>: went"')
    out = say(k, a, 'visit.go Dentist', ok=False)['text']
    assert '9 things are called Dentist' in out
    assert f'{ids[0]} (a meeting, start 2026-11-01T09:00)' in out and 'and 3 more' in out
    out = say(k, a, 'go Dentist', ok=False)['text']                 # the plain word asks the same way
    assert ids[0] in out and 'start 2026-11-01' in out


# ---------------------------------------------------------------------- kernel review, round 2 (28 Oct)
def test_a_number_written_with_odd_digits_never_breaks_a_view(world):
    """seats=² passed isdigit() and crashed int() in shown(): one member's thing broke every reader's lens."""
    k, a, b = world
    t = made(k, b, 'make kind=note title=Picnic seats=²')
    assert k.shown(a.person, t) is not None and k.shown(b.person, t) is not None
    say(k, a, 'rows note')


def test_a_kit_cannot_give_the_kernels_own_kinds_a_shape(world):
    import json
    k, a, b = world
    bundle = {'version': 1, 'source': '0' * 24, 'group': 'sh1', 'kernel': {},
              'definitions': [{'id': 'sh900', 'facts': {'kind': 'kind', 'name': 'said', 'needs': 'text chat'}}]}
    out = say(k, a, 'take bundle=' + json.dumps(json.dumps(bundle)), ok=False)
    assert "kernel's own kinds" in out['text']


def test_a_module_saw_with_a_rev_alone_fences_the_whole_thing(world):
    k, a, b = world
    out = k._module_saw('dk1', {'saw': {'sh5': {'rev': 3}, 'sh6': {'rev': 2, 'aspects': ['title']}, 'sh7': 4}})
    assert out == {'sh5': 3, 'sh6': {'rev': 2, 'aspects': ['title']}, 'sh7': 4}


def test_a_word_whose_shape_cannot_be_read_never_lets_a_plain_word_pick_another(world):
    k, a, b = world
    board, meeting, talk, task = events(k, a)
    say(k, a, 'verb cal.done needs=start steps="set $1 cal_done=yes" help="cal.done <event>: done"')
    say(k, a, 'verb task.done needs=title steps="set $1 task_done=yes" help="task.done <thing>: done"')
    k.state.things[k.find_entry('cal.done')]['needs'] = 'start:time'
    out = say(k, a, f'done {board}', ok=False)
    assert k.state.get(board, 'task_done') is None                     # no silent swap to task.done


def test_a_kind_whose_shape_cannot_be_read_can_be_repaired_while_in_use(world):
    k, a, b = world
    events(k, a)
    say(k, a, 'verb meet.go acts_on=meeting steps="set $1 going=yes" help="meet.go <meeting>: going"')
    d = kind_decl(k, 'meeting')
    k.state.things[d]['needs'] = 'place:point'
    k.kinds._seen = -1
    say(k, a, f'look {d}; set {d} needs=place')
    assert k.state.get(d, 'needs') == 'place'


def test_rows_of_a_kind_nothing_is_says_so_and_points_at_a_word_of_that_name(world):
    """JEFF, 28 Oct: `rows refusals` said "0 refusalses", which read as an empty log."""
    k, a, b = world
    out = say(k, a, 'rows refusals')['text']
    assert out == 'nothing here is a refusals; refusals is a word: say refusals'
    assert 'kinds lists the kinds' in say(k, a, 'rows gizmo')['text']


def test_a_closed_kind_is_declared_once_and_a_member_cannot_shadow_it(world):
    """Values review V1 (ran): a member's later closed `kind=kind name=issue` won decl() over the steward's, with
    whatever else it said. One declaration per name per scope, closed ones too; a nearer one needs a leader."""
    k, a, b = world
    first = made(k, a, 'make kind=kind name=ticket title=Tickets')
    out = say(k, b, 'make kind=kind name=ticket title=Mine', ok=False)
    assert 'declared here already' in out['text']
    assert k.kinds.decl('ticket')[0] == first
    g = say(k, a, 'group name=crew open=no')['text'].split()[2]
    say(k, a, f'role {b.person} member in={g}')
    out = say(k, b, f'make kind=kind name=ticket in={g}', ok=False)
    assert 'its leaders declare it' in out['text']
    say(k, b, f'make kind=kind name=crewnote in={g}')                # a name of her own is hers


def test_a_child_kind_holds_only_what_is_declared_one(world):
    """Alex, 28 Oct, "Children by declaration": the trials made all 300 board events meetings by shape."""
    k, a, b = world
    board, meeting, talk, task = events(k, a)
    placed = made(k, a, 'make kind=board-item post_kind=event title="Picnic" start=2026-11-04T12:00 place=Park')
    assert placed in [r['id'] for r in say(k, a, 'rows event')['rows']]          # the parent: by shape
    assert [r['id'] for r in say(k, a, 'rows meeting')['rows']] == [meeting]       # the child: only a meeting
    say(k, a, f'mark {placed} meeting')
    assert placed in [r['id'] for r in say(k, a, 'rows meeting')['rows']]
    assert 'marked a meeting' in [r['as'] for r in say(k, a, 'rows meeting')['rows'] if r['id'] == placed][0]


def test_a_word_on_a_child_kind_refuses_an_unmarked_thing(world):
    """Kinds-intelligence review K7 (ran): a word acting on a child kind still reached things that merely had its shape."""
    k, a, b = world
    events(k, a)
    say(k, a, 'verb meet.note acts_on=meeting steps="set $1 noted=yes" help="meet.note <meeting>: note it"')
    loose = made(k, a, 'make kind=note title="Coffee" start=2026-11-08T09:00 place=Cafe')
    out = say(k, a, f'meet.note {loose}', ok=False)
    assert 'meeting' in out['text']
    assert k.state.get(loose, 'noted') is None
    say(k, a, f'mark {loose} meeting')
    say(k, a, f'meet.note {loose}')
    assert k.state.get(loose, 'noted') == 'yes'


def test_a_mark_on_a_grandchild_counts_for_every_kind_between(world):
    """Approved-builds review M7: a thing marked council was an event, but not a meeting."""
    k, a, b = world
    events(k, a)
    say(k, a, 'make kind=kind name=council extends=meeting')
    loose = made(k, a, 'make kind=note title="Ward 3" start=2026-11-10T19:00 place=Hall')
    say(k, a, f'mark {loose} council')
    assert loose in [r['id'] for r in say(k, a, 'rows council')['rows']]
    assert loose in [r['id'] for r in say(k, a, 'rows meeting')['rows']]
