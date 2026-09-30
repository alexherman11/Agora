// apps/notes.js : Notes, a spatial canvas idea space. OWNER: Flint.
//
// Material: the free surface titled "Canvas" and everything on it. Every change is a desk command through
// Desk.do. The app keeps no state the world does not have except declared view state: zoom, pan, which card
// is being edited, a tag filter, and a cache of answers the DESK gave (keyed to the world version).
//
// Round five changes, each answering a measurement rather than a taste:
//   * Iris (a525) measured NINE font sizes in this app, all four of the desktop's fractional ones. There is
//     now not one px in this file. Type and colour come only from Wren's roles and tokens.
//   * 300 cards in a worktree showed the two real limits: reading, not compute (`look f05` printed 28KB with
//     no cut declared), and proximity degenerating into one blob. Both are now declared, not hidden.
//   * A view is a node with a query, so a card can be LIVE. It does not evaluate the query itself — it asks
//     the desk, through the same channel as everything else, and caches the answer against events_total.

(() => {
  const NEAR = 48;              // px (canvas units) under which two cards are "near". Declared in text().
  const ROWS = 40;              // text() stops enumerating past this and says so. My own `bulk` rule, on me.
  const DENSE = 0.5;            // a cluster holding more than this share of the canvas says nothing

  let editing = null;           // drift
  let filter = null;            // stance: mine only
  let ghost = null;             // the command a live gesture would become
  let zoom = 1, panX = 0, panY = 0;   // stance: mine only, never a deed
  let clipState = null;
  const answers = new Map();    // query -> {at: events_total, lines: [...]}  — the DESK's answers, cached

  const R = r => Desk.style ? Desk.style.role(r) : "";
  const V = t => Desk.style ? Desk.style.var(t) : `var(--t-${t})`;

  // Notes was hardcoded to the surface titled "Canvas", which made it one app for one surface. It now
  // renders ANY free surface named in ctx, so the same code is the renderer for any idea space — including
  // one authored from inside the desk. What is still missing is a way for such a surface to get a dock item
  // and a window of its own; that needs the shell's dock to be a view of the world (to-wren, to-jeff).
  let ctxSurface = null;
  const canvas = () => {
    const ns = Object.values(Desk.snapshot.nodes);
    if (ctxSurface) {
      const n = ns.find(x => x.id === ctxSurface || (x.type === "surface" && x.title === ctxSurface));
      if (n && n.layout === "free") return n;
    }
    return ns.find(n => n.type === "surface" && n.layout === "free" && (n.props || {}).app === "notes")
        || ns.find(n => n.type === "surface" && n.title === "Canvas");
  };
  const kids = id => Desk.children(id);
  const cards = id => kids(id).filter(n => n.type === "appearance" || n.layout === "view");
  const groups = id => kids(id).filter(n => n.type === "surface" && n.layout !== "view");
  const esc = s => Shell.esc(s == null ? "" : s);
  const q = s => String(s).replace(/"/g, "'");
  const kindOf = n => n.layout === "view" ? "view" : Desk.subject(n.subject).kind;
  const titleOf = n => n.layout === "view" ? n.title : Desk.subject(n.subject).title;

  const extent = surf => {
    const m = /^(\d+)x(\d+)$/.exec((surf.props || {}).extent || "");
    return m ? { w: +m[1], h: +m[2], declared: true } : { w: surf.w, h: surf.h, declared: false };
  };

  // ---- proximity: my reading of the arrangement, never the world's ------------------------------
  const gap = (a, b) => {
    const dx = Math.max(0, Math.max(a.x - (b.x + b.w), b.x - (a.x + a.w)));
    const dy = Math.max(0, Math.max(a.y - (b.y + b.h), b.y - (a.y + a.h)));
    return Math.round(Math.hypot(dx, dy));
  };
  const overlaps = (a, b) => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
  function clusters(list) {
    const seen = new Set(), out = [];
    list.forEach(n => {
      if (seen.has(n.id)) return;
      const pack = [n]; seen.add(n.id);
      for (let i = 0; i < pack.length; i++)
        list.forEach(m => { if (!seen.has(m.id) && gap(pack[i], m) <= NEAR) { pack.push(m); seen.add(m.id); } });
      out.push(pack);
    });
    return out;
  }
  const hull = p => {
    const x = Math.min(...p.map(n => n.x)), y = Math.min(...p.map(n => n.y));
    return { x, y, w: Math.max(...p.map(n => n.x + n.w)) - x, h: Math.max(...p.map(n => n.y + n.h)) - y };
  };
  // At 300 cards on a 320px pitch everything is within 48px of something, and single-linkage swallows the
  // whole canvas into one pack. A hull round the entire canvas is not a reading, it is a shrug. So a pack
  // that holds more than half of what is shown is reported as a failure of the method, not as a group.
  const readable = (packs, n) => packs.filter(p => p.length > 1 && p.length <= Math.max(2, n * DENSE));
  const degenerate = (packs, n) => packs.filter(p => p.length > 1 && p.length > Math.max(2, n * DENSE));

  // ---- asking the desk (never evaluating its language myself) -----------------------------------
  function ask(query) {
    const now = Desk.snapshot.events_total;
    const hit = answers.get(query);
    if (hit && hit.at === now) return hit;
    if (!hit || hit.at !== now) {
      answers.set(query, { at: hit ? hit.at : -1, lines: hit ? hit.lines : null, pending: true });
      Desk.do(`find ${query}`).then(r => {
        const lines = (r.text || "").split("\n").filter(l => /^\s{4}[af]\d+ /.test(l))
          .map(l => l.trim());
        answers.set(query, { at: now, lines });
        Shell.windows.forEach(w => w.app.id === "notes" && w.app.refresh(w.body, w.ctx));
      }).catch(() => answers.set(query, { at: now, lines: [], failed: true }));
    }
    return answers.get(query);
  }

  // ---- drawing ---------------------------------------------------------------------------------
  function draw(host) {
    const surf = canvas();
    host.className = R("desk");
    host.style.cssText = `position:relative;overflow:auto;height:100%;background:${V("paper")}`;
    host.innerHTML = "";
    if (!surf) {
      const p = document.createElement("p"); p.className = R("body");
      p.textContent = 'no surface titled "Canvas" in this world.'; host.appendChild(p); return;
    }

    const ex = extent(surf);
    const all = cards(surf.id);
    const shown = filter ? all.filter(n => (Desk.subject(n.subject)?.tags || []).includes(filter)) : all;
    const packs = clusters(shown);
    const rings = readable(packs, shown.length);
    const blobs = degenerate(packs, shown.length);

    const bar = document.createElement("div");
    bar.className = R("bar");
    bar.style.cssText = `position:sticky;top:0;z-index:50;display:flex;gap:${V("gap")};align-items:center;flex-wrap:wrap`;
    host.appendChild(bar);

    const scroll = document.createElement("div");
    scroll.style.cssText = `position:relative;width:${Math.round(ex.w * zoom)}px;height:${Math.round(ex.h * zoom)}px`;
    const plane = document.createElement("div");
    plane.style.cssText = `position:absolute;left:0;top:0;width:${ex.w}px;height:${ex.h}px;`
      + `transform:scale(${zoom});transform-origin:0 0`;
    scroll.appendChild(plane); host.appendChild(scroll);

    // cull: only draw what a viewport-sized window could show, and say how many were not drawn
    const vw = host.clientWidth / zoom, vh = host.clientHeight / zoom;
    const view = { x: host.scrollLeft / zoom, y: host.scrollTop / zoom, w: vw || ex.w, h: vh || ex.h };
    const near = n => n.x < view.x + view.w * 2 && n.x + n.w > view.x - view.w
                   && n.y < view.y + view.h * 2 && n.y + n.h > view.y - view.h;
    const drawn = shown.length > 120 ? shown.filter(near) : shown;

    // 1. informal groupings: a hatched FIELD, not a glyph (Iris a447)
    rings.forEach(pack => {
      const h = hull(pack), el = document.createElement("div");
      el.style.cssText = `position:absolute;left:${h.x - 14}px;top:${h.y - 26}px;width:${h.w + 28}px;height:${h.h + 40}px;`
        + `border:2px dashed color-mix(in srgb, ${V("mark")} 75%, transparent);border-radius:${V("gap")};`
        + `background:repeating-linear-gradient(135deg, color-mix(in srgb, ${V("mark")} 16%, transparent) 0 6px, transparent 6px 13px);`
        + `pointer-events:none`;
      const lab = document.createElement("div");
      lab.className = R("meta");
      lab.style.cssText = "position:absolute;left:0;top:0;transform:translateY(-100%);display:flex;gap:6px;align-items:center;pointer-events:auto";
      lab.innerHTML = `<b class="${R('mark')}">~</b> <span>${pack.length} near each other · my reading, not the world's</span>`;
      const name = document.createElement("button");
      name.className = R("tool"); name.textContent = "name this group";
      name.style.cursor = "pointer";
      name.onclick = () => {
        const t = prompt(`Name for these ${pack.length} things.\nThis makes the grouping a fact in the world (= instead of ~).`);
        if (t) Desk.do(`look ${surf.id}; do group ${pack.map(n => n.id).join(",")} as=free title="${q(t)}"`);
      };
      lab.appendChild(name); el.appendChild(lab); plane.appendChild(el);
    });

    // 2. links
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("style", "position:absolute;inset:0;width:100%;height:100%;pointer-events:none;overflow:visible");
    const at = sid => all.find(n => n.subject === sid);
    (Desk.snapshot.links || []).forEach(l => {
      const a = at(l.from), b = at(l.to); if (!a || !b) return;
      const p = document.createElementNS("http://www.w3.org/2000/svg", "path");
      const x1 = a.x + a.w / 2, y1 = a.y + a.h / 2, x2 = b.x + b.w / 2, y2 = b.y + b.h / 2;
      p.setAttribute("d", `M${x1},${y1} C${(x1 + x2) / 2},${y1} ${(x1 + x2) / 2},${y2} ${x2},${y2}`);
      p.setAttribute("fill", "none"); p.setAttribute("stroke", V("quiet"));
      p.setAttribute("stroke-width", "1.5"); p.setAttribute("opacity", ".55");
      svg.appendChild(p);
    });
    plane.appendChild(svg);

    // 3. named groups: facts in the world
    groups(surf.id).forEach(g => {
      const el = document.createElement("div");
      el.className = R("card");
      el.style.cssText = `position:absolute;left:${g.x}px;top:${g.y}px;width:${Math.max(g.w, 160)}px;min-height:${Math.max(g.h, 60)}px`;
      const lab = document.createElement("div"); lab.className = R("meta");
      lab.innerHTML = `<b class="${R('mark')}">=</b> ${esc(g.title)} · ${g.layout} · ${kids(g.id).length} inside`;
      el.appendChild(lab);
      kids(g.id).forEach(c => {
        if (c.type !== "appearance") return;
        const row = document.createElement("div"); row.className = R("body");
        row.textContent = Desk.subject(c.subject).title; el.appendChild(row);
      });
      plane.appendChild(el);
    });

    // 4. the cards
    drawn.forEach(n => plane.appendChild(card(n, surf)));

    plane.ondblclick = e => {
      if (e.target !== plane) return;
      const r = plane.getBoundingClientRect();
      compose(plane, Math.round((e.clientX - r.left) / zoom), Math.round((e.clientY - r.top) / zoom), surf);
    };

    // 5. the bar: counts, zoom, filter, and every cut declared
    const marks = R("mark");   // Wren c547: a mark names a role now; accent is free to mean link/filter/action
    const head = document.createElement("span");
    head.innerHTML = `${all.length} things · ${rings.length} near-groups <b class="${marks}">~</b>`
      + ` · ${groups(surf.id).length} named <b class="${marks}">=</b>`;
    bar.appendChild(head);

    [["−", -1], ["＋", 1]].forEach(([g, d]) => {
      const b = document.createElement("button"); b.className = R("tool"); b.textContent = g;
      b.style.cursor = "pointer";
      b.onclick = () => { zoom = Math.min(2, Math.max(.25, +(zoom * (d > 0 ? 1.25 : .8)).toFixed(2))); draw(host); };
      bar.appendChild(b);
    });
    const zl = document.createElement("span"); zl.className = R("meta");
    zl.textContent = `${Math.round(zoom * 100)}%`; bar.appendChild(zl);

    const tags = [...new Set(all.flatMap(n => Desk.subject(n.subject)?.tags || []))].sort().slice(0, 12);
    tags.forEach(t => {
      const b = document.createElement("button");
      b.className = R(filter === t ? "tool.on" : "tool"); b.textContent = "#" + t;
      b.style.cursor = "pointer";
      b.onclick = () => { filter = filter === t ? null : t; draw(host); };
      bar.appendChild(b);
    });
    if (filter) {
      const s = document.createElement("span"); s.className = R("meta");
      s.innerHTML = `<b class="${marks}">!</b> showing #${esc(filter)} only — yours, not a change to the world`;
      bar.appendChild(s);
    }
    if (drawn.length < shown.length) {
      const s = document.createElement("span"); s.className = R("cut");
      s.innerHTML = `<b class="${marks}">!</b> ${shown.length - drawn.length} card(s) not drawn (too far from the viewport)`;
      bar.appendChild(s);
    }
    blobs.forEach(p => {
      const s = document.createElement("span"); s.className = R("cut");
      s.innerHTML = `<b class="${marks}">~</b> proximity says nothing here: ${p.length} of ${shown.length} form one cluster at ${NEAR}px`;
      bar.appendChild(s);
    });

    const clip = document.createElement("span"); clip.className = R("meta");
    clip.style.cssText = "padding:0 6px;border-radius:4px;background:repeating-linear-gradient(135deg,"
      + `color-mix(in srgb, ${V("mark")} 16%, transparent) 0 5px, transparent 5px 11px)`;
    bar.appendChild(clip);
    const measure = () => {
      const w = host.clientWidth / zoom, h = host.clientHeight / zoom;
      const out = all.filter(n => n.x + n.w > host.scrollLeft / zoom + w || n.y + n.h > host.scrollTop / zoom + h
        || n.x < host.scrollLeft / zoom || n.y < host.scrollTop / zoom);
      const pct = Math.round(100 * Math.min(1, (w * h) / (ex.w * ex.h)));
      clip.innerHTML = `<b class="${marks}">!</b> you see ${pct}% of the ${ex.w}×${ex.h} canvas`
        + (out.length ? ` · ${out.length} card(s) outside the window` : "");
      clipState = { pct, out: out.map(n => n.id), vw: Math.round(w), vh: Math.round(h) };
    };
    host.onscroll = () => { measure(); if (shown.length > 120) draw(host); };
    requestAnimationFrame(measure);

    const g = document.createElement("span"); g.id = "notes-ghost"; g.className = R("source");
    g.style.marginLeft = "auto"; g.textContent = ghost ? ghost.line : "";
    bar.appendChild(g);
  }

  const say = line => { ghost = line ? { line } : null;
    const g = document.getElementById("notes-ghost"); if (g) g.textContent = line || ""; };

  // ---- one card --------------------------------------------------------------------------------
  function card(n, surf) {
    const kind = kindOf(n);
    const el = document.createElement("article");
    el.className = R("card");
    el.style.cssText = `position:absolute;left:${n.x}px;top:${n.y}px;width:${Math.max(n.w, 160)}px;`
      + `min-height:${Math.max(n.h, 80)}px;display:flex;flex-direction:column;gap:4px`;

    const title = document.createElement("div");
    title.className = R("title"); title.textContent = titleOf(n);

    // ---- a LIVE card: a view node. It does not evaluate the desk's language; it asks the desk. ----
    if (kind === "view") {
      el.appendChild(title);
      const src = document.createElement("div"); src.className = R("source");
      src.textContent = `of ${n.query}`; el.appendChild(src);
      const a = ask(n.query);
      if (!a || !a.lines) {
        const p = document.createElement("div"); p.className = R("meta");
        p.textContent = "asking the desk…"; el.appendChild(p);
      } else {
        a.lines.slice(0, 8).forEach(l => {
          const row = document.createElement("div"); row.className = R("body"); row.textContent = l; el.appendChild(row);
        });
        const f = document.createElement("div");
        f.className = a.lines.length > 8 ? R("cut") : R("meta");
        f.textContent = a.lines.length > 8
          ? `! ${a.lines.length - 8} more matches not shown · find ${n.query}`
          : `${a.lines.length} match(es), live from the desk`;
        el.appendChild(f);
      }
      moveable(el, n, surf);
      return el;
    }

    const s = Desk.subject(n.subject);
    field(title, n, "title", v => `do retitle ${n.id} title="${q(v)}"`, () => s.title);
    el.appendChild(title);

    // ---- a card that is a RUNNING RULE: prop rule=rN, drawn live from the snapshot ----
    const ruleId = (s.props || {}).rule;
    if (ruleId) {
      const rule = (Desk.snapshot.rules || []).find(r => r.id === ruleId);
      const src = document.createElement("div"); src.className = R("source");
      src.textContent = rule ? `rule ${rule.id} ${rule.text}` : `rule ${ruleId}`;
      el.appendChild(src);
      const m = document.createElement("div");
      m.className = rule ? R("meta") : R("cut");
      m.innerHTML = rule
        ? `fired ${rule.fired}× · live from the desk`
        : `<b class="${R('mark')}">!</b> no rule ${esc(ruleId)} in this world any more`;
      el.appendChild(m);
    } else if (kind === "image") {
      const p = document.createElement("div"); p.className = R("cut");
      p.innerHTML = `<b class="${R('mark')}">?</b> kind=image carries a title and nothing else in this desk — there is no picture to draw`;
      el.appendChild(p);
    } else {
      const body = document.createElement("div");
      body.className = R("body");
      body.style.cssText = "white-space:pre-wrap;flex:1";
      body.textContent = s.text || "";
      field(body, n, "text", v => `do rewrite ${n.id} text="${q(v)}"`, () => s.text || "");
      el.appendChild(body);
    }

    const foot = document.createElement("div");
    foot.className = R("meta");
    foot.style.cssText = "display:flex;gap:4px;align-items:center;flex-wrap:wrap";
    (s.tags || []).forEach(t => {
      const c = document.createElement("span"); c.className = R("tag"); c.textContent = "#" + t; foot.appendChild(c);
    });
    const add = document.createElement("button");
    add.className = R("tool"); add.textContent = "+tag"; add.style.cursor = "pointer";
    add.onclick = ev => { ev.stopPropagation();
      const t = prompt("tag"); if (t) Desk.do(`look ${n.id}; do tag ${n.id} add=${q(t).replace(/\s+/g, "-")}`); };
    foot.appendChild(add);
    if (kind === "doc" && /^##/m.test(s.text || "")) {
      const d = document.createElement("span");
      d.textContent = `· ${(s.text.match(/^##/gm) || []).length} sections`; foot.appendChild(d);
    }
    if ((s.comments || []).length) {
      const c = document.createElement("span"); c.textContent = `· ${s.comments.length} comment(s)`; foot.appendChild(c);
    }
    const ex2 = extent(surf);
    if (n.x + n.w > ex2.w || n.y + n.h > ex2.h) {
      const w = document.createElement("span"); w.className = R("cut");
      w.innerHTML = `<b class="${R('mark')}">!</b> past the canvas extent`; foot.appendChild(w);
    }
    el.appendChild(foot);

    const dot = document.createElement("button");
    dot.className = R("tool"); dot.title = "drag to another card to link them";
    dot.style.cssText = `position:absolute;right:-5px;top:50%;width:11px;height:11px;margin-top:-5px;padding:0;`
      + `border-radius:50%;border:1px solid ${V("line")};background:${V("card")};cursor:crosshair`;
    dot.onmousedown = ev => { ev.stopPropagation(); linkDrag(n, el.parentElement, surf); };
    el.appendChild(dot);

    const grip = document.createElement("div");
    grip.title = "resize";
    grip.style.cssText = "position:absolute;right:2px;bottom:2px;width:12px;height:12px;cursor:nwse-resize;opacity:.5";
    grip.innerHTML = `<svg width="12" height="12"><path d="M11 3 L3 11 M11 7 L7 11" stroke="${V("quiet")}" fill="none"/></svg>`;
    grip.onmousedown = ev => { ev.stopPropagation(); resizeDrag(ev, n, el); };
    el.appendChild(grip);

    moveable(el, n, surf);
    return el;
  }
  const moveable = (el, n, surf) => {
    el.onmousedown = ev => {
      if (editing || ev.target.closest("[contenteditable=true],button")) return;
      moveDrag(ev, n, el, surf);
    };
  };

  // ---- in-place editing: drift until it settles -------------------------------------------------
  function field(el, n, name, cmd, original) {
    el.onclick = ev => {
      if (editing) return;
      ev.stopPropagation();
      editing = { id: n.id, field: name };
      el.contentEditable = "true"; el.focus();
      el.style.boxShadow = `inset 0 -1px 0 ${V("accent")}`;
      say(`(unsettled — ${name} of ${n.id}. blur or ⌘⏎ settles, esc abandons)`);
      const settle = async () => {
        el.contentEditable = "false"; el.style.boxShadow = ""; editing = null;
        const v = el.textContent.trim();
        if (v === original()) { say(""); return; }
        say(""); await Desk.do(`look ${n.id}; ${cmd(v)}`);
      };
      el.onblur = settle;
      el.onkeydown = k => {
        if (k.key === "Escape") { k.preventDefault(); el.textContent = original(); el.onblur = null; settle(); }
        if (k.key === "Enter" && (k.metaKey || k.ctrlKey || name === "title")) { k.preventDefault(); el.blur(); }
      };
    };
  }

  // ---- gestures: live line is drift, release is the deed ----------------------------------------
  function moveDrag(ev, n, el, surf) {
    const ox = ev.clientX / zoom - n.x, oy = ev.clientY / zoom - n.y;
    let x = n.x, y = n.y;
    const move = m => {
      x = Math.max(0, Math.round(m.clientX / zoom - ox)); y = Math.max(0, Math.round(m.clientY / zoom - oy));
      el.style.left = x + "px"; el.style.top = y + "px";
      say(`release now: do move ${n.id} to=${x},${y}`);
    };
    const up = () => {
      removeEventListener("mousemove", move); removeEventListener("mouseup", up); say("");
      if (x !== n.x || y !== n.y) Desk.do(`look ${surf.id}; do move ${n.id} to=${x},${y}`);
    };
    addEventListener("mousemove", move); addEventListener("mouseup", up);
  }
  function resizeDrag(ev, n, el) {
    const sx = ev.clientX, sy = ev.clientY; let w = n.w, h = n.h;
    const move = m => {
      w = Math.max(160, Math.round(n.w + (m.clientX - sx) / zoom));
      h = Math.max(80, Math.round(n.h + (m.clientY - sy) / zoom));
      el.style.width = w + "px"; el.style.minHeight = h + "px";
      say(`release now: do resize ${n.id} to=${w}x${h}`);
    };
    const up = () => {
      removeEventListener("mousemove", move); removeEventListener("mouseup", up); say("");
      if (w !== n.w || h !== n.h) Desk.do(`look ${n.id}; do resize ${n.id} to=${w}x${h}`);
    };
    addEventListener("mousemove", move); addEventListener("mouseup", up);
  }
  function linkDrag(n, plane, surf) {
    const svg = plane.querySelector("svg");
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("stroke", V("quiet")); line.setAttribute("stroke-dasharray", "4 3");
    line.setAttribute("x1", n.x + n.w); line.setAttribute("y1", n.y + n.h / 2);
    svg.appendChild(line);
    const r = plane.getBoundingClientRect();
    const pt = m => ({ x: (m.clientX - r.left) / zoom, y: (m.clientY - r.top) / zoom });
    const hit = m => { const p = pt(m); const s = canvas(); return s && cards(s.id)
      .find(c => p.x >= c.x && p.x <= c.x + c.w && p.y >= c.y && p.y <= c.y + c.h); };
    const move = m => {
      const p = pt(m); line.setAttribute("x2", p.x); line.setAttribute("y2", p.y);
      const t = hit(m);
      say(t && t.id !== n.id ? `release now: do link ${n.id} ${t.id} as=refers`
        : "(drop on another card to link; nothing lands otherwise)");
    };
    const up = m => {
      removeEventListener("mousemove", move); removeEventListener("mouseup", up); line.remove(); say("");
      const t = hit(m);
      if (t && t.id !== n.id) Desk.do(`look ${n.id}; do link ${n.id} ${t.id} as=refers`);
    };
    addEventListener("mousemove", move); addEventListener("mouseup", up);
  }

  // ---- create in place --------------------------------------------------------------------------
  function compose(plane, x, y, surf) {
    const box = document.createElement("div");
    box.className = R("card");
    box.style.cssText = `position:absolute;left:${x}px;top:${y}px;width:220px;min-height:80px;border-style:dashed;border-width:2px`;
    const inp = document.createElement("div");
    inp.contentEditable = "true"; inp.className = R("title");
    inp.style.cssText = "outline:0;min-height:18px";
    const hint = document.createElement("div"); hint.className = R("meta");
    hint.textContent = "⏎ makes it · esc abandons (nothing is sent)";
    box.append(inp, hint); plane.appendChild(box); inp.focus();
    say(`(unsettled — a new note at ${x},${y}. nothing exists yet)`);
    const done = async commit => {
      const t = inp.textContent.trim(); box.remove(); say("");
      if (!commit || !t) return;
      await Desk.do(`look ${surf.id}; do create ${surf.id} kind=note title="${q(t)}"; do move $new to=${x},${y}`);
    };
    inp.onkeydown = k => {
      if (k.key === "Enter") { k.preventDefault(); done(true); }
      if (k.key === "Escape") { k.preventDefault(); done(false); }
    };
    inp.onblur = () => done(true);
  }

  // ---- what a text-only inhabitant reads --------------------------------------------------------
  function text() {
    const surf = canvas();
    if (!surf) return 'Notes: no surface titled "Canvas" in this world.';
    const ex = extent(surf), all = cards(surf.id), gs = groups(surf.id);
    const shown = filter ? all.filter(n => (Desk.subject(n.subject)?.tags || []).includes(filter)) : all;
    const packs = clusters(shown), rings = readable(packs, shown.length), blobs = degenerate(packs, shown.length);
    const L = [], pad = (s, n) => String(s).padEnd(n);

    L.push(`Notes · ${surf.title} (${surf.id}) · free · ${all.length} things, ${gs.length} named group(s)`);
    L.push(`  this window renders ${surf.id} because ` + (ctxSurface ? `it was opened on "${ctxSurface}"`
      : (surf.props || {}).app === "notes" ? `${surf.id} carries prop app=notes`
      : `nothing named a surface and it is the one titled "Canvas"`) + `.`);
    L.push(`= tile the desk enforces: ${surf.w}x${surf.h} at ${surf.x},${surf.y} in ${surf.parent}`);
    L.push(ex.declared
      ? `= extent (prop on ${surf.id}, a world fact): ${ex.w}x${ex.h} — the idea space Notes draws`
      : `! no extent prop on ${surf.id}; Notes falls back to the tile (${surf.w}x${surf.h}), too small for a canvas`);
    if (ex.declared) L.push(`  ! the desk still reports spills-parent past the TILE and export carries the desk's word, not mine.`);
    L.push(`! zoom ${Math.round(zoom * 100)}% — stance, mine only, never a deed. The other inhabitant is unaffected.`);
    L.push("");

    L.push(`= on the canvas${all.length > ROWS ? ` (first ${ROWS} of ${all.length}, in z order)` : ""}`);
    all.slice(0, ROWS).forEach(n => {
      const kind = kindOf(n);
      if (kind === "view") {
        const a = answers.get(n.query);
        L.push(`  ${pad(n.id, 6)} ${pad("view", 5)} ${pad('"' + n.title + '"', 34)} at ${pad(n.x + "," + n.y, 11)} ${n.w}x${n.h}`
          + `  of ${n.query}  ${a && a.lines ? `= ${a.lines.length} match(es), asked at events_total=${a.at}` : "~ not asked yet"}`);
        return;
      }
      const s = Desk.subject(n.subject);
      const over = all.filter(m => m !== n && overlaps(m, n));
      const touch = all.filter(m => m !== n && !overlaps(m, n) && gap(m, n) === 0);
      L.push(`  ${pad(n.id, 6)} ${pad(kind, 5)} ${pad('"' + s.title + '"', 34)} at ${pad(n.x + "," + n.y, 11)} ${n.w}x${n.h}`
        + ((s.tags || []).length ? `  #${s.tags.join(" #")}` : "")
        + ((s.props || {}).rule ? `  = running rule ${s.props.rule}` : "")
        + (kind === "image" ? `  ? no picture: kind=image carries only a title in this desk` : "")
        + (n.x + n.w > ex.w || n.y + n.h > ex.h ? `  ! past the extent` : "")
        + (over.length ? `  ~ overlaps ${over.slice(0, 4).map(o => o.id).join(", ")}${over.length > 4 ? ` +${over.length - 4}` : ""} (mine: a rectangle test; the desk measures % properly)` : "")
        + (touch.length ? `  · touches ${touch.slice(0, 4).map(o => o.id).join(", ")}` : "")
        + (shown.includes(n) ? "" : `  ! filtered out — in the world, NOT on his screen`));
      const first = (s.text || "").split("\n")[0];
      if (first) L.push(`         ${first.slice(0, 90)}${first.length > 90 ? " …" : ""}`);
    });
    if (all.length > ROWS)
      L.push(`  ! ${all.length - ROWS} more not listed. This app stops at ${ROWS} on purpose: a list of ${all.length} is not a reading.`
        + `\n    ask for them the way the desk asks: find in:${surf.id}  ·  table in:${surf.id} cols=tags  ·  find in:${surf.id},tag:<word>`);
    L.push("");

    if (gs.length) {
      L.push("= named groups (facts in the world, made by someone on purpose)");
      gs.forEach(g => {
        L.push(`  ${g.id} "${g.title}" ${g.layout} · ${kids(g.id).length} inside · at ${g.x},${g.y}`);
        kids(g.id).forEach(c => c.type === "appearance"
          && L.push(`        ${c.id} "${Desk.subject(c.subject).title}"`));
      });
      L.push("");
    }

    L.push(`~ near each other — MY READING, not the world's. Nobody said these belong together.`);
    L.push(`  method: rectangles whose gap is <= ${NEAR}px, joined transitively, over the ${shown.length} thing(s) ON SCREEN.`);
    blobs.forEach(p => {
      L.push(`  ! THE METHOD FAILS HERE: ${p.length} of ${shown.length} join into one cluster.`);
      L.push(`    At this density everything is near everything, so nearness carries no information and I draw nothing.`);
      L.push(`    Proximity is a reading for a sparse canvas. Spread things out, or group them on purpose.`);
    });
    if (!rings.length && !blobs.length) L.push("  nothing is near anything else.");
    rings.forEach((p, i) => {
      const h = hull(p);
      L.push(`  ${String.fromCharCode(65 + i)}: ${p.map(n => n.id).join(", ")}  (${p.length} things, bbox ${h.x},${h.y} ${h.w}x${h.h})`);
      L.push(`     if this is real: do group ${p.map(n => n.id).join(",")} as=free title="..."`);
    });
    L.push("");

    const links = (Desk.snapshot.links || []).filter(l => all.some(n => n.subject === l.from) && all.some(n => n.subject === l.to));
    L.push(`= links · ${links.length}`);
    links.slice(0, 20).forEach(l => {
      const a = all.find(n => n.subject === l.from), b = all.find(n => n.subject === l.to);
      L.push(`  ${a.id} -> ${b.id}  ${l.kind}   ("${Desk.title(a.id)}" -> "${Desk.title(b.id)}")`);
    });
    if (links.length > 20) L.push(`  ! ${links.length - 20} more not listed.`);
    L.push("");

    if (clipState) {
      L.push(`! the window shows ${clipState.pct}% of the ${ex.w}x${ex.h} canvas (viewport ${clipState.vw}x${clipState.vh} in canvas units at ${Math.round(zoom * 100)}% zoom).`);
      if (clipState.out.length <= 12 && clipState.out.length)
        L.push(`  outside his window right now: ${clipState.out.join(", ")} — present, scrollable to, not seen.`);
      else if (clipState.out.length)
        L.push(`  ${clipState.out.length} cards are outside his window right now — present, scrollable to, not seen.`);
      if (shown.length > 120) L.push(`  ! past 120 cards Notes only DRAWS what is near the viewport. The world holds all ${all.length}.`);
      L.push("");
    }

    L.push("= what this window offers a hand (and the command each one is)");
    L.push(`  double-click empty canvas   ->  do create ${surf.id} kind=note title="..."; do move $new to=x,y`);
    L.push(`  click a title or a body     ->  do retitle <id> title="..."  /  do rewrite <id> text="..."`);
    L.push(`  drag a card / its corner    ->  do move <id> to=x,y   /   do resize <id> to=WxH`);
    L.push(`  drag the dot on a card      ->  do link <a> <b> as=refers      (there is no unlink; filed to-jeff)`);
    L.push(`  +tag on a card              ->  do tag <id> add=<word>`);
    L.push(`  'name this group' on a ~    ->  do group <ids> as=free title="..."   — the one that turns ~ into =`);
    L.push(`  a tag chip, the zoom buttons   stance. mine only. no command, no event.`);
    L.push("");

    const sizes = [...new Set(all.map(n => `${n.w}x${n.h}`))];
    if (all.length > 1 && sizes.length === 1)
      L.push(`~ every card is ${sizes[0]}. Nobody has resized anything, so size carries no information here yet — only position does.`);
    L.push("");
    L.push("? what I cannot tell you");
    L.push("  whether the arrangement means anything to the person who made it. Proximity is evidence, not intent.");
    L.push("  how any of this looks: type, weight, colour, whether two cards read as one block.");
    L.push("  how much of a covered card is hidden. The desk knows (\"52% hidden by f30\"); I only have a rectangle test.");
    L.push("  what an image is. kind=image has a title and no data, so no picture exists to describe or to fail to describe.");
    L.push("  whether anyone is looking at this canvas right now, or where. The desk still has no presence.");
    return L.join("\n");
  }

  Desk.registerApp({
    id: "notes", title: "Notes", glyph: "◇",
    open: (host, ctx) => { ctxSurface = (ctx && (ctx.surface || ctx.id)) || null; draw(host); },
    refresh: (host, ctx) => { if (ctx && (ctx.surface || ctx.id)) ctxSurface = ctx.surface || ctx.id;
                              if (!editing) draw(host); },
    text,
  });
})();
