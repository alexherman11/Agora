(() => {
  // a6452: does any drawn message spill past its own part (wide tables, code, pictures), and does anything but the feed scroll
  const out = [];
  for (const el of document.querySelectorAll('.md-part')) {
    if (!el.getClientRects().length) continue;
    const box = el.getBoundingClientRect();
    for (const k of el.querySelectorAll('table, .md-code, img, .md-line, figure')) {
      const r = k.getBoundingClientRect();
      if (r.width && r.right > box.right + 1) out.push(`${el.dataset.key.split('/').slice(-3).join('/')} ${k.tagName}.${k.className} spills ${Math.round(r.right - box.right)}px`);
    }
    if (el.scrollWidth > el.clientWidth + 1) out.push(`${el.dataset.key.split('/').slice(-3).join('/')} is wider inside (${el.scrollWidth} > ${el.clientWidth})`);
  }
  const scrolls = [...document.querySelectorAll('[data-key]')].filter(e => { const s = getComputedStyle(e); return /(auto|scroll)/.test(s.overflowY + s.overflowX) && (e.scrollHeight > e.clientHeight + 1 || e.scrollWidth > e.clientWidth + 1); }).map(e => e.dataset.key.split('/').slice(-2).join('/'));
  return { width: innerWidth, docs: document.querySelectorAll('.md-part').length, failed: document.querySelectorAll('[data-md-failed]').length, spills: out.slice(0, 12), scrolling: scrolls };
})()
