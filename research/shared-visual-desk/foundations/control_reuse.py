"""Control reuse countermodel. No UI, media, audio, concurrency or Agora runtime.

Compare direct references and scoped relational lookup under the SAME policy.
A sample yields a domain request, not a claimed external effect.
"""
from dataclasses import dataclass, replace
from copy import deepcopy
import unittest


@dataclass
class Target:
    identity: str
    incarnation: int = 1
    value: float = 0.0
    content_revision: int = 1


@dataclass(frozen=True)
class Binding:
    target: Target
    mapping: str
    operation: str
    interpreter: str
    theme: str = 'shared-theme'


@dataclass(frozen=True)
class Gesture:
    binding: Binding
    target_incarnation: int

    def request(self, normalized):
        if not 0 <= normalized <= 1:
            raise ValueError('sample outside declared control domain')
        if self.binding.target.incarnation != self.target_incarnation:
            raise ValueError('target incarnation changed')
        value = normalized if self.binding.mapping == 'linear-opacity' else .25 * 16 ** normalized
        return dict(target=self.binding.target.identity,
                    incarnation=self.target_incarnation,
                    operation=self.binding.operation, value=value,
                    interpreter=self.binding.interpreter)


class Direct:
    def __init__(self):
        self.bindings = {}

    def bind(self, occurrence, binding):
        self.bindings[occurrence] = binding

    def resolve(self, occurrence):
        return self.bindings[occurrence]


class Relational:
    def __init__(self):
        self.claims = {}

    def bind(self, occurrence, binding):
        # This deliberately selects one scoped claim. It is not a general solver.
        self.claims[('uses', occurrence)] = [binding]

    def resolve(self, occurrence):
        claims = self.claims[('uses', occurrence)]
        if len(claims) != 1:
            raise ValueError('ambiguous scoped binding')
        return claims[0]


def begin(engine, occurrence):
    binding = engine.resolve(occurrence)
    return Gesture(binding, binding.target.incarnation)


def fork_control(engine, old, new, new_target):
    # The important policy is explicit in both engines: target forked, theme kept.
    engine.bind(new, replace(engine.resolve(old), target=new_target))


class Counterexamples(unittest.TestCase):
    def candidates(self):
        for cls in (Direct, Relational):
            with self.subTest(candidate=cls.__name__):
                yield cls()

    def test_reuse_changes_meaning_not_only_scalar_range(self):
        for e in self.candidates():
            e.bind('slider', Binding(Target('image'), 'linear-opacity', 'set-opacity', 'opacity-v1'))
            self.assertEqual(begin(e, 'slider').request(.5)['value'], .5)
            e.bind('slider', Binding(Target('player'), 'log-rate', 'request-rate', 'rate-v2'))
            r = begin(e, 'slider').request(.5)
            self.assertEqual((r['operation'], r['value'], r['interpreter']), ('request-rate', 1., 'rate-v2'))

    def test_copy_forks_target_but_keeps_theme(self):
        for e in self.candidates():
            e.bind('old', Binding(Target('old-player'), 'log-rate', 'request-rate', 'rate-v2'))
            fork_control(e, 'old', 'copy', Target('new-player'))
            self.assertEqual(e.resolve('old').theme, e.resolve('copy').theme)
            self.assertNotEqual(begin(e, 'old').request(.5)['target'], begin(e, 'copy').request(.5)['target'])

    def test_rebind_future_does_not_retarget_admitted_gesture(self):
        for e in self.candidates():
            e.bind('slider', Binding(Target('image'), 'linear-opacity', 'set-opacity', 'opacity-v1'))
            active = begin(e, 'slider')
            e.bind('slider', Binding(Target('player'), 'log-rate', 'request-rate', 'rate-v2'))
            self.assertEqual(active.request(.5)['target'], 'image')
            self.assertEqual(begin(e, 'slider').request(.5)['target'], 'player')

    def test_two_occurrences_have_independent_active_routes(self):
        for e in self.candidates():
            e.bind('mine', Binding(Target('image'), 'linear-opacity', 'set-opacity', 'opacity-v1'))
            e.bind('yours', Binding(Target('player'), 'log-rate', 'request-rate', 'rate-v2'))
            self.assertEqual(begin(e, 'mine').request(.5)['value'], .5)
            self.assertEqual(begin(e, 'yours').request(.5)['value'], 1.)

    def test_content_revision_irrelevant_to_opacity_target(self):
        for e in self.candidates():
            t = Target('image')
            e.bind('slider', Binding(t, 'linear-opacity', 'set-opacity', 'opacity-v1'))
            active = begin(e, 'slider')
            t.content_revision += 1
            self.assertEqual(active.request(.3)['value'], .3)

    def test_recreated_target_refuses_old_gesture(self):
        for e in self.candidates():
            t = Target('image')
            e.bind('slider', Binding(t, 'linear-opacity', 'set-opacity', 'opacity-v1'))
            active = begin(e, 'slider')
            t.incarnation += 1
            with self.assertRaises(ValueError):
                active.request(.3)

    def test_naive_deep_copy_wrongly_forks_shared_theme_object(self):
        theme = {'name': 'theme', 'color': 'blue'}
        copied = deepcopy({'target': Target('image'), 'theme': theme})
        theme['color'] = 'red'
        self.assertEqual(copied['theme']['color'], 'blue')

    def test_global_relation_alias_would_couple_copied_controls(self):
        e = Relational()
        e.bind('global-slider', Binding(Target('image'), 'linear-opacity', 'set-opacity', 'opacity-v1'))
        # Giving both appearances the same relation address rebinds both.
        aliases = {'original': 'global-slider', 'copy': 'global-slider'}
        e.bind(aliases['copy'], Binding(Target('player'), 'log-rate', 'request-rate', 'rate-v2'))
        self.assertEqual(begin(e, aliases['original']).request(.5)['target'], 'player')

    def test_conflicting_relations_do_not_silently_choose(self):
        e = Relational()
        a = Binding(Target('a'), 'linear-opacity', 'set-opacity', 'opacity-v1')
        b = Binding(Target('b'), 'linear-opacity', 'set-opacity', 'opacity-v1')
        e.claims[('uses', 'slider')] = [a, b]
        with self.assertRaises(ValueError):
            begin(e, 'slider')


if __name__ == '__main__':
    unittest.main(verbosity=2)
