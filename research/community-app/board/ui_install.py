"""Reviewed board lens/components. Scratch by default; --live never opens a window."""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1] / 'kernel-lab'
DESKTOP = LAB.parent / 'window-lab/kernel-desktop'
sys.path[:0] = [str(HERE), str(LAB), str(DESKTOP)]
from painter.install import upsert, widget_source, taskboard, Q
from painter.catalogue import cards, T
from install import install as install_world, modules
from protocol import line

NAMES = {
    'board-shell': ('A calm responsive frame with channels, feed and a conversation slot.', 'heading body', 'navigation feed thread composer', ''),
    'board-navigation': ('Channels from world things; saved conversations and leaders’ queue.', 'body', '', ''),
    'board-toolbar': ('Search, world orderings and compose.', 'body search', '', ''),
    'board-catchup': ('Plain catch-up data with explicit mark seen and optional labelled local summary.', 'body', 'entries', 'seen snapshot summarize'),
    'board-entry': ('Open one reading result or catch-up entry.', 'body', '', ''),
    'board-feed': ('A paged reading-backed collection, with a welcoming empty state.', 'body', 'posts', ''),
    'board-post': ('Post identity, states, a kind\'s accent token, and authored action lines around content slots.', 'body identity badge title outcome quote', 'content fields poll slots files', 'like personal unpersonal rsvp answer'),
    'board-thread': ('Two reply levels and an exact-passage reply form.', 'body reply status', 'posts replies', 'reply'),
    'board-notice': ('Visible leader-hide reason and receipt-specific undo.', 'body', '', 'undo'),
    'board-search': ('Filtered search results or a leaders-only queue reading.', 'body', 'results', ''),
    'board-composer': ('Kind-declared fields, private upload and attach after admission.', 'body upload status', '', 'post attach hide report decide edit pin'),
}
TOKENS = {
    'paper':'#faf9f5', 'card':'#ffffff', 'ink':'#303d37', 'muted':'#68756e', 'accent':'#3e7264',
    'nb-border':'#e3e6de','nb-soft':'#edf3ed','nb-soft-border':'#cbdcd0',
    'nb-body':'17px','nb-small':'14px','nb-tiny':'12px','nb-h1':'30px','nb-h2':'21px','nb-tight':'0px','nb-letterspace':'1px',
    'nb-leading':'1.6','nb-prose-leading':'1.65','nb-page-leading':'1.8','nb-h-leading':'1.4','nb-title-leading':'1.25','nb-weight':'600','nb-heading-weight':'650','nb-reading-font':'Georgia, serif',
    'nb-space-1':'4px','nb-space-2':'8px','nb-space-3':'12px','nb-space-4':'16px','nb-space-5':'22px','nb-space-6':'28px',
    'nb-line':'1px','nb-focus':'2px','nb-edge':'3px','nb-radius':'14px','nb-radius-small':'8px','nb-pill':'24px',
    'nb-touch':'44px','nb-short-touch':'36px','nb-logo-size':'48px','nb-avatar':'36px',
    'nb-max':'1500px','nb-nav-width':'190px','nb-thread-width':'340px','nb-menu-width':'210px','nb-panel-height':'80vh',
    'nb-photo-height':'240px','nb-phone-photo-height':'200px','nb-page-height':'180px',
    'nb-compose-width':'600px','nb-dialog-width':'94vw','nb-dialog-height':'92vh','nb-phone-dialog-width':'94vw','nb-bottom-room':'90px',
    'motion-pulse':json.dumps(dict(**{'from':dict(opacity=.6),'to':dict(opacity=1)},duration=180)),
}
VIEW = dict(channel='',order='',offset=0,thread='',replyTo='',compose='no',search='',queue='no',
            kind='',person='',since='',before='',quote='',source='',page=1,hide='',report='',decide='',edit='',pin='')
GRANTS = ('window.surface rows look look-view history components help component-health component-action '
          'board.* forgotten file-read upload files.convert attach like vote claim pin forget make set undo model.ask '
          'hear:make hear:set hear:forget hear:undo hear:component hear:component-action hear:board.* hear:like hear:vote hear:claim')


def install_ui(door):
    defaults={'discussion':'','question':'','announcement':'until','event':'','poll':'','ask':'closes','offer':'closes','document':'','decision':''}
    for kind in door.rows('kind'):
        if kind.get('name') in defaults and 'card_fields' not in kind:
            # Empty facts are removed by set, so a sentinel explicitly displays
            # no generic fields while specialised slots show dates/counts.
            door.say('look '+kind['id']);door.say('set '+kind['id']+' card_fields='+Q(defaults[kind['name']] or '-'))
        if kind.get('name') in defaults and 'field_types' not in kind:
            fields=kind.get('fields','').split()
            types={key:('datetime' if key in ('start','end','closes','until') else 'number' if key=='seats' else 'text') for key in fields}
            words={'start':'Starts','end':'Ends','closes':'Closes','until':'Until','seats':'Places available','location':'Meeting place','place':'Place reference','options':'Choices (one word each)'}
            labels={key:words.get(key,key.replace('_',' ').capitalize()) for key in fields}
            door.say('look '+kind['id']);door.say('set '+kind['id']+' field_types='+Q(json.dumps(types))+' field_labels='+Q(json.dumps(labels)))
    code=(HERE/'board-components.js').read_text(encoding='utf-8')
    code=code.replace('export default {mount', 'export default {css:'+json.dumps((HERE/'board-theme.css').read_text(encoding='utf-8'))+',mount')
    import hashlib
    for card in cards():
        name=card.pop('name')
        path=LAB/'components'/f'{name}.js'
        source=(path if path.exists() else LAB/'components/catalogue.js').read_text(encoding='utf-8')
        tid=upsert(door,'component',name,**card,code=source)
        if door.rows('component',name=name)[0].get('reviewed_code')!=hashlib.sha256(source.encode()).hexdigest():
            door.say('look '+tid);door.say('component '+tid)
    for name,(purpose,parts,slots,gestures) in NAMES.items():
        schema=dict(labels=T(default='{}'))
        if name=='board-shell':schema.update(title=T(default='Seabright'),subtitle=T(default='The neighbourhood board'))
        if name=='board-post':schema.update(layout=T(default='roomy'),detail=T('boolean',False))
        tid=upsert(door,'component',name,category='community',purpose=purpose,settings=json.dumps(schema),
                   parts=json.dumps({p:dict(facts='bound visible row') for p in parts.split()}),slots=json.dumps(slots.split()),
                   gestures=gestures,example=f'root : {name}',uses='Community board; feed; neighbourhood',
                   limitations='Presentation and guarded world-word gestures. No calendar page, map or notification routing.',code=code)
        if door.rows('component',name=name)[0].get('reviewed_code')!=hashlib.sha256(code.encode()).hexdigest():
            door.say('look '+tid);door.say('component '+tid)
    lens=upsert(door,'lens','seabright-board',title='Seabright board',painter='components',
                text=(HERE/'board.lens').read_text(encoding='utf-8'),view=json.dumps(VIEW))
    upsert(door,'part-style','seabright-theme',lens='seabright-board',target='tokens',**TOKENS)
    widget=upsert(door,'widget','seabright-board',title='Seabright board',style='bars',receipts='quiet',component_lens='seabright-board',code=widget_source())
    current=door.rows('widget',name='seabright-board')[0]
    if not current.get('on') or not any(g.get('words')==GRANTS and not g.get('revoked') for g in door.rows('grant',to=widget)):
        door.say('look '+widget);door.say('widget '+widget+' surface=window grants='+Q(GRANTS))
    button=upsert(door,'button','seabright-board-button',label='Seabright board',bar='taskbar',icon='messages-square',does='window.open seabright-board')
    upsert(door,'guide','seabright-ui-handles',title='Seabright board interface handles',text=(HERE/'UI-HANDLES.md').read_text(encoding='utf-8'))
    return dict(lens=lens,widget=widget,button=button)


def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--live',action='store_true');args=ap.parse_args()
    if not args.live:ap.error('import install_ui(door) for scratch; --live explicitly installs without opening')
    from gaming_gate import assert_clear
    assert_clear();door=taskboard.live_door()
    for spec in modules():
        existing=door.rows('module',name=spec['name'])
        if not existing:door.say(line('module '+spec['name'],run=json.dumps(spec['run']),publishes=spec['publishes'],grants=spec['grants']))
    if not door.rows('board-settings'):install_world(door.say,lambda command:door.request('/see',dict(line=command)))
    assert_clear();ids=install_ui(door)
    print('LIVE BOARD '+json.dumps(dict(**ids,opened=False,posts_seeded=0)),flush=True)


if __name__=='__main__':main()
