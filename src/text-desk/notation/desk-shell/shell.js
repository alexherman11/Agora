// shell.js : the desktop itself. OWNER: Wren.
//
// THE OPEN QUESTION, ANSWERED (and argued on the studio desk): an open window IS a fact in the world.
// A window showing a thing is an APPEARANCE of that thing on your own `<actor> screen` surface, at the
// window's x, y, w, h. So the other inhabitant can see what you have open, where it is and how big;
// so a reload restores your desktop from the world and not from a cookie; so `undo` reaches a window
// you closed by mistake; so moving a window is `do move a31 to=420,120` and appears in "said" like
// everything else. The desk already had the concept — an appearance is a thing placed somewhere —
// and no new server feature was needed.
// What stays view state, honestly: which window is in front (z), scroll position, and whether the
// "as text" face is showing. Those are per-eye and per-moment; the bar says so.

const Shell = (() => {
  const stage = document.getElementById("stage"), dock = document.getElementById("dock"),
        bar = document.getElementById("bar"), said = document.getElementById("said");
  const wins = new Map();     // appearance id (or "view:<n>") -> window record
  let z = 1, viewOnly = 0, styleSrc = "", lastRefusal = null, theme = "", sourceRev = 0, snapOn = false;
  const R = n => (typeof Style === "undefined" ? "" : Desk.style.role(n));

  // ---------- style ----------
  // A missing part subtracts itself and says so; it never stops the boot (Lark, a474; Iris, a467,
  // where `Style is not defined` left a blank white page that declared nothing). Everything below
  // this line runs whether or not the style exists.
  function bootSays(msg) {
    let el = document.getElementById("boot");
    if (!el) { el = document.createElement("div"); el.id = "boot"; document.body.prepend(el); }
    el.innerHTML = `<span>${esc(msg)}</span>`;
  }
  async function loadStyle() {
    // ?style=off simulates the failure on purpose, so the guard is testable rather than hoped for.
    if (new URLSearchParams(location.search).get("style") === "off") {
      bootSays("style is off by request (?style=off): everything below is unstyled, and every app still works. this is the boot guard, on purpose.");
      return;
    }
    if (typeof Style === "undefined") {
      bootSays("style is not loaded: everything below is unstyled, and the apps still work. (Style is not defined — style/style.js did not run)");
      return;
    }
    // 8 Oct: the style is read once, by the server (style.py); this page is handed the looks. The panel's edits go
    // the same way (POST /api/style), so an unsaved text is judged by the one reader too.
    let st;
    try { st = await (await fetch(`/api/style?name=calm&theme=${encodeURIComponent(theme)}&t=${Date.now()}`)).json(); }
    catch (e) { bootSays("the style could not be fetched (/api/style): everything below is unstyled. (" + e.message + ")"); return; }
    styleSrc = st.text || "";
    if (!(await apply(styleSrc))) bootSays("the style did not parse, so none of it is installed: everything below is unstyled. open the style panel for the refusal.");
  }
  async function apply(src) {
    let st;
    try { st = await (await fetch("/api/style", { method: "POST", body: JSON.stringify({ text: src, theme }) })).json(); }
    catch (e) { lastRefusal = new Style.Refusal(0, "the reader could not be reached: " + e.message); return false; }
    if (!st.looks) { const m = /^line (\d+): (.*)$/.exec(st.refusal || ""); lastRefusal = new Style.Refusal(m ? +m[1] : 0, m ? m[2] : (st.refusal || "refused"), st.escapes); return false; }
    Style.install(st.looks); lastRefusal = null; styleSrc = src; sourceRev++;
    return true;
  }

  // ---------- windows ----------
  function appFor(node, subject) {
    return Desk.apps.find(a => a.accepts && a.accepts(node, subject)) || Desk.apps[0];
  }

  function makeWindow(key, app, ctx, geom) {
    const el = document.createElement("section");
    el.className = "window " + R("window");
    el.style.zIndex = ++z;
    el.style.left = geom.x + "px"; el.style.top = geom.y + "px";
    el.style.width = geom.w + "px"; el.style.height = geom.h + "px";
    el.innerHTML =
      `<div class="titlebar ${R("titlebar")}"><span class="name ${R("windowname")}"></span><span class="sub"></span>
         <span class="grow"></span>
         <button class="astext ${R("tool")}" title="what a text-only inhabitant reads for this window">as text</button>
         <button class="close ${R("tool")}" title="close">close</button></div>
       <div class="body"></div><pre class="astext-face ${R("source")} hidden"></pre><div class="grip"></div>`;
    el.querySelector(".name").textContent = ctx.title || app.title;
    el.querySelector(".sub").className = "sub " + R("meta");
    el.querySelector(".sub").textContent = ctx.node ? ctx.node.id : "not in the world";
    const w = { key, app, ctx, el, body: el.querySelector(".body"), face: el.querySelector(".astext-face"), showing: "body" };
    w.body.dataset.owner = app.id;                      // so Style.reach can say WHO drew an off-ramp size
    el.dataset.owner = app.id;
    el.addEventListener("mousedown", () => { el.style.zIndex = ++z; paintBar(); });
    el.querySelector(".close").onclick = async (e) => {
      e.stopPropagation();
      wins.delete(key); el.remove();
      if (ctx.node) await Desk.do(`do remove ${ctx.node.id}`); else { viewOnly--; paintBar(); }
    };
    el.querySelector(".astext").onclick = (e) => {
      e.stopPropagation();
      const on = w.showing === "body";
      w.showing = on ? "text" : "body";
      w.body.classList.toggle("hidden", on); w.face.classList.toggle("hidden", !on);
      e.target.className = "astext " + R(on ? "tool.on" : "tool");
      refreshFace(w);
    };
    drag(w); resize(w);
    stage.appendChild(el); wins.set(key, w);
    try { app.open(w.body, ctx); } catch (err) { w.body.innerHTML = `<div class="${R("refusal")}">the app failed to open: ${esc(err.message)}</div>`; }
    paintBar();
    return w;
  }

  function refreshFace(w) {
    if (w.showing !== "text") return;
    w.face.textContent = w.app.text ? w.app.text(w.ctx)
      : `${w.app.title}\n\n(this app does not say what it reads as in text yet.\n by the law of the house that is a defect, not a missing nicety: OWNERS.md rule 2)`;
  }

  // Opening. A window on a thing becomes an appearance on your screen: a fact, not view state.
  async function open(app, ctx = {}) {
    if (!ctx.subject) {               // an app opened from the dock with nothing in it yet
      viewOnly++;
      return makeWindow("view:" + viewOnly, app, ctx, place());
    }
    const screen = await Desk.screenEnsure();
    if (!screen) return makeWindow("view:" + (++viewOnly), app, ctx, place());
    const g = place();
    const r = await Desk.do(`do place ${ctx.subject} into=${screen}`);
    if (r.error) return makeWindow("view:" + (++viewOnly), app, ctx, place());
    const mine = Desk.children(screen).filter(n => n.subject === ctx.subject);
    const node = mine[mine.length - 1];
    if (node) { await Desk.do(`do move ${node.id} to=${g.x},${g.y}`); await Desk.do(`do resize ${node.id} to=${g.w}x${g.h}`); }
    await Desk.refresh();
  }

  // Clicking an app in the dock opens it ON SOMETHING, so that the window is a fact in the world and
  // not a floating view. If nothing in the world fits, the window opens view-only and says so in the bar.
  function openBest(app) {
    const screens = new Set(Object.values(Desk.snapshot.nodes).filter(n => n.type === "surface" && /\sscreen$/.test(n.title || "")).map(n => n.id));
    const cand = Object.values(Desk.snapshot.nodes).filter(n => {
      if (n.type !== "appearance" || screens.has(n.parent)) return false;
      const s = Desk.subject(n.subject);
      return s && app.accepts && app.accepts(n, s);
    });
    return open(app, cand.length ? { node: cand[0], subject: cand[0].subject, id: cand[0].subject, title: Desk.title(cand[0].id) } : {});
  }

  function place() {
    const n = wins.size;
    const g = (Style && Style.token && Style.token("gap")) || 8;           // the cascade is on the grid too
    const snap8 = v => Math.round(v / g) * g;
    return { x: snap8(48 + (n % 5) * g * 4), y: snap8(24 + (n % 5) * g * 3),
             w: snap8(Math.min(720, stage.clientWidth - g * 15)), h: snap8(Math.min(464, stage.clientHeight - g * 12)) };
  }

  function drag(w) {
    const h = w.el.querySelector(".titlebar");
    h.addEventListener("mousedown", e => {
      if (e.target.tagName === "BUTTON") return;
      const ox = e.clientX - w.el.offsetLeft, oy = e.clientY - w.el.offsetTop;
      const move = m => { w.el.style.left = (m.clientX - ox) + "px"; w.el.style.top = Math.max(0, m.clientY - oy) + "px"; };
      const up = async () => {
        removeEventListener("mousemove", move); removeEventListener("mouseup", up);
        if (w.ctx.node) await Desk.do(`do move ${w.ctx.node.id} to=${parseInt(w.el.style.left)},${parseInt(w.el.style.top)}`);
      };
      addEventListener("mousemove", move); addEventListener("mouseup", up);
    });
  }
  function resize(w) {
    w.el.querySelector(".grip").addEventListener("mousedown", e => {
      e.stopPropagation();
      const sx = e.clientX, sy = e.clientY, sw = w.el.offsetWidth, sh = w.el.offsetHeight;
      const move = m => { w.el.style.width = Math.max(280, sw + m.clientX - sx) + "px"; w.el.style.height = Math.max(160, sh + m.clientY - sy) + "px"; };
      const up = async () => {
        removeEventListener("mousemove", move); removeEventListener("mouseup", up);
        if (w.ctx.node) await Desk.do(`do resize ${w.ctx.node.id} to=${w.el.offsetWidth}x${w.el.offsetHeight}`);
      };
      addEventListener("mousemove", move); addEventListener("mouseup", up);
    });
  }

  // ---------- the world draws the windows ----------
  function syncWindows() {
    const screen = Desk.screen();
    const want = new Map();
    if (screen) Desk.children(screen).forEach(n => want.set(n.id, n));
    for (const [key, w] of wins) if (key.startsWith("a") && !want.has(key)) { w.el.remove(); wins.delete(key); }
    for (const [id, node] of want) {
      const subject = Desk.subject(node.subject);
      const existing = wins.get(id);
      if (!existing) {
        const app = appFor(node, subject);
        if (app) makeWindow(id, app, { node, subject, id: node.subject, title: subject.title }, { x: node.x, y: node.y, w: node.w, h: node.h });
      } else if (document.activeElement !== existing.el && !existing.dragging) {
        existing.el.style.left = node.x + "px"; existing.el.style.top = node.y + "px";
        existing.el.style.width = node.w + "px"; existing.el.style.height = node.h + "px";
        existing.ctx.node = node;
      }
    }
  }

  // ---------- the bar ----------
  function offscreen() {
    let n = 0;
    for (const w of wins.values()) {
      const r = w.el.getBoundingClientRect(), s = stage.getBoundingClientRect();
      if (r.right < s.left + 8 || r.left > s.right - 8 || r.bottom < s.top + 8 || r.top > s.bottom - 8) n++;
    }
    return n;
  }

  function paintBar() {
    const snap = Desk.snapshot; if (!snap) return;
    const off = offscreen(), others = otherScreens();
    stage.classList.toggle("hasoff", off > 0);
    bar.className = R("bar");
    bar.innerHTML =
      `<span>${esc(Desk.session)}</span>${snap.worktree ? `<span class="alarm"><span>worktree ${esc(snap.worktree)} — not the base world</span></span>` : ""}<span>·</span><span>you are ${esc(Desk.actor)}</span>
       <span>·</span><span>${esc(snap.clock && snap.clock.today || "no clock")}</span>
       <span>·</span><span>${wins.size} window${wins.size === 1 ? "" : "s"} open</span>
       ${viewOnly ? `<span class="alarm"><span>${viewOnly} not in the world</span></span>` : ""}
       ${off ? `<span class="alarm"><span>${off} off the stage</span></span>` : ""}
       ${others.map(o => `<span>·</span><span>${esc(o)}</span>`).join("")}
       ${Desk.offline ? `<span>·</span><span class="${R("cut")}">! server away — this picture is stale</span>` : ""}
       <span class="grow"></span><span class="${R("meta")}">world @${snap.events_total}</span>
       <button class="tb ${R("tool")}" data-a="theme">theme: ${theme || "calm"}</button>
       <button class="tb ${R(snapOn ? "tool.on" : "tool")}" data-a="snap">snap to ramp${snapOn ? " (on)" : ""}</button>
       <button class="tb ${R("tool")}" data-a="style">style</button>
       <button class="tb ${R("tool")}" data-a="astext">desktop as text</button>`;
    bar.querySelectorAll(".tb").forEach(b => b.onclick = () => barAction(b.dataset.a));
  }

  function otherScreens() {
    const out = [];
    Object.values(Desk.snapshot.nodes).forEach(n => {
      if (n.type === "surface" && /\sscreen$/.test(n.title || "") && n.title !== Desk.screenName) {
        const who = n.title.replace(/\sscreen$/, "");
        const k = Desk.children(n.id).length;
        out.push(`${who} has ${k} open`);
      }
    });
    return out;
  }

  function barAction(a) {
    if (a === "theme") {
      const names = ["", ...Style.themes];
      theme = names[(names.indexOf(theme) + 1) % names.length];
      apply(styleSrc).then(() => { if (snapOn) Style.snap(true); paintAll(); }); return;
    }
    if (a === "snap") { snapOn = !snapOn; Style.snap(snapOn); paintBar(); paintSaid(); return; }
    if (a === "style") { openPanel("style"); return; }
    if (a === "astext") { openPanel("astext"); return; }
  }

  // ---------- the said panel, and the style panel ----------
  let panel = "said";
  function openPanel(which) { panel = which; said.classList.remove("hidden"); paintSaid(); }

  function paintSaid() {
    if (said.classList.contains("hidden")) return;
    said.className = R("said");
    const head = `<div class="row" style="gap:var(--t-gap)">
        ${["said", "style", "reach", "astext"].map(p => `<button data-p="${p}" class="${R(p === panel ? "tool.on" : "tool")}">${p === "astext" ? "desktop as text" : p === "reach" ? "style reach" : p}</button>`).join("")}
        <span class="grow"></span><button data-p="close" class="${R("tool")}">close</button></div>`;
    let body = "";
    if (panel === "said") {
      body = Desk.log.length
        ? Desk.log.slice(-20).reverse().map(l => `<div class="line" style="padding:calc(var(--t-gap)/2) 0">
             <code class="${R("source")}">${esc(l.line)}</code>
             <span class="${l.error ? R("cut") : R("meta")}">${esc((l.error || l.text || "").split("\n")[0])}</span></div>`).join("")
        : `<p class="${R("body")}">Nothing yet. Every gesture you make appears here as the command it became — drag a window and watch.</p>`;
    } else if (panel === "style") {
      body = (lastRefusal ? `<pre class="${R("refusal")}">${esc(lastRefusal.toText())}\n\n(the desktop is still drawn with the last style that parsed: a refused program is never installed, so there is nothing to restore)</pre>` : "")
        + `<textarea id="styleed" spellcheck="false" class="${R("source")}" style="width:100%;height:46vh;background:var(--t-card);color:var(--t-ink);border:1px solid var(--t-faint);border-radius:calc(var(--t-gap)/2);padding:var(--t-gap)"></textarea>
           <div class="row" style="gap:var(--t-gap);margin-top:var(--t-gap)">
             <button id="styleapply" class="${R("tool.on")}">apply</button>
             <span class="${R("meta")}">tokens are the only place a colour or a number may appear. try <code>on #eeeeee</code> or <code>pad 17px</code>.</span></div>`;
    } else if (panel === "reach") {
      body = `<pre class="${R("source")}" style="white-space:pre-wrap">${esc(reachText())}</pre>`;
    } else {
      body = `<pre class="${R("source")}" style="white-space:pre-wrap">${esc(desktopAsText())}</pre>`;
    }
    said.innerHTML = head + `<div class="scroll">${body}</div>`;
    said.querySelectorAll("[data-p]").forEach(b => b.onclick = () => {
      if (b.dataset.p === "close") said.classList.add("hidden"); else { panel = b.dataset.p; paintSaid(); }
    });
    const ed = said.querySelector("#styleed");
    if (ed) { ed.value = styleSrc; said.querySelector("#styleapply").onclick = async () => { if (await apply(ed.value)) paintAll(); else paintSaid(); }; }
  }

  // ---------- how far the one style actually reaches ----------
  // An honesty mark for the style itself. A shared style is not enforced by existing; it is enforced
  // by being the only thing that works, and nothing stops an app writing its own px in its own file.
  function reachText() {
    if (typeof Style === "undefined") return "style is not loaded; there is nothing to reach.";
    const r = Style.reach(document.body);
    const out = [];
    out.push(`the ramp, from calm.style: ${r.steps.map(s => `${s.step >= 0 ? "+" : ""}${s.step}=${s.px}px`).join("  ")}`);
    out.push(`  text = ${Style.token("text").size}/${Style.token("text").leading}, ramp = ${Style.token("ramp")}, theme = ${theme || "calm"}`);
    out.push("");
    if (!r.offenders.length) out.push("= every type size on this desktop is a step of the ramp.");
    else {
      out.push(`! ${r.offenders.reduce((a, b) => a + b.count, 0)} element(s) are OFF the ramp, in ${new Set(r.offenders.map(o => o.where.split(" @")[0])).size} zone(s):`);
      r.offenders.forEach(o => out.push(`    ${o.where.padEnd(24)} ${o.count} element(s)`));
      out.push("");
      out.push("the style language reaches a role a file names. it does not reach a px an app writes");
      out.push("in its own stylesheet, and it has no way to refuse one. press SNAP TO RAMP in the bar");
      out.push("to force every size to its nearest step: the difference you see is the exact distance");
      out.push("between a style that is available and a style that is binding. (wren-10 section 4)");
    }
    out.push("");
    out.push(`snap to ramp is ${snapOn ? "ON — sizes below are forced, not authored" : "off"}.`);
    return out.join("\n");
  }

  // ---------- the whole desktop, in text ----------
  function desktopAsText() {
    const out = [];
    const screen = Desk.screen();
    out.push(`${Desk.actor}'s screen${screen ? ` (${screen})` : " — not in the world yet"} · ${wins.size} window${wins.size === 1 ? "" : "s"} · world @${Desk.snapshot.events_total}`);
    out.push(`(quote that number when you ask anyone to look: it is the version this text is true of)`);
    for (const w of wins.values()) {
      const n = w.ctx.node;
      out.push(n
        ? `  ${n.id} ${w.app.title} "${Desk.title(n.id)}" · =${n.w}x${n.h} at ${n.x},${n.y}`
        : `  (view only) ${w.app.title} · not in the world: nothing is open in it, so there is nothing to place`);
      const t = w.app.text ? w.app.text(w.ctx) : null;
      if (t) t.split("\n").slice(0, 6).forEach(l => out.push("    " + l));
      else out.push(`    ! this app does not say what it reads as in text (OWNERS.md rule 2)`);
    }
    const off = offscreen();
    out.push("");
    out.push(`what this text does NOT carry, declared:`);
    out.push(`  which window is in front, scroll positions, and whether a window shows its text face.`);
    out.push(`  those are per-eye and per-moment; everything else above is in the world and undoable.`);
    if (off) out.push(`  ! ${off} window(s) are off the stage — present in the world, not visible on this screen.`);
    otherScreens().forEach(o => out.push(`  · ${o}`));
    return out.join("\n");
  }

  // ---------- dock ----------
  function paintDock() {
    dock.className = R("dock");
    dock.innerHTML = "";
    Desk.apps.forEach(app => {
      const b = document.createElement("button");
      b.className = "dockitem " + R("dockitem"); b.title = app.title;
      b.innerHTML = `<span class="glyph ${R("glyph")}">${app.glyph || "□"}</span><span>${esc(app.title)}</span>`;
      b.onclick = () => openBest(app);
      dock.appendChild(b);
    });
    const t = document.createElement("button");
    t.className = "dockitem " + R("dockitem");
    t.innerHTML = `<span class="glyph ${R("glyph")}">›</span><span>said</span>`;
    t.onclick = () => { said.classList.contains("hidden") ? openPanel("said") : said.classList.add("hidden"); };
    dock.appendChild(t);
  }

  // ---------- paint ----------
  function paintAll() {
    if (!Desk.snapshot) return;
    document.body.className = R("desk");
    syncWindows();
    paintDock(); paintBar(); paintSaid();
    for (const w of wins.values()) { if (w.app.refresh) try { w.app.refresh(w.body, w.ctx); } catch (_) {} refreshFace(w); }
    // Iris, c594: the button read "(on)" while a window still measured 11.5px. Snap ran once, and
    // everything painted after it was unsnapped — the label led the paint. Re-apply after every paint.
    if (snapOn && typeof Style !== "undefined") Style.snap(true);
  }

  const esc = s => String(s).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

  Desk.on(paintAll);
  loadStyle().then(() => { said.classList.add("hidden"); paintAll(); });
  addEventListener("resize", paintBar);

  return { open, wins, esc, desktopAsText, get styleSrc() { return styleSrc; }, get sourceRev() { return sourceRev; } };
})();
