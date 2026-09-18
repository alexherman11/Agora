"""Executable design model, not an Agora implementation. Run: python model.py.

A serialized in-memory authority, explicit domain routes, per-cell epochs, and
compensating undo. No distributed merge, authentication, actual render, or disk IO.
"""
from dataclasses import dataclass
from copy import deepcopy
import unittest


class Refused(Exception):
    pass


@dataclass(frozen=True)
class Cell:
    value: object
    epoch: int


@dataclass
class Event:
    actor: str
    writes: dict
    before: dict
    after_epochs: dict
    depends: frozenset
    undone: bool = False


class World:
    def __init__(self):
        self.clock = 0
        self.cells = {}
        self.events = []

    def seed(self, key, value):
        self.clock += 1
        self.cells[key] = Cell(deepcopy(value), self.clock)

    def read(self, key):
        return deepcopy(self.cells[key].value)

    def fence(self, *keys):
        return {key: self.cells[key].epoch for key in keys}

    def commit(self, actor, writes, expected, depends=()):
        # Every write must be guarded. Additional guards are semantic read inputs.
        if not set(writes) <= set(expected):
            raise Refused('unguarded write')
        if any(self.cells[key].epoch != epoch for key, epoch in expected.items()):
            raise Refused('stale dependency')
        if any(not isinstance(i, int) or i < 0 or i >= len(self.events)
               or self.events[i].undone for i in depends):
            raise Refused('invalid causal dependency')
        before = {key: deepcopy(self.cells[key].value) for key in writes}
        epochs = {}
        for key, value in writes.items():
            self.seed(key, value)
            epochs[key] = self.cells[key].epoch
        event = Event(actor, deepcopy(writes), before, epochs, frozenset(depends))
        self.events.append(event)
        return len(self.events) - 1

    def undo(self, actor, index):
        event = self.events[index]
        if event.actor != actor or event.undone:
            raise Refused('wrong actor or already compensated')
        if any(not later.undone and index in later.depends for later in self.events):
            raise Refused('accepted work depends on this change')
        result = self.commit(actor, event.before, event.after_epochs)
        event.undone = True
        return result


class Desk:
    """A theme and two occurrences of the same paragraph; roles are contextual."""
    def __init__(self):
        self.w = World()
        for key, value in {
            'p.text': 'hello', 'theme.width': 100,
            'a.override': None, 'b.override': None,
            'a.binding': 'p', 'b.binding': 'p',
            'a.mapping': 1, 'b.mapping': 1,
        }.items():
            self.w.seed(key, value)

    def observe(self, occurrence):
        subject = self.w.read(occurrence + '.binding')
        return self.w.fence(occurrence + '.binding', occurrence + '.mapping',
                            occurrence + '.override', subject + '.text', 'theme.width')

    def effective_width(self, occurrence):
        local = self.w.read(occurrence + '.override')
        return self.w.read('theme.width') if local is None else local

    def change(self, actor, occurrence, route, value, observation):
        binding = occurrence + '.binding'
        if observation.get(binding) != self.w.cells[binding].epoch:
            raise Refused('stale binding')
        subject = self.w.read(binding)
        routes = {'content': subject + '.text', 'shared': 'theme.width',
                  'local': occurrence + '.override'}
        if route not in routes:
            raise Refused('choose content, shared, or local; output is ambiguous')
        key = routes[route]
        required = {key, occurrence + '.binding'}
        if route in ('shared', 'local'):
            # This model treats these as graphical width gestures.
            required |= {occurrence + '.mapping'}
        expected = {k: observation[k] for k in required}
        return self.w.commit(actor, {key: value}, expected)


class Counterexamples(unittest.TestCase):
    def test_two_lawful_backward_maps_do_not_determine_intent(self):
        # get(a,b)=a+b. Both preserve untouched views and realize every requested
        # sum, yet choose different source edits. Lens laws cannot choose scope.
        puts = [lambda v, s: (v-s[1], s[1]), lambda v, s: (s[0], v-s[0])]
        for put in puts:
            for a in range(-3, 4):
                for b in range(-3, 4):
                    self.assertEqual(put(a+b, (a,b)), (a,b))
                    for target in range(-3, 4):
                        self.assertEqual(sum(put(target, (a,b))), target)
        self.assertNotEqual(puts[0](8, (2,3)), puts[1](8, (2,3)))

    def test_ambiguous_output_has_no_silent_default(self):
        d = Desk()
        with self.assertRaises(Refused):
            d.change('human', 'a', 'auto', 120, d.observe('a'))
        self.assertEqual(d.w.events, [])

    def test_shared_and_local_routes_have_different_fanout(self):
        d = Desk()
        d.change('human', 'a', 'shared', 120, d.observe('a'))
        self.assertEqual([d.effective_width(x) for x in ('a','b')], [120,120])
        d.change('human', 'a', 'local', 140, d.observe('a'))
        self.assertEqual([d.effective_width(x) for x in ('a','b')], [140,120])

    def test_content_identity_survives_reflow_but_pointer_mapping_does_not(self):
        d = Desk()
        old = d.observe('a')
        d.w.seed('a.mapping', 2)
        d.change('agent', 'a', 'content', 'revised', old)
        with self.assertRaises(Refused):
            d.change('human', 'a', 'local', 180, old)

    def test_same_subject_edit_updates_both_occurrences(self):
        d = Desk()
        d.change('agent', 'b', 'content', 'new', d.observe('b'))
        self.assertEqual(d.w.read(d.w.read('a.binding')+'.text'), 'new')
        self.assertEqual(d.w.read(d.w.read('b.binding')+'.text'), 'new')

    def test_stale_binding_never_silently_retargets(self):
        d = Desk()
        old = d.observe('a')
        d.w.seed('a.binding', 'another-subject')
        with self.assertRaises(Refused):
            d.change('agent', 'a', 'content', 'wrong', old)
        self.assertEqual(d.w.read('p.text'), 'hello')

    def test_fresh_rebinding_targets_new_subject(self):
        d = Desk()
        d.w.seed('q.text', 'other')
        d.w.seed('a.binding', 'q')
        d.change('agent', 'a', 'content', 'edited q', d.observe('a'))
        self.assertEqual(d.w.read('q.text'), 'edited q')
        self.assertEqual(d.w.read('p.text'), 'hello')

    def test_negative_dependency_refuses_without_mutation(self):
        d = Desk()
        with self.assertRaises(Refused):
            d.w.commit('agent', {'p.text': 'wrong'}, d.w.fence('p.text'), [-1])
        self.assertEqual(d.w.read('p.text'), 'hello')

    def test_undo_style_keeps_later_content(self):
        d = Desk()
        e = d.change('human', 'a', 'shared', 150, d.observe('a'))
        d.change('agent', 'b', 'content', 'important new work', d.observe('b'))
        d.w.undo('human', e)
        self.assertEqual(d.w.read('theme.width'), 100)
        self.assertEqual(d.w.read('p.text'), 'important new work')

    def test_undo_local_override_reveals_current_shared_rule(self):
        d = Desk()
        e = d.change('human', 'a', 'local', 150, d.observe('a'))
        d.change('agent', 'b', 'shared', 130, d.observe('b'))
        d.w.undo('human', e)
        # Undo restores absence of override, not the old rendered width 100.
        self.assertEqual(d.effective_width('a'), 130)

    def test_aba_same_value_does_not_make_undo_safe(self):
        d = Desk()
        e = d.change('human', 'a', 'shared', 150, d.observe('a'))
        d.change('agent', 'b', 'shared', 160, d.observe('b'))
        d.change('agent', 'b', 'shared', 150, d.observe('b'))
        with self.assertRaises(Refused):
            d.w.undo('human', e)
        self.assertEqual(d.w.read('theme.width'), 150)

    def test_accepted_causal_dependence_blocks_compensation(self):
        d = Desk()
        e = d.change('human', 'a', 'shared', 150, d.observe('a'))
        d.w.commit('agent', {'p.text': 'caption fitted to width'},
                   d.w.fence('p.text', 'theme.width'), depends=[e])
        with self.assertRaises(Refused):
            d.w.undo('human', e)

    def test_atomic_refusal_does_not_undo_unrelated_cell(self):
        w = World()
        w.seed('x', 0)
        w.seed('y', 0)
        e = w.commit('human', {'x': 1, 'y': 1}, w.fence('x','y'))
        w.commit('agent', {'y': 2}, w.fence('y'))
        with self.assertRaises(Refused):
            w.undo('human', e)
        self.assertEqual([w.read('x'), w.read('y')], [1,2])

    def test_actor_and_double_compensation(self):
        d = Desk()
        e = d.change('human', 'a', 'shared', 150, d.observe('a'))
        with self.assertRaises(Refused):
            d.w.undo('agent', e)
        d.w.undo('human', e)
        with self.assertRaises(Refused):
            d.w.undo('human', e)


if __name__ == '__main__':
    unittest.main(verbosity=2)
