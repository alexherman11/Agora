/* Existing native discussion objects through the public editor contract. No editor DOM access. */
(() => {
  'use strict';
  const {node, digest} = EditorUtilities, FACET = 'studio.comment-thread';
  const positions = (text, quote) => { const result = []; for (let at = 0; quote && (at = text.indexOf(quote, at)) >= 0; at++) result.push(at); return result; };
  function locate(anchor, text) {
    if (text === anchor.snapshot) return {state: 'attached', start: anchor.start, end: anchor.end};
    const hits = positions(text, anchor.quote);
    if (!hits.length) return {state: 'orphaned'};
    if (hits.length !== 1 || anchor.occurrences !== 1) return {state: 'ambiguous'};
    const start = hits[0], end = start + anchor.quote.length;
    if ((anchor.prefix && !text.slice(0, start).endsWith(anchor.prefix)) || (anchor.suffix && !text.slice(end).startsWith(anchor.suffix))) return {state: 'orphaned'};
    return {state: 'attached', start, end};
  }
  function evidence(selection) {
    const {text, start, end} = selection;
    const boundary = index => !(index > 0 && /[\uD800-\uDBFF]/.test(text[index - 1]) && /[\uDC00-\uDFFF]/.test(text[index] || ''));
    if (!boundary(start) || !boundary(end) || !selection.quote.trim()) throw new Error('Select complete characters and nonempty text.');
    return {convention: 'utf16-code-units', document_revision: selection.revision, start, end,
      quote: selection.quote, prefix: Array.from(text.slice(0, start)).slice(-32).join(''),
      suffix: Array.from(text.slice(end)).slice(0, 32).join(''), snapshot: text,
      sha256: selection.text_hash, occurrences: positions(text, selection.quote).length};
  }
  function message(text) {
    if (!text.trim() || Array.from(text).length > 3000) throw new Error('A discussion message needs 1–3000 characters.');
    return {text, created_at: new Date().toISOString()};
  }
  window.attachDiscussions = editor => {
    const {details, content} = editor.addPanel('Discussions');
    const capture = node('button', '', 'Use editor selection'), selectionLabel = node('p', 'muted', 'Select text to start or reanchor a discussion.');
    capture.onmousedown = event => event.preventDefault();
    const newMessage = node('textarea'); newMessage.setAttribute('aria-label', 'New discussion'); newMessage.placeholder = 'Start a discussion on the selected text'; newMessage.maxLength = 6000;
    const create = node('button', '', 'Start discussion'), status = node('p', 'annotation-status'); status.setAttribute('role', 'status');
    const picker = node('select'); picker.setAttribute('aria-label', 'Discussion thread');
    const detail = node('section'), quote = node('blockquote'), stateLabel = node('p', 'muted');
    const jump = node('button', '', 'Go to anchor'), resolve = node('button', '', 'Resolve'), reanchor = node('button', '', 'Reanchor to selection');
    const original = node('details'); original.append(node('summary', '', 'Original anchor evidence')); const originalText = node('pre'); original.append(originalText);
    const messages = node('ol'), reply = node('textarea'); reply.setAttribute('aria-label', 'Discussion reply'); reply.placeholder = 'Reply to this thread'; reply.maxLength = 6000;
    const send = node('button', '', 'Add reply'); detail.append(quote, stateLabel, jump, resolve, reanchor, original, messages, reply, send);
    content.append(capture, selectionLabel, newMessage, create, status, picker, detail);
    let rows = [], selected = '', captureValue = null, replies = {}, initialized = false, busy = null, refreshing = false, drawn = '';
    function retain() { if (initialized) editor.extensionState('discussions', {newMessage: newMessage.value, replies: {...replies, ...(selected ? {[selected]: reply.value} : {})}, selected, open: details.open}); }
    newMessage.oninput = retain; reply.oninput = () => { if (selected) replies[selected] = reply.value; retain(); }; details.ontoggle = retain;
    function current() { return rows.find(row => row.id === selected); }
    function render() {
      const object = current(), snapshot = editor.snapshot(); detail.hidden = !object;
      if (!object) return;
      const thread = object.facets[FACET], location = locate(thread.anchor, snapshot.text);
      stateLabel.textContent = thread.status + ' · ' + location.state + (snapshot.dirty ? ' · unsaved draft' : '');
      quote.textContent = thread.anchor.quote; jump.disabled = location.state !== 'attached'; resolve.textContent = thread.status === 'open' ? 'Resolve' : 'Reopen';
      if (drawn !== object.id + ':' + object.revision) {
        drawn = object.id + ':' + object.revision;
        messages.replaceChildren(...thread.messages.map(m => node('li', '', m.text + ' — ' + m.created_at)));
        originalText.textContent = JSON.stringify(thread.original_anchor, null, 2);
      }
    }
    async function refresh() {
      if (!initialized || refreshing) return; refreshing = true;
      try {
        const result = await editor.related('discussions', 'query'); rows = result.items;
        const signature = JSON.stringify(rows.map(row => [row.id, row.revision]));
        if (picker.dataset.signature !== signature) {
          picker.dataset.signature = signature; picker.replaceChildren(new Option('Choose a discussion', ''));
          for (const row of rows) { const thread = row.facets[FACET]; picker.append(new Option(thread.status + ' · ' + thread.anchor.quote.slice(0, 50), row.id)); }
          picker.value = selected;
        }
        render();
      } catch (error) { status.textContent = error.message; } finally { refreshing = false; }
    }
    function run(task) {
      if (busy) return busy;
      for (const button of [capture, create, resolve, reanchor, send]) button.disabled = true;
      busy = (async () => { try { await task(); } catch (error) { status.textContent = error.message + ' Drafts retained.'; }
        finally { busy = null; for (const button of [capture, create, resolve, reanchor, send]) button.disabled = false; await refresh(); } })();
      return busy;
    }
    async function write(object, thread, subjectRevision) {
      const result = await editor.related('discussions', 'transact', {changes: [{id: object.id, expected_revision: object.revision, facets: {[FACET]: thread}}],
        ...(subjectRevision ? {subject_revision: subjectRevision} : {})});
      return result.items[0];
    }
    async function captured() {
      if (!captureValue) throw new Error('Use editor selection first.');
      await editor.save(); const snapshot = editor.snapshot();
      if (captureValue.subject !== snapshot.subject || captureValue.revision !== snapshot.object.revision || captureValue.text !== snapshot.text) throw new Error('The captured selection is stale. Select its object and revision again.');
      return captureValue;
    }
    capture.onclick = () => run(async () => { captureValue = await editor.captureSelection(); selectionLabel.textContent = 'Revision ' + captureValue.revision + ' · ' + captureValue.quote; status.textContent = 'Selection captured on this object.'; });
    create.onclick = () => run(async () => {
      const selection = await captured(), anchor = evidence(selection), text = newMessage.value, first = message(text), at = first.created_at;
      const row = await write({id: 'comment-' + crypto.randomUUID(), revision: 0}, {document_id: selection.subject, anchor, original_anchor: structuredClone(anchor), messages: [first], status: 'open', created_at: at, updated_at: at}, selection.revision);
      if (selected) replies[selected] = reply.value; selected = row.id; reply.value = replies[selected] || '';
      if (newMessage.value === text) newMessage.value = ''; retain(); await editor.persistState(); status.textContent = 'Discussion saved on the same native object.';
    });
    picker.onchange = () => { if (selected) replies[selected] = reply.value; selected = picker.value; reply.value = replies[selected] || ''; drawn = ''; retain(); render(); };
    send.onclick = () => run(async () => {
      const row = current(); if (!row) return; const thread = structuredClone(row.facets[FACET]), key = row.id, text = reply.value;
      if (thread.messages.length >= 8) throw new Error('This thread already has eight messages.');
      thread.messages.push(message(text)); thread.updated_at = new Date().toISOString(); await write(row, thread);
      if (replies[key] === text) replies[key] = ''; if (selected === key && reply.value === text) reply.value = ''; retain(); await editor.persistState(); status.textContent = 'Reply saved.';
    });
    resolve.onclick = () => run(async () => { const row = current(); if (!row) return; const thread = structuredClone(row.facets[FACET]); thread.status = thread.status === 'open' ? 'resolved' : 'open'; thread.updated_at = new Date().toISOString(); await write(row, thread); status.textContent = 'Discussion status saved.'; });
    reanchor.onclick = () => run(async () => { const row = current(); if (!row) return; const selection = await captured(), thread = structuredClone(row.facets[FACET]); thread.anchor = evidence(selection); thread.updated_at = new Date().toISOString(); await write(row, thread, selection.revision); status.textContent = 'Same discussion reanchored; original evidence retained.'; });
    jump.onclick = () => run(async () => {
      const row = current(); if (!row) return; await editor.save(); const snapshot = editor.snapshot(), anchor = row.facets[FACET].anchor, location = locate(anchor, snapshot.text);
      if (location.state !== 'attached') throw new Error('This anchor is ' + location.state + '; select text to reanchor it explicitly.');
      await editor.revealSelection({subject: snapshot.subject, revision: snapshot.object.revision, text_hash: await digest(snapshot.text), start: location.start, end: location.end, quote: anchor.quote});
    });
    editor.ready.then(async () => {
      const retained = editor.extensionState('discussions') || {}; newMessage.value = retained.newMessage || ''; replies = retained.replies || {}; selected = retained.selected || ''; reply.value = replies[selected] || ''; details.open = !!retained.open; initialized = true; await refresh();
    });
    editor.subscribe(() => { render(); refresh(); });
    editor.onFlush(async () => { if (busy) await busy; retain(); await editor.persistState(); });
  };
})();
