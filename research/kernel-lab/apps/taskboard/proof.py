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
        check('App installed entirely through HTTP lines', made == 13, f'{made} declarations')
        before = k.state.snapshot(), len(k.log.records)
        check('Second install changes no facts or records', install(alex) == (0, 13) and before == (k.state.snapshot(), len(k.log.records)))
        for word in ('add', 'move', 'assign', 'done', 'note'):
            out = alex.say('help task-' + word)
            check('Dictionary help: task-' + word, bool(out['text']) and k.source(k.entry(k.find_entry('task-'+word)))[0] == 'verb')

        def add(title):
            return alex.say('task-add title=' + quote(title) + ' to=Backlog who=Alex when=2026-10-24 source=proof status=open text="Ready for our community evening"')['made'][0]
        a, b = add('Prepare the neighbourhood meeting'), add('Check the invitation text')
        alex.say('look ' + a)
        agent.say('look ' + b)
        barrier = threading.Barrier(2)
        def move(d, target):
            barrier.wait()
            return d.say(f'task-move {target} to=Now')
        with ThreadPoolExecutor(2) as pool:
            jobs = [pool.submit(move, alex, a), pool.submit(move, agent, b)]
            results = [j.result() for j in jobs]
        check('Alex and agent work simultaneously', all(r['ok'] for r in results) and k.state.get(a, 'lane') == k.state.get(b, 'lane') == 'Now')
        rec = k.log.records[int(results[1]['records'][0][1:])-1]
        check('Agent move has real authorship', rec.get('via') == 'agent' and rec.get('for') == k.accounts['alex'], rec.get('via'))
        alex.say('look ' + a)
        alex.say(f'task-assign {a} who=Claude')
        alex.say(f'task-note {a} text="Bring the latest agenda"')
        alex.say(f'set {a} detail="Ordinary edit outside the app words"')
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
                check('Real pointer drag moves Now to Done', not first.get('error') and k.state.get(b, 'lane') == 'Done', first['text'])
                await q.release(p2)
                await q.until('receipts.length===1')
                second = await q.js('receipts[0]')
                check('Second simultaneous pointer drop is stale', 'stale' in str(second.get('error')) and k.state.get(b, 'lane') == 'Done', second['text'])
                # Use the existing card-bound button gesture. Keep an old painted gesture for the competing person.
                old = await q.js('sent[0]')
                def walk(node):
                    yield node
                    for kid in node.get('kids', []):
                        yield from walk(kid)
                painted = agent.request('/api/scene?lens=taskboard&view=painter')
                old_node = next(n for n in walk(painted['scene']) if '/'+app+'/' in n['key'] and n['key'].endswith('/moves/backlog'))
                observed = dict(old_node['fence'], at=painted['events_total'], **{'def': painted['scene']['def']})
                point = await p.point(selector + ' [data-key$="/moves/now"]')
                await p.call('Input.dispatchMouseEvent', type='mousePressed', button='left', clickCount=1, **point)
                await p.call('Input.dispatchMouseEvent', type='mouseReleased', button='left', clickCount=1, **point)
                await p.until('receipts.length===2')
                moved = await p.js('receipts[1]')
                check('Lane button still moves through lens.js', not moved.get('error') and k.state.get(b, 'lane') == 'Now', moved['text'])
                refused = agent.request('/api/do', dict(line=old_node['acts'][0]['line'], observed=observed, gesture=secrets.token_hex(12)))
                check('Competing move from the old painted card is stale', 'stale' in str(refused.get('error')) and k.state.get(b, 'lane') == 'Now', refused['text'])
                move_record = next(r for r in reversed(k.log.records) if r.get('words', '').startswith('task-move'))
                alex.say('undo r' + str(move_record['seq']))
                check('Undo restores Done and its record stays in history', k.state.get(b, 'lane') == 'Done'
                    and any(r['word'] == 'undo' for r in alex.say('history ' + b)['rows'])
                    and any(r.get('undoes') == move_record['seq'] for r in k.log.records)
                    and not k.things('taskboard-event'))
                await p.until("document.querySelectorAll('[data-carry]').length===2")
                await asyncio.sleep(1.7)
                await p.js("[...document.querySelectorAll('button[aria-label=History]')].forEach(b=>b.click())")
                await p.until("document.querySelector('#paint').innerText.includes('Bring the latest agenda')")
                text = await p.js("document.querySelector('#paint').innerText")
                events = alex.say('history ' + a)['rows'] + alex.say('history ' + b)['rows']
                matched = [e['at'] == k.log.records[int(e['record'][1:])-1]['at'] for e in events]
                check('History fold paints raw records, direct edits and undo', bool(events) and all(matched)
                    and 'Bring the latest agenda' in text and 'agent for Alex' in text
                    and 'Ordinary edit outside the app words' in text and 'undo' in text,
                    f'{len(events)} rows linked to actual records')
                dates = await p.js("[...document.querySelectorAll('[data-key$=\"/history/created\"]')].map(n=>n.innerText)")
                check('Dates paint from the kernel clock and records', k.now().date().isoformat() in text
                    and len(dates) == 2 and all('none' not in d and 'changed 20' in d for d in dates)
                    and k.shown(k.accounts['alex'], a)['made'] in dates[0])
                (evidence / 'history-records.json').write_text(json.dumps([
                    dict(event=e, record=k.log.records[int(e['record'][1:])-1]) for e in events], indent=2), encoding='utf-8')
                await p.shot(evidence / 'scratch-board.png')
                check('Hidden screenshot captured', (evidence / 'scratch-board.png').stat().st_size > 10000)
                (evidence / 'drag-receipts.json').write_text(json.dumps(dict(first=first, second=second,
                    requests=[await p.js('sent[0]'), await q.js('sent[0]')], button=moved, stale_button=refused), indent=2), encoding='utf-8')
            finally:
                await browser.close()
        asyncio.run(picture_and_drags())
        alex.say('claim ' + a)
        for _ in range(80):
            if any(e.get('text') == 'Task completed' and e.get('about') == b for e in alex.rows('post')):
                break
            time.sleep(.05)
        check('Done own-word rule announces in Feed', any(e.get('text') == 'Task completed'
              and e.get('about') == b for e in alex.rows('post')))
        check('Claim appears in the real record trail', any(e['word'] == 'claim' for e in alex.say('history ' + a)['rows']))
        check('Scratch world replays exactly', Kernel(str(world)).state.snapshot() == k.state.snapshot())
    finally:
        (evidence / 'proof.json').write_text(json.dumps(dict(checks=checks, records=len(k.log.records),
            incomplete=[]), indent=2), encoding='utf-8')
        host.stop_all()
        for server in (srv, entry.srv):
            server.shutdown()
            server.server_close()
    print(f'{len(checks)} of {len(checks)} checks passed', flush=True)


# v1 scenario above is retained as historical evidence; v2 is the acceptance,
# including when another proof imports this module's run function.
from proof_v2 import run

if __name__ == '__main__':
    run()
