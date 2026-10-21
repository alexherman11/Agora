// Repeated shared frames may declare `resize <world prop> min <CSS pixels>`.
// Geometry is a preview; the two fenced desk acts are the only lasting state.
(function (root) {
  "use strict";
  const number = x => parseFloat(x) || 0;
  // Minimum outer sizes plus weighted surplus. In a physically too-small viewport
  // the minima scale together, keeping everything inside its parent.
  function allocation(space, minima, weights) {
    space = Math.max(0, space);
    const total = minima.reduce((a, b) => a + b, 0);
    const scale = total > space ? space / total : 1;
    const bases = minima.map(m => m * scale), extra = Math.max(0, space - total);
    const sum = weights.reduce((a, b) => a + b, 0);
    return { bases, sizes: bases.map((m, i) => m + extra * weights[i] / sum) };
  }
  function pair(a, b, minA, minB, wa, wb, delta) {
    const extra = a + b - minA - minB, sum = wa + wb;
    if (extra < .01) return [wa, wb];
    const first = Math.max(.000001, Math.min(1 - .000001, (a + delta - minA) / extra));
    return [sum * first, sum * (1 - first)];
  }
  function samePart(a, b) {
    // The two occurrences must share one definition: its fence then protects both
    // commands. Their distinct property and membership reads are combined below.
    return a && b && a.path === b.path && a.hash === b.hash && a.lens === b.lens;
  }
  function install(paint, api) {
    let handles = [], groups = [], active = null, pending = false, laying = false;
    const boxSize = (b, axis) => axis === "x" ? b.width : b.height;
    const chrome = (el, axis) => {
      const s = getComputedStyle(el);
      return axis === "x" ? number(s.paddingLeft) + number(s.paddingRight) + number(s.borderLeftWidth) + number(s.borderRightWidth)
        : number(s.paddingTop) + number(s.paddingBottom) + number(s.borderTopWidth) + number(s.borderBottomWidth);
    };
    const visible = e => !e.hidden && e.getClientRects().length && getComputedStyle(e).display !== "none";
    function layout() {
      if (laying || active || pending) return;
      laying = true;
      for (const g of groups) {
        const s = getComputedStyle(g.el), keyed = [...g.el.children].filter(e => e.dataset.key && visible(e));
        const gap = number(g.axis === "x" ? s.columnGap : s.rowGap);
        const content = (g.axis === "x" ? g.el.clientWidth - number(s.paddingLeft) - number(s.paddingRight)
          : g.el.clientHeight - number(s.paddingTop) - number(s.paddingBottom));
        const fixed = keyed.filter(e => !g.items.includes(e)).reduce((v, e) => v + boxSize(e.getBoundingClientRect(), g.axis), 0);
        const space = Math.max(0, content - gap * Math.max(0, keyed.length - 1) - fixed);
        // Intrinsic border/padding is also a lower bound. No magic HUD names.
        const mins = g.items.map(e => Math.max(e._n.paint.resize[1], chrome(e, g.axis)));
        const weights = g.items.map(e => e._n.paint.share);
        const fit = allocation(space, mins, weights); g.bases = fit.bases;
        g.items.forEach((e, i) => {
          const basis = getComputedStyle(e).boxSizing === "border-box" ? fit.bases[i] : fit.bases[i] - chrome(e, g.axis);
          e.style.flex = `${weights[i]} 1 ${Math.max(0, basis)}px`;
        });
      }
      position(); laying = false;
    }
    function position() {
      for (const h of handles) {
        const a = h.a.getBoundingClientRect(), b = h.b.getBoundingClientRect(), p = h.g.el.getBoundingClientRect();
        const x = h.g.axis === "x";
        const mid = x ? (a.right + b.left) / 2 : (a.bottom + b.top) / 2;
        Object.assign(h.el.style, x
          ? { left: mid - p.left - h.g.el.clientLeft - 6 + "px", top: Math.max(a.top, b.top) - p.top - h.g.el.clientTop + "px",
              width: "12px", height: Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top)) + "px" }
          : { top: mid - p.top - h.g.el.clientTop - 6 + "px", left: Math.max(a.left, b.left) - p.left - h.g.el.clientLeft + "px",
              height: "12px", width: Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) + "px" });
      }
    }
    function begin(h) {
      if (active || pending || api.busy()) return false;
      const i = h.g.items.indexOf(h.a), j = h.g.items.indexOf(h.b);
      active = { h, a: h.a._n, b: h.b._n, wa: h.a._n.paint.share, wb: h.b._n.paint.share,
        sa: boxSize(h.a.getBoundingClientRect(), h.g.axis), sb: boxSize(h.b.getBoundingClientRect(), h.g.axis),
        ma: h.g.bases[i], mb: h.g.bases[j], delta: 0 };
      api.hold(true); document.documentElement.dataset.resizing = h.g.axis;
      return true;
    }
    function move(delta) {
      if (!active) return;
      const c = active; c.delta = delta;
      [c.na, c.nb] = pair(c.sa, c.sb, c.ma, c.mb, c.wa, c.wb, delta);
      c.h.a.style.flexGrow = String(c.na); c.h.b.style.flexGrow = String(c.nb);
      position();
    }
    async function finish(cancel) {
      const c = active; if (!c) return;
      active = null; delete document.documentElement.dataset.resizing;
      if (cancel || c.na === undefined || Math.abs(c.na - c.wa) < .000001) {
        c.h.a.style.flexGrow = String(c.wa); c.h.b.style.flexGrow = String(c.wb);
        api.hold(false); layout(); return;
      }
      const command = (n, value) => n.acts.find(a => a.on === "resize").line.replace(/\$value\b/g, () => String(value));
      const n = { ...c.a, fence: { ...c.a.fence, reads: [...(c.a.fence.reads || []), ...(c.b.fence.reads || [])] } };
      // Hold the entire painted tree until the answer; an unrelated turn cannot
      // replace the neighbouring element under a pointer or erase a composer.
      pending = true;
      try { await api.send(n, command(c.a, c.na) + "; " + command(c.b, c.nb)); }
      finally { pending = false; api.hold(false); api.refresh(); }
    }
    function sync() {
      if (active || pending) return;
      handles.forEach(h => h.el.remove()); handles = []; groups = []; observer.disconnect();
      const parents = new Set([...paint.querySelectorAll("[data-key]")].filter(e => e._n?.paint.resize && visible(e)).map(e => e.parentElement));
      for (const el of parents) {
        const axis = el.classList.contains("l-row") ? "x" : el.classList.contains("l-column") ? "y" : null;
        if (!axis) continue;
        const kids = [...el.children].filter(e => e.dataset.key && visible(e));
        const items = kids.filter(e => e._n?.paint.resize && e._n.paint.share > 0);
        if (!items.length) continue;
        const g = { el, axis, items }; groups.push(g);
        el.style.position = "relative"; el.style.flexWrap = "nowrap";
        for (let i = 1; i < kids.length; i++) {
          const a = kids[i - 1], b = kids[i];
          if (!items.includes(a) || !items.includes(b) || a._n.paint.resize[0] !== b._n.paint.resize[0]
              || !samePart(a._n.fence?.defpart, b._n.fence?.defpart)) continue;
          const handle = document.createElement("div"), h = { el: handle, a, b, g };
          handle.className = "l-divider"; handle.dataset.axis = axis; handle.tabIndex = 0;
          handle.setAttribute("role", "separator"); handle.setAttribute("aria-orientation", axis === "x" ? "vertical" : "horizontal");
          handle.setAttribute("aria-label", axis === "x" ? "Resize neighbouring columns" : "Resize neighbouring panels");
          handle.addEventListener("pointerdown", e => {
            if (e.button !== 0 || !begin(h)) return;
            e.preventDefault(); e.stopPropagation(); handle.setPointerCapture(e.pointerId);
            const start = axis === "x" ? e.clientX : e.clientY;
            const moving = m => move((axis === "x" ? m.clientX : m.clientY) - start);
            const done = event => {
              handle.removeEventListener("pointermove", moving); handle.removeEventListener("pointerup", done);
              handle.removeEventListener("pointercancel", done); handle.removeEventListener("lostpointercapture", done);
              finish(event.type !== "pointerup");
            };
            handle.addEventListener("pointermove", moving); handle.addEventListener("pointerup", done);
            handle.addEventListener("pointercancel", done); handle.addEventListener("lostpointercapture", done);
          });
          handle.addEventListener("keydown", e => {
            const d = axis === "x" ? { ArrowLeft: -1, ArrowRight: 1 } : { ArrowUp: -1, ArrowDown: 1 };
            if (d[e.key]) { e.preventDefault(); if (!active && !begin(h)) return; move(active.delta + d[e.key] * (e.shiftKey ? 40 : 8)); }
            else if (e.key === "Enter" || e.key === "Escape") { e.preventDefault(); finish(e.key === "Escape"); }
          });
          handle.addEventListener("blur", () => { if (active?.h === h) finish(true); });
          el.appendChild(handle); handles.push(h);
        }
        observer.observe(el);
      }
      layout();
    }
    const observer = new ResizeObserver(() => { if (active) position(); else layout(); });
    window.addEventListener("resize", () => { if (active) finish(true); layout(); });
    window.addEventListener("blur", () => finish(true));
    document.addEventListener("keydown", e => { if (active && e.key === "Escape") { e.preventDefault(); finish(true); } });
    return { sync, busy: () => !!active || pending };
  }
  const exports = { allocation, pair, samePart, install };
  if (typeof module !== "undefined") module.exports = exports;
  else root.Dividers = exports;
})(typeof window !== "undefined" ? window : globalThis);
