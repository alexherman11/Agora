// shell-dock-item: one app in the dock (the dock repeats it, one per app). Its icon, how many windows, and a mark:
// running, in front, minimised. Press: start it, bring it forward, or tuck it away. Middle press: a new window.
// Right press: its windows, new window, keep in dock / remove, pin in place, close, and the ask box.
// Hover: a live preview of its windows (DWM thumbnails through window.native, laid over each tile).
// Facts on the body for styles: state (closed, open, front, minimised) and app (shell-dock-item.body[state=front]).
// Parts body, icon, mark, count, menu, preview, tile.
export default {mount(api, s) {
  const K = globalThis.ShellKit, { h, glyph, Icon, Pop, Menu, Data } = K;
  const x = s.group || { id: '?', app: '?', wins: [] };
  const n = x.wins.length, front = x.wins.some((w) => w.focused), allMin = n > 0 && x.wins.every((w) => w.state === 'minimised');
  const state = !n ? 'closed' : front ? 'front' : allMin ? 'minimised' : 'open';
  const b = api.part('body', 'button', { class: `item ${state}`, 'data-id': x.id, tabindex: '-1', draggable: 'false', 'aria-haspopup': 'menu',
    'aria-label': `${x.app}${n ? `, ${n} window${n > 1 ? 's' : ''}${front ? ', in front' : allMin ? ', minimised' : ''}` : ', not running'}` },
    api.part('icon', 'span', {}, Icon(x.icon, x.app, 'dock')),
    n > 1 ? api.part('count', 'i', { class: 'count', 'aria-hidden': 'true' }, String(n)) : '',
    api.part('mark', 'i', { class: 'mark', 'aria-hidden': 'true' }));
  b.setAttribute('data-fact-state', state);
  b.setAttribute('data-fact-app', String(x.app || '').toLowerCase().replace(/[^\w-]+/g, '-'));
  b.firstChild.style.display = 'contents';
  const dock = () => K.dock || { state: {}, items: [] };

  const click = async () => {
    unhover(true);
    if (!n) { await K.ran(Data.launch(x.line || `window.launch path=${JSON.stringify(x.exe)}`, x.exe)); return K.poke('windows'); }
    const st = dock().state;
    // the dock takes the focus when pressed, so the app in front a moment ago counts as in front (unless it is minimised)
    const f = x.wins.find((w) => w.focused) || x.wins.find((w) => w.key === st.lastFront && st.noFocus && w.state !== 'minimised');
    if (f) await K.ran(Data.minimise(f));
    else await K.ran(Data.focus(x.wins.find((v) => v.state !== 'minimised') || x.wins[0]));
    K.poke('windows');
  };
  const fresh = () => {
    if (x.launcher) return K.ran(Data.act(`${x.line} new=yes`));
    if (x.exe) return K.ran(Data.launch(`window.launch path=${JSON.stringify(x.exe)}`, x.exe));
    if (x.wins[0] && x.wins[0].agora) return K.ran(Data.act(`window.open ${x.wins[0].shows} new=yes`));
    return null;
  };
  const keep = async () => {
    await K.ran(Data.act(`make kind=button bar=taskbar label=${JSON.stringify(x.app)} path=${JSON.stringify(x.exe)} does=${JSON.stringify('window.launch path=' + x.exe)}`));
    K.toast(`${x.app} stays in the dock`); K.poke('pins');
  };
  const unkeep = async () => { if (x.pin && x.pin.id) { await K.ran(Data.act(`forget ${x.pin.id}`)); K.toast(`${x.app} left the dock`); K.poke('pins'); } };

  function menu() {
    unhover(true);
    const items = [{ head: x.app, icon: Icon(x.icon, x.app, 26), note: n ? `${n} window${n > 1 ? 's' : ''}` : 'not running' }];
    if (n) {
      items.push('-');
      x.wins.slice(0, 6).forEach((w, i) => items.push({ label: w.title || `${x.app} window ${i + 1}`, glyph: w.focused ? 'check' : 'monitor',
        hint: w.state === 'minimised' ? 'minimised' : w.state === 'pinned' ? 'pinned' : '', run: () => K.ran(Data.focus(w)).then(() => K.poke('windows')) }));
      if (n > 6) items.push({ label: `${n - 6} more`, disabled: true });
    }
    items.push('-');
    items.push({ label: n ? 'New window' : 'Open', glyph: 'external', run: () => fresh() || K.ran(Data.act(x.line || `window.launch path=${x.exe}`)) });
    if (x.pin) { if (x.pin.id || x.launcher) items.push({ label: 'Remove from dock', glyph: 'pin-off', run: () => (x.launcher ? K.toast('Agora apps are listed in the dock settings') : unkeep()), disabled: !!x.launcher }); }
    else if (x.exe) items.push({ label: 'Keep in dock', glyph: 'pin', run: keep });
    const f = x.wins.find((w) => w.focused) || x.wins[0];
    if (f && Data.wmOK && !f.agora) items.push({ label: f.state === 'pinned' ? 'Unpin from its place' : 'Pin in place', glyph: f.state === 'pinned' ? 'pin-off' : 'pin', run: () => K.ran(Data.act(`${f.state === 'pinned' ? 'wm.unpin' : 'wm.pin'} ${f.key}`)) });
    if (n) {
      items.push('-');
      items.push({ label: n > 1 ? 'Close all windows' : 'Close window', glyph: 'x', danger: true, run: () => { x.wins.forEach((w) => K.ran(Data.close(w))); K.poke('windows'); } });
    }
    Pop.open('menu', b, () => Menu(items, api.askBox()), { label: `${x.app} menu`, above: true, gap: 12, cls: 'narrow', card: api.part('menu', 'div') });
  }

  // ---- the hover preview: one at a time for the whole dock; titles are asked now and never kept
  let ht = 0;
  function hover(now) {
    clearTimeout(ht);
    if (!n || (Pop.cur && Pop.cur.id === 'menu')) return;
    ht = api.setTimeout(preview, now ? 0 : 380);
  }
  function unhover(now) {
    clearTimeout(ht);
    if (now) closePreview(); else ht = api.setTimeout(closePreview, 160);
  }
  function closePreview() {
    const d = dock(), pv = d.pv;
    if (!pv) return;
    d.pv = null;
    pv.card.remove();
    K.thumbs([]);
    K.report();
  }
  async function preview() {
    if (Pop.cur && Pop.cur.id === 'menu') return;
    closePreview();
    const wins = x.wins.slice(0, 4);
    const info = await Promise.all(wins.map((w) => Data.title(w).then((t) => t || {})));
    if (!b.isConnected) return;
    const tile = (w, i) => {
      const t = info[i] || {}, hwnd = t.hwnd || Data.hwnd(w);
      const th = h('div', { cls: 'th', 'data-key': w.key, 'data-hwnd': hwnd || '' },
        t.preview && /^(data:image\/|blob:)/.test(t.preview) ? h('img', { src: t.preview, alt: '' }) : h('div', { cls: 'ph' }, Icon(x.icon, x.app, 56)));
      return api.part('tile', 'button', { class: 'tile' + (w.focused ? ' front' : ''), 'aria-label': `${t.title || x.app}${w.state === 'minimised' ? ', minimised' : ''}. Switch to this window`,
        on: { click: () => { closePreview(); K.ran(Data.focus(w)).then(() => K.poke('windows')); } } },
        h('div', { cls: 'tt' }, Icon(x.icon, x.app, 16), h('span', {}, t.title || w.title || x.app),
          h('i', { cls: 'x', role: 'button', 'aria-label': 'Close this window', on: { click: (e) => { e.stopPropagation(); K.ran(Data.close(w)); closePreview(); K.poke('windows'); } } }, glyph('x'))), th);
    };
    const card = api.part('preview', 'div', { class: 'pop preview in', 'data-pop': 'preview', role: 'group', 'aria-label': `${x.app} windows`,
      on: { pointerenter: () => clearTimeout(ht), pointerleave: () => unhover(false) } }, ...wins.map(tile));
    document.body.append(card);
    dock().pv = { card, id: x.id };
    const a = b.getBoundingClientRect(), w = card.offsetWidth;
    card.style.left = Math.max(10, Math.min(a.left + a.width / 2 - w / 2, innerWidth - w - 10)) + 'px';
    card.style.top = Math.max(4, a.top - card.offsetHeight - 14) + 'px';
    K.report();
    // ask the host for the real thing: one DWM thumbnail per tile, laid over the placeholder
    api.requestAnimationFrame(() => {
      const rects = [...card.querySelectorAll('.th')].filter((t) => t.dataset.hwnd).map((t) => { const r = t.getBoundingClientRect(); return { hwnd: t.dataset.hwnd, key: t.dataset.key, x: r.left, y: r.top, w: r.width, h: r.height }; });
      K.thumbs(rects);
    });
  }

  b.addEventListener('click', click);
  b.addEventListener('auxclick', (e) => { if (e.button === 1) { e.preventDefault(); fresh(); } });
  b.addEventListener('mousedown', (e) => { if (e.button === 1) e.preventDefault(); });
  b.addEventListener('contextmenu', (e) => { e.preventDefault(); menu(); });
  b.addEventListener('dock-menu', menu);
  b.addEventListener('dock-preview', () => hover(true));
  b.addEventListener('pointerenter', () => hover(false));
  b.addEventListener('pointerleave', () => unhover(false));
  b.addEventListener('focus', () => { if (b.matches(':focus-visible')) hover(false); });
  b.addEventListener('blur', () => unhover(true));
  // a preview of this app stays open while the dock repaints the item (a window title changed); it goes with the app
  api.cleanup(() => { const pv = dock().pv; if (pv && pv.id === x.id && !(K.dock && K.dock.items.some((i) => i.id === x.id))) closePreview(); });
  return b;
}};
