const {chromium}=require('C:/Users/Alex/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict'),{spawn}=require('node:child_process');
(async()=>{
 const dataDir=fs.mkdtempSync(path.join(os.tmpdir(),'tessera-input-'));
 const proc=spawn(process.execPath,['server.mjs'],{cwd:__dirname,windowsHide:true,env:{...process.env,TESSERA_PORT:'4387',TESSERA_DATA_DIR:dataDir}});let browser,page;
 const report={ok:false,checks:[],errors:[],presses:[]};
 try{
  await new Promise((resolve,reject)=>{proc.stdout.on('data',d=>{if(String(d).includes('listening'))resolve()});proc.on('error',reject)});
  browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
  page=await browser.newPage({viewport:{width:1277,height:1216}});page.setDefaultTimeout(5000);page.on('pageerror',e=>report.errors.push(e.message));
  for(const trial of ['05-kinetic-loom','06-live-sandbox']){
   await page.goto(`http://127.0.0.1:4387/scene?trial=${trial}`);await page.waitForFunction(()=>window.tessera);
   for(const duration of [120,250,500]){
    await page.locator('[data-view="instrument.start"]').click();await page.waitForFunction(()=>window.tessera.saved.state.simulation.main.running);
    const pause=page.locator('[data-view="instrument.pause"]'),rect=await pause.boundingBox();
    await page.mouse.move(rect.x+rect.width/2,rect.y+rect.height/2);await page.mouse.down();
    const held=await pause.elementHandle(),before=await page.evaluate(()=>window.tessera.saved.state.simulation.main.steps);
    await page.waitForTimeout(duration);assert(await held.evaluate(n=>n.isConnected),'Native control was replaced during a held press');
    assert((await page.evaluate(()=>window.tessera.saved.state.simulation.main.steps))>before,'Simulation should advance while its display preserves the held control');
    await page.mouse.up();await page.waitForFunction(()=>!window.tessera.saved.state.simulation.main.running);
    const steps=await page.evaluate(()=>window.tessera.saved.state.simulation.main.steps);await page.waitForTimeout(150);
    assert.equal(await page.evaluate(()=>window.tessera.saved.state.simulation.main.steps),steps);report.presses.push({trial,durationMs:duration,ok:true});
   }
   report.checks.push(`${trial}: Pause works with 120/250/500ms mouse holds at 1277×1216`);
   const grip=await page.locator('[data-view="instrument.grip"]').boundingBox(),beforeDesk=await page.locator('[data-view="instrument.inspector"]').boundingBox();
   await page.mouse.move(grip.x+80,grip.y+12);await page.mouse.down();await page.mouse.move(grip.x+250,grip.y-248,{steps:20});await page.mouse.up();
   await page.waitForFunction(()=>window.tessera.saved.state.instrument.main.floated===true);
   const afterDesk=await page.locator('[data-view="instrument.inspector"]').boundingBox();assert(Math.abs(afterDesk.x-beforeDesk.x-170)<1);assert(Math.abs(afterDesk.y-beforeDesk.y+260)<1);
   report.checks.push(`${trial}: Signal Desk follows pointer and persists its new position below the old width threshold`);
   await page.reload();await page.waitForFunction(()=>window.tessera);assert.equal(await page.evaluate(()=>window.tessera.saved.state.instrument.main.floated),true);
   const restored=await page.locator('[data-view="instrument.inspector"]').boundingBox();assert(Math.abs(restored.x-afterDesk.x)<1&&Math.abs(restored.y-afterDesk.y)<1);
   report.checks.push(`${trial}: Reload preserves dragged desk placement`);await page.screenshot({path:`evidence/${trial}-input-fixed.png`});
  }
  report.ok=report.errors.length===0;
 }catch(e){report.failure=e.message;if(page)await page.screenshot({path:'evidence/input-failure.png'});throw e;}
 finally{fs.writeFileSync('evidence/input-regression.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));if(browser)await browser.close();proc.kill();}
})().catch(e=>{console.error(e);process.exit(1)});
