// shell.js : the desktop itself. OWNER: Wren. This is a deliberately plain skeleton to be replaced:
// a dock at the bottom, windows on a stage, a bar on top, and a panel that shows every command the shell has sent
// (the interface teaches the language) and what the front window reads as in text.
const Shell = (() => {
  const stage = document.getElementById("stage"), dock = document.getElementById("dock"),
        bar = document.getElementById("bar"), said = document.getElementById("said");
  const windows = [];   // view state only: which apps are open and in what order. Open question for the team:
                        // should an open window be a fact in the world, so the other inhabitant can see it?
  let z = 1;

  function openApp(app, ctx = {}) {
    const el = document.createElement("section");
    el.className = "window";
    el.style.zIndex = ++z;
    el.style.left = 60 + windows.length * 36 + "px";
    el.style.top = 30 + windows.length * 28 + "px";
    el.innerHTML = `<div class="titlebar"><span class="title"></span><button class="astext" title="what a text-only reader gets">as text</button><button class="close" title="close">×</button></div><div class="body"></div><pre class="text" hidden></pre>`;
    el.querySelector(".title").textContent = app.title;
    const w = { app, ctx, el, body: el.querySelector(".body"), text: el.querySelector(".text") };
    el.addEventListener("mousedown", () => { el.style.zIndex = ++z; });
    el.querySelector(".close").onclick = () => { el.remove(); windows.splice(windows.indexOf(w), 1); };
    el.querySelector(".astext").onclick = () => {
      w.text.hidden = !w.text.hidden; w.body.hidden = !w.body.hidden;
      w.text.textContent = app.text ? app.text(ctx) : "(this app does not say what it reads as in text yet: that is a defect)";
    };
    drag(el, el.querySelector(".titlebar"));
    stage.appendChild(el); windows.push(w);
    app.open(w.body, ctx);
    return w;
  }

  function drag(el, handle) {
    handle.addEventListener("mousedown", e => {
      if (e.target.tagName === "BUTTON") return;
      const ox = e.clientX - el.offsetLeft, oy = e.clientY - el.offsetTop;
      const move = m => { el.style.left = m.clientX - ox + "px"; el.style.top = Math.max(0, m.clientY - oy) + "px"; };
      const up = () => { removeEventListener("mousemove", move); removeEventListener("mouseup", up); };
      addEventListener("mousemove", move); addEventListener("mouseup", up);
    });
  }

  function paint(snap) {
    bar.textContent = `${Desk.session} · you are ${Desk.actor} · ${snap.clock.today || "no clock"} · ${Object.keys(snap.subjects).length} things`;
    dock.innerHTML = "";
    Desk.apps.forEach(app => {
      const b = document.createElement("button");
      b.className = "dockitem"; b.title = app.title;
      b.innerHTML = `<span class="glyph">${app.glyph || "□"}</span><span class="label">${app.title}</span>`;
      b.onclick = () => openApp(app);
      dock.appendChild(b);
    });
    const t = document.createElement("button");
    t.className = "dockitem quiet"; t.innerHTML = `<span class="glyph">›_</span><span class="label">said</span>`;
    t.onclick = () => { said.hidden = !said.hidden; paintSaid(); };
    dock.appendChild(t);
    windows.forEach(w => { if (w.app.refresh) w.app.refresh(w.body, w.ctx); if (!w.text.hidden && w.app.text) w.text.textContent = w.app.text(w.ctx); });
    paintSaid();
  }

  function paintSaid() {
    if (said.hidden) return;
    said.innerHTML = "<h2>said to the desk</h2>" + (Desk.log.slice(-12).map(l =>
      `<div class="line"><code>${esc(l.line)}</code><div class="${l.error ? "err" : "ok"}">${esc((l.error || l.text || "").split("\n")[0])}</div></div>`).join("") || "<p>nothing yet. every gesture you make will appear here as the command it became.</p>");
  }
  const esc = s => String(s).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

  Desk.on(paint);
  return { openApp, windows, esc };
})();
