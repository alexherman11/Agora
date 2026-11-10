"""Install only the original pixel guy's studio. Never activates the rejected demos.
Claude reviews source and handles the shared desktop reload before live use.
"""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
DESKTOP = HERE.parents[1] / 'desktop/kernel-desktop'
sys.path.insert(0, str(DESKTOP))
import guy_looks
from kd_guy import art
from install import taskboard, quote as Q

NAME = 'pixel-guy-editor'
BASE_GRANTS = 'window.surface rows look hear:set hear:undo guy.say'


def code(subject):
    data = dict(subject=subject, defaults=guy_looks.DEFAULTS, head=art.HEAD, body=art.BODY,
                hats=guy_looks.HATS, accessories=guy_looks.ACCESSORIES,
                palette={k:'#'+bytes(v).hex() for k,v in art.PAL.items()})
    return ((HERE/'common.js').read_text(encoding='utf-8') + '\nconst GUY_ART = ' +
            json.dumps(data) + ';\n' + (HERE/'pixel-guy-editor.js').read_text(encoding='utf-8'))


def install(door):
    provider = door.rows('module', name='guy')[0]['id']
    guys = door.rows('pixel-guy', provider=provider)
    if not guys:
        out = door.say('make kind=pixel-guy provider='+provider+' '+
                       ' '.join(k+'='+Q(v) for k,v in guy_looks.DEFAULTS.items() if v != ''))
        subject = out['made'][0]
    else:
        subject = guys[0]['id']
    source = code(subject)
    widgets = door.rows('widget', name=NAME)
    if widgets:
        mid = widgets[0]['id']
        if widgets[0].get('code') != source:
            door.say('look '+mid);door.say('set '+mid+' code='+Q(source))
    else:
        mid = door.say('make kind=widget name='+NAME+' title="Pixel guy studio" code='+Q(source))['made'][0]
    scope = 'thing:'+subject+';fields:'+','.join(guy_looks.FIELDS)
    grants = [g for g in door.rows('grant', to=mid) if not g.get('revoked')]
    if not (any(g.get('words')==BASE_GRANTS for g in grants) and
            any(g.get('words')=='set undo' and g.get('only')==scope for g in grants)):
        door.say('look '+mid)
        door.say('widget '+mid+' surface=window grants='+Q(BASE_GRANTS))
        door.say('grant '+mid+' words="set undo" only='+Q(scope))
    open_line='window.open '+NAME+' at=70,120 size=640,1040'
    if not door.rows('word',word='guy-studio'):
        door.say('verb guy-studio steps='+Q(open_line)+' help="Open the original pixel guy studio."')
    # A world-owned dock button; no taskbar source edits.
    if not door.rows('button', studio=NAME):
        door.say('make kind=button name="Pixel guy studio" bar=taskbar icon=palette studio='+NAME+
                 ' does=guy-studio')
    return dict(widget=mid, guy=subject, provider=provider)


def main():
    import argparse
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--open', action='store_true')
    ap.add_argument('--hello', action='store_true')
    args=ap.parse_args()
    from gaming_gate import assert_clear
    assert_clear()
    door=taskboard.live_door()
    # Old kernels refuse this unknown scope. Do not deploy a partly functional
    # editor or broaden its grants to work around a missing admission check.
    if 'fields' not in door.request('/health').get('grant_scopes', []):
        raise RuntimeError('Shared desktop needs coordinator reload for reviewed field-scoped grants; live world unchanged')
    ids=install(door)
    if args.open:
        door.say('window.open '+NAME+' at=70,120 size=640,1040')
    if args.hello:
        door.say('look '+ids['guy']);door.say('set '+ids['guy']+' hat=cap')
        door.say('guy.say "new hat!"')
    print('Pixel guy studio installed; window.open '+NAME)


if __name__=='__main__':
    main()
