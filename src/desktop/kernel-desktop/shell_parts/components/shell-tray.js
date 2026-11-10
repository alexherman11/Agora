// shell-tray: the quick-settings button. Its chips are its children (shell-chip: network, volume, battery, or any
// system.now key); pressing it opens one row per chip (each row says that chip's `press` gesture) and the switches
// for the optional readings in the bar (shell-settings show_cpu, show_memory).
export default {mount(api, s) {
  const K = globalThis.ShellKit, { h, glyph, Pop, Data } = K;
  const body = api.part('body', 'button', { class: 'btn qs', 'aria-label': 'Quick settings', 'aria-haspopup': 'dialog', 'aria-expanded': 'false' });
  for (const child of api.children) body.append(api.render(child));
  let sys = {}, settings = {};
  const NAMES = { network: 'Network', volume: 'Sound', battery: 'Battery', cpu: 'CPU', memory: 'Memory' };
  const chips = () => api.children.filter((c) => c.component === 'shell-chip');
  const label = () => {
    const parts = chips().map((c) => {
      const key = c.settings.key, r = sys[key];
      if (!r || (key === 'battery' && !r.value)) return key === 'network' ? 'Network unknown' : '';
      if (key === 'network') return 'Network connected';
      if (key === 'volume') return r.value === 'muted' ? 'volume muted' : `volume ${r.value}`;
      if (key === 'battery') return `battery ${r.value}${/charging/.test(r.detail || '') ? ', charging' : ''}`;
      return `${(NAMES[key] || key).toLowerCase()} ${r.value}`;
    });
    body.setAttribute('aria-label', 'Quick settings. ' + parts.filter(Boolean).join(', '));
  };
  K.watch(api, 'system', 2500, (v) => { sys = v; label(); });
  K.watch(api, 'settings', 4000, (v) => { settings = v; });
  body.addEventListener('click', () => {
    const rows = [];
    for (const c of chips()) {
      const key = c.settings.key, r = sys[key];
      if (key === 'battery' && !(r && r.value)) continue;
      const pct = r && parseInt(r.value, 10);
      const g = key === 'network' ? (r ? 'wifi' : 'wifi-off') : key === 'volume' ? (r && r.value === 'muted' ? 'volume-x' : 'volume')
        : key === 'battery' ? (/charging/.test((r && r.detail) || '') ? 'battery-charging' : 'battery') : key === 'memory' ? 'memory' : 'cpu';
      const value = key === 'network' ? (r ? 'Online' : 'Unknown') : r ? r.value : 'n/a';
      const detail = key === 'network' ? (r ? `${r.value} ${r.detail || ''}`.trim() : '') : key === 'volume' ? (r && r.value !== 'muted' && pct >= 0 ? 'Output volume' : '') : (r && r.detail) || '';
      const name = NAMES[key] || key;
      rows.push(h('button', { cls: 'qrow', 'aria-label': `${name}: ${value}. Open ${name.toLowerCase()} settings`,
        on: { click: () => { Pop.close(); c.gestures.some((x) => x.event === 'press') ? api.fireLatest(c, 'press').catch((e) => K.toast(String(e.message || e))) : K.ran(Data.act(`window.settings which=${key}`)); } } },
        h('span', { cls: 'qg' }, glyph(g)), h('span', { cls: 'qt' }, h('b', {}, name), h('small', {}, detail)), h('span', { cls: 'qv' }, value), glyph('right', 'go')));
      if (key === 'volume' && r && pct >= 0) rows.push(h('div', { cls: 'meter', role: 'meter', 'aria-label': 'Volume', 'aria-valuemin': '0', 'aria-valuemax': '100', 'aria-valuenow': String(pct) }, h('i', { style: { width: pct + '%' } })));
    }
    const toggle = (key, text) => h('button', { cls: 'sw', role: 'switch', 'aria-checked': K.yes(settings['show_' + key]) ? 'true' : 'false', 'aria-label': text,
      on: { click: async (e) => {
        const b = e.currentTarget, next = b.getAttribute('aria-checked') !== 'true';
        b.setAttribute('aria-checked', String(next));
        const id = settings.id;
        await K.ran(Data.act(id ? `set ${id} show_${key}=${next ? 'yes' : 'no'}` : `make kind=shell-settings show_${key}=${next ? 'yes' : 'no'}`));
        K.poke('settings');
      } } }, h('span', {}, text), h('i', {}));
    const switches = String(s.readings || 'cpu,memory').split(/[ ,]+/).filter(Boolean);
    Pop.open('quick', body, () => h('div', { cls: 'quick' }, ...rows,
      switches.length ? h('div', { cls: 'msep' }) : '', switches.length ? h('div', { cls: 'sub' }, 'Show in the bar') : '',
      ...switches.map((k) => toggle(k, NAMES[k] || k))),
    { label: 'Quick settings', align: 'right', cls: 'narrow', card: api.part('popover', 'div') });
  });
  return body;
}};
