// shell-launcher: the Agora mark; opens the launcher (Agora apps, pinned programs, or say a line). Alt+Space opens it.
// Handles: apps (comma list of Agora apps, default the dock's); gestures lines (window.open lines), start (window.start).
export default {mount(api, s) {
  const K = globalThis.ShellKit, { h, glyph, Icon, Pop, Data } = K;
  const body = api.part('body', 'button', { class: 'btn mark', 'aria-label': 'Agora launcher', 'aria-haspopup': 'dialog', 'aria-expanded': 'false' },
    Icon('agora:agora', 'Agora', 'bar'));
  let settings = {};
  K.watch(api, 'settings', 4000, (v) => { settings = v; });
  const open = async () => {
    if (Pop.cur && Pop.cur.id === 'launcher') { Pop.close(); return; }
    const [lenses, pins] = await Promise.all([Data.lensNames(), Data.pins()]);
    const have = new Set(lenses);
    const names = (s.apps || settings.dock_apps || K.DOCK_APPS).split(/[ ,]+/).filter(Boolean)
      .filter((n) => ['lines', 'help', 'thing', 'tasks'].includes(n) || have.has(n));
    const entries = [
      ...names.filter((n) => K.AGORA_APPS[n]).map((n) => ({ name: K.AGORA_APPS[n][0], icon: 'agora:' + n, line: K.AGORA_APPS[n][1] })),
      ...pins.map((p) => ({ name: p.label || p.name || 'Pinned', icon: p.path ? 'exe:' + p.path : 'agora:' + K.appOf(K.opensLens(p.does)), line: p.does || `window.launch path=${p.path}` })),
    ];
    const input = h('input', { type: 'text', placeholder: 'Open an app, or say a line', 'aria-label': 'Open an app or say a line', autocomplete: 'off', spellcheck: 'false', 'data-autofocus': '' });
    const grid = h('div', { cls: 'apps', role: 'list' });
    const draw = () => {
      const t = input.value.trim().toLowerCase();
      const shown = entries.filter((e) => !t || e.name.toLowerCase().includes(t));
      grid.replaceChildren(...shown.map((e) => api.part('app', 'button', { class: 'app', role: 'listitem', 'aria-label': `Open ${e.name}`, on: { click: () => { Pop.close(); K.ran(Data.act(e.line)); } } }, Icon(e.icon, e.name, 40), h('span', {}, e.name))));
      draw.first = shown[0];
      if (!shown.length) grid.append(h('p', { cls: 'empty' }, t ? `Press Enter to say "${input.value.trim()}" as a line.` : 'Nothing here yet.'));
    };
    input.oninput = draw;
    input.onkeydown = (e) => {
      if (e.key === 'Enter') { e.preventDefault(); const t = input.value.trim(); Pop.close(); if (draw.first) K.ran(Data.act(draw.first.line)); else if (t) K.ran(Data.act(t)); }
      if (e.key === 'ArrowDown') { e.preventDefault(); const b = grid.querySelector('button'); b && b.focus(); }
    };
    grid.addEventListener('keydown', (e) => {
      const bs = [...grid.querySelectorAll('button')], i = bs.indexOf(document.activeElement);
      const cols = Math.max(1, Math.floor(grid.clientWidth / 92));
      const to = { ArrowRight: i + 1, ArrowLeft: i - 1, ArrowDown: i + cols, ArrowUp: i - cols }[e.key];
      if (to !== undefined) { e.preventDefault(); if (to < 0) input.focus(); else (bs[to] || bs[i]).focus(); }
    });
    draw();
    Pop.open('launcher', body, () => h('div', { cls: 'launch' },
      api.part('search', 'div', { class: 'search' }, glyph('search'), input), grid,
      h('div', { cls: 'foot' },
        h('button', { cls: 'link', on: { click: () => { Pop.close(); K.fire(api, 'lines', 'window.open lines'); } } }, glyph('terminal'), 'Lines'),
        h('button', { cls: 'link', on: { click: () => { Pop.close(); K.fire(api, 'start', 'window.start'); } } }, glyph('grid'), 'Windows Start'))),
    { label: 'Launcher', align: 'left', cls: 'wide', card: api.part('popover', 'div') });
  };
  body.addEventListener('click', open);
  const key = api.guard((e) => { if (e.altKey && e.key === ' ') { e.preventDefault(); body.click(); } });
  document.addEventListener('keydown', key);
  api.cleanup(() => document.removeEventListener('keydown', key));
  return body;
}};
