// style/style.js : the studio's style language, made real. OWNER: Wren.
//
// One style for the whole desktop. Apps do not invent colours; they name roles and tokens.
//   Style.parse(src)        -> {tokens, roles, clauses, presents, themes} or throws a Refusal
//   Style.install(src, theme) -> injects :root custom properties and one .r-<role> class per role
//   Style.token(name)       -> the resolved value ("#3F5D73", 8, {family,size,leading})
//   Style.varName(name)     -> "--t-accent", for apps that want it in their own CSS
//   Style.roleClass(name)   -> "r-card", the class an app puts on an element
//   Style.look(thing)       -> {role, css, trace, parts} : the resolved look plus WHY, for `why :look`
//
// What the notation deliberately cannot say (each refusal prints two runnable escapes):
//   a colour or a length outside a token line · a type size off the ramp
//   a theme that redefines a role · a clause without its spaced colon
// Round-three findings are all in here: the clause separator is " : " because the desk's own
// selections use colons; a bare colour is the FOREGROUND and `on <colour>` is the background;
// `present` says which parts are drawn, because roles only ever said how they look.

const Style = (() => {
  const HEX = /^#[0-9a-fA-F]{3,8}$/;

  class Refusal extends Error {
    constructor(line, msg, escapes) { super(msg); this.line = line; this.msg = msg; this.escapes = escapes || []; }
    toText() { return `refused${this.line ? ` (line ${this.line})` : ""}: ${this.msg}\n` + this.escapes.map(e => `  -> ${e}`).join("\n"); }
  }

  const hexToRgb = h => { h = h.replace("#", ""); if (h.length === 3) h = h.split("").map(c => c + c).join(""); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)); };
  const rgbToHex = r => "#" + r.map(v => Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, "0")).join("");
  const mix = (a, b, t) => { const A = hexToRgb(a), B = hexToRgb(b); return rgbToHex([0, 1, 2].map(i => A[i] * (1 - t) + B[i] * t)); };

  function parse(src) {
    const out = { tokens: {}, tokenLine: {}, roles: {}, clauses: [], presents: {}, themes: {}, fonts: {} };
    let theme = null;
    src.split(/\r?\n/).forEach((raw, i) => {
      const n = i + 1, indented = /^\s+\S/.test(raw);
      // A comment is "#" at the start of a line, or " # " with a space on each side. That second rule
      // exists because "#" also begins every colour, and a trailing comment on a token line was
      // silently swallowed into its value — the whole desktop drew with no background and said nothing.
      const s = raw.trim().replace(/\s+#\s.*$/, "").trim();
      if (!s || s.startsWith("#") && !/^#[0-9a-fA-F]{3,8}\b/.test(s)) return;
      if (!s) return;
      let m;
      if ((m = s.match(/^theme\s+(\S+)\s+of\s+(\S+)$/))) { theme = m[1]; out.themes[theme] = { of: m[2], tokens: {}, line: n }; return; }
      // F8 (research/command-center): a style names its typefaces. `font pixel = Silkscreen, monospace` lets a text
      // token say `pixel 16/1.4`; the first name is loaded from Google Fonts, the rest is the fallback stack.
      if ((m = s.match(/^font\s+([\w-]+)\s*=\s*(.+)$/))) { theme = null; const [face, ...rest] = m[2].split(",").map(x => x.trim()).filter(Boolean); out.fonts[m[1]] = { face, fallback: rest.join(", ") || "sans-serif", line: n }; return; }
      if ((m = s.match(/^token\s+([\w.]+)\s*=\s*(.+)$/))) {
        if (theme && indented) out.themes[theme].tokens[m[1]] = m[2].trim();
        else { theme = null; out.tokens[m[1]] = m[2].trim(); out.tokenLine[m[1]] = n; }
        return;
      }
      // a theme may redefine tokens, never roles. Checked before the role branch.
      if (theme && indented && /^(role|when|present)\s/.test(s)) {
        const what = s.split(/\s+/)[1];
        throw new Refusal(n, `a theme may redefine tokens, not roles. "${what}" belongs to the chrome, and both inhabitants must see one shape.`,
          [`role ${what} : ...                 (change it for everyone, as a deed they will see)`,
           `do style <this appearance> ...     (change only this one, as an override)`]);
      }
      // `present` was REMOVED in round six. A removed word is refused, not ignored: a word silently
      // accepted that does nothing is worse than one that never existed. wren-12 section 5.
      if (/^present\s/.test(s)) throw new Refusal(n, "`present` was removed. A lens says which parts are drawn, and where each part's words come from.",
        ["in the lens:   card : column, role card",
         "                 title : text $title, role title",
         "                 body  : text $text, clamp 3, role body",
         "see design-studio/wren-12-lens-grammar.md section 5"]);
      if (/^(role|when)\s/.test(s)) {
        const at = s.lastIndexOf(" : ");
        const kw = s.split(/\s+/)[0];
        if (at < 0) throw new Refusal(n, `a ${kw} line needs " : " with spaces before its properties.`,
          [`${kw} <name> : <property>, <property>`, `(an unspaced colon belongs to a selection, as in kind:note)`]);
        const head = s.slice(0, at).replace(/^\w+\s+/, "").trim(), body = s.slice(at + 3).trim();
        theme = null;
        check(n, body);
        const props = body.split(",").map(x => x.trim()).filter(Boolean);
        if (kw === "role") out.roles[head] = { props, line: n };
        else out.clauses.push({ sel: head, props, line: n });
        return;
      }
      throw new Refusal(n, `not a token, role, clause, font or theme line: "${s}"`,
        [`token <name> = <value>`, `role <name> : <props>`, `when <selection> : <props>`, `font <name> = <Family>, <fallback>`, `theme <name> of <style>`]);
    });
    return out;
  }

  function check(n, text) {
    const hex = text.match(/#[0-9a-fA-F]{3,8}\b/);
    if (hex) throw new Refusal(n, `colours are named here. "${hex[0]}" may only appear on a token line.`,
      [`token <name> = ${hex[0]}        (a new colour, named, for everyone)`, `then say the name instead of the value`]);
    const px = text.match(/\b(\d+(?:\.\d+)?)px\b/);
    if (px) { const k = Math.max(1, Math.round(parseFloat(px[1]) / 8));
      throw new Refusal(n, `${px[0]} is not on the scale. lengths are gap, gap xN, gap /N, or an em.`,
        [`gap x${k}                       (= ${k * 8}px at gap 8)`, `token gap = <n>            (moves everything)`]); }
  }

  function resolveTokens(st, themeName) {
    const raw = Object.assign({}, st.tokens);
    if (themeName && st.themes[themeName]) Object.assign(raw, st.themes[themeName].tokens);
    const done = {};
    const get = (name, seen = new Set()) => {
      if (name in done) return done[name];
      if (!(name in raw) || seen.has(name)) return null;
      seen.add(name);
      const v = raw[name].trim(); let m;
      if (HEX.test(v)) return done[name] = { type: "colour", value: v };
      if ((m = v.match(/^([\w.]+)\s+at\s+([\d.]+)%?$/))) {
        const base = get(m[1], seen), paper = HEX.test(raw.paper || "") ? { value: raw.paper } : get("paper", new Set(["__"]));
        if (base && base.type === "colour" && paper) return done[name] = { type: "colour", value: mix(paper.value, base.value, parseFloat(m[2]) / 100) };
      }
      if (/^\d+(\.\d+)?$/.test(v)) return done[name] = { type: "length", value: parseFloat(v) };
      if ((m = v.match(/^([\w-]+)\s+([\d.]+)\/([\d.]+)$/))) return done[name] = { type: "text", family: m[1], size: +m[2], leading: +m[3] };
      return done[name] = { type: "word", value: v };
    };
    const t = {}; Object.keys(raw).forEach(k => t[k] = get(k)); return t;
  }

  // ---- selections: the desk's own language, no new matching machinery ----
  function matches(sel, thing, world) {
    return sel.split(",").map(x => x.trim()).filter(Boolean).every(term => {
      let neg = false; if (term.startsWith("-")) { neg = true; term = term.slice(1); }
      return one(term, thing, world) !== neg;
    });
  }
  function one(term, t, world) {
    let m;
    if ((m = term.match(/^kind:(.+)$/))) return m[1].split("|").includes(t.kind);
    if ((m = term.match(/^tag:(.+)$/))) return (t.tags || []).includes(m[1]);
    if ((m = term.match(/^type:(.+)$/))) return t.type === m[1];
    if ((m = term.match(/^layout:(.+)$/))) return t.layout === m[1];
    if ((m = term.match(/^title:(.+)$/))) return (t.title || "").toLowerCase().includes(m[1].toLowerCase());
    if ((m = term.match(/^in:(.+)$/))) { let p = t.parent; const N = (world && world.nodes) || {}; while (p) { if (p === m[1]) return true; p = (N[p] || {}).parent; } return false; }
    if (term === "comments:open") return (t.comments || []).some(c => !c.resolved);
    if (term === "due") return !!t.due;
    if (term === "folded") return !!t.folded;
    return false;
  }

  // ---- properties ----
  const len = (e, T) => { let m;
    if ((m = e.match(/^([\w.]+)\s*x\s*([\d.]+)$/))) { const b = T[m[1]]; if (b && b.type === "length") return b.value * +m[2]; }
    if ((m = e.match(/^([\w.]+)\s*\/\s*([\d.]+)$/))) { const b = T[m[1]]; if (b && b.type === "length") return b.value / +m[2]; }
    if ((m = e.match(/^([\w.]+)$/))) { const b = T[m[1]]; if (b && b.type === "length") return b.value; }
    if ((m = e.match(/^([\d.]+)em$/))) return { em: +m[1] };
    return null; };
  const colour = (e, T) => { let m;
    if ((m = e.match(/^([\w.]+)\s+at\s+([\d.]+)%?$/))) { const b = T[m[1]], p = T.paper; if (b && b.type === "colour" && p) return mix(p.value, b.value, +m[2] / 100); }
    const t = T[e]; return t && t.type === "colour" ? t.value : null; };

  function prop(p, T) {
    let m;
    if ((m = p.match(/^show\s+(\w+)$/))) return { part: m[1], show: true };
    if ((m = p.match(/^hide\s+(\w+)$/))) return { part: m[1], show: false };
    if ((m = p.match(/^on\s+(.+)$/))) { const c = colour(m[1], T); return c ? { css: { background: c } } : null; }
    if ((m = p.match(/^([\w.]+)\s*->\s*(.+)$/))) { const c = colour(m[2], T); return c ? { css: { color: c } } : null; }
    if ((m = p.match(/^edge\s+(.+)$/))) { const c = colour(m[1], T); return c ? { css: { border: `1px solid ${c}` } } : null; }
    if ((m = p.match(/^border\s+(top|right|bottom|left)\s+(.+)$/))) { const c = colour(m[2], T); return c ? { css: { ["border-" + m[1]]: `1px solid ${c}` } } : null; }
    if ((m = p.match(/^corner\s+(.+)$/))) { const l = len(m[1], T); return typeof l === "number" ? { css: { "border-radius": l + "px" } } : null; }
    if ((m = p.match(/^pad\s+(.+)$/))) { const l = len(m[1], T); return typeof l === "number" ? { css: { padding: l + "px" } } : null; }
    if ((m = p.match(/^pad\s+(top|right|bottom|left)\s+(.+)$/))) { const l = len(m[2], T); return typeof l === "number" ? { css: { ["padding-" + m[1]]: l + "px" } } : null; }
    if ((m = p.match(/^space\s+(above|below)\s+(.+)$/))) { const l = len(m[2], T); return typeof l === "number" ? { css: { [m[1] === "above" ? "margin-top" : "margin-bottom"]: l + "px" } } : null; }
    if ((m = p.match(/^between\s+(.+)$/))) { const l = len(m[1], T); return typeof l === "number" ? { css: { gap: l + "px" } } : null; }
    if ((m = p.match(/^width\s+(.+)$/))) { const l = len(m[1], T); if (l && l.em) return { css: { "max-width": l.em + "em" } }; return typeof l === "number" ? { css: { width: l + "px" } } : null; }
    if ((m = p.match(/^lift\s+(.+)$/))) { const l = len(m[1], T); const c = T.ink && T.ink.value; return typeof l === "number" && c ? { css: { "box-shadow": `0 ${l}px ${l * 3}px ${hexToRgb(c).join(",").replace(/^/, "rgba(")},.10)` } } : null; }
    if (/^text\b/.test(p)) {
      const t = T[p.startsWith("text.") ? p.split(/\s+/)[0] : "text"];
      if (!t || t.type !== "text") return null;
      let mr;
      if ((mr = p.match(/\bat\s+([\d.]+)\b/))) throw new Refusal(0, `"text at ${mr[1]}" is not a step. the type ramp has steps, like the spacing scale.`,
        ["text down            (one step smaller)", "text down 2          (two steps)", "text up", "token ramp = <n>     (the ratio between steps)"]);
      const css = { "font-family": family(t.family), "line-height": t.leading };
      const ratio = T.ramp && T.ramp.type === "length" ? T.ramp.value : 1.15;
      let size = t.size, mm;
      if ((mm = p.match(/\bdown(?:\s+(\d+))?\b/))) size = t.size / Math.pow(ratio, parseInt(mm[1] || "1", 10));
      if ((mm = p.match(/\bup(?:\s+(\d+))?\b/))) size = t.size * Math.pow(ratio, parseInt(mm[1] || "1", 10));
      css["font-size"] = Math.round(size) + "px";
      if (/\bstrong\b/.test(p)) css["font-weight"] = 600;
      if (/\bmedium\b/.test(p)) css["font-weight"] = 500;
      if (/\bslant\b/.test(p)) css["font-style"] = "italic";
      if (/\btracked\b/.test(p)) css["letter-spacing"] = "0.04em";
      return { css };
    }
    // a1140 (Alex: "gentle flashing next to things that are waiting for me"): the language's one motion. The part fades
    // between full and 60% opacity (Pike c1251: never faint enough to lose the words), 2.5s a cycle; no movement, size or
    // colour. Its keyframes exist only for a viewer who has not asked for reduced motion (install), so for one who has,
    // the animation names nothing and the part is still. Every pulse shares one phase (install): six waiting things
    // breathe together as one signal, not six flickers out of step.
    if (p === "pulse") return { css: { animation: "r-pulse 2.5s ease-in-out infinite" } };
    const c = colour(p, T); return c ? { css: { color: c } } : null;
  }

  // ---- resolution with provenance (why :look) ----
  function lookOf(thing, st, T, world) {
    const layers = []; const parts = {};
    let role = thing.as || null;
    const hits = st.clauses.filter(c => matches(c.sel, thing, world));
    if (!role) hits.forEach(c => c.props.forEach(p => { const m = p.match(/^as\s*=\s*([\w.]+)$/); if (m) role = m[1]; }));
    if (role && st.roles[role]) layers.push({ from: `role ${role}`, line: st.roles[role].line, props: st.roles[role].props });
    hits.forEach(c => layers.push({ from: `when ${c.sel}`, line: c.line, props: c.props.filter(p => !/^as\s*=/.test(p)) }));
    if (thing.override) layers.push({ from: `override by ${thing.override.by}`, line: null, props: thing.override.props });
    const css = {}, owner = {}, unreadable = [];
    for (const L of layers) for (const p of L.props) {
      let r; try { r = prop(p, T); } catch (e) { unreadable.push({ prop: p, from: L.from, why: e.msg }); continue; }
      if (!r) { unreadable.push({ prop: p, from: L.from, why: "the renderer cannot read this property" }); continue; }
      if (r.part) { parts[r.part] = r.show; continue; }
      for (const [k, v] of Object.entries(r.css)) {
        const prev = owner[k];
        owner[k] = { value: v, from: L.from, line: L.line, prop: p, beat: prev ? [...(prev.beat || []), { value: prev.value, from: prev.from, line: prev.line }] : [] };
        css[k] = v;
      }
    }
    return { role, css, parts, layers, owner, unreadable };
  }

  // ---- installation: tokens become custom properties, roles become classes ----
  let current = null, tokens = null, sheet = null, themeName = "", FONTS = {}, pinned = false;
  const loaded = new Set();
  function family(f) {
    if (FONTS[f]) return `'${FONTS[f].face}', ${FONTS[f].fallback}`;
    return f === "mono" ? "ui-monospace, SFMono-Regular, Consolas, monospace" : f === "serif" ? "Georgia, 'Iowan Old Style', serif" : "Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif";
  }
  function loadFonts(fonts) {
    Object.values(fonts).forEach(({ face }) => {
      if (loaded.has(face) || typeof document === "undefined") return;
      loaded.add(face);
      const l = document.createElement("link");
      l.rel = "stylesheet"; l.href = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(face).replace(/%20/g, "+")}&display=swap`;
      document.head.appendChild(l);
    });
  }

  function install(src, theme) {
    const st = parse(src);                       // throws Refusal; nothing is installed on a refusal,
    const T = resolveTokens(st, theme);          // so the last working look survives by construction.
    current = st; tokens = T; themeName = theme || ""; FONTS = st.fonts || {}; loadFonts(FONTS);
    const decl = o => Object.entries(o).map(([k, v]) => `${k}:${v}`).join(";");
    const val = v => v.type === "colour" ? v.value : v.type === "length" ? v.value + "px" : v.type === "text" ? v.size + "px" : v.value;
    const vars = Object.entries(T).filter(([, v]) => v).flatMap(([k, v]) => [`--t-${k}:${val(v)}`, `--${k}:${val(v)}`]);
    // Aliases the apps were already written against when the shell had placeholder tokens. They are the
    // same values, not a second palette: --surface is --card, --font is the one family, --radius is one corner.
    if (T.card) vars.push(`--surface:${T.card.value}`);
    if (T.gap) vars.push(`--radius:${T.gap.value}px`);
    if (T.text) vars.push(`--font:${family(T.text.family)}`);
    let out = ":root{" + vars.join(";") + "}\n";
    for (const name of Object.keys(st.roles)) {
      const lk = lookOf({ as: name }, st, T, { nodes: {} });
      out += `.r-${name.replace(/\./g, "_")}{${decl(lk.css)}}\n`;
    }
    out += "@media (prefers-reduced-motion: no-preference){@keyframes r-pulse{0%,100%{opacity:1}50%{opacity:.6}}}\n";
    // A CSS animation starts when its part is painted, so a part repainted or unfolded later would be out of step.
    // Each one is pinned to the page's clock as it starts: the same moment is the same point of the fade everywhere.
    if (!pinned && document.addEventListener) { pinned = true; document.addEventListener("animationstart", e => {
      if (e.animationName === "r-pulse") e.target.getAnimations().forEach(a => { if (a.animationName === "r-pulse") a.startTime = 0; });
    }, true); }
    // The ramp, named, so an app can say a size instead of inventing one:
    //   font-size: var(--t-size-0)   is `text`;  --t-size--1 is `text down`;  --t-size-2 is `text up 2`.
    ramp().forEach(({ step, px }) => { out = out.replace(/^:root\{/, `:root{--t-size-${step}:${px}px;`); });
    if (!sheet) { sheet = document.createElement("style"); sheet.id = "one-style"; document.head.appendChild(sheet); }
    sheet.textContent = out;
    return st;
  }

  // ---- the ramp, and how far it actually reaches ----
  function ramp() {
    const t = tokens && tokens.text, r = tokens && tokens.ramp;
    if (!t || t.type !== "text") return [];
    const ratio = r && r.type === "length" ? r.value : 1.15;
    return [-3, -2, -1, 0, 1, 2, 3].map(step => ({ step, px: Math.round(t.size * Math.pow(ratio, step)) }));
  }

  // Every element on the page whose type size is NOT a step of the ramp, and who drew it.
  // This is the honesty mark for the style itself: a shared style is not enforced by existing.
  function reach(root = document.body) {
    const steps = new Set(ramp().map(s => s.px));
    const bad = new Map();
    root.querySelectorAll("*").forEach(el => {
      if (/^(SCRIPT|STYLE|TEMPLATE|NOSCRIPT|HEAD|META|LINK|TITLE)$/.test(el.tagName)) return;
      if (!el.textContent || !el.textContent.trim()) return;
      const px = parseFloat(getComputedStyle(el).fontSize);
      if (steps.has(Math.round(px * 100) / 100) || steps.has(Math.round(px))) return;
      const owner = (el.closest("[data-owner]") || {}).dataset ? el.closest("[data-owner]").dataset.owner : "shell";
      const key = owner + " @ " + (Math.round(px * 100) / 100) + "px";
      bad.set(key, (bad.get(key) || 0) + 1);
    });
    const steps2 = ramp();
    return { steps: steps2, offenders: [...bad.entries()].map(([k, n]) => ({ where: k, count: n })).sort((a, b) => b.count - a.count) };
  }

  // Snap every off-ramp size to the nearest step. Deliberately a TOGGLE: the difference between
  // on and off is the measure of how far the style language reaches on its own. See wren-10 §4.
  let snapped = [];
  function snap(on, root = document.body) {
    snapped.forEach(el => el.style.removeProperty("font-size"));
    snapped = [];
    if (!on) return 0;
    const steps = ramp();
    if (!steps.length) return 0;
    root.querySelectorAll("*").forEach(el => {
      if (/^(SCRIPT|STYLE|TEMPLATE|NOSCRIPT)$/.test(el.tagName)) return;
      const px = parseFloat(getComputedStyle(el).fontSize);
      if (steps.some(s => s.px === Math.round(px)) && Number.isInteger(px)) return;
      const near = steps.reduce((a, b) => Math.abs(b.px - px) < Math.abs(a.px - px) ? b : a);
      el.style.setProperty("font-size", near.px + "px", "important");
      snapped.push(el);
    });
    return snapped.length;
  }

  return {
    Refusal, parse, install, ramp, reach, snap,
    get style() { return current; },
    get tokens() { return tokens; },
    get theme() { return themeName; },
    token: n => tokens && tokens[n] ? (tokens[n].value !== undefined ? tokens[n].value : tokens[n]) : null,
    varName: n => `var(--t-${n})`,
    roleClass: n => "r-" + String(n).replace(/\./g, "_"),
    present: n => (current && current.presents[n]) || null,
    look: (thing, world) => lookOf(thing, current, tokens, world || { nodes: {} }),
    matches,
  };
})();
