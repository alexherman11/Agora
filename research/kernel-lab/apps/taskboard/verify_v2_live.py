"""Read-only deployment boundary checks; --before saves facts/history, no tokens.

Run --before immediately before the authorized upgrade, then run without flags
after install.py. The hidden capture reads the live world without touching its
native window, focus, drafts or scroll position.
"""
import argparse
import asyncio
import json
from pathlib import Path
from install import live_door, install, migrate
from browser import Browser

HERE = Path(__file__).resolve().parent
BASELINE = HERE/'evidence/v2-live-before.json'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before', action='store_true')
    args = ap.parse_args()
    d = live_door()
    tasks = d.rows('taskboard-task')
    histories = {t['id']:d.say('history '+t['id'])['rows'] for t in tasks}
    windows = d.say('window.list')['rows']
    if args.before:
        BASELINE.parent.mkdir(exist_ok=True)
        BASELINE.write_text(json.dumps(dict(tasks=tasks, histories=histories,
            windows=windows), indent=2, ensure_ascii=False), encoding='utf-8')
        print(f'LIVE BEFORE: {len(tasks)} cards, {sum(map(len,histories.values()))} history rows saved; no session tokens')
        return
    before = json.loads(BASELINE.read_text(encoding='utf-8'))
    current = {t['id']:t for t in tasks}
    assert all(t['id'] in current for t in before['tasks']), 'An existing card disappeared'
    for old in before['tasks']:
        for key,value in old.items():
            if key not in ('rev','changed'):
                assert current[old['id']].get(key)==value, (old['id'],key,'previous fact changed')
        prior = before['histories'][old['id']]
        assert histories[old['id']][:len(prior)]==prior, 'Historical rows changed'
    assert all(t.get('short') and t.get('short_source') and t.get('priority') for t in tasks)
    module = d.rows('module', name='summarize')[0]
    grants = [g for g in d.rows('grant') if g.get('to')==module['id'] and not g.get('revoked')]
    assert grants and all(g.get('only')=='kind:taskboard-task' for g in grants)
    for name in ('summarize.task','summarize.all','summarize.add','summarize.save'):
        word = d.rows('word',bound=name)[0]
        assert word['undo']=='yes'
    state = d.say('status summarize')
    assert state['ok'] and 'Local task summaries' in state['text'], state['text']
    scene = d.request('/api/scene?lens=taskboard&view=painter&text=1')
    assert not scene.get('refused') and 'A little space for what matters' in scene['text']
    assert d.request('/api/style?name=taskboard').get('looks')
    shown = [w for w in windows if w.get('shows')=='taskboard' and w.get('shown')]
    assert len(shown)==1, 'Task board native visibility not confirmed'
    assert install(d)==(0,24) and migrate(d)==0, 'Repeat install would change app facts'
    async def capture():
        b = Browser()
        try:
            p = await b.page(d)
            await p.until("document.querySelectorAll('[data-carry] svg').length==="+str(len(tasks)))
            await p.shot(HERE/'evidence/v2-live-board-hidden.png')
        finally:
            await b.close()
    asyncio.run(capture())
    report = dict(cards=len(tasks), preserved=len(before['tasks']), histories_preserved=True,
                  shown=shown, module_status=state['text'],
                  model_cards=sum(t['short_source'].startswith('local model') for t in tasks),
                  fallback_cards=sum(t['short_source']=='short version, no model' for t in tasks))
    (HERE/'evidence/v2-live.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f'LIVE OK: {len(tasks)} cards; all {len(before["tasks"])} original identities, facts and history prefixes preserved')
    print('LIVE OK: summarize process answering; task-only grant; undo=yes; repeat install/migration changes nothing')
    print('LIVE OK: v2 scene/style and priority icons painted hidden; one native Task board shown; native pixels checked separately')
    print(f'LIVE SUMMARY SOURCES: {report["model_cards"]} local model; {report["fallback_cards"]} labelled fallback')


if __name__ == '__main__':
    main()
