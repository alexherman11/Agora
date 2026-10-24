"""Read-only live verification and hidden picture; --open opens just the requested board at the end."""
import argparse
import asyncio
import json
import sys
import time

sys.dont_write_bytecode = True
from install import HERE, live_door, install, seed, open_board
from browser import Browser


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--open', action='store_true')
    args = ap.parse_args()
    door = live_door()
    before = door.request('/health')['records']
    made, skipped = install(door)
    added, source_count = seed(door)
    after = door.request('/health')['records']
    assert made == added == 0 and before == after, (made, added, before, after)
    print(f'Live repeat: {made} definitions changed, {added} tasks added, {after-before} records added', flush=True)
    tasks = door.rows('taskboard-task')
    assert len(tasks) == source_count
    counts = {lane: sum(t['lane'] == lane for t in tasks) for lane in ('Backlog', 'Now', 'Done')}
    print(f'Live seed: {len(tasks)} tasks · ' + ' · '.join(f'{k} {v}' for k, v in counts.items()), flush=True)
    browser = Browser()
    async def capture():
        try:
            page = await browser.page(door)
            await page.shot(HERE / 'evidence/live-board-headless.png')
            text = await page.js("document.querySelector('#paint').innerText")
            assert 'Task board' in text and tasks[0]['title'] in text and '$today' not in text
            print('Live hidden painter screenshot: passed', flush=True)
        finally:
            await browser.close()
    asyncio.run(capture())
    receipt = None
    if args.open:
        receipt = open_board(door)
        print(receipt, flush=True)
        for _ in range(40):
            listing = door.say('window.list')['rows']
            board = next((w for w in listing if w.get('name') == 'Task board' and w.get('shown')), None)
            if board:
                print('Live desktop: Task board shown', flush=True)
                break
            time.sleep(.5)
        else:
            board = None
            print('Live desktop: open recorded; actual shown state unconfirmed', flush=True)
    result = dict(tasks=len(tasks), lanes=counts, repeat=dict(definitions=made, tasks=added, records=after-before),
        word_names=[door.rows('word', bound='task-'+n)[0]['word'] for n in ('add', 'move', 'assign', 'done', 'note')],
        screenshot='live-board-headless.png', native_screenshot=False, window_open_receipt=receipt)
    if args.open:
        result['window_shown'] = board
    (HERE / 'evidence/live.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
