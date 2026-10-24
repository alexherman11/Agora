"""Real HTTP, simultaneous people and real lens.js drags in hidden Chrome; scratch world only."""
import asyncio
import json
import secrets
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
sys.path[:0] = [str(LAB), str(LAB / 'tests')]
from kernel.kernel import Kernel
from kernel.door import serve
from test_skeleton import StandInEntry
from install import Door, install, quote
from browser import Browser


def run():
    evidence = HERE / 'evidence'
    evidence.mkdir(exist_ok=True)
    world = evidence / ('scratch-' + str(time.time_ns()))
    secret = secrets.token_hex(16)
    entry = StandInEntry(secret)
    k = Kernel(str(world), dict(tag='tb', name='Task board proof', steward=dict(account='alex', name='Alex')))
    srv, host = serve(k, entry.url, secret, 0, LAB)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    entry.kernel_url = url = 'http://127.0.0.1:' + str(srv.server_address[1])
    entry.sessions['alex'] = dict(account='alex', method='proof')
    alex = Door(url, 'alex')
    agent_token, _ = entry.sign_in('alex', 'Alex', agent='Builder')
    agent = Door(url, agent_token)
    checks = []

    def check(name, ok, detail=''):
        checks.append(dict(check=name, ok=bool(ok), detail=detail))
        print(f'{len(checks):02d} {"ok" if ok else "FAIL"} {name}' + (' · ' + str(detail) if detail else ''), flush=True)
        assert ok, (name, detail)

    try:
        made, _ = install(alex)
        check('App installed entirely through HTTP lines', made == 14, f'{made} declarations')
        before = k.state.snapshot(), len(k.log.records)
        check('Second install changes no facts or records', install(alex) == (0, 14) and before == (k.state.snapshot(), len(k.log.records)))
        for word in ('add', 'move', 'assign', 'done', 'note'):
            out = alex.say('help task.' + word)
            check('Dictionary help: task.' + word, bool(out['text']) and k.source(k.entry(k.find_entry('task.'+word)))[0] == 'verb')

        def add(title):
            return alex.say('task.add title=' + quote(title) + ' to=Backlog who=Alex when=2026-10-24 source=proof status=open text="Ready for our community evening"')['made'][0]
        a, b = add('Prepare the neighbourhood meeting'), add('Check the invitation text')
        alex.say('look ' + a)
        agent.say('look ' + b)
        barrier = threading.Barrier(2)
        def move(d, target):
            barrier.wait()
            return d.say(f'task.move {target} to=Now when=2026-10-24')
        with ThreadPoolExecutor(2) as pool:
            jobs = [pool.submit(move, alex, a), pool.submit(move, agent, b)]
            results = [j.result() for j in jobs]
        check('Alex and agent work simultaneously', all(r['ok'] for r in results) and k.state.get(a, 'lane') == k.state.get(b, 'lane') == 'Now')
        rec = k.log.records[int(results[1]['records'][0][1:])-1]
        check('Agent move has real authorship', rec.get('via') == 'agent' and rec.get('for') == k.accounts['alex'], rec.get('via'))
        alex.say('look ' + a)
        alex.say(f'task.assign {a} who=Claude when=2026-10-24')
        alex.say(f'task.note {a} text="Bring the latest agenda" when=2026-10-24')
        scene = alex.request('/api/scene?lens=taskboard&view=painter&text=1')
        assert 'refused' not in scene, scene
        browser = Browser()

        async def picture_and_drags():
            try:
                p = await browser.page(alex)
                q = await browser.page(agent)
                check('Three lanes paint through unchanged lens.js', await p.js("document.querySelectorAll('[data-drop]').length===3"))
                app = 'a' + str(int(b[2:])*8)
                selector = '[data-carry][data-key$="/' + app + '"]'
                # Both hands pick up the same painted generation before either releases it.
                p1 = await p.start_drag(selector, '[data-key="root/board/done"]')
                p2 = await q.start_drag(selector, '[data-key="root/board/backlog"]')
                await p.release(p1)
                await p.until('receipts.length===1')
                first = await p.js('receipts[0]')
                check('Native drag gap reproduced without any source patch', 'needs a thing' in str(first.get('error')) and k.state.get(b, 'lane') == 'Now', first['text'])
                await q.release(p2)
                await q.until('receipts.length===1')
                second = await q.js('receipts[0]')
                check('Both unsupported drags leave the card unchanged', bool(second.get('error')) and k.state.get(b, 'lane') == 'Now', second['text'])
                # Use the existing card-bound button gesture. Keep an old painted gesture for the competing person.
                old = await q.js('sent[0]')
                def walk(node):
                    yield node
                    for kid in node.get('kids', []):
                        yield from walk(kid)
                painted = agent.request('/api/scene?lens=taskboard&view=painter')
                old_node = next(n for n in walk(painted['scene']) if '/'+app+'/' in n['key'] and n['key'].endswith('/moves/backlog'))
                observed = dict(old_node['fence'], at=painted['events_total'], **{'def': painted['scene']['def']})
                point = await p.point(selector + ' [data-key$="/moves/done"]')
                await p.call('Input.dispatchMouseEvent', type='mousePressed', button='left', clickCount=1, **point)
                await p.call('Input.dispatchMouseEvent', type='mouseReleased', button='left', clickCount=1, **point)
                await p.until('receipts.length===2')
                moved = await p.js('receipts[1]')
                check('Lane button moves the card through lens.js', not moved.get('error') and k.state.get(b, 'lane') == 'Done', moved['text'])
                refused = agent.request('/api/do', dict(line=old_node['acts'][0]['line'], observed=observed, gesture=secrets.token_hex(12)))
                check('Competing move from the old painted card is stale', 'stale' in str(refused.get('error')) and k.state.get(b, 'lane') == 'Done', refused['text'])
                move_record = next(r for r in reversed(k.log.records) if r.get('words', '').startswith('task.done'))
                move_events = [f[0] for part in move_record['parts'] for f in part['facts'] if f[1] == 'kind' and f[-1] == 'taskboard-event']
                alex.say('undo r' + str(move_record['seq']))
                check('Undo moves card back and removes its history event', k.state.get(b, 'lane') == 'Now'
                    and all(e not in k.things('taskboard-event') for e in move_events)
                    and any(r.get('undoes') == move_record['seq'] for r in k.log.records))
                await p.until("document.querySelectorAll('[data-carry]').length===2")
                await asyncio.sleep(1.7)
                await p.js("[...document.querySelectorAll('button[aria-label=History]')].forEach(b=>b.click())")
                await p.until("document.querySelector('#paint').innerText.includes('Bring the latest agenda')")
                text = await p.js("document.querySelector('#paint').innerText")
                events = alex.rows('taskboard-event')
                matched = []
                for event in events:
                    r = k.log.records[event['rev']-1]
                    facts = [f for part in r['parts'] for f in part['facts']]
                    matched.append(any(f[0] == event['id'] and f[1] == 'about' for f in facts))
                check('History fold paints authored things from actual task records', bool(events) and all(matched) and 'Bring the latest agenda' in text and 'agent for Alex' in text, f'{len(events)} events linked to their real records')
                (evidence / 'history-records.json').write_text(json.dumps([
                    dict(event=e, record=k.log.records[e['rev']-1]) for e in events], indent=2), encoding='utf-8')
                await p.shot(evidence / 'scratch-board.png')
                check('Hidden screenshot captured', (evidence / 'scratch-board.png').stat().st_size > 10000)
                (evidence / 'drag-receipts.json').write_text(json.dumps(dict(first=first, second=second,
                    requests=[await p.js('sent[0]'), await q.js('sent[0]')], button=moved, stale_button=refused), indent=2), encoding='utf-8')
            finally:
                await browser.close()
        asyncio.run(picture_and_drags())
        alex.say('claim ' + a)
        for _ in range(80):
            if any(e.get('text') == 'Work claimed' for e in alex.rows('taskboard-event')):
                break
            time.sleep(.05)
        check('Claim rule adds real task history', any(e.get('text') == 'Work claimed' and e.get('actor') == k.accounts['alex'] for e in alex.rows('taskboard-event')))
        check('Scratch world replays exactly', Kernel(str(world)).state.snapshot() == k.state.snapshot())
    finally:
        (evidence / 'proof.json').write_text(json.dumps(dict(checks=checks, records=len(k.log.records),
            incomplete=['Native carry/drop seam', 'Raw record history row source']), indent=2), encoding='utf-8')
        host.stop_all()
        for server in (srv, entry.srv):
            server.shutdown()
            server.server_close()
    print(f'{len(checks)} of {len(checks)} checks passed', flush=True)


if __name__ == '__main__':
    run()
