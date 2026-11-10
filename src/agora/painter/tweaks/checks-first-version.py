"""Independent success predicates, written before any ten-tweak agent runs.

These inspect computed pixels/DOM and authoritative facts. They neither supply
implementations nor reuse a component's own success/description claims.
"""
from datetime import datetime,timedelta,timezone
import json
import re
import time


def check(number,f,p,peer_page,answer,folder):
    tasks=f.door.rows('taskboard-task')
    by_id={t['id']:t for t in tasks}
    def js(expression):return p.js(expression)
    def cards(expression):return js('[...document.querySelectorAll(".card[data-task]")].map(n=>{const t='+json.dumps(by_id)+'[n.dataset.task];return '+expression+'})')
    def wait(condition,seconds=8):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            p.c.js('0')
            if condition():return True
            time.sleep(.08)
        return False
    if number==1:
        samples=cards('({priority:+t.priority,shadow:getComputedStyle(n).boxShadow})')
        def red_shadow(s):
            return any(int(a)>int(b)*1.3 and int(a)>int(c)*1.3 for a,b,c in re.findall(r'rgba?\((\d+),\s*(\d+),\s*(\d+)',s))
        return bool(samples) and all(red_shadow(s['shadow']) if s['priority']==1 else not red_shadow(s['shadow']) for s in samples)
    if number==2:
        values=cards('({due:t.due||"",chips:[...n.querySelectorAll("span,small,time,[data-part]")].filter(x=>x.textContent.trim()===(t.due||"MISSING")).map(x=>({text:x.textContent,colour:getComputedStyle(x).color,radius:getComputedStyle(x).borderRadius}))})')
        def red(colour):
            m=re.search(r'(\d+),\s*(\d+),\s*(\d+)',colour)
            return bool(m and int(m[1])>int(m[2])*1.3 and int(m[1])>int(m[3])*1.3)
        return all(any(red(c['colour'])==(v['due']<f.k.now().strftime('%Y-%m-%d')) and c['radius']!='0px' for c in v['chips']) for v in values if v['due']) and sum(bool(v['due']) for v in values)>0
    if number==3:
        return js('![...document.querySelectorAll(".lane")].some(n=>n.dataset.lane==="Done"&&n.getBoundingClientRect().width>0)') and peer_page.js('[...document.querySelectorAll(".lane")].some(n=>n.dataset.lane==="Done"&&n.getBoundingClientRect().width>0)') and any(t['lane']=='Done' for t in tasks)
    if number==4:
        values=cards('({pad:parseFloat(getComputedStyle(n).paddingTop),titles:[...n.querySelectorAll(".cardtitle,[data-part=title]")].map(x=>({clamp:getComputedStyle(x).webkitLineClamp,height:x.getBoundingClientRect().height,line:parseFloat(getComputedStyle(x).lineHeight)}))})')
        return bool(values) and all(v['pad']<16 and any(0<int(t['clamp'])<=2 and t['height']<=t['line']*2+1 for t in v['titles'] if t['clamp'].isdigit()) for v in values)
    if number==5:
        names=js('[...document.querySelectorAll(".lane")].filter(n=>n.getBoundingClientRect().width>0).map(n=>n.dataset.lane)')
        return names==['Backlog','Now','Waiting','Done'] and any(l.get('name')=='Waiting' for l in f.door.rows('taskboard-lane'))
    if number==6:
        values=cards('({who:t.who,avatars:[...n.querySelectorAll(".avatar,[data-part=avatar]")].map(x=>({text:x.textContent.trim(),radius:getComputedStyle(x).borderRadius,w:x.getBoundingClientRect().width,h:x.getBoundingClientRect().height}))})')
        return bool(values) and all(any(a['text']==''.join(x[0] for x in v['who'].split()).upper() and a['radius'] in ('50%','999px','9999px') and abs(a['w']-a['h'])<1 and 12<=a['w']<=40 for a in v['avatars']) for v in values)
    if number==7:
        task=next(t for t in tasks if t['lane']=='Now')
        # Observe actual animation objects during a streamed Done transition.
        js('globalThis.checkAnimations=[];globalThis.animationProbe=setInterval(()=>{for(const a of document.getAnimations({subtree:true})){const n=a.effect?.target;if(n&&(n.textContent.includes("✓")||n.textContent.includes("✔")||/check/i.test(n.getAttribute("aria-label")||"")))checkAnimations.push({state:a.playState,text:n.textContent})}},16)')
        f.door.say('look '+task['id']);f.door.say('task-move '+task['id']+' to=Done')
        ok=wait(lambda:bool(js('checkAnimations.length')),6)
        js('clearInterval(animationProbe)');return ok
    if number==8:
        labels=js('[...document.querySelectorAll(".lanehead")].map(n=>n.innerText)')
        peer_labels=peer_page.js('[...document.querySelectorAll(".lanehead")].map(n=>n.innerText)')
        js('document.querySelector(".cardtop button").click()')
        p.until('!!document.querySelector(".menu")')
        menu=js('document.querySelector(".menu").innerText')
        # Semantic Spanish labels, accepting common translations.
        return len(labels)==3 and any(re.search(r'pendient|por hacer|por empezar|atrasad',x,re.I) for x in labels) and any(re.search(r'curso|haciendo|ahora|progreso',x,re.I) for x in labels) and any(re.search(r'hech|complet|terminad|listo',x,re.I) for x in labels) and 'Backlog' in ' '.join(peer_labels) and bool(re.search(r'prioridad|urgente|alta',menu,re.I)) and bool(re.search(r'mover|mueve|mover a',menu,re.I)) and bool(re.search(r'eliminar|quitar|borrar',menu,re.I))
    if number==9:
        task=next(t for t in tasks if t['lane']=='Backlog');sel='[data-task="'+task['id']+'"]'
        js('document.querySelector('+json.dumps(sel+' .cardtop button')+').click()');p.until('!!document.querySelector(".menu")')
        found=js('(()=>{const b=[...document.querySelectorAll(".menu button")].find(n=>n.textContent.includes("Snooze until tomorrow"));if(!b)return false;b.click();return true})()')
        if not found:return False
        hidden=wait(lambda:not js('!!document.querySelector('+json.dumps(sel)+')'))
        preserved=any(t['id']==task['id'] for t in f.door.rows('taskboard-task'))
        future=f.k.now()+timedelta(days=1,seconds=1);f.k.clock=lambda:future
        p.set_clock(future)
        f.door.say('make kind=trial-tick text="tomorrow"')
        returned=wait(lambda:js('!!document.querySelector('+json.dumps(sel)+')'),8)
        return hidden and preserved and returned
    if number==10:
        # The fixture's actual record clock stamps are the independent ground
        # truth, not a writable changed_at hint or the agent's claimed count.
        expected=[]
        for task in tasks:
            if str(task.get('priority'))!='1' or task.get('lane')!='Now':continue
            entered=None
            for event in f.door.say('history '+task['id'])['rows']:
                for fact in event.get('facts',[]):
                    if fact.get('aspect')=='lane':
                        entered=event['at'] if fact.get('value')=='Now' else None
            if entered and f.k.now()-datetime.fromisoformat(entered.replace('Z','+00:00'))>timedelta(days=3):expected.append(task)
        actual=set(re.findall(r'\bdk\d+\b',answer))&set(by_id);wanted={t['id'] for t in expected}
        named={t['id'] for t in tasks if t.get('title','') in answer}
        return bool(expected) and (actual==wanted or named==wanted)
    raise ValueError(number)
