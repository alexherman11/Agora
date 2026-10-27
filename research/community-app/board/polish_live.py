"""Gated polish adoption. Hidden; no board window or imagined content."""
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from ui_live import Gate, GatedDoor, protected, digest, taskboard, DESKTOP, HERE
from ui_install import install_ui

OUT=HERE/'evidence/ui/polish'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    gate=Gate();gate('inspect live polish target')
    door=taskboard.live_door();before=protected(door)
    modules=[dict(name=m['name'],on=m.get('on')) for m in door.rows('module')]
    status=dict(at=datetime.now(timezone.utc).isoformat(),tasks=len(before['tasks']),windows=len(before['windows']),modules=modules,feed_posts=len(door.request('/see',dict(line='board.feed'))['rows']),opened=False)
    print('POLISH LIVE INSPECT '+json.dumps(status,sort_keys=True),flush=True)
    if not args.live:return
    if before['window_on']:
        raise RuntimeError('Window provider is active; refusing a runtime restart that could show windows. Component adoption remains pending.')
    if status['feed_posts']:
        raise RuntimeError('Live board is no longer empty; inspect with coordinator before changing its installed definitions.')
    (OUT/'live-before.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
    for name in ['kdesk_off.py','kdesk_on.py']:
        gate('adopt polish runtime: '+name)
        result=subprocess.run([sys.executable,'-B',str(DESKTOP/name)]+(['--wait'] if name=='kdesk_on.py' else []),capture_output=True,text=True,creationflags=0x08000000)
        print(result.stdout.strip(),flush=True)
        if result.returncode:raise RuntimeError(result.stderr)
    door=GatedDoor(taskboard.live_door(),gate)
    ids=install_ui(door)
    after=protected(door)
    assert before==after,'Protected tasks/history/window facts/provider changed'
    assert not door.see('board.feed')['rows']
    # A structural projection proves the running compiler adopted format and
    # viewer metadata, without constructing or opening a native window.
    projection=door.see('look-view '+ids['lens']+' plan=yes')['rows'][0]
    assert projection['tree']['viewer']['id'],'Running compiler has no viewer metadata'
    assert not projection['style_errors'],projection['style_errors']
    assert not any(p['health']['health']=='stopped' for p in projection['parts']),projection['parts']
    widget=door.rows('widget',name='seabright-board')[0]
    from ui_install import widget_source
    assert widget['code']==widget_source()
    assert door.rows('component',name='date-tile')
    evidence=dict(at=datetime.now(timezone.utc).isoformat(),**ids,opened=False,posts_seeded=0,feed_posts=0,tasks_preserved=len(before['tasks']),histories_preserved=True,windows_preserved=len(before['windows']),provider_on=after['window_on'],protected_sha256=digest(before),widget_source_matches=True,projection_read=True)
    (OUT/'live-install.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print('POLISH LIVE '+json.dumps(evidence,sort_keys=True),flush=True)


if __name__=='__main__':main()
