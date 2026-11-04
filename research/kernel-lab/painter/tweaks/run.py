"""Twenty independent fresh-agent trials over one frozen scratch log snapshot."""
from datetime import datetime
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

HERE=Path(__file__).resolve().parent;LAB=HERE.parents[1];sys.path.insert(0,str(LAB))
from kernel import scratch
from painter.freeze import verify,FROZEN
from painter.install import taskboard,Q
from painter.fresh_agent import run as fresh,ROOT
from painter.browser import Page
from painter.tweaks.checks import check
from test_kdesk import Desk
import kdesk


class Copy:
    def __init__(self):
        archived=FROZEN.parent/'frozen-source'
        manifest=verify(source_root=archived) if archived.exists() else verify()
        # Replays use the exact inline JS in the saved world. The Python
        # compiler must still match; a later painter JS repair is not imported.
        compiler='research/kernel-lab/painter/arrangement.py'
        assert hashlib.sha256((ROOT/compiler).read_bytes()).hexdigest()==manifest['sha256'][compiler]
        self.d=Desk.__new__(Desk);self.d.dir=scratch.mkdtemp(prefix='painter-tweak-')
        world=Path(self.d.dir)/'world';shutil.copytree(FROZEN,world)
        self.d.k,self.d.srv,self.d.host,self.d.entry=kdesk.start(world,0,headless=True)
        self.d.url=f'http://127.0.0.1:{self.d.srv.server_address[1]}'
        self.k=self.d.k;self.url=self.d.url;self.token=self.d.entry.token('alex');self.peer=self.d.entry.token('peer')
        self.door=taskboard.Door(self.url,self.token);self.tasks=manifest['tasks'];self.ids=manifest['ids'];self.js=manifest['js']
        now=datetime.fromisoformat(manifest['at']);self.k.clock=lambda:now
        self.d.wait(lambda:'summarize.save' in self.door.say('help')['text'])
        assert self.door.rows('taskboard-task')==manifest['task_facts'],'Scratch task facts differ from frozen snapshot'

    def close(self):self.d.close()


def changes(before,after):
    result=[]
    for tid in set(before)|set(after):
        a,b=before.get(tid,{}),after.get(tid,{})
        for field in set(a)|set(b):
            if a.get(field)==b.get(field):continue
            kind=b.get('kind',a.get('kind'))
            category='style' if kind=='part-style' else 'lens' if kind in ('lens','view-preference') else 'component code' if kind=='component' and field=='code' else 'source' if kind=='widget' and field=='code' else 'facts'
            diff=list(difflib.ndiff(str(a.get(field,'')).splitlines(),str(b.get(field,'')).splitlines()))
            lines=sum(x.startswith(('+ ','- ')) for x in diff)
            result.append(dict(thing=tid,kind=kind,field=field,category=category,lines=lines))
    return sorted(result,key=lambda x:(x['category'],x['thing'],x['field']))


def regression(f,p,mid,folder):
    """Repeat realistic board actions after each change; expected layout can vary.

    Preserves the original proof's behaviour expectations (real quick-add, menu,
    priority keyboard, spring pointer drop, stale competing drop, editing, colour,
    history, remove/undo). Full 25-card/layout and catalogue assertions live in
    painter/proof.py and are run on the frozen baseline separately.
    """
    checks=[];q=None
    def record(name,fn):
        try:ok=bool(fn());detail=''
        except Exception as exc:ok=False;detail=str(exc)[:500]
        checks.append(dict(check=name,ok=ok,detail=detail));return ok
    def wait(cond):
        return f.d.wait(lambda:([x.c.js('0') for x in (p,q) if x],cond())[1],12)
    try:
        visible=p.js('[...document.querySelectorAll(".card[data-task]")].map(n=>n.dataset.task)')
        if not visible:return [dict(check='Board still has readable cards',ok=False)]
        task=visible[0];sel='[data-task="'+task+'"]'
        record('Cards still show their authoritative titles',lambda:p.js('[...document.querySelectorAll(".card[data-task]")].some(n=>n.textContent.includes('+json.dumps(f.k.state.get(task,'short') or f.k.state.get(task,'title'))+'))'))
        p.js('document.querySelector('+json.dumps(sel)+').focus()')
        p.c.call('Input.dispatchKeyEvent',type='keyDown',key='3',code='Digit3',windowsVirtualKeyCode=51)
        record('Focused-card priority shortcut writes the fact',lambda:wait(lambda:str(f.k.state.get(task,'priority'))=='3'))
        p.until('!!document.querySelector('+json.dumps(sel)+')')
        p.js('document.querySelector('+json.dumps(sel+' .cardtop button')+').click()')
        record('Card menu remains available with its action set',lambda:(p.until('!!document.querySelector(".menu")'),p.js('document.querySelectorAll(".menu button").length>=15'))[1])
        p.js('document.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape",bubbles:true}))')
        p.js('document.querySelector('+json.dumps(sel)+').dispatchEvent(new MouseEvent("dblclick",{bubbles:true}))')
        p.until('!!document.querySelector(".drawer")')
        record('Detail drawer reads real history',lambda:(p.until('document.querySelector(".history").innerText.length>0'),bool(p.js('document.querySelector(".history").innerText.match(/2026-/)')))[1])
        note='## Shared notes\n\nWelcome every neighbour.\n- [ ] Bring tea'
        p.js('(()=>{const n=document.querySelector("[aria-label=Notes]");n.value='+json.dumps(note)+';n.focus();n.dispatchEvent(new KeyboardEvent("keydown",{key:"s",ctrlKey:true,bubbles:true}))})()')
        record('Multiline Markdown saves to authoritative facts',lambda:wait(lambda:f.k.state.get(task,'note')==note))
        p.js('document.querySelector(".drawerhead button").click()')
        # Source and receiver stay visible while two real pointers compete.
        p.until('!!document.querySelector('+json.dumps(sel)+')')
        q=Page(f.url,f.token,mid,clock=f.k.now());q.until('!!document.querySelector('+json.dumps(sel)+')')
        lanes=p.js('[...document.querySelectorAll(".lane")].map(n=>n.dataset.lane)');old=f.k.state.get(task,'lane')
        target=next((l for l in lanes if l!=old),None)
        if target:
            dest='[data-lane="'+target+'"]';a=p.start_drag(sel,dest);b=q.start_drag(sel,dest)
            record('Pointer drag keeps the spring ghost',lambda:p.js('!!document.querySelector(".dragging")'))
            p.release(a);record('Pointer drop writes the task-move fact',lambda:wait(lambda:f.k.state.get(task,'lane')==target))
            q.release(b)
            record('Competing stale pointer refuses',lambda:(q.until('document.body.innerText.includes("stale")'),f.k.state.get(task,'lane')==target)[1])
        before=len(f.door.rows('taskboard-task'))
        p.js('document.querySelector("input").focus()')
        p.c.call('Input.insertText',text='Proof a new shared task p2');p.c.call('Input.dispatchKeyEvent',type='keyDown',key='Enter',code='Enter',windowsVirtualKeyCode=13)
        record('Native quick-add preserves priority and description',lambda:wait(lambda:len(f.door.rows('taskboard-task'))==before+1) and any(t.get('title')=='Proof a new shared task' and str(t.get('priority'))=='2' for t in f.door.rows('taskboard-task')))
        added=next((t for t in f.door.rows('taskboard-task') if t.get('title')=='Proof a new shared task'),None)
        if added:
            f.door.say('look '+added['id']);f.door.say('task-remove '+added['id'])
            record('Removal forgets the card',lambda:not any(t['id']==added['id'] for t in f.door.rows('taskboard-task')))
            f.door.say('undo')
            record('Undo restores card and record trail',lambda:any(t['id']==added['id'] for t in f.door.rows('taskboard-task')) and any(r['word']=='undo' for r in f.door.say('history '+added['id'])['rows']))
    except Exception as exc:checks.append(dict(check='Board proof completed',ok=False,detail=str(exc)[:700]))
    finally:
        if q:q.close()
    (folder/'board-proof.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    return checks


def one(board,number,request):
    verify();folder=HERE/'runs'/f'{board}-{number:02}';folder.mkdir(parents=True,exist_ok=True)
    if (folder/'result.json').exists():return json.loads((folder/'result.json').read_text(encoding='utf-8'))
    f=Copy();pages=[];started=time.monotonic()
    try:
        before=json.loads(json.dumps(f.k.state.things));mid=f.ids['taskboard-components'] if board=='A' else f.js
        name='taskboard-components' if board=='A' else 'taskboard-js'
        result=fresh(f,'Target board: '+name+'. Change only this board definition/its supporting pieces; the shared task and lane facts remain shared.\n'
                     'Request (exactly as commissioned): "'+request+'"\n'
                     'Act now, or answer the reading question. Say clearly if you must edit code.',folder)
        after=json.loads(json.dumps(f.k.state.things));delta=changes(before,after)
        result.update(board=board,number=number,request=request,changes=delta,lines=sum(x['lines'] for x in delta),
                      landed=sorted({x['category'] for x in delta}) or ['reading'],success=False,board_proof=False)
        try:
            p=Page(f.url,f.token,mid,clock=f.k.now());pages.append(p)
            p.until('!!document.querySelector(".card[data-task]")')
            peer=Page(f.url,f.peer,mid,clock=f.k.now());pages.append(peer);peer.until('!!document.querySelector(".card[data-task]")')
            p.shot(folder/'screenshot.png')
            try:result['success']=bool(check(number,f,p,peer,result['answer'],folder))
            except Exception as exc:result['check_error']=str(exc)[:1200]
            print(f'{board}{number:02} {"PASS" if result["success"] else "FAIL"} tweak check',flush=True)
            # Close overlays opened by a check before the independent board proof.
            p.js('document.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape",bubbles:true}))')
            proof=regression(f,p,mid,folder);result['board_proof']=all(c['ok'] for c in proof)
            result['proof_passed']=sum(c['ok'] for c in proof);result['proof_checks']=len(proof)
        except Exception as exc:result['render_error']=str(exc)[:1500]
        result['wall_seconds']=round(time.monotonic()-started,2)
        (folder/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(f'{board}{number:02} {"PASS" if result["success"] else "FAIL"} · {result["seconds"]}s agent · {result["lines"]} lines · {result["landed"]} · board proof {result.get("proof_passed",0)}/{result.get("proof_checks",0)}',flush=True)
        return result
    finally:
        for p in pages:p.close()
        f.close()


def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--boards',default='AB');ap.add_argument('--numbers',default=','.join(str(n) for n in range(1,11)));args=ap.parse_args()
    requests=json.loads((HERE/'requests.json').read_text(encoding='utf-8'));results=[]
    for number in [int(x) for x in args.numbers.split(',')]:
        for board in args.boards:
            if (HERE/'runs/STOP').exists():print('Stopped between isolated trials.',flush=True);return
            results.append(one(board,number,requests[number-1]))
    (HERE/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(f'{sum(r["success"] for r in results)} of {len(results)} tweak checks passed',flush=True)


if __name__=='__main__':main()
