"""Real isolated-world receipts and compiled arrangements; no browser/model/live door."""
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
LAB=HERE.parents[1]/'agora'
sys.path[:0]=[str(HERE),str(LAB)]
from proof import Proof, install, line
from painter.catalogue import cards
from painter.install import upsert
from painter.arrangement import compile_view, resolve_line
from asks_install import VIEW
from ui_install import NAMES


def main():
    f=Proof()
    location=Path(f.tmp.name)
    try:
        ids=install(lambda s:f.say('Alex',s),lambda s:f.see('Alex',s))
        class Door:
            say=staticmethod(lambda s:f.say('Alex',s))
            rows=staticmethod(lambda kind,**kw:f.see('Alex',line('rows',kind,**kw))['rows'])
        d=Door()
        original={kind:d.rows(kind) for kind in ('grant','widget','window')}
        for card in cards():
            name=card.pop('name');source=LAB/'components'/f'{name}.js'
            tid=upsert(d,'component',name,**card,code=(source if source.exists() else LAB/'components/catalogue.js').read_text(encoding='utf-8'))
            d.say('look '+tid);d.say('component '+tid)
        # Only the shared thread is needed by this arrangement. It accepts arbitrary
        # text-block children carrying visible target facts.
        purpose,parts,slots,gestures=NAMES['board-thread']
        tid=upsert(d,'component','board-thread',purpose=purpose,settings=json.dumps({
            'threadKey':{'type':'text','default':'thread'},'replyKey':{'type':'text','default':'replyTo'}}),
            parts=json.dumps({p:{} for p in parts.split()}),slots=json.dumps(slots.split()),gestures=gestures,
            code=(HERE/'board-components.bundle.js').read_text(encoding='utf-8'))
        d.say('look '+tid);d.say('component '+tid)
        channel=ids['channels']['Asks & offers']
        lens=upsert(d,'lens','round2-asks',painter='components',
                    text=(HERE/'asks.lens').read_text(encoding='utf-8'),view=json.dumps(dict(VIEW,asks_channel=channel)))
        actor=f.k.actor_for(f.k.accounts['alex'])
        def plan(view=None):
            return compile_view(f.k,actor,lens,reader=lambda s:f.raw('Alex',s,'see'),view=view or {})['rows'][0]
        def walk(n):
            yield n
            for c in n['children']:yield from walk(c)
        def named(tree,name):
            return next(n for n in walk(tree) if n['name']==name)
        def command(node,event,**values):
            g=next(g for g in node['gestures'] if g['event']==event)
            return resolve_line(g['line'],dict(g['env'],**values))
        p=plan()
        ask=d.say(command(named(p['tree'],'ask'),'submit',value='Ladder needed'))['made'][0]
        p=plan()
        reply=named(p['tree'],'reply')
        f.check('Asks reply routes both scoped keys to the actual post',
                reply['settings']['selectKey']=='asksThread asksReplyTo' and reply['settings']['value']==ask)
        p=plan({'asksThread':ask,'asksReplyTo':ask})
        conversation=named(p['tree'],'conversation')
        f.check('standalone Asks compiles a visible conversation with the selected text',
                named(conversation,'selected')['children'][0]['settings']['value']=='Ladder needed')
        # Resolve the actual authored reply gesture, then exercise board.reply directly.
        g=next(g for g in conversation['gestures'] if g['event']=='reply')
        cmd=resolve_line(g['line'].replace('$fields','text="I can bring it"'),dict(g['env'],target=ask))
        reply_id=d.say(cmd)['made'][0]
        f.check('reply from the Asks arrangement reaches its source thread',
                next(r for r in d.rows('post') if r['id']==reply_id)['thread']==ask)
        done=named(plan()['tree'],'done')
        receipt=d.say(command(done,'press'))['records'][-1]
        f.check('done item leaves the active list',not named(plan()['tree'],'entries')['children'])
        f.check('completed filter recovers the item',
                named(plan({'asks_status':'done'})['tree'],'entries')['children'][0]['facts']['id']==ask)
        recovery=named(plan()['tree'],'outcome')
        d.say(command(recovery,'undo',value=receipt))
        f.check('receipt-specific completion Undo restores the same item',
                named(plan()['tree'],'entries')['children'][0]['facts']['id']==ask)

        pin=d.say(line('make',kind='spot',name='Fixture meeting point',lat='36.9',lon='-122.0'))['made'][0]
        move=d.say(line('set',pin,lat='36.91',lon='-122.01'))['records'][-1]
        unrelated=d.say(line('make',kind='note',text='Unrelated action after move'))['made'][0]
        d.say(command(recovery,'undo',value=move))
        restored=f.see('Alex','look '+pin)['rows'][0]
        f.check('map-style exact-receipt Undo restores both coordinates after an unrelated act',
                str(restored['lat'])=='36.9' and str(restored['lon'])=='-122.0')
        f.check('Undo preserves the later unrelated action',bool(f.see('Alex','look '+unrelated)['rows']))

        event=d.say(line('board.post',post_kind='event',start='2026-11-08T18:00:00Z',text='Fixture picnic',
                         **{'in':ids['channels']['Meetings & events']}))['made'][0]
        f.check('event is admitted without typed capacity and uses its world default',str(next(r for r in d.rows('post') if r['id']==event)['seats'])=='500')
        attendance=d.say(line('board.rsvp',event,status='going'))['records'][-1]
        d.say(command(recovery,'undo',value=attendance))
        f.check('attendance Undo removes RSVP and restores the reserved seat',
                not [r for r in d.rows('board-rsvp') if r.get('about')==event] and next(r for r in d.rows('post') if r['id']==event)['seats_left']==500)
        marked=d.say(line('board.personal',ask,action='hide'))['records'][-1]
        f.check('private hide excludes its source from the feed',ask not in [r['id'] for r in f.see('Alex','board.feed')['rows']])
        d.say(command(recovery,'undo',value=marked))
        f.check('private-hide Undo restores the source',ask in [r['id'] for r in f.see('Alex','board.feed')['rows']])
        # Work uses a real task action, with exact-receipt recovery, not filter restoration.
        work_line=upsert(d,'component','work-line',purpose='Fixture Work task action',
                        settings=json.dumps({'title':{'type':'text'},'state':{'type':'text'}}),
                        parts='{"body": {}, "done": {}}',slots='[]',gestures='done',
                        code=(LAB/'components/work-line.js').read_text(encoding='utf-8'))
        d.say('look '+work_line);d.say('component '+work_line)
        task=d.say(line('make',kind='taskboard-task',title='Fixture Work task',lane='Now'))['made'][0]
        # Replace only House's data reader with fixture rows. Keep the authored Work action.
        work_text=(LAB/'apps/work/work.lens').read_text(encoding='utf-8')
        work_text=work_text.replace('root : work-overview','root : column').replace(
            'of reading:"house.active" as t','of tag:taskboard-task as t')
        work_lens=upsert(d,'lens','round2-work',painter='components',text=work_text,view='{}')
        work_plan=compile_view(f.k,actor,work_lens,reader=lambda s:f.raw('Alex',s,'see'),view={})['rows'][0]
        task_node=next(n for n in walk(work_plan['tree']) if n['component']=='work-line')
        done_receipt=d.say(command(task_node,'done'))['records'][-1]
        f.check('Work authored Mark done actually updates the fixture task',
                f.see('Alex','look '+task)['rows'][0]['lane']=='Done')
        work_notice=named(work_plan['tree'],'notice')
        f.check('Work exposes the shared notice with scoped action state',
                work_notice['settings']['stateKey']=='workNotice'
                and work_notice['settings']['scopeKeys']=='workFilter workPage')
        d.say(command(work_notice,'undo',value=done_receipt))
        f.check('Work authored Undo restores the exact task state',
                f.see('Alex','look '+task)['rows'][0]['lane']=='Now')
        f.check('new capability test changes no widget grant or window',all(d.rows(k)==rows for k,rows in original.items()))
        f.check('discoverable notice metadata names exact receipt and reuse',
                all(word in d.rows('component',name='action-notice')[0]['limitations'] for word in ('receipt','Undo')))
        print('ROUND2 WORLD CHECKS '+str(f.checks),flush=True)
    finally:
        f.close()
    assert not location.exists(),str(location)
    print('ROUND2 FIXTURE REMOVED',flush=True)

if __name__=='__main__':
    main()
