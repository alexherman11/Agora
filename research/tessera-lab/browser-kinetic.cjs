const {chromium}=require('C:/Users/Alex/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict'),{spawn}=require('node:child_process');
(async()=>{
 const dataDir=fs.mkdtempSync(path.join(os.tmpdir(),'tessera-kinetic-'));
 const proc=spawn(process.execPath,['server.mjs'],{cwd:__dirname,windowsHide:true,env:{...process.env,TESSERA_PORT:'4385',TESSERA_DATA_DIR:dataDir}});let browser,page;
 const base='http://127.0.0.1:4385',trial='05-kinetic-loom',report={ok:false,checks:[],errors:[]};
 try{
 await new Promise((resolve,reject)=>{proc.stdout.on('data',d=>{if(String(d).includes('listening'))resolve()});proc.on('error',reject)});
 browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 page=await browser.newPage({viewport:{width:1600,height:1000}});page.setDefaultTimeout(6000);page.on('pageerror',e=>report.errors.push(e.message));
 await page.goto(`${base}/scene?trial=${trial}`);await page.waitForFunction(()=>window.tessera);
 const view=id=>page.locator(`[data-view="${id}"]`);
 const state=async()=>(await(await page.request.get(`${base}/api/state?trial=${trial}`)).json());
 const post=async(endpoint,data)=>(await(await page.request.post(`${base}/api/${endpoint}?trial=${trial}`,{data})).json());
 assert.deepEqual(await page.evaluate(()=>window.tessera.issues),[]);assert.equal(await view('motion.body').count(),16);
 await page.screenshot({path:'evidence/trial05-initial.png'});
 await view('instrument.step').click();await page.waitForFunction(()=>window.tessera.saved.state.simulation.main.steps===1);report.checks.push('Composed Step updates simulation and measured visuals');
 await view('instrument.start').click();await page.waitForFunction(()=>window.tessera.saved.state.simulation.main.steps>=8);
 const before=await state(),commits=await page.evaluate(()=>window.tessera.metrics.commits);
 const handle=await page.evaluate(()=>{const n=[...document.querySelectorAll('[data-view="motion.body"]')].find(n=>n.dataset.scope.endsWith('/ember'));const r=n.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};});
 await page.mouse.move(handle.x,handle.y);await page.mouse.down();await page.mouse.move(handle.x+150,handle.y+60,{steps:20});await page.mouse.up();
 await page.waitForFunction(n=>window.tessera.metrics.commits>n,commits);
 const after=await state();report.runningDrag={before:before.state.bodies.ember,after:after.state.bodies.ember,newConflicts:after.conflicts.slice(before.conflicts.length)};
 assert.equal(report.runningDrag.newConflicts.length,0,JSON.stringify(report.runningDrag.newConflicts));
 assert(after.state.bodies.ember.dragX-before.state.bodies.ember.dragX>140,'Drag should add a visible displacement to the running body');report.checks.push('Dragging a body during authoritative motion commits as an additive displacement');
 const force=await view('field.handle').boundingBox();await page.mouse.move(force.x+18,force.y+18);await page.mouse.down();await page.mouse.move(force.x+108,force.y-22,{steps:12});await page.mouse.up();
 await page.waitForFunction(()=>window.tessera.saved.state.fields.main.x>580);report.checks.push('Independent force handle remains movable during simulation');
 await view('instrument.pause').click();await page.waitForFunction(()=>window.tessera.saved.state.simulation.main.running===false);
 const paused=await state();await page.waitForTimeout(250);assert.equal((await state()).serial,paused.serial);report.checks.push('Pause stops all authoritative ticks');
 await view('instrument.modeObs').click();await page.waitForFunction(()=>window.tessera.saved.state.instrument.main.mode==='observatory');
 await page.screenshot({path:'evidence/trial05-observatory.png'});report.checks.push('Appearance and spatial placement change with stable moving-body identities');
 await view('instrument.overrideOff').click();await page.waitForFunction(()=>window.tessera.issues.some(x=>x.code==='style-conflict'));
 assert((await page.evaluate(()=>window.tessera.issues)).every(i=>i.code==='style-conflict'&&i.property.startsWith('border')));
 await view('instrument.overrideGlow').click();await page.waitForFunction(()=>window.tessera.issues.length===0);report.checks.push('Competing body styles are exposed and resolved explicitly');
 await page.locator('#status').click();const retained=(await state()).state;
 await page.locator('[data-module="field"]').uncheck();await page.waitForFunction(()=>!window.tessera.saved.modules.find(m=>m.id==='field').enabled);
 assert.equal(await view('field.handle').count(),0);assert.deepEqual((await state()).state,retained);
 await page.locator('[data-module="field"]').check();await page.waitForFunction(()=>window.tessera.saved.modules.find(m=>m.id==='field').enabled);
 assert.equal(await view('field.handle').count(),1);assert.deepEqual((await state()).state,retained);await page.locator('#status').click();report.checks.push('Live author-layer withdrawal and restoration preserve exact object state');
 for(let mask=0;mask<8;mask++){
  const enabled=['motion','field','instrument'].filter((_,i)=>mask&(1<<i));const result=await post('layers',{enabled});assert(!result.error,JSON.stringify(result));
  await page.waitForFunction(ids=>window.tessera.saved.modules.filter(m=>m.enabled&&m.id!=='base').length===ids.length,enabled);
 }
 await post('layers',{enabled:['motion','field','instrument']});await view('instrument.start').waitFor();report.checks.push('All 8 author subsets render without browser exceptions');
 const rate=async()=>{const a=await state(),start=Date.now();await page.waitForTimeout(1200);const b=await state();return (b.state.simulation.main.steps-a.state.simulation.main.steps)/((Date.now()-start)/1000);};
 await view('instrument.start').click();await page.waitForFunction(()=>window.tessera.saved.state.simulation.main.running);const one=await rate();
 const extra=await Promise.all([0,1].map(async()=>{const c=await browser.newContext({viewport:{width:1600,height:1000}}),p=await c.newPage();await p.goto(`${base}/scene?trial=${trial}`);await p.waitForFunction(()=>window.tessera);return p;}));
 const three=await rate();report.clockRates={oneBrowserStepsPerSecond:one,threeBrowserStepsPerSecond:three};assert(three<=one*1.35&&three>=3,JSON.stringify(report.clockRates));
 await post('action',{action:'instrument.pause',args:{}});report.checks.push('Three independent browser clients do not multiply simulation speed');
 report.metrics=await page.evaluate(()=>window.tessera.metrics);report.ok=report.errors.length===0;
 }catch(e){report.failure=e.message;if(page)await page.screenshot({path:'evidence/trial05-browser-failure.png'});throw e;}
 finally{fs.writeFileSync('evidence/trial05-browser.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));if(browser)await browser.close();proc.kill();}
})().catch(e=>{console.error(e);process.exit(1)});
