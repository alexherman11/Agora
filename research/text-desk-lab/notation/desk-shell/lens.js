// lens.js : the generic painter. OWNER: Jeff.
// LINE BUDGET (Wren's rule): 150 lines, ever. Each new scene word costs lines here; at the ceiling a word must
// be removed to add one. This is the guard against growing into a worse HTML that cannot be argued around.
// It paints a scene tree from /api/scene and sends gestures back as desk command lines. It knows the scene
// vocabulary (layout, role, text, clamp, box, acts) and nothing else: no app, no kind, no colour, no size.
// If a lens needs something this file cannot paint, the answer is a new scene word argued for on the studio
// desk, never a special case here.
(async () => {
  const q = new URLSearchParams(location.search);
  const session = q.get("session") || "lens", who = q.get("as") || "alex", lens = q.get("lens") || "notes";
  const paint = document.getElementById("paint"), said = document.getElementById("said");
  Style.install(await (await fetch("style/calm.style")).text(), q.get("theme") || undefined);

  let last = "", busy = false, sceneAt = 0;

  // Astra: a gesture acts on the generation that was painted. It carries what was observed; the desk's fence judges that.
  async function send(n, line) {
    const observed = n.item ? { item: n.item, rev: n.rev, at: sceneAt } : null;
    const r = await (await fetch("/api/do", { method: "POST", body: JSON.stringify({ session, as: who, line, observed }) })).json();
    const t = r.text || r.error || "";
    if (r.error || t.startsWith("ERR")) said.textContent = "refused: " + t + "\n\n" + said.textContent;
    busy = false;
    await refresh(true);
  }

  function make(n) {
    const el = document.createElement("div");
    el.dataset.key = n.key;      // Iris: with the key on the paint, agreement is a join, not two trees walked side by side
    if (n.role) el.className = Style.roleClass(n.role);
    if (n.layout) el.classList.add("l-" + n.layout);
    if (n.box) { el.classList.add("boxed"); Object.assign(el.style, { left: n.box[0] + "px", top: n.box[1] + "px", width: n.box[2] + "px", height: n.box[3] + "px" }); }
    if (n.text !== null) {
      el.textContent = n.text;
      if (n.clamp) { el.classList.add("clamp"); el.style.webkitLineClamp = n.clamp; }
    }
    for (const a of n.acts) {
      if (a.on === "click") el.addEventListener("click", () => send(n, a.line));
      if (a.on === "edit") {
        el.contentEditable = "plaintext-only";
        el.addEventListener("focus", () => { busy = true; });
        el.addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); el.blur(); } if (e.key === "Escape") { el.textContent = n.text; el.blur(); } });
        el.addEventListener("blur", () => {
          // Rook: never show a person text they did not write. Escape for the desk's quoting; do not rewrite.
          const v = el.textContent.trim().replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\r?\n/g, "\\n");
          if (v && v !== n.text) send(n, a.line.replace("$value", () => v)); else busy = false;
        });
      }
      if (a.on === "drag" && n.box) {
        el.dataset.drag = "1";
        el.addEventListener("pointerdown", e => {
          if (e.target.isContentEditable && e.target !== el) return;
          busy = true; el.setPointerCapture(e.pointerId);
          const x0 = e.clientX, y0 = e.clientY; let x = n.box[0], y = n.box[1];
          const move = m => { x = Math.max(0, n.box[0] + m.clientX - x0); y = Math.max(0, n.box[1] + m.clientY - y0); el.style.left = x + "px"; el.style.top = y + "px"; };
          const up = () => {
            el.removeEventListener("pointermove", move); el.removeEventListener("pointerup", up);
            if (x !== n.box[0] || y !== n.box[1]) send(n, a.line.replace("$x", Math.round(x)).replace("$y", Math.round(y))); else busy = false;
          };
          el.addEventListener("pointermove", move); el.addEventListener("pointerup", up);
        });
      }
    }
    for (const k of n.kids) el.appendChild(make(k));
    return el;
  }

  async function refresh(force) {
    if (busy && !force) return;
    const r = await (await fetch(`/api/scene?session=${encodeURIComponent(session)}&as=${who}&lens=${lens}`)).json();
    const key = JSON.stringify(r.scene || r.refused);
    if (key === last) return;
    last = key;
    sceneAt = r.events_total;
    if (r.refused) { paint.replaceChildren(); said.textContent = "refused: " + r.refused; return; }
    paint.replaceChildren(make(r.scene));
    said.textContent = r.text;
  }

  await refresh();
  setInterval(refresh, 1500);
})();
