// lens.js : the generic painter, by paint kind. OWNER: Pike (OWNERS.md, 25 Sep).
// LINE BUDGET (Wren's rule, counted apart from continuity since a361): 150 lines of vocabulary. Each new paint kind or
// interaction primitive costs lines here; at the ceiling one must be removed to add one. viewer.js holds continuity.
// It paints the scene's painter contract (pike-7 section 6: key, paint, acts, fence, kids) and sends gestures back as
// desk command lines. It knows paint kinds, roles and interaction primitives, and nothing else: no app, no kind, no
// colour, no size. `fence` is opaque: returned with a gesture, never drawn, never compared.
(async () => {
  const q = new URLSearchParams(location.search);
  const session = q.get("session") || "lens", who = q.get("as") || "alex", lens = q.get("lens") || "notes";
  const paint = document.getElementById("paint"), said = document.getElementById("said");
  Style.install(await (await fetch("style/calm.style")).text(), q.get("theme") || undefined);
  const V = Viewer(session, who, lens, said);
  let last = "", sceneAt = 0, def = null;

  // Astra: a gesture acts on the generation that was painted. It carries what was observed; the desk's fence judges that.
  async function send(n, line, draft, more) {
    const observed = { ...(n.fence || {}), at: sceneAt, def, ...more };
    const r = await (await fetch("/api/do", { method: "POST", body: JSON.stringify({ session, as: who, line, observed }) })).json();
    const t = r.text || r.error || ""; V.answered(n.key, r.error || t.startsWith("ERR") ? t : null, draft);
    await refresh(true);
  }

  // Iris, Astra: a part whose painting did not change keeps its element; only what changed is made again. Pike (run 1):
  // the signature is what is drawn (paint, the shapes of the acts, the kids' keys), never the fence.
  let kept = new Map(), next = new Map();
  function make(n) {
    const old = kept.get(n.key), p = n.paint || {};
    if (old && V.hold === n.key) { next.set(n.key, old); return old.el; }   // the part in a person's hands is not repainted under them
    const sig = JSON.stringify([p, n.acts.map(a => [a.on, a.line, a.part]), n.kids.map(k => k.key), V.drafts.get(n.key)]);
    if (old && old.sig === sig) { old.el._n = n; if (V.reuse(old.el, n.kids.map(make), p.text != null)) { next.set(n.key, old); return old.el; } }
    const el = document.createElement("div");
    el._n = n; el.hidden = !!p.absent; el.dataset.key = n.key;   // Iris: with the key on the paint, agreement is a join
    next.set(n.key, { el, sig }); if (p.why) el.dataset.why = p.why;
    const role = p.role || (p.state || p.cut ? "cut" : null);    // a bind that is not live, or a clamp's leaf, says so in `cut`
    if (role) el.className = Style.roleClass(role);
    if (p.kind === "frame") el.classList.add("l-" + p.flow);
    if (p.box) { el.classList.add("boxed"); Object.assign(el.style, { left: p.box[0] + "px", top: p.box[1] + "px", width: p.box[2] + "px", height: p.box[3] + "px" }); }
    if (p.text != null) {
      el.textContent = V.words(n.key, p.text); V.mark(el, n.key);
      if (p.wrap === "verbatim") el.classList.add("t-verbatim");
      if (p.clamp) { el.classList.add("clamp"); el.style.webkitLineClamp = p.clamp; }
    }
    for (const a of n.acts) {
      if (a.on === "click") el.addEventListener("click", e => {     // a click knows where it landed: $x $y in this part's own space
        if (e.target !== el && a.line.includes("$x")) return;
        const r = el.getBoundingClientRect();
        send(el._n, a.line.replace("$x", Math.round(e.clientX - r.left + el.scrollLeft)).replace("$y", Math.round(e.clientY - r.top + el.scrollTop)));
      });
      if (a.on === "edit") edits(el, n, a);
      if (a.on === "drag" && p.box) drags(el, n, a);
      if (a.on === "carry") carries(el, n);
      if (a.on === "drop") { el.dataset.drop = a.part; el._drop = a; }
    }
    for (const k of n.kids) el.appendChild(make(k));
    return el;
  }

  function edits(el, n, a) {
    el.contentEditable = "plaintext-only"; el.addEventListener("focus", () => { if (!V.repainting) V.hold = n.key; });
    el.addEventListener("input", () => V.typed(n.key, el.textContent, { key: n.key, fence: el._n.fence }));
    el.addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); el.blur(); }
      if (e.key === "Escape") { V.drop(n.key); V.mark(el, n.key); el.textContent = el._n.paint.text; el.blur(); }
    });
    el.addEventListener("blur", () => {
      if (V.repainting) return;      // a repaint moved it; the person is still editing it
      // Rook: never show a person text they did not write. Escape for the desk's quoting; do not rewrite.
      const raw = el.textContent.trim(), v = raw.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\r?\n/g, "\\n");
      const seen = (V.drafts.get(n.key) || {}).seen || el._n;
      if (raw !== (el._n.paint.text || "").trim()) send(seen, a.line.replace("$value", () => v), raw); else { V.hold = null; V.drop(n.key); }
    });
  }

  // drag is geometry: $x $y in the free parent. Pointer and keys take, move and put through the same three steps (S9).
  function drags(el, n, a) {
    el.dataset.drag = "1"; el.tabIndex = 0;
    let m0 = null, x = 0, y = 0;
    const to = (nx, ny) => { x = Math.max(0, Math.round(nx)); y = Math.max(0, Math.round(ny)); el.style.left = x + "px"; el.style.top = y + "px"; };
    const take = () => { m0 = el._n; V.hold = n.key; x = m0.paint.box[0]; y = m0.paint.box[1]; };
    const put = back => {
      const m = m0; m0 = null; if (back) to(m.paint.box[0], m.paint.box[1]);
      if (!back && (x !== m.paint.box[0] || y !== m.paint.box[1])) send(m, a.line.replace("$x", x).replace("$y", y)); else V.hold = null;
    };
    el.addEventListener("pointerdown", e => {
      if (e.target.isContentEditable && e.target !== el) return;
      take(); el.setPointerCapture(e.pointerId);
      const x0 = e.clientX - x, y0 = e.clientY - y, move = m => to(m.clientX - x0, m.clientY - y0);
      const up = () => { el.removeEventListener("pointermove", move); el.removeEventListener("pointerup", up); put(false); };
      el.addEventListener("pointermove", move); el.addEventListener("pointerup", up);
    });
    el.addEventListener("keydown", e => {
      const d = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[e.key], step = e.shiftKey ? 40 : 8;
      if (e.target !== el || !(d || m0)) return;
      if (d) { e.preventDefault(); if (!m0) take(); to(x + d[0] * step, y + d[1] * step); }
      if (e.key === "Enter" || e.key === "Escape") { e.preventDefault(); put(e.key === "Escape"); }
    });
    el.addEventListener("blur", () => { if (m0 && !V.repainting) put(false); });
  }

  // carry is relation (pike-3): pick a thing up, put it down on a part that says `on drop <its part>`; the receiver says
  // what that means, and both are fenced. Pointer: press, move, release over a receiver. Keys: Space takes it, Tab
  // reaches the receivers that accept it, Enter puts it down, Escape cancels. Nothing is sent onto the receiver it came from.
  let carrying = null; const receivers = part => [...paint.querySelectorAll(`[data-drop="${CSS.escape(part)}"]`)];
  const over = r => { const c = Style.roleClass("tool.on"); if (carrying.over) carrying.over.classList.remove(c); carrying.over = r; if (r) r.classList.add(c); };
  // a receiver is judged on what it meant at pick-up (pike-3), though the view keeps repainting while a card is in the air
  function take(el) { const rs = receivers(el._n.part); carrying = { el, n: el._n, over: null, seen: new Map(rs.map(r => [r.dataset.key, r._n.fence])) }; V.hold = el._n.key; rs.forEach(r => { r.tabIndex = 0; }); }
  function put(r) {
    const c = carrying; if (!c) return;
    over(null); carrying = null; c.el.style.transform = ""; receivers(c.n.part).forEach(x => x.removeAttribute("tabindex"));
    if (!r || r.contains(c.el)) { V.hold = null; c.el.focus(); return; }
    const f = c.seen.get(r.dataset.key) || r._n.fence || {};
    send({ key: r._n.key, fence: f }, r._drop.line, undefined, { carried: c.n.fence, receiver: f });
  }
  function carries(el, n) {
    el.tabIndex = 0; el.dataset.carry = n.part;
    el.addEventListener("pointerdown", e => {
      if (e.target.isContentEditable) return;
      take(el); el.setPointerCapture(e.pointerId);
      const x0 = e.clientX, y0 = e.clientY;
      const at = m => document.elementsFromPoint(m.clientX, m.clientY).find(x => x.dataset && x.dataset.drop === n.part) || null;
      const move = m => { el.style.transform = `translate(${m.clientX - x0}px, ${m.clientY - y0}px)`; over(at(m)); };
      const up = m => { el.removeEventListener("pointermove", move); el.removeEventListener("pointerup", up); put(at(m)); };
      el.addEventListener("pointermove", move); el.addEventListener("pointerup", up);
    });
    el.addEventListener("keydown", e => { if (e.key === " " && e.target === el && !carrying) { e.preventDefault(); take(el); } });
  }
  document.addEventListener("keydown", e => {
    if (!carrying) return;
    const r = document.activeElement && document.activeElement.dataset.drop === carrying.n.part ? document.activeElement : null;
    if (e.key === "Escape") { e.preventDefault(); put(null); }
    else if (e.key === "Enter" && r) { e.preventDefault(); put(r); }
    else if (e.key === "Tab") setTimeout(() => over(document.activeElement.dataset.drop === carrying?.n.part ? document.activeElement : null));
  });

  async function refresh(force) {
    const r = await (await fetch(`/api/scene?session=${encodeURIComponent(session)}&as=${who}&lens=${lens}&view=painter`)).json();
    const key = JSON.stringify(r.scene || r.refused);
    if (key === last && !force) return;
    last = key; sceneAt = r.events_total; def = (r.scene && r.scene.def) || r.def || null;
    if (r.refused) { if (!V.hold) paint.replaceChildren(); V.show("refused: " + r.refused); return; }
    V.keep(() => { next = new Map(); const root = make(r.scene); kept = next; if (paint.firstChild !== root) paint.replaceChildren(root); });
    V.show(r.text); report();
  }

  const report = () => V.report(paint, sceneAt, carrying ? { [carrying.n.key]: "carried" + (carrying.over ? " over " + carrying.over.dataset.key : "") } : {}, q.get("share") === "attention");
  let scrolling; paint.addEventListener("scroll", () => { clearTimeout(scrolling); scrolling = setTimeout(report, 400); });

  await refresh();
  setInterval(() => refresh().catch(() => {}), 1500);   // the server restarting is not an error worth a console line
})();
