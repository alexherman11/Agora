/* The resident conversation is a desktop client of native chat and retained drafts. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id), call = AgoraDesktop.request;
  let loaded = false, dirty = false, revision = 0, saveTimer, queue = Promise.resolve(), busy = false, polling = false, running = false, lastTranscript = '', resident = 'JEFF';
  const input = $('chat-input');
  function error(text) { $('chat-error').hidden = !text; $('chat-error').textContent = text; }
  function show(open) { document.body.classList.toggle('chat-open', open); $('chat-toggle').setAttribute('aria-expanded', String(open)); if (open && loaded) input.focus(); }
  $('chat-toggle').onclick = () => show(!document.body.classList.contains('chat-open')); $('chat-close').onclick = () => show(false);
  function renderMarkdown(element, text) {
    element.innerHTML = DOMPurify.sanitize(marked.parse(text || '', {async: false}), {ALLOWED_TAGS: ['p','br','strong','em','del','blockquote','pre','code','ul','ol','li','h1','h2','h3','h4','hr','a','table','thead','tbody','tr','th','td'], ALLOWED_ATTR: ['href','title']});
    for (const link of element.querySelectorAll('a')) { const href = link.getAttribute('href') || ''; if (!/^https?:\/\//i.test(href)) link.removeAttribute('href'); else { link.target = '_blank'; link.rel = 'noopener noreferrer'; } }
  }
  function saveDraft() {
    clearTimeout(saveTimer); if (!loaded || !dirty) return queue;
    const text = input.value; dirty = false;
    queue = queue.catch(() => {}).then(async () => {
      try { const result = await call('world.transact', {changes: [{id: 'shell.chat-draft', expected_revision: revision, facets: {'core.text': {text}, 'core.draft': {conversation: 'main'}}}]}); revision = result.items[0].revision; $('chat-draft-status').textContent = text ? 'Draft retained' : 'Ctrl+Enter to send'; }
      catch (cause) { dirty = true; error('Your draft is still here. ' + cause.message); throw cause; }
    });
    return queue;
  }
  input.oninput = () => { dirty = true; clearTimeout(saveTimer); saveTimer = setTimeout(() => saveDraft().catch(() => {}), 250); };
  AgoraDesktop.onFlush(async () => { input.readOnly = true; try { await saveDraft(); } catch (cause) { input.readOnly = false; throw cause; } });
  window.addEventListener('message', event => { if (event.source === parent && event.data?.agora && event.data.event === 'cancel-reload') input.readOnly = false; });
  AgoraDesktop.selectionHandler(async selection => {
    if (!loaded) throw new Error('Wait for your existing chat draft to load.');
    const block = 'Selected passage from “' + selection.title + '” (object ' + selection.subject + ', revision ' + selection.revision + ', UTF-16 ' + selection.start + '–' + selection.end + '):\n\n' + selection.quote;
    if (!input.value.includes(block)) {
      const text = input.value + (input.value ? '\n\n' : '') + block;
      if (text.length > 30000) throw new Error('The combined chat draft would be too long. Your existing draft was preserved.');
      input.value = text; dirty = true; await saveDraft();
    }
    show(true); input.setSelectionRange(input.value.length, input.value.length);
  });
  async function poll() {
    if (polling) return; polling = true;
    try {
      const status = await call('chat.status'); running = status.running; resident = status.resident?.name || 'JEFF';
      $('resident-name').textContent = $('composer-name').textContent = resident;
      $('continuity-status').textContent = status.resident?.resumable ? 'Same resident · conversation retained' : 'Native history retained';
      const owner = status.resident?.owner_matches !== false;
      $('chat-send').disabled = !loaded || running || busy || !owner; $('chat-stop').hidden = !running;
      if (!owner) error('This copied world does not own the resident conversation.');
      const signature = JSON.stringify(status.messages);
      if (signature !== lastTranscript) {
        const list = $('chat-transcript'), nearBottom = list.scrollHeight - list.scrollTop - list.clientHeight < 100 || !lastTranscript;
        lastTranscript = signature; list.replaceChildren();
        for (const message of status.messages) {
          const article = document.createElement('article'); article.className = 'chat-message ' + message.role;
          const label = document.createElement('strong'); label.textContent = message.role === 'assistant' ? resident : message.role === 'user' ? 'Alex / conversation' : 'Migration record';
          const body = document.createElement('div'); renderMarkdown(body, message.text); article.append(label, body); list.append(article);
        }
        if (nearBottom) list.scrollTop = list.scrollHeight;
      }
      const progress = $('chat-progress'); progress.hidden = !running; progress.replaceChildren();
      if (running) {
        const tool = status.activity?.tool; const label = document.createElement('small'); label.textContent = tool?.running ? tool.name + ' · ' + Math.max(0, Math.floor(Date.now()/1000 - tool.started_at)) + 's' : resident + ' is thinking…'; progress.append(label);
        for (const message of (status.activity?.messages || []).slice(-2)) { const block = document.createElement('div'); renderMarkdown(block, message.text); progress.append(block); }
      }
      if (status.error) error(status.error);
    } catch (cause) { error(cause.message); } finally { polling = false; setTimeout(poll, running ? 700 : 2200); }
  }
  async function send() {
    if (!loaded || running || busy || !input.value.trim()) return;
    busy = true; $('chat-send').disabled = true; const text = input.value; error('');
    try { await saveDraft(); await call('chat.send', {message: text}); if (input.value === text) { input.value = ''; dirty = true; await saveDraft(); } }
    catch (cause) { error(cause.message); } finally { busy = false; poll(); }
  }
  $('chat-send').onclick = send; input.onkeydown = event => { if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') { event.preventDefault(); send(); } };
  $('chat-stop').onclick = async () => { try { await call('chat.stop'); poll(); } catch (cause) { error(cause.message); } };
  (async () => {
    try {
      const result = await call('world.query', {facets: ['core.draft'], limit: 200});
      const draft = result.items.find(item => item.id === 'shell.chat-draft');
      revision = draft?.revision || 0; input.value = draft?.facets['core.text']?.text || ''; loaded = true; input.disabled = false; $('chat-draft-status').textContent = input.value ? 'Draft restored' : 'Ctrl+Enter to send';
    } catch (cause) { error('Draft loading failed: ' + cause.message); }
    poll();
  })();
})();
