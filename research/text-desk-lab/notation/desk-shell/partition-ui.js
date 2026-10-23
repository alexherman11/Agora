// Pointer/keyboard adapter for Partition's pure world-tree/geometry operations.
(function (host) {
  "use strict";
  function install(paint, api, P = host.Partition) {
    let groups = [], active = null, pending = false, armed = false, controlCleanup = null;
    const px = n => n + "px";
    const rect = el => ({ x: 0, y: 0, w: el.clientWidth, h: el.clientHeight });
    const pagePoint = (g, e) => { const r = g.el.getBoundingClientRect(); return {
      x: e.clientX - r.left - (g.el.clientLeft || 0), y: e.clientY - r.top - (g.el.clientTop || 0) }; };
    function measure(el, width, minimum) {
      // Measure the existing content synchronously, restoring every inline style
      // before a frame. No cloned app/frame loads, detached editors, focus or keys.
      const touched = [el, ...el.querySelectorAll("[data-share]")];
      const fields = ["flex", "width", "height", "minWidth", "minHeight", "maxWidth", "maxHeight"];
      const saved = touched.map(e => fields.map(f => e.style[f])), display = el.style.display;
      el.style.display = "";
      touched.forEach(e => { e.style.flex = "0 0 auto"; e.style.height = "auto"; e.style.minHeight = "0"; });
      Object.assign(el.style, { width: "max-content", maxWidth: px(width), height: "max-content", maxHeight: "none" });
      let size;
      try {
        const b = el.getBoundingClientRect();
        size = [Math.max(minimum[0], Math.min(width, b.width)), Math.max(minimum[1], b.height)];
      } finally {
        touched.forEach((e, i) => fields.forEach((f, j) => { e.style[f] = saved[i][j] || ""; }));
        el.style.display = display;
      }
      return size;
    }
    const controlIn = (target, grip) => {
      for (let n = target; n && n !== grip; n = n.parentElement) {
        if (n.isContentEditable || /^(BUTTON|INPUT|TEXTAREA|SELECT|A)$/.test(n.tagName) ||
            n._clicks || n.dataset?.tool || n.matches?.('[role="button"],[role="link"],.t-mark-link,.t-mark-thing')) return n;
      }
      return grip.isContentEditable ? grip : null;
    };
    function suppressReleaseClick(control = null) {
      const eat = e => {
        if (control && !control.contains(e.target)) return;
        e.preventDefault(); e.stopPropagation();
      };
      window.addEventListener("click", eat, true);
      setTimeout(() => window.removeEventListener("click", eat, true), 0);
    }
    function controlPress(control, e) {
      // An authored action inside a grip is clickable, not selectable/draggable
      // page text. Editors and native input selection never enter this path.
      e.preventDefault();
      controlCleanup?.(true);
      const x = e.clientX, y = e.clientY, pid = e.pointerId;
      let moved = false, cancelled = false;
      const move = m => {
        if (m.pointerId !== pid) return;
        if (Math.hypot(m.clientX - x, m.clientY - y) >= 5) moved = true;
        if (moved) m.preventDefault();
      };
      const clear = () => {
        document.removeEventListener("pointermove", move);
        document.removeEventListener("pointerup", up);
        document.removeEventListener("pointercancel", up);
        controlCleanup = null;
      };
      const up = m => {
        if (m.pointerId !== pid) return;
        // Release may arrive without the final move, or after moving back.
        move(m);
        if (moved || cancelled || m.type === "pointercancel") suppressReleaseClick(control);
        clear();
      };
      // Retain cancellation through the actual release (which can be much
      // later than Escape/blur). A subsequent press retires the old listener.
      controlCleanup = retire => { cancelled = true; if (retire) clear(); };
      document.addEventListener("pointermove", move);
      document.addEventListener("pointerup", up);
      document.addEventListener("pointercancel", up);
    }
    function projected(g, tree = g.tree, focus = g.focus) {
      let root = P.project(tree.root, g.visible);
      const hidden = [];
      if (focus && g.visible.has(focus)) {
        const selected = [focus, ...[...g.visible].filter(id => id !== focus && g.members.get(id)._n.paint.companion)];
        hidden.push(...[...g.visible].filter(id => !selected.includes(id)));
        root = selected.length === 1 ? { id: focus } : {
          axis: "x", kids: selected.map(id => ({ id })), weights: selected.map(id => {
            const saved = tree.focus_weights?.[focus]?.[id];
            return Number.isFinite(saved) && saved > 0 ? saved : id === focus ? 13 : 6;
          })
        };
      }
      const bounds = rect(g.el), rail = hidden.length ? Math.min(120, bounds.w / 5) : 0;
      const room = { ...bounds, x: rail, w: bounds.w - rail };
      return { ...P.geometry(root, room, { ...g.options, visible: undefined }), hidden, rail, room, root };
    }
    function place(el, b) {
      Object.assign(el.style, { position: "absolute", boxSizing: "border-box", margin: "0",
        minWidth: "0", minHeight: "0", maxWidth: "none", maxHeight: "none",
        left: px(b.x), top: px(b.y), width: px(b.w), height: px(b.h) });
    }
    function button(g, label, tip, run, box) {
      const b = document.createElement("button");
      b.type = "button"; b.textContent = label; b.title = tip; b.className = "partition-tool";
      b.setAttribute("aria-label", tip);
      // Do not steal the caret from a draft in a sibling panel.
      b.addEventListener("pointerdown", e => e.preventDefault());
      b.addEventListener("click", e => { e.stopPropagation(); run(); });
      place(b, box); g.el.appendChild(b); g.chrome.push(b); return b;
    }
    function label(g, id) {
      const e = g.members.get(id);
      return e._n.paint.tip?.[0] || e.querySelector("[data-carry]")?.textContent?.trim() || "Panel";
    }
    function render(g, tree = g.tree, focus = g.focus, tools = true) {
      if (tools) { g.chrome.forEach(e => e.remove()); g.chrome = []; }
      const geo = projected(g, tree, focus); g.geometry = geo;
      for (const [id, e] of g.members) {
        const b = geo.boxes[id]; e.style.display = b && g.visible.has(id) ? "" : "none";
        if (b) place(e, b);
      }
      if (!tools) return;
      for (const t of geo.tabs) {
        const members = P.ids(t.node), width = t.box.w / members.length;
        members.forEach((id, i) => button(g, label(g, id), "Show " + label(g, id), () => {
          commit(g, { ...g.tree, root: P.activate(g.tree.root, id) }, g.focus);
        }, { ...t.box, x: t.box.x + width * i, w: width }));
      }
      const railHeight = Math.min(32, g.el.clientHeight / Math.max(1, geo.hidden.length));
      geo.hidden.forEach((id, i) => button(g, label(g, id), "Fill with " + label(g, id),
        () => focusOn(g, id), { x: 0, y: i * railHeight, w: geo.rail, h: railHeight }));
      for (const [id, box] of Object.entries(geo.boxes)) {
        const current = (function find(n) { return n.id ? n.id === id ? n : null : n.kids.map(find).find(Boolean); })(g.tree.root);
        if (!focus && current?.size === "content") for (const axis of ["x","y"]) {
          const h=document.createElement("div"), x=axis==="x";
          h.className="l-divider";h.dataset.axis=axis;h.tabIndex=0;
          h.setAttribute("role","separator");h.setAttribute("aria-orientation",x?"vertical":"horizontal");
          h.setAttribute("aria-label",x?"Resize content width":"Resize content height");
          place(h,x?{x:box.x+box.w-6,y:box.y,w:12,h:box.h}:{x:box.x,y:box.y+box.h-6,w:box.w,h:12});
          const begin=()=>{
            if(active||armed||pending||api.busy())return false;
            active={g,kind:"content",next:null,delta:0};api.hold(true);return true;
          };
          const change=delta=>{
            active.delta=delta;
            const extent=[box.w,box.h],i=x?0:1;
            extent[i]=Math.max(g.options.minimum[i],extent[i]+delta);
            const root=P.replace(g.tree.root,id,n=>({...n,size:"content",extent}));
            active.next={...g.tree,root};render(g,active.next,focus,false);
          };
          h.addEventListener("pointerdown",e=>{
            if(e.button!==0||!begin())return;e.preventDefault();e.stopPropagation();
            const start=x?e.clientX:e.clientY;
            listen(e.pointerId,m=>change((x?m.clientX:m.clientY)-start),cancel=>finish(cancel));
          });
          h.addEventListener("keydown",e=>{
            const step=x?{ArrowLeft:-8,ArrowRight:8}:{ArrowUp:-8,ArrowDown:8};
            if(step[e.key]){e.preventDefault();if(!active&&!begin())return;change(active.delta+step[e.key]);}
            else if(["Enter","Escape"].includes(e.key)&&active){e.preventDefault();finish(e.key==="Escape");}
          });
          g.el.appendChild(h);g.chrome.push(h);
        }
        if (g.members.get(id)._n.paint.chrome === "none") continue;
        button(g, current?.size === "content" ? "↔" : "Fit", current?.size === "content" ? "Fill allocated space" : "Fit content", () => {
          const next = { ...g.tree, root: P.replace(g.tree.root, id, n => {
            const { extent, ...rest } = n;
            return { ...rest, size: n.size === "content" ? "stretch" : "content" };
          }) };
          commit(g, next, g.focus);
        }, { x: box.x + Math.max(0, box.w - 36), y: box.y + Math.max(0, box.h - 22), w: Math.min(36, box.w), h: Math.min(22, box.h) });
      }
      for (const s of geo.splits) for (let i = 0; i < s.children.length - 1; i++) {
        const a = s.children[i], b = s.children[i + 1], x = s.node.axis === "x";
        const h = document.createElement("div");
        h.className = "l-divider"; h.dataset.axis = s.node.axis; h.tabIndex = 0;
        h.setAttribute("role", "separator"); h.setAttribute("aria-orientation", x ? "vertical" : "horizontal");
        h.setAttribute("aria-label", x ? "Resize neighbouring columns" : "Resize neighbouring panels");
        place(h, x ? { x: (a.x + a.w + b.x) / 2 - 6, y: a.y, w: 12, h: a.h }
          : { x: a.x, y: (a.y + a.h + b.y) / 2 - 6, w: a.w, h: 12 });
        const begin = () => {
          if (active || armed || pending || api.busy()) return false;
          active = { g, kind: "resize", base: g.focus ? { v: 1, root: geo.root } : g.tree, path: s.path, index: i, delta: 0, next: null };
          api.hold(true); return true;
        };
        const change = delta => {
          if (!active || active.g !== g) return;
          active.delta = delta;
          let next = P.resize(active.base, s.path, i, delta, geo.room,
            g.focus ? { ...g.options, visible: undefined } : g.options);
          if (g.focus) {
            const weights = Object.fromEntries(next.root.kids.map((k, j) => [k.id, next.root.weights[j]]));
            next = { ...g.tree, focus_weights: { ...g.tree.focus_weights, [g.focus]: weights } };
          }
          active.next = next; render(g, next, g.focus, false);
        };
        h.addEventListener("pointerdown", e => {
          if (e.button !== 0 || !begin()) return;
          e.preventDefault(); e.stopPropagation();
          const start = x ? e.clientX : e.clientY, pid = e.pointerId;
          listen(pid, m => change((x ? m.clientX : m.clientY) - start), cancel => finish(cancel));
        });
        h.addEventListener("keydown", e => {
          const step = x ? { ArrowLeft: -8, ArrowRight: 8 } : { ArrowUp: -8, ArrowDown: 8 };
          if (step[e.key]) { e.preventDefault(); if (!active && !begin()) return; change(active.delta + step[e.key] * (e.shiftKey ? 5 : 1)); }
          else if (["Enter", "Escape"].includes(e.key) && active) { e.preventDefault(); finish(e.key === "Escape"); }
        });
        g.el.appendChild(h); g.chrome.push(h);
      }
    }
    async function focusOn(g, id) {
      if (active || armed || pending || api.busy()) return;
      const a = g.el._n.acts.find(a => a.on === "partition-focus");
      if (a) await api.send(g.el._n, a.line.replace(/\$value\b/g, () => id));
    }
    async function commit(g, tree, focus, restore) {
      if (active || armed || pending || api.busy()) return;
      pending = true; api.hold(true);
      try { await api.send(g.el._n, P.command(g.el._n, tree, focus)); }
      finally {
        pending = false; api.hold(false);
        if (restore) { try { await api.refresh(); } finally { restore(); } }
        else api.refresh();
      }
    }
    function continuity(g) {
      // Scroll offsets do not require intrinsic measurements. Keep the actual
      // editors, never a cloned/replaced app, and restore after authoritative
      // refresh as well as cancellation. Viewer owns continuity across repaints.
      const elements = [...g.members.values()].flatMap(el => [el, ...el.querySelectorAll("*")]);
      const scroll = elements.map(el => [el, el.scrollLeft, el.scrollTop]);
      const focused = document.activeElement;
      return () => {
        // Reflow may hide the focused tab and send focus to body. Recover that
        // loss, but never override an intentional move to another editor.
        // Retained editors own their current caret, including typing during a
        // delayed send; replaying a pickup-time range would lose that progress.
        if (focused?.isConnected && focused.getClientRects().length && elements.includes(focused) &&
            (!document.activeElement || document.activeElement === document.body || document.activeElement === focused)) {
          if (document.activeElement !== focused) focused.focus?.({ preventScroll: true });
        }
        for (const [el, x, y] of scroll) if (el.isConnected) {
          if (x !== undefined) el.scrollLeft = x;
          if (y !== undefined) el.scrollTop = y;
        }
      };
    }
    function showCandidate(a, plan) {
      const next = plan?.tree || null;
      a.preview.hidden = !plan;
      a.preview.title = plan?.fallback === "tabs" ? "Not enough room for a split; previewing tabs" : "";
      if (plan?.box) place(a.preview, plan.box);
      // No work for a stationary snapped target: geometry changes only when
      // the candidate changes, not for every ghost position.
      const key = next ? JSON.stringify(next) : "";
      if (key === a.previewKey) return;
      a.previewKey = key; a.next = next;
      a.g.chrome.forEach(e => e.remove()); a.g.chrome = [];
      render(a.g, next || a.g.tree, next ? "" : a.g.focus, false);
    }
    function listen(pid, moving, done) {
      const move = e => { if (e.pointerId === pid) moving(e); };
      const up = e => {
        if (e.pointerId !== pid) return;
        document.removeEventListener("pointermove", move); document.removeEventListener("pointerup", up);
        document.removeEventListener("pointercancel", up); activeCleanup = null;
        done(e.type === "pointercancel");
      };
      document.addEventListener("pointermove", move); document.addEventListener("pointerup", up); document.addEventListener("pointercancel", up);
      activeCleanup = () => {
        document.removeEventListener("pointermove", move); document.removeEventListener("pointerup", up);
        document.removeEventListener("pointercancel", up); activeCleanup = null;
      };
    }
    let activeCleanup = null;
    function finish(cancel) {
      const a = active; if (!a) return;
      activeCleanup?.(); active = null;
      a.ghost?.remove(); a.preview?.remove();
      if (cancel) a.external?.cancel();
      if (a.whole) a.whole.style.opacity = "";
      a.restoreSelection?.();
      if (a.kind === "carry") {
        // Suppress only the synthetic release-click following a real drag.
        suppressReleaseClick();
      }
      delete document.documentElement.dataset.resizing;
      api.hold(false);
      if (!cancel && a.external?.target) {
        pending = true;
        a.external.release().finally(() => { pending = false; api.refresh(); });
        render(a.g); a.restore?.();
      } else if (!cancel && a.next) {
        a.external?.cancel();
        const focus = a.kind === "carry" ? "" : a.g.focus;
        // Keep the exact released preview until the fenced answer arrives.
        // A refusal/lost answer refreshes from the world, retaining drafts.
        // The old tools belong to g.tree, not this preview. Remove them now:
        // otherwise an invisible old divider can intercept the next title press.
        a.g.chrome.forEach(e => e.remove()); a.g.chrome = [];
        render(a.g, a.next, focus, false);
        commit(a.g, a.next, focus, a.restore);
      } else { a.external?.cancel(); render(a.g); a.restore?.(); api.refresh(); }
    }
    function carry(grip, e) {
      const g = groups.find(g => g.el.contains(grip));
      if (!g) return false;
      const whole = [...g.members.values()].find(el => el.contains(grip));
      if (!whole || grip._n.fence?.item !== whole._n.paint.partition_item) return false;
      // Owning the gesture includes declined/interactive presses: the legacy
      // carry adapter must never also start a second drag on this tree.
      if (e.button !== 0) return true;
      controlCleanup?.(true);
      const control = controlIn(e.target, grip);
      if (control) {
        if (!control.isContentEditable && !/^(INPUT|TEXTAREA|SELECT)$/.test(control.tagName)) controlPress(control, e);
        return true;
      }
      // Own the initial press, including passive descendants in nested lenses.
      // Waiting for threshold leaves Chromium free to start native selection or
      // a selected-text drag before our first move. This cancels neither click
      // handlers nor any existing page/editor range, and preserves draft focus.
      e.preventDefault();
      if (active || armed || pending || api.busy()) {
        // This title gesture is owned but cannot start against an unanswered
        // tree. Cancel the pointer's default too: merely declining it lets
        // Chromium select text and turn the next press into a native text drag.
        // No selection policy/ranges or app-control input are changed here.
        return true;
      }
      const id = whole._n.paint.partition_item, start = { x: e.clientX, y: e.clientY };
      let taken = false; armed = true;
      listen(e.pointerId, m => {
        if (!taken) {
          if (Math.hypot(m.clientX - start.x, m.clientY - start.y) < 5) return;
          if (!whole.isConnected || !groups.includes(g)) { activeCleanup?.(); armed = false; return; }
          taken = true; armed = false; api.hold(true);
          const ghost = whole.cloneNode(true), box = whole.getBoundingClientRect();
          ghost.removeAttribute("id"); ghost.removeAttribute("data-key");
          ghost.querySelectorAll("[id],[data-key]").forEach(el => { el.removeAttribute("id"); el.removeAttribute("data-key"); });
          ghost.querySelectorAll("iframe,video,audio").forEach(el => el.remove());
          Object.assign(ghost.style, { position: "fixed", left: px(box.left), top: px(box.top), width: px(box.width), height: px(box.height),
            pointerEvents: "none", zIndex: "40", opacity: ".85", animation: "none", transition: "none" });
          document.body.appendChild(ghost); whole.style.opacity = ".35";
          const preview = document.createElement("div"); preview.className = "landing-box"; g.el.appendChild(preview);
          active = { kind: "carry", g, ghost, preview, whole, next: null, previewKey: "",
            bounds: rect(g.el), boxes: g.geometry.boxes, restore: g.magnetic ? continuity(g) : null, snap: null,
            external: host.CarryTargets?.session(paint, { el: grip, n: grip._n }, api.send, g.el) };
          // Only a threshold drag changes selection policy; clicks and app
          // controls retain their normal focus/caret behavior.
          const userSelect = document.body.style.userSelect;
          document.body.style.userSelect = "none";
          window.getSelection()?.removeAllRanges();
          active.restoreSelection = () => { document.body.style.userSelect = userSelect; };
        }
        if (!active) return;
        m.preventDefault();
        active.ghost.style.transform = `translate(${m.clientX - start.x}px,${m.clientY - start.y}px)`;
        if (active.external?.move(m)) {
          if (g.magnetic) { active.snap = null; showCandidate(active, null); }
          else { active.next = null; active.preview.hidden = true; }
          return;
        }
        if (!g.magnetic) {
          const target = P.hit(rect(g.el), g.geometry.boxes, pagePoint(g, m), id);
          const p = P.plan(g.tree, id, target, rect(g.el), g.options);
          active.next = p?.tree; active.preview.hidden = !p;
          if (p?.box) place(active.preview, p.box);
          return;
        }
        const prior = active.snap;
        const snap = P.magneticHit(active.bounds, active.boxes, pagePoint(g, m), id, prior);
        if (snap === active.snap) return;
        active.snap = snap;
        if (prior && snap && JSON.stringify(prior.target) === JSON.stringify(snap.target)) return;
        showCandidate(active, P.previewPlan(g.tree, id, snap?.target, active.bounds, g.options));
      }, cancel => { armed = false; if (taken) finish(cancel); });
      return true;
    }
    function key(grip, e) {
      const g = groups.find(g => g.el.contains(grip));
      if (!g) return false;
      const whole = [...g.members.values()].find(el => el.contains(grip));
      if (!whole || grip._n.fence?.item !== whole._n.paint.partition_item) return false;
      if (e.target !== grip) return true;
      if (e.key === " " && !active && !armed && !pending && !api.busy()) {
        e.preventDefault(); api.hold(true);
        const preview = document.createElement("div"); preview.className = "landing-box"; g.el.appendChild(preview);
        active = { g, kind: "carry", whole, id: whole._n.paint.partition_item, preview, next: null,
          previewKey: "", restore: g.magnetic ? continuity(g) : null };
      } else if (active?.g === g && active.kind === "carry") {
        const side = { ArrowLeft: "left", ArrowRight: "right", ArrowUp: "top", ArrowDown: "bottom" }[e.key];
        if (side) {
          e.preventDefault();
          const plan = (g.magnetic ? P.previewPlan : P.plan)(g.tree, active.id, { global: true, side }, rect(g.el), g.options);
          if (g.magnetic) showCandidate(active, plan);
          else { active.next = plan?.tree; if (plan?.box) place(active.preview, plan.box); }
        } else if (e.key === "Enter") { e.preventDefault(); finish(false); }
      }
      return true;
    }
    function sync() {
      if (active || pending) return;
      groups.forEach(g => g.chrome.forEach(e => e.remove())); groups = []; observer.disconnect();
      for (const el of paint.querySelectorAll("[data-key]")) {
        const spec = el._n?.paint.partition;
        if (!spec || el.hidden || !el.getClientRects().length) continue;
        // Establish the same bounded formatting context before measurement and
        // on every authoritative sync, independent of focus/rail contents.
        el.style.contain = "size layout";
        const members = new Map([...el.children].filter(e => e._n?.paint.partition_item).map(e => [e._n.paint.partition_item, e]));
        const visible = new Set([...members].filter(([, e]) => !e.hidden && !e._n.paint.absent).map(([id]) => id));
        const preferences = Object.fromEntries([...members].map(([id,e]) => [id,e._n.paint.sizing]));
        const tree = P.model(spec.tree, [...members.keys()], preferences), content = new Set();
        (function visit(n) { if (!n) return; if (n.id) { if (n.size === "content") content.add(n.id); }
          else n.kids.forEach(visit); })(tree.root);
        const intrinsic = Object.fromEntries([...members].filter(([id]) => content.has(id)).map(([id, e]) =>
          [id, measure(e, el.clientWidth, spec.minimum)]));
        const g = { el, members, visible, tree, focus: spec.focus || "", magnetic: spec.magnetic === true, chrome: [],
          options: { minimum: spec.minimum, gap: spec.gap, intrinsic } };
        g.options.visible = visible;
        el.dataset.partition = "1"; el.style.position = "relative"; el.style.display = "block"; el.style.padding = "0"; el.style.gap = "0";
        groups.push(g); render(g); observer.observe(el);
      }
    }
    const observer = new ResizeObserver(() => { if (!active && !pending) groups.forEach(g => render(g)); });
    window.addEventListener("resize", () => { controlCleanup?.(); if (armed) { activeCleanup?.(); armed = false; } if (active) finish(true); });
    window.addEventListener("blur", () => { controlCleanup?.(); activeCleanup?.(); armed = false; if (active) finish(true); });
    document.addEventListener("keydown", e => {
      if (e.key === "Escape" && controlCleanup) { e.preventDefault(); controlCleanup(); }
      if (e.key === "Escape" && (active || armed)) { e.preventDefault(); activeCleanup?.(); armed = false; finish(true); }
    });
    return { sync, carry, key, busy: () => !!active || armed || pending };
  }
  if (typeof module !== "undefined") module.exports = { install };
  else host.PartitionUI = { install };
})(typeof window !== "undefined" ? window : globalThis);
