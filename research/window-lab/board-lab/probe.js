// probe.js (a6010): time a press from the pointer going down to the painted result, in a screen.py page.
// `js @research/window-lab/board-lab/probe.js` installs it once; after each `click`, `wait 2500` then
// `js "__probe.read()"` gives: ms to the first change on the page, ms to the last, each fetch the press made (path, ms,
// KB), and how many parts the page holds. A change is a DOM mutation inside #paint; each read starts the next count.
(() => {
  if (window.__probe) return "probe already in";
  const P = window.__probe = { t0: null, muts: [], fetches: [] };
  const paint = document.getElementById("paint");
  addEventListener("pointerdown", () => { P.t0 = performance.now(); P.muts = []; P.fetches = []; }, true);
  new MutationObserver(ms => { if (P.t0 != null) P.muts.push([performance.now(), ms.length]); })
    .observe(paint, { childList: true, subtree: true, characterData: true, attributes: true });
  const f0 = window.fetch;
  window.fetch = async (u, o) => {
    const t = performance.now(), r = await f0(u, o), b = await r.clone().text();
    if (P.t0 != null) P.fetches.push([String(u).split("?")[0], Math.round(t - P.t0), Math.round(performance.now() - t), Math.round(b.length / 1024)]);
    return r;
  };
  P.read = () => {
    const m = P.muts.map(x => x[0] - P.t0), n = P.muts.reduce((a, x) => a + x[1], 0);
    const out = { first: m.length ? Math.round(m[0]) : null, last: m.length ? Math.round(m[m.length - 1]) : null,
      mutations: n, fetches: P.fetches.map(f => `${f[0]} at ${f[1]} took ${f[2]}ms ${f[3]}KB`),
      parts: paint.querySelectorAll("*").length };
    P.t0 = null; P.muts = []; P.fetches = [];
    return out;
  };
  return "probe in";
})()
