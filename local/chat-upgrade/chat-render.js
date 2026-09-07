  // Markdown is presentation only: no executable HTML, remote images or embedded controls.
  function renderMarkdown(target, text) {
    if (target.dataset.source === text) return;
    const fragment = DOMPurify.sanitize(marked.parse(text, {gfm:true, breaks:true}), {
      RETURN_DOM_FRAGMENT:true,
      ALLOWED_TAGS:['p','br','strong','em','del','code','pre','blockquote','ul','ol','li','h1','h2','h3','h4','h5','h6','hr','a','table','thead','tbody','tr','th','td','input'],
      ALLOWED_ATTR:['href','title','start','type','checked','disabled'],
      ALLOW_DATA_ATTR:false, ALLOW_ARIA_ATTR:false
    });
    for (const link of fragment.querySelectorAll('a')) {
      const href = link.getAttribute('href') || '';
      if (!/^(https?:\/\/|mailto:)/i.test(href)) link.removeAttribute('href');
      else { link.target = '_blank'; link.rel = 'noopener noreferrer'; }
    }
    for (const input of fragment.querySelectorAll('input')) {
      if (input.type !== 'checkbox') input.remove(); else input.disabled = true;
    }
    target.replaceChildren(fragment); target.dataset.source = text;
  }
  function toolActivity(tool) {
    if (!tool?.running) return 'JEFF is working…';
    const labels = {'guest.execute':'Running a command in the Linux guest', 'package.get':'Inspecting a package', 'package.save':'Saving package source', 'package.build':'Checking a candidate', 'package.install':'Installing the update', 'candidate.exercise':'Testing a candidate', 'world.query':'Inspecting your space', 'world.get':'Reading an object', 'world.transact':'Saving changes', 'action.invoke':'Running an installed action'};
    const elapsed = Math.max(0, Math.floor(Date.now()/1000-tool.started_at));
    return `${labels[tool.name] || tool.name} · ${elapsed}s`;
  }
  function renderChat(status) {
    state.chatRunning = !!status.running; updateSend();
    const messages = (status.messages || []).map(chatMessage);
    const activity = status.activity;
    // After completion, the durable final message replaces its streamed counterpart.
    const progress = (activity?.messages || []).filter(m => m.text &&
      (status.running || (m.phase !== 'final_answer' && m.text !== status.reply)));
    const displayed = [...messages];
    const live = progress.map(m => ({...m, id:`live-${activity.id}-${m.id}`, role:'assistant', progress:true}));
    if (!status.running && status.reply && displayed.at(-1)?.role === 'assistant') {
      displayed.splice(displayed.length-1,0,...live);
    } else displayed.push(...live);
    const signature = JSON.stringify(displayed);
    if (signature !== state.lastChat) {
      const scroller = $('messages'); const nearEnd = scroller.scrollHeight-scroller.scrollTop-scroller.clientHeight<100; const hadNone = !state.lastChat;
      const wanted = new Set();
      displayed.forEach((message) => {
        wanted.add(message.id); let node = [...scroller.querySelectorAll('.message')].find(n=>n.dataset.messageId===message.id);
        if (!node) {
          node = element('article',`message ${message.role === 'user' ? 'user' : 'assistant'}`); node.dataset.messageId = message.id;
          const meta = element('div','message-meta'); meta.append(element('strong','',message.role === 'user' ? 'YOU' : 'JEFF'));
          node.append(meta,element('div','message-content')); scroller.append(node);
        }
        node.classList.toggle('intermediate',!!message.progress && message.phase !== 'final_answer');
        node.querySelector('strong').textContent = message.role === 'user' ? 'YOU' : message.progress && message.phase !== 'final_answer' ? 'JEFF · PROGRESS' : 'JEFF';
        const body = node.querySelector('.message-content');
        if (message.role === 'user') { if (body.textContent !== message.text) body.textContent = message.text; }
        else renderMarkdown(body,message.text);
        // Reconcile order when progress is inserted before a newly persisted final.
        scroller.append(node);
      });
      for (const node of scroller.querySelectorAll('.message')) if (!wanted.has(node.dataset.messageId)) node.remove();
      $('chat-welcome').hidden = displayed.length>0;
      if (nearEnd || hadNone || state.sending) scroller.scrollTop = scroller.scrollHeight;
      state.lastChat = signature;
    }
    const events = status.events || []; const last = events[events.length-1];
    const fallback = typeof last === 'string' ? last : last?.message || last?.tool || last?.name;
    if (status.error) showActivity(errorText(status.error),true);
    else showActivity(state.chatRunning ? (activity ? toolActivity(activity.tool) : fallback || 'JEFF is working…') : '');
    $('jeff-subtitle').textContent = state.chatRunning ? 'Working in your space' : status.available === false ? 'Connection needed' : 'Here in your space';
    if (status.model) $('chat-model').textContent = status.model;
  }
