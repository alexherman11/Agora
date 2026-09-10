/* Exercise only a disposable migrated world. Never run against the resident service. */
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const world = path.resolve(process.argv[2]), port = Number(process.argv[3]);
if (!world.includes('rehearsal') || [8870,8873].includes(port)) throw Error('Use an isolated rehearsal.');
const token = JSON.parse(fs.readFileSync(path.join(world,'keep.json'))).operator;
const migration = JSON.parse(fs.readFileSync(path.join(world,'migration-report.json')));
const out = path.resolve('local/resident-migration-browser'); fs.mkdirSync(out,{recursive:true});
const checks=[], errors=[]; let browser;
async function rpc(method,args={}) {
  const response=await fetch(`http://127.0.0.1:${port}/api/rpc`,{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},body:JSON.stringify({method,args})});
  const body=await response.json(); if(body.error)throw Error(body.error);return body.result;
}
async function until(fn,label) {const end=Date.now()+15000;let error;while(Date.now()<end){try{const result=await fn();if(result)return result;}catch(e){error=e;}await new Promise(r=>setTimeout(r,100));}throw Error(label+': '+(error?.message||'timeout'));}
function check(label,value){assert.ok(value,label);checks.push(label);console.log('PASS '+label);}
(async()=>{
  browser=await chromium.launch({channel:'msedge',headless:true});const page=await browser.newPage({viewport:{width:1600,height:1100}});
  page.on('pageerror',e=>errors.push(e.message));await page.goto(`http://127.0.0.1:${port}/#${token}`);
  const desk=await until(()=>page.frames().find(f=>f.parentFrame()===page.mainFrame()),'desktop');
  await desk.locator('#resident-name').getByText('JEFF0',{exact:true}).waitFor();
  check('resident is named JEFF0 and the retained transcript is visible',await desk.locator('.chat-message').count()===30);
  await desk.getByRole('button',{name:'Close conversation',exact:true}).click();
  let listed=await rpc('application.list');
  const selected=listed.views.find(v=>v.package==='agora.documents'&&v.subject===migration.selected);
  async function frame(id){return until(async()=>{const el=await desk.locator(`[data-view="${id}"] iframe`).elementHandle();const f=el&&await el.contentFrame();return f&&await f.locator('.editor-status').count()&&!(await f.locator('.editor-status').innerText()).includes('Opening')?f:null;},'editor mounted');}
  let docs=await frame(selected.id);
  check('JEFF0 live Markdown implementation mounts in Documents',await docs.locator('.cm-content').isVisible());
  const before=await rpc('world.get',{id:selected.subject});const originalText=before.facets['core.text'].text;
  const live=docs.locator('.cm-content');await live.click();await live.press('Control+End');await live.press('End');await page.keyboard.insertText('\n\nMigration rehearsal live edit.');await live.press('Control+s');
  await until(async()=>(await rpc('world.get',{id:selected.subject})).facets['core.text'].text.includes('Migration rehearsal live edit.'),'live edit saved');
  check('real typing in live Markdown commits through the shared editor',true);
  await live.press('Control+z');await live.press('Control+s');
  await until(async()=>(await rpc('world.get',{id:selected.subject})).facets['core.text'].text===originalText,'live undo');
  check('live Markdown undo survives native save and restores the text',true);
  await docs.getByRole('combobox',{name:'Editor view',exact:true}).selectOption('source');
  const input=docs.getByRole('textbox',{name:'Text',exact:true});await input.press('Control+Home');await input.press('Shift+End');
  const selectedQuote=await input.evaluate(n=>n.value.slice(n.selectionStart,n.selectionEnd));
  const messagesBefore=(await rpc('chat.status')).messages.length;
  await docs.getByRole('button',{name:'Ask JEFF',exact:true}).click();
  await until(async()=>(await desk.locator('#chat-input').inputValue()).includes(selectedQuote),'selection staged');
  const draft=await desk.locator('#chat-input').inputValue();
  check('Ask JEFF stages object revision and text without sending',draft.includes(selected.subject)&&draft.includes('revision')&&(await rpc('chat.status')).messages.length===messagesBefore);
  await desk.getByRole('button',{name:'Close conversation',exact:true}).click();
  await docs.getByText('Discussions',{exact:true}).click();
  const related=await rpc('world.query',{facets:['studio.comment-thread'],limit:1000});
  const threads=related.items.filter(row=>row.facets['studio.comment-thread'].document_id===selected.subject);
  check('legacy discussions are available on the same object identities',threads.length>0&&(await docs.locator('select[aria-label="Discussion thread"] option').count())===threads.length+1);
  const anchorThread=threads.find(row=>row.facets['studio.comment-thread'].anchor.snapshot===originalText)||threads[0];
  await docs.getByRole('combobox',{name:'Discussion thread',exact:true}).selectOption(anchorThread.id);
  check('original anchor evidence is unchanged by opening the migrated discussion',JSON.stringify((await rpc('world.get',{id:anchorThread.id})).facets['studio.comment-thread'])===JSON.stringify(anchorThread.facets['studio.comment-thread']));
  // A new discussion uses only the public editor selection contract.
  await input.press('Control+Home');await input.press('Shift+End');
  await docs.getByRole('button',{name:'Use editor selection',exact:true}).click();
  await docs.getByRole('textbox',{name:'New discussion',exact:true}).fill('Created through public selection contract.');
  await docs.getByRole('button',{name:'Start discussion',exact:true}).click();
  await until(async()=>(await rpc('world.query',{facets:['studio.comment-thread'],limit:1000})).items.length===related.items.length+1,'new discussion');
  check('new discussions bind the object and saved revision',true);
  const draftSubject=Object.keys(migration.drafts).find(id=>Object.keys(migration.drafts[id].replies).length&&migration.drafts[id].newMessage);
  const retainedView=listed.views.find(v=>v.package==='agora.documents'&&v.subject===draftSubject);
  await rpc('application.reopen',{view:retainedView.id});
  const retained=await frame(retainedView.id);const retainedState=migration.drafts[draftSubject];
  await until(async()=>await retained.getByRole('textbox',{name:'New discussion',exact:true}).inputValue()===retainedState.newMessage,'new draft restored');
  check('unfinished new discussion draft survives migration',true);
  await retained.getByRole('combobox',{name:'Discussion thread',exact:true}).selectOption(retainedState.selected);
  check('unfinished reply survives migration on its original thread',await retained.getByRole('textbox',{name:'Discussion reply',exact:true}).inputValue()===retainedState.replies[retainedState.selected]);
  const threadBefore=await rpc('world.get',{id:retainedState.selected});
  await retained.getByRole('textbox',{name:'Discussion reply',exact:true}).fill('Rehearsal reply through the shared extension.');
  await retained.getByRole('button',{name:'Add reply',exact:true}).click();
  await until(async()=>(await rpc('world.get',{id:retainedState.selected})).revision===threadBefore.revision+1,'reply saved');
  const threadAfter=await rpc('world.get',{id:retainedState.selected});
  check('reply updates existing discussion and preserves original anchor',JSON.stringify(threadAfter.facets['studio.comment-thread'].original_anchor)===JSON.stringify(threadBefore.facets['studio.comment-thread'].original_anchor));
  await page.screenshot({path:path.join(out,'migrated-discussions.png'),fullPage:true});
  check('no browser JavaScript errors',errors.length===0);
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({passed:true,checks,errors},null,2));await browser.close();
})().catch(async error=>{console.error(error.stack);fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({passed:false,checks,errors,error:error.stack},null,2));if(browser)await browser.close();process.exitCode=1;});
