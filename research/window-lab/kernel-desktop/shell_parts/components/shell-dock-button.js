// shell-dock-button: a fixed button in the dock (the Agora launcher, the overview). Handles: icon (agora:<app> or an
// exe: ref), label, opens launcher|"" ; gesture press (the overview: window.open tasks). Parts body, popover.
export default {mount(api, s) {
  const K = globalThis.ShellKit, { h, glyph, Icon, Pop } = K;
  const label = s.label || 'Agora';
  const launcher = s.opens === 'launcher';
  const b = api.part('body', 'button', { class: 'item ' + (launcher ? 'brand' : String(api.node.name || '').replace(/[^\w-]/g, '')), 'data-id': api.node.name, tabindex: '-1',
    'aria-label': label, ...(launcher ? { 'aria-haspopup': 'dialog', 'aria-expanded': 'false' } : {}) }, Icon(s.icon || 'agora:agora', label, 'dock'));
  b.addEventListener('click', () => {
    if (!launcher) return K.fire(api, 'press', 'window.open tasks');
    Pop.open('launcher', b, () => {
      const entries = ((K.dock && K.dock.items) || []).filter((x) => x.launcher || x.exe);
      const press = (x) => { Pop.close(); const it = document.querySelector(`.pill [data-id="${CSS.escape(x.id)}"]`); if (it) it.click(); };
      const grid = h('div', { cls: 'apps', role: 'list' }, entries.map((e) => api.part('app', 'button', { class: 'app', role: 'listitem', 'aria-label': `Open ${e.app}`, on: { click: () => press(e) } }, Icon(e.icon, e.app, 40), h('span', {}, e.app))));
      return h('div', { cls: 'launch' }, grid, h('div', { cls: 'foot' },
        h('button', { cls: 'link', 'data-autofocus': '', on: { click: () => { Pop.close(); K.fire(api, 'lines', 'window.open lines'); } } }, glyph('terminal'), 'Lines'),
        h('button', { cls: 'link', on: { click: () => { Pop.close(); K.fire(api, 'start', 'window.start'); } } }, glyph('grid'), 'Windows Start')));
    }, { label: 'Launcher', above: true, gap: 12, cls: 'wide', card: api.part('popover', 'div') });
  });
  return b;
}};
