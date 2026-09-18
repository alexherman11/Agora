"""Read-only conformance probes against Claude's actual scene/style bridge.
No sessions, network, HTTP server, world persistence or production imports are used.
DEFECT tests assert observed failures of the stated contract, not desired behavior.
"""
from pathlib import Path
from types import SimpleNamespace
import copy
import hashlib
import json
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
NOTATION = ROOT / 'research/text-desk-lab/notation'
sys.dont_write_bytecode = True
sys.path.insert(0, str(NOTATION))
import scene
from world import World
from desk_knife import DeskKnife

FILES = ['scene.py', 'desk-shell/lens.js', 'desk-shell/lens.html',
         'desk-shell/style/style.js', 'desk-shell/style/calm.style', 'deskd.py',
         'desk-shell/core.js', 'world.py', 'desk.py', 'desk_moo.py', 'desk_knife.py']
HASHES = {name: hashlib.sha256((NOTATION/name).read_bytes()).hexdigest() for name in FILES}


def real_desk(text='Original body', tags=('one', 'two')):
    w = World()
    w.me = 'alice'
    sid = w.add_subject('note', 'Shared subject', text, tags)
    a = w.place(sid, w.root, 10, 20, 160, 100)
    b = w.place(sid, w.root, 220, 20, 160, 100)
    d = DeskKnife(w, 'lean')
    d.batch = True
    d.lean = True
    d.read_cap = 4
    d.ids = {}
    return d, sid, a, b


def command(desk, line):
    return desk.dispatch('desk', {'line': line})


class SceneConformance(unittest.TestCase):
    def test_SUPPORTED_subject_and_appearance_binding_remain_distinct(self):
        d, sid, a, b = real_desk()
        sc = scene.build(d, 'root : free, of kind:note, each card\ncard : at item, text $id / $item / $text')
        self.assertEqual([n['item'] for n in sc['kids']], [a, b])
        self.assertEqual([n['box'][0] for n in sc['kids']], [10, 220])
        self.assertTrue(all(sid in n['text'] for n in sc['kids']))
        self.assertNotEqual(sc['kids'][0]['key'], sc['kids'][1]['key'])
        self.assertEqual(d.world.events, [])

    def test_SUPPORTED_instance_keys_survive_selection_reorder(self):
        d, sid, a, b = real_desk()
        ids = [a, b]
        fake = SimpleNamespace(world=d.world, _parse_selection=lambda _: (ids, 'fixture'))
        src = 'root : column, of whatever, each card\ncard : text $item'
        first = {n['item']: n['key'] for n in scene.build(fake, src)['kids']}
        ids.reverse()
        second = {n['item']: n['key'] for n in scene.build(fake, src)['kids']}
        self.assertEqual(first, second)

    def test_SUPPORTED_unknown_property_and_missing_part_refused(self):
        for src in ['root : teleport moon', 'root : of kind:note, each missing']:
            with self.assertRaises(scene.LensRefusal):
                scene.parse(src)

    def test_REPAIRED_text_preserves_short_tail_and_discloses_long_cut(self):
        d, *_ = real_desk()
        text = 'a' * 101 + 'VISIBLE_TAIL'
        sc = scene.build(d, 'root : text ' + text)
        out = scene.to_text(sc, 'fixture', 'alice', 0)
        self.assertEqual(sc['text'], text)
        self.assertIn(text, out)
        long_text = 'a' * 300 + 'VISIBLE_TAIL'
        long_scene = scene.build(d, 'root : text ' + long_text)
        long_out = scene.to_text(long_scene, 'fixture', 'alice', 0)
        self.assertEqual(long_scene['text'], long_text)
        self.assertNotIn('VISIBLE_TAIL', long_out)
        self.assertIn('=240 of ' + str(len(long_text)) + ' chars printed here', long_out)
        self.assertIn('for all', long_out)

    def test_DEFECT_literal_comma_space_is_not_quote_aware(self):
        with self.assertRaises(scene.LensRefusal):
            scene.parse('root : text "Hello, world"')

    def test_DEFECT_comment_marker_inside_text_loses_suffix(self):
        d, *_ = real_desk()
        sc = scene.build(d, 'root : text "Keep # this literal"')
        self.assertEqual(sc['text'], 'Keep')

    def test_DEFECT_literal_backslash_n_is_reparsed_as_structure(self):
        with self.assertRaises(scene.LensRefusal):
            scene.parse(r'root : text "C:\notes"')

    def test_REPAIRED_advertised_count_placeholder_is_bound(self):
        d, *_ = real_desk()
        sc = scene.build(d, 'root : text $n notes, of kind:note, each card\ncard : text $title')
        self.assertEqual(sc['n'], 2)
        self.assertEqual(sc['text'], '2 notes')
        self.assertIn('2 notes', scene.to_text(sc, 'fixture', 'alice', 0))

    def test_DEFECT_recursive_each_raises_python_error_not_lens_refusal(self):
        d, *_ = real_desk()
        fake = SimpleNamespace(world=d.world, _parse_selection=lambda _: ([next(iter(d.world.nodes))], 'fixture'))
        with self.assertRaises(RecursionError):
            scene.build(fake, 'root : of anything, each root')

    def test_DEFECT_no_scene_node_budget_at_1200_instances(self):
        d, _, a, _ = real_desk()
        ids = []
        for i in range(1200):
            ident = 'fixture' + str(i)
            d.world.nodes[ident] = dict(d.world.nodes[a], id=ident)
            ids.append(ident)
        fake = SimpleNamespace(world=d.world, _parse_selection=lambda _: (ids, 'fixture'))
        sc = scene.build(fake, 'root : column, of fixture, each card\ncard : text $title')
        self.assertEqual(len(sc['kids']), 1200)

    def test_DEFECT_duplicate_part_definition_silently_replaces_first(self):
        d, *_ = real_desk()
        sc = scene.build(d, 'root : text first\nroot : text second')
        self.assertEqual(sc['text'], 'second')

    def test_DEFECT_duplicate_child_names_produce_duplicate_scene_keys(self):
        d, *_ = real_desk()
        sc = scene.build(d, 'root : column\n  child : text first\n  child : text second')
        self.assertEqual(sc['kids'][0]['key'], sc['kids'][1]['key'])
        self.assertNotEqual(sc['kids'][0]['text'], sc['kids'][1]['text'])

    def test_LIMIT_tag_repeat_keys_are_positions_not_value_identities(self):
        d, sid, *_ = real_desk()
        src = 'root : column, of kind:note, each card\ncard : row, over $tags, each tag\ntag : text $it'
        a = scene.build(d, src)['kids'][0]['kids'][0]
        d.world.subjects[sid]['tags'].reverse()
        b = scene.build(d, src)['kids'][0]['kids'][0]
        self.assertEqual(a['key'], b['key'])
        self.assertNotEqual(a['text'], b['text'])

    def test_DEFECT_unescaped_subject_text_changes_command_literal(self):
        d, sid, a, _ = real_desk('She said "yes"')
        sc = scene.build(d, 'root : column, of kind:note, each card\ncard : on click do do rewrite $item text="$text"')
        line = sc['kids'][0]['acts'][0]['line']
        command(d, 'look ' + a)
        result = command(d, line)
        self.assertNotIn('error', result)
        self.assertEqual(d.world.subjects[sid]['text'], 'She said yes')

    def test_DEFECT_fresh_look_prefix_bypasses_original_scene_staleness(self):
        d, sid, a, _ = real_desk()
        command(d, 'look ' + a)
        d.world.me = 'bob'
        command(d, 'look ' + a)
        command(d, f'do rewrite {a} text="Other author"')
        d.world.me = 'alice'
        # Restore Alice's old seen revision; _seen_idx still records her old observation.
        d.seen[a] = 1
        first = command(d, f'do rewrite {a} text="Old pixels draft"')
        self.assertIn('stale', first.get('text', '') + first.get('error', ''))
        second = command(d, f'look {a}; do rewrite {a} text="Old pixels draft"')
        self.assertNotIn('stale', second.get('text', '') + second.get('error', ''))
        self.assertEqual(d.world.subjects[sid]['text'], 'Old pixels draft')

    def test_DEFECT_drop_is_admitted_to_scene_without_painter_handler(self):
        d, *_ = real_desk()
        sc = scene.build(d, 'root : on drop do do link $item $other as=refers')
        self.assertEqual(sc['acts'][0]['on'], 'drop')
        painter = (NOTATION/'desk-shell/lens.js').read_text()
        self.assertNotIn('a.on === "drop"', painter)

    def test_DEFECT_scene_has_no_observed_revision_binding(self):
        d, *_ = real_desk()
        sc = scene.build(d, 'root : column, of kind:note, each card\ncard : text $title, on click do read $item')
        node = sc['kids'][0]
        self.assertNotIn('rev', node)
        self.assertNotIn('subjectRev', node)
        self.assertNotIn('expected', node['acts'][0])

    def test_style_compiler_observed_outputs(self):
        node = Path('C:/Users/Alex/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
        script = r'''
const fs=require('node:fs'),vm=require('node:vm');
const sheets=[];
const context={document:{createElement:()=>({textContent:''}),head:{appendChild:s=>sheets.push(s)}}};
vm.createContext(context);
vm.runInContext(fs.readFileSync(process.argv[2],'utf8')+'\nglobalThis.TestStyle=Style;',context);
const S=context.TestStyle;
S.install('token ink = #111111\nrole card : ink');
const previous=sheets[0].textContent;
let syntaxRefused=false;
try{S.install('token ink = #111111\nrole card : pad 9px');}catch(e){syntaxRefused=true;}
const lastGood=previous===sheets[0].textContent;
S.install('token ink = #111111\nrole card : pad missingToken');
const unreadable=S.look({as:'card'}).unreadable;
const unknownAccepted=S.style.roles.card.props[0]==='pad missingToken';
S.install('token sneaky = ok; outline: 99px solid red\nrole card : text');
const rawCSS=sheets[0].textContent.includes('--t-sneaky:ok; outline: 99px solid red');
process.stdout.write(JSON.stringify({syntaxRefused,lastGood,unknownAccepted,unreadable,rawCSS}));
'''
        run = subprocess.run([str(node), '-', str(NOTATION/'desk-shell/style/style.js')], input=script, text=True, capture_output=True, timeout=15, check=True)
        observed = json.loads(run.stdout)
        self.assertTrue(observed['syntaxRefused'])
        self.assertTrue(observed['lastGood'])
        self.assertTrue(observed['unknownAccepted'])
        self.assertEqual(len(observed['unreadable']), 1)
        self.assertTrue(observed['rawCSS'])
        print('STYLE_OBSERVATIONS ' + json.dumps(observed, sort_keys=True))


if __name__ == '__main__':
    print('SOURCE_HASHES ' + json.dumps(HASHES, sort_keys=True), flush=True)
    result = unittest.main(exit=False, verbosity=2).result
    after = {name: hashlib.sha256((NOTATION/name).read_bytes()).hexdigest() for name in FILES}
    unchanged = HASHES == after
    print('SOURCE_UNCHANGED_DURING_RUN ' + str(unchanged), flush=True)
    sys.exit(0 if result.wasSuccessful() and unchanged else 1)
