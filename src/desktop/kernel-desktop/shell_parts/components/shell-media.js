// shell-media: what is playing, with its cover; pressing it opens play/pause, next and previous.
// Gestures play, next, prev (default media.play, media.next, media.prev). Parts body, art, title, popover.
export default {mount(api) {
  const K = globalThis.ShellKit, { h, glyph, Pop } = K;
  const art = api.part('art', 'span', { class: 'art' });
  const title = api.part('title', 'span', { class: 'mt' });
  const body = api.part('body', 'button', { class: 'btn media', 'aria-label': 'Media', 'aria-haspopup': 'dialog', 'aria-expanded': 'false' }, art, title);
  body.hidden = true;
  let m = null;
  const picture = (src) => (src && /^(data:image\/|blob:)/.test(src) ? h('img', { src, alt: '' }) : glyph('play'));
  K.watch(api, 'media', 2500, (v) => {
    m = v;
    body.hidden = !m;
    if (!m) return;
    if (art.dataset.src !== (m.art || '')) { art.dataset.src = m.art || ''; art.replaceChildren(picture(m.art)); }
    title.textContent = m.title || '';
    body.classList.toggle('playing', !!m.playing);
    body.setAttribute('aria-label', `Media: ${m.title || 'nothing'}${m.artist ? ' by ' + m.artist : ''}, ${m.playing ? 'playing' : 'paused'}`);
  });
  const say = (event, line) => { K.fire(api, event, line).then(() => K.poke('media')); };
  body.addEventListener('click', () => {
    if (!m) return;
    Pop.open('media', body, () => h('div', { cls: 'mediapop' },
      h('div', { cls: 'cover' }, picture(m.art)),
      h('div', { cls: 'meta' }, h('b', {}, m.title), h('span', {}, m.artist || m.player || ''), h('small', {}, m.player ? `${m.player} · ${m.playing ? 'playing' : 'paused'}` : '')),
      h('div', { cls: 'ctl' },
        h('button', { cls: 'btn', 'aria-label': 'Previous', on: { click: () => say('prev', 'media.prev') } }, glyph('prev')),
        h('button', { cls: 'btn big', 'aria-label': m.playing ? 'Pause' : 'Play', 'data-autofocus': '', on: { click: () => say('play', 'media.play') } }, glyph(m.playing ? 'pause' : 'play')),
        h('button', { cls: 'btn', 'aria-label': 'Next', on: { click: () => say('next', 'media.next') } }, glyph('next'))),
      m.duration ? h('div', { cls: 'prog', role: 'progressbar', 'aria-valuemin': '0', 'aria-valuemax': '100', 'aria-valuenow': String(Math.round(100 * (m.position || 0) / m.duration)) },
        h('i', { style: { width: Math.min(100, 100 * (m.position || 0) / m.duration) + '%' } })) : ''),
    { label: 'Media', align: 'right', cls: 'narrow', card: api.part('popover', 'div') });
  });
  return body;
}};
