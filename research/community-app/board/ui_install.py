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
from install import install as install_world, modules, CHANNEL_KEYS
from protocol import line

NAMES = {
    'board-shell': ('A calm responsive frame with channels, feed and a conversation slot.', 'heading body', 'navigation feed thread composer', ''),
    'board-navigation': ('Channels from world things; saved conversations and leaders’ queue.', 'body', '', ''),
    'board-toolbar': ('Search, world orderings and compose.', 'body search', '', ''),
    'board-catchup': ('Plain catch-up data with explicit mark seen and optional labelled local summary.', 'body', 'entries', 'seen snapshot summarize'),
    'board-entry': ('Open one reading result or catch-up entry.', 'body', '', ''),
    'board-feed': ('A paged reading-backed collection, with a welcoming empty state.', 'body', 'posts', ''),
    'board-post': ('Post identity, states, a kind\'s accent token, and authored action lines around content slots.', 'body identity badge title outcome quote kind answer', 'content fields date poll slots files', 'like personal unpersonal rsvp answer'),
    'board-thread': ('Two reply levels and an exact-passage reply form.', 'body reply status', 'posts replies', 'reply'),
    'board-notice': ('Visible leader-hide reason and receipt-specific undo.', 'body', '', 'undo'),
    'board-search': ('Filtered search results or a leaders-only queue reading.', 'body', 'results', ''),
    'board-chat': ('One chat: grouped lines, day and New dividers, replies, reactions, edit, remove, pin, mentions, older pages.', 'body composer edit', 'lines', 'send edit remove react pin unpin seen reseen'),
    'board-composer': ('Kind-declared fields, private upload and attach after admission.', 'body upload status', '', 'post attach hide report decide edit pin'),
}
TOKENS = {
    'paper':'#faf9f5', 'card':'#ffffff', 'ink':'#303d37', 'muted':'#59685f', 'accent':'#315f52',
    'nb-border':'#e3e6de','nb-soft':'#edf3ed','nb-soft-border':'#cbdcd0',
    'nb-body':'17px','nb-small':'14px','nb-tiny':'12px','nb-h1':'30px','nb-h2':'21px','nb-tight':'0px','nb-letterspace':'1px',
    'nb-leading':'1.6','nb-prose-leading':'1.65','nb-page-leading':'1.8','nb-h-leading':'1.4','nb-title-leading':'1.25','nb-weight':'600','nb-heading-weight':'650','nb-reading-font':'Georgia, serif',
    'nb-space-1':'4px','nb-space-2':'8px','nb-space-3':'12px','nb-space-4':'16px','nb-space-5':'22px','nb-space-6':'28px',
    'nb-line':'1px','nb-focus':'2px','nb-edge':'3px','nb-radius':'14px','nb-radius-small':'8px','nb-pill':'24px',
    'nb-touch':'44px','nb-short-touch':'36px','nb-logo-size':'48px','nb-avatar':'28px',
    'nb-max':'1500px','nb-nav-width':'184px','nb-thread-width':'520px','nb-menu-width':'210px','nb-panel-height':'80vh',
    'nb-photo-height':'240px','nb-phone-photo-height':'200px','nb-page-height':'180px',
    'nb-compose-width':'600px','nb-dialog-width':'94vw','nb-dialog-height':'92vh','nb-phone-dialog-width':'94vw','nb-bottom-room':'90px',
    'nb-top-height':'64px','nb-search-width':'640px','nb-count-size':'20px','nb-card-title':'19px','nb-thread-share':'45%',
    'nb-amber-soft':'#fff1d1','nb-amber-ink':'#805000','nb-announcement':'#f6f9f5','nb-date-width':'62px',
    'nb-meter-width':'110px','nb-reading-width':'640px','nb-reading-size':'18px','nb-preview-size':'56px',
    'nb-phone-compose-room':'76px','nb-phone-channel-width':'80px','nb-phone-role-width':'65px',
    'nb-kind-discussion':'#59685f','nb-kind-question':'#805000','nb-kind-event':'#315d86',
    'nb-kind-poll':'#684b87','nb-kind-ask':'#884a35','nb-kind-offer':'#315f52',
    'nb-kind-document':'#4f596c','nb-kind-announcement':'#315f52','nb-kind-decision':'#315f52',
    'nb-chat-chrome':'190px','nb-phone-chat-chrome':'128px','nb-chat-min':'420px','nb-chat-gutter':'40px',
    'nb-mention-soft':'#fff6dc','nb-mention-edge':'#d9a63a','nb-new-line':'#c8553d','nb-danger':'#a8402f',
    'motion-pulse':json.dumps(dict(**{'from':dict(opacity=.6),'to':dict(opacity=1)},duration=180)),
}
VIEW = dict(channel='',order='',offset=0,thread='',replyTo='',focus='',compose='no',search='',queue='no',opens='',calendarView='',calendarDate='',calendarAdd='no',calendarEvent='',
            kind='',person='',since='',before='',quote='',source='',page=1,documentPage=1,documentFile='',documentRequest=0,chat='',navOpen='no',hide='',report='',decide='',edit='',pin='')
# The map opens as a list entry (opens=map), so its panel starts unfolded (map-panel's own view key for root/map).
VIEW['map.root/map.open']='yes'
GRANTS = ('window.surface rows look look-view history components help component-health component-action '
          'board.* forgotten file-read upload files.convert attach like vote claim pin forget make set undo model.ask model.status '
          'chat say react '
          'hear:make hear:set hear:forget hear:undo hear:component hear:component-action hear:board.* hear:like hear:vote hear:claim '
          'hear:say hear:react hear:pin')


def install_ui(door):
    # A place is optional on every board post. Keep neighbour-defined fields and labels.
    for kind in door.rows('kind'):
        if kind.get('name') not in {'discussion','question','announcement','event','poll','ask','offer','document','decision'}:
            continue
        fields=kind.get('fields','').split()
        if 'place' not in fields:
            fields.append('place')
            extra={}
            if kind.get('field_types'):
                types=json.loads(kind['field_types']);types.setdefault('place','text')
                extra['field_types']=json.dumps(types)
            if kind.get('field_labels'):
                labels=json.loads(kind['field_labels']);labels.setdefault('place','Link to a place')
                extra['field_labels']=json.dumps(labels)
            door.say('look '+kind['id'])
            door.say(line('set',kind['id'],fields=' '.join(fields),**extra))
    compose={
        'discussion':('Share something','News, an idea, or a conversation.','☰'),
        'question':('Ask a question','Find an answer from your neighbors.','?'),
        'event':('Plan an event','Choose a time and place to meet.','▦'),
        'poll':('Run a poll','Give everyone a choice.','▥'),
        'ask':('Ask for help','Find a few hands for something useful.','↗'),
        'offer':('Offer help','Share your time or something useful.','♡'),
        'document':('Share a document','Keep useful information together.','▤'),
        'announcement':('Make an announcement','Share important news with everyone.','⌖'),
        'decision':('Share a decision','Let neighbors know what was agreed.','✓')}
    defaults={'discussion':'','question':'','announcement':'until','event':'','poll':'','ask':'closes','offer':'closes','document':'','decision':''}
    for kind in door.rows('kind'):
        # Neighbour-authored post kinds (e.g. Lost pet) declare fields too.
        # Other apps must declare their own compose_scope before this migration.
        if (kind.get('name') in compose or 'fields' in kind) and not kind.get('compose_scope'):
            door.say('look '+kind['id']);door.say(line('set',kind['id'],compose_scope='board'))
        if kind.get('name')=='event' and 'seats' in kind.get('required','').split():
            door.say('look '+kind['id']);door.say(line('set',kind['id'],required=' '.join(k for k in kind['required'].split() if k!='seats')))
        if kind.get('name') in compose and not kind.get('accent'):
            door.say('look '+kind['id']);door.say(line('set',kind['id'],accent='nb-kind-'+kind['name']))
        if kind.get('field_labels'):
            labels=json.loads(kind['field_labels']);changed=False
            for key,old,new in [('closes','Closes','Sign-ups close'),('place','Place reference','Link to a place'),('until','Until','Show until')]:
                if labels.get(key)==old:labels[key]=new;changed=True
            if changed:
                door.say('look '+kind['id']);door.say(line('set',kind['id'],field_labels=json.dumps(labels)))
        if not kind.get('compose_label') and (kind.get('compose_scope')=='board' or kind.get('name') in compose or ('fields' in kind and not kind.get('compose_scope'))):
            label,description,icon=compose.get(kind.get('name'),(kind.get('name','Post'),'Share this with your neighbors.','✦'))
            door.say('look '+kind['id']);door.say(line('set',kind['id'],compose_label=label,compose_description=description,compose_icon=icon))
        if kind.get('name') in defaults and 'card_fields' not in kind:
            # Empty facts are removed by set, so a sentinel explicitly displays
            # no generic fields while specialised slots show dates/counts.
            door.say('look '+kind['id']);door.say('set '+kind['id']+' card_fields='+Q(defaults[kind['name']] or '-'))
        if kind.get('name') in defaults and 'field_types' not in kind:
            fields=kind.get('fields','').split()
            types={key:('datetime' if key in ('start','end','closes','until') else 'number' if key=='seats' else 'text') for key in fields}
            words={'start':'Starts','end':'Ends','closes':'Sign-ups close','until':'Show until','seats':'Places available','location':'Meeting place','place':'Link to a place','options':'Choices (one word each)'}
            labels={key:words.get(key,key.replace('_',' ').capitalize()) for key in fields}
            door.say('look '+kind['id']);door.say('set '+kind['id']+' field_types='+Q(json.dumps(types))+' field_labels='+Q(json.dumps(labels)))
    code=(HERE/'board-components.bundle.js').read_text(encoding='utf-8')
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
        if name=='board-shell':schema.update(title=T(default='Seabright'),subtitle=T(default='The neighborhood board'),extras=T(default='feed'))
        if name=='board-post':schema.update(layout=T(default='compact'),detail=T('boolean',False),excerptLines=T('number',3),stamp=T(),date=T(),initials=T())
        if name=='board-entry':schema.update(stamp=T())
        if name=='board-thread':schema.update(threadKey=T(default='thread'),replyKey=T(default='replyTo'))
        if name=='board-catchup':schema.update(previewCount=T('number',3))
        if name=='board-chat':schema.update(chatKey=T(default='chat'),longPressMs=T('number',450),title=T(default=''),emoji=T(default='👍 ❤️ 😂 🎉 😮 😢 🙏 👀'),groupMinutes=T('number',7),pageSize=T('number',50),maxComposerHeight=T('number',200),signinUrl=T(default='/signin'))
        if name=='board-composer':schema.update(advancedFields=T(default='closes place'),kindScope=T(default='board'))
        tid=upsert(door,'component',name,category='community',purpose=purpose,settings=json.dumps(schema),
                   parts=json.dumps({p:dict(facts='bound visible row') for p in parts.split()}),slots=json.dumps(slots.split()),
                   gestures=gestures,example=f'root : {name}',uses='Community board; feed; neighborhood',
                   limitations='Presentation and guarded world-word gestures. A channel opens its own view by its opens fact (a calendar today). No map or notification routing.',code=code)
        if door.rows('component',name=name)[0].get('reviewed_code')!=hashlib.sha256(code.encode()).hexdigest():
            door.say('look '+tid);door.say('component '+tid)
    # Each channel's own view and each kind's defaults are world data from definitions.json,
    # brought onto an already-installed world here (a fresh world gets them from install).
    data=json.loads((HERE/'definitions.json').read_text(encoding='utf-8'))
    for definition in data['kinds']:
        for kind in door.rows('kind',name=definition['name']):
            changes={key:definition[key] for key in ('compose_fields_first','compose_message_rows') if key in definition and kind.get(key)!=definition[key]}
            if changes:door.say('look '+kind['id']);door.say(line('set',kind['id'],**changes))
    for definition in data['channels']:
        existing=door.rows('board-channel',title=definition['name'])
        facts={k:definition[k] for k in CHANNEL_KEYS if k in definition}
        if not existing and definition.get('opens')=='chat':
            # a list entry new since this world was installed: its chat and its board-channel thing
            chats=[c for c in door.rows('chat') if c.get('name')==definition['name']]
            cid=chats[0]['id'] if chats else door.say(line('make',kind='chat',name=definition['name']))['made'][0]
            door.say(line('make',kind='board-channel',chat=cid,title=definition['name'],**facts));continue
        if not existing and definition.get('group')=='no':
            door.say(line('make',kind='board-channel',title=definition['name'],**facts));continue
        for channel in existing:
            changes={k:v for k,v in facts.items() if channel.get(k)!=v}
            if changes:door.say('look '+channel['id']);door.say(line('set',channel['id'],**changes))
    for definition in data['kinds']:
        for kind in door.rows('kind',name=definition['name']):
            if definition.get('defaults') and not kind.get('defaults'):
                door.say('look '+kind['id']);door.say(line('set',kind['id'],defaults=definition['defaults']))
    lens=upsert(door,'lens','seabright-board',title='Seabright board',painter='components',right_click='ask',
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
