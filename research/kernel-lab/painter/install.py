"""Install reviewed components and arrangements through ordinary door words.

Default is explicit --live; importing install() is scratch-safe. No native code
is installed, no rejected guy demos are activated, and no live restart is done.
"""
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
LAB=HERE.parent
DESKTOP=LAB.parents[0]/'window-lab/kernel-desktop'
spec=importlib.util.spec_from_file_location('painter_board_install',LAB/'apps/taskboard/install.py')
taskboard=importlib.util.module_from_spec(spec);spec.loader.exec_module(taskboard)
Q=taskboard.quote
sys.path.insert(0,str(LAB))
from painter.catalogue import cards


def upsert(door,kind,name,**facts):
    old=door.rows(kind,name=name)
    if not old:
        return door.say('make kind='+kind+' name='+name+''.join(' '+k+'='+Q(v) for k,v in facts.items()))['made'][0]
    t=old[0]['id'];changes={k:v for k,v in facts.items() if str(old[0].get(k,''))!=str(v)}
    if changes:
        door.say('look '+t);door.say('set '+t+''.join(' '+k+'='+Q(v) for k,v in changes.items()))
    return t


def widget_source():
    return '\n\n'.join(p.read_text(encoding='utf-8') for p in
        [LAB/'widgets/common.js',HERE/'primitives.js',HERE/'theme.js',HERE/'painter.js'])


def install(door, board=True):
    ids={}
    upsert(door,'guide','component-painter-guide',title='Component painter guide',
           text=(HERE/'ARRANGEMENT.md').read_text(encoding='utf-8'))
    for card in cards():
        name=card.pop('name')
        path=LAB/'components'/f'{name}.js'
        code=(path if path.exists() else LAB/'components/catalogue.js').read_text(encoding='utf-8')
        t=upsert(door,'component',name,**card,code=code)
        current=door.rows('component',name=name)[0]
        import hashlib
        if current.get('reviewed_code')!=hashlib.sha256(code.encode()).hexdigest():
            door.say('look '+t);door.say('component '+t)
        ids[name]=t
    if board:
        if not door.rows('taskboard-settings'): taskboard.install(door)
        upsert(door,'lens','taskboard-components',title='Task board · Components',painter='components',
               text=(LAB/'apps/taskboard/component-board.lens').read_text(encoding='utf-8'))
        ids['taskboard-components']=activate(door,'taskboard-components','Task board · Components')
    # The gallery is an arrangement made from catalogue components, including
    # live examples and literal setting cards. No separate gallery renderer.
    gallery=['root : column, role catalogue', '  heading : text "Component gallery"']
    for i,card in enumerate(cards()):
        name=card['name'];prefix=f'  item-{i}'
        gallery += [prefix+' : column, role gallery-example','  '+prefix+'-name : text '+json.dumps(name+' · '+card['purpose']),
                    '  '+prefix+'-help : code', '      setting value='+json.dumps('Settings: '+card['settings']+'\nExample: '+card['example']+'\nLimits: '+card['limitations']),
                    '  '+prefix+'-preview : scroll, role gallery-preview']
        example=card['example'].splitlines()
        gallery += ['    '+prefix+'-example :'+example[0].split(':',1)[1]]
        gallery += ['      '+line for line in example[1:]]
    upsert(door,'lens','component-gallery',title='Component gallery',painter='components',text='\n'.join(gallery))
    ids['component-gallery']=activate(door,'component-gallery','Component gallery')
    upsert(door,'button','component-gallery-button',label='Component gallery',bar='taskbar',icon='app-window',
           does='window.open component-gallery')
    return ids


def activate(door,name,title):
    mid=upsert(door,'widget',name,title=title,style='bars',component_lens=name,code=widget_source())
    grants=('window.surface rows look look-view history components help task-add task-move task-assign task-done '
            'task-note task-priority task-colour task-note-colour task-note-style task-filter task-rename task-edit task-text task-remove summarize.* make set forget undo '
            'hear:make hear:set hear:forget hear:undo hear:component')
    current=door.rows('widget',name=name)[0]
    matching=any(g.get('words')==grants and not g.get('revoked') for g in door.rows('grant',to=mid))
    if not current.get('on') or not matching:
        door.say('look '+mid);door.say('widget '+mid+' surface=window grants='+Q(grants)+' only=kind:taskboard-task,taskboard-settings')
    return mid


def main():
    import argparse
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--live',action='store_true');args=ap.parse_args()
    if not args.live: ap.error('use install(door) for a scratch world, or explicitly --live')
    sys.path.insert(0,str(DESKTOP));from gaming_gate import assert_clear
    assert_clear();door=taskboard.live_door()
    # New words must already have been adopted by the coordinator's runtime.
    if not door.request('/see',{'line':'help look-view'}).get('ok'):
        raise RuntimeError('Coordinator must adopt reviewed painter kernel words before live install; no restart attempted.')
    ids=install(door)
    assert_clear();door.say('window.open taskboard-components to=left')
    print('Installed component board and gallery; opened the component board only.')


if __name__=='__main__':main()
