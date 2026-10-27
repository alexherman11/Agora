// shell-dock: the centred pill. Its parts are arranged in the lens (launcher, separators, the app slot, overview); the
// child that is a shell-dock-item is a slot, repeated once per app: pinned apps first (Agora apps from dock_apps, then
// kept programs), then running ones in a remembered order, then Agora's own windows. Reads wm.windows each second.
// Handles: apps (comma list of Agora apps; default shell-settings dock_apps). Parts pill.
export default {mount(api, s) {
  const K = globalThis.ShellKit, { Data } = K;
  document.body.dataset.page = 'dock';
  const pill = api.part('pill', 'nav', { class: 'pill', role: 'toolbar', 'aria-label': 'Dock', 'aria-orientation': 'horizontal' });
  const slot = api.children.find((c) => c.component === 'shell-dock-item');
  const state = { wins: [], pins: [], lenses: [], settings: {}, order: [], lastFront: null, noFocus: false };
  const shown = new Map();            // group id -> {el, sig}
  const marker = document.createComment('apps');
  for (const child of api.children) pill.append(child === slot ? marker : api.render(child));
  K.dock = { state, items: [] };
  const rov = K.roving(pill, '.item');

  function groups() {
    const g = new Map();
    const keyOf = (w) => (w.agora ? 'agora:' + w.key : (w.exe || w.app).toLowerCase());
    for (const w of state.wins) {
      const k = keyOf(w);
      if (!g.has(k)) g.set(k, { id: k, app: w.app, exe: w.exe, icon: w.icon, wins: [], agora: !!w.agora, pin: null });
      g.get(k).wins.push(w);
    }
    const have = new Set(state.lenses);
    const apps = String(s.apps || state.settings.dock_apps || K.DOCK_APPS).split(/[ ,]+/).filter(Boolean)
      .filter((n) => K.AGORA_APPS[n] && (['lines', 'help', 'thing', 'tasks'].includes(n) || have.has(n)));
    const pinned = apps.map((n) => ({ id: 'app:' + n, app: K.AGORA_APPS[n][0], exe: '', icon: 'agora:' + n, wins: [], line: K.AGORA_APPS[n][1], launcher: n, pin: { id: '' } }));
    const launched = new Set(pinned.map((p) => p.line));
    for (const p of state.pins) {
      const exe = p.path || '';
      if (!exe && launched.has(p.does)) continue;
      pinned.push({ id: exe ? exe.toLowerCase() : 'pin:' + p.id, app: p.label || p.name || (exe.split(/[\\/]/).pop() || 'Pinned').replace(/\.exe$/i, ''), exe,
        icon: exe ? 'exe:' + exe : 'agora:' + K.appOf(K.opensLens(p.does)), wins: [], line: p.does || `window.launch path=${exe}`, pin: { id: p.id } });
    }
    // a running Agora window shares the slot of whatever opens it (a launcher, or a button that says window.open)
    const slotted = new Set();
    for (const p of pinned) {
      const lens = K.opensLens(p.line);
      const k = lens ? [...g.keys()].find((x) => x.startsWith('agora:') && !slotted.has(x) && g.get(x).wins.some((w) => w.shows === lens)) : p.id;
      const run = k && g.get(k);
      if (run && !slotted.has(k)) { p.wins = run.wins; slotted.add(k); }
    }
    const running = [...g.values()].filter((x) => !slotted.has(x.id) && !x.agora);
    const own = [...g.values()].filter((x) => !slotted.has(x.id) && x.agora);
    const all = [...pinned, ...running, ...own];
    for (const x of all) if (!state.order.includes(x.id)) state.order.push(x.id);
    const pinIds = new Set(pinned.map((x) => x.id));
    const rest = all.filter((x) => !pinIds.has(x.id)).sort((a, b) => state.order.indexOf(a.id) - state.order.indexOf(b.id));
    return [...pinned, ...rest];
  }

  function paint() {
    if (!slot) return;
    const items = groups();
    K.dock.items = items;
    const keep = document.activeElement && document.activeElement.closest && document.activeElement.closest('.item');
    const keepId = keep && keep.dataset.id;
    const next = [];
    for (const x of items) {
      const sig = JSON.stringify(x);
      let it = shown.get(x.id);
      if (!it || it.sig !== sig) {
        const el = api.child(slot.name, { group: x }, x.id);
        if (it && it.el.isConnected) it.el.replaceWith(el);
        it = { el, sig };
        shown.set(x.id, it);
      }
      next.push(it.el);
    }
    for (const [id, it] of shown) if (!items.some((x) => x.id === id)) { it.el.remove(); shown.delete(id); }
    // in order, after the marker; a node already in place is not moved (its hover and focus stay)
    let at = marker;
    for (const el of next) { if (at.nextSibling !== el) at.after(el); at = el; }
    if (keepId) { const k = pill.querySelector(`[data-id="${CSS.escape(keepId)}"]`); if (k && document.activeElement !== k) k.focus({ preventScroll: true }); }
    rov.refresh();
    const f = items.find((x) => x.wins.some((w) => w.focused));
    pill.setAttribute('aria-label', `Dock, ${items.filter((x) => x.wins.length).length} apps running${f ? ', ' + f.app + ' in front' : ''}`);
    K.report();
  }
  K.watch(api, 'windows', 2500, (wins) => {   // 2.5 s: at 1 s the kernel was saturated (26 Oct)
    state.wins = wins;
    const f = wins.find((w) => w.focused);          // clicking the dock activates the dock: remember who was in front before
    state.noFocus = !f; if (f) state.lastFront = f.key;
    paint();
  });
  K.watch(api, 'pins', 4000, (v) => { state.pins = v; paint(); });
  K.watch(api, 'lenses', 30000, (v) => { state.lenses = v; paint(); });
  K.watch(api, 'settings', 4000, (v) => { state.settings = v; paint(); });
  pill.addEventListener('keydown', (e) => {
    const it = document.activeElement && document.activeElement.closest && document.activeElement.closest('.item');
    if (!it) return;
    if (e.key === 'ContextMenu' || (e.shiftKey && e.key === 'F10')) { e.preventDefault(); it.dispatchEvent(new CustomEvent('dock-menu')); }
    if (e.key === 'ArrowUp') { e.preventDefault(); it.dispatchEvent(new CustomEvent('dock-preview')); }
  });
  // The window is solid over the pill and a little around it, never further up than the strip the dock reserves:
  // above that are other programs' windows. ShellKit adds whatever is open (menus, previews, the ask menu, a toast).
  K.shape = () => {
    const p = pill.getBoundingClientRect(), go = parseFloat(K.cssVar('--ag-gap-outer')) || 10, side = Math.min(go, 8);
    const pr = parseFloat(getComputedStyle(pill).borderTopLeftRadius) || 0;
    return { reserve: Math.ceil(innerHeight - p.top + go), pill: { x: p.left, y: p.top, w: p.width, h: p.height },
      shape: [{ x: p.left - side, y: p.top - go, w: p.width + 2 * side, h: p.height + 2 * go + 2, r: Math.min(pr + go, (p.height + 2 * go) / 2) }] };
  };
  api.cleanup(() => { if (K.dock && K.dock.state === state) K.dock = null; });
  return pill;
}};
