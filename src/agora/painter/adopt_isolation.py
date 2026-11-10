"""Explicit live adoption; preserves authored arrangements, task/history data,
and the window provider's on/off state. Never opens, raises or activates a view.
"""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
DESKTOP=HERE.parents[1]/'desktop/kernel-desktop'
sys.path[:0]=[str(HERE.parent),str(DESKTOP)]
from gaming_gate import reasons
from painter.install import taskboard,Q,activate,upsert
from painter.catalogue import cards


def gate():
    started=time.monotonic();attempt=0
    while True:
        found=reasons();record=dict(at=datetime.now(timezone.utc).isoformat(),attempt=attempt,reasons=found)
        print('SCREEN_GATE '+json.dumps(record),flush=True)
        if not found:return
        if time.monotonic()-started>=5400:raise RuntimeError('Screen gate remained closed for 90 minutes; adoption did not proceed')
        due=time.monotonic()+300
        while time.monotonic()<due:time.sleep(min(1,due-time.monotonic()))
        attempt+=1


def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def stored_rows(rows):
    # The previously resident kernel predates the repository's derived groups
    # column. This is read metadata, not a source fact on any task/window.
    return [{key:value for key,value in row.items() if key!='groups'} for row in rows]


def main():
    if '--live' not in sys.argv:raise SystemExit('Explicit --live is required')
    gate();d=taskboard.live_door()
    before=d.rows('taskboard-task')
    histories={t['id']:d.request('/see',dict(line='history '+t['id']))['rows'] for t in before}
    windows=d.rows('window');window_module=d.rows('module',name='window')[0]
    lenses={l['id']:l.get('text') for l in d.rows('lens') if l.get('painter')=='components'}
    result=dict(at=datetime.now(timezone.utc).isoformat(),task_count=len(before),before_hash=digest(before),window_provider_on=bool(window_module.get('on')))
    # A full restart is needed to adopt Python word implementations. This is
    # explicitly commissioned; each external step checks games AND fullscreen.
    (HERE/'evidence/isolation-live-before.json').write_text(json.dumps(dict(result,history_hashes={tid:digest(h) for tid,h in histories.items()},windows_hash=digest(stored_rows(windows))),indent=2),encoding='utf-8')
    if '--restart' in sys.argv or not d.request('/see',dict(line='help component-action')).get('ok'):
        for script in ('kdesk_off.py','kdesk_on.py'):
            gate()
            run=subprocess.run([sys.executable,str(DESKTOP/script)]+(['--wait'] if script=='kdesk_on.py' else []),capture_output=True,text=True,creationflags=0x08000000,timeout=75)
            print(run.stdout.strip(),flush=True)
            if run.returncode:raise RuntimeError(run.stderr)
        d=taskboard.live_door()
    for word in ('component-action','component-health','personal-view','personal-style'):
        if not d.request('/see',dict(line='help '+word)).get('ok'):raise RuntimeError('Live kernel is missing '+word)
    gate()
    # Existing world arrangements and personal preferences are not reinstallable
    # source templates. Update the runtime and first-party handles only.
    for card in cards():
        name=card.pop('name');old=d.rows('component',name=name)
        if not old:continue
        path=HERE.parent/'components'/f'{name}.js'
        code=(path if path.exists() else HERE.parent/'components/catalogue.js').read_text(encoding='utf-8')
        tid=upsert(d,'component',name,**card,code=code)
        now=d.rows('component',name=name)[0]
        if now.get('reviewed_code')!=hashlib.sha256(code.encode()).hexdigest():d.say('look '+tid);d.say('component '+tid)
    upsert(d,'guide','component-painter-guide',title='Component painter guide',text=(HERE/'ARRANGEMENT.md').read_text(encoding='utf-8'))
    for name in ('taskboard-components','component-gallery'):
        old=d.rows('widget',name=name)
        if old:activate(d,name,old[0].get('title') or name)
    from kernel.words import KERNEL_ENTRIES
    for name in ('component','look-view'):
        standard=next(e for e in KERNEL_ENTRIES if e['word']==name)
        for entry in d.rows('word',bound=name):
            if entry.get('from')!='kernel':continue
            d.say('look '+entry['id']);d.say('word-set '+entry['id']+' help='+Q(standard['help']))
    after=d.rows('taskboard-task')
    result['tasks_unchanged']=stored_rows(before)==stored_rows(after)
    result['histories_unchanged']=all(d.request('/see',dict(line='history '+tid))['rows']==history for tid,history in histories.items())
    result['arrangements_unchanged']=all(next(l for l in d.rows('lens') if l['id']==tid).get('text')==text for tid,text in lenses.items())
    result['saved_windows_unchanged']=stored_rows(d.rows('window'))==stored_rows(windows)
    result['window_provider_state_preserved']=bool(d.rows('module',name='window')[0].get('on'))==bool(window_module.get('on'))
    result['after_hash']=digest(after)
    result['prior_resident_task_hash']='1bcedb871a6d230d42cce35f56ad8281acf8fc12be242c4bd22cfaacfdf955dd'
    result['exact_prior_hash_without_derived_groups']=digest(stored_rows(after))==result['prior_resident_task_hash']
    reading=d.request('/see',dict(line='look-view taskboard-components'))
    result['live_compact_reading']=reading.get('ok') and 'tree' not in reading['rows'][0]
    result['counts']=reading['rows'][0]['counts'] if reading.get('ok') else {}
    result['widget_source_hash']=hashlib.sha256(d.rows('widget',name='taskboard-components')[0]['code'].encode()).hexdigest()
    (HERE/'evidence/isolation-live.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    assert all(result[key] for key in ('tasks_unchanged','histories_unchanged','arrangements_unchanged','saved_windows_unchanged','window_provider_state_preserved','live_compact_reading')),result
    # A short, reversible world note records the source gap without touching
    # Conversation or sending any message as Alex.
    gate();upsert(d,'note','painter-isolation-rough-spots',title='Rough spots · Component isolation',
                 text='Builder implementation for Claude review: component-health/action, private reports, personal-view/style, validated styles, compact look-view, display formatting and motion handles. Native WebView2 sibling frames share a renderer; Worker quarantine and verified native renderer recovery are required. Measurements and limits: src/agora/painter/ISOLATION.md. Authored component arrangements, task facts/histories and the window provider state were preserved. No git state changed.')
    (HERE/'evidence/isolation-live.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('LIVE_ISOLATION '+json.dumps(result),flush=True)


if __name__=='__main__':main()
