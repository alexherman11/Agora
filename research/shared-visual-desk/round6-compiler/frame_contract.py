"""Revision-bound frame metadata over Claude's actual scene compiler.

Caller must hold its world-owner lock across capture/compile and check/activation.
No action execution, scene parser, renderer, world owner or session loading here.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from types import ModuleType

NOTATION = Path(__file__).resolve().parents[2] / 'text-desk-lab' / 'notation'
SCENE_PATH = NOTATION / 'scene.py'
STYLE_PATH = NOTATION / 'desk-shell' / 'style' / 'calm.style'
MAX_SOURCE = 65536
MAX_JSON_BYTES = 8 * 1024 * 1024


class FrameRefusal(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.diagnostics = [{'code': code, 'message': message}]


def _json_value(value, depth=0):
    if depth > 64:
        raise FrameRefusal('dependency-depth', 'Dependency data exceeds depth 64')
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, dict):
        if not all(isinstance(k, str) for k in value):
            raise FrameRefusal('dependency-type', 'Dependency object keys must be strings')
        return {k: _json_value(v, depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(v, depth + 1) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_json_value(v, depth + 1) for v in value), key=lambda x: json.dumps(x, sort_keys=True))
    raise FrameRefusal('dependency-type', 'Non-JSON dependency value: ' + type(value).__name__)


def _encoded(value):
    try:
        encoded = json.dumps(_json_value(value), sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (TypeError, ValueError) as exc:
        if isinstance(exc, FrameRefusal):
            raise
        raise FrameRefusal('dependency-type', str(exc)) from exc
    if len(encoded) > MAX_JSON_BYTES:
        raise FrameRefusal('dependency-size', 'Frame/dependency data exceeds 8 MiB')
    return encoded


def _digest(value):
    return sha256(_encoded(value)).hexdigest()


def _source_hashes():
    try:
        return {'scene_sha256': sha256(SCENE_PATH.read_bytes()).hexdigest(),
                'style_sha256': sha256(STYLE_PATH.read_bytes()).hexdigest()}
    except OSError as exc:
        raise FrameRefusal('compiler-source', str(exc)) from exc


def dependency_signature(desk):
    """Conservative preview/activation fence, NOT an action dependency policy."""
    payload = {'snapshot': desk.snapshot(), 'events': desk.world.events,
               'readers': getattr(desk, '_per', {}), 'actor': desk.world.me,
               'handles': getattr(desk, 'vars', None), 'aliases': getattr(desk, 'ids', {}),
               'last_created': desk.world.last_created, 'last_surface': desk.world.last_surface}
    return {'scope': 'conservative-world-snapshot', 'digest': _digest(payload),
            'world_event_count': len(desk.world.events)}


class _CompilationDesk:
    """Delegate to isolated snapshot while refusing compiler session-file rows."""
    def __init__(self, desk):
        self._desk = desk

    def __getattr__(self, name):
        if name == '_session':
            raise FrameRefusal('external-row-source', 'worktrees rows read external saved sessions; this frame adapter does not admit them')
        return getattr(self._desk, name)


def _load_actual_compiler(source_bytes):
    # Load these exact trusted host-source bytes, avoiding stale sys.modules and
    # bytecode files. This is not execution of authored lens text.
    module = ModuleType('_revision_bound_actual_scene')
    module.__file__ = str(SCENE_PATH)
    exec(compile(source_bytes, str(SCENE_PATH), 'exec'), module.__dict__)
    return module


def compile_frame(desk, definition_id, *, source=None, actor=None):
    """Compile a candidate without changing the anchor definition or caller desk."""
    if not isinstance(definition_id, str) or not definition_id:
        raise FrameRefusal('definition', 'Definition id must be a nonempty string')
    before = dependency_signature(desk)
    hashes = _source_hashes()
    scene_bytes = SCENE_PATH.read_bytes()
    if sha256(scene_bytes).hexdigest() != hashes['scene_sha256']:
        raise FrameRefusal('compiler-changed', 'Compiler changed while capturing source')
    snapshot = deepcopy(desk)
    definition = snapshot.world.subjects.get(definition_id)
    if not definition or 'lens' not in definition.get('tags', []):
        raise FrameRefusal('definition', 'Definition must be an existing lens subject')
    authored = definition['text'] if source is None else source
    if not isinstance(authored, str) or len(authored.encode('utf-8')) > MAX_SOURCE:
        raise FrameRefusal('source-size', 'Lens source must be a string up to 64 KiB')
    actor = snapshot.world.me if actor is None else actor
    if not isinstance(actor, str):
        raise FrameRefusal('actor', 'Actor must be a label string')
    snapshot.world.me = actor
    compiler = _load_actual_compiler(scene_bytes)
    try:
        # Reuse the actual parser for provenance; do not introduce another grammar.
        _, parts = compiler.parse(authored)
        origins = {}
        def collect(node):
            origins.setdefault(node['name'], []).append(node['line'])
            if (node.get('of') or '').strip() == 'worktrees':
                raise FrameRefusal('external-row-source', 'worktrees rows require external session dependencies not admitted by this adapter')
            for child in node['kids']:
                collect(child)
        for part in parts.values():
            collect(part)
        tree = compiler.build(_CompilationDesk(snapshot), authored, props=definition.get('props') or {})
        printed = compiler.to_text(tree, definition['title'], actor, len(snapshot.world.events))
    except FrameRefusal:
        raise
    except compiler.LensRefusal as exc:
        raise FrameRefusal('lens-refused', str(exc)) from exc
    except (RecursionError, KeyError, TypeError, ValueError) as exc:
        raise FrameRefusal('compiler-error', type(exc).__name__ + ': ' + str(exc)) from exc
    bindings = {}
    origin_tables = {definition_id: origins}
    outer_identity = {'id': definition_id, 'revision': definition['rev'], 'source_sha256': sha256(authored.encode('utf-8')).hexdigest()}
    definitions = {definition_id: outer_identity}
    declared_rows = []
    warnings = ['Logical scene inspection; no measured pixels, visibility, focus or local draft state.',
                'Dependency fence is conservative for activation; it is not the scoped action admission contract.',
                'Actions retain compiler command templates; this adapter grants no execution capability.']
    def bind(node, depth=0, chain=None):
        chain = chain or [outer_identity]
        if depth > 64 or len(bindings) >= 1500:
            raise FrameRefusal('frame-budget', 'Frame exceeds 1500 nodes or depth 64')
        key = node['key']
        if key in bindings:
            raise FrameRefusal('duplicate-key', 'Compiled scene key is not unique: ' + key)
        item = node.get('item')
        appearance = snapshot.world.nodes.get(item)
        subject_id = appearance.get('subject') if appearance else item if item in snapshot.world.subjects else None
        subject = snapshot.world.subjects.get(subject_id)
        parent = snapshot.world.nodes.get(appearance.get('parent')) if appearance else None
        def ref(record):
            return {'id': record['id'], 'revision': record['rev']} if record else None
        bindings[key] = {
            'appearance': ref(appearance) if appearance and appearance.get('type') == 'appearance' else None,
            'subject': ref(subject),
            'parent': {**ref(parent), 'layout': parent.get('layout')} if parent else None,
            'material_item': item,
            'definition_chain': deepcopy(chain),
            'provenance': {'definition': chain[-1]['id'], 'part': node['part'], 'source_lines': sorted(set(origin_tables[chain[-1]['id']].get(node['part'], []))),
                           'precision': 'part-name-candidates; compiler does not emit exact source origin'},
            'identity': {'key': key, 'scope': 'definition-and-frame',
                         'continuity': 'appearance-bound' if appearance and appearance.get('type') == 'appearance' else 'definition-or-row; positional keys may rebind'},
        }
        if node.get('of'):
            declared_rows.append({'node': key, 'declared_source': node['of'], 'shown': node.get('n'), 'omitted': node.get('cut', 0)})
            if node['of'] == 'events':
                warnings.append('events source currently supplies the last 20 events; repeat count is not the full journal count.')
            elif '$' in node['of']:
                warnings.append('A dynamic row/selection source is covered by the conservative snapshot, not an exact compiler read trace.')
        for child in node['kids']:
            inner_chain = chain
            if node.get('lens') and child['key'] == node['key'] + '/lens:' + node['lens']:
                inner = compiler.find_lens(snapshot, node['lens'])
                identity = {'id': inner['id'], 'revision': inner['rev'], 'source_sha256': sha256(inner['text'].encode('utf-8')).hexdigest()}
                definitions[inner['id']] = identity
                if inner['id'] not in origin_tables:
                    _, inner_parts = compiler.parse(inner['text'])
                    table = {}
                    def locate(part):
                        table.setdefault(part['name'], []).append(part['line'])
                        for kid in part['kids']:
                            locate(kid)
                    for part in inner_parts.values():
                        locate(part)
                    origin_tables[inner['id']] = table
                inner_chain = chain + [identity]
            bind(child, depth + 1, inner_chain)
    bind(tree)
    after = dependency_signature(desk)
    if before != after:
        raise FrameRefusal('world-changed', 'World changed during compile; capture again under the owner lock')
    if hashes != _source_hashes():
        raise FrameRefusal('compiler-changed', 'Compiler or style changed during compile')
    frame = {'version': 1, 'actor': actor,
             'definition': {'id': definition_id, 'revision': definition['rev'],
                            'observed_source_sha256': sha256(definition['text'].encode('utf-8')).hexdigest(),
                            'source_sha256': sha256(authored.encode('utf-8')).hexdigest()},
             'compiler': hashes, 'definitions': list(definitions.values()), 'scene': tree, 'bindings': bindings, 'dependencies': before,
             'inspection': {'text': printed, 'coverage': 'logical scene from actual compiler printer; omissions follow that printer',
                            'node_count': len(bindings), 'row_sources': declared_rows, 'limitations': list(dict.fromkeys(warnings))}}
    frame['frame_id'] = _digest(frame)
    return frame


def check_frame(desk, frame):
    """Check a retained candidate under the caller's lock; never refresh it."""
    diagnostics = []
    def bad(code, message):
        diagnostics.append({'code': code, 'message': message})
    try:
        expected_id = frame.get('frame_id')
        content = {k: v for k, v in frame.items() if k != 'frame_id'}
        if expected_id != _digest(content):
            bad('frame-integrity', 'Retained frame changed after compilation')
        if frame.get('version') != 1:
            bad('frame-version', 'Unsupported frame contract version')
        anchor = frame['definition']
        current = desk.world.subjects.get(anchor['id'])
        if not current or current['rev'] != anchor['revision'] or sha256(current['text'].encode('utf-8')).hexdigest() != anchor['observed_source_sha256']:
            bad('definition-changed', 'Anchor definition changed since compilation')
        if _source_hashes() != frame['compiler']:
            bad('compiler-changed', 'Compiler or style changed since compilation')
        if dependency_signature(desk) != frame['dependencies']:
            bad('dependencies-changed', 'Conservative world snapshot changed since compilation')
    except (FrameRefusal, KeyError, TypeError, AttributeError) as exc:
        bad(getattr(exc, 'code', 'frame-invalid'), str(exc))
    return {'ok': not diagnostics, 'reasons': [d['message'] for d in diagnostics], 'diagnostics': diagnostics}
