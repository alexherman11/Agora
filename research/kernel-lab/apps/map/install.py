"""Install the map: its words (the map module), five kinds, the map thing, four starter layers, ten component cards,
the map lens and its window, three place pages (lens + window widget each), and a taskbar button. Every step is an
ordinary line through the door. The ground is live (tiles.py): nothing to upload.

Importing install(door) is scratch-safe. `--live` installs into Alex's desktop world (door 8810) and opens nothing.
Undo: `off map` stops the words; `forget` the map, layers, lenses, widgets and button (or `undo` each act).
"""
import hashlib
import json
import re
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
LENS = 'seabright-map'
MAP = 'Seabright'
MODULE_GRANTS = 'rows look make set personal-view board.*'
MAP_WORDS = ('map.tile map.find map.where map.near map.place map.add map.adopt map.path map.route map.layers map.hide '
             'map.unhide map.style map.show map.cache')
GRANTS = ('window.surface window.open rows look look-view history components help component-health component-action '
          'file-read ' + MAP_WORDS + ' make set forget undo post like personal-view personal-style hear:make hear:set '
          'hear:forget hear:undo hear:post hear:like hear:component hear:component-action hear:map.route hear:map.hide '
          'hear:map.unhide hear:map.show hear:map.style hear:map.add hear:map.adopt')
VIEW = {'tool': 'look', 'stops': '[]', 'selected': '', 'mode': 'walk', 'focus': '', 'fly': ''}   # plain values only

KINDS = {
    'spot': dict(fields='lat lon text tags osm map', compose_label='Add a spot',
                 compose_description='A place on the map people can find: a tide pool, a gate, a good bench.',
                 field_labels=json.dumps({'lat': 'Latitude', 'lon': 'Longitude', 'osm': 'OpenStreetMap feature'})),
    'map': dict(fields='lens centre style search', compose_label='Make a map'),
    'map-layer': dict(fields='map shows look color icon label order on about only', compose_label='Make a map layer',
                      compose_description='A reading shown on a map: rows spot, rows event, board.feed …'),
    'route': dict(fields='map stops mode path metres minutes streets stop_points', compose_label='Plan a route'),
    'structure': dict(fields='ref lat lon class subtype osm number street height page text', compose_label='Adopt a building',
                      compose_description='A building that matters to someone: a town hall, a house, a shop. It has a '
                                          'page where things happen: events at it, posts about it.'),
}
LAYERS = [('Places', 'rows structure', 'place', '#8a6a3c', 1), ('Spots', 'rows spot', 'pin', '#2f7f8f', 2),
          ('Events', 'rows event', 'pin', '#cf5a3c', 3), ('Routes', 'rows route', 'path', '#6c5bb3', 4)]

T = lambda type_='text', default='': dict(type=type_, default=default)
COMPONENTS = {
    'map-shell': ('A map window: the map full-bleed, a column for search and what you pressed, one for layers.',
                  'shell', 'map side', '', dict(title=T(default='Map'), labels=T(default='{}'))),
    'geo-map': ('A flat 3D map of the live ground (OpenStreetMap, Overture buildings), anywhere on Earth, with the '
                'placed things of every layer as pins and routes. Drag to move, scroll to zoom, right-drag to turn; '
                'Add puts a spot, an event, a note or any kind at a building or a point; Route plans a walk.',
                'surface pin', '', 'put move resume',
                dict(map=T(), hide=T(), focus=T(), style=T(), labels=T(default='{}'))),
    'map-layers': ('Layers of a map: show or hide each for yourself, + Add a layer from a gallery of readings (shared or '
                   'only yours), the ground\'s own layers, and how the map looks.',
                   'layers', '', 'hide unhide make make-mine edit-layer forget-layer style', dict(map=T(), labels=T(default='{}'))),
    'map-search': ('Search for things, places, streets, corners and towns (map.find); choosing one flies there.',
                   'search', '', '', dict(map=T(), labels=T(default='{}'))),
    'map-inspector': ('What was pressed: a building\'s card (what is at it, the talk, its page), every fact of a thing, '
                      'or what is new on the map.',
                      'inspector', '', 'put adopt open-page say edit forget replan', dict(map=T(), labels=T(default='{}'))),
    'map-route': ('A route planner: stops in order, on foot or by bike, the street path\'s length and time, and save.',
                  'route', '', 'route', dict(map=T(), labels=T(default='{}'))),
    'place-page': ('A page for one place: a window opened on a structure ($view.target); its parts follow.',
                   'page', '', '', dict(accent=T(), labels=T(default='{}'))),
    'place-head': ('The place\'s name, what it is, a small 3D view of it, Show on the map and Rename.',
                   'head', '', 'show edit', dict(badge=T(), show=T(), labels=T(default='{}'))),
    'place-list': ('Things at the place, of one kind (and type): events soonest first, others newest; a form adds one.',
                   'section', '', 'add', dict(title=T(), kind=T(), type=T(), fields=T(default='title start'), add=T(),
                                                  empty=T(), past=T(), labels=T(default='{}'))),
    'place-talk': ('Posts about the place, with likes, and a box to say something.',
                   'talk', '', 'say like', dict(title=T(), prompt=T(), empty=T(), labels=T(default='{}'))),
}
# Pages a place can open in. A page widget's places= says which buildings use it (their class or kind); any lens
# with a widget that says places= joins in, so a community adds a page for its library without touching this file.
PAGES = [('place-page', 'Place', ''),
         ('town-hall-page', 'Town hall', 'townhall town_hall government public'),
         ('home-page', 'Home', 'house detached residential apartments semidetached_house terrace bungalow home')]
PAGE_GRANTS = ('window.surface rows look look-view history components help component-health component-action '
               'map.place map.tile map.show map.where make set forget undo post like hear:make hear:set hear:forget '
               'hear:undo hear:post hear:like hear:map.add hear:map.adopt hear:component hear:component-action')


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


def widget(door, name, title, grants, **facts):
    """A window widget for a component lens: the painter, quiet receipts, and its grants (said again when they change)."""
    wid = upsert(door, 'widget', name, title=title, style='bars', receipts='quiet', component_lens=name,
                 code=widget_source(board_look=False), **facts)
    current = door.rows('widget', name=name)[0]
    if not current.get('on') or not any(g.get('words') == grants and not g.get('revoked') for g in door.rows('grant', to=wid)):
        door.say('look ' + wid)
        door.say('widget ' + wid + ' surface=window grants=' + Q(grants))
    return wid


def install(door, map_name=MAP, centre='36.9672,-122.0088'):
    ids = {}
    if not door.rows('module', name='map'):
        door.say('module map run=' + Q(json.dumps([sys.executable, str(MODULE)])) + ' publishes="map.*" grants=' + Q(MODULE_GRANTS))
    elif 'map.place' not in door.request('/see', {'line': 'help all'}).get('text', ''):
        # an older map process is running: off and undo start it again on the new code (its grants come back too)
        out = door.say('off map')
        rec = re.search(r'\[r(\d+)\]', out.get('text', '') + json.dumps(out.get('records', '')))
        door.say('undo r' + rec.group(1) if rec else 'undo')
    wait_for(door, 'map.place')
    for kind, facts in KINDS.items():
        ids['kind:' + kind] = upsert(door, 'kind', kind, **facts)
    ids['map'] = upsert(door, 'map', map_name, lens=LENS, centre=centre, search='nominatim')
    m = door.rows('map', name=map_name)[0]
    if m.get('ground'):
        door.say(f'set {ids["map"]} ground=')       # the live ground replaces the first ground file (it stays a file)
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
    ids['widget'] = widget(door, LENS, map_name + ' map', GRANTS)
    for name, title, places in PAGES:
        text = (HERE / 'pages' / (name + '.lens')).read_text(encoding='utf-8')
        ids['lens:' + name] = upsert(door, 'lens', name, title=title, painter='components', text=text,
                                     view=json.dumps({'target': ''}), reconcile_ms='15000')
        ids['widget:' + name] = widget(door, name, title, PAGE_GRANTS, places=places)
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
    door = taskboard.live_door()
    # A window open while its component code is swapped repaints with code not yet reviewed (it runs isolated, without
    # its draft), and two failures quarantine the part (27 Oct). So the map's own windows close first and reopen after.
    ours = {LENS} | {name for name, _, _ in PAGES}
    open_now = [r for r in door.request('/see', {'line': 'rows window'}).get('rows', []) if r.get('shows') in ours]
    for r in open_now:
        door.say('window.close ' + r['id'])
    print(json.dumps(install(door), indent=1))
    for r in open_now:
        door.say('window.open ' + r['shows'] + (' ' + r['target'] if r.get('target') else ''))


if __name__ == '__main__':
    main()
