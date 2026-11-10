// clipped.js (a6549): every painted part whose content is taller than its box. A part that hides the rest (overflow
// hidden or clip) is a silent clip unless an ancestor scrolls it; one that scrolls (auto or scroll) is fine. Only the
// outermost clip of each chain is listed, with how much it hides. Run in a page: screen.py js @clipped.js
(() => {
  const vis = e => e.getClientRects().length > 0;
  const rows = [];
  for (const e of document.querySelectorAll("[data-key]")) {
    if (!vis(e)) continue;
    const hidden = e.scrollHeight - e.clientHeight;
    if (hidden < 8) continue;
    const oy = getComputedStyle(e).overflowY;
    const scrolls = oy === "auto" || oy === "scroll";
    // a scrolling ancestor shows all of this part, so a clip inside it is no loss to the reader
    let up = e.parentElement, inScroller = false;
    for (; up; up = up.parentElement) {
      const o = getComputedStyle(up).overflowY;
      if ((o === "auto" || o === "scroll") && up.scrollHeight > up.clientHeight + 1) { inScroller = true; break; }
    }
    if (!scrolls && inScroller) continue;
    // a one-line clamp (text-overflow ellipsis) or a line clamp is meant
    const cs = getComputedStyle(e);
    if (cs.webkitLineClamp && cs.webkitLineClamp !== "none") continue;
    rows.push({ key: e.dataset.key, overflow: oy, box: e.clientHeight, content: e.scrollHeight, hides: hidden,
                scrolls, top: Math.round(e.scrollTop), bar: scrolls ? cs.scrollbarWidth : "" });
  }
  // keep only the outermost clip: drop a silent clip whose ancestor is itself listed as a silent clip
  const silent = rows.filter(r => !r.scrolls);
  const keys = silent.map(r => r.key);
  const outer = silent.filter(r => !keys.some(k => k !== r.key && r.key.startsWith(k + "/")));
  return { silent: outer, scrollers: rows.filter(r => r.scrolls).map(r => `${r.key} ${r.box}/${r.content} at ${r.top}`) };
})()
