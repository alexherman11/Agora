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
    // a5504: the shadow is a custom property, so a rail and a glow can be drawn beside it in one box-shadow
    lift: (v, look) => ({ "--lift": `0 ${v}px ${v * 3}px rgba(${hexToRgb(look.lift_ink || "#000").join(",")},${look.lift_shadow ? ".45" : ".10"})` }),
    rail: v => ({ "--rail": `inset 3px 0 0 ${v}` }),
    glow: v => ({ "--glow": v, animation: "r-glow 2.8s ease-in-out infinite" }),
    glide: () => ({}),
    text: t => {
      // no joined letters (13 Oct): a pixel face's "fi" drew as one glyph that read as an A ("Arst" for "first")
      const css = { "font-family": t.family, "line-height": t.leading, "font-size": px(t.size), "font-variant-ligatures": "none" };
      if (t.weight) css["font-weight"] = t.weight;
      if (t.slant) css["font-style"] = "italic";
      if (t.tracked) css["letter-spacing"] = "0.04em";
      return css;
    },
    afloat: () => ({ height: "0", "min-height": "0", overflow: "visible", transition: "transform 140ms ease-out", "will-change": "transform" }),
    shy: () => ({ opacity: "0", "--shy": "1" }),
    pulse: () => ({ animation: "r-pulse 2.5s ease-in-out infinite" }),
    align: v => ({ "align-self": { start: "flex-start", end: "flex-end", center: "center", stretch: "stretch" }[v] }),   // 15 Oct
    wave: () => ({ "white-space": "pre" }),     // 14 Oct: its characters are spans the painter makes (lens.js wave)
    touch: () => ({ cursor: "pointer", transition: "transform 120ms ease-out, filter 120ms ease-out" }),   // a5500: and the rules in install
    leaves: () => ({}), away: () => ({}),        // a6010: the one rule in install
  };
  for (const side of ["top", "right", "bottom", "left"]) {
    TABLE["border_" + side] = v => ({ ["border-" + side]: `1px solid ${v}` });
    TABLE["pad_" + side] = v => ({ ["padding-" + side]: px(v) });
  }
  function cssOf(look) {
    const css = {};
    for (const [k, v] of Object.entries(look || {})) if (TABLE[k]) Object.assign(css, TABLE[k](v, look));
    if (look && (look.lift || look.rail || look.glow))      // the one box-shadow: the rail, then the shadow (r-glow adds the halo)
      css["box-shadow"] = "var(--rail, 0 0 transparent), var(--lift, 0 0 transparent)";
    return css;
  }

  // ---- installation: tokens become custom properties, roles become classes ----
  let current = null, tokens = null, sheet = null, pinned = false, afloat = [], glide = [];
  const loaded = new Set();
  function loadFonts(fonts) {
    Object.values(fonts || {}).forEach(({ face }) => {
      if (!face || loaded.has(face) || typeof document === "undefined") return;
      loaded.add(face);
      const l = document.createElement("link");
      // 13 Oct: `medium` and `strong` are real weights of the face when it has them (asked for alone, a face came in one
      // weight and the browser faked the rest); a face without them refuses the whole request, and is asked for plainly
      const href = w => `https://fonts.googleapis.com/css2?family=${encodeURIComponent(face).replace(/%20/g, "+")}${w}&display=swap`;
      l.rel = "stylesheet"; l.href = href(":wght@400;500;600"); l.onerror = () => { l.onerror = null; l.href = href(""); };
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
    afloat = []; glide = [];
    let out = ":root{" + vars.join(";") + "}\n";
    for (const [name, r] of Object.entries(looks.roles)) {
      const c = "." + cls(name);
      out += `${c}{${decl(cssOf(r.look))}}\n`;
      if (r.look.afloat) afloat.push(c);
      if (r.look.glide) glide.push(c);
      if (r.look.shy)      // shy: seen when the pointer or the caret is in the part holding it (or the one above), or when it has focus
        out += [":hover > ", ":hover > * > ", ":focus-within > ", ":focus-within > * > "].map(a => a + c).join(",") + `,${c}:focus{opacity:1}\n`;
      if (r.look.touch)    // a5500: the part answers the pointer, brighter under it, darker while pressed; it moves only below
        out += `${c}:hover{filter:brightness(1.3)}${c}:active{filter:brightness(.85)}`
          + `@media (prefers-reduced-motion: no-preference){${c}:hover{transform:translateY(-3px)}${c}:active{transform:translateY(0) scale(.94)}}\n`;
    }
    // a6010 (Snappy Desk stage 3 for presses): a part whose look says `leaves` is not drawn while a press on a part inside
    // it whose look says `away` is on its way (lens.js marks the pressed part data-sending until its answer is painted);
    // a refusal takes the mark off, so it is drawn again beside the reason, and an answer's scene shows where it went.
    // Its room stays until then: hidden, not taken out, so the next card does not slide under the pointer and take the
    // second click of a double-click (seen headless: three quick presses landed at one spot on three cards)
    const leaves = Object.entries(looks.roles).filter(([, r]) => r.look.leaves).map(([n]) => "." + cls(n));
    const away = Object.entries(looks.roles).filter(([, r]) => r.look.away).map(([n]) => "." + cls(n));
    if (leaves.length && away.length) out += `:is(${leaves.join(",")}):has(:is(${away.join(",")})[data-sending="1"]){visibility:hidden}\n`;
    // a1140: the language's one motion, only for a viewer who has not asked for reduced motion; every pulse in one phase
    out += "@media (prefers-reduced-motion: no-preference){@keyframes r-pulse{0%,100%{opacity:1}50%{opacity:.6}}}\n";
    // a5504: `glow`, a halo of the part's glow colour breathing beside its rail and shadow; a still ring for reduced motion
    const base = "var(--rail, 0 0 transparent), var(--lift, 0 0 transparent)";
    out += `@media (prefers-reduced-motion: no-preference){@keyframes r-glow{0%,100%{box-shadow:${base}, 0 0 0 1px color-mix(in srgb, var(--glow) 30%, transparent), 0 0 2px 0 color-mix(in srgb, var(--glow) 0%, transparent)}`
      + `50%{box-shadow:${base}, 0 0 0 1px color-mix(in srgb, var(--glow) 70%, transparent), 0 0 18px 1px color-mix(in srgb, var(--glow) 32%, transparent)}}}\n`;
    out += `@media (prefers-reduced-motion: reduce){${Object.entries(looks.roles).filter(([, r]) => r.look.glow).map(([n]) => "." + cls(n)).join(",") || ".r-none"}{box-shadow:${base}, 0 0 0 1px color-mix(in srgb, var(--glow) 60%, transparent)}}\n`;
    // 14 Oct (Alex: 'an animation on those three dots, ideally a cool animation'): `wave`, each character rising in
    // turn and brightening, then settling; still for a viewer who asked for reduced motion
    out += "@media (prefers-reduced-motion: no-preference){@keyframes r-wave{0%,60%,100%{transform:translateY(0);opacity:.35}30%{transform:translateY(-0.35em);opacity:1}}"
      + ".t-wave{display:inline-block;animation:r-wave 1.3s ease-in-out infinite;animation-delay:calc(var(--i) * 0.16s)}}\n";
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
    get glide() { return glide; },        // a5504: the classes of parts that travel to where their thing is painted next
    token: n => tokens && tokens[n] ? (tokens[n].value !== undefined ? tokens[n].value : tokens[n]) : null,
    varName: n => `var(--t-${n})`,
    roleClass: cls,
    present: () => null,
    look: thing => { const role = (thing && thing.as) || null, r = role && current && current.roles[role]; return { role, look: r ? r.look : {}, css: cssOf(r ? r.look : {}), unreadable: r ? r.unread : [] }; },
  };
})();
