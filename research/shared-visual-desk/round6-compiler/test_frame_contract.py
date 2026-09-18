from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
NOTATION = Path(__file__).resolve().parents[2] / 'text-desk-lab' / 'notation'
sys.path.insert(0, str(NOTATION))
from world import World
from desk_knife import DeskKnife
from frame_contract import compile_frame, check_frame, dependency_signature, FrameRefusal

SOURCE = '''root : free, of kind:note, each card
card : column, at item
  body : text $text, on edit do rewrite $id text="$value"
'''


def fixture():
    w = World(); w.me = 'alice'
    sid = w.add_subject('note', 'Material', 'Line one\nLine two', ('tag',))
    a = w.place(sid, w.root, 10, 20, 140, 100)
    b = w.place(sid, w.root, 200, 20, 140, 100)
    lens = w.add_subject('note', 'Definition', SOURCE, ('lens',))
    d = DeskKnife(w, 'lean'); d.batch = True; d.lean = True; d.read_cap = 4; d.ids = {}
    return d, lens, sid, a, b


class FrameChecks(unittest.TestCase):
    def test_candidate_uses_actual_scene_and_printer_with_no_world_mutation(self):
        d, lens, sid, a, b = fixture(); before = deepcopy(d.snapshot()); seen = deepcopy(d.seen)
        f = compile_frame(d, lens)
        self.assertEqual(d.snapshot(), before); self.assertEqual(d.seen, seen)
        self.assertTrue(check_frame(d, f)['ok'])
        self.assertIn('Line one', f['inspection']['text'])
        for node in f['scene']['kids']:
            self.assertIn('line', node['kids'][0]['acts'][0])
        self.assertEqual(f['inspection']['node_count'], len(f['bindings']))
        self.assertEqual(f['dependencies'], dependency_signature(d))

    def test_two_appearances_have_distinct_binding_shared_subject_and_provenance(self):
        d, lens, sid, a, b = fixture(); f = compile_frame(d, lens)
        left = f['bindings']['root/' + a]; right = f['bindings']['root/' + b]
        self.assertEqual(left['subject'], right['subject']); self.assertEqual(left['subject']['id'], sid)
        self.assertNotEqual(left['appearance']['id'], right['appearance']['id'])
        self.assertEqual(left['parent']['id'], d.world.root)
        self.assertEqual(left['provenance']['source_lines'], [2])
        self.assertIn('candidates', left['provenance']['precision'])

    def test_source_override_compiles_without_requiring_candidate_in_world(self):
        d, lens, *_ = fixture(); old = d.world.subjects[lens]['text']
        candidate = 'root : column\n  heading : text Candidate view'
        f = compile_frame(d, lens, source=candidate)
        self.assertEqual(d.world.subjects[lens]['text'], old)
        self.assertNotEqual(f['definition']['source_sha256'], f['definition']['observed_source_sha256'])
        self.assertTrue(check_frame(d, f)['ok'])
        self.assertIn('Candidate view', f['inspection']['text'])

    def test_conservative_fence_detects_unrelated_changes_without_refreshing_frame(self):
        d, lens, *_ = fixture(); f = compile_frame(d, lens)
        d.world.add_subject('note', 'Unrelated', 'new')
        r = check_frame(d, f); self.assertFalse(r['ok'])
        self.assertIn('dependencies-changed', [x['code'] for x in r['diagnostics']])
        self.assertNotEqual(dependency_signature(d), f['dependencies'])

    def test_definition_revision_and_in_place_text_change_detected(self):
        for bump in (False, True):
            d, lens, *_ = fixture(); f = compile_frame(d, lens)
            d.world.subjects[lens]['text'] = 'root : text changed'
            if bump: d.world.subjects[lens]['rev'] += 1
            self.assertIn('definition-changed', [x['code'] for x in check_frame(d, f)['diagnostics']])

    def test_source_generation_change_refuses_without_mutating_sources(self):
        d, lens, *_ = fixture(); f = compile_frame(d, lens)
        with patch('frame_contract._source_hashes', return_value={'scene_sha256':'changed','style_sha256':'changed'}):
            self.assertIn('compiler-changed', [x['code'] for x in check_frame(d, f)['diagnostics']])

    def test_invalid_definition_has_structured_refusal_no_world_change(self):
        d, lens, *_ = fixture(); before = dependency_signature(d)
        with self.assertRaises(FrameRefusal) as caught:
            compile_frame(d, lens, source='root : browser-js run anything')
        self.assertEqual(caught.exception.code, 'lens-refused')
        self.assertEqual(before, dependency_signature(d))

    def test_external_worktree_rows_explicitly_refused_static_and_dynamic(self):
        d, lens, sid, *_ = fixture()
        with self.assertRaises(FrameRefusal) as caught:
            compile_frame(d, lens, source='root : column, of worktrees, each row\nrow : text $name')
        self.assertEqual(caught.exception.code, 'external-row-source')
        d.world.subjects[sid]['title'] = 'worktrees'
        source = 'root : column, of kind:note, each card\ncard : column, of $title, each row\nrow : text $name'
        with self.assertRaises(FrameRefusal) as caught:
            compile_frame(d, lens, source=source)
        self.assertEqual(caught.exception.code, 'external-row-source')

    def test_event_tail_limit_is_disclosed_in_inspection(self):
        d, lens, sid, *_ = fixture()
        d.world.events = [{'id':'e'+str(i),'verb':'rewrite','target':sid,'by':'alice'} for i in range(25)]
        f = compile_frame(d, lens, source='root : column, of events, each row\nrow : text $eid $verb')
        self.assertEqual(f['scene']['n'], 20)
        self.assertTrue(any('last 20 events' in w for w in f['inspection']['limitations']))
        self.assertEqual(f['dependencies']['world_event_count'], 25)

    def test_local_actor_reader_state_is_a_dependency_not_online_presence(self):
        d, lens, *_ = fixture(); d._per = {'alice': ({}, {d.world.root}, 0)}
        f = compile_frame(d, lens, source='root : column, of actors, each row\nrow : text $name $read')
        d._per['alice'] = ({}, {d.world.root}, 1)
        self.assertFalse(check_frame(d, f)['ok'])
        self.assertTrue(any('no measured pixels' in w for w in f['inspection']['limitations']))

    def test_retained_frame_mutation_detected(self):
        d, lens, *_ = fixture(); f = compile_frame(d, lens)
        f['scene']['kids'][0]['text'] = 'tampered'
        self.assertIn('frame-integrity', [x['code'] for x in check_frame(d, f)['diagnostics']])

    def test_compiler_duplicate_and_recursive_definitions_remain_refusals(self):
        d, lens, *_ = fixture()
        for src in ['root : text one\nroot : text two', 'root : of kind:note, each root']:
            with self.assertRaises(FrameRefusal) as caught:
                compile_frame(d, lens, source=src)
            self.assertEqual(caught.exception.code, 'lens-refused')


    def test_nested_lens_retains_inner_definition_revision_and_origin(self):
        d, lens, sid, *_ = fixture()
        inner = d.world.add_subject('note', 'Inner', 'inner : column, of kind:note, each card\ncard : text $text, on edit do rewrite $id text="$value"', ('lens',))
        f = compile_frame(d, lens, source='root : column\n  panel : lens Inner')
        bindings = [b for b in f['bindings'].values() if len(b['definition_chain']) == 2]
        self.assertTrue(bindings)
        self.assertEqual(bindings[0]['definition_chain'][-1]['id'], inner)
        self.assertEqual(bindings[0]['provenance']['definition'], inner)
        self.assertEqual({x['id'] for x in f['definitions']}, {lens, inner})
        d.world.subjects[inner]['rev'] += 1
        self.assertFalse(check_frame(d, f)['ok'])

    def test_root_definition_numeric_props_reach_actual_spread_compiler(self):
        d, lens, sid, a, b = fixture()
        d.world.subjects[lens]['props'] = {'spacing': 75}
        source = 'root : free, of kind:note, each card, spread x 20 step $spacing to 440\ncard : column, at item\n  body : text $text'
        before = deepcopy(d.snapshot())
        f = compile_frame(d, lens, source=source)
        self.assertEqual([kid['box'][0] for kid in f['scene']['kids']], [20, 95])
        self.assertEqual(d.snapshot(), before)
        self.assertTrue(check_frame(d, f)['ok'])
        d.world.subjects[lens]['props']['spacing'] = 120
        self.assertFalse(check_frame(d, f)['ok'])

    def test_nested_external_worktree_source_is_also_refused(self):
        d, lens, *_ = fixture()
        d.world.add_subject('note', 'External', 'inner : column, of worktrees, each row\nrow : text $name', ('lens',))
        with self.assertRaises(FrameRefusal) as caught:
            compile_frame(d, lens, source='root : lens External')
        self.assertEqual(caught.exception.code, 'external-row-source')


if __name__ == '__main__':
    from frame_contract import _source_hashes
    before = _source_hashes()
    print('ACTUAL_COMPILER_SOURCES', before, flush=True)
    result = unittest.main(verbosity=2, exit=False).result
    after = _source_hashes()
    print('ACTUAL_COMPILER_SOURCES_AFTER', after, flush=True)
    print('SOURCES_STABLE_DURING_SUITE', before == after, flush=True)
    sys.exit(0 if result.wasSuccessful() and before == after else 1)
