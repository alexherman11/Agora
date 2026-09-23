"""Pointer snapping tests against the retained shell and a simulated bridge.
Run: python tests/snap_browser.py [path/to/index.html]
No live world writes. Also run drag_browser.py for drag/resize/reload regressions.
"""
import asyncio
from drag_browser import HTML, BRIDGE
from playwright.async_api import async_playwright

BRIDGE = BRIDGE.replace("items:[copy(objects.n)]","items:Object.values(objects).filter(o=>o.facets['core.appearance']).map(copy)")
NOTE = '[data-object-id="n"]'

async def main():
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True,args=['--no-sandbox'])
  errors=[]
  async def setup(x=350,y=300,width=1800):
   p=await browser.new_page(viewport={'width':width,'height':1000})
   p.on('pageerror',lambda e:errors.append(str(e)))
   await p.route('http://localhost/**',lambda r:r.fulfill(content_type='text/html',body=HTML if r.request.url.endswith('/shell') else BRIDGE))
   await p.goto('http://localhost/')
   f=p.frames[1];await f.wait_for_function('state.draftLoaded && state.connected')
   await p.evaluate("([x,y])=>{objects.q=copy(objects.n);objects.q.id='q';objects.q.facets['core.appearance'].x=x;objects.q.facets['core.appearance'].y=y;}",[x,y])
   await f.evaluate('refresh()')
   return p,f
  async def xy(f):
   return await f.locator(NOTE).evaluate('(e)=>[parseFloat(e.style.left),parseFloat(e.style.top)]')
  async def start(p,f,x,y):
   box=await f.locator(NOTE+' .note-header').bounding_box()
   origin=await xy(f)
   sx,sy=box['x']+32,box['y']+6
   await p.mouse.move(sx,sy);await p.mouse.down()
   await p.mouse.move(sx+x-origin[0],sy+y-origin[1],steps=5)
   return sx-origin[0],sy-origin[1]
  async def settle(f):
   await f.wait_for_function('[...state.notes.values()].every(e=>!e.positionPromise && !e.savePromise)')
  async def moves(p):
   return await p.evaluate("requests.filter(r=>r.method==='world.transact' && r.args.changes.some(c=>c.facets['core.appearance']))")
  async def snapped(f):
   return await f.locator(NOTE).evaluate("(e)=>e.classList.contains('snapped')")

  for side,target in [('right',[607,300]),('left',[93,300]),('below',[350,517]),('above',[350,83])]:
   p,f=await setup()
   neighbor=await p.evaluate('copy(objects.q)')
   await f.locator('#chat-input').focus()
   await f.locator('#chat-input').evaluate('(e)=>e.setSelectionRange(2,8)')
   await start(p,f,target[0]+5,target[1]+7)
   assert await xy(f)==target,(side,await xy(f))
   assert await snapped(f)
   assert len(await moves(p))==0
   assert await f.locator('#chat-input').evaluate('(e)=>document.activeElement===e && e.selectionStart===2 && e.selectionEnd===8')
   await p.mouse.up();await settle(f)
   assert await xy(f)==target and not await snapped(f)
   req=(await moves(p))[0]['args']['changes']
   assert len(req)==1 and req[0]['id']=='n' and req[0]['expected_revision']==1
   assert list(req[0]['facets'])==['core.appearance']
   assert await p.evaluate('objects.q')==neighbor
   assert await f.locator('#chat-input').input_value()=='Existing unsent draft'
   assert await f.locator('.message-content').inner_text()=='Existing conversation'
   await p.evaluate("document.querySelector('iframe').remove();let f=document.createElement('iframe');f.src='/shell';document.body.append(f)")
   f=p.frames[1];await f.wait_for_selector(NOTE)
   assert await xy(f)==target
   await p.close()
   print('PASS '+side+' adjacency: 12px gap, edge alignment, preview, one CAS write, unchanged neighbor, drafts/focus and reopen',flush=True)

  p,f=await setup()
  ox,oy=await start(p,f,98,307)
  assert await xy(f)==[93,300]
  await p.keyboard.down('Alt')
  assert await xy(f)==[98,307] and not await snapped(f)
  await p.keyboard.up('Alt')
  assert await xy(f)==[93,300] and await snapped(f)
  await p.mouse.move(ox+140,oy+307)
  assert await xy(f)==[140,307] and not await snapped(f)
  await p.mouse.move(ox+98,oy+307)
  assert await snapped(f)
  await p.keyboard.down('Alt');await p.mouse.up();await p.keyboard.up('Alt');await settle(f)
  assert await xy(f)==[98,307]
  assert len(await moves(p))==1
  await p.close()
  print('PASS pull-away releases snapping; Alt toggles preview without motion and bypasses on release',flush=True)

  for mode in ['cancel','refuse','stale','projected']:
   p,f=await setup()
   await start(p,f,98,307)
   if mode=='cancel':
    await p.keyboard.press('Escape');await p.mouse.up()
    assert await xy(f)==[20,20] and len(await moves(p))==0
   else:
    if mode=='refuse':await p.evaluate('refuse=true')
    else:
     await p.evaluate("objects.n.revision++;objects.n.facets['core.appearance'].x=160")
     if mode=='projected':await f.evaluate('refresh()')
    await p.mouse.up();await settle(f)
    assert await xy(f)==([20,20] if mode=='refuse' else [160,20])
    assert await f.locator('#notice').is_visible()
    assert len(await moves(p))==(0 if mode=='projected' else 1)
   assert not await snapped(f)
   await p.close()
  print('PASS snapped preview cancellation, refusal, and stale/concurrent source writes preserve confirmed geometry',flush=True)

  p,f=await setup()
  # Check proximity, overlap, differing sizes, bounds, and nearest-candidate choice.
  result=await f.evaluate("""()=>{
    const n=state.notes.get('n'),q=state.notes.get('q');
    const snap=(x,y)=>snapNotePosition(n,{x,y},245,205);
    const distant=snap(93,0),outside=snap(110,300),partial=snap(98,380);
    paintGeometry(q,{x:350,y:300,width:200,height:180});
    const bottom=snap(98,280),right=snap(310,492);
    const r={id:'r',revision:1,facets:{'core.title':{text:'Third'},'core.text':{text:''},'core.appearance':{scene:'desk',x:350,y:340,width:245,height:205}}};
    createNote(r);
    const nearest=snap(98,337);
    paintGeometry(q,{x:100,y:300,width:200,height:180});
    const negative=snap(0,300);
    return {distant,outside,partial,bottom,right,nearest,negative};
  }""")
  assert not result['distant']['snapped'] and not result['outside']['snapped']
  assert result['partial']==dict(x=93,y=380,snapped=True)
  assert result['bottom']==dict(x=93,y=275,snapped=True)
  assert result['right']==dict(x=305,y=492,snapped=True)
  assert result['nearest']==dict(x=93,y=337,snapped=True) # Closest valid side, no gratuitous alignment.
  assert not result['negative']['snapped']
  await p.close()
  print('PASS proximity/overlap limits, partial adjacency, unequal-size end alignment, nearest candidate, no negative snap',flush=True)

  p,f=await setup(x=340,y=20)
  b=await f.locator(NOTE+' .note-resize.se').bounding_box()
  x,y=b['x']+b['width']/2,b['y']+b['height']/2
  await p.mouse.move(x,y);await p.mouse.down();await p.mouse.move(x+70,y);await p.mouse.up();await settle(f)
  assert await f.locator(NOTE).evaluate('(e)=>parseFloat(e.style.width)')==315
  assert not await snapped(f)
  await p.close()
  p,f=await setup(x=289,y=20)
  await f.locator(NOTE+' .note-handle').focus();await p.keyboard.press('ArrowRight');await settle(f)
  assert await xy(f)==[30,20]
  await p.close()
  p,f=await setup(width=390)
  await start(p,f,98,307);await p.mouse.up()
  assert len(await moves(p))==0 and not await snapped(f)
  await p.close()
  print('PASS resize and keyboard precision unchanged; stacked mobile desk does not snap or write',flush=True)
  assert not errors,errors
  await browser.close()
  print('ALL SNAP TESTS PASSED; simulated bridge, not live host',flush=True)

if __name__ == '__main__':
 asyncio.run(main())
