const {chromium}=require('C:/Users/Alex/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict'),{spawn}=require('node:child_process');
(async()=>{
 const dataDir=fs.mkdtempSync(path.join(os.tmpdir(),'tessera-fluid-'));
 const proc=spawn(process.execPath,['server.mjs'],{cwd:__dirname,windowsHide:true,env:{...process.env,TESSERA_PORT:'4384',TESSERA_DATA_DIR:dataDir}});let browser,page;
 const report={ok:false,checks:[],errors:[]};
 try{
 await new Promise((resolve,reject)=>{proc.stdout.on('data',d=>{if(String(d).includes('listening'))resolve()});proc.on('error',reject)});
 browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 page=await browser.newPage({viewport:{width:1600,height:1000}});page.setDefaultTimeout(8000);page.on('pageerror',e=>report.errors.push(e.message));
 await page.goto('http://127.0.0.1:4384/scene?trial=04-fluid-scene');await page.locator('[data-view="studio.surface"]').waitFor();
 const view=id=>page.locator(`[data-view="${id}"]`),card=id=>page.locator(`[data-view="card.shell"][data-scope$="/${id}"]`);
 const get=()=>page.evaluate(()=>window.tessera.saved);
 const endpoints=async()=>page.evaluate(()=>{
  const card=id=>[...document.querySelectorAll('[data-view="card.shell"]')].find(n=>n.dataset.scope.endsWith('/'+id));
  return Object.entries(window.tessera.state.connections).map(([id,c])=>{const line=[...document.querySelectorAll('#paint line')].find(n=>n.dataset.connection===id);return {id,c};});
 });
 assert.equal(await view('reading.surface').count(),1);assert.deepEqual(await page.evaluate(()=>window.tessera.issues),[]);
 await page.screenshot({path:'evidence/trial04-overview.png'});
 await view('toolkit.toolbar.target').selectOption('studio');await view('toolkit.toolbar.focus').click();
 await page.waitForFunction(()=>window.tessera.saved.state.settings.scene.mode==='focused');
 const beforeHeight=(await card('studio-brief').boundingBox()).height;
 await card('studio-brief').locator('[data-view="card.grip.expand"]').click();
 await page.waitForFunction(()=>window.tessera.saved.state.cards['studio-brief'].expanded===true,{},{timeout:8000});
 const afterHeight=(await card('studio-brief').boundingBox()).height;assert(afterHeight>beforeHeight+50);report.checks.push('Intrinsic card expansion without a shared size constant');
 await card('studio-brief').locator('[data-view="card.tools.editBody"]').fill('A long, live research document. Its representation can change without breaking any relationship. The shared card remains the same object when it moves to a different window.');
 await card('studio-brief').locator('[data-view="card.tools.save"]').click();
 await page.waitForFunction(()=>window.tessera.saved.state.cards['studio-brief'].body.startsWith('A long, live'));
 const assertGeometry=async()=>{
  const accuracy=await page.evaluate(()=>{
   const cards=Object.fromEntries([...document.querySelectorAll('[data-view="card.shell"]')].map(n=>{const r=n.getBoundingClientRect();return [n.dataset.scope.split('/').at(-1),{x:r.x+r.width/2,y:r.y+r.height/2}]}));
   const connections=Object.entries(window.tessera.state.connections).sort(([a],[b])=>a.localeCompare(b));const lines=[...document.querySelectorAll('#paint line')];
   return connections.map(([id,c],i)=>({id,delta:Math.max(Math.abs(Number(lines[i].getAttribute('x1'))-cards[c.fromId].x),Math.abs(Number(lines[i].getAttribute('y1'))-cards[c.fromId].y),Math.abs(Number(lines[i].getAttribute('x2'))-cards[c.toId].x),Math.abs(Number(lines[i].getAttribute('y2'))-cards[c.toId].y))}));
  });assert(accuracy.every(x=>x.delta<1),JSON.stringify(accuracy));
 };
 await assertGeometry();report.checks.push('Cross-window measured endpoints follow expanded/edited content');
 await view('toolkit.toolbar.overview').click();await page.waitForFunction(()=>window.tessera.saved.state.settings.scene.mode==='overview');
 const {source,host}=await page.evaluate(()=>{
  const grip=[...document.querySelectorAll('[data-view="card.shell"]')].find(n=>n.dataset.scope.endsWith('/studio-brief')).querySelector('[data-view="card.grip"]');
  const rect=n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};};
  return {source:rect(grip),host:rect(document.querySelector('[data-view="reading.host"]'))};
 });
 assert(source.width>0&&host.width>0,'Both drag handles and destinations must be rendered');
 await page.mouse.move(source.x+20,source.y+8);await page.mouse.down();await page.mouse.move(host.x+100,host.y+80,{steps:18});await page.mouse.up();
 await page.waitForFunction(()=>window.tessera.saved.state.cards['studio-brief'].host==='reading.host');await assertGeometry();report.checks.push('Connected expanded document moves into an independently added host');
 await page.screenshot({path:'evidence/trial04-cross-window.png'});
 for(const [width,height]of [[1000,800],[600,900]]){
  await page.setViewportSize({width,height});await page.waitForTimeout(100);
  await view('toolkit.toolbar.target').selectOption('reading');await view('toolkit.toolbar.focus').click();
  await page.waitForFunction(()=>window.tessera.saved.state.settings.scene.focusId==='reading');
  assert(await view('toolkit.toolbar.overview').isVisible());const r=await view('reading.surface').boundingBox();assert(r.x>=0&&r.x+r.width<=width+1,JSON.stringify(r));
  await assertGeometry();await page.screenshot({path:`evidence/trial04-${width}.png`});report.checks.push(`Reachable focused editing and correct links at ${width}×${height}`);
 }
 // Actual concurrent clients with one shared revision snapshot, then a genuine collision.
 const pages=await Promise.all([0,1,2].map(async()=>{const context=await browser.newContext();const p=await context.newPage();await p.goto('http://127.0.0.1:4384/scene?trial=04-fluid-scene');await p.locator('[data-view="reading.surface"]').waitFor();return p;}));
 const snapshot=await get();const ids=['studio','atlas','reading'];
 const results=await Promise.all(pages.map((p,i)=>p.evaluate(async request=>await(await fetch('/api/action?trial=04-fluid-scene',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request)})).json(),{action:'surface.move',args:{id:ids[i],x:40+i*220,y:100+i*40},expected:snapshot.versions})));
 assert(results.every(r=>r.result.ok),JSON.stringify(results.map(r=>r.result)));report.checks.push('Three concurrent isolated clients move distinct windows from one snapshot');
 const sameSnapshot=(await(await page.request.get('http://127.0.0.1:4384/api/state?trial=04-fluid-scene')).json()).versions;const collisions=await Promise.all(pages.slice(0,2).map((p,i)=>p.evaluate(async request=>await(await fetch('/api/action?trial=04-fluid-scene',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request)})).json(),{action:'surface.move',args:{id:'studio',x:100+i*20,y:130},expected:sameSnapshot})));
 assert.equal(collisions.filter(r=>r.result.ok).length,1);report.checks.push('Competing same-window stale movement preserves an explicit conflict');
 report.metrics=await page.evaluate(()=>window.tessera.metrics);report.ok=report.errors.length===0;
 }catch(e){report.failure=e.message;if(page)await page.screenshot({path:'evidence/trial04-browser-failure.png'});throw e;}
 finally{fs.writeFileSync('evidence/trial04-browser.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));if(browser)await browser.close();proc.kill();}
})().catch(e=>{console.error(e);process.exit(1)});
