// shell-jeff: JEFF's presence (here, busy, away) and a way to the conversation. Gesture open (default: the
// shell-settings jeff_open line, else window.open lines). Parts body, dot, name, popover.
export default {mount(api) {
  const K = globalThis.ShellKit, { h, glyph, Pop, Data } = K;
  const dot = api.part('dot', 'span', { class: 'dot' });
  const name = api.part('name', 'span', { class: 'jn' }, 'JEFF');
  const body = api.part('body', 'button', { class: 'btn jeff', 'aria-label': 'JEFF', 'aria-haspopup': 'dialog', 'aria-expanded': 'false' }, dot, name);
  let j = { state: 'here', note: '' }, settings = {};
  K.watch(api, 'settings', 4000, (v) => { settings = v; });
  K.watch(api, 'jeff', 4000, (v) => {
    j = v || j;
    body.dataset.state = j.state || 'here';
    body.dataset.factState = j.state || 'here';
    body.setAttribute('aria-label', `JEFF is ${j.state || 'here'}${j.note ? ': ' + j.note : ''}. Open JEFF`);
  });
  body.addEventListener('click', () => Pop.open('jeff', body, () => h('div', { cls: 'jeffpop' },
    h('div', { cls: 'who' }, h('span', { cls: 'dot big', 'data-state': j.state }), h('div', {}, h('b', {}, 'JEFF'), h('small', {}, ({ here: 'Here with you', busy: 'Working on something', away: 'Away' })[j.state] || j.state || 'Here'))),
    j.note ? h('p', {}, j.note) : '',
    h('button', { cls: 'link wide', 'data-autofocus': '', on: { click: () => { Pop.close(); K.fire(api, 'open', settings.jeff_open || 'window.open lines'); } } }, glyph('message'), 'Open the conversation')),
  { label: 'JEFF', align: 'right', cls: 'narrow', card: api.part('popover', 'div') }));
  return body;
}};
