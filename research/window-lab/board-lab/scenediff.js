// scenediff.js (a6010): which parts of this page's scene changed between two moments, and how. First call stores the
// scene now; the next returns the parts whose paint or acts differ (key, and the first difference), then stores again.
(async () => {
  const q = new URLSearchParams(location.search);
  const r = await (await fetch(`/api/scene?session=${q.get("session")}&as=${q.get("as")}&lens=${q.get("lens")}&view=painter&keys=${encodeURIComponent("Enter,Tab,Shift+Tab,Backspace,Delete")}`)).json();
  const flat = new Map(), walk = n => { flat.set(n.key, n); (n.kids || []).forEach(walk); };
  walk(r.scene);
  const was = window.__scene; window.__scene = flat;
  if (!was) return `stored ${flat.size} parts`;
  const out = [];
  for (const [k, n] of flat) {
    const o = was.get(k);
    if (!o) { out.push(`new ${k}`); continue; }
    const a = JSON.stringify([o.paint, o.acts]), b = JSON.stringify([n.paint, n.acts]);
    if (a !== b) {
      let i = 0; while (i < a.length && a[i] === b[i]) i++;
      out.push(`${k}: ...${a.slice(Math.max(0, i - 40), i + 60)}  ->  ...${b.slice(Math.max(0, i - 40), i + 60)}`);
    }
  }
  for (const k of was.keys()) if (!flat.has(k)) out.push(`gone ${k}`);
  return { changed: out.length, first: out.slice(0, 8) };
})()
