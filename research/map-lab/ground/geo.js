// Geography for the map frame: WGS84 lat/lon <-> local metres, the tiny-earth curve, and footprint triangulation.
// Nothing here changes a stored coordinate: every function takes lat/lon (or metres) and returns new numbers.
//
// Spaces:  geographic  {lat, lon} degrees (WGS84), height h in metres above the displayed ground
//          local       {e, n} metres east and north of the fixture's centre (an equirectangular tangent frame;
//                      over 500 m its error against true geodesic distance is far below a centimetre)
//          world       [x, y, z] what the GPU draws: x = east, y = up, z = south. With the curve off, world is
//                      local as it is; with it on, the flat plane is wrapped onto a sphere of radius R whose top
//                      touches the plane at the centre, keeping distance along the ground (an azimuthal
//                      equidistant wrap). Both ways are exactly invertible, so a point always maps back to the
//                      lat/lon it came from.
'use strict';
const Geo = (() => {
  function frame(meta) {
    return {lat0: meta.centre.lat, lon0: meta.centre.lon, mlat: meta.m_per_deg_lat, mlon: meta.m_per_deg_lon};
  }
  const toLocal = (f, lat, lon) => ({e: (lon - f.lon0) * f.mlon, n: (lat - f.lat0) * f.mlat});
  const fromLocal = (f, e, n) => ({lat: f.lat0 + n / f.mlat, lon: f.lon0 + e / f.mlon});

  // local metres (+ height) -> world, curve radius R (0 or less: flat)
  function warp(R, e, h, n) {
    const d = Math.hypot(e, n);
    if (!(R > 0)) return [e, h, -n];
    const r = R + h;
    if (d < 1e-9) return [0, h, 0];
    const t = d / R, s = Math.sin(t) * r / d;
    return [e * s, Math.cos(t) * r - R, -n * s];
  }
  // world -> local metres and height: the exact inverse of warp
  function unwarp(R, x, y, z) {
    if (!(R > 0)) return {e: x, h: y, n: -z};
    const cy = y + R, hor = Math.hypot(x, z), r = Math.hypot(hor, cy);
    const d = Math.atan2(hor, cy) * R;
    return hor < 1e-12 ? {e: 0, n: 0, h: r - R} : {e: x / hor * d, n: -z / hor * d, h: r - R};
  }
  const world = (f, R, lat, lon, h = 0) => { const l = toLocal(f, lat, lon); return warp(R, l.e, h, l.n); };
  function geographic(f, R, p) {
    const l = unwarp(R, p[0], p[1], p[2]);
    return Object.assign(fromLocal(f, l.e, l.n), {h: l.h});
  }
  // where a ray (origin o, direction d) meets the ground: the plane y = 0, or the sphere when curved
  function hitGround(R, o, d) {
    if (!(R > 0)) {
      if (Math.abs(d[1]) < 1e-12) return null;
      const t = -o[1] / d[1];
      return t > 0 ? [o[0] + d[0] * t, 0, o[2] + d[2] * t] : null;
    }
    const oc = [o[0], o[1] + R, o[2]];
    const b = oc[0] * d[0] + oc[1] * d[1] + oc[2] * d[2];
    const c = oc[0] * oc[0] + oc[1] * oc[1] + oc[2] * oc[2] - R * R;
    const a = d[0] * d[0] + d[1] * d[1] + d[2] * d[2];
    const disc = b * b - a * c;
    if (disc < 0) return null;
    const t = (-b - Math.sqrt(disc)) / a;
    return t > 0 ? [o[0] + d[0] * t, o[1] + d[1] * t, o[2] + d[2] * t] : null;
  }

  // ---- triangulation: ear clipping, holes bridged into the outer ring ----
  // rings: arrays of [x, y] (outer first, any winding). Returns indices into the concatenated ring points.
  function area(ring) {
    let a = 0;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) a += (ring[j][0] - ring[i][0]) * (ring[j][1] + ring[i][1]);
    return a / 2;   // > 0: counter-clockwise in x-right/y-up
  }
  const cross = (a, b, c) => (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
  function inTri(a, b, c, p) {
    return cross(a, b, p) >= 0 && cross(b, c, p) >= 0 && cross(c, a, p) >= 0;
  }
  function segHits(a, b, c, d) {          // proper or touching intersection of segments ab and cd
    const d1 = cross(a, b, c), d2 = cross(a, b, d), d3 = cross(c, d, a), d4 = cross(c, d, b);
    return ((d1 > 0) !== (d2 > 0)) && ((d3 > 0) !== (d4 > 0));
  }
  function triangulate(rings) {
    const pts = [], base = [];
    for (const r of rings) { base.push(pts.length); for (const p of r) pts.push(p); }
    const loop = (k, ccw) => {
      const idx = rings[k].map((_, i) => base[k] + i);
      return (area(rings[k]) > 0) === ccw ? idx : idx.reverse();
    };
    let poly = loop(0, true);
    // bridge each hole, rightmost first, from its rightmost vertex to a visible outer vertex
    const holes = rings.slice(1).map((_, i) => loop(i + 1, false))
      .filter(h => h.length >= 3)
      .sort((h1, h2) => Math.max(...h2.map(i => pts[i][0])) - Math.max(...h1.map(i => pts[i][0])));
    for (const h of holes) {
      let hi = 0;
      for (let i = 1; i < h.length; i++) if (pts[h[i]][0] > pts[h[hi]][0]) hi = i;
      const hp = pts[h[hi]];
      let best = -1, bestD = Infinity;
      for (let i = 0; i < poly.length; i++) {
        const q = pts[poly[i]], dd = (q[0] - hp[0]) ** 2 + (q[1] - hp[1]) ** 2;
        if (dd >= bestD) continue;
        let blocked = false;            // the bridge must cross no edge of the polygon or of this hole
        for (const ring of [poly, h]) {
          for (let j = 0; j < ring.length && !blocked; j++) {
            const a = ring[j], b = ring[(j + 1) % ring.length];
            if (a === poly[i] || b === poly[i] || a === h[hi] || b === h[hi]) continue;
            if (segHits(hp, q, pts[a], pts[b])) blocked = true;
          }
        }
        if (!blocked) { best = i; bestD = dd; }
      }
      if (best < 0) continue;            // no clean bridge: the hole is filled rather than the footprint lost
      const hole = h.slice(hi).concat(h.slice(0, hi));
      poly = poly.slice(0, best + 1).concat(hole, [hole[0], poly[best]], poly.slice(best + 1));
    }
    // ear clipping
    const out = [];
    let v = poly.slice(), guard = 0;
    while (v.length > 3 && guard++ < 100000) {
      let cut = false;
      for (let i = 0; i < v.length; i++) {
        const ia = v[(i + v.length - 1) % v.length], ib = v[i], ic = v[(i + 1) % v.length];
        const a = pts[ia], b = pts[ib], c = pts[ic];
        if (cross(a, b, c) <= 1e-12) continue;          // reflex or flat corner
        let inside = false;
        for (const j of v) {
          if (j === ia || j === ib || j === ic) continue;
          const p = pts[j];
          if ((p[0] === a[0] && p[1] === a[1]) || (p[0] === b[0] && p[1] === b[1]) || (p[0] === c[0] && p[1] === c[1])) continue;
          if (inTri(a, b, c, p)) { inside = true; break; }
        }
        if (inside) continue;
        out.push(ia, ib, ic);
        v.splice(i, 1);
        cut = true;
        break;
      }
      if (!cut) {                                         // degenerate leftovers: drop the flattest corner
        let k = 0, m = Infinity;
        for (let i = 0; i < v.length; i++) {
          const c = Math.abs(cross(pts[v[(i + v.length - 1) % v.length]], pts[v[i]], pts[v[(i + 1) % v.length]]));
          if (c < m) { m = c; k = i; }
        }
        v.splice(k, 1);
      }
    }
    if (v.length === 3 && cross(pts[v[0]], pts[v[1]], pts[v[2]]) > 0) out.push(v[0], v[1], v[2]);
    return {pts, tris: out};
  }

  return {frame, toLocal, fromLocal, warp, unwarp, world, geographic, hitGround, triangulate, area};
})();
if (typeof module !== 'undefined') module.exports = Geo;
