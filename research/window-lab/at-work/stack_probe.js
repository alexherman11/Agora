(() => {
  const f = [...document.querySelectorAll('.l-float')].find(x => x.dataset.folded !== "1");
  if (!f) return 'no open popover';
  const pop = f.querySelector(':scope > [data-key]:not([data-peek])');
  const r = pop.getBoundingClientRect();
  const top = document.elementFromPoint(r.left + 200, r.top + 20);
  const chain = el => { const out = []; for (let e = el; e && e !== document.body; e = e.parentElement) {
    const s = getComputedStyle(e);
    if (s.zIndex !== 'auto' || s.opacity !== '1' || s.transform !== 'none' || s.isolation !== 'auto' || s.contain !== 'none' || s.position !== 'static')
      out.push([(e.dataset.key || e.tagName).slice(-60), s.position, s.zIndex, s.opacity, s.transform.slice(0, 20), s.contain, s.isolation].join(' ')); }
    return out; };
  return { hit: (top && (top.dataset.key || top.className)) || null, inPop: pop.contains(top), hitChain: chain(top), popChain: chain(pop) };
})()
