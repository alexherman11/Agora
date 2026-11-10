"""Focused hidden selection diagnosis using the real proof world/driver."""
from ui_proof import UI
import json

ui=UI()
ui.metrics['first_paint_upper_bound_ms']=0
try:
    p=ui.page();post=ui.examples['document'];ui.navigate(p,thread=post['id'],replyTo=post['id'])
    file=next(f for f in ui.d.rows('file') if f.get('name')=='planning.pdf')
    selector='.nb-thread [data-fact-id='+file['id']+'] .nb-page'
    ui.wait(p,'!!document.querySelector('+json.dumps(selector)+')');ui.drag_text(p,selector)
    print('SELECTED '+str(p.js('getSelection().toString()')),flush=True)
    print('CONTROLS '+str(p.js('[...document.querySelectorAll(".nb-thread .selection-action")].map(b=>({text:b.textContent,hidden:b.hidden,rect:b.getBoundingClientRect().toJSON()}))')),flush=True)
    ui.button(p,'Quote selection','document.querySelector(".nb-thread [data-fact-id='+file['id']+']")')
    ui.wait(p,'JSON.parse(document.querySelector(".nb-shell").dataset.view).source==='+json.dumps(file['id']))
    print('POLISH QUOTE: selected page reached the reply form; hidden=True',flush=True)
finally:ui.close()
