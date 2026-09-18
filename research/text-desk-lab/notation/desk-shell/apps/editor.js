// apps/editor.js : the Text editor (a Google-Docs-like page). OWNER: Moss. This stub shows the pattern; replace it.
// Material: subjects of kind doc. The stub commits the whole text with `do rewrite` when you leave the field, which is
// exactly the crude thing the studio argued against (open / settle, anchors that ride along). Make it right.
(() => {
  let current = null;
  const docs = () => Object.values(Desk.snapshot.nodes).filter(n => n.type === "appearance" && Desk.subject(n.subject).kind === "doc");

  function draw(host) {
    const list = docs();
    if (!current || !Desk.node(current)) current = list[0]?.id;
    host.innerHTML = "";
    host.style.cssText = "display:grid;grid-template-columns:200px 1fr;height:100%";
    const rail = document.createElement("div"), page = document.createElement("div");
    rail.style.cssText = "border-right:1px solid var(--line);padding:12px;overflow:auto;font-size:13px";
    page.style.cssText = "padding:28px 40px;overflow:auto";
    list.forEach(n => { const a = document.createElement("div"); a.textContent = Desk.title(n.id);
      a.style.cssText = `padding:4px 8px;border-radius:6px;cursor:pointer;${n.id === current ? "background:var(--paper);font-weight:500" : "color:var(--quiet)"}`;
      a.onclick = () => { current = n.id; draw(host); }; rail.appendChild(a); });
    if (current) {
      const s = Desk.subject(Desk.node(current).subject);
      const h = document.createElement("h1"); h.textContent = s.title; h.style.cssText = "font-weight:500;font-size:24px;margin:0 0 16px";
      const ta = document.createElement("textarea"); ta.value = s.text || "";
      ta.style.cssText = "width:100%;min-height:340px;border:0;outline:0;resize:none;font:15px/1.7 var(--font);color:var(--ink);background:transparent";
      ta.onblur = () => { if (ta.value !== (s.text || ""))
        Desk.do(`read ${current}; do rewrite ${current} text="${ta.value.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, "\\n")}"`); };
      page.append(h, ta);
    } else page.textContent = "no documents in this world yet";
    host.append(rail, page);
  }

  Desk.registerApp({
    id: "editor", title: "Editor", glyph: "¶",
    open: draw, refresh: host => { if (!host.querySelector("textarea:focus")) draw(host); },
    text: () => current ? `read ${current}\n\n` + (Desk.subject(Desk.node(current).subject).text || "") : "no document open",
  });
})();
