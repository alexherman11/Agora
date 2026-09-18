// apps/notes.js : the Notes application, a spatial canvas idea space. OWNER: Flint. This stub shows the pattern; replace it.
// Material: the free-layout surface titled "Canvas" and the appearances on it. A drag is `do move <id> to=x,y`.
(() => {
  const canvasId = () => Object.values(Desk.snapshot.nodes).find(n => n.type === "surface" && n.title === "Canvas")?.id;

  function draw(host) {
    const id = canvasId();
    host.innerHTML = "";
    host.style.background = "var(--paper)";
    if (!id) { host.textContent = 'no surface titled "Canvas" in this world'; return; }
    Desk.children(id).forEach(n => {
      if (n.type !== "appearance") return;
      const s = Desk.subject(n.subject), card = document.createElement("div");
      card.style.cssText = `position:absolute;left:${n.x}px;top:${n.y}px;width:${Math.max(n.w, 160)}px;padding:10px 12px;background:var(--surface);border:1px solid var(--line);border-radius:8px;cursor:grab`;
      card.innerHTML = `<div style="font-weight:500">${Shell.esc(s.title)}</div><div style="color:var(--quiet);font-size:12px">${Shell.esc((s.text || "").split("\n")[0].slice(0, 90))}</div>`;
      card.onmousedown = e => {
        const ox = e.clientX - n.x, oy = e.clientY - n.y; let x = n.x, y = n.y;
        const move = m => { x = Math.max(0, m.clientX - ox); y = Math.max(0, m.clientY - oy); card.style.left = x + "px"; card.style.top = y + "px"; };
        const up = () => { removeEventListener("mousemove", move); removeEventListener("mouseup", up);
          if (x !== n.x || y !== n.y) Desk.do(`look ${id}; do move ${n.id} to=${Math.round(x)},${Math.round(y)}`); };
        addEventListener("mousemove", move); addEventListener("mouseup", up);
      };
      host.appendChild(card);
    });
    host.ondblclick = e => { if (e.target !== host) return;
      const t = prompt("title of the new note"); if (t) Desk.do(`look ${id}; do create ${id} kind=note title="${t.replace(/"/g, "'")}"`); };
  }

  Desk.registerApp({
    id: "notes", title: "Notes", glyph: "✎",
    open: draw, refresh: draw,
    text: () => { const id = canvasId(); return id ? `look ${id} :3   (what a text-only reader asks for)\n\n` + Desk.snapshot.outline : "no Canvas"; },
  });
})();
