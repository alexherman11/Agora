const {chromium}=require('C:/Users/Alex/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict'),{spawn}=require('node:child_process');
(async()=>{
 const fixtureRoot=fs.mkdtempSync(path.join(os.tmpdir(),'tessera-render-load-')),dataDir=path.join(fixtureRoot,'data'),trialsDir=path.join(fixtureRoot,'trials');
 const report={scope:'Local headless Chrome; full-render time excludes interpreter dispatch, network and DOM input handling. Instrumentation is included.',results:[]};
 fs.mkdirSync(dataDir);fs.mkdirSync(trialsDir);
 for(const count of [20,80,160]){
  const dir=path.join(trialsDir,`load-${count}`);fs.mkdirSync(dir);
  for(const file of fs.readdirSync(path.join(__dirname,'trials/05-kinetic-loom')).filter(f=>f.endsWith('.tessera.json')))fs.copyFileSync(path.join(__dirname,'trials/05-kinetic-loom',file),path.join(dir,file));
  fs.writeFileSync(path.join(dir,'fixture.tessera.json'),JSON.stringify({id:'fixture',claims:Array.from({length:count-16},(_,i)=>({kind:'seed',id:`bodies/load-${i}`,values:{label:`LOAD ${i}`,x:(i*137)%1000,y:(i*79)%640,vx:20,vy:15}}))}));
 }
 const proc=spawn(process.execPath,['server.mjs'],{cwd:__dirname,windowsHide:true,env:{...process.env,TESSERA_PORT:'4386',TESSERA_DATA_DIR:dataDir,TESSERA_TRIALS_DIR:trialsDir}});let browser;
 try{
  await new Promise((resolve,reject)=>{proc.stdout.on('data',d=>{if(String(d).includes('listening'))resolve()});proc.on('error',reject)});
  browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
  for(const count of [20,80,160]){
   const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.goto(`http://127.0.0.1:4386/scene?trial=load-${count}`);await page.waitForFunction(()=>window.tessera);
   const before=await page.evaluate(()=>({...window.tessera.metrics}));const start=Date.now();
   await page.request.post(`http://127.0.0.1:4386/api/action?trial=load-${count}`,{data:{action:'instrument.start',args:{}}});
   await page.waitForFunction(()=>window.tessera.saved.state.simulation.main.steps>=25,null,{timeout:20000});
   await page.request.post(`http://127.0.0.1:4386/api/action?trial=load-${count}`,{data:{action:'instrument.pause',args:{}}});
   await page.waitForFunction(()=>!window.tessera.saved.state.simulation.main.running);
   const after=await page.evaluate(()=>({metrics:window.tessera.metrics,steps:window.tessera.saved.state.simulation.main.steps,issues:window.tessera.issues,nodes:document.querySelectorAll('[data-key]').length}));
   assert.deepEqual(errors,[]);assert.deepEqual(after.issues,[]);
   report.results.push({bodies:count,observedSteps:after.steps,wallMs:Date.now()-start,renders:after.metrics.renders-before.renders,meanRenderMs:(after.metrics.renderMs-before.renderMs)/(after.metrics.renders-before.renders),maxRenderMs:after.metrics.maxRenderMs,viewOccurrences:after.nodes});
   await page.screenshot({path:`evidence/trial05-load-${count}.png`});await page.close();
  }
  report.ok=true;
 }finally{fs.writeFileSync('evidence/trial05-render-pressure.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));if(browser)await browser.close();proc.kill();}
})().catch(e=>{console.error(e);process.exit(1)});
