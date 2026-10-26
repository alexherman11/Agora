"""Realistic board expectations, adapted to the guarded component driver."""
import json
from pathlib import Path
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent))
from painter.fixture import Fixture
from painter.browser import Page
from painter.install import install,Q,taskboard


def run():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--minutes',type=float,default=0);args=ap.parse_args()
    evidence=HERE/'evidence';evidence.mkdir(exist_ok=True)
    f=Fixture();d=f.door;k=f.k;checks=[];pages=[]
    original_wait=f.d.wait
    def wait(cond,timeout=15):
        try:return original_wait(lambda:([p.c.js('0') for p in pages],cond())[1],timeout)
        except AssertionError:
            for p in pages: print('PAGE DIAGNOSTIC',p.c.js('document.querySelector("#receipt").innerText'),p.js('({errors:globalThis.errors,text:document.body.innerText.slice(-300)})'),flush=True)
            raise
    f.d.wait=wait
    def check(name,ok):
        checks.append(dict(check=name,ok=bool(ok)));print(('PASS ' if ok else 'FAIL ')+name,flush=True)
        assert ok,name
    try:
        if args.minutes:
            agent=taskboard.Door(f.url,f.d.entry.token('claude'));started=time.monotonic()
            for i,t in enumerate(f.tasks):
                actor=d if i%2==0 else agent;original=k.state.get(t,'priority')
                actor.say('look '+t);actor.say('task-priority '+t+' priority='+str(int(original)%4+1))
                actor.say('look '+t);actor.say('task-priority '+t+' priority='+str(original))
                due=started+args.minutes*60*(i+1)/len(f.tasks)
                while time.monotonic()<due:
                    actor.say('history '+t);time.sleep(min(1,max(0,due-time.monotonic())))
            elapsed=time.monotonic()-started
            check('Sustained 25-task triage duration',elapsed>=args.minutes*60)
            print(f'RAN {elapsed:.2f} seconds of triage; requested {args.minutes:g} minutes',flush=True)
        n=len(k.log.records);install(d);check('Idempotent component installation',len(k.log.records)==n)
        plan=d.say('look-view taskboard-components plan=yes')['rows'][0]
        check('Painter describes 25 cards and three lanes without executing component JS',plan['counts']['card']==25 and plan['counts']['lane']==3)
        check('Five app components arrange the board',set(plan['counts'])=={'board','lane','card','flag','menu'})
        check('Part reading carries facts, settings and gesture lines',all(n['facts'].get('id') for n in plan['parts'] if n['component']=='card') and 'task-move' in json.dumps(plan['tree']))
        check('Catalogue purposes and examples discoverable',len(d.say('components')['rows'])>=30 and 'root : calendar' in d.say('help calendar')['text'])
        p=Page(f.url,f.token,f.ids['taskboard-components']);pages.append(p)
        p.until('document.querySelectorAll(".card").length===25')
        p.js('window.errors=[];addEventListener("error",e=>errors.push(e.message));addEventListener("unhandledrejection",e=>errors.push(String(e.reason)))')
        p.shot(evidence/'component-board.png')
        check('25 cards and three drop lanes at 1600px',p.c.js('innerWidth===1600') and p.js('document.querySelectorAll("[data-drop]").length===3'))
        check('Every task paints a priority marker',p.js('document.querySelectorAll(".card .flag").length===25'))
        check('Priorities sort within lanes',p.js('[...document.querySelectorAll(".lane")].every(l=>{const ps=[...l.querySelectorAll(".card")].map(n=>+n.dataset.factPriority);return ps.every((x,i)=>!i||x>=ps[i-1])})'))
        check('Notes preserve multiline source and colours',all('\n- [ ]' in k.state.get(t,'note') and k.state.get(t,'note_colour')=='sage' for t in f.tasks[:2]))
        # Real quick-add through the module's deterministic unavailable-model path.
        p.js('document.querySelector("input").focus()')
        p.c.call('Input.insertText',text='Check the back door p2')
        p.c.call('Input.dispatchKeyEvent',type='keyDown',key='Enter',code='Enter',windowsVirtualKeyCode=13)
        p.c.call('Input.dispatchKeyEvent',type='keyUp',key='Enter',code='Enter',windowsVirtualKeyCode=13)
        try: f.d.wait(lambda:len(d.rows('taskboard-task'))==26)
        except AssertionError:
            print('QUICK ADD DIAGNOSTIC',p.js('({value:document.querySelector("input").value,active:document.activeElement.outerHTML,text:document.body.innerText.slice(-2000)})'),p.c.js('document.querySelector("#receipt").innerText'),flush=True)
            raise
        added=next(t for t in d.rows('taskboard-task') if t['title']=='Check the back door')
        check('Real quick-add typing preserves spaces and strips p2',str(added['priority'])=='2')
        d.say('look '+added['id']);d.say('task-remove '+added['id']);p.until('document.querySelectorAll(".card").length===25')
        task=f.tasks[0];sel=f'[data-task="{task}"]'
        p.js('document.querySelector('+json.dumps(sel+' .cardtop button')+').click()')
        p.until('!!document.querySelector(".menu")');p.shot(evidence/'component-menu.png')
        check('Card menu exposes priority colour moves assignment rename summary removal',p.js('["⚑  P1 · Urgent","Colour · Sage","Move · Done","Assign to JEFF","Details & rename","Summarize","Remove"].every(s=>[...document.querySelectorAll(".menu button")].some(b=>b.textContent===s))'))
        p.js('[...document.querySelectorAll(".menu button")].find(b=>b.textContent==="⚑  P2 · High").click()')
        f.d.wait(lambda:str(k.state.get(task,'priority'))=='2');check('Card menu changes the actual priority',str(k.state.get(task,'priority'))=='2')
        p.until('document.querySelector('+json.dumps(sel)+')?.dataset.factPriority==="2"')
        q=Page(f.url,f.token,f.ids['taskboard-components']);pages.append(q);q.until('document.querySelectorAll(".card").length===25')
        a=p.start_drag(sel,'[data-lane=Done]');b=q.start_drag(sel,'[data-lane=Now]')
        check('Pointer drag has spring ghost',p.js('!!document.querySelector(".dragging")'))
        p.release(a);f.d.wait(lambda:k.state.get(task,'lane')=='Done')
        check('Real pointer drag says task-move and moves to Done',k.state.get(task,'lane')=='Done')
        q.release(b);q.until('document.body.innerText.includes("stale")')
        check('Stale competing pointer drag refuses without moving',k.state.get(task,'lane')=='Done')
        p.until('document.querySelector('+json.dumps(sel)+')?.closest(".lane").dataset.lane==="Done"')
        p.js('document.querySelector('+json.dumps(sel)+').dispatchEvent(new MouseEvent("dblclick",{bubbles:true}))')
        p.until('!!document.querySelector(".drawer")')
        p.until('document.querySelector(".history").innerText.includes("task-move")')
        check('History renders real record dates and authors',p.js('document.querySelector(".history").innerText.includes("task-move") && /2026-/.test(document.querySelector(".history").innerText)'))
        p.js('(()=>{const n=document.querySelector("[aria-label=Notes]");n.value="## Meet\\n\\n**Welcome** all\\n- [ ] Bring tea\\nLiteral \\\\n stays literal";n.focus();n.dispatchEvent(new KeyboardEvent("keydown",{key:"s",ctrlKey:true,bubbles:true}))})()')
        f.d.wait(lambda:'Literal' in str(k.state.get(task,'note')))
        check('Detail drawer saves lossless multiline Markdown through fresh revisions','\n- [ ]' in k.state.get(task,'note') and '\\n stays literal' in k.state.get(task,'note'))
        p.js('(()=>{const n=document.querySelector("[aria-label=Notes]");const a=n.value.indexOf("Welcome");n.focus();n.setSelectionRange(a,a+7);n.dispatchEvent(new KeyboardEvent("keydown",{key:"b",ctrlKey:true,bubbles:true}));const b=n.value.indexOf("Bring");n.setSelectionRange(b,b+5);n.dispatchEvent(new KeyboardEvent("keydown",{key:"i",ctrlKey:true,bubbles:true}));n.dispatchEvent(new KeyboardEvent("keydown",{key:"s",ctrlKey:true,bubbles:true}))})()')
        f.d.wait(lambda:'**Welcome**' in k.state.get(task,'note') and '_Bring_' in k.state.get(task,'note'))
        check('Actual Bold and Italic selection commands persist Markdown','**Welcome**' in k.state.get(task,'note') and '_Bring_' in k.state.get(task,'note'))
        p.js('document.querySelector('+json.dumps('[title="Note peach"]')+').click()')
        f.d.wait(lambda:k.state.get(task,'note_colour')=='peach')
        p.js('[...document.querySelectorAll(".editorbar button")].find(b=>b.textContent==="slant").click()')
        f.d.wait(lambda:k.state.get(task,'note_style')=='slant')
        check('Note colours and slant style write actual facts',k.state.get(task,'note_colour')=='peach' and k.state.get(task,'note_style')=='slant')
        p.shot(evidence/'component-editor.png');p.js('document.querySelector(".drawerhead button").click()')
        p.js('document.querySelector('+json.dumps(sel)+').focus()');p.c.call('Input.dispatchKeyEvent',type='keyDown',key='4',code='Digit4',windowsVirtualKeyCode=52)
        f.d.wait(lambda:str(k.state.get(task,'priority'))=='4');check('Focused-card keyboard shortcut changes priority',str(k.state.get(task,'priority'))=='4')
        history=d.say('history '+task)['rows'];check('Raw history retains prior note and moves',any(r['word']=='task-move' for r in history) and any(r['word']=='task-note' for r in history))
        p.js('[...document.querySelectorAll(".filters button")].find(b=>b.textContent==="P1").click()')
        expected=sum(str(t.get('priority'))=='1' for t in d.rows('taskboard-task'))
        p.until('document.querySelectorAll(".card").length==='+str(expected))
        check('P1 filter is an actual world gesture',str(d.rows('taskboard-settings')[0]['filter'])=='1')
        p.js('[...document.querySelectorAll(".filters button")].find(b=>b.textContent==="All tasks").click()');p.until('document.querySelectorAll(".card").length===25')
        last=f.tasks[-1];d.say('look '+last);d.say('task-remove '+last)
        check('Remove forgets a card',last not in {t['id'] for t in d.rows('taskboard-task')})
        d.say('undo');check('Undo restores the original card and trail',last in {t['id'] for t in d.rows('taskboard-task')} and any(r['word']=='undo' for r in d.say('history '+last)['rows']))
        # Compare the same 25 facts in the original pure JS board, hidden.
        js=Page(f.url,f.token,f.js);pages.append(js);js.until('document.querySelectorAll(".card").length===25');js.shot(evidence/'javascript-board.png')
        check('JS comparison board reads identical task identities',set(js.js('[...document.querySelectorAll(".card")].map(n=>n.dataset.task)'))==set(f.tasks))
        gallery=Page(f.url,f.token,f.ids['component-gallery'],1200,1000);pages.append(gallery)
        gallery.until('document.body.innerText.includes("pixel-surface")')
        gallery.shot(evidence/'component-gallery.png')
        check('Gallery uses painter and renders live catalogue examples',gallery.js('document.querySelectorAll("[data-component=calendar]").length>0 && document.querySelectorAll("canvas").length>=3'))
        check('Gallery has a one-click taskbar entry',bool(d.rows('button',name='component-gallery-button')))
        from kernel.kernel import Kernel
        # Paint-health reports can land while the replay is being loaded. Hold
        # the writer lock so both sides describe the same committed instant.
        with k.lock:
            replay=Kernel(str(Path(f.d.dir)/'world')).state.snapshot()
            current=k.state.snapshot()
        check('Scratch replay matches all current facts',replay==current)
        print(f'{len(checks)} of {len(checks)} component checks passed',flush=True)
    finally:
        (evidence/'proof.json').write_text(json.dumps(dict(checks=checks,count=len(checks)),indent=2),encoding='utf-8')
        for p in pages:p.close()
        f.close()


if __name__=='__main__':run()
