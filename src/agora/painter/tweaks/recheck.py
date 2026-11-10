"""Replay the original agent's exact word calls; never retry the agent.

Used only to correct a checker/driver bug. Old results remain alongside rechecks.
Frozen painter/component bytes and the agent's chosen changes stay identical.
"""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from painter.tweaks.run import Copy,regression
from painter.tweaks.checks import check
from painter.browser import Page
from painter.install import taskboard


def run(board,number):
    folder=Path(__file__).resolve().parent/'runs'/f'{board}-{number:02}'
    original=json.loads((folder/'result.json').read_text(encoding='utf-8'));f=Copy();pages=[]
    try:
        actor=taskboard.Door(f.url,f.d.entry.token('claude'));calls=[]
        for raw in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines():
            e=json.loads(raw);item=e.get('item',{})
            if e.get('type')!='item.completed' or item.get('type')!='mcp_tool_call' or item.get('status')!='completed':continue
            tool=item.get('tool');line=item.get('arguments',{}).get('line')
            if tool not in ('do','see') or not line:continue
            out=actor.request('/'+tool,dict(line=line));calls.append(dict(tool=tool,ok=out.get('ok')))
        mid=f.ids['taskboard-components'] if board=='A' else f.js
        p=Page(f.url,f.token,mid,clock=f.k.now());pages.append(p);p.until('!!document.querySelector(".card")')
        peer=Page(f.url,f.peer,mid,clock=f.k.now());pages.append(peer);peer.until('!!document.querySelector(".card")')
        success=bool(check(number,f,p,peer,original['answer'],folder))
        p.shot(folder/'rechecked-screenshot.png')
        reason={2:'Checker accepts an Overdue label and red chip background.',5:'Checker requires a real functional Waiting drop in order, rather than a particular lane storage representation.',10:'Checker distinguishes explicit exclusions from the tasks listed as qualifying.'}.get(number,'Checker diagnostic replay.')
        result=dict(success=success,reason=reason+' Exact original word calls replayed, no new agent or implementation edits.',replayed_calls=len(calls))
        (folder/'recheck.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(board,number,'PASS' if success else 'FAIL',result,flush=True)
    finally:
        for p in pages:p.close()
        f.close()


if __name__=='__main__':run(sys.argv[1],int(sys.argv[2]))
