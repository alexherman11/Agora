// probe.js (a6010): time a press from the pointer going down to the painted result, in a screen.py page.
// `js @research/window-lab/board-lab/probe.js` installs it once; after each `click`, `wait 2500` then
// `js "__probe.read()"` gives: ms to the first change on the page, ms to the last, each fetch the press made (path, ms,
// KB), and how many parts the page holds. A change is a DOM mutation inside #paint; each read starts the next count.
(() => {
  if (window.__probe) return "probe already in";
  const P = window.__probe = { t0: null, muts: [], fetches: [] };
  const paint = document.getElementById("paint");
  addEventListener("pointerdown", () => { P.t0 = performance.now(); P.muts = []; P.fetches = []; P.where = []; }, true);
  P.where = [];          // [ms, the nearest keyed part of each change] for `__probe.where` (what a burst repainted)
  new MutationObserver(ms => {
    if (P.t0 == null) return;
    P.muts.push([performance.now(), ms.length]);
    for (const m of ms) { const t = m.target.nodeType === 1 ? m.target : m.target.parentElement, k = t && t.closest("[data-key]");
      P.where.push([Math.round(performance.now() - P.t0), k ? k.dataset.key : "?"]); }
  })
    .observe(paint, { childList: true, subtree: true, characterData: true, attributes: true });
  const f0 = window.fetch;
  window.fetch = async (u, o) => {
    const t = performance.now(), r = await f0(u, o), b = await r.clone().text();
    if (P.t0 != null) P.fetches.push([String(u).split("?")[0], Math.round(t - P.t0), Math.round(performance.now() - t), Math.round(b.length / 1024)]);
    return r;
  };
  P.read = () => {
    const m = P.muts.map(x => x[0] - P.t0), n = P.muts.reduce((a, x) => a + x[1], 0);
    const bursts = [];        // the changes in runs (a gap over 50 ms ends one): [ms at its start, changes in it]
    P.muts.forEach(([t, k]) => { const b = bursts[bursts.length - 1]; if (b && t - P.t0 - b[2] < 50) { b[1] += k; b[2] = t - P.t0; } else bursts.push([Math.round(t - P.t0), k, t - P.t0]); });
    const out = { first: m.length ? Math.round(m[0]) : null, last: m.length ? Math.round(m[m.length - 1]) : null,
      mutations: n, bursts: bursts.map(b => `${b[0]}ms:${b[1]}`).join(" "), fetches: P.fetches.map(f => `${f[0]} at ${f[1]} took ${f[2]}ms ${f[3]}KB`),
      parts: paint.querySelectorAll("*").length };
    P.t0 = null; P.muts = []; P.fetches = [];
    return out;
  };
  // the parts changed after `from` ms, counted by their key cut to `depth` segments (read before __probe.read())
  P.whereAfter = (from, depth) => {
    const c = {};
    for (const [t, k] of P.where) if (t >= from) { const s = k.split("/").slice(0, depth || 6).join("/"); c[s] = (c[s] || 0) + 1; }
    return Object.entries(c).sort((a, b) => b[1] - a[1]).slice(0, 12);
  };
  return "probe in";
})()
