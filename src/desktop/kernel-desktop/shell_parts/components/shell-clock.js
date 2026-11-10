// shell-clock: the time and the date; pressing it opens a month calendar with a way to the notifications.
// Handles: date yes|no, seconds yes|no; parts body, time, date, popover (style targets: shell-clock.time size=1.3em).
export default {mount(api, s) {
  const K = globalThis.ShellKit, { h, glyph, fmt, Pop } = K;
  const time = api.part('time', 'b', { class: 't' });
  const date = api.part('date', 'span', { class: 'd' });
  const body = api.part('body', 'button', { class: 'btn clock', 'aria-label': 'Calendar and notifications', 'aria-haspopup': 'dialog', 'aria-expanded': 'false' }, time, date);
  const showDate = s.date !== false && !/^(no|false|0)$/i.test(String(s.date ?? 'yes'));
  const seconds = K.yes(s.seconds);
  date.hidden = !showDate;
  let notes = [];
  K.watch(api, 'notes', 4000, (v) => { notes = v; });
  const tick = () => {
    const d = new Date(), t = fmt.time(d, seconds), dd = fmt.date(d);
    if (time.textContent !== t) time.textContent = t;
    if (date.textContent !== dd) date.textContent = dd;
    body.setAttribute('aria-label', `Calendar and notifications. ${fmt.long(d)}, ${t}`);
  };
  tick();
  api.setInterval(tick, 1000);
  body.addEventListener('click', () => {
    let view = new Date(); view.setDate(1);
    const box = h('div', { cls: 'cal' });
    const draw = () => {
      const today = new Date(), y = view.getFullYear(), m = view.getMonth();
      const first = new Date(y, m, 1).getDay(), days = new Date(y, m + 1, 0).getDate();
      const cells = [];
      for (let i = 0; i < first; i++) cells.push(h('i'));
      for (let d = 1; d <= days; d++) {
        const is = d === today.getDate() && m === today.getMonth() && y === today.getFullYear();
        cells.push(h('span', { cls: 'day' + (is ? ' today' : ''), 'aria-current': is ? 'date' : null, 'aria-label': new Date(y, m, d).toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' }) }, String(d)));
      }
      const dows = [...Array(7)].map((_, i) => new Date(2024, 0, 7 + i).toLocaleDateString([], { weekday: 'narrow' }));
      box.replaceChildren(
        h('div', { cls: 'calhead' }, h('b', {}, view.toLocaleDateString([], { month: 'long', year: 'numeric' })), h('span', { cls: 'grow' }),
          h('button', { cls: 'btn sm', 'aria-label': 'Previous month', on: { click: () => { view = new Date(y, m - 1, 1); draw(); } } }, glyph('left')),
          h('button', { cls: 'btn sm', 'aria-label': 'Next month', on: { click: () => { view = new Date(y, m + 1, 1); draw(); } } }, glyph('right'))),
        h('div', { cls: 'grid7', role: 'grid', 'aria-label': view.toLocaleDateString([], { month: 'long', year: 'numeric' }) }, dows.map((d) => h('em', {}, d)), cells));
    };
    draw();
    const n = notes.length;
    Pop.open('clock', body, () => h('div', { cls: 'calwrap' },
      h('div', { cls: 'bigtime' }, h('b', {}, fmt.time(new Date(), seconds)), h('span', {}, fmt.long(new Date()))), box,
      h('button', { cls: 'link wide', on: { click: () => { Pop.close(); K.emit('open', 'notifications'); } } }, glyph('bell'), n ? `${n} notification${n === 1 ? '' : 's'}` : 'No notifications')),
    { label: 'Calendar and notifications', cls: 'cal-pop', card: api.part('popover', 'div') });
  });
  return body;
}};
