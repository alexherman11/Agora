// lens.js : the generic painter. OWNER: Jeff.
// It paints a scene tree from /api/scene and sends gestures back as desk command lines. It knows the scene
// vocabulary (layout, role, text, clamp, box, acts) and nothing else: no app, no kind, no colour, no size.
// If a lens needs something this file cannot paint, the answer is a new scene word argued for on the studio
// desk, never a special case here.
(async () => {
  const q = new URLSearchParams(location.search);
  const session = q.get("session") || "lens", who = q.get("as") || "alex", lens = q.get("lens") || "notes";
  const paint = document.getElementById("paint"), said = document.getElementById("said");
  Style.install(await (await fetch("style/calm.style")).text(), q.get("theme") || undefined);

  let last = "", busy = false;

  async function send(line) {
    const r = await (await fetch("/api/do", { method: "POST", body: JSON.stringify({ session, as: who, line }) })).json();
    const t = r.text || r.error || "";
    if (r.error || t.startsWith("ERR")) said.textContent = "refused: " + t + "\n\n" + said.textContent;
    busy = false;
    await refresh(true);
  }

  // the desk refuses an act on a thing you have not looked at; a gesture on a painted thing IS having looked
  const looked = (item, line) => (item ? `look ${item}; ` : "") + line;

  function make(n) {
    const el = document.createElement("div");
    if (n.role) el.className = Style.roleClass(n.role);
    if (n.layout) el.classList.add("l-" + n.layout);
    if (n.box) { el.classList.add("boxed"); Object.assign(el.style, { left: n.box[0] + "px", top: n.box[1] + "px", width: n.box[2] + "px", height: n.box[3] + "px" }); }
    if (n.text !== null) {
      el.textContent = n.text;
      if (n.clamp) { el.classList.add("clamp"); el.style.webkitLineClamp = n.clamp; }
    }
    for (const a of n.acts) {
      if (a.on === "click") el.addEventListener("click", () => send(looked(n.item, a.line)));
      if (a.on === "edit") {
        el.contentEditable = "plaintext-only";
        el.addEventListener("focus", () => { busy = true; });
        el.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); el.blur(); } if (e.key === "Escape") { el.textContent = n.text; el.blur(); } });
        el.addEventListener("blur", () => {
          const v = el.textContent.trim().replace(/"/g, "'");
          if (v && v !== n.text) send(looked(n.item, a.line.replace("$value", v))); else busy = false;
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
            if (x !== n.box[0] || y !== n.box[1]) send(looked(n.item, a.line.replace("$x", Math.round(x)).replace("$y", Math.round(y)))); else busy = false;
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
    if (r.refused) { paint.replaceChildren(); said.textContent = "refused: " + r.refused; return; }
    paint.replaceChildren(make(r.scene));
    said.textContent = r.text;
  }

  await refresh();
  setInterval(refresh, 1500);
})();
