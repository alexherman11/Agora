/* A generic authored desktop. Application names and implementations come from the registry. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const node = (tag, cls, text) => { const el = document.createElement(tag); if (cls) el.className = cls; if (text !== undefined) el.textContent = text; return el; };
  const pending = new Map(), windows = new Map(), flushers = new Set();
  let registry = [], subjects = [], selected = '', syncing = false, syncAgain = false, nextZ = 2, stageSelection;
  function notice(text) { $('notice').hidden = !text; $('notice').textContent = text; }
  function call(method, args = {}) {
    return new Promise((resolve, reject) => {
      const id = crypto.randomUUID(), timer = setTimeout(() => { pending.delete(id); reject(new Error('The native gateway did not respond.')); }, 20000);
      pending.set(id, {resolve, reject, timer}); parent.postMessage({agora: true, id, method, args}, '*');
    });
  }
  window.AgoraDesktop = Object.freeze({request: call, onFlush(handler) { flushers.add(handler); return () => flushers.delete(handler); }, selectionHandler(handler) { stageSelection = handler; }});
  const title = subject => subjects.find(o => o.id === subject)?.facets['core.title']?.text || 'Untitled';
  const app = packageId => registry.find(a => a.package === packageId);
  const compatible = (application, subject) => application.contract.accepts.every(f => subjects.find(o => o.id === subject)?.facets[f]);
  function send(entry, value) { entry.frame.contentWindow.postMessage({agoraApp: true, ...value}, '*'); }
  function thaw(entry) { entry.frame.inert = false; }
  function flush(entry) {
    return new Promise((resolve, reject) => {
      if (!entry.context || !entry.ready) { reject(new Error('Wait for the application to finish opening.')); return; }
      entry.frame.inert = true;
      const id = crypto.randomUUID(), timer = setTimeout(() => { entry.flushes.delete(id); thaw(entry); reject(new Error('The application did not confirm its drafts were retained.')); }, 12000);
      entry.flushes.set(id, {resolve, reject, timer}); send(entry, {type: 'flush', id});
    });
  }
  async function open(packageId, subject) {
    try { const result = await call('application.open', {package: packageId, ...(subject ? {subject} : {})}); selected = result.subject; await sync(); }
    catch (error) { notice(error.message); }
  }
  async function close(entry) {
    try { await flush(entry); await call('application.close', {view: entry.info.id}); await sync(); }
    catch (error) { thaw(entry); notice(error.message); }
  }
  function applyBounds(entry) {
    const bounds = entry.info.bounds;
    Object.assign(entry.node.style, {left: bounds.x + 'px', top: bounds.y + 'px', width: bounds.width + 'px', height: bounds.height + 'px'});
    sizeBoard();
  }
  function sizeBoard() {
    if (matchMedia('(max-width:760px)').matches) { $('board').style.height = ''; return; }
    let bottom = 400; for (const entry of windows.values()) bottom = Math.max(bottom, entry.info.bounds.y + entry.info.bounds.height + 28);
    $('board').style.height = bottom + 'px';
  }
  function gesture(entry, handle, resize = false) {
    handle.addEventListener('pointerdown', event => {
      if (event.button !== 0 || matchMedia('(max-width:760px)').matches) return;
      event.preventDefault(); handle.setPointerCapture(event.pointerId); entry.node.style.zIndex = ++nextZ;
      const initial = {...entry.info.bounds}, x = event.clientX, y = event.clientY;
      entry.gesture = {initial};
      const move = event => {
        if (resize) entry.info.bounds = {...initial, width: Math.max(220, Math.min(1400, initial.width + event.clientX - x)), height: Math.max(180, Math.min(1200, initial.height + event.clientY - y))};
        else entry.info.bounds = {...initial, x: Math.max(0, initial.x + event.clientX - x), y: Math.max(0, initial.y + event.clientY - y)};
        applyBounds(entry);
      };
      const finish = async event => {
        handle.removeEventListener('pointermove', move); handle.removeEventListener('pointerup', finish); handle.removeEventListener('pointercancel', cancel);
        if (handle.hasPointerCapture(event.pointerId)) handle.releasePointerCapture(event.pointerId);
        entry.gesture = null;
        try { await call('application.position', {view: entry.info.id, bounds: entry.info.bounds}); } catch (error) { entry.info.bounds = initial; applyBounds(entry); notice(error.message); }
      };
      const cancel = event => { entry.info.bounds = initial; applyBounds(entry); finish(event); };
      handle.addEventListener('pointermove', move); handle.addEventListener('pointerup', finish); handle.addEventListener('pointercancel', cancel);
    });
    handle.addEventListener('keydown', async event => {
      const delta = {ArrowLeft: [-1,0], ArrowRight: [1,0], ArrowUp: [0,-1], ArrowDown: [0,1]}[event.key]; if (!delta) return;
      event.preventDefault(); const step = event.shiftKey ? 10 : 1, b = entry.info.bounds;
      const bounds = resize ? {...b, width: Math.max(220, Math.min(1400, b.width + delta[0]*step)), height: Math.max(180, Math.min(1200, b.height + delta[1]*step))} : {...b, x: Math.max(0, b.x + delta[0]*step), y: Math.max(0, b.y + delta[1]*step)};
      try { await call('application.position', {view: entry.info.id, bounds}); entry.info.bounds = bounds; applyBounds(entry); } catch (error) { notice(error.message); }
    });
  }
  async function mount(info, existing) {
    const application = app(info.package); if (!application) return;
    let entry = existing;
    if (!entry) {
      const section = node('section', 'application-window'); section.dataset.view = info.id; section.dataset.package = info.package;
      const header = node('header', 'window-header');
      const handle = node('button', 'drag-handle'); handle.setAttribute('aria-label', 'Move view');
      const openWith = node('select', 'open-with'); openWith.setAttribute('aria-label', 'Open this object with');
      openWith.onchange = () => { const packageId = openWith.value; openWith.value = ''; if (packageId) open(packageId, entry.info.subject); };
      const update = node('button', 'update', 'Update'); update.hidden = true;
      const closeButton = node('button', 'close', '×'); closeButton.setAttribute('aria-label', 'Close view');
      const frame = document.createElement('iframe'); frame.sandbox = 'allow-scripts';
      const loading = node('div', 'window-loading', 'Opening application…');
      const resize = node('button', 'resize-handle'); resize.setAttribute('aria-label', 'Resize view');
      header.append(handle, openWith, update, closeButton); section.append(header, frame, loading, resize); $('board').append(section);
      entry = {info, node: section, frame, handle, openWith, update, loading, flushes: new Map(), inFlight: 0}; windows.set(info.id, entry);
      closeButton.onclick = () => close(entry);
      update.onclick = async () => { try { await flush(entry); await call('application.refresh', {view: entry.info.id}); await sync(); } catch (error) { thaw(entry); notice(error.message); } };
      section.addEventListener('pointerdown', () => { section.style.zIndex = ++nextZ; });
      gesture(entry, handle); gesture(entry, resize, true); applyBounds(entry);
    }
    const surface = await call('application.surface', {view: info.id});
    entry.info = surface.view; entry.context = surface.context; entry.ready = false; entry.loading.hidden = false;
    thaw(entry);
    entry.frame.title = application.name + ': ' + title(info.subject); entry.frame.srcdoc = surface.html;
    applyBounds(entry); return entry;
  }
  function decorate(entry) {
    const application = app(entry.info.package); if (!application) return;
    entry.handle.replaceChildren(document.createTextNode(application.name), node('span', '', title(entry.info.subject)));
    entry.frame.title = application.name + ': ' + title(entry.info.subject);
    entry.update.hidden = entry.info.installation_revision === application.revision;
    const signature = registry.map(a => a.package + ':' + a.revision).join('|');
    if (entry.openWith.dataset.signature !== signature) {
      entry.openWith.replaceChildren(new Option('Open with…', ''));
      for (const a of registry) if (compatible(a, entry.info.subject)) entry.openWith.append(new Option(a.name, a.package));
      entry.openWith.dataset.signature = signature;
    }
  }
  async function exportApp(packageId) {
    try {
      const bundle = await call('application.export', {package: packageId});
      const url = URL.createObjectURL(new Blob([JSON.stringify(bundle, null, 2)], {type: 'application/json'}));
      const link = node('a'); link.href = url; link.download = packageId + '.agora-app.json'; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
      notice('Application exported. Documents and drafts are not included.');
    } catch (error) { notice(error.message); }
  }
  async function removeApp(application) {
    try {
      for (const entry of windows.values()) if (entry.info.package === application.package) await flush(entry);
      await call('application.uninstall', {package: application.package, expected_revision: application.revision});
      await sync(); notice(application.name + ' removed. Your objects and drafts remain in Agora.');
    } catch (error) { for (const entry of windows.values()) if (entry.info.package === application.package) thaw(entry); notice(error.message); }
  }
  function sidebar(views) {
    const appSignature = JSON.stringify([selected, registry.map(a => [a.package, a.revision])]);
    if ($('applications').dataset.signature !== appSignature) {
      $('applications').replaceChildren();
      for (const application of registry) {
        const row = node('section', 'application'); row.dataset.package = application.package; row.append(node('strong', '', application.name));
        const actions = node('div', 'application-actions');
        const create = node('button', '', 'New'); create.onclick = () => open(application.package);
        const reuse = node('button', '', 'Open selected'); reuse.disabled = !selected || !compatible(application, selected); reuse.onclick = () => open(application.package, selected);
        actions.append(create, reuse); row.append(actions);
        const secondary = node('div', 'secondary-actions'); const download = node('button', '', 'Export'); download.onclick = () => exportApp(application.package);
        const remove = node('button', '', 'Remove'); remove.onclick = () => removeApp(application); secondary.append(download, remove); row.append(secondary); $('applications').append(row);
      }
      $('applications').dataset.signature = appSignature;
    }
    const objectSignature = JSON.stringify([selected, subjects.map(o => [o.id, o.facets['core.title']?.text])]);
    if ($('objects').dataset.signature !== objectSignature) {
      $('objects').replaceChildren();
      for (const obj of subjects) {
        const button = node('button', 'object-row' + (obj.id === selected ? ' selected' : ''), title(obj.id)); button.dataset.subject = obj.id;
        button.append(node('small', '', obj.facets['text.format']?.kind || 'text')); button.onclick = () => { selected = obj.id; sidebar(views); };
        $('objects').append(button);
      }
      $('objects').dataset.signature = objectSignature;
    }
    const closed = views.filter(view => !view.open && app(view.package));
    const closedSignature = JSON.stringify(closed.map(v => [v.id, v.package, v.subject]));
    if ($('closed-views').dataset.signature !== closedSignature) {
      $('closed-views').replaceChildren();
      for (const view of closed) { const button = node('button', '', app(view.package).name + ' · ' + title(view.subject)); button.onclick = async () => { try { await call('application.reopen', {view: view.id}); await sync(); } catch (error) { notice(error.message); } }; $('closed-views').append(button); }
      $('closed-views').dataset.signature = closedSignature;
    }
  }
  async function sync() {
    if (syncing) { syncAgain = true; return; } syncing = true;
    try {
      const [status, objects] = await Promise.all([call('application.list'), call('world.query', {facets: ['core.text'], limit: 200})]);
      registry = status.applications; subjects = objects.items.filter(o => !o.id.startsWith('agora.') && !o.facets['core.draft']);
      if (!subjects.some(o => o.id === selected)) selected = subjects[0]?.id || '';
      sidebar(status.views);
      const active = status.views.filter(view => view.open && app(view.package));
      for (const [id, entry] of windows) if (!active.some(view => view.id === id)) { entry.node.remove(); windows.delete(id); }
      for (const info of active) {
        let entry = windows.get(info.id);
        if (!entry || entry.info.build !== info.build) entry = await mount(info, entry);
        if (!entry.gesture) { entry.info = info; applyBounds(entry); } decorate(entry);
      }
      $('view-count').textContent = active.length + ' open views'; $('empty').hidden = !!active.length;
    } catch (error) { notice(error.message); }
    finally { syncing = false; if (syncAgain) { syncAgain = false; queueMicrotask(sync); } }
  }
  window.addEventListener('message', async event => {
    const value = event.data;
    if (event.source === parent && value?.agora === true) {
      if (value.event === 'cancel-reload') { for (const entry of windows.values()) thaw(entry); return; }
      if (value.event === 'changed') { sync(); for (const entry of windows.values()) if (entry.ready) send(entry, {type: 'changed'}); return; }
      if (value.event === 'prepare-reload') {
        try { await Promise.all([...windows.values()].map(flush).concat([...flushers].map(handler => handler()))); parent.postMessage({agora: true, event: 'reload-ready', id: value.id, result: {ready: true}}, '*'); }
        catch (error) { for (const entry of windows.values()) thaw(entry); notice(error.message); parent.postMessage({agora: true, event: 'reload-ready', id: value.id, result: {ready: false}}, '*'); } return;
      }
      const task = pending.get(value.id); if (task) { pending.delete(value.id); clearTimeout(task.timer); if (value.error) task.reject(new Error(value.error)); else task.resolve(value.result); } return;
    }
    if (value?.agoraApp !== true) return;
    const entry = [...windows.values()].find(e => e.frame.contentWindow === event.source); if (!entry) return;
    if (value.type === 'ready') { if (entry.context) { entry.ready = true; entry.loading.hidden = true; send(entry, {type: 'init', context: entry.context}); } return; }
    if (value.lease !== entry.context?.lease) return;
    if (value.type === 'flushed') { const task = entry.flushes.get(value.id); if (task) { entry.flushes.delete(value.id); clearTimeout(task.timer); if (value.ready) task.resolve(); else { thaw(entry); task.reject(new Error(value.error || 'Application did not retain its draft.')); } } return; }
    if (value.type === 'request') {
      if (entry.inFlight >= 8) { send(entry, {type: 'response', id: value.id, error: 'Too many pending application requests.'}); return; }
      entry.inFlight++;
      try {
        let result;
        if (value.method === 'stage-chat') {
          const selection = value.args?.selection;
          const object = await call('application.request', {view: entry.info.id, lease: entry.context.lease, method: 'read', args: {}});
          const text = object.facets['core.text']?.text;
          if (!stageSelection || !selection || selection.subject !== object.id || selection.revision !== object.revision || typeof text !== 'string' || !Number.isInteger(selection.start) || !Number.isInteger(selection.end) || selection.start < 0 || selection.end <= selection.start || selection.end - selection.start > 12000 || selection.end > text.length || !selection.quote?.trim() || text.slice(selection.start, selection.end) !== selection.quote) throw new Error('The selected object or revision changed; select the passage again.');
          const boundary = index => !(index > 0 && /[\uD800-\uDBFF]/.test(text[index - 1]) && /[\uDC00-\uDFFF]/.test(text[index] || ''));
          if (!boundary(selection.start) || !boundary(selection.end)) throw new Error('Select complete characters.');
          await stageSelection({subject: object.id, revision: object.revision, title: object.facets['core.title']?.text || 'Untitled', start: selection.start, end: selection.end, quote: selection.quote});
          result = {staged: true, sent: false};
        } else result = await call('application.request', {view: entry.info.id, lease: entry.context.lease, method: value.method, args: value.args || {}});
        send(entry, {type: 'response', id: value.id, result});
      }
      catch (error) { send(entry, {type: 'response', id: value.id, error: error.message}); }
      finally { entry.inFlight--; }
    }
  });
  $('import').onclick = () => $('bundle-file').click();
  $('bundle-file').onchange = async () => {
    const file = $('bundle-file').files[0]; if (!file) return;
    try {
      if (file.size > 3000000) throw new Error('Application bundle exceeds 3 MB.');
      const bundle = JSON.parse(await file.text());
      const catalog = await call('package.catalog'); const existing = catalog.packages.find(p => p.package_id === bundle.source?.id);
      await call('application.import', {bundle, expected_revision: existing?.source_revision || 0}); await sync();
      notice('Application installed. Existing views can adopt it with Update after retaining their drafts.');
    } catch (error) { notice(error.message); } finally { $('bundle-file').value = ''; }
  };
  window.addEventListener('resize', sizeBoard);
  sync(); setInterval(sync, 2500);
})();
