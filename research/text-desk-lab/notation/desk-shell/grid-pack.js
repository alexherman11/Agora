// Opt-in item layout only: no partition, gesture, world state or element reordering.
(function (host) {
  "use strict";
  const number = x => Math.max(0, parseFloat(x) || 0);
  function span(width, column, gap, columns) {
    return Math.min(columns, Math.max(1, Math.ceil((width + gap - .01) / (column + gap))));
  }
  // Deterministic bottom-left first fit, including holes under spanning items.
  // Items are considered in list order; visual order may differ, DOM/Tab never do.
  function solve(columns, gap, items) {
    const placed = [];
    for (const item of items) {
      const wide = Math.min(columns, Math.max(1, item.span)), height = Math.max(1, Math.ceil(item.height));
      let best = null;
      for (let x = 0; x <= columns - wide; x++) {
        let y = 0, hit;
        do {
          hit = placed.find(p => x < p.x + p.span && x + wide > p.x &&
            y < p.y + p.height + gap && y + height + gap > p.y);
          if (hit) y = hit.y + hit.height + gap;
        } while (hit);
        if (!best || y < best.y) best = { x, y, span: wide, height };
      }
      placed.push(best);
    }
    return placed;
  }

  // Injected platform enables deterministic DOM/observer tests without a browser.
  function painter(env) {
    const live = new Map();
    const owned = ["width", "maxWidth", "minWidth", "gridColumn", "gridRow", "alignSelf", "overflowX"];
    const save = c => Object.fromEntries(owned.map(k => [k, c.style[k]]));
    const restore = (c, original) => Object.assign(c.style, original);
    let frame = 0, watching = false;
    const css = el => env.getComputedStyle(el);
    const size = el => { const r = el.getBoundingClientRect(); return [r.width, r.height]; };
    const same = (a, b) => a && Math.abs(a[0] - b[0]) < .1 && Math.abs(a[1] - b[1]) < .1;
    function schedule(state) {
      state.dirty = true;
      if (!frame) frame = env.requestAnimationFrame(flush);
    }
    function flush() {
      frame = 0;
      for (const [el, s] of live) {
        if (!el.isConnected) {
          for (const [c, original] of s.original) restore(c, original);
          el.style.gridAutoRows = s.rows; el.style.rowGap = s.gap;
          s.ro.disconnect(); live.delete(el);
          continue;
        }
        if (s.dirty) { s.dirty = false; measure(el, s); }
      }
    }
    function measure(el, state) {
      // Remove prior explicit spans before counting auto-fill tracks. Otherwise a
      // formerly wide item creates implicit columns after a narrower resize.
      for (const c of el.children) if (c.dataset.key) { c.style.gridColumn = ""; c.style.gridRow = ""; }
      const cs = css(el), width = el.clientWidth - number(cs.paddingLeft) - number(cs.paddingRight);
      if (!(width > 0)) {
        state.rootWidth = size(el)[0]; // a later reveal must schedule, even at the old visible width
        return;
      }
      const columns = cs.gridTemplateColumns.trim().split(/\s+/).filter(t => /^\d/.test(t)).length;
      if (!columns) return;
      // Row gap is owned by packing; retain authored column-gap as the spacing policy.
      const gap = Math.ceil(number(cs.columnGap)), column = (width - (columns - 1) * gap) / columns;
      const children = [...el.children].filter(c => c.dataset.key && !c.hidden && css(c).display !== "none");
      for (const c of state.children) if (!children.includes(c)) {
        state.ro.unobserve(c);
        if (state.original.has(c)) restore(c, state.original.get(c));
        state.original.delete(c);
      }
      state.children = children;
      for (const c of children) {
        if (!state.original.has(c)) { state.original.set(c, save(c)); state.ro.observe(c); }
        // Synchronous measure phases: never clone/reparent an editor or replace its text.
        c.style.width = "min-content"; c.style.maxWidth = "none"; c.style.minWidth = "0";
        c.style.gridColumn = `1 / span ${columns}`;
      }
      const intrinsic = children.map(c => {
        const st = css(c);
        return c.getBoundingClientRect().width + number(st.marginLeft) + number(st.marginRight);
      });
      children.forEach((c, i) => {
        restore(c, state.original.get(c));
        c.style.gridColumn = `span ${span(intrinsic[i], column, gap, columns)}`;
        c.style.gridRow = "auto"; c.style.alignSelf = "start";
        c.style.minWidth = "0"; c.style.maxWidth = "100%";
        // Physical impossibility stays local and reachable, never HUD overflow or scaling.
        if (intrinsic[i] > width + .1) c.style.overflowX = "auto";
      });
      el.style.gridAutoRows = "1px"; el.style.rowGap = "0px";
      const boxes = solve(columns, gap, children.map((c, i) => {
        const st = css(c);
        return { span: span(intrinsic[i], column, gap, columns),
          height: c.getBoundingClientRect().height + number(st.marginTop) + number(st.marginBottom) };
      }));
      children.forEach((c, i) => {
        const p = boxes[i];
        c.style.gridColumn = `${p.x + 1} / span ${p.span}`;
        c.style.gridRow = `${p.y + 1} / span ${p.height}`;
      });
      state.boxes = boxes;
      state.rootWidth = size(el)[0];
      state.sizes = new Map(children.map(c => [c, size(c)])); // ignore own placement notifications
    }
    function attach(el) {
      let s = live.get(el);
      if (!s) {
        s = { dirty: true, children: [], original: new Map(), sizes: new Map(), boxes: [],
          rows: el.style.gridAutoRows, gap: el.style.rowGap };
        s.ro = new env.ResizeObserver(entries => {
          if (entries.some(e => e.target === el ? !Number.isFinite(s.rootWidth) || Math.abs(size(el)[0] - s.rootWidth) >= .1 :
            !same(size(e.target), s.sizes.get(e.target)))) schedule(s);
        });
        live.set(el, s); s.ro.observe(el);
      }
      if (!watching) {
        watching = true;
        new env.MutationObserver(records => {
          for (const [root, st] of live) {
            if (!root.isConnected || records.some(r => root.contains(r.target) || r.target.contains?.(root))) schedule(st);
          }
        }).observe(env.document.documentElement, { subtree: true, childList: true, characterData: true,
          attributes: true, attributeFilter: ["class", "hidden"] });
        env.addEventListener("resize", () => { for (const st of live.values()) schedule(st); });
        env.document.fonts?.addEventListener("loadingdone", () => { for (const st of live.values()) schedule(st); });
      }
      schedule(s);
    }
    // Later carry consumers may read this geometry; no carry policy lives here.
    function geometry(el) {
      const s = live.get(el);
      return s ? s.boxes.map((p, i) => ({ key: s.children[i].dataset.key, ...p })) : [];
    }
    return { attach, geometry };
  }
  const api = { solve, span, painter };
  if (typeof module !== "undefined") module.exports = api;
  if (host.document) host.GridPack = { ...api, ...painter(host) };
})(typeof window === "undefined" ? globalThis : window);
