// shell-notifications: the bell, its unread count and the inbox. Gesture clear (default notice.clear).
export default {mount(api) {
  const K = globalThis.ShellKit, { h, glyph, Pop } = K;
  const badge = api.part('badge', 'i', { class: 'badge' });
  const body = api.part('body', 'button', { class: 'btn bell', 'aria-label': 'Notifications', 'aria-haspopup': 'dialog', 'aria-expanded': 'false' }, glyph('bell'), badge);
  let notes = [];
  K.watch(api, 'notes', 4000, (v) => {
    notes = v;
    const unread = notes.filter((n) => n.unread !== 'no' && n.read !== 'yes').length;
    body.classList.toggle('has', unread > 0);
    badge.textContent = unread > 9 ? '9+' : unread || '';
    body.setAttribute('aria-label', unread ? `Notifications, ${unread} unread` : 'Notifications, none unread');
  });
  const open = () => Pop.open('bell', body, () => h('div', { cls: 'inbox' },
    h('div', { cls: 'ph' }, h('b', {}, 'Notifications'), h('span', { cls: 'grow' }),
      notes.length ? h('button', { cls: 'link', on: { click: () => { K.fire(api, 'clear', 'notice.clear'); K.toast('Cleared'); Pop.close(); K.poke('notes'); } } }, 'Clear') : ''),
    notes.length ? h('ul', {}, notes.slice(0, 8).map((n) => h('li', { cls: n.unread === 'no' ? '' : 'new' }, h('span', { cls: 'dot' }), h('span', {}, n.text || n.title || 'Something happened'), n.at ? h('small', {}, n.at) : '')))
      : h('p', { cls: 'empty' }, 'You are all caught up.')),
  { label: 'Notifications', align: 'right', cls: 'narrow', card: api.part('popover', 'div') });
  body.addEventListener('click', open);
  K.on(api, 'open', (what) => { if (what === 'notifications') open(); });
  return body;
}};
