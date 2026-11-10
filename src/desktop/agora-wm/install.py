"""Print a genesis fragment or ordinary install words. Never contacts a kernel.
Coordinator merges the fragment, or executes the printed words after review.
"""
import argparse
import json
from pathlib import Path
from manager import DEFAULTS

HERE=Path(__file__).resolve().parent
PYTHON=HERE.parents[2]/'.venv'/'Scripts'/'python.exe'
GRANTS='wm.* rows make set hear:make hear:set hear:undo hear:forget hear:theme.changed'


def spec(headless=False,allow_live=False):
    argv=[str(PYTHON),str(HERE/'wm_module.py')]
    if headless:argv.append('--headless')
    if allow_live:argv.append('--allow-live')
    return {'name':'wm','run':argv,'publishes':'wm.*','grants':GRANTS,'only':'kind:wm-settings','for':'steward'}


def fragment(headless=False,allow_live=False):
    sizes=json.loads((HERE/'size-policies.json').read_text(encoding='utf-8'))
    return {'modules':[spec(headless,allow_live)],'things':[{'kind':'wm-settings','name':'wm-settings',**DEFAULTS,
        'sizes':json.dumps(sizes)}]}


def lines(allow_live=False):
    module=spec(allow_live=allow_live)
    return ['make kind=wm-settings name=wm-settings when_full=minimise-oldest manage=all drag=ghost reflow=gentle mode=shadow never="[]"'
        ' dwell_ms=350 snap_px=16 deadzone_px=10 motion_ms=250 pin_min=0.5 edges=shared sizes='+
        json.dumps(json.dumps(json.loads((HERE/'size-policies.json').read_text(encoding='utf-8')))),
        'module wm run='+json.dumps(json.dumps(module['run']))+' grants='+json.dumps(GRANTS)]


def sizes_line(settings_id):
    """Print the prepared world fact; caller needs the settings owner's authority."""
    sizes=json.loads((HERE/'size-policies.json').read_text(encoding='utf-8'))
    return 'set '+settings_id+' sizes='+json.dumps(json.dumps(sizes))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--lines',action='store_true');p.add_argument('--headless',action='store_true');p.add_argument('--allow-live',action='store_true')
    p.add_argument('--sizes-line',metavar='SETTINGS_ID');a=p.parse_args()
    print(sizes_line(a.sizes_line) if a.sizes_line else
          '\n'.join(lines(a.allow_live)) if a.lines else json.dumps(fragment(a.headless,a.allow_live),indent=2))
