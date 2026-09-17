/* Two browser instances against a disposable world; never targets a resident. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const world=path.resolve(process.argv[2] || 'local/live-update-test');
const ready=JSON.parse(fs.readFileSync(path.join(world,'application-ready.json')));
if([8870,8872,8873,8874].includes(ready.port))throw Error('Refusing resident port');
const token=JSON.parse(fs.readFileSync(path.join(world,'keep.json'))).operator;
const base='http://127.0.0.1:'+ready.port;
const checks=[];
async function rpc(method,args={}){
 const r=await fetch(base+'/api/rpc',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},body:JSON.stringify({method,args})});
 const v=await r.json();if(!r.ok||v.error)throw Error(v.error||r.status);return v.result;
}
async function until(fn,label,timeout=35000){const end=Date.now()+timeout;let error;while(Date.now()<end){try{if(await fn())return;}catch(e){error=e;}await new Promise(r=>setTimeout(r,100));}throw Error(label+': '+(error?.message||'timed out'));}
function pass(name){checks.push(name);console.log('PASS '+name);}
async function publish(id,edit){
 const p=await rpc('package.get',{id});const source=p.facets['agora.package'];edit(source.files,source.manifest);
 await rpc('package.save',{id,expected_revision:p.revision,files:source.files,manifest:source.manifest});
 const b=await rpc('package.build',{id,expected_revision:p.revision+1});await rpc('package.install',b.install_args);
}
let browser;
(async()=>{
 // Each run gets a fresh subject/view; failed-test drafts remain recoverable.
 for(const view of (await rpc('application.list')).views.filter(v=>v.open))await rpc('application.close',{view:view.id});
 const doc=await rpc('application.open',{package:'agora.documents'});
 const run=Date.now().toString(36),appMarker='app-'+run,shellMarker='shell-'+run,retryMarker='retry-'+run;
 // Delay fixture autosave so actual input remains an unsaved draft during publication.
 await publish('agora.documents',files=>{files['shared/editor.js']=files['shared/editor.js'].replaceAll(', 550)',', 60000)');});
 browser=await chromium.launch({channel:'msedge',headless:true});
 const a=await browser.newPage({viewport:{width:1440,height:1000}}),b=await browser.newPage({viewport:{width:1440,height:1000}});
 for(const p of [a,b])p.setDefaultTimeout(2000);
 const errors=[];for(const p of [a,b])p.on('pageerror',e=>errors.push(e.message));
 await a.goto(base+'/#'+token);await b.goto(base+'/#'+token);
 const desk=p=>p.frames().find(f=>f.parentFrame()===p.mainFrame());
 async function editor(p){const handle=await desk(p).locator('[data-view="'+doc.id+'"] iframe').elementHandle();return handle.contentFrame();}
 for(const p of [a,b]){
  await until(async()=>!(await (await editor(p)).locator('.editor-input').isDisabled()),'editor ready');
  await (await editor(p)).getByLabel('Editor view',{exact:true}).selectOption('source');
 }
 const lease=(await rpc('application.surface',{view:doc.id})).context.lease;
 const draft='Unsaved human draft survives publication.\n\nSecond paragraph.';
 await (await editor(a)).getByRole('textbox',{name:'Text',exact:true}).fill(draft);
 await until(async()=>Object.values(await a.evaluate(()=>({...sessionStorage}))).some(s=>s.includes('Unsaved human draft')),'local draft retained');
 await publish('agora.documents',files=>{files['app.js']+='\ndocument.body.dataset.updateProbe='+JSON.stringify(appMarker)+';';});
 for(const [p,name] of [[a,'human'],[b,'observer']]){
   await until(async()=>await (await editor(p)).evaluate(()=>document.body.dataset.updateProbe)===appMarker,name+' auto app update');
 }
 assert.equal(await (await editor(a)).getByRole('textbox',{name:'Text',exact:true}).inputValue(),draft);
 assert.equal((await rpc('world.get',{id:doc.subject})).facets['core.text'].text,draft);
 assert.equal((await rpc('application.surface',{view:doc.id})).context.lease,lease);
 pass('Application publication reaches both browsers automatically and retains actual typed draft');
 // A same-build refresh by the observer must not break human save/read.
 await rpc('application.refresh',{view:doc.id});
 assert.equal(await (await editor(a)).evaluate(()=>AgoraApp.request('read').then(o=>o.facets['core.text'].text)),draft);
 pass('Same-build refresh does not revoke the other browser');
 // Prepare an explicit conflict; its local state must survive a clean observer flush.
 const conflictDraft='Human conflict draft must remain local.';
 await (await editor(a)).getByRole('textbox',{name:'Text',exact:true}).fill(conflictDraft);
 const obj=await rpc('world.get',{id:doc.subject});
 await rpc('world.transact',{changes:[{id:obj.id,expected_revision:obj.revision,facets:{'core.text':{text:'A separate accepted native edit.'}}}]});
 await (await editor(a)).getByRole('button',{name:'Save',exact:true}).click();
 await until(async()=>(await (await editor(a)).locator('.editor-error').innerText()).includes('Conflict'),'conflict displayed');
 await (await editor(b)).evaluate(async()=>{const x=await AgoraApp.request('state.get');await AgoraApp.request('state.set',{state:{...x.state,editor:{...x.state.editor,dirty:false,text:'A separate accepted native edit.'}}});});
 await desk(a).locator('#chat-input').fill('Unsent chat draft — do not send');
 await publish('agora.shell',files=>{files['desktop.js']+='\ndocument.body.dataset.updateProbe='+JSON.stringify(shellMarker)+';';});
 for(const p of [a,b])await until(async()=>await desk(p).evaluate(()=>document.body.dataset.updateProbe)===shellMarker,'shell publication');
 await until(async()=>!(await (await editor(a)).locator('.editor-input').isDisabled()),'editor restored after shell update');
 await until(async()=>await desk(a).locator('#chat-input').inputValue()==='Unsent chat draft — do not send','chat draft restored');
 assert.equal(await (await editor(a)).getByRole('textbox',{name:'Text',exact:true}).inputValue(),conflictDraft);
 assert.equal(await desk(a).locator('#chat-input').inputValue(),'Unsent chat draft — do not send');
 assert.equal((await rpc('world.get',{id:doc.subject})).facets['core.text'].text,'A separate accepted native edit.');
 pass('Shell publication retains conflict draft and unsent chat without replacing native content');
 // Real blocked handshake: refuse once, then recover without clicking Reload.
 await desk(a).evaluate(()=>{let once=true;AgoraDesktop.onFlush(()=>{if(once){once=false;throw Error('Temporary fixture save blocker');}});});
 await publish('agora.shell',files=>{files['desktop.js']+='\ndocument.body.dataset.updateProbe='+JSON.stringify(retryMarker)+';';});
 await until(async()=>(await a.locator('#status').innerText()).includes('Temporary fixture save blocker'),'visible blocker');
 await until(async()=>await desk(a).evaluate(()=>document.body.dataset.updateProbe)===retryMarker,'automatic retry');
 pass('Blocked publication reports the cause and retries automatically');
 assert.deepEqual(errors,[]);pass('No browser JavaScript errors');
 fs.writeFileSync(path.join(world,'browser-test-results.json'),JSON.stringify({checks},null,2));
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();});
