// The map frame: draws the fixture's buildings, roads and green as a light cartoon miniature, and the pins and
// routes its parent sends in one 'draw' message. Draws only when something changes (no render loop).
// Messages (contract a7875, THE SEAM), channel agora-map/1, coordinates always named lat and lon:
//   in   {channel, op:'draw', pins:[{id, rev, lat, lon, height, label, icon, colour}], routes:[{id, rev, label, pins:[ids]}]}
//   out  {channel, op:'press', id}   {channel, op:'drop', lat, lon}   {channel, op:'move', id, rev, lat, lon}
//   all of these travel on the MessagePort the parent's {channel, op:'hello'} carried; nothing on the window counts
'use strict';
(() => {
  const CH = 'agora-map/1';
  const FX = window.MAP_FIXTURE, META = FX.meta, F = Geo.frame(META);
  const CURVE_R = 800;                       // tiny-earth radius in metres, a view setting only
  const q = new URLSearchParams(location.search);
  const $ = id => document.getElementById(id);
  const stats = {frames: 0, drawMs: [], intervals: [], rafRequests: 0, firstFrameMs: null, triangles: 0,
                 lastDrawAt: null, mode: null, renderer: null, sync: false};

  // ---- the fixture in local metres -------------------------------------------------------------------------------
  const ring = flat => { const r = []; for (let i = 0; i < flat.length; i += 2) { const l = Geo.toLocal(F, flat[i], flat[i + 1]); r.push([l.e, l.n]); } return r; };
  const open = r => (r.length > 1 && r[0][0] === r[r.length - 1][0] && r[0][1] === r[r.length - 1][1]) ? r.slice(0, -1) : r;
  const B = FX.buildings.map((b, i) => Object.assign({}, b, {i, loc: b.rings.map(r => open(ring(r)))}));
  const ROADS = FX.roads.map(r => Object.assign({}, r, {loc: ring(r.pts)}));
  const AREAS = FX.areas.map(a => Object.assign({}, a, {loc: a.rings.map(r => open(ring(r)))}));
  const SW = Geo.toLocal(F, META.bbox.south, META.bbox.west), NE = Geo.toLocal(F, META.bbox.north, META.bbox.east);
  const MARGIN = 30;
  const GX0 = SW.e - MARGIN, GX1 = NE.e + MARGIN, GY0 = SW.n - MARGIN, GY1 = NE.n + MARGIN;
  const PALETTE = ['#f3dcc8', '#f1e7cc', '#dde9d3', '#d6e3ee', '#e7dded', '#f2d9d4', '#ece6d8', '#e1ece9'];
  const hash = s => { let h = 2166136261; for (const c of s) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return h >>> 0; };
  const colourOf = b => PALETTE[hash(b.osm) % PALETTE.length];
  const rgb = hex => [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16) / 255);
  const EST = {tag: 0, levels: 1, guess: 2};
  const counts = {tag: 0, levels: 0, guess: 0};
  for (const b of B) counts[b.h_src]++;

  // ---- the plan: ground texture for 3D, and the whole picture for the static fallback ------------------------------
  const ROADSTYLE = {   // [casing width, fill width] in metres, fill colour
    major: [17, 14, '#ffffff'], street: [11, 8.5, '#ffffff'], service: [6.5, 4.5, '#fbfaf5'],
    walk: [7, 6, '#f7f2e7'], path: [2.8, 1.8, '#fbf8f1']};
  function drawPlan(ctx, px, scale, withBuildings) {
    // px: local [e, n] -> canvas [x, y]; scale: canvas pixels per metre
    const poly = (r, close = true) => { ctx.beginPath(); r.forEach((p, i) => { const c = px(p); i ? ctx.lineTo(c[0], c[1]) : ctx.moveTo(c[0], c[1]); }); if (close) ctx.closePath(); };
    const a = px([GX0, GY1]), b = px([GX1, GY0]);
    ctx.fillStyle = '#f1f0ea'; ctx.fillRect(a[0], a[1], b[0] - a[0], b[1] - a[1]);
    const s0 = px([SW.e, NE.n]), s1 = px([NE.e, SW.n]);
    ctx.fillStyle = '#ebeee0'; ctx.fillRect(s0[0], s0[1], s1[0] - s0[0], s1[1] - s0[1]);
    ctx.save(); ctx.beginPath(); ctx.rect(s0[0], s0[1], s1[0] - s0[0], s1[1] - s0[1]); ctx.clip();   // green, like roads, ends with the data
    for (const ar of AREAS) {
      ctx.beginPath();
      for (const r of ar.loc) { r.forEach((p, i) => { const c = px(p); i ? ctx.lineTo(c[0], c[1]) : ctx.moveTo(c[0], c[1]); }); ctx.closePath(); }
      ctx.fillStyle = '#cfe3c1'; ctx.fill('evenodd'); ctx.strokeStyle = '#b8d2a8'; ctx.lineWidth = Math.max(1, .8 * scale); ctx.stroke();
    }
    ctx.restore();
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    const order = ['path', 'walk', 'service', 'street', 'major'];
    for (const pass of [0, 1]) for (const cls of order) for (const r of ROADS) {
      if (r.cls !== cls) continue;
      const st = ROADSTYLE[cls];
      poly(r.loc, false);
      ctx.lineWidth = Math.max(pass ? .8 : 1.6, st[pass] * scale);
      ctx.strokeStyle = pass ? st[2] : '#d8d1c1';
      ctx.stroke();
    }
    for (const bl of B) {                                 // a soft cartoon shadow under each building
      ctx.beginPath();
      for (const r of bl.loc) { r.forEach((p, i) => { const c = px([p[0] + 2.2, p[1] - 2.2]); i ? ctx.lineTo(c[0], c[1]) : ctx.moveTo(c[0], c[1]); }); ctx.closePath(); }
      ctx.fillStyle = 'rgba(95, 88, 74, .16)'; ctx.fill('evenodd');
    }
    if (withBuildings) for (const bl of B) {
      ctx.beginPath();
      for (const r of bl.loc) { r.forEach((p, i) => { const c = px(p); i ? ctx.lineTo(c[0], c[1]) : ctx.moveTo(c[0], c[1]); }); ctx.closePath(); }
      ctx.fillStyle = document.body.classList.contains('mark') ? MARKHEX[EST[bl.h_src]] : colourOf(bl);
      ctx.fill('evenodd'); ctx.strokeStyle = '#8d8577'; ctx.lineWidth = Math.max(.7, .35 * scale); ctx.stroke();
    }
    ctx.setLineDash([Math.max(3, 4 * scale), Math.max(3, 4 * scale)]);  // where the data ends
    ctx.strokeStyle = '#a99f8c'; ctx.lineWidth = Math.max(1, .6 * scale);
    ctx.strokeRect(s0[0], s0[1], s1[0] - s0[0], s1[1] - s0[1]);
    ctx.setLineDash([]);
  }
  const MARKHEX = ['#f0c662', '#bcd6ef', '#f4f4f2'];   // height from a tag, from levels, guessed

  // ---- matrices --------------------------------------------------------------------------------------------------
  const M4 = {
    mul(a, b) { const o = new Float64Array(16); for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) { let s = 0; for (let k = 0; k < 4; k++) s += a[k * 4 + r] * b[c * 4 + k]; o[c * 4 + r] = s; } return o; },
    persp(fovy, asp, n, f) { const t = 1 / Math.tan(fovy / 2), o = new Float64Array(16); o[0] = t / asp; o[5] = t; o[10] = (f + n) / (n - f); o[11] = -1; o[14] = 2 * f * n / (n - f); return o; },
    look(e, c, u) {
      const z = norm([e[0] - c[0], e[1] - c[1], e[2] - c[2]]), x = norm(crs(u, z)), y = crs(z, x);
      return new Float64Array([x[0], y[0], z[0], 0, x[1], y[1], z[1], 0, x[2], y[2], z[2], 0,
        -dot(x, e), -dot(y, e), -dot(z, e), 1]);
    },
    inv(m) {
      const o = new Float64Array(16), [a00, a01, a02, a03, a10, a11, a12, a13, a20, a21, a22, a23, a30, a31, a32, a33] = m;
      const b00 = a00 * a11 - a01 * a10, b01 = a00 * a12 - a02 * a10, b02 = a00 * a13 - a03 * a10, b03 = a01 * a12 - a02 * a11,
        b04 = a01 * a13 - a03 * a11, b05 = a02 * a13 - a03 * a12, b06 = a20 * a31 - a21 * a30, b07 = a20 * a32 - a22 * a30,
        b08 = a20 * a33 - a23 * a30, b09 = a21 * a32 - a22 * a31, b10 = a21 * a33 - a23 * a31, b11 = a22 * a33 - a23 * a32;
      const d = 1 / (b00 * b11 - b01 * b10 + b02 * b09 + b03 * b08 - b04 * b07 + b05 * b06);
      o[0] = (a11 * b11 - a12 * b10 + a13 * b09) * d; o[1] = (a02 * b10 - a01 * b11 - a03 * b09) * d;
      o[2] = (a31 * b05 - a32 * b04 + a33 * b03) * d; o[3] = (a22 * b04 - a21 * b05 - a23 * b03) * d;
      o[4] = (a12 * b08 - a10 * b11 - a13 * b07) * d; o[5] = (a00 * b11 - a02 * b08 + a03 * b07) * d;
      o[6] = (a32 * b02 - a30 * b05 - a33 * b01) * d; o[7] = (a20 * b05 - a22 * b02 + a23 * b01) * d;
      o[8] = (a10 * b10 - a11 * b08 + a13 * b06) * d; o[9] = (a01 * b08 - a00 * b10 - a03 * b06) * d;
      o[10] = (a30 * b04 - a31 * b02 + a33 * b00) * d; o[11] = (a21 * b02 - a20 * b04 - a23 * b00) * d;
      o[12] = (a11 * b07 - a10 * b09 - a12 * b06) * d; o[13] = (a00 * b09 - a01 * b07 + a02 * b06) * d;
      o[14] = (a31 * b01 - a30 * b03 - a32 * b00) * d; o[15] = (a20 * b03 - a21 * b01 + a22 * b00) * d;
      return o;
    },
    app(m, v) { return [0, 1, 2, 3].map(r => m[r] * v[0] + m[4 + r] * v[1] + m[8 + r] * v[2] + m[12 + r] * v[3]); },
  };
  function norm(v) { const l = Math.hypot(...v) || 1; return v.map(x => x / l); }
  function crs(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
  function dot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }

  // ---- view state (never stored data) ----------------------------------------------------------------------------
  const HOME = {yaw: -0.35, pitch: 0.82, dist: 1000, te: 0, tn: 0};
  const home = () => Object.assign({}, HOME, {dist: innerWidth / innerHeight < 1.5 ? 1060 : 930});   // the whole square in view
  const view = Object.assign({curve: false, mark: false, mode: '3d'}, home());
  const R = () => view.curve ? CURVE_R : 0;
  let VP = null, IVP = null, eyeW = null;
  const size = {w: 1, h: 1, dpr: 1};

  // ---- WebGL ----------------------------------------------------------------------------------------------------
  const glc = $('gl');
  let gl = null;
  if (q.get('nogl') !== '1') {
    try { gl = glc.getContext('webgl2', {antialias: true, preserveDrawingBuffer: true}); } catch (e) { gl = null; }
  }
  const WARP = `vec3 warp(vec3 p){ if(uR<=0.0) return p; float d=length(p.xz); if(d<1e-6) return vec3(0.0,p.y,0.0);
    float t=d/uR; float r=uR+p.y; float s=sin(t)*r/d; return vec3(p.x*s, cos(t)*r-uR, p.z*s); }`;
  const VS_LIT = `#version 300 es
    in vec3 aPos; in vec3 aCol; in vec3 aNrm; in float aEst;
    uniform mat4 uVP; uniform float uR; uniform float uMark; uniform float uLine;
    out vec3 vCol;
    ${WARP}
    void main(){
      vec3 c = aCol;
      if (uMark > 0.5 && uLine < 0.5) c = aEst < 0.5 ? vec3(0.941,0.776,0.384) : (aEst < 1.5 ? vec3(0.737,0.839,0.937) : vec3(0.957,0.957,0.949));
      if (uMark > 0.5 && uLine > 0.5) c = vec3(0.45,0.43,0.40);
      vec3 L = normalize(vec3(-0.45, 0.8, 0.35));
      float sh = uLine > 0.5 ? 1.0 : 0.66 + 0.34 * max(dot(normalize(aNrm), L), 0.0);
      vCol = c * sh;
      gl_Position = uVP * vec4(warp(aPos), 1.0);
    }`;
  const FS_LIT = `#version 300 es
    precision mediump float; in vec3 vCol; out vec4 o; void main(){ o = vec4(vCol, 1.0); }`;
  const VS_GROUND = `#version 300 es
    in vec3 aPos; in vec2 aUV; uniform mat4 uVP; uniform float uR; out vec2 vUV;
    ${WARP}
    void main(){ vUV = aUV; gl_Position = uVP * vec4(warp(aPos), 1.0); }`;
  const FS_GROUND = `#version 300 es
    precision mediump float; in vec2 vUV; uniform sampler2D uTex; out vec4 o; void main(){ o = texture(uTex, vUV); }`;

  function program(vs, fs) {
    const p = gl.createProgram();
    for (const [type, src] of [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fs]]) {
      const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
      gl.attachShader(p, s);
    }
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
    return p;
  }
  function vao(prog, data, layout, index) {
    const v = gl.createVertexArray(); gl.bindVertexArray(v);
    const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf); gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
    const stride = layout.reduce((s, l) => s + l[1], 0) * 4;
    let off = 0;
    for (const [name, n] of layout) {
      const loc = gl.getAttribLocation(prog, name);
      if (loc >= 0) { gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, n, gl.FLOAT, false, stride, off); }
      off += n * 4;
    }
    if (index) { const ib = gl.createBuffer(); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, index, gl.STATIC_DRAW); }
    gl.bindVertexArray(null);
    return v;
  }

  // building geometry, kept in flat (unwarped) world space for drawing and for picking
  const geom = {verts: [], tris: [], triOwner: [], lines: []};
  function buildBuildings() {
    const V = [], I = [], owner = [], L = [];
    const push = (x, y, z, c, n, est) => { V.push(x, y, z, c[0], c[1], c[2], n[0], n[1], n[2], est); return V.length / 10 - 1; };
    for (const b of B) {
      const c = rgb(colourOf(b)), est = EST[b.h_src], h = b.h;
      const lc = c.map(x => x * .55);
      const rings = b.loc.filter(r => r.length >= 3);
      if (!rings.length) continue;
      const t = Geo.triangulate(rings);
      const base = V.length / 10;
      for (const p of t.pts) push(p[0], h, -p[1], c, [0, 1, 0], est);
      for (let k = 0; k < t.tris.length; k += 3) { I.push(base + t.tris[k], base + t.tris[k + 1], base + t.tris[k + 2]); owner.push(b.i); }
      rings.forEach((r, ri) => {
        const ccw = Geo.area(r) > 0, out = ri === 0 ? ccw : !ccw;    // walls of holes face into the courtyard
        for (let i = 0; i < r.length; i++) {
          const a = r[i], z = r[(i + 1) % r.length];
          const dx = z[0] - a[0], dn = z[1] - a[1], len = Math.hypot(dx, dn);
          if (len < 1e-6) continue;
          const nn = out ? [dn / len, -dx / len] : [-dn / len, dx / len];
          const nrm = [nn[0], 0, -nn[1]];
          const k = Math.max(1, Math.ceil(len / 12));             // short pieces, so walls follow a curved ground
          for (let j = 0; j < k; j++) {
            const e0 = a[0] + dx * j / k, n0 = a[1] + dn * j / k, e1 = a[0] + dx * (j + 1) / k, n1 = a[1] + dn * (j + 1) / k;
            const v0 = push(e0, 0, -n0, c, nrm, est), v1 = push(e1, 0, -n1, c, nrm, est);
            const v2 = push(e1, h, -n1, c, nrm, est), v3 = push(e0, h, -n0, c, nrm, est);
            I.push(v0, v1, v2, v0, v2, v3); owner.push(b.i, b.i);
          }
          L.push(a[0], h, -a[1], ...lc, 0, 1, 0, est, z[0], h, -z[1], ...lc, 0, 1, 0, est);   // roof edge
          const p = r[(i + r.length - 1) % r.length];                                       // corner line where it turns
          const turn = Math.abs(Math.atan2(cross2([a[0] - p[0], a[1] - p[1]], [dx, dn]), dot2([a[0] - p[0], a[1] - p[1]], [dx, dn])));
          if (turn > 0.35) for (let j = 0; j < 4; j++) L.push(a[0], h * j / 4, -a[1], ...lc, 0, 1, 0, est, a[0], h * (j + 1) / 4, -a[1], ...lc, 0, 1, 0, est);
        }
      });
    }
    geom.verts = new Float32Array(V); geom.tris = new Uint32Array(I); geom.triOwner = owner; geom.lines = new Float32Array(L);
  }
  const cross2 = (a, b) => a[0] * b[1] - a[1] * b[0], dot2 = (a, b) => a[0] * b[0] + a[1] * b[1];

  const G = {};
  function initGL() {
    buildBuildings();
    G.lit = program(VS_LIT, FS_LIT); G.ground = program(VS_GROUND, FS_GROUND);
    const LAY = [['aPos', 3], ['aCol', 3], ['aNrm', 3], ['aEst', 1]];
    G.bVao = vao(G.lit, geom.verts, LAY, geom.tris); G.bCount = geom.tris.length;
    G.lVao = vao(G.lit, geom.lines, LAY, null); G.lCount = geom.lines.length / 10;
    const N = 64, gv = [], gi = [];                       // the ground: a grid fine enough to bend with the curve
    for (let j = 0; j <= N; j++) for (let i = 0; i <= N; i++) {
      const e = GX0 + (GX1 - GX0) * i / N, n = GY0 + (GY1 - GY0) * j / N;
      gv.push(e, 0, -n, i / N, 1 - j / N);
    }
    for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
      const a = j * (N + 1) + i; gi.push(a, a + 1, a + N + 2, a, a + N + 2, a + N + 1);
    }
    G.gVao = vao(G.ground, new Float32Array(gv), [['aPos', 3], ['aUV', 2]], new Uint32Array(gi)); G.gCount = gi.length;
    G.gridCell = Math.max((GX1 - GX0) / N, (GY1 - GY0) / N);
    G.tex = gl.createTexture();
    paintGroundTexture();
    stats.triangles = (G.bCount + G.gCount) / 3;
    stats.trianglesBuildings = G.bCount / 3; stats.trianglesGround = G.gCount / 3; stats.lines = G.lCount / 2;
    const dbg = gl.getExtension('WEBGL_debug_renderer_info');
    stats.renderer = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
    G.aniso = gl.getExtension('EXT_texture_filter_anisotropic');
  }
  function paintGroundTexture() {
    const S = 2048, cv = document.createElement('canvas'); cv.width = cv.height = S;
    const ctx = cv.getContext('2d');
    const sx = S / (GX1 - GX0), sy = S / (GY1 - GY0);
    drawPlan(ctx, p => [(p[0] - GX0) * sx, (GY1 - p[1]) * sy], (sx + sy) / 2, false);
    gl.bindTexture(gl.TEXTURE_2D, G.tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, cv);
    gl.generateMipmap(gl.TEXTURE_2D);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    const an = gl.getExtension('EXT_texture_filter_anisotropic');
    if (an) gl.texParameterf(gl.TEXTURE_2D, an.TEXTURE_MAX_ANISOTROPY_EXT, Math.min(8, gl.getParameter(an.MAX_TEXTURE_MAX_ANISOTROPY_EXT)));
  }

  // ---- camera and projection -------------------------------------------------------------------------------------
  function camera() {
    const t = Geo.warp(R(), view.te, 0, view.tn);
    const cp = Math.cos(view.pitch);
    const off = [-Math.sin(view.yaw) * cp, Math.sin(view.pitch), Math.cos(view.yaw) * cp];
    eyeW = [t[0] + off[0] * view.dist, t[1] + off[1] * view.dist, t[2] + off[2] * view.dist];
    const P = M4.persp(40 * Math.PI / 180, size.w / size.h, view.dist * 0.02, view.dist * 6);
    VP = M4.mul(P, M4.look(eyeW, t, [0, 1, 0]));
    IVP = M4.inv(VP);
  }
  // static plan: local metres <-> css pixels, the square fitted into the window
  function planXf() {
    const pad = 24, w = GX1 - GX0, h = GY1 - GY0, s = Math.min((size.w - 2 * pad) / w, (size.h - 2 * pad) / h);
    return {s, ox: (size.w - w * s) / 2, oy: (size.h - h * s) / 2};
  }
  // lat/lon/height -> css pixel [x, y] (null when behind the eye)
  function project(lat, lon, h = 0) {
    if (view.mode === 'static') {
      const l = Geo.toLocal(F, lat, lon), x = planXf();
      return [x.ox + (l.e - GX0) * x.s, x.oy + (GY1 - l.n) * x.s];
    }
    const p = Geo.world(F, R(), lat, lon, h), c = M4.app(VP, [p[0], p[1], p[2], 1]);
    if (c[3] <= 1e-9) return null;
    return [(c[0] / c[3] + 1) / 2 * size.w, (1 - c[1] / c[3]) / 2 * size.h];
  }
  // css pixel -> the ray through it, in world space
  function ray(x, y) {
    const nx = x / size.w * 2 - 1, ny = 1 - y / size.h * 2;
    const a = M4.app(IVP, [nx, ny, -1, 1]), b = M4.app(IVP, [nx, ny, 1, 1]);
    const o = [a[0] / a[3], a[1] / a[3], a[2] / a[3]], f = [b[0] / b[3], b[1] / b[3], b[2] / b[3]];
    return {o, d: norm([f[0] - o[0], f[1] - o[1], f[2] - o[2]])};
  }
  // css pixel -> the ground's lat/lon under it (null: sky)
  function pick(x, y) {
    if (view.mode === 'static') {
      const t = planXf(), l = {e: GX0 + (x - t.ox) / t.s, n: GY1 - (y - t.oy) / t.s};
      return Geo.fromLocal(F, l.e, l.n);
    }
    const r = ray(x, y), hit = Geo.hitGround(R(), r.o, r.d);
    if (!hit) return null;
    const g = Geo.geographic(F, R(), hit);
    return {lat: g.lat, lon: g.lon};
  }
  // css pixel -> the building under it (nearest hit along the ray), for the info panel
  let warped = {R: null, v: null};
  function pickBuilding(x, y) {
    if (view.mode === 'static') {
      const g = pick(x, y), l = Geo.toLocal(F, g.lat, g.lon);
      return B.find(b => inside(b.loc, [l.e, l.n])) || null;
    }
    if (warped.R !== R()) {
      const v = new Float64Array(geom.verts.length / 10 * 3);
      for (let i = 0, j = 0; i < geom.verts.length; i += 10, j += 3) {
        const w = Geo.warp(R(), geom.verts[i], geom.verts[i + 1], -geom.verts[i + 2]); v[j] = w[0]; v[j + 1] = w[1]; v[j + 2] = w[2];
      }
      warped = {R: R(), v};
    }
    const r = ray(x, y), v = warped.v, T = geom.tris;
    let best = Infinity, who = -1;
    for (let k = 0; k < T.length; k += 3) {
      const a = T[k] * 3, b = T[k + 1] * 3, c = T[k + 2] * 3;
      const e1 = [v[b] - v[a], v[b + 1] - v[a + 1], v[b + 2] - v[a + 2]], e2 = [v[c] - v[a], v[c + 1] - v[a + 1], v[c + 2] - v[a + 2]];
      const p = crs(r.d, e2), det = dot(e1, p);
      if (Math.abs(det) < 1e-12) continue;
      const s = [r.o[0] - v[a], r.o[1] - v[a + 1], r.o[2] - v[a + 2]], u = dot(s, p) / det;
      if (u < 0 || u > 1) continue;
      const qq = crs(s, e1), w = dot(r.d, qq) / det;
      if (w < 0 || u + w > 1) continue;
      const t = dot(e2, qq) / det;
      if (t > 0 && t < best) { best = t; who = geom.triOwner[k / 3]; }
    }
    return who >= 0 ? B[who] : null;
  }
  function inside(rings, p) {
    let c = false;
    for (const r of rings) for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
      if (((r[i][1] > p[1]) !== (r[j][1] > p[1])) && p[0] < (r[j][0] - r[i][0]) * (p[1] - r[i][1]) / (r[j][1] - r[i][1]) + r[i][0]) c = !c;
    }
    return c;
  }

  // ---- drawing on demand -----------------------------------------------------------------------------------------
  let pending = false;
  function requestRender() {
    if (pending) return;
    pending = true; stats.rafRequests++;
    requestAnimationFrame(t => { pending = false; if (stats.lastDrawAt != null) stats.intervals.push(t - stats.lastDrawAt); stats.lastDrawAt = t; draw(); });
  }
  function resize() {
    const dpr = window.devicePixelRatio || 1, w = Math.max(1, innerWidth), h = Math.max(1, innerHeight);
    Object.assign(size, {w, h, dpr});
    for (const c of [glc, $('plan'), $('ov')]) { c.width = Math.round(w * dpr); c.height = Math.round(h * dpr); }
    if (view.mode === 'static') paintPlan();
  }
  function paintPlan() {
    const cv = $('plan'), ctx = cv.getContext('2d'), t = planXf();
    ctx.setTransform(size.dpr, 0, 0, size.dpr, 0, 0);
    ctx.clearRect(0, 0, size.w, size.h);
    drawPlan(ctx, p => [t.ox + (p[0] - GX0) * t.s, t.oy + (GY1 - p[1]) * t.s], t.s, true);
  }
  function draw() {
    const t0 = performance.now();
    if (view.mode === '3d') {
      camera();
      gl.viewport(0, 0, glc.width, glc.height);
      gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      gl.enable(gl.DEPTH_TEST);
      const vp = new Float32Array(VP);
      gl.useProgram(G.ground);
      gl.uniformMatrix4fv(gl.getUniformLocation(G.ground, 'uVP'), false, vp);
      gl.uniform1f(gl.getUniformLocation(G.ground, 'uR'), R());
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, G.tex);
      gl.uniform1i(gl.getUniformLocation(G.ground, 'uTex'), 0);
      gl.enable(gl.POLYGON_OFFSET_FILL); gl.polygonOffset(2, 4);
      gl.bindVertexArray(G.gVao); gl.drawElements(gl.TRIANGLES, G.gCount, gl.UNSIGNED_INT, 0);
      gl.useProgram(G.lit);
      gl.uniformMatrix4fv(gl.getUniformLocation(G.lit, 'uVP'), false, vp);
      gl.uniform1f(gl.getUniformLocation(G.lit, 'uR'), R());
      gl.uniform1f(gl.getUniformLocation(G.lit, 'uMark'), view.mark ? 1 : 0);
      gl.uniform1f(gl.getUniformLocation(G.lit, 'uLine'), 0);
      gl.polygonOffset(1, 1);
      gl.bindVertexArray(G.bVao); gl.drawElements(gl.TRIANGLES, G.bCount, gl.UNSIGNED_INT, 0);
      gl.disable(gl.POLYGON_OFFSET_FILL);
      gl.uniform1f(gl.getUniformLocation(G.lit, 'uLine'), 1);
      gl.bindVertexArray(G.lVao); gl.drawArrays(gl.LINES, 0, G.lCount);
      gl.bindVertexArray(null);
      if (stats.sync || stats.firstFrameMs == null) gl.finish();
    }
    drawOverlay();
    const ms = performance.now() - t0;
    stats.frames++; stats.drawMs.push(ms);
    if (stats.drawMs.length > 4000) stats.drawMs.shift();
    if (stats.firstFrameMs == null) stats.firstFrameMs = performance.now();
  }

  // ---- pins and routes: only what the last 'draw' said --------------------------------------------------------------
  let drawn = {pins: [], routes: []};       // the last valid draw, as received (never changed by the frame)
  const shown = new Map();                  // id -> {lat, lon} where a pin is shown while a move is pending
  let selected = null;
  function pinAt(p) { const s = shown.get(p.id); return s ? s : p; }
  function drawOverlay() {
    const cv = $('ov'), ctx = cv.getContext('2d');
    ctx.setTransform(size.dpr, 0, 0, size.dpr, 0, 0); ctx.clearRect(0, 0, size.w, size.h);
    const byId = new Map(drawn.pins.map(p => [p.id, p]));
    for (const r of drawn.routes) {                        // a route: the pins in order, along the ground
      const ps = r.pins.map(id => byId.get(id)).filter(Boolean);
      const path = [];
      for (let i = 0; i + 1 < ps.length; i++) {
        const a = pinAt(ps[i]), b = pinAt(ps[i + 1]);
        for (let k = 0; k <= 24; k++) { const s = project(a.lat + (b.lat - a.lat) * k / 24, a.lon + (b.lon - a.lon) * k / 24, 0); if (s) path.push(s); }
      }
      if (path.length < 2) continue;
      ctx.lineJoin = ctx.lineCap = 'round';
      for (const [w, c] of [[7, 'rgba(255,255,255,.95)'], [3.5, '#2a7f8f']]) {
        ctx.beginPath(); path.forEach((s, i) => i ? ctx.lineTo(s[0], s[1]) : ctx.moveTo(s[0], s[1]));
        ctx.lineWidth = w; ctx.strokeStyle = c; ctx.setLineDash(c === '#2a7f8f' ? [9, 6] : []); ctx.stroke();
      }
      ctx.setLineDash([]);
      for (let i = 0; i + 1 < ps.length; i++) {             // an arrow halfway along each leg: the order
        const a = pinAt(ps[i]), b = pinAt(ps[i + 1]);
        const m = project((a.lat + b.lat) / 2, (a.lon + b.lon) / 2, 0), n = project(a.lat + (b.lat - a.lat) * .52, a.lon + (b.lon - a.lon) * .52, 0);
        if (!m || !n) continue;
        const ang = Math.atan2(n[1] - m[1], n[0] - m[0]);
        ctx.save(); ctx.translate(m[0], m[1]); ctx.rotate(ang); ctx.beginPath();
        ctx.moveTo(7, 0); ctx.lineTo(-5, -6); ctx.lineTo(-5, 6); ctx.closePath();
        ctx.fillStyle = '#2a7f8f'; ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.stroke(); ctx.fill(); ctx.restore();
      }
    }
    for (const p of drawn.pins) {                          // the exact ground point, and a stick when raised
      const a = pinAt(p), g = project(a.lat, a.lon, 0), t = project(a.lat, a.lon, p.height);
      const el = pinEls.get(p.id);
      if (!g || !t) { if (el) el.style.display = 'none'; continue; }
      ctx.beginPath(); ctx.ellipse(g[0], g[1], 6, 3, 0, 0, Math.PI * 2); ctx.fillStyle = 'rgba(40,40,40,.25)'; ctx.fill();
      if (p.height > 0) { ctx.beginPath(); ctx.moveTo(g[0], g[1]); ctx.lineTo(t[0], t[1]); ctx.strokeStyle = '#555'; ctx.lineWidth = 1.5; ctx.stroke(); }
      if (el) { el.style.display = ''; el.style.left = t[0] + 'px'; el.style.top = t[1] + 'px'; }
    }
  }
  const pinEls = new Map();
  function rebuildPins() {
    const box = $('pins'), list = $('pinlist');
    box.textContent = ''; list.textContent = ''; pinEls.clear();
    for (const p of drawn.pins) {
      const el = document.createElement('button');
      el.type = 'button'; el.className = 'pin' + (p.id === selected ? ' sel' : '') + (shown.has(p.id) ? ' pending' : '');
      el.style.setProperty('--c', p.colour || '#e0603a');
      el.setAttribute('aria-label', 'Pin: ' + p.label);
      const tag = document.createElement('span'); tag.className = 'tag'; tag.textContent = p.label;
      const head = document.createElement('span'); head.className = 'head';
      const ic = document.createElement('span'); ic.textContent = p.icon || ''; head.appendChild(ic);
      el.append(tag, head);
      el.style.transform = 'translate(-50%, calc(-100% - 5px))';
      pinDrag(el, p);
      box.appendChild(el); pinEls.set(p.id, el);
      const li = document.createElement('li'), b = document.createElement('button');
      b.type = 'button'; b.textContent = p.label; b.title = `${p.lat.toFixed(6)}, ${p.lon.toFixed(6)} (lat, lon)`;
      b.onclick = () => { select(p.id); send({op: 'press', id: p.id}); };
      li.appendChild(b); list.appendChild(li);
    }
  }
  function select(id) { selected = id; for (const [k, el] of pinEls) el.classList.toggle('sel', k === id); }
  function pinDrag(el, p) {
    let start = null, moved = false;
    el.addEventListener('pointerdown', e => {
      if (e.button !== 0) return;
      e.stopPropagation(); el.setPointerCapture(e.pointerId);
      const tip = project(pinAt(p).lat, pinAt(p).lon, p.height);
      start = {x: e.clientX, y: e.clientY, dx: tip ? tip[0] - e.clientX : 0, dy: tip ? tip[1] - e.clientY : 0}; moved = false;
    });
    el.addEventListener('pointermove', e => {
      if (!start) return;
      if (!moved && Math.hypot(e.clientX - start.x, e.clientY - start.y) < 5) return;
      moved = true;
      const g = pick(e.clientX + start.dx, e.clientY + start.dy);
      if (g) { shown.set(p.id, g); el.classList.add('pending'); requestRender(); }
    });
    const end = e => {
      if (!start) return;
      const was = moved; start = null; moved = false;
      if (e.type === 'pointercancel') { shown.delete(p.id); el.classList.remove('pending'); requestRender(); return; }
      if (was && shown.has(p.id)) {
        const g = shown.get(p.id);
        send({op: 'move', id: p.id, rev: p.rev, lat: g.lat, lon: g.lon});
        status(`moved ${p.label}: waiting for the world`);
      } else { select(p.id); send({op: 'press', id: p.id}); }
    };
    el.addEventListener('pointerup', end); el.addEventListener('pointercancel', end);
    el.addEventListener('click', e => { if (e.detail === 0) { select(p.id); send({op: 'press', id: p.id}); } });  // keyboard
  }

  // ---- messages --------------------------------------------------------------------------------------------------
  // Who is speaking (a7875): a sandboxed frame's origin is 'null', so the host proves itself by handing this load one
  // MessagePort in a 'hello'. Draws are taken from that port only, and press, drop and move go out on it only.
  const outbox = [], refusals = [];
  let port = null;
  function send(m) {
    const msg = Object.assign({channel: CH}, m);
    outbox.push(msg);
    if (port) port.postMessage(msg);           // ids and coordinates only; never a command, never an actor
  }
  const ID = /^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$/;
  const fin = (v, lo, hi) => typeof v === 'number' && Number.isFinite(v) && v >= lo && v <= hi;
  const revOk = v => (typeof v === 'number' && Number.isFinite(v)) || (typeof v === 'string' && v.length <= 64);
  function checkPin(p) {
    if (!p || typeof p !== 'object' || Array.isArray(p)) return 'not an object';
    if (typeof p.id !== 'string' || !ID.test(p.id)) return 'bad id';
    if (!revOk(p.rev)) return 'bad rev';
    if (!fin(p.lat, -90, 90)) return 'lat not a finite number in -90..90';
    if (!fin(p.lon, -180, 180)) return 'lon not a finite number in -180..180';
    if (p.height !== undefined && p.height !== null && !fin(p.height, 0, 10000)) return 'height not a finite number in 0..10000';
    if (p.label !== undefined && (typeof p.label !== 'string' || p.label.length > 200)) return 'bad label';
    if (p.icon !== undefined && p.icon !== null && p.icon !== '' && (typeof p.icon !== 'string' || [...p.icon].length > 4)) return 'bad icon';
    if (p.colour !== undefined && p.colour !== null && p.colour !== '' && !(typeof p.colour === 'string' && /^#[0-9a-fA-F]{6}$/.test(p.colour))) return 'bad colour';
    return null;
  }
  function checkRoute(r) {
    if (!r || typeof r !== 'object' || Array.isArray(r)) return 'not an object';
    if (typeof r.id !== 'string' || !ID.test(r.id)) return 'bad id';
    if (!revOk(r.rev)) return 'bad rev';
    if (r.label !== undefined && (typeof r.label !== 'string' || r.label.length > 200)) return 'bad label';
    if (!Array.isArray(r.pins) || r.pins.length > 500 || !r.pins.every(x => typeof x === 'string' && ID.test(x))) return 'pins must be a list of ids';
    return null;
  }
  // a whole message: refused entirely only when it is not a draw at all; a bad pin or route refuses only itself
  function receive(d) {
    if (!d || typeof d !== 'object' || Array.isArray(d)) return refuse('not an object');
    if (d.channel !== CH) return refuse('wrong channel');
    if (d.op !== 'draw') return refuse('unknown op ' + JSON.stringify(String(d.op)).slice(0, 40));
    if (!Array.isArray(d.pins) || d.pins.length > 2000) return refuse('pins must be a list');
    if (d.routes !== undefined && (!Array.isArray(d.routes) || d.routes.length > 500)) return refuse('routes must be a list');
    const pins = [], routes = [], seen = new Set(), bad = [];
    for (const p of d.pins) {
      const why = checkPin(p) || (seen.has(p.id) ? 'duplicate id' : null);
      if (why) { bad.push(`pin ${typeof p?.id === 'string' ? p.id.slice(0, 40) : '?'}: ${why}`); continue; }
      seen.add(p.id);
      pins.push({id: p.id, rev: p.rev, lat: p.lat, lon: p.lon, height: p.height || 0, label: p.label || p.id,
                 icon: p.icon || '', colour: p.colour || ''});          // only the named fields are kept
    }
    for (const r of d.routes || []) {
      const why = checkRoute(r);
      if (why) { bad.push(`route ${typeof r?.id === 'string' ? r.id.slice(0, 40) : '?'}: ${why}`); continue; }
      routes.push({id: r.id, rev: r.rev, label: r.label || r.id, pins: r.pins.slice()});
    }
    drawn = {pins, routes};
    shown.clear();
    rebuildPins();
    for (const b of bad) refusals.push(b);
    status(bad.length ? `drew ${pins.length} pins, ${routes.length} routes; refused ${bad.length}: ${bad[0]}` : '');
    requestRender();
    return {pins: pins.length, routes: routes.length, refused: bad};
  }
  function refuse(why) { refusals.push(why); status('refused a message: ' + why); return {refused: [why]}; }
  window.addEventListener('message', ev => {
    const d = ev.data;
    if (window.parent !== window && ev.source === window.parent && d && d.channel === CH && d.op === 'hello' && ev.ports[0]) {
      if (port) port.close();
      port = ev.ports[0];
      port.onmessage = m => receive(m.data);
      return;
    }
    refuse('posted to the window, not on the port');      // even a well-formed draw
  });

  // ---- input -----------------------------------------------------------------------------------------------------
  let drag = null;
  glc.addEventListener('pointerdown', e => {
    drag = {x: e.clientX, y: e.clientY, pan: e.button === 2 || e.shiftKey, moved: false};
    glc.setPointerCapture(e.pointerId); glc.classList.add('dragging');
  });
  glc.addEventListener('pointermove', e => {
    if (!drag) return;
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    if (!drag.moved && Math.hypot(dx, dy) < 3) return;
    drag.moved = true; drag.x = e.clientX; drag.y = e.clientY;
    if (drag.pan) {
      const k = view.dist * 0.0016, c = Math.cos(view.yaw), s = Math.sin(view.yaw);
      view.te += (dy * s - dx * c) * k; view.tn += (dx * s + dy * c) * k;   // the ground follows the pointer
      view.te = clamp(view.te, GX0, GX1); view.tn = clamp(view.tn, GY0, GY1);
    } else {
      view.yaw += dx * 0.006; view.pitch = clamp(view.pitch + dy * 0.005, 0.2, 1.52);
    }
    requestRender();
  });
  const endDrag = e => {
    if (!drag) return;
    const click = !drag.moved && e.type === 'pointerup' && e.button === 0;
    drag = null; glc.classList.remove('dragging');
    if (click) showInfo(pickBuilding(e.clientX, e.clientY));
  };
  glc.addEventListener('pointerup', endDrag); glc.addEventListener('pointercancel', endDrag);
  glc.addEventListener('contextmenu', e => e.preventDefault());
  glc.addEventListener('wheel', e => { e.preventDefault(); view.dist = clamp(view.dist * Math.exp(e.deltaY * 0.0012), 90, 2200); requestRender(); }, {passive: false});
  const dropAt = (x, y) => { const g = pick(x, y); if (g) send({op: 'drop', lat: g.lat, lon: g.lon}); };
  glc.addEventListener('dblclick', e => dropAt(e.clientX, e.clientY));
  $('plan').addEventListener('dblclick', e => dropAt(e.clientX, e.clientY));
  $('plan').addEventListener('click', e => showInfo(pickBuilding(e.clientX, e.clientY)));
  glc.addEventListener('keydown', e => {
    const k = e.key, step = 0.08;
    if (k === 'ArrowLeft') view.yaw -= step; else if (k === 'ArrowRight') view.yaw += step;
    else if (k === 'ArrowUp') view.pitch = clamp(view.pitch + step, 0.2, 1.52); else if (k === 'ArrowDown') view.pitch = clamp(view.pitch - step, 0.2, 1.52);
    else if (k === '+' || k === '=') view.dist = clamp(view.dist / 1.15, 90, 2200); else if (k === '-') view.dist = clamp(view.dist * 1.15, 90, 2200);
    else return;
    e.preventDefault(); requestRender();
  });
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  function showInfo(b) {
    const el = $('info');
    if (!b) { el.classList.remove('on'); el.textContent = ''; return; }
    el.textContent = '';
    const t = document.createElement('b'); t.textContent = b.name || `building (${b.kind})`;
    const l1 = document.createElement('div'); l1.textContent = `${b.h} m tall: ${b.h_note}`;
    const l2 = document.createElement('div'); l2.textContent = `OpenStreetMap ${b.osm.replace('/', ' ')}`;
    el.append(t, l1, l2); el.classList.add('on');
  }
  let statusTimer = null;
  function status(s) { $('status').textContent = s; clearTimeout(statusTimer); if (s) statusTimer = setTimeout(() => { $('status').textContent = ''; }, 6000); }

  // ---- controls and legend ---------------------------------------------------------------------------------------
  function legend() {
    const L = $('legend'); L.textContent = '';
    const line = (label, text) => { const d = document.createElement('div'); const b = document.createElement('b'); b.textContent = label + ' '; d.append(b, text); L.appendChild(d); return d; };
    line('Ground:', 'flat. No terrain data; everything stands at 0 m.');
    line('Heights:', `${counts.levels} estimated from level counts, ${counts.guess} guessed from kind, ${counts.tag} from a height tag.`);
    line('Data:', `${B.length} buildings from OpenStreetMap, ${META.osm_base.slice(0, 10)}. The dashed line is where the data ends.`);
    if (view.curve) line('Curve:', `tiny-earth view (radius ${CURVE_R} m). Only the drawing bends; every lat/lon stays as stored.`);
    if (view.mode === 'static') line('View:', 'flat plan, no 3D.');
    const m = document.createElement('div'); m.className = 'marks';
    [['from a height tag', 0], ['estimated from levels', 1], ['guessed', 2]].forEach(([t, i]) => {
      const s = document.createElement('span'); s.className = 'sw'; s.style.background = MARKHEX[i]; s.style.border = '1px solid #998f80';
      m.append(s, t + (i < 2 ? ' · ' : ''));
    });
    L.appendChild(m);
  }
  $('curve').addEventListener('change', e => { view.curve = e.target.checked; legend(); requestRender(); });
  $('mark').addEventListener('change', e => { view.mark = e.target.checked; document.body.classList.toggle('mark', view.mark); if (view.mode === 'static') paintPlan(); requestRender(); });
  $('reset').addEventListener('click', () => { Object.assign(view, home()); requestRender(); });
  $('flat2d').addEventListener('click', () => setMode(view.mode === '3d' ? 'static' : '3d'));
  function setMode(m) {
    if (m === '3d' && !gl) m = 'static';
    view.mode = stats.mode = m;
    document.body.classList.toggle('static', m === 'static');
    $('curve').disabled = m === 'static';
    $('flat2d').textContent = m === 'static' ? (gl ? '3D view' : 'Flat plan (3D unavailable)') : 'Flat plan (no 3D)';
    $('flat2d').disabled = !gl;
    if (m === 'static') paintPlan();
    legend(); requestRender();
  }

  // ---- start -----------------------------------------------------------------------------------------------------
  if (gl) { try { initGL(); } catch (e) { console.error(e); stats.glError = String(e); gl = null; } }
  resize();
  window.addEventListener('resize', () => { resize(); requestRender(); });
  setMode(gl && q.get('static') !== '1' ? '3d' : 'static');

  // ---- for the measuring script (read-only views, and the same paths a person or the parent uses) ---------------
  window.__map = {
    stats, view, outbox, refusals, meta: META, curveRadius: CURVE_R, gridCell: () => G.gridCell,
    footprints: B.length, heights: counts,
    drawn: () => JSON.parse(JSON.stringify(drawn)),
    receive,                                   // the same check a parent's message goes through
    project, pick, pickBuilding: (x, y) => { const b = pickBuilding(x, y); return b && {osm: b.osm, name: b.name, h: b.h, h_src: b.h_src}; },
    geo: Geo, frame: F,
    setCurve(on) { $('curve').checked = !!on; $('curve').dispatchEvent(new Event('change')); },
    setMode, requestRender,
    // a measured spin: n frames, each turning the view a little; -> the frame intervals and draw times
    bench(n = 240, sync = true) {
      return new Promise(done => {
        const keep = Object.assign({}, view), d0 = stats.drawMs.length, i0 = stats.intervals.length;
        stats.sync = sync; stats.lastDrawAt = null;
        let k = 0;
        const step = () => {
          if (k++ >= n) { stats.sync = false; Object.assign(view, keep); requestRender();
            return done({draw: stats.drawMs.slice(d0), intervals: stats.intervals.slice(i0)}); }
          view.yaw += 2 * Math.PI / n; view.dist = keep.dist * (1 - 0.3 * Math.sin(Math.PI * k / n));
          requestRender(); requestAnimationFrame(() => setTimeout(step, 0));
        };
        step();
      });
    },
  };
})();
