"""Fast hidden regression for a committed dialog and its unobscured Undo."""
import ui_proof
from ui_proof import fixtures
from pathlib import Path
from install import install
from protocol import line


def minimal(f):
    ids=install(lambda x:f.say('Alex',x),lambda x:f.see('Alex',x))
    f.say('Alex',line('board.post',title='Walking together',text='Meet at the crossing.',**{'in':ids['channels']['Neighbours']}))
    return dict(posts=1)


ui_proof.Proof.run=minimal
ui=ui_proof.UI()
ui.metrics['first_paint_upper_bound_ms']=0  # Focused probes never overwrite acceptance rasters.
try:
    p=ui.page();post=ui.posts[0];ui.navigate(p,thread=post['id'],replyTo=post['id'])
    ui.click(p,'.nb-thread [data-post='+post['id']+'] > .nb-actions > .nb-more > summary')
    ui.button(p,'Hide with a reason','document.querySelector(".nb-thread")')
    ui.fill(p,'[aria-label="Reason for hiding"]','Verify the crossing time.')
    ui.button(p,'Save');ui.wait(p,'!document.querySelector(".nb-dialog")&&!!document.querySelector(".nb-notice")')
    ui.check('Successful hide closes its dialog before repaint',True)
    ui.button(p,'Undo hide','document.querySelector(".nb-notice")')
    ui.wait(p,'!!document.querySelector(".nb-thread [data-post='+post['id']+']")')
    ui.check('Unobscured pointer Undo restores the hidden post',any(row['id']==post['id'] for row in ui.d.rows('post')))
    ui.click(p,'.nb-masthead .nb-primary');ui.wait(p,'!!document.querySelector(".nb-kind-tiles")&&document.querySelector("[aria-label=\\"Post type\\"]").options.length>=9');ui.choose(p,'[aria-label="Post type"]','discussion')
    ui.fill(p,'[aria-label="Your message"]','Bring a copy for a neighbour.');ui.fill(p,'[aria-label="Title (optional)"]','Two attachments')
    paths=[]
    for name in ['camera.txt','planning.pdf']:
        path=Path(ui.f.tmp.name)/name;path.write_bytes(fixtures()[name]);paths.append(str(path))
    remote=p.c.call('Runtime.evaluate',expression='document.querySelector("input[type=file]")',**p.context())['result']['objectId']
    p.c.call('DOM.setFileInputFiles',files=paths,objectId=remote,**({'_session':p.context()['_session']} if '_session' in p.context() else {}))
    ui.wait(p,'document.querySelectorAll(".nb-upload-list p").length===2',35)
    ui.button(p,'Post to neighbours');ui.wait(p,'!document.querySelector(".nb-dialog")',35)
    made=next(row for row in ui.d.rows('post') if row.get('title')=='Two attachments')
    ui.check('Final attach closes compose and retains both attachments',len([row for row in ui.d.rows('file') if row.get('attached_to')==made['id']])==2)
    ui.navigate(p,thread='')
    from ui_install import Q
    ui.d.say('make kind=component name=polish-extra settings="{}" parts="{}" slots="[]" code='+Q('export default {mount(){while(true){}}}'))
    lens=ui.d.rows('lens',name='seabright-board')[0];ui.d.say('look '+lens['id']);ui.d.say('set '+lens['id']+' text='+Q(lens['text'].replace('  centre :','  broken : polish-extra\n  centre :')))
    ui.wait(p,'!!document.querySelector(".nb-centre>.component-stopped")',20)
    ui.check('Stopped extra retains the feed column width',p.js('document.querySelector(".nb-centre").getBoundingClientRect().width>1000'))
    from ui_install import widget_source,GRANTS
    from painter.browser import Page
    ui.d.say(line('make',kind='lens',name='polish-date',painter='components',text='root : date-tile, start "2026-11-04T18:00:00Z", end "2026-11-04T20:00:00Z", place "The library"'))
    widget=ui.d.say(line('make',kind='widget',name='polish-date',title='Date tile proof',component_lens='polish-date',code=widget_source()))['made'][0]
    ui.d.say('look '+widget);ui.d.say(line('widget '+widget,surface='window',grants=GRANTS))
    date=Page(ui.url,ui.f.tokens['Alex'],widget,640,480,clock=ui.f.at);ui.pages.append(date)
    ui.wait(date,'!!document.querySelector(".date-tile-calendar")')
    ui.check('Date tile carries its skin without the board shell',date.js('!document.querySelector(".nb-shell")&&getComputedStyle(document.querySelector(".date-tile-calendar")).display==="flex"&&document.querySelector(".date-tile-calendar").getBoundingClientRect().width===62'))
    date.shot(ui_proof.OUT/'polish'/'date-tile-standalone.png')
    ui.fill(p,'[aria-label="Search the board"]','written comments');ui.key(p,'Enter')
    ui.wait(p,'!!document.querySelector(".nb-search .nb-entry-button")')
    ui.click(p,'.nb-search .nb-entry-button')
    ui.wait(p,'document.querySelector(".nb-thread [aria-label=\\"Choose a page\\"]")?.value==="3"')
    ui.check('A document page search hit opens its owning thread at page three',True)
    event=ui.f.say('Alex',line('board.post',post_kind='event',title='A library meeting',text='Meet at the library.',start='2026-11-04T18:00:00Z',seats='3',**{'in':ui.channels['Meetings & events']}))['made'][0]
    ui.navigate(p,thread=event,search='')
    ui.d.say('make kind=part-style lens=seabright-board target=tokens date-tile-day-size=42px')
    ui.wait(p,'getComputedStyle(document.querySelector(".nb-thread .date-tile-calendar strong")).fontSize==="42px"')
    ui.check('Catalogue date-tile tokens also change the board through world handles',True)
    print('POLISH ACTIONS: 7/7 checks passed; hidden=True',flush=True)
finally:ui.close()
