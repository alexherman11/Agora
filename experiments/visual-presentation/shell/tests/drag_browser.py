"""Browser regression tests for the retained shell (simulated parent bridge).
Run: python tests/drag_browser.py [path/to/index.html]
Requires Playwright and its Chromium. Does not write to a live Agora world.
"""
import asyncio, json, pathlib, sys
from playwright.async_api import async_playwright

HTML = pathlib.Path(sys.argv[1] if len(sys.argv)>1 else pathlib.Path(__file__).parents[1]/'index.html').read_text()
BRIDGE = r"""<!doctype html><style>body{margin:0}iframe{width:100vw;height:100vh;border:0}</style>
<script>
const copy=x=>JSON.parse(JSON.stringify(x));
window.objects = {
 n:{id:'n',revision:1,facets:{'core.title':{text:'A title to edit'},'core.text':{text:'Keep this note body'},'core.appearance':{scene:'desk',x:20,y:20,width:245,height:205}}},
 'shell.chat-draft':{id:'shell.chat-draft',revision:1,facets:{'core.text':{text:'Existing unsent draft'},'core.draft':{conversation:'main'}}}
};
window.requests=[]; window.replies=[]; window.delayMove=0; window.delayText=0; window.refuse=false;
window.addEventListener('message',async event=>{
 const d=event.data;if(!d.agora)return;
 if(d.event){replies.push(d);return;}
 requests.push(copy(d));
 let result,error;
 try {
  if(d.method==='world.query') result={items:[copy(objects.n)],complete:true};
  else if(d.method==='world.get') {if(!objects[d.args.id])throw Error('not found');result=copy(objects[d.args.id]);}
  else if(d.method==='world.transact'){
   const moving=d.args.changes.some(c=>c.facets['core.appearance']);
   await new Promise(r=>setTimeout(r,moving?delayMove:delayText));
   if(moving&&refuse)throw Error('Write refused for test');
   for(const c of d.args.changes)if((objects[c.id]?.revision||0)!==c.expected_revision)throw Error('Stale revision');
   result={items:d.args.changes.map(c=>{
    const obj=objects[c.id]={id:c.id,revision:(objects[c.id]?.revision||0)+1,facets:{...objects[c.id]?.facets,...c.facets}};
    return copy(obj);
   })};
  }
  else if(d.method==='chat.status')result={running:false,messages:[{id:'m',role:'assistant',text:'Existing conversation'}]};
  else if(d.method==='system.status')result={signed_in:true};
  else result={};
 }catch(e){error=e.message;}
 event.source.postMessage({agora:true,id:d.id,result,error},'*');
});
</script><iframe src="/shell"></iframe>"""

async def main():
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True,args=['--no-sandbox'])
  errors=[]
  async def setup(width=1400):
   page=await browser.new_page(viewport={'width':width,'height':900},has_touch=True)
   page.on('pageerror',lambda e:errors.append(str(e)))
   await page.route('http://localhost/**',lambda r:r.fulfill(content_type='text/html',body=HTML if r.request.url.endswith('/shell') else BRIDGE))
   await page.goto('http://localhost/')
   frame=page.frames[1]
   await frame.wait_for_selector('.note')
   await frame.wait_for_function('state.draftLoaded && state.connected')
   return page,frame
  async def xy(f):
   return await f.locator('.note').evaluate('(n)=>[parseFloat(n.style.left),parseFloat(n.style.top)]')
  async def start(p,f,dx=60,dy=40):
   box=await f.locator('.note-header').bounding_box()
   x,y=box['x']+32,box['y']+6
   await p.mouse.move(x,y);await p.mouse.down();await p.mouse.move(x+dx,y+dy,steps=5)
   return x,y
  async def settle(f):
   await f.wait_for_function('[...state.notes.values()].every(e=>!e.positionPromise && !e.savePromise)')
  async def moves(p):
   return await p.evaluate("requests.filter(r=>r.method==='world.transact'&&r.args.changes[0].facets['core.appearance'])")
  def passed(name):print('PASS '+name,flush=True)

  p,f=await setup()
  await f.locator('#chat-input').focus()
  await f.locator('#chat-input').evaluate('(e)=>e.setSelectionRange(2,8)')
  await start(p,f)
  assert await xy(f)==[80,60],await xy(f)
  assert await f.locator('#chat-input').evaluate('(e)=>document.activeElement===e && e.selectionStart===2 && e.selectionEnd===8')
  assert len(await moves(p))==0
  await p.mouse.up();await settle(f)
  assert await p.evaluate("objects.n.facets['core.appearance']")==dict(scene='desk',x=80,y=60,width=245,height=205)
  req=(await moves(p))[0]['args']['changes'][0]
  assert req['expected_revision']==1 and list(req['facets'])==['core.appearance']
  assert await f.locator('#chat-input').input_value()=='Existing unsent draft'
  assert await f.locator('.message-content').inner_text()=='Existing conversation'
  passed('pointer preview, one native-shaped CAS write, focus/selection/chat/draft preserved')
  await p.close()

  p,f=await setup()
  await f.locator('.note-title').click()
  await f.locator('.note-title').fill('Edited title')
  await f.locator('.note-title').evaluate('(e)=>e.setSelectionRange(1,6)')
  await f.evaluate("updateNote(state.notes.get('n'),state.notes.get('n').latest)")
  assert await f.locator('.note-title').evaluate('(e)=>e.selectionStart===1&&e.selectionEnd===6')
  await start(p,f,3,1);await p.mouse.up();assert len(await moves(p))==0
  await start(p,f);await p.mouse.up();await settle(f)
  await f.evaluate("saveNote(state.notes.get('n'))")
  assert await p.evaluate("objects.n.facets['core.title'].text")=='Edited title'
  assert await xy(f)==[80,60]
  # Recreate iframe at the exact same entry URL.
  await p.evaluate("document.querySelector('iframe').remove();let f=document.createElement('iframe');f.src='/shell';document.body.append(f)")
  f=p.frames[1];await f.wait_for_selector('.note')
  assert await xy(f)==[80,60]
  assert await f.locator('.note-title').input_value()=='Edited title'
  passed('title editing, click threshold, text/move serialization and reopen persistence')
  await p.close()

  p,f=await setup()
  b=await f.locator('.note-title').bounding_box()
  await p.mouse.move(b['x']+5,b['y']+8);await p.mouse.down();await p.mouse.move(b['x']+65,b['y']+8);await p.mouse.up()
  assert len(await moves(p))==0 and await xy(f)==[20,20]
  assert await f.locator('.note-title').evaluate('(e)=>document.activeElement===e && e.selectionEnd>e.selectionStart')
  for kind in ['Escape','pointercancel','lostpointercapture','blur','resize']:
   await start(p,f)
   if kind=='Escape':await p.keyboard.press('Escape')
   elif kind=='blur':await f.evaluate("window.dispatchEvent(new Event('blur'))")
   elif kind=='resize':
    await p.set_viewport_size({'width':1390,'height':900});await p.wait_for_timeout(60)
   else:await f.evaluate("(kind)=>{const d=state.activeDrag;d.header.dispatchEvent(new PointerEvent(kind,{pointerId:d.pointerId}));}",kind)
   await p.mouse.up();assert await xy(f)==[20,20] and len(await moves(p))==0,kind
  passed('title text selection; Escape, pointer cancel, capture loss, blur, resize rollback')
  await p.close()

  for projected in [False,True]:
   p,f=await setup()
   await start(p,f)
   await p.evaluate("objects.n.revision++;objects.n.facets['core.appearance'].x=310")
   if projected:await f.evaluate('refresh()')
   assert await xy(f)==[80,60]  # no poll-time snapping
   await p.mouse.up();await settle(f)
   assert await xy(f)==[310,20]
   assert await p.evaluate("objects.n.facets['core.appearance'].x")==310
   assert await f.locator('#notice').is_visible()
   assert len(await moves(p))==(0 if projected else 1)
   passed('concurrent move '+('observed during drag' if projected else 'rejected by CAS')+' never overwritten')
   await p.close()

  p,f=await setup()
  await p.evaluate('refuse=true')
  await start(p,f);await p.mouse.up();await settle(f)
  assert await xy(f)==[20,20] and len(await moves(p))==1
  assert 'Move failed'==await f.locator('.note-move-status').inner_text()
  # An old projection arriving after successful save must not roll it back.
  await p.evaluate('refuse=false')
  old=await p.evaluate('copy(objects.n)')
  await start(p,f);await p.mouse.up();await settle(f)
  await f.evaluate('(o)=>updateNote(state.notes.get("n"),o)',old)
  assert await xy(f)==[80,60]
  passed('refused move rollback/no retry; late stale projection ignored')
  await p.close()

  p,f=await setup()
  await p.evaluate('delayText=450;delayMove=350')
  await f.locator('.note-body').fill('In-flight text')
  await f.evaluate("void saveNote(state.notes.get('n'))")
  await start(p,f);await p.mouse.up()
  await f.locator('.note-body').fill('Newer unsaved text')
  await f.evaluate("void prepareReload('pending')")
  await p.wait_for_function("replies.some(r=>r.id==='pending')")
  reply=await p.evaluate("replies.find(r=>r.id==='pending')")
  assert reply.get('result',{}).get('ready'),reply
  assert await p.evaluate("objects.n.facets['core.text'].text")=='Newer unsaved text'
  assert await p.evaluate("objects.n.facets['core.appearance'].x")==80
  await f.evaluate("cancelReload('pending')")
  assert not await f.locator('#app').evaluate('(e)=>e.inert')
  passed('in-flight text then move then newer text; reload flush and thaw')
  await p.close()

  p,f=await setup()
  await start(p,f)
  await f.evaluate("prepareReload('active')")
  await p.wait_for_function("replies.some(r=>r.id==='active')")
  assert await p.evaluate("!!replies.find(r=>r.id==='active').error")
  assert not await f.locator('#app').evaluate('(e)=>e.inert')
  await p.keyboard.press('Escape');await p.mouse.up()
  await p.evaluate('delayMove=150;refuse=true')
  await start(p,f);await p.mouse.up()
  await f.evaluate("prepareReload('refused')")
  await p.wait_for_function("replies.some(r=>r.id==='refused')")
  assert await p.evaluate("!!replies.find(r=>r.id==='refused').error")
  assert not await f.locator('#app').evaluate('(e)=>e.inert')
  passed('reload rejected while dragging and after in-flight refused move')
  await p.close()

  p,f=await setup()
  await f.locator('.note-handle').focus();await p.keyboard.press('ArrowRight');await settle(f)
  assert await xy(f)==[30,20]
  await p.keyboard.press('Shift+ArrowDown');await settle(f)
  assert await xy(f)==[30,21]
  # Drag beyond the note boundary, then force scroll during capture.
  await start(p,f,600,400)
  assert await f.evaluate('!!state.activeDrag && state.activeDrag.header.hasPointerCapture(state.activeDrag.pointerId)')
  await f.evaluate("$('desk').parentElement.scrollTop=80")
  await p.wait_for_timeout(50)
  assert (await xy(f))[1]>=421
  await p.mouse.up();await settle(f)
  passed('keyboard movement; outside-card pointer capture and scrolled coordinates')
  await p.close()

  p,f=await setup(390)
  assert await f.locator('.note-handle').evaluate('(e)=>getComputedStyle(e).touchAction')=='auto'
  assert await f.locator('.note-title').evaluate('(e)=>getComputedStyle(e).touchAction')=='auto'
  await start(p,f);await p.mouse.up()
  assert len(await moves(p))==0
  assert await f.locator('.note').evaluate('(e)=>getComputedStyle(e).position')=='relative'
  passed('mobile stacked layout retains native touch behavior and does not persist fake moves')
  await p.close()

  p,f=await setup()
  cdp=await p.context.new_cdp_session(p)
  b=await f.locator('.note-handle').bounding_box()
  x,y=b['x']+b['width']/2,b['y']+b['height']/2
  await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
  for n in range(1,6):
   await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+10*n,'y':y+6*n}]})
  await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
  await settle(f)
  assert await xy(f)==[70,50],await xy(f)
  assert len(await moves(p))==1
  passed('real Chromium touch pointer moves from header handle on wide desk')
  await p.close()

  p,f=await setup()
  await f.locator('.note-body').fill('My local edit')
  await p.evaluate("objects.n.revision++;objects.n.facets['core.text'].text='New remote text'")
  await f.evaluate('refresh()')
  await start(p,f);await p.mouse.up();await settle(f)
  await f.evaluate("saveNote(state.notes.get('n'))")
  assert await f.locator('.note-body').input_value()=='My local edit'
  assert await p.evaluate("objects.n.facets['core.text'].text")=='New remote text'
  assert await f.evaluate("state.notes.get('n').conflict")
  passed('moving a dirty note does not bless a newer remote text baseline')
  await p.close()

  p,f=await setup()
  await p.evaluate('delayMove=3000')
  await start(p,f);await p.mouse.up()
  await f.evaluate("prepareReload('slow')")
  await p.wait_for_function("replies.some(r=>r.id==='slow')")
  assert await p.evaluate("!!replies.find(r=>r.id==='slow').error")
  assert not await f.locator('#app').evaluate('(e)=>e.inert')
  await settle(f)
  assert await xy(f)==[80,60]
  passed('reload deadline thaws without cancelling or falsely acknowledging the pending move')
  await p.close()


  async def geometry(f):
   return await f.evaluate("noteGeometry(state.notes.get('n'))")
  async def resize(p,f,corner='se',dx=60,dy=40):
   b=await f.locator('.note-resize.'+corner).bounding_box()
   x,y=b['x']+b['width']/2,b['y']+b['height']/2
   await p.mouse.move(x,y);await p.mouse.down();await p.mouse.move(x+dx,y+dy,steps=5)
  original=dict(x=20,y=20,width=245,height=205)
  for corner,expected in [
   ('se',dict(x=20,y=20,width=305,height=245)),
   ('sw',dict(x=80,y=20,width=185,height=245)),
   ('ne',dict(x=20,y=60,width=305,height=165)),
   ('nw',dict(x=80,y=60,width=185,height=165))]:
   p,f=await setup()
   await f.locator('.note-body').focus()
   await f.locator('.note-body').evaluate('(e)=>e.setSelectionRange(2,8)')
   await resize(p,f,corner)
   assert await geometry(f)==expected,(corner,await geometry(f))
   assert len(await moves(p))==0
   assert await f.locator('.note-body').evaluate('(e)=>document.activeElement===e&&e.selectionStart===2&&e.selectionEnd===8')
   await p.mouse.up();await settle(f)
   assert await p.evaluate("objects.n.facets['core.appearance']")==dict(scene='desk',**expected)
   req=(await moves(p))[0]['args']['changes'][0]
   assert req['expected_revision']==1 and list(req['facets'])==['core.appearance']
   assert await f.locator('#chat-input').input_value()=='Existing unsent draft'
   assert await f.locator('.message-content').inner_text()=='Existing conversation'
   await p.evaluate("document.querySelector('iframe').remove();let f=document.createElement('iframe');f.src='/shell';document.body.append(f)")
   f=p.frames[1];await f.wait_for_selector('.note')
   assert await geometry(f)==expected
   passed(corner+' resize preview, opposite corner anchored, CAS save/reopen, focus and draft retention')
   await p.close()

  p,f=await setup()
  await resize(p,f,'se',-300,-300);await p.mouse.up();await settle(f)
  assert await geometry(f)==dict(x=20,y=20,width=160,height=140)
  await f.locator('.note-resize.se').focus()
  await p.keyboard.press('ArrowRight');await settle(f)
  await p.keyboard.press('Shift+ArrowDown');await settle(f)
  assert await geometry(f)==dict(x=20,y=20,width=170,height=141)
  await resize(p,f,'nw',-100,-100);await p.mouse.up();await settle(f)
  assert await geometry(f)==dict(x=0,y=0,width=190,height=161)
  await f.locator('.note-resize.nw').focus()
  count=len(await moves(p))
  await p.keyboard.press('ArrowLeft');await settle(f)
  assert len(await moves(p))==count
  # Pure bounds check without laying out a 100000px browser surface.
  assert await f.evaluate("resizedGeometry({x:0,y:0,width:245,height:205},'se',200000,200000)")==dict(x=0,y=0,width=100000,height=100000)
  passed('minimum/maximum sizes, desk edge clamps, keyboard corner movement and no-op')
  await p.close()

  for kind in ['Escape','pointercancel','lostpointercapture','blur','resize','hidden']:
   p,f=await setup()
   await resize(p,f)
   if kind=='Escape':await p.keyboard.press('Escape')
   elif kind=='blur':await f.evaluate("window.dispatchEvent(new Event('blur'))")
   elif kind=='resize':
    await p.set_viewport_size({'width':1390,'height':900});await p.wait_for_timeout(60)
   elif kind=='hidden':
    await f.evaluate("Object.defineProperty(document,'hidden',{value:true,configurable:true});document.dispatchEvent(new Event('visibilitychange'))")
   else:await f.evaluate("(kind)=>{const d=state.activeDrag;d.header.dispatchEvent(new PointerEvent(kind,{pointerId:d.pointerId}));}",kind)
   await p.mouse.up()
   assert await geometry(f)==original and len(await moves(p))==0,kind
   await p.close()
  passed('resize Escape/cancel/capture-loss/blur/viewport/visibility rollback')

  for projected in [False,True]:
   p,f=await setup()
   old=await p.evaluate('copy(objects.n)')
   await resize(p,f)
   await p.evaluate("objects.n.revision++;objects.n.facets['core.appearance'].width=330")
   if projected:await f.evaluate('refresh()')
   assert (await geometry(f))['width']==305
   await p.mouse.up();await settle(f)
   assert (await geometry(f))['width']==330
   assert await f.locator('.note-move-status').inner_text()=='Resize failed'
   assert len(await moves(p))==(0 if projected else 1)
   await f.evaluate('(o)=>updateNote(state.notes.get("n"),o)',old)
   assert (await geometry(f))['width']==330
   await p.close()
  passed('resize conflicts observed during gesture or refused by CAS; no overwrite or stale projection')

  p,f=await setup()
  await p.evaluate('refuse=true')
  await resize(p,f);await p.mouse.up();await settle(f)
  assert await geometry(f)==original and len(await moves(p))==1
  assert await f.locator('.note-move-status').inner_text()=='Resize failed'
  assert await f.locator('#notice').is_visible()
  passed('refused size save rolls back visibly without retry')
  await p.close()

  p,f=await setup()
  await resize(p,f,dx=3,dy=1);await p.mouse.up()
  assert await geometry(f)==original and len(await moves(p))==0
  await resize(p,f)
  await f.evaluate("prepareReload('resize-active')")
  await p.wait_for_function("replies.some(r=>r.id==='resize-active')")
  assert await p.evaluate("!!replies.find(r=>r.id==='resize-active').error")
  await p.keyboard.press('Escape');await p.mouse.up()
  await p.evaluate('delayText=450;delayMove=350')
  await f.locator('.note-title').fill('Resize title edit')
  await f.evaluate("void saveNote(state.notes.get('n'))")
  await resize(p,f);await p.mouse.up()
  await f.locator('.note-body').fill('Newer text while size saves')
  await f.evaluate("void prepareReload('resize-pending')")
  await p.wait_for_function("replies.some(r=>r.id==='resize-pending')")
  assert await p.evaluate("!!replies.find(r=>r.id==='resize-pending').result?.ready")
  assert await p.evaluate("objects.n.facets['core.title'].text")=='Resize title edit'
  assert await p.evaluate("objects.n.facets['core.text'].text")=='Newer text while size saves'
  assert (await geometry(f))['width']==305
  await f.evaluate("cancelReload('resize-pending')")
  assert not await f.locator('#app').evaluate('(e)=>e.inert')
  passed('resize click threshold, active reload refusal, serialized text/size/new text reload flush and thaw')
  await p.close()

  p,f=await setup()
  cdp=await p.context.new_cdp_session(p)
  b=await f.locator('.note-resize.se').bounding_box()
  x,y=b['x']+b['width']/2,b['y']+b['height']/2
  await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
  for n in range(1,6):
   await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+10*n,'y':y+6*n}]})
  await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
  await settle(f)
  assert await geometry(f)==dict(x=20,y=20,width=295,height=235)
  assert await f.locator('.note-body').evaluate('(e)=>getComputedStyle(e).touchAction')=='auto'
  passed('Chromium touch resize on wide desk; body keeps native touch behavior')
  await p.close()

  p,f=await setup(390)
  for c in ['nw','ne','sw','se']:assert not await f.locator('.note-resize.'+c).is_visible()
  assert await f.locator('.note').evaluate('(e)=>getComputedStyle(e).position')=='relative'
  assert len(await moves(p))==0
  passed('mobile remains stacked/scrollable without misleading corner controls')
  await p.close()

  assert not errors,errors
  await browser.close()
  print('ALL TESTS PASSED; bridge is simulated, not the live host',flush=True)
if __name__ == '__main__':
 asyncio.run(main())
