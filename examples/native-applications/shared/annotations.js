/* An editor extension using only the public subject/selection/facet contract. */
(() => {
  'use strict';
  const {node, digest} = EditorUtilities;
  const hits = (text, quote) => { const rows = []; for (let i = 0; quote && (i = text.indexOf(quote, i)) >= 0; i++) rows.push(i); return rows; };
  function locate(anchor, text, hash) {
    if (anchor.text_hash === hash && text.slice(anchor.start, anchor.end) === anchor.quote) return {state: 'attached', start: anchor.start, end: anchor.end};
    const places = hits(text, anchor.quote);
    if (!places.length) return {state: 'orphaned'};
    if (places.length !== 1 || anchor.occurrences !== 1) return {state: 'ambiguous'};
    const start = places[0], end = start + anchor.quote.length;
    if ((anchor.prefix && !text.slice(0, start).endsWith(anchor.prefix)) || (anchor.suffix && !text.slice(end).startsWith(anchor.suffix))) return {state: 'orphaned'};
    return {state: 'attached', start, end};
  }
  window.attachAnnotations = editor => {
    const {details, content} = editor.addPanel('Annotations');
    const input = node('textarea', 'annotation-input'); input.placeholder = 'Comment on selected text'; input.setAttribute('aria-label', 'New annotation'); input.maxLength = 3000;
    const add = node('button', '', 'Attach to selection'); add.onmousedown = event => event.preventDefault();
    const status = node('p', 'annotation-status'); status.setAttribute('role', 'status'); const list = node('div', 'annotation-list');
    content.append(input, add, status, list);
    let signature = '', rendering = 0, initialized = false;
    input.oninput = () => editor.extensionState('annotations', {draft: input.value, open: details.open});
    details.ontoggle = () => { if (initialized) editor.extensionState('annotations', {draft: input.value, open: details.open}); };
    editor.ready.then(() => { const retained = editor.extensionState('annotations'); if (retained) { input.value = retained.draft || ''; details.open = !!retained.open; } initialized = true; });
    add.onclick = async () => {
      add.disabled = true;
      try {
        if (!input.value.trim()) throw new Error('Write a comment first.');
        const selection = await editor.captureSelection();
        const anchor = {revision: selection.revision, text_hash: selection.text_hash, start: selection.start, end: selection.end,
          quote: selection.quote, prefix: selection.text.slice(Math.max(0, selection.start - 24), selection.start),
          suffix: selection.text.slice(selection.end, selection.end + 24), occurrences: hits(selection.text, selection.quote).length};
        const threads = editor.snapshot().object.facets['text.annotations']?.threads || [];
        await editor.updateFacet('text.annotations', {threads: [...threads, {id: crypto.randomUUID(), message: input.value.trim(), status: 'open', anchor}]}, selection.revision);
        input.value = ''; editor.extensionState('annotations', {draft: '', open: true}); await editor.persistState(); status.textContent = 'Annotation saved on this object.';
      } catch (error) { status.textContent = error.message; } finally { add.disabled = false; }
    };
    editor.subscribe(async snapshot => {
      const threads = snapshot.object.facets['text.annotations']?.threads || [];
      const next = JSON.stringify([threads, snapshot.text]); if (next === signature) return;
      const job = ++rendering, hash = await digest(snapshot.text); if (job !== rendering) return; signature = next;
      list.replaceChildren();
      if (!threads.length) list.append(node('p', 'muted', 'Annotations follow the object into either application.'));
      for (const thread of threads) {
        const card = node('article', 'annotation'); const location = locate(thread.anchor, snapshot.text, hash);
        card.append(node('blockquote', '', thread.anchor.quote), node('p', '', thread.message), node('small', '', thread.status + ' · ' + location.state));
        const jump = node('button', '', 'Show text'); jump.disabled = location.state !== 'attached'; jump.onclick = async () => {
          try { await editor.save(); const current = editor.snapshot(), hash = await digest(current.text), fresh = locate(thread.anchor, current.text, hash);
            if (fresh.state !== 'attached') throw new Error('Anchor no longer resolves.');
            await editor.revealSelection({subject: current.subject, revision: current.object.revision, text_hash: hash, ...fresh, quote: thread.anchor.quote});
          } catch (error) { status.textContent = error.message; }
        };
        const resolve = node('button', '', thread.status === 'resolved' ? 'Reopen' : 'Resolve');
        resolve.onclick = async () => {
          try { await editor.save(); const current = editor.snapshot().object; const all = current.facets['text.annotations'].threads;
            await editor.updateFacet('text.annotations', {threads: all.map(t => t.id === thread.id ? {...t, status: t.status === 'resolved' ? 'open' : 'resolved'} : t)}, current.revision);
          } catch (error) { status.textContent = error.message; }
        };
        card.append(jump, resolve); list.append(card);
      }
    });
  };
})();
