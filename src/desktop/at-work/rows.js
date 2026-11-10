// the painted lines of At work (keys of the row parts whose fold can open), and the header part's key
(() => {
  const rows = [...document.querySelectorAll('.l-float')].filter(e => e.getClientRects().length && e.dataset.key.includes('house-at-work-row'))
    .map(e => e.dataset.key + '/line');
  const head = [...document.querySelectorAll('[data-key$="/lens:house-at-work-small"]')].filter(e => e.getClientRects().length).map(e => e.dataset.key);
  return { rows, head };
})()
