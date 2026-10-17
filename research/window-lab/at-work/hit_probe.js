(() => {
  const f = [...document.querySelectorAll('.l-float')].find(x => x.dataset.folded !== "1");
  if (!f) return 'no open popover';
  const pop = f.querySelector(':scope > [data-key]:not([data-peek])');
  const r = pop.getBoundingClientRect(), out = {};
  for (const x of [100, 300, 400, 500, 650]) {
    const e = document.elementFromPoint(r.left + x, r.top + r.height / 2);
    out[x] = e ? (pop.contains(e) ? 'POP' : (e.dataset.key || e.className || e.tagName).slice(-70)) : null;
  }
  return out;
})()
