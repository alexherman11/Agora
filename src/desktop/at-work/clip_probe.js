(() => {
  const f = [...document.querySelectorAll('.l-float')].find(x => x.dataset.folded !== "1");
  if (!f) return 'no open popover';
  const pop = f.querySelector(':scope > [data-key]:not([data-peek])');
  const pr = pop.getBoundingClientRect(), out = [];
  for (let e = pop; e && e !== document.documentElement; e = e.parentElement) {
    const s = getComputedStyle(e), r = e.getBoundingClientRect();
    if (e === pop || s.overflow !== 'visible' || s.transform !== 'none' || s.contain !== 'none' || s.filter !== 'none' || s.willChange !== 'auto' || s.containerType !== 'normal')
      out.push([(e.dataset.key || e.id || e.tagName).slice(-50), 'ov=' + s.overflow, 'tf=' + s.transform.slice(0, 24), 'ct=' + s.contain, 'cq=' + s.containerType, 'w=' + Math.round(r.width)].join(' '));
  }
  return { pop: [pr.left, pr.top, pr.width, pr.height].map(Math.round), w: getComputedStyle(pop).width, maxw: getComputedStyle(pop).maxWidth, chain: out };
})()
