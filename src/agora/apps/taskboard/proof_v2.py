"""Two real sessions, a real module process and unchanged painter. Scratch only.

Default runs a ten-minute, 25-task triage with reads/actions throughout; --minutes
0 is a development pass and is explicitly labelled as such in the evidence.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import secrets
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
sys.path[:0] = [str(LAB), str(LAB / 'tests')]
from kernel.kernel import Kernel
from kernel.door import serve
from test_skeleton import StandInEntry
from install import Door, install, migrate, quote
from browser import Browser

TITLES = [
    'Fix the bar before the neighbourhood demo', 'Confirm the venue and accessible entrance',
    'Review invitation wording with the organisers', 'Print a large type version of the agenda',
    'Ask the library about the projector', 'Prepare tea and a quiet corner',
    'Check that the microphone reaches the back row', 'Write a short welcome for newcomers',
    'Collect questions about the Seabright crossing', 'Share the bus timetable with visitors',
    'Check the door signage; include the side entrance', 'Bring spare pens and blank name badges',
    'Confirm the chairs and leave space for wheelchairs', 'Draft a follow-up message for volunteers',
    'Test the map on a phone before the meeting', 'Ask two neighbours to review the task board',
    'Set aside five minutes for a break', 'Prepare a checklist for the evening hosts',
    'Find the latest council meeting notes', 'Summarize the actions after the meeting',
    'Keep the original notes alongside the summary', 'Arrange a ride home for the late volunteers',
    'Recheck the date on the printed flyers', 'Thank everyone who helped with setup',
    'Plan the next small step with the group',
]


def run():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--minutes', type=float, default=10)
    args = ap.parse_args()
    evidence = HERE / 'evidence'
    evidence.mkdir(exist_ok=True)
    world = evidence / ('scratch-v2-' + str(time.time_ns()))
    entry = StandInEntry(secrets.token_hex(16))
    spec = dict(name='summarize', run=[sys.executable, str(LAB/'modules/summarize/summarize.py')],
                publishes='summarize.*', grants='summarize.* rows make set',
                only='kind:taskboard-task', **{'for': 'steward'})
    k = Kernel(str(world), dict(tag='tv', name='Task board v2 proof',
                steward=dict(account='alex', name='Alex'), modules=[spec]))
    srv, host = serve(k, entry.url, entry.secret, 0, LAB)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    entry.kernel_url = url = 'http://127.0.0.1:' + str(srv.server_address[1])
    entry.sessions['alex'] = dict(account='alex', method='proof')
    alex = Door(url, 'alex')
    token, _ = entry.sign_in('alex', 'Alex', agent='Builder')
    agent = Door(url, token)
    checks, activity = [], []
    started = time.monotonic()

    def check(name, ok, detail=''):
        checks.append(dict(check=name, ok=bool(ok), detail=detail))
        print(f'{len(checks):02d} {"ok" if ok else "FAIL"} {name}' + (' · '+str(detail) if detail else ''), flush=True)
        assert ok, (name, detail)

    def say(d, line):
        result = d.say(line)
        activity.append(dict(seconds=round(time.monotonic()-started, 3), who='Alex' if d is alex else 'agent',
                             line=line, records=result.get('records')))
        return result

    def wait_summaries():
        for _ in range(200):
            rows = alex.rows('taskboard-task')
            if rows and all(t.get('short') for t in rows):
                return rows
            time.sleep(.05)
        raise AssertionError('automatic summaries did not settle')

    try:
        for _ in range(100):
            if k.find_entry('summarize.task'):
                break
            time.sleep(.05)
        made, skipped = install(alex)
        check('Authored world definitions install', made == 24, f'{made} declarations')
        style = alex.request('/api/style?name=taskboard')
        check('Style resolves without refused or unread properties', bool(style.get('looks')) and not style.get('refusal') and not style.get('looks',{}).get('unread'), str(style.get('refusal','')))
        before = len(k.log.records)
        check('Second install is a no-op', install(alex) == (0, 24) and len(k.log.records) == before)
        check('Empty board explains quick add', 'A clear board. Add your first task' in alex.request('/api/scene?lens=taskboard&text=1')['text'])
        mid = k.module_named('summarize')
        check('Summary writes are restricted to task things', all(k.state.get(g,'only')=='kind:taskboard-task' for g in k.things('grant') if k.state.get(g,'to')==mid))
        # Deterministic offline run: exercise unavailable-model fallback without
        # downloading or invoking the user's installed model on 25 fixtures.
        settings = alex.rows('taskboard-settings')[0]
        alex.say('set '+settings['id']+' model=taskboard-proof-unavailable')
        for word in ('task-priority', 'task-note-colour', 'task-note-style', 'task-remove', 'summarize.task', 'summarize.all', 'summarize.add'):
            check('Help: '+word, bool(alex.say('help '+word)['text']))
        tasks = []
        triage_start = time.monotonic()
        for i, title in enumerate(TITLES):
            d = alex if i % 2 == 0 else agent
            out = say(d, 'summarize.add text=' + quote(title + ' p' + str(i % 4 + 1)))
            task = out['made'][0]
            tasks.append(task)
            wait_summaries()
            say(d, 'look '+task)
            if i % 3 == 0:
                say(d, 'task-move '+task+' to=Now')
            if i in (0, 1):
                say(d, 'task-note '+task+' text='+quote('## Evening notes\n\n**Welcome** every neighbour.\n\n- [ ] Check the entrance\n- [ ] Bring tea\n\nKeep the *original* details.'))
                say(d, 'task-note-colour '+task+' colour='+('sage' if i == 0 else 'lilac'))
                say(d, 'task-note-style '+task+' style='+('strong' if i == 0 else 'slant'))
            if i == 15:
                say(agent, 'summarize.all lane=Now')
            # Sustain actual triage for the requested wall time, including reads
            # by both people; no invented timestamps or backdated records.
            due = triage_start + args.minutes * 60 * (i + 1) / 25
            while time.monotonic() < due:
                say(d, 'history '+task)
                time.sleep(min(5, max(0, due-time.monotonic())))
        elapsed = time.monotonic()-triage_start
        rows = wait_summaries()
        check('25 quick-adds parse p1–p4 and preserve descriptions', len(rows)==25 and all(
            k.state.get(t,'title') == title and str(k.state.get(t,'priority')) == str(i%4+1)
            for i,(t,title) in enumerate(zip(tasks,TITLES))))
        check('Automatic summaries disclose provenance', all(t.get('short_source') and '\n' not in t['short'] and len(t['short'])<=90 for t in rows))
        check('Two notes retain multiline Markdown, colours and styles',
              all('\n- [ ]' in k.state.get(t,'note') for t in tasks[:2]) and
              k.state.get(tasks[0],'note_colour')=='sage' and k.state.get(tasks[1],'note_style')=='slant')
        check('Triage duration', elapsed >= args.minutes*60, f'{elapsed:.1f} seconds; requested {args.minutes:g} minutes')
        browser = Browser()

        async def visuals():
            try:
                p, q = await browser.page(alex), await browser.page(agent)
                await p.until("document.querySelectorAll('[data-carry]').length===25")
                await p.js("document.querySelector('[data-key=\"root/toolbar/add\"]').focus()")
                await p.call('Input.insertText', text='Check the back door p2')
                await p.call('Input.dispatchKeyEvent', type='keyDown', key='Enter', code='Enter', windowsVirtualKeyCode=13)
                await p.call('Input.dispatchKeyEvent', type='keyUp', key='Enter', code='Enter', windowsVirtualKeyCode=13)
                await p.until('receipts.length===1')
                added = next((t for t in alex.rows('taskboard-task') if t.get('title')=='Check the back door'), None)
                check('Real quick-add typing keeps spaces and strips p2', added is not None and str(added['priority'])=='2')
                wait_summaries()
                say(alex, 'look '+added['id'])
                say(alex, 'set '+added['id']+' short= short_source=')
                await p.until("[...document.querySelectorAll('[data-carry]')].some(n=>n.innerText.includes('Check the back door'))")
                check('Missing or undone summary retains original description', 'Check the back door' in alex.request('/api/scene?lens=taskboard&text=1')['text'])
                say(alex, 'look '+added['id'])
                say(alex, 'task-remove '+added['id'])
                await p.until("document.querySelectorAll('[data-carry]').length===25")
                await p.js('receipts=[];sent=[]')
                check('25 cards in three drop lanes at 1600px', await p.js("innerWidth===1600 && document.querySelectorAll('[data-drop]').length===3"))
                check('Every task paints a priority icon', await p.js("document.querySelectorAll('[data-carry] svg').length===25"))
                app = 'a'+str(int(tasks[0][2:])*8)
                selector = '[data-carry][data-key$="/'+app+'"]'
                async def menu(selector, label=None):
                    point = await p.point(selector, .8, .15)
                    await p.call('Input.dispatchMouseEvent', type='mousePressed', button='right', clickCount=1, **point)
                    await p.call('Input.dispatchMouseEvent', type='mouseReleased', button='right', clickCount=1, **point)
                    await p.until("!!document.querySelector('#menu-pop')")
                    if label:
                        count = await p.js('(()=>{let b=[...document.querySelectorAll("#menu-pop button")].find(b=>b.textContent==='+json.dumps(label)+');if(!b)return 0;b.click();return 1})()')
                        assert count, label
                await menu(selector)
                await p.shot(evidence/'v2-card-menu.png')
                check('Card menu exposes requested actions', await p.js("['Priority · P1','Colour · Sage','Move · Done','Assign · my agent','Rename','Summarize','Remove · undo brings it back'].every(t=>[...document.querySelectorAll('#menu-pop button')].some(b=>b.textContent===t))"))
                await p.js("[...document.querySelectorAll('#menu-pop button')].find(b=>b.textContent==='Priority · P2').click()")
                await p.until('receipts.length===1')
                check('Priority changes through real card menu', not (await p.js('receipts[0]')).get('error') and str(k.state.get(tasks[0],'priority'))=='2')
                # Actual native pointer drags from the same painted generation.
                await q.until("document.querySelectorAll('[data-carry]').length===25")
                await asyncio.sleep(.6)
                a = await p.start_drag(selector, '[data-key="root/board/done"]')
                b = await q.start_drag(selector, '[data-key="root/board/backlog"]')
                n = await p.js('receipts.length')
                await p.release(a)
                await p.until(f'receipts.length>{n}')
                first = await p.js('receipts.at(-1)')
                await q.release(b)
                await q.until('receipts.length===1')
                stale = await q.js('receipts[0]')
                check('Pointer drag moves card to Done', not first.get('error') and k.state.get(tasks[0],'lane')=='Done', first.get('text'))
                check('Stale competing drag refuses without moving', 'stale' in str(stale.get('error')) and k.state.get(tasks[0],'lane')=='Done')
                say(alex, 'look '+tasks[0])
                say(alex, 'task-move '+tasks[0]+' to=Now')
                await p.until("document.querySelectorAll('[data-carry]').length===25")
                await asyncio.sleep(.6)
                # Counts and sorted order are read from the actual scene/DOM.
                priorities = await p.js("[...document.querySelectorAll('[data-key=\"root/board/backlog/cards\"] > [data-carry]')].map(n=>n.querySelector('[data-key$=\"/summary\"]').innerText)")
                painted = alex.request('/api/scene?lens=taskboard&view=painter&text=1')
                check('Priority ordering compiles with real counts', 'by priority' in painted.get('text','') and 'Backlog · 16' in (await p.js("document.querySelector('#paint').innerText")))
                ordered = await p.js('''[...document.querySelectorAll('[data-key$="/cards"]')].every(l=>{
                  const ns=[...l.children].filter(n=>n.hasAttribute('data-carry')).map(n=>Number(n.querySelector('svg').parentElement.dataset.key.match(/p([1-4])$/)[1]));
                  return ns.every((n,i)=>i===0||ns[i-1]<=n)})''')
                check('Painted tasks sort by priority in every lane', ordered)
                await p.shot(evidence/'v2-board-1600.png')
                await p.js('document.querySelector('+json.dumps(selector)+').querySelector("button[aria-label=Details]").click()')
                await p.until('!!document.querySelector('+json.dumps(selector+' [data-key$="/details/editor/prose"]')+')')
                editor = selector+' [data-key$="/details/editor"]'
                prose = editor+' [contenteditable=true]'
                await p.js('document.querySelector('+json.dumps(prose)+').focus()')
                await p.js('document.querySelector('+json.dumps(editor+' [data-key$="/toolbar/source"]')+').click()')
                await p.call('Input.dispatchKeyEvent', type='keyDown', key='a', code='KeyA', modifiers=2, windowsVirtualKeyCode=65)
                await p.call('Input.dispatchKeyEvent', type='keyUp', key='a', code='KeyA', modifiers=2, windowsVirtualKeyCode=65)
                edited = '## Evening notes\n\nWelcome every neighbour.\n\n- [ ] Check the entrance\n- [ ] Bring tea\n\nA follow-up for neighbours.'
                await p.call('Input.insertText', text=edited)
                async def mark(word, button):
                    # Native selection in the actual editor, then its authored
                    # toolbar press; no direct invocation of editor internals.
                    found = await p.js('''(()=>{const r=document.querySelector('''+json.dumps(prose)+''');
                    const w=document.createTreeWalker(r,NodeFilter.SHOW_TEXT);let n;
                    while(n=w.nextNode()){const i=n.textContent.indexOf('''+json.dumps(word)+''');if(i>=0){
                    const s=getSelection();s.setBaseAndExtent(n,i,n,i+'''+str(len(word))+''');return true}}return false})()''')
                    assert found, word
                    await p.js('document.querySelector('+json.dumps(editor+' [data-key$="/toolbar/'+button+'"]')+').click()')
                await mark('follow-up', 'bold')
                await mark('neighbours', 'italic')
                await p.js('document.querySelector('+json.dumps(editor+' [data-key$="/toolbar/save"]')+').click()')
                for _ in range(100):
                    if '**follow-up**' in k.state.get(tasks[0],'note'):
                        break
                    await asyncio.sleep(.1)
                check('Real multiline note editing, Bold, Italic and Save', '**follow-up**' in k.state.get(tasks[0],'note') and '*neighbours*' in k.state.get(tasks[0],'note') and '\n- [ ] Bring tea' in k.state.get(tasks[0],'note'))
                await p.js('document.querySelector('+json.dumps(editor+' [data-key$="/toolbar/source"]')+').click()')
                await menu(editor, 'Note colour · Peach')
                await p.until("!document.querySelector('#menu-pop')")
                await asyncio.sleep(.4)
                await menu(editor, 'Note style · slant')
                await asyncio.sleep(.6)
                check('Note menu changes actual colour and style facts', k.state.get(tasks[0],'note_colour')=='peach' and k.state.get(tasks[0],'note_style')=='slant')
                await p.js('document.querySelector('+json.dumps(editor)+').scrollIntoView({block:"center"})')
                await p.shot(evidence/'v2-note-editor.png')
                check('Three hidden screenshots saved', all((evidence/name).stat().st_size>10000 for name in ('v2-board-1600.png','v2-note-editor.png','v2-card-menu.png')))
                # Chips are actual lens gestures, shared state is intentional.
                n = await p.js('receipts.length')
                await p.js("document.querySelector('[data-key=\"root/filters/p1\"]').click()")
                await p.until(f'receipts.length>{n}')
                await p.until("document.querySelectorAll('[data-carry]').length===6")
                check('P1 chip filters tasks', k.state.get(alex.rows('taskboard-settings')[0]['id'],'filter')=='1')
                await p.js("document.querySelector('[data-key=\"root/filters/pall\"]').click()")
                await p.until("document.querySelectorAll('[data-carry]').length===25")
                (evidence/'v2-drags.json').write_text(json.dumps(dict(first=first, stale=stale), indent=2), encoding='utf-8')
            finally:
                await browser.close()
        asyncio.run(visuals())
        say(agent, 'look '+tasks[-1])
        say(agent, 'task-remove '+tasks[-1])
        check('Remove forgets a card', tasks[-1] not in [t['id'] for t in alex.rows('taskboard-task')])
        say(agent, 'undo')
        check('Undo my last act restores card and history', tasks[-1] in [t['id'] for t in alex.rows('taskboard-task')] and any(e['word']=='undo' for e in agent.say('history '+tasks[-1])['rows']))
        before = len(k.log.records)
        check('Migration is idempotent', migrate(alex)==0 and len(k.log.records)==before)
        check('Scratch replay matches all current facts', Kernel(str(world)).state.snapshot()==k.state.snapshot())
    finally:
        (evidence/'v2-proof.json').write_text(json.dumps(dict(checks=checks, activity=activity,
            requested_minutes=args.minutes, wall_seconds=round(time.monotonic()-started, 2),
            records=len(k.log.records), at=datetime.now(timezone.utc).isoformat()), indent=2), encoding='utf-8')
        host.stop_all()
        for server in (srv, entry.srv):
            server.shutdown()
            server.server_close()
    print(f'{len(checks)} of {len(checks)} checks passed', flush=True)
