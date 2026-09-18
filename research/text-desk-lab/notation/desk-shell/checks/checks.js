// checks/checks.js — Iris's fixed script of measured checks. Owner: Iris.
//
// This file is the eyes' instrument. It is deliberately boring and deliberately the same
// every pass, so that a difference between two passes is a difference in the desktop and
// not a difference in how I happened to look that time.
//
// Run it from the page:
//     const m = await import('/checks/checks.js'); m.run()
// or, for the markdown row block that goes into checks/results.md:
//     const m = await import('/checks/checks.js'); m.md()
//
// Every result carries document.title, the href and the wall-clock time, because pages
// change under me: last round a prototype was edited between my measuring it and my
// publishing it, and every number in the draft went false.
//
// Marks, as the studio uses them:
//   =  measured   — this script read a value back. Reproducible by anyone with the page.
//   ~  described  — a viewer's judgement. This script NEVER emits one; I write those by hand.
//   ?  opaque     — could not be determined, with its extent stated.
//   !  stale      — true of a version that is no longer on disk.
// A check that cannot run returns "?" with a reason. It never returns "pass" by default.

const PX = 8;                 // the grid the shell claims
const AA = 4.5;               // WCAG AA for body text
const AA_LARGE = 3.0;         // AA for >=24px or >=19px bold

// ---------------------------------------------------------------- colour

const cv = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
function hex(c) {
  try { cv.fillStyle = c; return cv.fillStyle; } catch (e) { return null; }
}
function rgbOf(c) {
  const h = hex(c);
  if (!h || h[0] !== '#') {                       // color(srgb ...) and friends
    const m = String(c).match(/[\d.]+/g);
    if (!m) return null;
    const v = m.slice(0, 3).map(Number);
    return v.every(x => x <= 1) ? v.map(x => Math.round(x * 255)) : v.map(Math.round);
  }
  return [1, 3, 5].map(i => parseInt(h.substr(i, 2), 16));
}
function lum(c) {
  const v = rgbOf(c);
  if (!v) return null;
  const f = x => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); };
  return 0.2126 * f(v[0]) + 0.7152 * f(v[1]) + 0.0722 * f(v[2]);
}
function contrast(fg, bg) {
  const a = lum(fg), b = lum(bg);
  if (a == null || b == null) return null;
  return +(((Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05))).toFixed(2);
}
function alpha(c) {
  const m = String(c).match(/rgba?\([^)]*?([\d.]+)\s*\)/);
  return m ? parseFloat(m[1]) : (String(c) === 'transparent' ? 0 : 1);
}
// The painted background behind an element: walk up until something is not transparent.
function bgBehind(el) {
  let n = el;
  while (n && n !== document.documentElement) {
    const c = getComputedStyle(n).backgroundColor;
    if (alpha(c) > 0.05) return hex(c);
    n = n.parentElement;
  }
  return hex(getComputedStyle(document.body).backgroundColor) || '#ffffff';
}

// ---------------------------------------------------------------- the page

// A <style> or <script> tag is a childless node full of text, and every naive
// "what is on screen" query picks it up. On 2026-09-18 my word-diff reported an app's
// whole inline stylesheet as text the screen shows and its text() does not.
const INVISIBLE = /^(STYLE|SCRIPT|TEMPLATE|NOSCRIPT|TITLE|META|LINK|HEAD)$/;

function leaves() {
  return [...document.querySelectorAll('body *')].filter(el => {
    if (INVISIBLE.test(el.tagName)) return false;
    if (el.children.length) return false;
    const t = (el.textContent || '').trim();
    if (!t) return false;
    const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  });
}
function big(s) {                                  // WCAG "large text"
  const px = parseFloat(s.fontSize), w = parseInt(s.fontWeight) || 400;
  return px >= 24 || (px >= 18.66 && w >= 700);
}
const onGrid = v => Math.abs(v - Math.round(v / PX) * PX) < 0.75;
const round = v => Math.round(v * 100) / 100;

// ---------------------------------------------------------------- error capture
// Installed once; later passes report what was caught since the last one.

if (!window.__irisErrors) {
  window.__irisErrors = [];
  window.__irisSince = performance.now();
  addEventListener('error', e => window.__irisErrors.push(
    'error: ' + (e.message || e.type) + ' @ ' + (e.filename || '?') + ':' + (e.lineno || '?')));
  addEventListener('unhandledrejection', e => window.__irisErrors.push(
    'unhandled rejection: ' + String(e.reason && e.reason.message || e.reason)));
  const ce = console.error;
  console.error = function (...a) { window.__irisErrors.push('console.error: ' + a.map(String).join(' ').slice(0, 160)); return ce.apply(this, a); };
}

// ================================================================ the checks
// Each returns { id, mark, ok, value, detail }. mark is '=' or '?'. ok may be null
// when the check is informational rather than pass/fail.

const CHECKS = [];
const check = (id, fn) => CHECKS.push({ id, fn });

// A check that passes because there is nothing to check is a lie, and it is the exact
// lie I keep finding in other people's screens. On 2026-09-18 this script reported
// "4 pass" against a page that had not finished booting: 0 font sizes, no text, no dock.
// So: nothing content-shaped may return a verdict until the shell is actually up.
// Readiness is itself a measured check, and it fails loudly rather than waiting.
const MIN_LEAVES = 6;
function notReady() {
  const n = leaves().length;
  if (n >= MIN_LEAVES && document.querySelector('[class*=dock]')) return null;
  return {
    mark: '?', ok: null,
    value: 'page not ready (' + n + ' text leaves, dock ' + (document.querySelector('[class*=dock]') ? 'present' : 'absent') + ')',
    detail: 'extent: everything. Re-run when the shell has booted; this is not a pass.'
  };
}

// The shell, and each open window, as separately addressable zones. A number about the
// whole desktop is an accusation; the same number per zone is an address.
function zones() {
  const z = {};
  ['bar', 'dock', 'said', 'stage'].forEach(id => { const e = document.getElementById(id); if (e) z[id] = e; });
  [...document.querySelectorAll('.r-window,[class*=window]')]
    .filter(w => w.getBoundingClientRect().width > 120)
    .forEach(w => {
      const n = ((w.querySelector('[class*=windowname],[class*=title],[class*=name]') || {}).textContent || 'window')
        .trim().split('\n')[0].slice(0, 12) || 'window';
      z[n] = w;
    });
  return z;
}

// 1 — how many distinct type sizes, are any fractional, and WHOSE they are.
// On 2026-09-18 the desktop measured 12 sizes with 4 half-pixels. Split by zone it
// turned out the shell had 3 and each app had invented its own ramp: not one bad scale
// but four scales, which is a different problem with a different owner.
check('type-scale', () => {
  const h = {};
  leaves().forEach(el => { const s = getComputedStyle(el).fontSize; h[s] = (h[s] || 0) + 1; });
  const sizes = Object.keys(h).map(parseFloat).sort((a, b) => a - b);
  const frac = sizes.filter(v => Math.abs(v - Math.round(v)) > 0.01);
  const per = Object.entries(zones()).map(([k, v]) => {
    const s = new Set();
    [...v.querySelectorAll('*')].forEach(e => {
      if (e.children.length || INVISIBLE.test(e.tagName) || !(e.textContent || '').trim()) return;
      s.add(parseFloat(getComputedStyle(e).fontSize));
    });
    return s.size ? `${k} ${s.size}(${[...s].sort((a, b) => a - b).join('/')})` : null;
  }).filter(Boolean);
  return {
    mark: '=', ok: sizes.length <= 5 && frac.length === 0,
    value: sizes.length + ' sizes: ' + sizes.join('/'),
    detail: (frac.length ? 'fractional: ' + frac.join(', ') + '. ' : '') +
      (sizes.length > 5 ? 'more than 5 steps. ' : '') + 'by zone — ' + per.join('; ')
  };
});

// 2 — the worst text contrast on screen, and how many fail AA.
check('contrast-min', () => {
  let worst = { r: 99 }, fails = [];
  leaves().forEach(el => {
    const s = getComputedStyle(el);
    const bg = bgBehind(el);
    const r = contrast(s.color, bg);
    if (r == null) return;
    const need = big(s) ? AA_LARGE : AA;
    const row = { r, need, px: parseFloat(s.fontSize), fg: hex(s.color), bg, t: el.textContent.trim().slice(0, 28) };
    if (r < worst.r) worst = row;
    if (r < need) fails.push(row);
  });
  return {
    mark: '=', ok: fails.length === 0,
    value: 'min ' + (worst.r === 99 ? '?' : worst.r) + ':1, ' + fails.length + ' below AA',
    detail: fails.slice(0, 4).map(f => `${f.r}:1 ${f.px}px ${f.fg} on ${f.bg} "${f.t}"`).join(' | ')
  };
});

// 3 — an honesty mark must be at least as loud as what it qualifies.
// Loudness = contrast x size. A mark (= ~ ? !) is compared with the loudest
// text in its own line box, which is what it is qualifying.
check('honesty-loudness', () => {
  const MARKS = /^\s*[=~?!]\s*\S|[·\s][=~?!]\s*\S/;
  const quiet = [];
  let n = 0;
  const loud = el => {
    const s = getComputedStyle(el);
    const r = contrast(s.color, bgBehind(el));
    return r == null ? null : r * parseFloat(s.fontSize);
  };
  leaves().forEach(el => {
    const t = (el.textContent || '').trim();
    if (!MARKS.test(t)) return;
    n++;
    const mine = loud(el);
    if (mine == null) return;
    const row = el.closest('[class*=line],[class*=row],li,p,div');
    if (!row) return;
    let best = null, bestEl = null;
    [...row.querySelectorAll('*')].forEach(o => {
      if (o.children.length || !(o.textContent || '').trim()) return;
      if (o === el || MARKS.test(o.textContent.trim())) return;
      const l = loud(o);
      if (l != null && (best == null || l > best)) { best = l; bestEl = o; }
    });
    if (best != null && mine < best * 0.9) quiet.push({
      mark: t.slice(0, 34), mine: Math.round(mine), qualifies: bestEl.textContent.trim().slice(0, 24), theirs: Math.round(best)
    });
  });
  if (!n) return { mark: '?', ok: null, value: 'no honesty marks found on this screen', detail: 'extent: the whole screen' };
  return {
    mark: '=', ok: quiet.length === 0,
    value: n + ' marks, ' + quiet.length + ' quieter than what they qualify',
    detail: quiet.slice(0, 4).map(q => `"${q.mark}" ${q.mine} vs "${q.qualifies}" ${q.theirs}`).join(' | ')
  };
});

// 4 — dock and windows on the 8px grid.
check('grid-8', () => {
  const targets = [...document.querySelectorAll('[class*=dock],[class*=window],[class*=win],[class*=bar],[class*=stage]')]
    .filter(el => { const r = el.getBoundingClientRect(); return r.width > 24 && r.height > 12; });
  if (!targets.length) return { mark: '?', ok: null, value: 'no dock/window/bar elements matched', detail: 'extent: the whole shell' };
  const off = [];
  targets.forEach(el => {
    const r = el.getBoundingClientRect();
    const bad = ['x', 'y', 'width', 'height'].filter(k => !onGrid(r[k]));
    if (bad.length) off.push(String(el.className).slice(0, 22) + ' ' +
      bad.map(k => k + '=' + round(r[k])).join(' '));
  });
  return {
    mark: '=', ok: off.length === 0,
    value: (targets.length - off.length) + '/' + targets.length + ' on the 8px grid',
    detail: off.slice(0, 5).join(' | ')
  };
});

// 5 — nothing clipped without saying so.
// An element whose content overflows, or whose text is line-clamped/ellipsised,
// must have a nearby element that admits it.
check('clipped-unsaid', () => {
  const ADMITS = /offscreen|past the bottom|more\b|\+\d|cut|truncat|hidden|not shown|show all|scroll|veiled|inside \(count/i;
  const bad = [];
  [...document.querySelectorAll('body *')].forEach(el => {
    const s = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) return;
    const overflows = (el.scrollWidth > el.clientWidth + 2 || el.scrollHeight > el.clientHeight + 2)
      && /hidden|clip|auto|scroll/.test(s.overflowX + s.overflowY);
    const clamped = s.webkitLineClamp && s.webkitLineClamp !== 'none';
    const ellipsis = s.textOverflow === 'ellipsis' && el.scrollWidth > el.clientWidth + 2;
    if (!overflows && !clamped && !ellipsis) return;
    const scope = el.closest('[class*=win],[class*=col],[class*=card],section,article') || el.parentElement || el;
    if (ADMITS.test(scope.textContent || '')) return;
    bad.push(String(el.className || el.tagName).slice(0, 20) +
      ` ${el.scrollWidth}x${el.scrollHeight} in ${el.clientWidth}x${el.clientHeight}` +
      (clamped ? ' clamped' : '') + (ellipsis ? ' ellipsis' : ''));
  });
  return {
    mark: '=', ok: bad.length === 0,
    value: bad.length + ' clipped without saying so',
    detail: bad.slice(0, 5).join(' | ')
  };
});

// 6 — what the eye lands on, as a computed proxy.
// area x contrast x weight x chroma. This is a PROXY and is reported as such:
// it is '=' about the ranking it computes, never about what a person sees.
check('first-landing', () => {
  const rank = [];
  leaves().forEach(el => {
    const s = getComputedStyle(el), r = el.getBoundingClientRect();
    if (r.bottom < 0 || r.top > innerHeight || r.right < 0 || r.left > innerWidth) return;
    const c = contrast(s.color, bgBehind(el));
    if (c == null) return;
    const v = rgbOf(s.color) || [0, 0, 0];
    const chroma = (Math.max(...v) - Math.min(...v)) / 255;
    const w = (parseInt(s.fontWeight) || 400) / 400;
    const score = Math.sqrt(r.width * r.height) * c * w * (1 + chroma * 1.5);
    rank.push({ score: Math.round(score), t: el.textContent.trim().slice(0, 30), px: parseFloat(s.fontSize) });
  });
  rank.sort((a, b) => b.score - a.score);
  return {
    mark: '=', ok: null,
    value: rank.slice(0, 3).map(r => `"${r.t}" (${r.score})`).join(' > '),
    detail: 'proxy: sqrt(area) x contrast x weight x chroma. A ranking, not a report of seeing.'
  };
});

// 7 — script errors since the previous pass.
// The hook is installed when this module is first imported, which is always AFTER the
// page has loaded. Errors thrown during boot happened before it existed and are invisible
// to it. On 2026-09-18 this check reported "0 errors" while two ReferenceErrors from
// Desk.start() sat in the console. So the check now states its own blind spot, and a
// clean run is reported as clean SINCE IMPORT, never as clean.
check('console-errors', () => {
  const out = (window.__irisErrors || []).slice();
  window.__irisErrors = [];
  const booted = performance.now() - (window.__irisSince || 0);
  return {
    mark: '=', ok: out.length === 0 ? null : false,
    value: out.length + ' since this script was imported (' + Math.round(booted / 1000) + 's of coverage)',
    detail: out.length ? out.slice(0, 4).join(' | ')
      : 'blind spot: errors thrown during boot, before the import, are not visible here. Read the console separately.'
  };
});

// 8 — does each window's "as text" say what the screen shows?
// Compares the distinctive words visible in the window body with the words in its
// text panel. Reports what the screen has that the text does not.
check('as-text-agreement', () => {
  const wins = [...document.querySelectorAll('[class*=win]')]
    .filter(w => w.getBoundingClientRect().width > 120 && !w.closest('[class*=dock]'));
  if (!wins.length) return { mark: '?', ok: null, value: 'no windows open', detail: 'extent: cannot judge until a window is open' };
  const words = s => new Set((s || '').toLowerCase().match(/[a-z][a-z0-9_-]{3,}/g) || []);
  const rows = [];
  wins.forEach(w => {
    let panel = w.querySelector('pre.text, [class*=astext-panel], textarea.text');
    const title = (w.querySelector('[class*=title],h1,h2,h3') || {}).textContent || String(w.className);
    // A panel that is empty or hidden is a panel that has not been switched on. That is
    // not a disagreement, it is an unknown, and it must not be scored as one.
    if (panel && (!(panel.textContent || '').trim() || getComputedStyle(panel).display === 'none')) panel = null;
    if (!panel) { rows.push({ win: title.trim().slice(0, 18), missing: null }); return; }
    const onScreen = words([...w.querySelectorAll('*')]
      .filter(e => !panel.contains(e) && !e.children.length && !INVISIBLE.test(e.tagName)
        && !/astext|close|titlebar/.test(String(e.className) + String((e.parentElement || {}).className)))
      .map(e => e.textContent).join(' '));
    const inText = words(panel.textContent);
    const missing = [...onScreen].filter(x => !inText.has(x));
    rows.push({ win: title.trim().slice(0, 18), missing: missing.slice(0, 6), n: missing.length, seen: onScreen.size });
  });
  const noPanel = rows.filter(r => r.missing === null);
  const disagree = rows.filter(r => r.missing && r.n > 0);
  if (noPanel.length) return {
    mark: '?', ok: null,
    value: noPanel.length + ' of ' + rows.length + ' windows have no text panel open',
    detail: 'toggle "as text" on each window, then re-run; extent: ' + noPanel.map(r => r.win).join(', ')
  };
  return {
    mark: '=', ok: disagree.length === 0,
    value: disagree.length + ' of ' + rows.length + ' windows show words their text does not say',
    detail: disagree.slice(0, 3).map(r => `${r.win}: ${r.n}/${r.seen} e.g. ${r.missing.join(', ')}`).join(' | ')
  };
});

// 9 — nothing overlaps the dock, and every dock item is a real target.
check('dock-clearance', () => {
  const dock = document.querySelector('[class*=dock]');
  if (!dock) return { mark: '?', ok: null, value: 'no dock element found', detail: 'extent: the whole shell' };
  const d = dock.getBoundingClientRect();
  const over = [...document.querySelectorAll('[class*=win]')].filter(w => {
    if (dock.contains(w)) return false;
    const r = w.getBoundingClientRect();
    return r.width > 40 && r.bottom > d.top + 1 && r.right > d.left && r.left < d.right;
  }).map(w => String(w.className).slice(0, 18));
  const small = [...dock.querySelectorAll('button,[role=button],a')]
    .map(b => ({ n: (b.textContent || '').trim().slice(0, 10), r: b.getBoundingClientRect() }))
    .filter(x => x.r.width < 24 || x.r.height < 24)
    .map(x => `${x.n} ${Math.round(x.r.width)}x${Math.round(x.r.height)}`);
  return {
    mark: '=', ok: over.length === 0 && small.length === 0,
    value: over.length + ' windows over the dock, ' + small.length + ' targets under 24px',
    detail: over.concat(small).slice(0, 5).join(' | ')
  };
});

// 10 — every interactive thing has a name a text inhabitant could use.
check('named-controls', () => {
  const els = [...document.querySelectorAll('button,[role=button],a[href],input,select,textarea')];
  if (!els.length) return { mark: '?', ok: null, value: 'no controls found', detail: '' };
  const unnamed = els.filter(e => {
    const n = (e.getAttribute('aria-label') || e.getAttribute('title') || e.textContent || e.value || '').trim();
    return n.length === 0;
  }).map(e => e.tagName + '.' + String(e.className).slice(0, 14));
  return {
    mark: '=', ok: unnamed.length === 0,
    value: (els.length - unnamed.length) + '/' + els.length + ' controls carry a name',
    detail: unnamed.slice(0, 5).join(' | ')
  };
});

// ================================================================ runner

export function run() {
  const stamp = {
    title: document.title,
    href: location.href,
    at: new Date().toTimeString().slice(0, 8),
    viewport: innerWidth + 'x' + innerHeight,
    scheme: matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light',
    nodes: document.querySelectorAll('*').length
  };
  const unready = notReady();
  const rows = CHECKS.map(c => {
    let r;
    if (unready && c.id !== 'console-errors') r = unready;
    else { try { r = c.fn(); } catch (e) { r = { mark: '?', ok: null, value: 'check threw', detail: String(e.message).slice(0, 90) }; } }
    return { id: c.id, mark: r.mark, ok: r.ok, value: r.value, detail: r.detail || '' };
  });
  const pass = rows.filter(r => r.ok === true).length;
  const fail = rows.filter(r => r.ok === false).length;
  const open = rows.filter(r => r.ok === null).length;
  return { stamp, score: `${pass} pass / ${fail} fail / ${open} open`, rows };
}

// Switch every window's "as text" panel on, so the as-text check has something to read,
// then run. Without this the check honestly returns '?' rather than a false disagreement.
export async function withText() {
  document.querySelectorAll('[class*=astext]').forEach(b => {
    const w = b.closest('[class*=win]');
    const p = w && w.querySelector('pre.text, [class*=astext-panel]');
    if (p && !(p.textContent || '').trim()) b.click();
  });
  // setTimeout, not requestAnimationFrame: a hidden pane never paints, and a check that
  // hangs when nobody is looking is worse than a check that runs one frame early.
  await new Promise(r => setTimeout(r, 120));
  return run();
}

// A markdown block ready to paste under a heading in checks/results.md.
export function md(pass) {
  const r = run();
  const line = x => `| \`${x.id}\` | ${x.ok === true ? 'PASS' : x.ok === false ? 'FAIL' : '?'} | ${x.mark} ${x.value} | ${x.detail.replace(/\|/g, '/')} |`;
  return [
    `### Pass ${pass || '?'} — ${r.stamp.at} — ${r.stamp.title} — ${r.stamp.viewport} ${r.stamp.scheme} — ${r.stamp.nodes} nodes`,
    ``,
    `${r.score}. \`${r.stamp.href}\``,
    ``,
    `| check | | result | detail |`,
    `|---|---|---|---|`,
    ...r.rows.map(line),
    ``
  ].join('\n');
}

export default { run, md };
