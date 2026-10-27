"""Install the map: its words (the map module), four kinds, a ground file, the map thing, three starter layers, six
component cards, the lens and its window, and a taskbar button. Every step is an ordinary line through the door.

Importing install(door) is scratch-safe. `--live` installs into Alex's desktop world (door 8810) and opens nothing.
Undo: `off map` stops the words; `forget` the map, layers, lens, widget and button (or `undo` each act).
"""
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
ROOT = LAB.parents[1]
sys.path[:0] = [str(LAB)]
from painter.install import upsert, widget_source, taskboard, Q  # noqa: E402

MODULE = LAB / 'modules' / 'map' / 'map.py'
GROUND = ROOT / 'research' / 'map-lab' / 'seabright' / 'seabright-ground.json'
LENS = 'seabright-map'
MAP = 'Seabright'
MODULE_GRANTS = 'rows look make set personal-view board.*'
GRANTS = ('window.surface rows look look-view history components help component-health component-action file-read '
          'map.find map.where map.near map.path map.route map.layers map.hide map.unhide map.show make set forget undo '
          'personal-view personal-style hear:make hear:set hear:forget hear:undo hear:component hear:component-action '
          'hear:map.route hear:map.hide hear:map.unhide hear:map.show')
VIEW = {'tool': 'look', 'stops': '[]', 'selected': '', 'mode': 'walk', 'focus': '', 'fly': ''}   # plain values only

KINDS = {
    'spot': dict(fields='lat lon text tags osm map', compose_label='Add a spot',
                 compose_description='A place on the map people can find: a tide pool, a gate, a good bench.',
                 field_labels=json.dumps({'lat': 'Latitude', 'lon': 'Longitude', 'osm': 'OpenStreetMap feature'})),
    'map': dict(fields='ground lens centre', compose_label='Make a map'),
    'map-layer': dict(fields='map shows look color icon label order on', compose_label='Make a map layer',
                      compose_description='A reading shown on a map: rows spot, rows event, board.feed …'),
    'route': dict(fields='map stops mode path metres minutes streets stop_points', compose_label='Plan a route'),
}
LAYERS = [('Spots', 'rows spot', 'pin', '#2f7f8f', 1), ('Events', 'rows event', 'pin', '#cf5a3c', 2),
          ('Routes', 'rows route', 'path', '#6c5bb3', 3)]

T = lambda type_='text', default='': dict(type=type_, default=default)
COMPONENTS = {
    'map-shell': ('A map window: the map full-bleed and every other part floating beside it (a sheet on a phone).',
                  'shell', 'map side', '', dict(title=T(default='Map'), labels=T(default='{}'))),
    'geo-map': ('A 3D map surface of a ground file, with the placed things of every layer as pins and routes. '
                'Drag to move, scroll to zoom, right-drag to turn; tools to add spots and plan routes.',
                'surface pin', '', 'add add-event move',
                dict(map=T(), hide=T(), focus=T(), curve=T('number', 2400), labels=T(default='{}'))),
    'map-layers': ('Layers of a map: show or hide each for yourself, the ground\'s own layers, and a new-layer form.',
                   'layers', '', 'hide unhide make edit-layer forget-layer', dict(map=T(), labels=T(default='{}'))),
    'map-search': ('Search a map for streets, corners, places and spots (map.find); choosing one flies there.',
                   'search', '', '', dict(map=T(), labels=T(default='{}'))),
    'map-inspector': ('What was pressed on the map: every fact of a thing, where it is, what is near, and its actions.',
                      'inspector', '', 'edit forget add replan', dict(map=T(), labels=T(default='{}'))),
    'map-route': ('A route planner: stops in order, on foot or by bike, the street path\'s length and time, and save.',
                  'route', '', 'route', dict(map=T(), labels=T(default='{}'))),
}


def code():
    return '\n'.join((HERE / f).read_text(encoding='utf-8') for f in ('geo-worker.js', 'geo-engine.js', 'map-components.js'))


def wait_for(door, word, seconds=20):
    end = time.time() + seconds
    while time.time() < end:
        if word in door.request('/see', {'line': 'help all'}).get('text', ''):
            return True
        time.sleep(0.3)
    raise RuntimeError(f'{word} did not appear in help all')


def upload(door, path, name):
    data = Path(path).read_bytes()
    req = urllib.request.Request(door.url + '/upload', data, {'Authorization': 'Bearer ' + door.token,
                                                             'X-Filename': name, 'Content-Type': 'application/octet-stream'})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    if not out.get('ok', True) or not out.get('made'):
        raise RuntimeError(out)
    return out['made'][0]


def install(door, ground=GROUND, map_name=MAP, centre='36.9672,-122.0088'):
    ids = {}
    if not door.rows('module', name='map'):
        door.say('module map run=' + Q(json.dumps([sys.executable, str(MODULE)])) + ' publishes="map.*" grants=' + Q(MODULE_GRANTS))
    wait_for(door, 'map.layers')
    for kind, facts in KINDS.items():
        ids['kind:' + kind] = upsert(door, 'kind', kind, **facts)
    digest = hashlib.sha256(Path(ground).read_bytes()).hexdigest()
    files = [f for f in door.rows('file') if f.get('blob_hash') == digest]
    ids['ground'] = files[0]['id'] if files else upload(door, ground, Path(ground).name)
    ids['map'] = upsert(door, 'map', map_name, ground=ids['ground'], lens=LENS, centre=centre)
    for name, shows, look, color, order in LAYERS:
        if not [r for r in door.rows('map-layer', name=name) if r.get('map') in (ids['map'], map_name)]:
            ids['layer:' + name] = door.say(f'make kind=map-layer map={ids["map"]} name={Q(name)} shows={Q(shows)} '
                                            f'look={look} color={color} order={order}')['made'][0]
    source = code()
    for name, (purpose, parts, slots, gestures, schema) in COMPONENTS.items():
        tid = upsert(door, 'component', name, category='places', purpose=purpose, settings=json.dumps(schema),
                     parts=json.dumps({p: dict(facts='bound visible row') for p in parts.split()}),
                     slots=json.dumps(slots.split()), gestures=gestures, example=f'root : {name}, map {map_name}',
                     uses='Community maps; places, events and routes', code=source,
                     limitations='Needs WebGL for the 3D surface; one ground file per map; routes walk the ground\'s '
                                 'streets only (no traffic, no transit).')
        if door.rows('component', name=name)[0].get('reviewed_code') != hashlib.sha256(source.encode()).hexdigest():
            door.say('look ' + tid)
            door.say('component ' + tid)
        ids[name] = tid
    lens_text = (HERE / 'map.lens').read_text(encoding='utf-8').replace('Seabright', map_name)
    ids['lens'] = upsert(door, 'lens', LENS, title=map_name + ' map', painter='components', text=lens_text,
                         view=json.dumps(VIEW), reconcile_ms='15000')
    ids['widget'] = upsert(door, 'widget', LENS, title=map_name + ' map', style='bars', receipts='quiet',
                           component_lens=LENS, code=widget_source(board_look=False))
    current = door.rows('widget', name=LENS)[0]
    if not current.get('on') or not any(g.get('words') == GRANTS and not g.get('revoked') for g in door.rows('grant', to=ids['widget'])):
        door.say('look ' + ids['widget'])
        door.say('widget ' + ids['widget'] + ' surface=window grants=' + Q(GRANTS))
    ids['button'] = upsert(door, 'button', LENS + '-button', label=map_name + ' map', bar='taskbar', icon='map',
                           does='window.open ' + LENS)
    return ids


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--live', action='store_true')
    args = ap.parse_args()
    if not args.live:
        ap.error('import install(door) for a scratch world; --live installs into the desktop world without opening it')
    sys.path.insert(0, str(ROOT / 'research/window-lab/kernel-desktop'))
    from gaming_gate import assert_clear
    assert_clear()
    print(json.dumps(install(taskboard.live_door()), indent=1))


if __name__ == '__main__':
    main()
