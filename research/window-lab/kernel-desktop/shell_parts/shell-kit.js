// shell-kit.js: the shell bars' painter vocabulary (SHELL.md, "The bars as components"). Builder draft, 26 Oct 2026.
//
// Loaded only into the shell-top and shell-dock widgets' code, after the painter's core and before painter.js runs, the
// way primitives.js is: module scope, so it shares `el`, `css`, `agora`, `nativeTimers`. The bar's parts are components
// (shell_parts/components/*.js) arranged by the lenses shell-top and shell-dock; this file is what they share and what is
// not a part:
//
//   h, glyph, Icon        DOM, the UI glyphs, an app's colour icon (bytes fetched by the trusted host: the frame has no network)
//   Data                  what the bars ask the world (wm.windows, else window.list + window.desktop; system.now; ...)
//                         and the window actions (wm.* when the manager answers, window.activate when it is off)
//   watch / poke          one live-reading hub: each reading is polled once for every part that wants it, at the fastest
//                         rate asked (dock 1 s, bar 2.5 s and 4 s, as before); a part's callback runs as that part
//   Pop, Menu, roving     one popover at a time, menus (each ends with the ask box), the roving toolbar
//   report                the window's shape and strip, sent through agora.native('layout') (window.native)
//
// Live readings never enter the painter's projection, so the projection only changes when the lens, a style, a
// preference or a component changes: popovers stay open and nothing is rebuilt every second.
const ShellKit = (() => {
  'use strict';
  const doc = document, root = doc.documentElement;
  const num = (v, d) => (v === null || v === undefined || v === '' || Number.isNaN(+v) ? d : +v);
  const yes = (v) => /^(yes|on|true|1)$/i.test(String(v ?? ''));

  // ------------------------------------------------------------------------------------------------ tiny DOM
  function h(tag, attrs, ...kids) {
    const e = doc.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v === undefined || v === null || v === false) continue;
      if (k === 'on') for (const [ev, f] of Object.entries(v)) e.addEventListener(ev, f);
      else if (k === 'cls') e.className = v;
      else if (k === 'style' && typeof v === 'object') for (const [p, x] of Object.entries(v)) e.style.setProperty(p, x);
      else e.setAttribute(k, v === true ? '' : v);
    }
    for (const c of kids.flat(3)) if (c !== null && c !== undefined && c !== false && c !== '') e.append(c.nodeType ? c : String(c));
    return e;
  }
  const cssVar = (name) => getComputedStyle(root).getPropertyValue(name).trim();

  // ------------------------------------------------------------------------------------------------ glyphs
  const G = {
    wifi: '<path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><path d="M12 20h.01"/>',
    'wifi-off': '<path d="M2 2l20 20"/><path d="M8.5 16.4a6 6 0 0 1 7 0"/><path d="M5 12.6a11 11 0 0 1 5.2-2.6"/><path d="M12 20h.01"/>',
    volume: '<path d="M11 5 6 9H2v6h4l5 4V5z"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>',
    'volume-low': '<path d="M11 5 6 9H2v6h4l5 4V5z"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>',
    'volume-x': '<path d="M11 5 6 9H2v6h4l5 4V5z"/><path d="m22 9-6 6"/><path d="m16 9 6 6"/>',
    battery: '<rect x="2" y="7" width="16" height="10" rx="2"/><path d="M22 11v2"/><path d="M6 11v2" class="lvl"/>',
    'battery-charging': '<path d="M15 7h1a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2h-2"/><path d="M6 17H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h1"/><path d="m11 7-3 5h4l-3 5"/><path d="M22 11v2"/>',
    bell: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
    left: '<path d="m15 18-6-6 6-6"/>', right: '<path d="m9 18 6-6-6-6"/>', down: '<path d="m6 9 6 6 6-6"/>',
    x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>', minus: '<path d="M5 12h14"/>',
    power: '<path d="M18.36 6.64a9 9 0 1 1-12.73 0"/><path d="M12 2v10"/>',
    play: '<path d="M6 4v16l14-8z" fill="currentColor"/>',
    pause: '<rect x="6" y="4" width="4" height="16" rx="1" fill="currentColor"/><rect x="14" y="4" width="4" height="16" rx="1" fill="currentColor"/>',
    next: '<path d="M5 4v16l10-8z" fill="currentColor"/><path d="M19 5v14"/>',
    prev: '<path d="M19 4v16L9 12z" fill="currentColor"/><path d="M5 5v14"/>',
    pin: '<path d="M12 17v5"/><path d="M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z"/>',
    'pin-off': '<path d="M12 17v5"/><path d="M15 9.34V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H7.89"/><path d="m2 2 20 20"/><path d="M9 9v1.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h11"/>',
    grid: '<rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/>',
    settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    monitor: '<rect width="20" height="14" x="2" y="3" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/>',
    external: '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    cpu: '<rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9"/><path d="M15 2v2M15 20v2M2 15h2M2 9h2M20 15h2M20 9h2M9 2v2M9 20v2"/>',
    memory: '<path d="M6 19v-3M10 19v-3M14 19v-3M18 19v-3M8 11V9M16 11V9M12 11V9"/><path d="M2 15h20"/><path d="M2 7a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v1.1a2 2 0 0 0 0 3.8V17a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-5.1a2 2 0 0 0 0-3.8z"/>',
    check: '<path d="M20 6 9 17l-5-5"/>', terminal: '<path d="m4 17 6-6-6-6"/><path d="M12 19h8"/>',
    message: '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22z"/>', alert: '<path d="M12 9v4"/><path d="M12 17h.01"/><circle cx="12" cy="12" r="10"/>',
  };
  function glyph(name, cls = '') {
    const s = h('span', { cls: 'gl ' + cls, 'aria-hidden': 'true' });
    s.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${G[name] || G.grid}</svg>`;
    return s;
  }

  // ------------------------------------------------------------------------------------------------ icons
  const AGORA_APPS = {
    lines: ['Lines', 'window.open lines'], help: ['Help', 'window.open help'], board: ['Board', 'window.open board'],
    taskboard: ['Task board', 'window.open taskboard-components'], appearance: ['Appearance', 'window.open appearance'],
    feed: ['Feed', 'window.open feed'], thing: ['Thing', 'window.open thing'], tasks: ['Running windows', 'window.open tasks'],
    work: ['Work', 'window.open work'],          // who is at work and what is moving (kernel-lab/apps/work, 27 Oct)
    writing: ['Writing', 'window.open writing'], // documents and plans to review (kernel-lab/apps/writing, 27 Oct)
  };
  const DOCK_APPS = 'lines,help,board,taskboard,appearance,feed';
  const appOf = (name) => {
    const n = (name || '').toLowerCase();
    if (AGORA_APPS[n]) return n;
    for (const [re, app] of [[/task/, 'taskboard'], [/board/, 'board'], [/appearance|theme/, 'appearance'], [/feed/, 'feed'],
                             [/help/, 'help'], [/lines|chat/, 'lines']]) if (re.test(n)) return app;
    return 'thing';
  };
  const opensLens = (line) => ((line || '').match(/^window\.open (\S+)/) || [])[1] || '';
  // The frame has no network: the trusted host fetches the icon's bytes (/desk/icon, or an Agora app's svg) and hands
  // back a Blob, as it does for files. One object URL per icon, kept for the frame's life.
  const icons = new Map();
  function iconUrl(ref, size = 128) {
    if (!ref) return Promise.resolve('');
    if (/^(data:image\/|blob:)/.test(ref)) return Promise.resolve(ref);
    const key = ref + '@' + size;
    if (!icons.has(key)) {
      if (icons.size > 400) icons.clear();
      icons.set(key, agora.native('icon', ref, size).then((r) => (r && r.blob ? URL.createObjectURL(r.blob) : '')).catch(() => ''));
    }
    return icons.get(key);
  }
  function Icon(ref, name, size = 28) {          // size: px, or "dock" / "bar" (the theme's own sizes)
    const e = h('span', { cls: 'ico' + (typeof size === 'string' ? ' ' + size : ''), 'aria-hidden': 'true' });
    if (typeof size === 'number') e.style.setProperty('--isz', size + 'px');
    const letter = () => { e.classList.add('letter'); e.replaceChildren(h('b', {}, (name || '?').trim().slice(0, 1).toUpperCase())); };
    if (!ref) { letter(); return e; }
    iconUrl(ref, typeof size === 'number' && size > 56 ? 256 : 128).then((url) => {
      if (!url) return letter();
      e.style.setProperty('--src', `url("${url}")`);
      e.replaceChildren(h('img', { src: url, alt: '', draggable: 'false', on: { error: letter } }));
    });
    return e;
  }

  // ------------------------------------------------------------------------------------------------ data
  const NICE = { windowsterminal: 'Terminal', msedge: 'Edge', chatgpt: 'ChatGPT', obs64: 'OBS', code: 'Code', explorer: 'Files',
    applicationframehost: 'Settings', claude: 'Claude', spotify: 'Spotify', chrome: 'Chrome', discord: 'Discord', python: 'Python',
    pythonw: 'Python', notepad: 'Notepad', mspaint: 'Paint', taskmgr: 'Task Manager', cmd: 'Command Prompt', powershell: 'PowerShell' };
  const nice = (p) => NICE[(p || '').toLowerCase()] || ((p || '').slice(0, 1).toUpperCase() + (p || '').slice(1));
  const refused = (r) => !r || r.ok === false || r.refused || /^refused|no word|unknown word|nothing answers/i.test(r.text || '');

  const Data = {
    wmOK: null,
    async see(line) { try { return await agora.see(line); } catch (e) { return { ok: false, text: String(e.message || e), rows: [] }; } },
    async act(line) { try { return await agora.do(line); } catch (e) { return { ok: false, text: String(e.message || e), rows: [] }; } },
    // A window's native handle, where its key carries one (the WM's key is pid:created:hwnd; the fallback's is the handle).
    hwnd: (w) => { const last = String(w.key || '').split(':').pop(); return !w.agora && /^\d{1,12}$/.test(last) ? last : ''; },
    async windows() {
      const r = await this.see('wm.windows');
      const refOf = (v) => (/^(exe|hwnd|pkg|aumid|agora|data):/.test(v) ? v : /^[A-Za-z]:[\\/]/.test(v) ? 'exe:' + v : v || '');
      if (!refused(r) && Array.isArray(r.rows)) {
        this.wmOK = true;
        const own = new Map();
        if (r.rows.some((w) => w.agora)) for (const w of ((await this.see('window.list')).rows || [])) if (w.kind === 'window') own.set(w.id, w);
        return r.rows.filter((w) => w.key !== undefined && w.kind !== 'work').flatMap((w) => {
          const o = w.agora ? own.get(w.agora) : null;
          if (w.agora && (!o || o.edge || /^(taskbar|shell-)/.test(o.shows || ''))) return [];
          const shows = (o && o.shows) || w.shows || '';
          return [{ key: String(w.key), app: (o && o.name) || w.app || nice((w.exe || '').split(/[\\/]/).pop().replace(/\.exe$/i, '')), exe: w.exe || '',
            icon: w.agora ? 'agora:' + appOf(shows) : refOf(w.icon) || (w.exe ? 'exe:' + w.exe : ''),
            agora: w.agora || '', state: w.state || 'normal', focused: !!w.focused, managed: w.managed !== false, why: w.why || '', shows, space: w.space || '' }];
        });
      }
      this.wmOK = false;               // the window manager is off: the native shell is the fallback
      const [a, b] = await Promise.all([this.see('window.list'), this.see('window.desktop')]);
      const mine = (a.rows || []).filter((w) => w.kind === 'window' && !w.edge && !/^(taskbar|shell-)/.test(w.shows || ''))
        .map((w) => ({ key: w.id, app: w.name || nice(w.shows), exe: '', icon: 'agora:' + appOf(w.shows),
          agora: w.id, state: w.shown === false ? 'minimised' : 'normal', focused: !!w.front, managed: false, shows: w.shows, title: w.name }));
      const theirs = (b.rows || []).filter((w) => w.handle).map((w) => ({
        key: String(w.handle), app: nice(w.program), exe: w.path || '', icon: w.ref || (w.path ? 'exe:' + w.path : 'hwnd:' + w.handle),
        agora: '', state: w.shown === false ? 'minimised' : 'normal', focused: !!w.front, managed: false, title: w.name }));
      return [...theirs, ...mine];
    },
    async settings() { const r = await this.see('rows shell-settings'); return (r && r.rows && r.rows[0]) || {}; },
    async pins() {
      const r = await this.see('rows any bar=taskbar');
      return ((r && r.rows) || []).filter((p) => !p.slot && p.kind !== 'widget' && (p.path || /^window\.open /.test(p.does || '')));
    },
    async lensNames() { const r = await this.see('rows lens'); return [...new Set(((r && r.rows) || []).map((x) => (x.name || '').toLowerCase()))]; },
    async system() { const r = await this.see('system.now'); const o = {}; for (const x of (r && r.rows) || []) o[x.key] = x; return o; },
    async media() { const r = await this.see('media.now'); return (r && r.rows && r.rows[0]) || null; },
    async notes() { const r = await this.see('rows notification'); return !refused(r) && Array.isArray(r.rows) ? r.rows : []; },
    async jeff() {
      const r = await this.see('rows presence');
      const p = !refused(r) && r.rows && r.rows[0];
      return p ? { state: p.state || 'here', note: p.note || '' } : { state: 'here', note: '' };
    },
    // A live title, asked now and never kept: the manager's word if it has one, else the window's own (window.native).
    // The manager has no wm.title today (it never hands out titles), so once the kernel says nothing answers to it,
    // the bar stops asking: each hover was one more line in refusals (28 Oct).
    async title(w) {
      const r = this.noTitleWord ? null : await this.see('wm.title ' + w.key);
      if (r && refused(r) && /nothing answers/.test(r.text || r.refused || '')) this.noTitleWord = true;
      const t = r && !refused(r) && r.rows && r.rows[0];
      if (t) return t;
      const hwnd = this.hwnd(w);
      if (hwnd) { try { const title = await agora.native('title', hwnd); if (title) return { title, hwnd }; } catch (e) { /* no grant */ } }
      return hwnd ? { hwnd } : null;
    },
    // actions: wm.* when the manager answers, the native shell otherwise
    focus(w) {
      if (this.wmOK && w.state === 'pinned') return this.act(`wm.focus ${w.key}`);
      if (this.wmOK) return this.act(w.state === 'minimised' ? `wm.restore ${w.key} share=yes` : `wm.focus ${w.key} share=yes`);
      if (w.agora) return this.act(`window.focus ${w.agora}`);
      return this.act(`window.activate handle=${w.key}`);
    },
    async launch(line, exe) {
      if (this.wmOK && exe && /^window\.launch\s/.test(line) && /\.exe$/i.test(exe)) {
        const ready = await this.act(`wm.arrange expect=${JSON.stringify(exe)}`);
        if (refused(ready)) return ready;
      }
      return this.act(line);
    },
    minimise(w) {
      if (w.agora) return this.act(`window.focus ${w.agora}`);          // focus on the front window tucks it away
      if (this.wmOK) return this.act(`wm.minimise ${w.key}`);
      return this.act(`window.activate handle=${w.key}`);              // activate on the front window minimises it
    },
    close(w) {
      if (w.agora) return this.act(`window.close ${w.agora}`);
      if (this.wmOK) return this.act(`wm.close ${w.key}`);
      return this.act(`window.activate handle=${w.key} do=close`);
    },
  };

  // ------------------------------------------------------------------------------------------------ the reading hub
  // watch(api, name, ms, fn): fn(value) now (if there is one) and whenever the reading changes; it runs as the part
  // (api.guard), and the subscription ends with the part (api.cleanup). poke(name): read again now (after an act).
  const loaders = { windows: () => Data.windows(), settings: () => Data.settings(), pins: () => Data.pins(), lenses: () => Data.lensNames(),
    system: () => Data.system(), media: () => Data.media(), notes: () => Data.notes(), jeff: () => Data.jeff() };
  const hub = {};
  function feed(name) {
    if (!hub[name]) hub[name] = { subs: new Set(), value: undefined, sig: '', timer: 0, busy: false };
    return hub[name];
  }
  async function pull(name) {
    const f = feed(name);
    if (f.busy || !f.subs.size) return;
    f.busy = true;
    try {
      const value = await loaders[name]();
      const sig = JSON.stringify(value);
      if (sig !== f.sig) { f.sig = sig; f.value = value; for (const s of [...f.subs]) s.fn(value); }
    } catch (e) { /* a reading failed: try again next time */ }
    finally { f.busy = false; }
  }
  function schedule(name) {
    const f = feed(name);
    nativeTimers.clearTimeout(f.timer);
    if (!f.subs.size) return;
    const ms = Math.max(250, Math.min(...[...f.subs].map((s) => s.ms)));
    f.timer = nativeTimers.setTimeout(async () => { await pull(name); schedule(name); }, ms);
  }
  function watch(api, name, ms, fn) {
    if (!loaders[name]) throw Error('ShellKit has no reading ' + name);
    const f = feed(name), sub = { ms, fn: api.guard(fn) };
    f.subs.add(sub);
    if (f.value !== undefined) sub.fn(f.value);
    if (f.value === undefined) pull(name);
    schedule(name);                     // at the fastest rate any part now asks
    api.cleanup(() => { f.subs.delete(sub); if (!f.subs.size) nativeTimers.clearTimeout(f.timer); });
    return sub;
  }
  const poke = (...names) => { for (const n of names) if (hub[n]) { hub[n].sig = ''; pull(n); } };
  // a tiny bus between parts of one bar (the clock's calendar opens the notifications)
  const bus = new EventTarget();
  const on = (api, type, fn) => { const g = api.guard((e) => fn(e.detail)); bus.addEventListener(type, g); api.cleanup(() => bus.removeEventListener(type, g)); };
  const emit = (type, detail) => bus.dispatchEvent(new CustomEvent(type, { detail }));

  // A part's gesture when the lens arranges one, else the line it has always said (so a lens may leave them out).
  async function fire(api, event, fallback, values) {
    if (api.node.gestures.some((g) => g.event === event)) { try { return await api.fire(event, values || {}); } catch (e) { toast(String(e.message || e)); return { ok: false }; } }
    return ran(Data.act(fallback));
  }

  // ------------------------------------------------------------------------------------------------ popovers
  let lastInput = 'pointer';
  const Pop = {
    cur: null,
    open(id, anchor, build, opts = {}) {
      if (this.cur && this.cur.id === id) { this.close(); return null; }
      this.close(true);
      const body = build();
      const card = opts.card || h('div');
      card.classList.add('pop', ...String(opts.cls || '').split(/\s+/).filter(Boolean));
      for (const [k, v] of Object.entries({ role: 'dialog', 'aria-label': opts.label || id, tabindex: '-1', 'data-pop': id })) card.setAttribute(k, v);
      card.append(body);
      doc.body.append(card);
      anchor.setAttribute('aria-expanded', 'true');
      card.addEventListener('keydown', (e) => {
        if (doc.activeElement !== card || !['ArrowDown', 'ArrowUp', 'Tab'].includes(e.key)) return;
        const f = card.querySelector('[data-autofocus], button:not([disabled]), input');
        if (f) { e.preventDefault(); f.focus(); }
      });
      this.cur = { id, anchor, card, opts, returnTo: doc.activeElement };
      this.position();
      nativeTimers.requestAnimationFrame(() => {
        card.classList.add('in');
        const first = card.querySelector('[data-autofocus]') || card.querySelector('button, input, [tabindex="0"]');
        (lastInput === 'key' && first ? first : card).focus({ preventScroll: true });
        report();
      });
      return card;
    },
    position() {
      const c = this.cur; if (!c) return;
      const a = c.anchor.getBoundingClientRect(), vw = innerWidth, card = c.card;
      const w = card.offsetWidth, hh = card.offsetHeight, gap = c.opts.gap ?? 8;
      let x = a.left + a.width / 2 - w / 2;
      if (c.opts.align === 'left') x = a.left;
      if (c.opts.align === 'right') x = a.right - w;
      x = Math.max(10, Math.min(x, vw - w - 10));
      const y = c.opts.above ? a.top - hh - gap : a.bottom + gap;
      card.style.left = x + 'px';
      card.style.top = Math.max(4, y) + 'px';
      card.style.setProperty('--ox', (a.left + a.width / 2 - x) + 'px');
    },
    close(quiet) {
      const c = this.cur; if (!c) return;
      this.cur = null;
      c.anchor.setAttribute('aria-expanded', 'false');
      try { if (c.opts.onClose) c.opts.onClose(); } catch (e) { /* the part that opened it may have gone */ }
      c.card.classList.remove('in');
      c.card.setAttribute('inert', '');
      const gone = () => c.card.remove();
      if (quiet || root.dataset.reduce === 'yes') gone(); else nativeTimers.setTimeout(() => { gone(); report(); }, 120);
      if (!quiet) { const t = c.returnTo && c.returnTo.isConnected ? c.returnTo : c.anchor; if (t.isConnected) t.focus({ preventScroll: true }); }
      report();
    },
  };
  doc.addEventListener('keydown', () => { lastInput = 'key'; }, true);
  doc.addEventListener('pointerdown', () => { lastInput = 'pointer'; }, true);
  doc.addEventListener('pointerdown', (e) => {
    const c = Pop.cur; if (!c) return;
    if (c.card.contains(e.target) || c.anchor.contains(e.target) || (e.target.closest && e.target.closest('.ask-menu'))) return;
    Pop.close(true);
  }, true);
  doc.addEventListener('keydown', (e) => { if (e.key === 'Escape' && Pop.cur && !doc.querySelector('.ask-menu')) { e.preventDefault(); Pop.close(); } });
  addEventListener('blur', () => { if (Pop.cur && !Pop.cur.opts.sticky) Pop.close(true); });

  // a menu is a popover of rows; arrow keys move, Enter acts. ask: an input from api.askBox(), the menu's last row.
  function Menu(items, ask) {
    const m = h('div', { cls: 'menu', role: 'menu' });
    for (const it of items) {
      if (!it) continue;
      if (it === '-') { m.append(h('div', { cls: 'msep', role: 'separator' })); continue; }
      if (it.head) { m.append(h('div', { cls: 'mhead' }, it.icon || '', h('span', {}, it.head), it.note ? h('small', {}, it.note) : '')); continue; }
      m.append(h('button', { cls: 'mrow' + (it.danger ? ' danger' : ''), role: 'menuitem', disabled: it.disabled ? '' : null,
        on: { click: () => { Pop.close(); it.run && it.run(); } } },
        it.glyph ? glyph(it.glyph) : h('span', { cls: 'gl' }), h('span', { cls: 'mlabel' }, it.label), it.hint ? h('small', {}, it.hint) : ''));
    }
    if (ask) {
      // the painter's ask box: it says `ask` itself and closes the painter's menu; the popover closes with it
      ask.addEventListener('keydown', (e) => { if (e.key === 'Enter' && ask.value.trim()) nativeTimers.setTimeout(() => Pop.close(true), 0); });
      m.append(ask);
    }
    m.addEventListener('keydown', (e) => {
      const rows = [...m.querySelectorAll('.mrow:not([disabled]), .menu-ask')];
      const i = rows.indexOf(doc.activeElement);
      if (e.key === 'ArrowDown') { e.preventDefault(); (rows[(i + 1) % rows.length] || rows[0]).focus(); }
      if (e.key === 'ArrowUp') { e.preventDefault(); (rows[(i - 1 + rows.length) % rows.length] || rows[0]).focus(); }
    });
    return m;
  }

  // a roving toolbar: one tab stop, arrows move between the buttons
  function roving(container, selector = 'button') {
    const items = () => [...container.querySelectorAll(selector)].filter((b) => !b.disabled && b.offsetParent !== null && !b.closest('[data-stale],.pop'));
    const sync = (cur) => items().forEach((b) => b.setAttribute('tabindex', b === cur ? '0' : '-1'));
    container.addEventListener('keydown', (e) => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
      const list = items(), i = list.indexOf(doc.activeElement);
      if (i < 0) return;
      e.preventDefault();
      const n = e.key === 'Home' ? 0 : e.key === 'End' ? list.length - 1 : (i + (e.key === 'ArrowRight' ? 1 : -1) + list.length) % list.length;
      list[n].focus();
    });
    container.addEventListener('focusin', (e) => { if (e.target.matches(selector)) sync(e.target); });
    return { refresh() { const list = items(); const cur = list.find((b) => b.getAttribute('tabindex') === '0') || list[0]; sync(cur); } };
  }

  function toast(text) {
    let t = doc.getElementById('live');
    if (!t) { t = h('div', { id: 'live', role: 'status', 'aria-live': 'polite', cls: 'toast shell-toast' }); doc.body.append(t); }
    t.textContent = text; t.classList.add('on');
    nativeTimers.clearTimeout(toast.t); toast.t = nativeTimers.setTimeout(() => { t.classList.remove('on'); report(); }, 3600);
    report();
  }
  const ran = async (p) => { const r = await p; if (r && (r.ok === false || /^refused/.test(r.text || ''))) toast((r.text || 'That did not work').replace(/^refused:?\s*/, '')); return r; };

  const fmt = {
    time: (d, seconds) => d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', ...(seconds ? { second: '2-digit' } : {}) }).replace(/\s?([AP]M)$/i, ' $1'),
    date: (d) => d.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' }),
    long: (d) => d.toLocaleDateString([], { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }),
  };

  // ------------------------------------------------------------------------------------------------ the window's shape
  // The root part (shell-bar, shell-dock) sets K.shape: () => {reserve, shape}. Everything that opens or closes calls
  // report(); a mutation observer catches the rest. The host checks the numbers and passes them to the window.
  let shapeFn = null, reportT = 0, lastSent = '';
  function report() {
    nativeTimers.cancelAnimationFrame(reportT);
    reportT = nativeTimers.requestAnimationFrame(() => {
      if (Pop.cur && !Pop.cur.anchor.isConnected) {
        // the part that opened it was painted again: find its new self, or close
        const a = Pop.cur.anchor.dataset.path && doc.querySelector(`[data-path="${CSS.escape(Pop.cur.anchor.dataset.path)}"][data-part="${CSS.escape(Pop.cur.anchor.dataset.part || '')}"]`);
        if (a) { Pop.cur.anchor = a; a.setAttribute('aria-expanded', 'true'); } else Pop.close(true);
      }
      if (!shapeFn) return;
      let s;
      try { s = shapeFn(); } catch (e) { return; }
      for (const el of doc.querySelectorAll('.pop.in, .toast.on, .ask-menu')) {
        const b = el.getBoundingClientRect();
        if (b.width && b.height) s.shape.push({ x: b.left, y: b.top, w: b.width, h: b.height, r: el.classList.contains('toast') ? 12 : parseFloat(getComputedStyle(el).borderTopLeftRadius) || 0 });
      }
      window.__shape = s;
      const sig = JSON.stringify(s);
      if (sig === lastSent) return;
      lastSent = sig;
      agora.native('layout', s).catch(() => { lastSent = ''; });
    });
  }
  const thumbs = (tiles) => agora.native('thumbs', tiles).catch(() => 0);
  addEventListener('resize', report);
  // the painter's ask menu opens at the pointer; in a bar it opens just below the rail (or above the pill) instead,
  // so it never covers the part being asked about
  addEventListener('agora-menu', (e) => {
    const m = e.detail && e.detail.open && doc.querySelector('.ask-menu'), bar = doc.querySelector('.rail, .pill');
    if (m && bar) {
      const b = bar.getBoundingClientRect(), r = m.getBoundingClientRect();
      if (bar.classList.contains('rail') && r.top < b.bottom + 6) m.style.top = (b.bottom + 6) + 'px';
      if (bar.classList.contains('pill') && r.bottom > b.top - 8) m.style.top = Math.max(4, b.top - 8 - r.height) + 'px';
    }
    report();
  });
  doc.addEventListener('transitionend', (e) => { if (e.target.classList && e.target.classList.contains('pop')) report(); });
  new MutationObserver(() => report()).observe(doc.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ['class', 'hidden', 'style'] });
  // the host may have been without its window API at first; a slow heartbeat sends the shape again if it changed
  nativeTimers.setInterval(() => { lastSent = ''; report(); }, 15000);

  // ------------------------------------------------------------------------------------------------ a stopped part
  // In a bar a stopped part is a small chip (its last good rendering, dimmed, and a mark); pressing it opens the
  // recovery (Try again / Use the previous version / Turn it off) in a popover. The buttons are the painter's own.
  function stoppedChip(card) {
    if (card.dataset.shellChip) return;
    card.dataset.shellChip = 'yes';
    card.tabIndex = 0;
    const what = card.querySelector('div') ? card.querySelector('div').textContent : 'part';
    card.setAttribute('aria-label', `${what} stopped. Press for what to do`);
    const open = () => {
      const recovery = card.querySelector('.component-recovery');
      const why = card.querySelector('p') ? card.querySelector('p').textContent : '';
      Pop.open('stopped', card, () => h('div', { cls: 'stopped-pop' },
        h('div', { cls: 'mhead' }, glyph('alert'), h('span', {}, card.querySelector('strong') ? card.querySelector('strong').textContent : 'This part stopped'), h('small', {}, what)),
        why ? h('p', { cls: 'why' }, why) : '', recovery || ''),
      { label: what + ' stopped', align: doc.body.dataset.page === 'dock' ? undefined : 'left', above: doc.body.dataset.page === 'dock', gap: 12, cls: 'narrow',
        onClose: () => { if (recovery && card.isConnected) card.append(recovery); } });
    };
    card.addEventListener('click', open);
    card.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); } });
  }
  new MutationObserver(() => { for (const c of doc.querySelectorAll('.rail .component-stopped, .pill .component-stopped')) stoppedChip(c); })
    .observe(doc.documentElement, { childList: true, subtree: true });

  // ------------------------------------------------------------------------------------------------ the theme's switches
  // icons.style (native|plate|mono), reduced motion and island outlines, read from the --ag-* sheet the frame wears
  function readTheme() {
    root.dataset.icons = cssVar('--ag-icon-style') || 'native';
    root.dataset.reduce = cssVar('--ag-motion-reduce') === '1' ? 'yes' : 'no';
    root.dataset.outline = cssVar('--ag-island-outline') === '1' ? 'yes' : 'no';
    report();
  }
  readTheme();
  addEventListener('ag-theme', () => nativeTimers.requestAnimationFrame(readTheme));

  return { h, glyph, Icon, iconUrl, AGORA_APPS, DOCK_APPS, appOf, opensLens, nice, yes, num, cssVar, Data, watch, poke, on, emit, fire,
    Pop, Menu, roving, toast, ran, fmt, report, thumbs,
    set shape(fn) { shapeFn = fn; report(); }, get shape() { return shapeFn; } };
})();
globalThis.ShellKit = ShellKit;
css(SHELL_CSS);
