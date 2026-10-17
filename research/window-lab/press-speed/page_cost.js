// page_cost.js (a6153): in a painted lens page, what a scene answer costs the page itself: the trip, reading its body,
// and parsing it, for the scene this page asks (text=0), five times. screen.py <world> ... js @research/window-lab/press-speed/page_cost.js
(async () => {
  const q = new URLSearchParams(location.search), out = [];
  const u = `/api/scene?session=${encodeURIComponent(q.get("session"))}&as=${q.get("as")}&lens=${q.get("lens")}&view=painter&text=0`;
  for (let i = 0; i < 5; i++) {
    const t0 = performance.now();
    const r = await fetch(u + `&nocache=${Date.now()}`);
    const t1 = performance.now();
    const s = await r.text();
    const t2 = performance.now();
    JSON.parse(s);
    const t3 = performance.now();
    out.push({ headers: Math.round(t1 - t0), body: Math.round(t2 - t1), parse: Math.round(t3 - t2), kb: Math.round(s.length / 1024) });
  }
  return out;
})()
