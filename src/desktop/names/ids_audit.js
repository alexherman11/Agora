// a6109 (Alex, 16 Oct: 'I should never see id names'): every raw id still readable on the page, as a person sees it.
// A word counts when it is drawn (it has a box, is not hidden, is not a hidden mark's source) and its box meets the
// window. Run with screen.py: js @src/desktop/names/ids_audit.js. -> {visible, inDom, ids: {id: "n first-part"}}
(() => {
  const rx = /(?<![\w-])(?:worker-|builder-)?(?:[afscemp]\d{2,}|cap-\d+)(?![\w-])/g;
  const W = innerWidth, H = innerHeight, seen = {}, dom = {};
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const shown = el => {
    for (let x = el; x && x !== document.body; x = x.parentElement) {
      const cs = getComputedStyle(x);
      if (cs.display === "none" || cs.visibility === "hidden" || cs.opacity === "0") return false;
    }
    return true;
  };
  let n;
  while ((n = walker.nextNode())) {
    const el = n.parentElement;
    if (!el || el.closest("script,style,#term,.desk-term,#said")) continue;     // #said: the scene's source, never shown
    for (const m of n.data.matchAll(rx)) {
      const full = (el.closest("[data-key]") || {}).dataset?.key || "?";
      const key = full.split("/").filter(s => s.startsWith("lens:")).pop() + " …" + full.split("/").slice(-3).join("/");
      (dom[m[0]] ||= []).push(key);
      const r = document.createRange(); r.setStart(n, m.index); r.setEnd(n, m.index + m[0].length);
      const b = r.getBoundingClientRect();
      if (!b.width || b.right < 0 || b.bottom < 0 || b.left > W || b.top > H || !shown(el)) continue;
      // cut by a scrolling or clipping box above it
      let cut = false;
      for (let x = el.parentElement; x && x !== document.body; x = x.parentElement) {
        const cs = getComputedStyle(x);
        if (/(auto|scroll|hidden|clip)/.test(cs.overflow + cs.overflowX + cs.overflowY)) {
          const c = x.getBoundingClientRect();
          if (b.bottom <= c.top || b.top >= c.bottom || b.right <= c.left || b.left >= c.right) { cut = true; break; }
        }
      }
      if (!cut) (seen[m[0]] ||= []).push(key);
    }
  }
  const sum = o => Object.values(o).reduce((a, v) => a + v.length, 0);
  return { visible: sum(seen), inDom: sum(dom),
           ids: Object.fromEntries(Object.entries(seen).map(([k, v]) => [k, v.length + " " + v[0]])) };
})()
