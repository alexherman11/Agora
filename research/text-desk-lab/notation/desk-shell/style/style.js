// style/style.js : the browser's installer of a style. OWNER: Wren (file), Claude (8 Oct rewrite, logged in Rough spots).
//
// 8 Oct 2026, step 1 of the grammar unification: the style text is read ONCE, in Python (style.py), and every painter
// is handed the result: `looks`, role name -> a medium-neutral look (colours as hex, lengths in pixels, a face with
// its size on the ramp). This file no longer parses, checks, resolves tokens or matches selections; it keeps one
// small table from a look's keys to CSS, and the page-side duties no reader has: fonts loaded by name, the pulse
// pinned to one phase, shy parts shown near the pointer, and the ramp's honesty marks (reach, snap) for the old shell.
//
//   Style.install(looks)   -> injects :root custom properties and one .r-<role> class per role
//   Style.token(name)      -> the resolved value ("#3F5D73", 8, {family,size,leading})
//   Style.varName(name)    -> "var(--t-accent)"            Style.roleClass(name) -> "r-card"
//   Style.look(thing)      -> {role, look, css} for a thing wearing role `thing.as`
//   Style.Refusal          -> what a page keeps when the server's reader refused a text (line, msg, escapes)

const Style = (() => {
  class Refusal extends Error {
    constructor(line, msg, escapes) { super(msg); this.line = line; this.msg = msg; this.escapes = escapes || []; }
    toText() { return `refused${this.line ? ` (line ${this.line})` : ""}: ${this.msg}\n` + this.escapes.map(e => `  -> ${e}`).join("\n"); }
  }
  const hexToRgb = h => { h = h.replace("#", ""); if (h.length === 3) h = h.split("").map(c => c + c).join(""); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)); };

  // ---- the table: a look's key -> CSS. The only place this file knows what a key means. ----
  const px = n => n + "px";
  const TABLE = {
    on: v => ({ background: v }),
    ink: v => ({ color: v }),
    edge: v => ({ border: `1px solid ${v}` }),
    corner: v => ({ "border-radius": px(v) }),
    pad: v => ({ padding: px(v) }),
    space_above: v => ({ "margin-top": px(v) }),
    space_below: v => ({ "margin-bottom": px(v) }),
    between: v => ({ gap: px(v) }),
    height: v => ({ "min-height": px(v) }),
    height_em: v => ({ "min-height": v + "em" }),
    width: v => ({ width: px(v) }),
    width_em: v => ({ "max-width": v + "em" }),
    lift: (v, look) => ({ "box-shadow": `0 ${v}px ${v * 3}px rgba(${hexToRgb(look.lift_ink || "#000").join(",")},.10)` }),
    text: t => {
      const css = { "font-family": t.family, "line-height": t.leading, "font-size": px(t.size) };
      if (t.weight) css["font-weight"] = t.weight;
      if (t.slant) css["font-style"] = "italic";
      if (t.tracked) css["letter-spacing"] = "0.04em";
      return css;
    },
    afloat: () => ({ height: "0", "min-height": "0", overflow: "visible" }),
    shy: () => ({ opacity: "0", "--shy": "1" }),
    pulse: () => ({ animation: "r-pulse 2.5s ease-in-out infinite" }),
  };
  for (const side of ["top", "right", "bottom", "left"]) {
    TABLE["border_" + side] = v => ({ ["border-" + side]: `1px solid ${v}` });
    TABLE["pad_" + side] = v => ({ ["padding-" + side]: px(v) });
  }
  function cssOf(look) {
    const css = {};
    for (const [k, v] of Object.entries(look || {})) if (TABLE[k]) Object.assign(css, TABLE[k](v, look));
    return css;
  }

  // ---- installation: tokens become custom properties, roles become classes ----
  let current = null, tokens = null, sheet = null, pinned = false, afloat = [];
  const loaded = new Set();
  function loadFonts(fonts) {
    Object.values(fonts || {}).forEach(({ face }) => {
      if (!face || loaded.has(face) || typeof document === "undefined") return;
      loaded.add(face);
      const l = document.createElement("link");
      l.rel = "stylesheet"; l.href = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(face).replace(/%20/g, "+")}&display=swap`;
      document.head.appendChild(l);
    });
  }
  const cls = name => "r-" + String(name).replace(/\./g, "_");
  function install(looks) {
    if (!looks || !looks.roles) throw new Refusal(0, "install wants the looks the server read (GET /api/style), not a style text");
    current = looks; tokens = looks.tokens || {}; loadFonts(looks.fonts);
    const decl = o => Object.entries(o).map(([k, v]) => `${k}:${v}`).join(";");
    const val = v => v.type === "colour" ? v.value : v.type === "length" ? v.value + "px" : v.type === "text" ? v.size + "px" : v.value;
    const vars = Object.entries(tokens).filter(([, v]) => v).flatMap(([k, v]) => [`--t-${k}:${val(v)}`, `--${k}:${val(v)}`]);
    // Aliases the old shell's apps were written against: the same values, not a second palette.
    if (tokens.card) vars.push(`--surface:${tokens.card.value}`);
    if (tokens.gap) vars.push(`--radius:${tokens.gap.value}px`);
    if (tokens.text) { const f = Object.values(looks.roles).map(r => r.look.text).find(Boolean); if (f) vars.push(`--font:${f.family}`); }
    (looks.ramp || []).forEach(({ step, px }) => vars.push(`--t-size-${step}:${px}px`));   // the ramp, named: var(--t-size-0) is `text`
    afloat = [];
    let out = ":root{" + vars.join(";") + "}\n";
    for (const [name, r] of Object.entries(looks.roles)) {
      const c = "." + cls(name);
      out += `${c}{${decl(cssOf(r.look))}}\n`;
      if (r.look.afloat) afloat.push(c);
      if (r.look.shy)      // shy: seen when the pointer or the caret is in the part holding it (or the one above), or when it has focus
        out += [":hover > ", ":hover > * > ", ":focus-within > ", ":focus-within > * > "].map(a => a + c).join(",") + `,${c}:focus{opacity:1}\n`;
    }
    // a1140: the language's one motion, only for a viewer who has not asked for reduced motion; every pulse in one phase
    out += "@media (prefers-reduced-motion: no-preference){@keyframes r-pulse{0%,100%{opacity:1}50%{opacity:.6}}}\n";
    if (!pinned && typeof document !== "undefined" && document.addEventListener) { pinned = true; document.addEventListener("animationstart", e => {
      if (e.animationName === "r-pulse") e.target.getAnimations().forEach(a => { if (a.animationName === "r-pulse") a.startTime = 0; });
    }, true); }
    if (!sheet) { sheet = document.createElement("style"); sheet.id = "one-style"; document.head.appendChild(sheet); }
    sheet.textContent = out;
    return looks;
  }

  // ---- the ramp, and how far it actually reaches (the old shell's honesty marks; they measure the page, not a text) ----
  function ramp() { return (current && current.ramp) || []; }
  function reach(root = document.body) {
    const steps = new Set(ramp().map(s => s.px));
    const bad = new Map();
    root.querySelectorAll("*").forEach(el => {
      if (/^(SCRIPT|STYLE|TEMPLATE|NOSCRIPT|HEAD|META|LINK|TITLE)$/.test(el.tagName)) return;
      if (!el.textContent || !el.textContent.trim()) return;
      const p = parseFloat(getComputedStyle(el).fontSize);
      if (steps.has(Math.round(p * 100) / 100) || steps.has(Math.round(p))) return;
      const owner = (el.closest("[data-owner]") || {}).dataset ? el.closest("[data-owner]").dataset.owner : "shell";
      const key = owner + " @ " + (Math.round(p * 100) / 100) + "px";
      bad.set(key, (bad.get(key) || 0) + 1);
    });
    return { steps: ramp(), offenders: [...bad.entries()].map(([k, n]) => ({ where: k, count: n })).sort((a, b) => b.count - a.count) };
  }
  let snapped = [];
  function snap(on, root = document.body) {
    snapped.forEach(el => el.style.removeProperty("font-size"));
    snapped = [];
    if (!on) return 0;
    const steps = ramp();
    if (!steps.length) return 0;
    root.querySelectorAll("*").forEach(el => {
      if (/^(SCRIPT|STYLE|TEMPLATE|NOSCRIPT)$/.test(el.tagName)) return;
      const p = parseFloat(getComputedStyle(el).fontSize);
      if (steps.some(s => s.px === Math.round(p)) && Number.isInteger(p)) return;
      const near = steps.reduce((a, b) => Math.abs(b.px - p) < Math.abs(a.px - p) ? b : a);
      el.style.setProperty("font-size", near.px + "px", "important");
      snapped.push(el);
    });
    return snapped.length;
  }

  return {
    Refusal, install, ramp, reach, snap, cssOf,
    get style() { return current; },
    get tokens() { return tokens; },
    get theme() { return (current && current.theme) || ""; },
    get themes() { return (current && current.themes) || []; },
    get afloat() { return afloat; },      // the classes of parts that take no room (lens.js keeps them from lying on each other)
    token: n => tokens && tokens[n] ? (tokens[n].value !== undefined ? tokens[n].value : tokens[n]) : null,
    varName: n => `var(--t-${n})`,
    roleClass: cls,
    present: () => null,
    look: thing => { const role = (thing && thing.as) || null, r = role && current && current.roles[role]; return { role, look: r ? r.look : {}, css: cssOf(r ? r.look : {}), unreadable: r ? r.unread : [] }; },
  };
})();
