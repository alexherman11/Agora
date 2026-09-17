const {chromium}=require('C:/Users/Alex/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict'),{spawn}=require('node:child_process');
(async()=>{
 const dataDir=fs.mkdtempSync(path.join(os.tmpdir(),'tessera-clients-'));
 const proc=spawn(process.execPath,['server.mjs'],{cwd:__dirname,windowsHide:true,env:{...process.env,TESSERA_PORT:'4382',TESSERA_DATA_DIR:dataDir}});
 let browser;
 try{
  await new Promise((resolve,reject)=>{proc.stdout.on('data',d=>{if(String(d).includes('listening'))resolve()});proc.on('error',reject);proc.on('exit',c=>reject(Error(`server exited ${c}`)));});
  browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
  const pages=await Promise.all(Array.from({length:3},async()=>{const c=await browser.newContext();const p=await c.newPage();await p.goto('http://127.0.0.1:4382/?trial=02-expedition');await p.locator('[data-view="missions.card"]').first().waitFor();return p;}));
  const snapshot=await(await fetch('http://127.0.0.1:4382/api/state?trial=02-expedition')).json();
  const commands=[{action:'mission.dispatch',args:{id:'ridge',eventId:'concurrent-ridge'}},{action:'mission.dispatch',args:{id:'coast',eventId:'concurrent-coast'}},{action:'finance.topUp',args:{id:'alpine',amount:100}}];
  const started=Date.now();
  const results=await Promise.all(pages.map((p,i)=>p.evaluate(async request=>{
    const started=performance.now();const response=await fetch('/api/action?trial=02-expedition',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request)});return {durationMs:performance.now()-started,...await response.json()};
  },{...commands[i],expected:snapshot.versions})));
  const state=await(await fetch('http://127.0.0.1:4382/api/state?trial=02-expedition')).json();
  assert.equal(results.slice(0,2).filter(r=>r.result.ok).length,1,'Exactly one competing mission should commit');
  assert(results[2].result.ok,'The independent counter top-up should commute');
  assert.equal(state.state.stock.radio.available,1);assert.equal(Object.keys(state.state.ledger).length,1);
  for(const p of Object.values(state.state.projects))assert(p.available>=0);
  const report={ok:true,clients:3,transport:'three isolated Chromium contexts, concurrent fetch with one captured snapshot',elapsedMs:Date.now()-started,results:results.map((r,i)=>({action:commands[i].action,id:commands[i].args.id,result:r.result,durationMs:r.durationMs})),state:state.state};
  fs.writeFileSync('evidence/concurrent-clients.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
 }finally{if(browser)await browser.close();proc.kill();}
})().catch(e=>{console.error(e);process.exit(1)});
