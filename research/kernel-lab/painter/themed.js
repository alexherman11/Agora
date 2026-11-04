// EDITING THE PAINTER (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
// The painter's vocabulary (formats, handles, scopes, parts) is shared by every app. Add to it only what any lens could
// use, documented where lens authors read it (ARRANGEMENT.md); never a handle, format or branch for one app. If one app
// needs something, the general form of it is the change.
//
// Wearing the theme: how the component painter's colours follow the viewer's theme (research/kernel-lab/theme/THEMES.md).
//
// The painter's old tokens (paper, card, ink, muted, accent and the colour names) are roles: the host passes them already
// mapped (theme.paper = the theme's surface ...). A lens may also write colours of its own, as hex, in its part styles and
// its tokens (the board's nb-soft, nb-kind-event ...). Those were written for the place's light look, so `lift` carries each
// one across: neutrals ride the theme's own ramp from ink to surface, and a coloured one keeps its hue family, taking the
// theme's colour for that family, with its saturation and lightness kept in proportion. A lens that wants its colours exactly
// as written sets the token `pin-colours` (any value): a deliberate exception that the theme shows rather than overrides.
// Nothing here reads or writes the world; it is arithmetic on colours.
const Themed = (() => {
  const cbrt = Math.cbrt;
  const lin = c => { c /= 255; return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
  const gam = x => { x = Math.max(0, Math.min(1, x)); return 255 * (x <= 0.0031308 ? 12.92 * x : 1.055 * Math.pow(x, 1 / 2.4) - 0.055); };
  const rgb = h => { h = h.replace('#', ''); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)); };
  const toLab = h => {
    const [r, g, b] = rgb(h).map(lin);
    const l = cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
    const m = cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
    const s = cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
    return [0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s, 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s, 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s];
  };
  const fromLab = ([L, a, b]) => {
    const l = Math.pow(L + 0.3963377774 * a + 0.2158037573 * b, 3), m = Math.pow(L - 0.1055613458 * a - 0.0638541728 * b, 3), s = Math.pow(L - 0.0894841775 * a - 1.2914855480 * b, 3);
    const out = [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s, -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s];
    return '#' + out.map(x => Math.round(gam(x)).toString(16).padStart(2, '0')).join('');
  };
  const lch = h => { const [L, a, b] = toLab(h); return [L, Math.hypot(a, b), (Math.atan2(b, a) * 180 / Math.PI + 360) % 360]; };
  const fromLch = (L, C, h) => fromLab([L, C * Math.cos(h * Math.PI / 180), C * Math.sin(h * Math.PI / 180)]);
  const mixLab = (a, b, t) => { const x = toLab(a), y = toLab(b); return fromLab(x.map((v, i) => v + (y[i] - v) * t)); };

  // The place's own light look is the reference the lenses were written against.
  const REF = {
    neutral: [[0, 'ink7'], [0.38, 'ink'], [0.65, 'muted'], [0.975, 'surface'], [1, 'raised']],
    slots: { accent: '#638779', base08: '#cf514a', base09: '#c58332', base0A: '#c9a227', base0B: '#5e9a6e', base0C: '#4a9aa5', base0D: '#507ebc', base0E: '#8a6fb0', base0F: '#a0714f' },
  };
  const REF_LCH = Object.fromEntries(Object.entries(REF.slots).map(([k, v]) => [k, lch(v)]));
  const NAMED = { white: '#ffffff', black: '#000000', red: '#ff0000', blue: '#0000ff', green: '#008000', grey: '#808080', gray: '#808080', orange: '#ffa500', purple: '#800080', pink: '#ffc0cb', yellow: '#ffff00' };

  function parse(value) {
    let v = String(value).trim().toLowerCase();
    if (v === 'transparent') return null;
    if (NAMED[v]) v = NAMED[v];
    let m = /^#([0-9a-f]{3,8})$/.exec(v);
    if (!m) return null;
    let h = m[1];
    if (h.length === 3 || h.length === 4) h = [...h].map(c => c + c).join('');
    if (h.length !== 6 && h.length !== 8) return null;
    return { hex: '#' + h.slice(0, 6), alpha: h.length === 8 ? h.slice(6) : '' };
  }

  function wearing() {
    const t = (typeof theme !== 'undefined' && theme) || {};
    return t.roles && t.palette ? t : null;
  }

  function neutral(L, t) {
    const stops = REF.neutral.map(([l, name]) => [l, name === 'ink7' ? t.palette.base07 : name === 'ink' ? t.roles.ink : name === 'muted' ? t.roles['ink-muted'] : name === 'surface' ? t.roles.surface : t.roles.raised]);
    L = Math.max(0, Math.min(1, L));
    for (let i = 1; i < stops.length; i++) if (L <= stops[i][0]) { const [l0, c0] = stops[i - 1], [l1, c1] = stops[i]; return mixLab(c0, c1, (L - l0) / (l1 - l0)); }
    return stops[stops.length - 1][1];
  }

  function slotColour(name, t) { return name === 'accent' ? t.roles.accent : t.palette[name]; }

  // One colour written for the light look, as the theme wears it.
  function lift(value, t = wearing()) {
    if (!t) return value;
    const p = parse(value);
    if (!p) return value;
    const [L, C, h] = lch(p.hex);
    const dist = (a, b) => { const d = Math.abs(a - b) % 360; return d > 180 ? 360 - d : d; };
    let out;
    let best = 'accent', bd = 1e9;
    for (const [name, [, , rh]] of Object.entries(REF_LCH)) { const d = dist(h, rh); if (d < bd) { bd = d; best = name; } }
    if (best === 'base0B') best = 'accent';          // the greens of a lens written for a sage place are its accent
    const [rL, rC, rH] = REF_LCH[best];
    const target = lch(slotColour(best, t));
    if (C < 0.007) {
      out = neutral(L, t);                            // a grey rides the theme's ink-to-surface ramp
    } else if (C < 0.03 || (L > 0.9 && C < 0.08)) {
      // a tint (a faintly coloured grey, or a pale wash of a colour): the theme's grey with the same breath of that colour
      out = fromLch(lch(neutral(L, t))[0], C * (t.variant === 'dark' ? 0.8 : 1), target[2] + (dist(target[2], rH) < 25 ? h - rH : 0));
    } else {
      // a colour: the theme's colour for that family, as much lighter or darker as the original was (about half that, the other way, on a dark theme)
      const Lt = target[0] + (t.variant === 'dark' ? -1 : 1) * (L - rL) * (t.variant === 'dark' ? 0.55 : 1);
      const Ct = Math.min(0.32, C * Math.max(0.5, Math.min(2, target[1] / rC)));
      out = fromLch(Math.max(0, Math.min(1, Lt)), Ct, target[2] + (h - rH));
    }
    return out + p.alpha;
  }

  const COLOUR = /^(#[0-9a-fA-F]{3,8}|transparent|black|white|red|blue|green|grey|gray|orange|purple|pink|yellow)$/;

  // A lens's token values as this viewer's theme wears them. In the place's own light look (the reference) this is the
  // identity, so nothing changes there; in any other theme every colour moves with it.
  function tokens(planTokens, t = wearing()) {
    const out = { ...(planTokens || {}) };
    if (!t || 'pin-colours' in out) return out;
    for (const [k, v] of Object.entries(out)) if (typeof v === 'string' && COLOUR.test(v)) out[k] = lift(v, t);
    return out;
  }
  // Colours a component's stylesheet declares once, as custom properties on :root (the board's --board-colour-N), are worn
  // the same way: each is lifted and set on the root, which wins over the stylesheet. Names in `skip` are the painter's own.
  function rootVars(skip = new Set(), t = wearing()) {
    if (!t) return;
    for (const sheet of document.styleSheets) {
      let rules;
      try { rules = sheet.cssRules; } catch (e) { continue; }
      for (const rule of rules) {
        if (rule.type !== 1 || rule.selectorText !== ':root') continue;
        for (let i = 0; i < rule.style.length; i++) {
          const name = rule.style[i];
          if (!name.startsWith('--') || name.startsWith('--ag-') || skip.has(name.slice(2))) continue;
          const v = rule.style.getPropertyValue(name).trim();
          if (COLOUR.test(v)) document.documentElement.style.setProperty(name, lift(v, t));
        }
      }
    }
  }
  const pinned = planTokens => !!planTokens && 'pin-colours' in planTokens;
  return { lift, tokens, pinned, wearing, rootVars };
})();
