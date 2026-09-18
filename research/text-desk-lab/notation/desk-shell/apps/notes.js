// apps/notes.js : Notes, a spatial canvas idea space. OWNER: Flint.
//
// Material: the free surface titled "Canvas" and the appearances on it. Nothing is kept here that the world
// does not have, except three honest pieces of view state: which card is being edited, the live drag offset,
// and a per-actor tag filter (stance: mine, durable to me, never a deed).
//
// The two registers, visible everywhere:
//   drift  — a drag in progress, an unsettled edit. Shown, never sent, never in history.
//   deed   — what the release or the settle becomes, always an ordinary desk command through Desk.do.
// Every gesture shows the command it is about to become BEFORE it lands ("release now: ..."), so the
// interface teaches the language instead of hiding it.
//
// Colours come from Wren's tokens only (--paper --surface --ink --quiet --line --accent). Where a tint is
// needed it is derived with color-mix from a token, never invented. Requested of Wren: a --mark token for
// honesty marks, and --dash for informal borders (to-wren posted).

(() => {
  const NEAR = 48;              // px gap under which two cards are "near each other". Declared in text().
  const MINW = 160, MINH = 90;

  let editing = null;           // {id, field} — drift
  let filter = null;            // tag filter — stance, mine only
  let ghost = null;             // {line} — the command a live gesture would become
  let clipState = null;         // what the window actually shows of the canvas — view state, reported honestly

  const canvas = () => Object.values(Desk.snapshot.nodes)
    .find(n => n.type === "surface" && n.title === "Canvas");

  // The Canvas tile is whatever the parent column gives it (400x380 today), which is not an idea space.
  // Until the desk can carry a free surface's own extent (to-jeff #1), Notes reads an `extent` PROP off the
  // surface — a real world fact, set with `do prop f05 extent=1600x1200`, visible to everyone, in export.
  // The desk still measures spills-parent against the tile, so the two disagree; text() says so out loud.
  const extent = surf => {
    const m = /^(\d+)x(\d+)$/.exec((surf.props || {}).extent || "");
    return m ? { w: +m[1], h: +m[2], declared: true } : { w: surf.w, h: surf.h, declared: false };
  };
  const cards = id => Desk.children(id).filter(n => n.type === "appearance");
  const groups = id => Desk.children(id).filter(n => n.type === "surface");
  const esc = s => Shell.esc(s == null ? "" : s);
  const q = s => String(s).replace(/"/g, "'");

  // ---- proximity: my reading of the arrangement, never the world's ------------------------------
  const gap = (a, b) => {
    const dx = Math.max(0, Math.max(a.x - (b.x + b.w), b.x - (a.x + a.w)));
    const dy = Math.max(0, Math.max(a.y - (b.y + b.h), b.y - (a.y + a.h)));
    return Math.round(Math.hypot(dx, dy));
  };
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
  // gap()===0 means TOUCHING, which is not overlapping. Conflating them put "! overlaps a09" on two cards
  // that merely share an edge — a false statement in text(), which is the one thing this app may not do.
  const overlaps = (a, b) =>
    a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
  const hull = pack => {
    const x = Math.min(...pack.map(n => n.x)), y = Math.min(...pack.map(n => n.y));
    return { x, y, w: Math.max(...pack.map(n => n.x + n.w)) - x, h: Math.max(...pack.map(n => n.y + n.h)) - y };
  };

  // ---- drawing ---------------------------------------------------------------------------------
  function draw(host) {
    const surf = canvas();
    host.style.cssText = "position:relative;background:var(--paper);min-height:100%;overflow:auto";
    host.innerHTML = "";
    if (!surf) { host.innerHTML = `<p style="padding:24px;color:var(--quiet)">no surface titled "Canvas" in this world.</p>`; return; }

    const all = cards(surf.id);
    const shown = filter ? all.filter(n => (Desk.subject(n.subject).tags || []).includes(filter)) : all;
    const packs = clusters(shown).filter(p => p.length > 1);

    const ex = extent(surf);
    const plane = document.createElement("div");
    plane.style.cssText = `position:relative;width:${ex.w}px;height:${ex.h}px`;
    host.appendChild(plane);

    // 1. informal clusters, behind everything. Dashed = inferred, not in the world.
    packs.forEach((pack, i) => {
      const h = hull(pack), el = document.createElement("div");
      // Iris measured (c429) that a dashed --line border is 1.25:1 against its fill and does not render as
      // dashes at all. The informal signal must be one the eye gets before it reads, so: a visible dashed
      // rule derived from --quiet (which has contrast), plus a tint, plus the mark itself.
      // Iris, a447: "an honesty mark has to be a property of the surface, not a character in the text,
      // because a character can always be made quiet and a surface cannot." Four of us drew our marks as
      // glyphs and all four came out too quiet. So the informal grouping is a HATCHED FIELD — understood
      // before it is read — and the ~ glyph only names what the texture already said.
      el.style.cssText = `position:absolute;left:${h.x - 14}px;top:${h.y - 22}px;width:${h.w + 28}px;height:${h.h + 36}px;
        border:1.5px dashed color-mix(in srgb, var(--quiet) 55%, transparent);border-radius:14px;
        background:repeating-linear-gradient(135deg,
          color-mix(in srgb, var(--quiet) 11%, transparent) 0 6px,
          transparent 6px 13px);pointer-events:none`;
      const tag = document.createElement("div");
      tag.style.cssText = `position:absolute;left:0;top:-2px;transform:translateY(-100%);display:flex;gap:6px;
        align-items:center;font-size:12px;color:var(--quiet);pointer-events:auto`;
      tag.innerHTML = `<b style="color:var(--accent);font:700 14px/1 var(--font)">~</b>
        <span>${pack.length} near each other · my reading, not the world's</span>`;
      const name = document.createElement("button");
      name.textContent = "name this group";
      name.style.cssText = `border:0;background:transparent;color:var(--quiet);font:inherit;font-size:12px;
        text-decoration:underline;cursor:pointer;padding:0`;
      name.onclick = () => {
        const t = prompt(`Name for these ${pack.length} things.\nThis makes the grouping a fact in the world (= instead of ~).`);
        if (t) Desk.do(`look ${surf.id}; do group ${pack.map(n => n.id).join(",")} as=free title="${q(t)}"`);
      };
      tag.appendChild(name); el.style.pointerEvents = "none"; tag.style.pointerEvents = "auto";
      el.appendChild(tag); plane.appendChild(el);
    });

    // 2. links, under the cards
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("style", "position:absolute;inset:0;width:100%;height:100%;pointer-events:none;overflow:visible");
    const at = sid => all.find(n => n.subject === sid);
    (Desk.snapshot.links || []).forEach(l => {
      const a = at(l.from), b = at(l.to); if (!a || !b) return;
      const p = document.createElementNS("http://www.w3.org/2000/svg", "path");
      const x1 = a.x + a.w / 2, y1 = a.y + a.h / 2, x2 = b.x + b.w / 2, y2 = b.y + b.h / 2;
      p.setAttribute("d", `M${x1},${y1} C${(x1 + x2) / 2},${y1} ${(x1 + x2) / 2},${y2} ${x2},${y2}`);
      p.setAttribute("fill", "none"); p.setAttribute("stroke", "var(--quiet)");
      p.setAttribute("stroke-width", "1.25"); p.setAttribute("opacity", ".5");
      svg.appendChild(p);
    });
    plane.appendChild(svg);

    // 3. named groups (real surfaces in the world): solid border, and honest about what grouping cost
    groups(surf.id).forEach(g => {
      const el = document.createElement("div");
      el.style.cssText = `position:absolute;left:${g.x}px;top:${g.y}px;width:${Math.max(g.w, MINW)}px;
        min-height:${Math.max(g.h, 60)}px;border:1px solid var(--line);border-radius:12px;background:var(--surface);
        padding:24px 10px 10px`;
      const lab = document.createElement("div");
      lab.style.cssText = "position:absolute;left:10px;top:6px;font-size:11px;color:var(--quiet)";
      lab.innerHTML = `<b style="color:var(--accent);font:700 14px/1 var(--font)">=</b> ${esc(g.title)} · ${g.layout}`
        + (g.layout !== "free" ? ` <span title="the desk's group verb made a column; the canvas positions of these things were lost">· <b style="color:var(--accent);font:700 14px/1 var(--font)">!</b> positions lost</span>` : "");
      el.appendChild(lab);
      Desk.children(g.id).forEach(c => {
        if (c.type !== "appearance") return;
        const s = Desk.subject(c.subject), row = document.createElement("div");
        row.style.cssText = "font-size:12.5px;padding:3px 0;color:var(--ink)";
        row.textContent = s.title; el.appendChild(row);
      });
      plane.appendChild(el);
    });

    // 4. the cards
    shown.forEach(n => plane.appendChild(card(n, surf)));

    // 5. create in place
    plane.ondblclick = e => {
      if (e.target !== plane) return;
      const r = plane.getBoundingClientRect();
      compose(plane, Math.round(e.clientX - r.left), Math.round(e.clientY - r.top), surf);
    };

    // 6. the quiet bar: filter (stance) and what the canvas reads as
    const bar = document.createElement("div");
    bar.style.cssText = `position:sticky;top:0;z-index:50;display:flex;gap:10px;align-items:center;flex-wrap:wrap;
      padding:7px 12px;background:color-mix(in srgb, var(--surface) 88%, transparent);
      border-bottom:1px solid var(--line);font-size:11.5px;color:var(--quiet);backdrop-filter:blur(6px)`;
    const tags = [...new Set(all.flatMap(n => Desk.subject(n.subject).tags || []))].sort();
    const M = 'color:var(--accent);font:700 14px/1 var(--font)';
    bar.innerHTML = `<span>${all.length} things · ${packs.length} near-groups <b style="${M}">~</b>`
      + ` · ${groups(surf.id).length} named <b style="${M}">=</b></span>`;
    tags.forEach(t => {
      const b = document.createElement("button");
      b.textContent = "#" + t;
      b.style.cssText = `border:1px solid var(--line);border-radius:999px;padding:1px 9px;cursor:pointer;font:inherit;
        background:${filter === t ? "var(--ink)" : "transparent"};color:${filter === t ? "var(--surface)" : "var(--quiet)"}`;
      b.onclick = () => { filter = filter === t ? null : t; draw(host); };
      bar.appendChild(b);
    });
    if (filter) {
      const s = document.createElement("span");
      s.innerHTML = `<b style="${M}">!</b> showing #${esc(filter)} only — yours, not a change to the world`;
      bar.appendChild(s);
    }
    // clipped-unsaid (Iris, a483): the plane is larger than the window body and nothing said so.
    const clip = document.createElement("span");
    clip.id = "notes-clip";
    clip.style.cssText = "display:inline-flex;gap:5px;align-items:center;padding:0 7px;border-radius:4px;"
      + "background:repeating-linear-gradient(135deg, color-mix(in srgb, var(--quiet) 13%, transparent) 0 5px, transparent 5px 11px)";
    bar.appendChild(clip);
    const measure = () => {
      const vw = host.clientWidth, vh = host.clientHeight;
      const out = all.filter(n => n.x + n.w > host.scrollLeft + vw || n.y + n.h > host.scrollTop + vh
        || n.x < host.scrollLeft || n.y < host.scrollTop);
      const pct = Math.round(100 * Math.min(1, (vw * vh) / (ex.w * ex.h)));
      clip.innerHTML = `<b style="color:var(--accent);font:700 14px/1 var(--font)">!</b>`
        + `<span>you see ${pct}% of the ${ex.w}x${ex.h} canvas` + (out.length ? ` · ${out.length} card(s) outside the window` : "") + `</span>`;
      clipState = { pct, out: out.map(n => n.id), vw, vh };
    };
    host.onscroll = measure;
    requestAnimationFrame(measure);

    const g = document.createElement("span");
    g.id = "notes-ghost"; g.style.cssText = "margin-left:auto;font:11.5px ui-monospace,Consolas,monospace;color:var(--ink)";
    g.textContent = ghost ? ghost.line : "";
    bar.appendChild(g);
    host.insertBefore(bar, plane);
  }

  const say = line => { ghost = line ? { line } : null;
    const g = document.getElementById("notes-ghost"); if (g) g.textContent = line || ""; };

  // ---- one card --------------------------------------------------------------------------------
  function card(n, surf) {
    const s = Desk.subject(n.subject);
    const el = document.createElement("article");
    const ex = extent(surf);
    const spills = n.x + n.w > ex.w || n.y + n.h > ex.h;
    const pastTile = !spills && (n.x + n.w > surf.w || n.y + n.h > surf.h);
    el.style.cssText = `position:absolute;left:${n.x}px;top:${n.y}px;width:${Math.max(n.w, MINW)}px;
      min-height:${Math.max(n.h, MINH)}px;background:var(--surface);border:1px solid var(--line);
      border-radius:var(--radius);padding:10px 12px 8px;box-shadow:0 1px 2px rgba(36,35,31,.05);
      display:flex;flex-direction:column;gap:5px`;

    const title = document.createElement("div");
    title.style.cssText = "font-weight:500;font-size:13.5px;line-height:1.35;outline:0";
    title.textContent = s.title;
    field(title, n, "title", v => `do retitle ${n.id} title="${q(v)}"`, () => s.title);

    const body = document.createElement("div");
    body.style.cssText = "font-size:12.5px;color:var(--quiet);line-height:1.45;white-space:pre-wrap;flex:1;outline:0";
    body.textContent = s.text || "";
    body.dataset.placeholder = "";
    field(body, n, "text", v => `do rewrite ${n.id} text="${q(v)}"`, () => s.text || "");

    el.append(title, body);

    const foot = document.createElement("div");
    foot.style.cssText = "display:flex;gap:5px;align-items:center;flex-wrap:wrap;font-size:10.5px;color:var(--quiet)";
    (s.tags || []).forEach(t => {
      const c = document.createElement("span");
      c.textContent = "#" + t;
      c.style.cssText = "border:1px solid var(--line);border-radius:999px;padding:0 6px";
      foot.appendChild(c);
    });
    const add = document.createElement("button");
    add.textContent = "+tag"; add.title = "do tag " + n.id + " add=...";
    add.style.cssText = "border:0;background:transparent;color:var(--quiet);cursor:pointer;font:inherit;padding:0 2px";
    add.onclick = ev => { ev.stopPropagation();
      const t = prompt("tag"); if (t) Desk.do(`look ${n.id}; do tag ${n.id} add=${q(t).replace(/\s+/g, "-")}`); };
    foot.appendChild(add);
    if (spills || pastTile) {
      const w = document.createElement("span");
      w.innerHTML = spills
        ? `<b style="color:var(--accent);font:700 13px/1 var(--font)">!</b> past the canvas extent`
        : `<b style="color:var(--accent);font:700 13px/1 var(--font)">!</b> the desk calls this spills-parent`;
      w.title = spills ? "" : "outside the 400x380 tile the desk enforces, inside the extent Notes honours";
      foot.appendChild(w);
    }
    if ((s.comments || []).length) foot.append(` · ${s.comments.length} comment${s.comments.length > 1 ? "s" : ""}`);
    el.appendChild(foot);

    // link handle
    const dot = document.createElement("button");
    dot.title = "drag to another card to link them";
    dot.style.cssText = `position:absolute;right:-5px;top:50%;width:10px;height:10px;margin-top:-5px;padding:0;
      border-radius:50%;border:1px solid var(--line);background:var(--surface);cursor:crosshair`;
    dot.onmousedown = ev => { ev.stopPropagation(); linkDrag(n, el.parentElement, surf); };
    el.appendChild(dot);

    // resize handle
    const grip = document.createElement("div");
    grip.title = "resize";
    grip.style.cssText = "position:absolute;right:2px;bottom:2px;width:12px;height:12px;cursor:nwse-resize;opacity:.45";
    grip.innerHTML = `<svg width="12" height="12"><path d="M11 3 L3 11 M11 7 L7 11" stroke="var(--quiet)" fill="none"/></svg>`;
    grip.onmousedown = ev => { ev.stopPropagation(); resizeDrag(ev, n, el); };
    el.appendChild(grip);

    el.onmousedown = ev => {
      if (editing || ev.target.closest("[contenteditable=true],button")) return;
      moveDrag(ev, n, el, surf);
    };
    return el;
  }

  // ---- in-place editing: drift until it settles -------------------------------------------------
  function field(el, n, name, cmd, original) {
    el.onclick = ev => {
      if (editing) return;
      ev.stopPropagation();
      editing = { id: n.id, field: name };
      el.contentEditable = "true"; el.focus();
      el.style.boxShadow = "inset 0 -1px 0 var(--accent)";
      say(`(unsettled — ${name} of ${n.id}. blur or ⌘⏎ settles, esc abandons)`);
      const settle = async () => {
        el.contentEditable = "false"; el.style.boxShadow = ""; editing = null;
        const v = el.textContent.trim();
        if (v === original()) { say(""); return; }
        say("");
        await Desk.do(`look ${n.id}; ${cmd(v)}`);
      };
      el.onblur = settle;
      el.onkeydown = k => {
        if (k.key === "Escape") { k.preventDefault(); el.textContent = original(); el.onblur = null; settle(); }
        if (k.key === "Enter" && (k.metaKey || k.ctrlKey)) { k.preventDefault(); el.blur(); }
        if (k.key === "Enter" && name === "title") { k.preventDefault(); el.blur(); }
      };
    };
  }

  // ---- gestures: the live line is drift, the release is the deed --------------------------------
  function moveDrag(ev, n, el, surf) {
    const ox = ev.clientX - n.x, oy = ev.clientY - n.y;
    let x = n.x, y = n.y;
    el.style.cursor = "grabbing";
    const move = m => {
      x = Math.max(0, Math.round(m.clientX - ox)); y = Math.max(0, Math.round(m.clientY - oy));
      el.style.left = x + "px"; el.style.top = y + "px";
      say(`release now: do move ${n.id} to=${x},${y}`);
    };
    const up = () => {
      removeEventListener("mousemove", move); removeEventListener("mouseup", up);
      el.style.cursor = ""; say("");
      if (x !== n.x || y !== n.y) Desk.do(`look ${surf.id}; do move ${n.id} to=${x},${y}`);
    };
    addEventListener("mousemove", move); addEventListener("mouseup", up);
  }

  function resizeDrag(ev, n, el) {
    const sx = ev.clientX, sy = ev.clientY; let w = n.w, h = n.h;
    const move = m => {
      w = Math.max(MINW, Math.round(n.w + m.clientX - sx)); h = Math.max(MINH, Math.round(n.h + m.clientY - sy));
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
    line.setAttribute("stroke", "var(--quiet)"); line.setAttribute("stroke-dasharray", "4 3");
    line.setAttribute("x1", n.x + n.w); line.setAttribute("y1", n.y + n.h / 2);
    svg.appendChild(line);
    const r = plane.getBoundingClientRect();
    const move = m => {
      line.setAttribute("x2", m.clientX - r.left); line.setAttribute("y2", m.clientY - r.top);
      const t = target(m, plane);
      say(t ? `release now: do link ${n.id} ${t.id} as=refers` : "(drop on another card to link; nothing lands otherwise)");
    };
    const up = m => {
      removeEventListener("mousemove", move); removeEventListener("mouseup", up);
      line.remove(); say("");
      const t = target(m, plane);
      if (t && t.id !== n.id) Desk.do(`look ${n.id}; do link ${n.id} ${t.id} as=refers`);
    };
    addEventListener("mousemove", move); addEventListener("mouseup", up);
  }
  function target(m, plane) {
    const r = plane.getBoundingClientRect(), x = m.clientX - r.left, y = m.clientY - r.top;
    const surf = canvas(); if (!surf) return null;
    return cards(surf.id).find(c => x >= c.x && x <= c.x + c.w && y >= c.y && y <= c.y + c.h);
  }

  // ---- create in place: a draft that is nothing until it settles ---------------------------------
  function compose(plane, x, y, surf) {
    const box = document.createElement("div");
    box.style.cssText = `position:absolute;left:${x}px;top:${y}px;width:${MINW + 40}px;min-height:${MINH}px;
      background:var(--surface);border:1.5px dashed var(--accent);border-radius:var(--radius);padding:10px 12px`;
    const inp = document.createElement("div");
    inp.contentEditable = "true";
    inp.style.cssText = "font-weight:500;font-size:13.5px;outline:0;min-height:18px";
    box.appendChild(inp);
    const hint = document.createElement("div");
    hint.style.cssText = "font-size:10.5px;color:var(--quiet);margin-top:6px";
    hint.textContent = "⏎ makes it · esc abandons (nothing is sent)";
    box.appendChild(hint);
    plane.appendChild(box); inp.focus();
    say(`(unsettled — a new note at ${x},${y}. nothing exists yet)`);
    const done = async commit => {
      const t = inp.textContent.trim(); box.remove(); say("");
      if (!commit || !t) return;
      await Desk.do(`look ${surf.id}; do create ${surf.id} kind=note title="${q(t)}"; do move $item to=${x},${y}`);
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
    if (!surf) return "Notes: no surface titled \"Canvas\" in this world.";
    const all = cards(surf.id), gs = groups(surf.id);
    const shown = filter ? all.filter(n => (Desk.subject(n.subject).tags || []).includes(filter)) : all;
    // Lark's audit (a457 #2): draw() clustered `shown`, text() clustered `all`, so with a filter on the two
    // sides asserted different groups. text() describes THIS window, and this window is filtered, so both
    // now cluster the same set and the method line says which set that is.
    const packs = clusters(shown).filter(p => p.length > 1);
    const L = [];
    const pad = (s, n) => String(s).padEnd(n);

    const ex = extent(surf);
    L.push(`Notes · ${surf.title} (${surf.id}) · free · ${all.length} things, ${gs.length} named group(s)`);
    L.push(`= tile the desk enforces: ${surf.w}x${surf.h} at ${surf.x},${surf.y} in ${surf.parent}`);
    L.push(ex.declared
      ? `= extent (prop on ${surf.id}, a world fact): ${ex.w}x${ex.h} — this is the idea space Notes draws`
      : `! no extent prop on ${surf.id}; Notes falls back to the tile, which is ${surf.w}x${surf.h} and too small for a canvas`);
    if (ex.declared) L.push(`  ! the desk still reports spills-parent for anything past the TILE, and export carries the desk's word, not mine. Until to-jeff #1 lands these two disagree; believe the desk.`);
    L.push(`read at ${Desk.snapshot.clock?.today || "no clock"} · everything below marked = is a world fact, ~ is my reading, ? is what I cannot tell you`);
    L.push("");

    L.push("= on the canvas");
    all.forEach(n => {
      const s = Desk.subject(n.subject);
      const over = all.filter(m => m !== n && overlaps(m, n));
      const touch = all.filter(m => m !== n && !overlaps(m, n) && gap(m, n) === 0);
      L.push(`  ${pad(n.id, 5)} ${pad(s.kind, 5)} ${pad('"' + s.title + '"', 38)} at ${pad(n.x + "," + n.y, 10)} ${n.w}x${n.h}`
        + ((s.tags || []).length ? "  #" + s.tags.join(" #") : "")
        + (n.x + n.w > ex.w || n.y + n.h > ex.h ? `  ! past the extent (${ex.w}x${ex.h})`
           : (n.x + n.w > surf.w || n.y + n.h > surf.h) ? `  · outside the desk's tile (the desk says spills-parent)` : "")
        + (over.length ? `  ~ overlaps ${over.map(o => o.id).join(", ")} (mine: a rectangle test. the desk measures this properly — \`look ${surf.id}\` gives "N% hidden by")` : "")
        + (touch.length ? `  · touches ${touch.map(o => o.id).join(", ")}` : "")
        + ((s.comments || []).length ? `  · ${s.comments.length} comment(s), ${(s.comments || []).filter(c => !c.resolved).length} open` : "")
        + (shown.includes(n) ? "" : `  ! filtered out — in the world, NOT on his screen`));
      const first = (s.text || "").split("\n")[0];
      if (first) L.push(`        ${first.slice(0, 92)}${first.length > 92 ? " …" : ""}`);
    });
    if (!all.length) L.push("  (empty)");
    L.push("");

    if (gs.length) {
      L.push("= named groups (facts in the world, made by someone on purpose)");
      gs.forEach(g => {
        L.push(`  ${g.id} "${g.title}" ${g.layout} · ${Desk.children(g.id).length} inside · at ${g.x},${g.y}`);
        Desk.children(g.id).forEach(c => {
          if (c.type !== "appearance") return;
          L.push(`        ${c.id} "${Desk.subject(c.subject).title}"`);
        });
        if (g.layout !== "free")
          L.push(`        ! the desk's group verb made a column; these things' canvas positions were lost (filed to-jeff)`);
      });
      L.push("");
    }

    L.push(`~ near each other — MY READING, not the world's. Nobody said these belong together.`);
    L.push(`  method: rectangles whose gap is <= ${NEAR}px, joined transitively. Recomputed at every look.`);
    L.push(`  computed from the ${shown.length} thing(s) ON SCREEN${filter ? ` (your #${filter} filter hides ${all.length - shown.length})` : ""}, so this matches what is drawn.`);
    if (!packs.length) L.push("  nothing is near anything else.");
    packs.forEach((p, i) => {
      const h = hull(p), pairs = [];
      p.forEach((a, j) => p.slice(j + 1).forEach(b => { const d = gap(a, b); if (d <= NEAR) pairs.push(`${a.id}~${b.id} ${d}px`); }));
      L.push(`  ${String.fromCharCode(65 + i)}: ${p.map(n => n.id).join(", ")}  (${p.length} things, bbox ${h.x},${h.y} ${h.w}x${h.h})`);
      L.push(`     ${pairs.join(" · ")}`);
      L.push(`     if this is real: do group ${p.map(n => n.id).join(",")} as=free title="..."`);
    });
    L.push("");

    const links = (Desk.snapshot.links || []).filter(l => all.some(n => n.subject === l.from) && all.some(n => n.subject === l.to));
    L.push("= links");
    if (!links.length) L.push("  none on this canvas.");
    links.forEach(l => {
      const a = all.find(n => n.subject === l.from), b = all.find(n => n.subject === l.to);
      L.push(`  ${a.id} -> ${b.id}  ${l.kind}   ("${Desk.title(a.id)}" -> "${Desk.title(b.id)}")`);
    });
    L.push("");

    if (filter) {
      L.push(`! you are looking through a filter: #${filter} · ${shown.length} of ${all.length} shown`);
      L.push(`  this is stance — mine, not a change to the world. The other inhabitant sees all ${all.length}.`);
      L.push("");
    }
    if (editing) {
      L.push(`! something is unsettled: the ${editing.field} of ${editing.id} is being edited and has not landed.`);
      L.push(`  the value above is the last settled one. No event exists yet.`);
      L.push("");
    }

    if (clipState) {
      L.push(`! the window shows ${clipState.pct}% of the ${ex.w}x${ex.h} canvas (viewport ${clipState.vw}x${clipState.vh}).`);
      if (clipState.out.length)
        L.push(`  outside his window right now: ${clipState.out.join(", ")} — present, scrollable to, not seen.`);
      L.push("");
    }
    // Iris, c496: the one word on screen that text() never said was "name" — from a control, not content.
    // text() was complete about the world and silent about what the screen offers a hand. Both inhabitants
    // need the same list of what can be done here, in the form each of them would use it.
    L.push("= what this window offers a hand (and the command each one is)");
    L.push("  double-click empty canvas   a draft appears; nothing exists until Enter  ->  do create " + surf.id + " kind=note title=\"...\"; do move $item to=x,y");
    L.push("  click a title or a body     edits in place, settles on blur, Escape sends nothing  ->  do retitle <id> title=\"...\" / do rewrite <id> text=\"...\"");
    L.push("  drag a card / its corner    ->  do move <id> to=x,y   /   do resize <id> to=WxH");
    L.push("  drag the dot on a card      ->  do link <a> <b> as=refers      (there is no unlink; filed to-jeff)");
    L.push("  +tag on a card              ->  do tag <id> add=<word>");
    L.push("  'name this group' on a ~ ring  ->  do group <ids> as=free title=\"...\"   — the one that turns ~ into =");
    L.push("  a tag chip in the bar       filters MY view only. stance, not a deed, no command.");
    L.push("");
    // Iris, c499: everything is 300x160, so the looseness lives entirely in the positions. That is itself
    // a readable fact about the arrangement, and the same kind of fact as proximity.
    const sizes = [...new Set(all.map(n => `${n.w}x${n.h}`))];
    if (all.length > 1 && sizes.length === 1)
      L.push(`~ every card is ${sizes[0]}. Nobody has resized anything, so size carries no information on this canvas yet — only position does.`);
    else if (all.length > 1)
      L.push(`~ ${sizes.length} different card sizes are in use (${sizes.join(", ")}), so size may be carrying meaning here as well as position.`);
    L.push("");
    L.push("? what I cannot tell you");
    L.push(`  how much of a covered card is actually hidden. The desk knows ("52% hidden by f30"); Notes only has`);
    L.push(`  a rectangle test, so anything above marked ~ overlaps is my arithmetic, not the desk's measurement.`);
    L.push("  whether the arrangement means anything to the person who made it. Proximity is evidence, not intent.");
    L.push("  how any of this looks: type, weight, the colour of a card, whether two cards read as one block.");
    L.push("  whether a person is looking at this canvas right now, or where. The desk has no presence yet.");
    return L.join("\n");
  }

  Desk.registerApp({
    id: "notes", title: "Notes", glyph: "◇",
    open: draw, refresh: host => { if (!editing) draw(host); },
    text,
  });
})();
