"""Corner snapping and native-shaped note style tests; simulated bridge."""
import asyncio
from drag_browser import HTML, BRIDGE
from playwright.async_api import async_playwright
BRIDGE=BRIDGE.replace("items:[copy(objects.n)]","items:Object.values(objects).filter(o=>o.facets['core.appearance']).map(copy)")
BRIDGE=BRIDGE.replace("c=>c.facets['core.appearance']","c=>c.facets['core.appearance']||c.facets['desk.note-style']")
N='[data-object-id="n"]'
async def main():
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(args=['--no-sandbox'])
  errors=[]
  async def setup(width=1800,dark=False):
   p=await browser.new_page(viewport={'width':width,'height':1000},color_scheme='dark' if dark else 'light')
   p.on('pageerror',lambda e:errors.append(str(e)))
   await p.route('http://localhost/**',lambda r:r.fulfill(content_type='text/html',body=HTML if r.request.url.endswith('/shell') else BRIDGE))
   await p.goto('http://localhost/');f=p.frames[1]
   await f.wait_for_function('state.draftLoaded && state.connected')
   return p,f
  async def settle(f):
   await f.wait_for_function('[...state.notes.values()].every(e=>!e.positionPromise && !e.savePromise)')
  async def xy(f):
   return await f.locator(N).evaluate('(e)=>[parseFloat(e.style.left),parseFloat(e.style.top)]')
  async def start(p,f,x,y):
   b=await f.locator(N+' .note-header').bounding_box()
   sx,sy=b['x']+32,b['y']+6
   await p.mouse.move(sx,sy);await p.mouse.down();await p.mouse.move(sx+x-20,sy+y-20,steps=5)
  async def menu(p,f):
   b=await f.locator(N+' .note-header').bounding_box()
   await p.mouse.click(b['x']+32,b['y']+6,button='right')
   await f.wait_for_selector('#note-menu:not([hidden])')
  async def choose(f,color):
   await f.locator('#note-menu [data-color="'+color+'"]').click()
  async def writes(p):
   return await p.evaluate("requests.filter(r=>r.method==='world.transact')")

  for h,v in [('left','above'),('right','above'),('left','below'),('right','below')]:
   p,f=await setup()
   await p.evaluate("""([h,v])=>{
    for(const [id,x,y] of [['q',h==='left'?93:607,240],['r',300,v==='above'?83:517]]) {
     objects[id]=copy(objects.n);objects[id].id=id;Object.assign(objects[id].facets['core.appearance'],{x,y});
    }
   }""",[h,v])
   await f.evaluate('refresh()')
   await start(p,f,355,307)
   assert await xy(f)==[350,300],(h,v,await xy(f))
   assert len(await writes(p))==0
   await p.keyboard.down('Alt');assert await xy(f)==[355,307]
   await p.keyboard.up('Alt');assert await xy(f)==[350,300]
   await p.mouse.up();await settle(f)
   req=(await writes(p))[0]['args']['changes']
   assert len(req)==1 and req[0]['id']=='n' and req[0]['expected_revision']==1
   assert await p.evaluate("objects.q.revision===1 && objects.r.revision===1")
   # Incompatible orthogonal neighbor cannot pull a corner through empty space.
   await f.evaluate("paintGeometry(state.notes.get('r'),{x:0,y:83,width:245,height:205})")
   assert await f.evaluate("snapNotePosition(state.notes.get('n'),{x:355,y:307},245,205)")==dict(x=350,y=307,snapped=True)
   await p.close()
  print('PASS all four two-neighbor corners, offset edges, Alt bypass, one CAS write, final-overlap validation',flush=True)

  p,f=await setup()
  before=await p.evaluate('copy(objects.n)')
  await f.locator(N+' .note-body').focus()
  await f.locator(N+' .note-body').evaluate('(e)=>e.setSelectionRange(2,8)')
  await menu(p,f)
  assert await f.locator('#note-menu [aria-checked="true"]').inner_text()=='Yellow'
  await choose(f,'blue');await settle(f)
  assert await f.locator(N).get_attribute('data-color')=='blue'
  assert await f.locator(N+' .note-body').evaluate('(e)=>document.activeElement===e && e.selectionStart===2 && e.selectionEnd===8')
  assert await p.evaluate("objects.n.facets['desk.note-style']")==dict(color='blue')
  req=(await writes(p))[0]['args']['changes'][0]
  assert req['expected_revision']==1 and list(req['facets'])==['desk.note-style']
  assert await p.evaluate("objects.n.facets['core.appearance']")==before['facets']['core.appearance']
  assert await p.evaluate("objects.n.facets['core.text']")==before['facets']['core.text']
  assert await f.locator('#chat-input').input_value()=='Existing unsent draft'
  # Reopen with the retained world projection.
  await p.evaluate("document.querySelector('iframe').remove();let f=document.createElement('iframe');f.src='/shell';document.body.append(f)")
  f=p.frames[1];await f.wait_for_selector(N)
  assert await f.locator(N).get_attribute('data-color')=='blue'
  await p.close()
  print('PASS right-click color, isolated facet CAS, unchanged text/geometry/drafts, selection restored, reopen',flush=True)

  for mode in ['refuse','stale','projected']:
   p,f=await setup()
   await menu(p,f)
   if mode=='refuse':await p.evaluate('refuse=true')
   else:
    await p.evaluate("objects.n.revision++;objects.n.facets['desk.note-style']={color:'pink'}")
    if mode=='projected':await f.evaluate('refresh()')
   await choose(f,'blue');await settle(f)
   assert await f.locator(N).get_attribute('data-color')==('yellow' if mode=='refuse' else 'pink')
   assert await f.locator('.note-move-status').inner_text()=='Color failed'
   assert len(await writes(p))==(0 if mode=='projected' else 1)
   assert await f.locator('#notice').is_visible()
   await p.close()
  print('PASS refused/stale/menu-opening-baseline conflicts never overwrite newer color',flush=True)

  p,f=await setup()
  await f.evaluate("document.addEventListener('contextmenu',e=>window.lastContextPrevented=e.defaultPrevented)")
  await f.locator(N+' .note-title').click(button='right')
  assert not await f.evaluate('window.lastContextPrevented')
  assert not await f.locator('#note-menu').is_visible()
  await p.keyboard.press('Escape')
  await f.locator(N+' .note-actions').focus();await p.keyboard.press('Enter')
  await f.wait_for_selector('#note-menu:not([hidden])')
  await p.keyboard.press('End')
  assert await f.locator('#note-menu [data-color="gray"]').evaluate('(e)=>document.activeElement===e')
  await p.keyboard.press('Home');await p.keyboard.press('ArrowDown');await p.keyboard.press('Enter');await settle(f)
  assert await f.locator(N).get_attribute('data-color')=='green'
  await menu(p,f);await p.keyboard.press('Escape')
  assert not await f.locator('#note-menu').is_visible()
  await menu(p,f);await p.mouse.click(900,100)
  assert not await f.locator('#note-menu').is_visible()
  await menu(p,f)
  await f.evaluate("prepareReload('open-menu')")
  await p.wait_for_function("replies.some(r=>r.id==='open-menu')")
  assert await p.evaluate("!!replies.find(r=>r.id==='open-menu').error")
  await p.keyboard.press('Escape')
  assert not await f.locator('#app').evaluate('(e)=>e.inert')
  await p.close()
  print('PASS native editor context menu; keyboard actions/arrows/Home/End/Escape, outside dismissal, active-menu reload refusal',flush=True)

  p,f=await setup()
  await p.evaluate('delayText=400;delayMove=350')
  await f.locator(N+' .note-body').fill('Edited before color')
  await menu(p,f);await choose(f,'lavender')
  await f.locator(N+' .note-body').fill('Newer text during color save')
  await f.evaluate("void prepareReload('color-pending')")
  await p.wait_for_function("replies.some(r=>r.id==='color-pending')")
  assert await p.evaluate("!!replies.find(r=>r.id==='color-pending').result?.ready")
  assert await p.evaluate("objects.n.facets['core.text'].text")=='Newer text during color save'
  assert await p.evaluate("objects.n.facets['desk.note-style'].color")=='lavender'
  await f.evaluate("cancelReload('color-pending')")
  assert not await f.locator('#app').evaluate('(e)=>e.inert')
  await p.close()
  print('PASS text/color/newer-text serialization and safe-reload flush/thaw',flush=True)

  p,f=await setup()
  await f.locator(N+' .note-body').fill('Keep my draft')
  await p.evaluate("objects.n.revision++;objects.n.facets['core.text'].text='Remote body'")
  await f.evaluate('refresh()')
  await menu(p,f);await choose(f,'gray');await settle(f)
  assert await f.locator(N+' .note-body').input_value()=='Keep my draft'
  assert await p.evaluate("objects.n.facets['core.text'].text")=='Remote body'
  assert await f.evaluate("state.notes.get('n').conflict")
  await p.close()
  print('PASS color does not bless conflicting remote text baseline',flush=True)

  for dark in [False,True]:
   p,f=await setup(width=390,dark=dark)
   for color in ['green','blue','pink','lavender','gray','yellow']:
    await f.locator(N+' .note-actions').click()
    await choose(f,color);await settle(f)
    assert await f.locator(N).get_attribute('data-color')==color
   await f.locator(N+' .note-actions').click()
   box=await f.locator('#note-menu').bounding_box()
   assert box['x']>=0 and box['x']+box['width']<=390 and box['y']+box['height']<=1000
   assert await f.locator(N).evaluate('(e)=>getComputedStyle(e).position')=='relative'
   await p.close()
  print('PASS six palettes, narrow mobile button/menu bounds, light and dark render paths',flush=True)
  assert not errors,errors
  await browser.close()
  print('ALL CORNER/COLOR TESTS PASSED; simulated bridge, not live host',flush=True)
if __name__=='__main__':asyncio.run(main())
