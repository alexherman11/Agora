// style.js — a parser and resolver for Wren's style notation.
// The point of this file is that the style is PARSED, not translated by hand.
// Whatever it cannot express is a finding, not a bug to paper over.

export const HEX = /^#[0-9a-fA-F]{3,8}$/;
export const BARE_NUM = /^-?\d+(\.\d+)?(px|pt|rem|%)?$/;

// ---------- refusals ----------
export class Refusal extends Error {
  constructor(line, msg, escapes) {
    super(msg);
    this.line = line; this.msg = msg; this.escapes = escapes || [];
  }
  toText() {
    return `refused (line ${this.line}): ${this.msg}\n` +
      this.escapes.map(e => `  -> ${e}`).join('\n');
  }
}

// ---------- colour ----------
function hexToRgb(h) {
  h = h.replace('#', '');
  if (h.length === 3) h = h.split('').map(c => c + c).join('');
  return [parseInt(h.slice(0,2),16), parseInt(h.slice(2,4),16), parseInt(h.slice(4,6),16)];
}
function rgbToHex(r) { return '#' + r.map(v => Math.round(Math.max(0,Math.min(255,v))).toString(16).padStart(2,'0')).join(''); }
function mix(a, b, t) { const A=hexToRgb(a), B=hexToRgb(b); return rgbToHex([0,1,2].map(i => A[i]*(1-t) + B[i]*t)); }

// ---------- the parser ----------
// token <name> = <value>
// role <name> : <property>, <property>, ...
// when <selection> : <property>, ...
// theme <name> of <style>   /   indented token lines under it
export function parseStyle(src) {
  const out = { tokens: {}, tokenSrc: {}, roles: {}, clauses: [], presents: {}, themes: {}, order: [] };
  const lines = src.split(/\r?\n/);
  let theme = null;

  const check = (n, text) => {
    // the first two refusals of the catalogue, made real
    const hex = text.match(/#[0-9a-fA-F]{3,8}\b/);
    if (hex) throw new Refusal(n, `colours are named here. "${hex[0]}" may only appear on a token line.`,
      [`token <name> = ${hex[0]}      (a new ground colour, named, for everyone)`,
       `then use the name: ... ${hex[0] === '#000' ? 'ink' : '<name>'} ...`]);
    const px = text.match(/\b(\d+(?:\.\d+)?)px\b/);
    if (px) throw new Refusal(n, `${px[0]} is not on the scale. lengths are gap, gap xN, gap /N, or an em.`,
      [`use gap x${Math.max(1, Math.round(parseFloat(px[1]) / 8))}  (= ${Math.max(1,Math.round(parseFloat(px[1])/8))*8}px at gap 8)`,
       `token gap = <n>            (moves everything)`]);
  };

  lines.forEach((raw, i) => {
    const n = i + 1;
    const indented = /^\s+\S/.test(raw);
    const s = raw.trim();
    if (!s || s.startsWith('#')) return;

    let m;
    if ((m = s.match(/^theme\s+(\S+)\s+of\s+(\S+)$/))) {
      theme = m[1]; out.themes[theme] = { of: m[2], tokens: {}, line: n }; return;
    }
    if ((m = s.match(/^token\s+([\w.]+)\s*=\s*(.+)$/))) {
      const [, name, val] = m;
      if (theme && indented) { out.themes[theme].tokens[name] = val.trim(); }
      else { theme = null; out.tokens[name] = val.trim(); out.tokenSrc[name] = n; out.order.push(name); }
      return;
    }
    // NOTE (found by building this): the clause colon cannot be "the colon", because the
    // desk's own selection language uses colons (kind:note, comments:open). The separator
    // is a SPACED colon, and we split on the LAST one. Unspaced colons belong to selections.
    // present <role> : <part>, <part> ...   — WHICH PARTS are drawn, and in what order.
    // Found missing while building: roles say how a part looks, and nothing said what parts exist.
    if (/^present\s/.test(s)) {
      const i3 = s.lastIndexOf(' : ');
      if (i3 < 0) throw new Refusal(n, `a present line needs " : " before its parts.`, [`present card : title, body :3, meta, tags`]);
      theme = null;
      out.presents[s.slice(0, i3).replace(/^present\s+/, '').trim()] = { parts: splitProps(s.slice(i3 + 3)), line: n };
      return;
    }
    // refusal 6: a theme may redefine tokens, never roles. Checked before the role branch.
    if (theme && indented && /^(role|when|present)\s/.test(s)) {
      const what = s.split(/\s+/)[1];
      throw new Refusal(n, `a theme may redefine tokens, not roles. "${what}" belongs to the chrome, and both sides must see one shape.`,
        [`role ${what} : ...                 (change it for everyone, as a deed they will see)`,
         `do style <this appearance> ...     (change only this one, as an override)`]);
    }
    if (/^role\s/.test(s) || /^when\s/.test(s)) {
      const i2 = s.lastIndexOf(' : ');
      if (i2 < 0) throw new Refusal(n, `a ${s.split(/\s+/)[0]} line needs " : " with spaces before its properties.`,
        [`${s.split(/\s+/)[0]} <name> : <property>, <property>`,
         `(an unspaced colon belongs to a selection, as in kind:note)`]);
      const head = s.slice(0, i2).trim(), body = s.slice(i2 + 3).trim();
      theme = null; check(n, body);
      if (head.startsWith('role')) out.roles[head.replace(/^role\s+/, '')] = { props: splitProps(body), line: n };
      else out.clauses.push({ sel: head.replace(/^when\s+/, ''), props: splitProps(body), line: n });
      return;
    }
    if (theme && indented && s.startsWith('role')) {
      throw new Refusal(n, `a theme may redefine tokens, not roles. "${s.split(/\s+/)[1]}" belongs to the chrome.`,
        [`role ${s.split(/\s+/)[1]} : ...          (change it for everyone)`,
         `do style <this appearance> ...   (change only this one, as an override)`]);
    }
    throw new Refusal(n, `not a token, role, clause or theme line: "${s}"`,
      [`token <name> = <value>`, `role <name> : <props>`, `when <selection> : <props>`]);
  });
  return out;
}

function splitProps(s) { return s.split(',').map(x => x.trim()).filter(Boolean); }

// ---------- token resolution ----------
export function resolveTokens(st, themeName) {
  const raw = Object.assign({}, st.tokens);
  if (themeName && st.themes[themeName]) Object.assign(raw, st.themes[themeName].tokens);
  const done = {};
  const get = (name, seen = new Set()) => {
    if (name in done) return done[name];
    if (!(name in raw)) return null;
    if (seen.has(name)) return null;
    seen.add(name);
    const v = raw[name].trim();
    let m;
    if (HEX.test(v)) return done[name] = { type: 'colour', value: v };
    if ((m = v.match(/^([\w.]+)\s+at\s+([\d.]+)%?$/))) {
      const base = get(m[1], seen); const paper = get('paper', new Set(['__']));
      if (base && base.type === 'colour' && paper)
        return done[name] = { type: 'colour', value: mix(paper.value, base.value, parseFloat(m[2]) / 100) };
    }
    if (/^\d+(\.\d+)?$/.test(v)) return done[name] = { type: 'length', value: parseFloat(v) };
    if ((m = v.match(/^([\w-]+)\s+([\d.]+)\/([\d.]+)$/)))
      return done[name] = { type: 'text', family: m[1], size: parseFloat(m[2]), leading: parseFloat(m[3]) };
    return done[name] = { type: 'word', value: v };
  };
  const t = {};
  Object.keys(raw).forEach(k => t[k] = get(k));
  return t;
}

// ---------- selections (the desk's own language) ----------
export function matches(sel, thing, world) {
  return sel.split(',').map(x => x.trim()).filter(Boolean).every(term => {
    let neg = false;
    if (term.startsWith('-')) { neg = true; term = term.slice(1); }
    return one(term, thing, world) !== neg;
  });
}
function one(term, t, world) {
  let m;
  if ((m = term.match(/^kind:(.+)$/))) return m[1].split('|').includes(t.kind);
  if ((m = term.match(/^tag:(.+)$/))) return (t.tags || []).includes(m[1]);
  if ((m = term.match(/^in:(.+)$/))) { let p = t.parent; while (p) { if (p === m[1]) return true; p = (world.nodes[p] || {}).parent; } return false; }
  if ((m = term.match(/^title:(.+)$/))) return (t.title || '').toLowerCase().includes(m[1].toLowerCase());
  if (term === 'comments:open') return (t.comments || []).some(c => !c.resolved);
  if (term === 'comments:any') return (t.comments || []).length > 0;
  if (term === 'folded') return !!t.folded;
  if ((m = term.match(/^type:(.+)$/))) return t.type === m[1];
  if ((m = term.match(/^\?(.+)$/))) return ((t.title || '') + ' ' + (t.text || '')).toLowerCase().includes(m[1].toLowerCase());
  return false;
}

// ---------- property -> css, with provenance ----------
// Returns { css: {...}, trace: [{prop, value, from, line, beat:[...]}], parts:{} }
export function resolveLook(thing, st, tokens, world) {
  const applied = [];               // ordered: role first, then clauses in file order
  const parts = {};
  let roleName = thing.as || null;

  // A clause may assign a role only where none is set. An explicit as= on the appearance is
  // a deed about this one thing; a clause is a rule about a kind of thing. The specific wins.
  const hits = st.clauses.filter(c => matches(c.sel, thing, world));
  if (!roleName) hits.forEach(c => c.props.forEach(p => { const m = p.match(/^as\s*=\s*([\w.]+)$/); if (m) roleName = m[1]; }));

  if (roleName && st.roles[roleName]) applied.push({ from: `role ${roleName}`, line: st.roles[roleName].line, props: st.roles[roleName].props });
  hits.forEach(c => applied.push({ from: `when ${c.sel}`, line: c.line, props: c.props.filter(p => !/^as\s*=/.test(p)) }));
  if (thing.override) applied.push({ from: `override by ${thing.override.by}`, line: null, props: thing.override.props, isOverride: true });

  const css = {}; const trace = []; const owner = {};
  for (const layer of applied) {
    for (const p of layer.props) {
      const r = prop(p, tokens);
      if (!r) { trace.push({ prop: p, value: '(unreadable)', from: layer.from, line: layer.line, unreadable: true }); continue; }
      if (r.part) { parts[r.part] = r.show; trace.push({ prop: p, value: `${r.show ? 'show' : 'hide'} ${r.part}`, from: layer.from, line: layer.line }); continue; }
      for (const [k, v] of Object.entries(r.css)) {
        const prev = owner[k];
        owner[k] = { value: v, from: layer.from, line: layer.line, prop: p, beat: prev ? [...(prev.beat || []), { from: prev.from, line: prev.line, prop: prev.prop, value: prev.value }] : [] };
        css[k] = v;
      }
    }
  }
  Object.entries(owner).forEach(([k, o]) => trace.push({ prop: o.prop, css: k, value: o.value, from: o.from, line: o.line, beat: o.beat }));
  return { role: roleName, css, trace, parts, applied };
}

function len(expr, tokens) {
  let m;
  if ((m = expr.match(/^([\w.]+)\s*x\s*([\d.]+)$/))) { const b = tokens[m[1]]; if (b && b.type === 'length') return b.value * parseFloat(m[2]); }
  if ((m = expr.match(/^([\w.]+)\s*\/\s*([\d.]+)$/))) { const b = tokens[m[1]]; if (b && b.type === 'length') return b.value / parseFloat(m[2]); }
  if ((m = expr.match(/^([\w.]+)$/))) { const b = tokens[m[1]]; if (b && b.type === 'length') return b.value; }
  if ((m = expr.match(/^([\d.]+)em$/))) return { em: parseFloat(m[1]) };
  return null;
}
function colour(expr, tokens) {
  let m;
  if ((m = expr.match(/^([\w.]+)\s+at\s+([\d.]+)%?$/))) {
    const b = tokens[m[1]], paper = tokens['paper'];
    if (b && b.type === 'colour' && paper) return mix(paper.value, b.value, parseFloat(m[2]) / 100);
  }
  const t = tokens[expr];
  return t && t.type === 'colour' ? t.value : null;
}

function prop(p, tokens) {
  let m;
  if ((m = p.match(/^show\s+(\w+)$/))) return { part: m[1], show: true };
  if ((m = p.match(/^hide\s+(\w+)$/))) return { part: m[1], show: false };
  if ((m = p.match(/^on\s+(.+)$/))) { const c = colour(m[1], tokens); return c ? { css: { background: c } } : null; }
  if ((m = p.match(/^([\w.]+)\s*->\s*(.+)$/))) { const c = colour(m[2], tokens); return c ? { css: { color: c } } : null; }
  if ((m = p.match(/^edge\s+(.+)$/))) { const c = colour(m[1], tokens); return c ? { css: { border: `1px solid ${c}` } } : null; }
  if ((m = p.match(/^border\s+(top|right|bottom|left)\s+(.+)$/))) {
    const c = colour(m[2], tokens); const k = 'border' + m[1][0].toUpperCase() + m[1].slice(1);
    return c ? { css: { [k]: `1px solid ${c}` } } : null;
  }
  if ((m = p.match(/^corner\s+(.+)$/))) { const l = len(m[1], tokens); return typeof l === 'number' ? { css: { borderRadius: l + 'px' } } : null; }
  if ((m = p.match(/^pad\s+(.+)$/))) { const l = len(m[1], tokens); return typeof l === 'number' ? { css: { padding: l + 'px' } } : null; }
  if ((m = p.match(/^space\s+(above|below)\s+(.+)$/))) {
    const l = len(m[2], tokens); const k = m[1] === 'above' ? 'marginTop' : 'marginBottom';
    return typeof l === 'number' ? { css: { [k]: l + 'px' } } : null;
  }
  if ((m = p.match(/^width\s+(.+)$/))) { const l = len(m[1], tokens); if (l && l.em) return { css: { maxWidth: l.em + 'em' } }; return typeof l === 'number' ? { css: { width: l + 'px' } } : null; }
  if (/^text\b/.test(p)) {
    const t = tokens[p.startsWith('text.') ? p.split(/\s+/)[0] : 'text'];
    if (!t || t.type !== 'text') return null;
    // Refusal 10, added after Iris measured seven font sizes on one screen, four of them
    // differing by half a pixel: "a scale in name only". Type is a ramp with steps, like gap.
    let mr;
    if ((mr = p.match(/\bat\s+([\d.]+)\b/))) throw new Refusal(0,
      `"text at ${mr[1]}" is not a step. the type ramp has steps, like the spacing scale.`,
      ['text down            (one step smaller)', 'text down 2          (two steps)',
       'text up', 'token ramp = <n>     (the ratio between steps)']);
    const css = { fontFamily: t.family === 'ui' ? 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif' : (t.family === 'mono' ? 'ui-monospace, SFMono-Regular, Menlo, monospace' : 'Georgia, serif'), lineHeight: t.leading };
    let size = t.size;
    const ratio = (tokens.ramp && tokens.ramp.type === 'length') ? tokens.ramp.value : 1.2;
    let mm;
    if ((mm = p.match(/\bdown(?:\s+(\d+))?\b/))) size = t.size / Math.pow(ratio, parseInt(mm[1] || '1', 10));
    if ((mm = p.match(/\bup(?:\s+(\d+))?\b/))) size = t.size * Math.pow(ratio, parseInt(mm[1] || '1', 10));
    css.fontSize = Math.round(size) + 'px';
    if (/\bstrong\b/.test(p)) css.fontWeight = 620;
    if (/\bslant\b/.test(p)) css.fontStyle = 'italic';
    if (/\btracked\b/.test(p)) css.letterSpacing = '0.05em';
    return { css };
  }
  const c = colour(p, tokens);
  if (c) return { css: { color: c } };
  return null;
}

export const _internals = { mix, colour, len };
