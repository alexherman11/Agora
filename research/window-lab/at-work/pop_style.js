(() => {
  const e = [...document.querySelectorAll('.l-float')].filter(f => f.dataset.folded !== "1")
    .map(f => f.querySelector(':scope > [data-key]:not([data-peek])')).find(Boolean);
  if (!e) return 'no open popover';
  const s = getComputedStyle(e), r = e.getBoundingClientRect();
  return { cls: e.className, bg: s.backgroundColor, width: s.width, pos: s.position, z: s.zIndex, display: s.display,
           align: s.alignItems, rect: [r.left, r.top, r.width, r.height].map(Math.round) };
})()
