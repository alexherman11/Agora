"""Overlapping-note interaction regression; simulated parent bridge only."""
import asyncio
from drag_browser import HTML, BRIDGE
from playwright.async_api import async_playwright

BRIDGE=BRIDGE.replace("items:[copy(objects.n)]","items:Object.values(objects).filter(o=>o.facets['core.appearance']).map(copy)")
async def main():
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(args=['--no-sandbox'])
  p=await browser.new_page(viewport={'width':1400,'height':900})
  errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
  await p.route('http://localhost/**',lambda r:r.fulfill(content_type='text/html',body=HTML if r.request.url.endswith('/shell') else BRIDGE))
  await p.goto('http://localhost/');f=p.frames[1]
  await f.wait_for_function('state.draftLoaded && state.connected')
  await p.evaluate("""()=>{
   for(const [id,x,y] of [['q',100,70],['r',150,120]]){
    objects[id]=copy(objects.n);objects[id].id=id;
    Object.assign(objects[id].facets['core.appearance'],{x,y});
   }
  }""")
  await f.evaluate('refresh()')
  async def front():
   return await f.evaluate("""()=>{
    const rect=$('desk').getBoundingClientRect();
    return document.elementFromPoint(rect.left+180,rect.top+150).closest('.note').dataset.objectId;
   }""")
  assert await front()=='r'
  # Keep references to detect accidental editor replacement.
  await f.evaluate("window.originalBody=state.notes.get('n').body")
  await f.locator('[data-object-id="n"] .note-title').click()
  assert await front()=='n'
  assert await f.locator('[data-object-id="n"] .note-title').evaluate('(e)=>document.activeElement===e')
  # Click q's exposed right-hand strip; no editor handling may be swallowed.
  b=await f.locator('[data-object-id="q"]').bounding_box()
  await p.mouse.click(b['x']+230,b['y']+20)
  assert await front()=='q'
  # Keyboard navigation into an underlying editor raises it as well.
  await f.locator('[data-object-id="r"] .note-title').focus()
  assert await front()=='r'
  await f.locator('[data-object-id="n"] .note-body').focus()
  await f.locator('[data-object-id="n"] .note-body').evaluate('(e)=>e.setSelectionRange(2,8)')
  assert await front()=='n'
  await f.evaluate('refresh()')
  assert await front()=='n'
  assert await f.evaluate("state.notes.get('n').body===window.originalBody")
  assert await f.locator('[data-object-id="n"] .note-body').evaluate('(e)=>document.activeElement===e && e.selectionStart===2 && e.selectionEnd===8')
  await f.locator('#chat-input').click()
  assert await front()=='n'
  assert await f.locator('#chat-input').input_value()=='Existing unsent draft'
  assert await f.locator('.message-content').inner_text()=='Existing conversation'
  assert await p.evaluate("requests.filter(r=>r.method==='world.transact').length")==0
  assert await f.evaluate("Math.max(...[...state.notes.values()].map(e=>Number(e.node.style.zIndex)))")<=13
  assert not errors,errors
  await browser.close()
  print('PASS exposed clicks, keyboard focus, overlap hit-testing, retained stacking/DOM/selection/drafts, bounded layers and zero native writes')

if __name__=='__main__':asyncio.run(main())
