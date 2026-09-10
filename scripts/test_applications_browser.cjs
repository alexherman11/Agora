/* Real-browser acceptance for the isolated application world. Never targets the active Desk. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const world = path.resolve(process.argv[2] || 'worlds/application-browser-test');
const output = path.resolve(process.argv[3] || 'local/application-browser-evidence');
const ready = JSON.parse(fs.readFileSync(path.join(world, 'application-ready.json')));
if (ready.port === 8870) throw Error('Refusing to target the active Desk port.');
const token = JSON.parse(fs.readFileSync(path.join(world, 'keep.json'))).operator;
const base = `http://127.0.0.1:${ready.port}`;
fs.mkdirSync(output, {recursive: true});
const checks = [], errors = [];
async function rpc(method, args = {}) {
  const response = await fetch(base + '/api/rpc', {method: 'POST', headers: {'Content-Type':'application/json', Authorization:'Bearer ' + token}, body: JSON.stringify({method,args})});
  const value = await response.json(); if (!response.ok || value.error) throw Error(value.error || String(response.status)); return value.result;
}
async function eventually(fn, description, timeout=12000) {
  const deadline = Date.now() + timeout; let failure;
  while (Date.now() < deadline) { try { const result = await fn(); if (result) return result; } catch (error) { failure = error; } await new Promise(resolve => setTimeout(resolve, 100)); }
  throw Error(description + (failure ? ': ' + failure.message : ''));
}
function check(name, condition) { assert.ok(condition, name); checks.push(name); console.log('PASS ' + name); }
let browser;
(async () => {
  browser = await chromium.launch({channel: 'msedge', headless: true});
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}, acceptDownloads: true});
  const page = await context.newPage();
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(base + '/#' + token);
  let desk;
  await eventually(async () => { desk = page.frames().find(f => f.parentFrame() === page.mainFrame()); return desk && await desk.locator('.application-window').count() === 3; }, 'Three application appearances mount');
  const initial = await rpc('application.list');
  const sharedNote = initial.views.find(v => v.package === 'agora.notes' && v.subject === 'example.shared');
  const sharedDoc = initial.views.find(v => v.package === 'agora.documents' && v.subject === 'example.shared');
  const scratch = initial.views.find(v => v.package === 'agora.notes' && v.subject === 'example.scratch');
  const windowFor = id => desk.locator(`[data-view="${id}"]`);
  async function frameFor(id) {
    return eventually(async () => {
      const element = await windowFor(id).locator('iframe').elementHandle();
      const frame = element && await element.contentFrame();
      return frame && await frame.getByRole('textbox', {name: 'Text', exact:true}).isEnabled() ? frame : null;
    }, 'Application editor becomes ready');
  }
  let notes = await frameFor(sharedNote.id), docs = await frameFor(sharedDoc.id);
  const notesText = () => notes.getByRole('textbox', {name:'Text', exact:true});
  const docsText = () => docs.getByRole('textbox', {name:'Text', exact:true});
  check('separate browser frames display one native subject', notes !== docs && sharedNote.subject === sharedDoc.subject);
  await page.screenshot({path: path.join(output, 'initial-desktop.png'), fullPage: true});
  const boundary = await notes.evaluate(async () => {
    let parentDOM = false; try { void parent.document.body; parentDOM = true; } catch {}
    const attempt = async (method,args) => { try { await AgoraApp.request(method,args); return true; } catch { return false; } };
    return {parentDOM, foreign: await attempt('read',{id:'example.scratch'}), guest: await attempt('guest.execute',{command:'true'}), management: await attempt('application.open',{package:'agora.documents'})};
  });
  check('app cannot access parent DOM, another subject, guest execution or management', Object.values(boundary).every(v => v === false));
  const sharedText = 'Shared phrase for annotation.\n\nBoth applications edit the same object.';
  await notesText().fill(sharedText); await notesText().press('Control+s');
  await eventually(async () => (await rpc('world.get',{id:'example.shared'})).facets['core.text'].text === sharedText, 'Note commits native text');
  await eventually(async () => await docsText().inputValue() === sharedText, 'Documents receives note edit');
  check('typing in Notes updates Documents without copying content', await docsText().inputValue() === sharedText);
  await notesText().press('Control+Home'); await notesText().press('Shift+End');
  await notes.getByText('Annotations', {exact:true}).click();
  await notes.getByRole('textbox', {name:'New annotation', exact:true}).fill('This comment follows the object.');
  await notes.getByRole('button', {name:'Attach to selection', exact:true}).click();
  await eventually(async () => (await rpc('world.get',{id:'example.shared'})).facets['text.annotations']?.threads?.length === 1, 'Annotation commits to shared object');
  await docs.getByText('Annotations', {exact:true}).click();
  await docs.getByText('This comment follows the object.', {exact:true}).waitFor();
  check('the same annotation extension works in both applications', await docs.getByText('This comment follows the object.', {exact:true}).isVisible());
  await docs.getByRole('button', {name:'Show text', exact:true}).click();
  const selectedBefore = await docsText().evaluate(el => [el.selectionStart, el.selectionEnd]);
  await new Promise(resolve => setTimeout(resolve, 3000));
  check('selection survives background data refresh', JSON.stringify(await docsText().evaluate(el => [el.selectionStart,el.selectionEnd])) === JSON.stringify(selectedBefore));
  await Promise.all([notesText().fill('First writer wins this conflict.'), docsText().fill('Second writer draft must survive.')]);
  await notesText().press('Control+s');
  await eventually(async () => (await rpc('world.get',{id:'example.shared'})).facets['core.text'].text === 'First writer wins this conflict.', 'First editor wins');
  await docsText().press('Control+s');
  await eventually(async () => (await docs.locator('.editor-status').innerText()).includes('conflict'), 'Second editor reports conflict');
  check('a conflicting editor retains its draft instead of overwriting', await docsText().inputValue() === 'Second writer draft must survive.');
  await windowFor(sharedDoc.id).getByRole('button', {name:'Close view', exact:true}).click();
  await eventually(async () => await windowFor(sharedDoc.id).count() === 0, 'Document view closes');
  check('closing a conflicting view preserves native content', (await rpc('world.get',{id:'example.shared'})).facets['core.text'].text === 'First writer wins this conflict.');
  await desk.locator('#closed').evaluate(el => { el.open = true; });
  await desk.locator('#closed-views').getByRole('button', {name:'Documents · Application field notes', exact:true}).click();
  docs = await frameFor(sharedDoc.id);
  check('reopening restores the conflicting draft', await docsText().inputValue() === 'Second writer draft must survive.');
  await docs.getByRole('button', {name:'Use saved text', exact:true}).click();
  await eventually(async () => await docsText().inputValue() === 'First writer wins this conflict.', 'Resolve conflict explicitly');
  const continuity = await docs.evaluate(() => window.continuityMarker = crypto.randomUUID());
  const originalScratchFrame = await frameFor(scratch.id);
  const originalScratchMarker = await originalScratchFrame.evaluate(() => window.continuityMarker = crypto.randomUUID());
  const sourceObject = await rpc('package.get',{id:'agora.notes'});
  const source = sourceObject.facets['agora.package'];
  source.files['app.js'] += '\ndocument.body.dataset.release = "two";';
  await rpc('package.save',{id:source.id,expected_revision:sourceObject.revision,files:source.files,manifest:source.manifest});
  const built = await rpc('package.build',{id:source.id,expected_revision:sourceObject.revision+1});
  await rpc('package.install',built.install_args);
  await windowFor(sharedNote.id).getByRole('button', {name:'Update', exact:true}).waitFor();
  check('installation does not silently replace an open view', await notes.evaluate(() => document.body.dataset.release) === undefined);
  await windowFor(sharedNote.id).getByRole('button', {name:'Update', exact:true}).click();
  await eventually(async () => { notes = await frameFor(sharedNote.id); return await notes.evaluate(() => document.body.dataset.release) === 'two'; }, 'One note view adopts update');
  check('updating one view preserves other applications and sibling instances',
    await docs.evaluate(() => window.continuityMarker) === continuity && await originalScratchFrame.evaluate(() => window.continuityMarker) === originalScratchMarker);
  const downloadWait = page.waitForEvent('download');
  await desk.locator('.application[data-package="agora.notes"]').getByRole('button',{name:'Export',exact:true}).click();
  const download = await downloadWait;
  const exportedFile = path.join(output, 'notes.agora-app.json'); await download.saveAs(exportedFile);
  const exportedText = fs.readFileSync(exportedFile, 'utf8');
  const exported = JSON.parse(exportedText);
  check('browser exports a portable application without content, drafts or credentials', exported.format === 'agora.application-bundle/1' && !exportedText.includes('Second writer draft must survive.') && !exportedText.includes(token) && !exportedText.includes('example.shared'));
  const nativeBeforeRemove = await rpc('world.get',{id:'example.shared'});
  await desk.locator('.application[data-package="agora.notes"]').getByRole('button',{name:'Remove',exact:true}).click();
  await eventually(async () => await desk.locator('.application-window[data-package="agora.notes"]').count() === 0, 'Notes views removed');
  check('removing Notes preserves shared content and the Documents view', JSON.stringify(await rpc('world.get',{id:'example.shared'})) === JSON.stringify(nativeBeforeRemove) && await docs.evaluate(() => window.continuityMarker) === continuity);
  await desk.locator('#bundle-file').setInputFiles(exportedFile);
  await eventually(async () => await desk.locator('.application[data-package="agora.notes"]').count() === 1, 'Reimport exported application');
  await desk.locator('#closed').evaluate(el => { el.open = true; });
  await desk.locator('#closed-views').getByRole('button',{name:'Notes · Application field notes',exact:true}).click();
  notes = await frameFor(sharedNote.id);
  check('an imported application reopens on the same retained object', await notesText().inputValue() === nativeBeforeRemove.facets['core.text'].text);
  await page.reload();
  await eventually(async () => { desk = page.frames().find(f => f.parentFrame() === page.mainFrame()); return desk && await desk.locator('.application-window').count() === 2; }, 'Open views restore on browser reload');
  notes = await frameFor(sharedNote.id); docs = await frameFor(sharedDoc.id);
  check('browser reload restores independent views and shared content', await notesText().inputValue() === await docsText().inputValue());
  await page.setViewportSize({width: 390, height: 844});
  await new Promise(resolve => setTimeout(resolve, 300));
  const noOverflow = await desk.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1);
  const childWidths = await Promise.all([notes, docs].map(frame => frame.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)));
  check('desktop and both applications fit a narrow viewport', noOverflow && childWidths.every(Boolean));
  await page.screenshot({path:path.join(output,'mobile.png'),fullPage:true});
  await page.setViewportSize({width:1440,height:1000});
  await page.screenshot({path:path.join(output,'final-desktop.png'),fullPage:true});
  check('no browser JavaScript errors', errors.length === 0);
  fs.writeFileSync(path.join(output,'report.json'),JSON.stringify({passed:true,checks,errors,world,port:ready.port},null,2));
  console.log(JSON.stringify({passed:checks.length,evidence:output}));
  await browser.close();
})().catch(async error => {
  fs.writeFileSync(path.join(output,'report.json'),JSON.stringify({passed:false,checks,errors,error:error.stack,world,port:ready.port},null,2));
  console.error(error.stack); if (browser) await browser.close(); process.exitCode=1;
});
