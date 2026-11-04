// EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
// This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
// facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
// who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
// (people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
// use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.
//
// shell.js: the desktop shell's three surfaces (top bar, dock, desktop layer) and the small parts they share.
// Shell builder, 26 Oct 2026. Contracts: agora-wm/CONTRACTS.md section 3 (this), section 1 (the theme it reads: only
// --ag-* variables, never a colour of its own) and section 2 (the words it speaks: wm.*).
//
// Shape of the file. Everything is a small named part with a settings object (its handles); a page is an arrangement of
// parts. The parts are plain DOM, not painter components, because a bar has to talk to its own native window (shape,
// reserved strip, DWM thumbnails) and the sandboxed component frame has no such bridge (SHELL.md, "Why not components").
//
//   Theme    the stylesheet (host /theme.css, or a look from looks/ when there is none), live on theme.changed
//   Wall     the wallpaper slice that sits behind a window (so a bar over the desktop layer looks see-through)
//   Data     what the pages ask the world: wm.windows (fallback: window.desktop + window.list), system.now, media.now ...
//   Glyph    UI glyphs (tintable SVG);   Icon: an app's colour icon (or the theme's plate with a letter)
//   Pop      one popover at a time, with focus return, Escape, outside click
//   Top      the top bar;   Dock: the dock;   Desk: the desktop layer
//   Native   the window's side: Native.layout({reserve, shape}) tells the host what strip to reserve and where the
//            window is solid (SetWindowRgn); Native.thumb(...) asks for a live DWM thumbnail.
"use strict";
const Shell = (() => {
  const q = new URLSearchParams(location.search);
  const doc = document, root = doc.documentElement;
  const num = (v, d) => (v === null || v === undefined || v === "" || Number.isNaN(+v) ? d : +v);

  // ------------------------------------------------------------------------------------------------ tiny DOM
  function h(tag, attrs, ...kids) {
    const e = doc.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v === undefined || v === null || v === false) continue;
      if (k === "on") for (const [ev, f] of Object.entries(v)) e.addEventListener(ev, f);
      else if (k === "cls") e.className = v;
      else if (k === "style" && typeof v === "object") for (const [p, x] of Object.entries(v)) e.style.setProperty(p, x);
      else if (k === "html") e.innerHTML = v;
      else e.setAttribute(k, v === true ? "" : v);
    }
    for (const c of kids.flat(3)) if (c !== null && c !== undefined && c !== false) e.append(c.nodeType ? c : String(c));
    return e;
  }
  const $ = (s, r = doc) => r.querySelector(s);
  const css = (name) => getComputedStyle(root).getPropertyValue(name).trim();

  // ------------------------------------------------------------------------------------------------ theme
  const Theme = {
    link: null, look: q.get("look"),
    async exists(url) {
      try {
        const r = await fetch(url, { cache: "no-store" });
        return r.ok && /css/.test(r.headers.get("content-type") || "");
      } catch (e) { return false; }
    },
    async init() {
      if (this.link) return;                       // once per page (the component host and the fallback share it)
      this.link = h("link", { rel: "stylesheet", id: "theme" });
      doc.head.append(this.link);
      // ?theme=<same-origin url> (a proof's own compiled theme), ?look=<stand-in>, else the host's /desk/theme.css,
      // else a stand-in look (so the shell still wears something when no theme builder is running)
      let href = q.get("theme");
      if (!href && this.look) href = `/desk/shell/looks/${this.look}.css`;
      if (!href) for (const u of ["/desk/theme.css", "/theme.css"]) if (await this.exists(u)) { href = u; break; }
      if (!href) href = "/desk/shell/looks/seabright-day.css";
      await this.load(href);
      this.source = href;
    },
    load(href) {
      return new Promise((res) => {
        this.link.onload = this.link.onerror = () => { this.read(); res(); };
        this.link.href = href;
      });
    },
    // the host publishes the happening theme.changed; every surface repaints without a reload
    reload() { return this.load(this.source.split("?")[0] + "?v=" + Date.now()); },
    use(look) { this.source = `/desk/shell/looks/${look}.css`; return this.load(this.source); },
    read() {
      root.dataset.icons = css("--ag-icon-style") || "native";
      root.dataset.reduce = css("--ag-motion-reduce") === "1" ? "yes" : "no";
      root.dataset.outline = css("--ag-island-outline") === "1" ? "yes" : "no";
      Theme.name = (css("--ag-variant") || "");
      for (const f of Theme.listeners || []) f();
    },
  };

  // ------------------------------------------------------------------------------------------------ the wallpaper slice
  // The desktop layer draws the wallpaper. A bar or dock is a window over that layer, so it draws the same wallpaper
  // at the same place behind itself: sx, sy is where this window sits on the screen (window.screenX/Y, or the
  // composite proof's own numbers), sw, sh the screen. Over a bar that is only ever above the desktop (its strip is
  // reserved), the copy and the real thing are the same pixels, which is what lets a rounded floating dock be see-through
  // without a transparent window (SHELL.md, spike 1).
  const Wall = {
    el: null,
    init() {
      if (this.el) return;
      this.el = h("div", { cls: "wall", "aria-hidden": "true" });
      doc.body.prepend(this.el);
      this.place();
      setInterval(() => this.place(), 600);
      addEventListener("resize", () => this.place());
    },
    place() {
      const sx = num(q.get("sx"), window.screenX), sy = num(q.get("sy"), window.screenY);
      const sw = num(q.get("sw"), screen.width), sh = num(q.get("sh"), screen.height);
      const key = [sx, sy, sw, sh].join();
      if (key === this.key) return;
      this.key = key;
      this.el.style.cssText = `left:${-sx}px;top:${-sy}px;width:${sw}px;height:${sh}px`;
      root.style.setProperty("--sx", sx + "px");
      root.style.setProperty("--sy", sy + "px");
    },
  };

  // ------------------------------------------------------------------------------------------------ glyphs
  // Tintable UI glyphs in the stroke style of the vendored Lucide set (24 px grid, 2 px stroke, round). The simple
  // ones are drawn here; the rest come from pages/icons.
  const G = {
    wifi: '<path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><path d="M12 20h.01"/>',
    "wifi-off": '<path d="M2 2l20 20"/><path d="M8.5 16.4a6 6 0 0 1 7 0"/><path d="M5 12.6a11 11 0 0 1 5.2-2.6"/><path d="M12 20h.01"/>',
    volume: '<path d="M11 5 6 9H2v6h4l5 4V5z"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>',
    "volume-low": '<path d="M11 5 6 9H2v6h4l5 4V5z"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>',
    "volume-x": '<path d="M11 5 6 9H2v6h4l5 4V5z"/><path d="m22 9-6 6"/><path d="m16 9 6 6"/>',
    battery: '<rect x="2" y="7" width="16" height="10" rx="2"/><path d="M22 11v2"/><path d="M6 11v2" class="lvl"/>',
    "battery-charging": '<path d="M15 7h1a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2h-2"/><path d="M6 17H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h1"/><path d="m11 7-3 5h4l-3 5"/><path d="M22 11v2"/>',
    bell: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
    left: '<path d="m15 18-6-6 6-6"/>', right: '<path d="m9 18 6-6-6-6"/>', down: '<path d="m6 9 6 6 6-6"/>',
    x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>', minus: '<path d="M5 12h14"/>',
    power: '<path d="M18.36 6.64a9 9 0 1 1-12.73 0"/><path d="M12 2v10"/>',
    play: '<path d="M6 4v16l14-8z" fill="currentColor"/>',
    pause: '<rect x="6" y="4" width="4" height="16" rx="1" fill="currentColor"/><rect x="14" y="4" width="4" height="16" rx="1" fill="currentColor"/>',
    next: '<path d="M5 4v16l10-8z" fill="currentColor"/><path d="M19 5v14"/>',
    prev: '<path d="M19 4v16L9 12z" fill="currentColor"/><path d="M5 5v14"/>',
    pin: '<path d="M12 17v5"/><path d="M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z"/>',
    "pin-off": '<path d="M12 17v5"/><path d="M15 9.34V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H7.89"/><path d="m2 2 20 20"/><path d="M9 9v1.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h11"/>',
    grid: '<rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/>',
    settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    monitor: '<rect width="20" height="14" x="2" y="3" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/>',
    external: '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    cpu: '<rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9"/><path d="M15 2v2M15 20v2M2 15h2M2 9h2M20 15h2M20 9h2M9 2v2M9 20v2"/>',
    memory: '<path d="M6 19v-3M10 19v-3M14 19v-3M18 19v-3M8 11V9M16 11V9M12 11V9"/><path d="M2 15h20"/><path d="M2 7a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v1.1a2 2 0 0 0 0 3.8V17a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-5.1a2 2 0 0 0 0-3.8z"/>',
    check: '<path d="M20 6 9 17l-5-5"/>', terminal: '<path d="m4 17 6-6-6-6"/><path d="M12 19h8"/>',
    message: '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22z"/>',
  };
  function glyph(name, cls = "") {
    const s = h("span", { cls: "gl " + cls, "aria-hidden": "true" });
    s.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${G[name] || G.grid}</svg>`;
    return s;
  }

  // ------------------------------------------------------------------------------------------------ icons
  const AGORA_APPS = {
    viewer: ["Viewer", "window.open viewer"],
    lines: ["Lines", "window.open lines"], help: ["Help", "window.open help"], board: ["Board", "window.open board"],
    taskboard: ["Task board", "window.open taskboard-components"], appearance: ["Appearance", "window.open appearance"],
    feed: ["Feed", "window.open feed"], thing: ["Thing", "window.open thing"], tasks: ["Running windows", "window.open tasks"],
    work: ["Work", "window.open work"],          // who is at work and what is moving (kernel-lab/apps/work, 27 Oct)
    writing: ["Writing", "window.open writing"], // documents and plans to review (kernel-lab/apps/writing, 27 Oct)
  };
  // Which Agora app a window or button belongs to, for its icon: the lens name itself, else a family by name
  // (seabright-board is a board, taskboard-components a task board). "thing" is the plain fallback.
  const appOf = (name) => {
    const n = (name || "").toLowerCase();
    if (AGORA_APPS[n]) return n;
    for (const [re, app] of [[/task/, "taskboard"], [/board/, "board"], [/appearance|theme/, "appearance"], [/feed/, "feed"],
                             [/help/, "help"], [/lines|chat/, "lines"]]) if (re.test(n)) return app;
    return "thing";
  };
  const opensLens = (line) => ((line || "").match(/^window\.open (\S+)/) || [])[1] || "";
  const iconUrl = (ref, size = 128) => {
    if (!ref) return "";
    if (ref.startsWith("agora:")) return `/desk/shell/apps/${ref.slice(6).replace(/[^a-z0-9-]/g, "")}.svg`;
    if (ref.startsWith("data:") || ref.startsWith("/") || ref.startsWith("http")) return ref;
    return `/desk/icon?ref=${encodeURIComponent(ref)}&size=${size}`;
  };
  // An app's icon: its own colours (native), or the theme's plate behind them, or one tint (mono): the theme's
  // `icons.style`, read from --ag-icon-style by Theme.read into html[data-icons]. If the picture cannot load, the
  // plate and the first letter stand in.
  function Icon(ref, name, size = 28) {          // size: px, or "dock" / "bar" (the theme's own sizes)
    const e = h("span", { cls: "ico" + (typeof size === "string" ? " " + size : ""), "aria-hidden": "true" });
    if (typeof size === "number") e.style.setProperty("--isz", size + "px");
    const letter = () => { e.classList.add("letter"); e.replaceChildren(h("b", {}, (name || "?").trim().slice(0, 1).toUpperCase())); };
    if (!ref) { letter(); return e; }
    const url = iconUrl(ref, size > 56 ? 256 : 128);
    e.style.setProperty("--src", `url("${url}")`);
    e.append(h("img", { src: url, alt: "", draggable: "false", on: { error: letter } }));
    return e;
  }

  // ------------------------------------------------------------------------------------------------ data
  const NICE = { windowsterminal: "Terminal", msedge: "Edge", chatgpt: "ChatGPT", obs64: "OBS", code: "Code", explorer: "Files",
    applicationframehost: "Settings", claude: "Claude", spotify: "Spotify", chrome: "Chrome", discord: "Discord", python: "Python",
    pythonw: "Python", notepad: "Notepad", mspaint: "Paint", taskmgr: "Task Manager", cmd: "Command Prompt", powershell: "PowerShell" };
  const nice = (p) => NICE[(p || "").toLowerCase()] || ((p || "").slice(0, 1).toUpperCase() + (p || "").slice(1));

  const Data = {
    wmOK: null,
    see: (line) => (window.__fx ? window.__fx.see(line) : KD.see(line)),
    act: (line) => (window.__fx ? window.__fx.act(line) : KD.doLine(line)),
    async windows() {
      const r = await this.see("wm.windows");
      const refOf = (v) => (/^(exe|hwnd|pkg|aumid|agora|data):/.test(v) ? v : /^[A-Za-z]:[\\/]/.test(v) ? "exe:" + v : v || "");
      if (r && r.ok !== false && !r.refused && Array.isArray(r.rows) && !/^refused|no word|unknown word/i.test(r.text || "")) {
        this.wmOK = true;
        // Agora's own windows are in wm.windows too (with their thing id); which view each shows, and which are the shell's
        // own strips, comes from window.list (the window host), never from a title
        const own = new Map();
        if (r.rows.some((w) => w.agora)) for (const w of ((await this.see("window.list")).rows || [])) if (w.kind === "window") own.set(w.id, w);
        return r.rows.filter((w) => w.key !== undefined && w.kind !== "work").flatMap((w) => {
          const o = w.agora ? own.get(w.agora) : null;
          if (w.agora && (!o || o.edge || /^(taskbar|shell-)/.test(o.shows || ""))) return [];
          const shows = (o && o.shows) || w.shows || "";
          return [{ key: String(w.key), app: (o && o.name) || w.app || nice((w.exe || "").split(/[\\/]/).pop().replace(/\.exe$/i, "")), exe: w.exe || "",
            icon: w.agora ? "agora:" + appOf(shows) : refOf(w.icon) || (w.exe ? "exe:" + w.exe : ""),
            agora: w.agora || "", state: w.state || "normal", focused: !!w.focused, managed: w.managed !== false, why: w.why || "", shows, space: w.space || "" }];
        });
      }
      this.wmOK = false;               // the window manager is off: the native shell is the fallback
      const [a, b] = await Promise.all([this.see("window.list"), this.see("window.desktop")]);
      const mine = (a.rows || []).filter((w) => w.kind === "window" && !w.edge && !/^(taskbar|shell-)/.test(w.shows || ""))
        .map((w) => ({ key: w.id, app: w.name || nice(w.shows), exe: "", icon: "agora:" + appOf(w.shows),
          agora: w.id, state: w.shown === false ? "minimised" : "normal", focused: !!w.front, managed: false, shows: w.shows, title: w.name }));
      const theirs = (b.rows || []).filter((w) => w.handle).map((w) => ({
        key: String(w.handle), app: nice(w.program), exe: w.path || "", icon: w.ref || (w.path ? "exe:" + w.path : "hwnd:" + w.handle),
        agora: "", state: w.shown === false ? "minimised" : "normal", focused: !!w.front, managed: false, title: w.name }));
      return [...theirs, ...mine];
    },
    async settings() {
      const r = await this.see("rows shell-settings");
      return (r && r.rows && r.rows[0]) || {};
    },
    async pins() {
      const r = await this.see("rows any bar=taskbar");
      return ((r && r.rows) || []).filter((p) => !p.slot && p.kind !== "widget" && (p.path || /^window\.open /.test(p.does || "")));
    },
    async lensNames() {
      const r = await this.see("rows lens");
      return new Set(((r && r.rows) || []).map((x) => (x.name || "").toLowerCase()));
    },
    async system() {
      const r = await this.see("system.now");
      const o = {};
      for (const x of (r && r.rows) || []) o[x.key] = x;
      return o;
    },
    async media() {
      const r = await this.see("media.now");
      return (r && r.rows && r.rows[0]) || null;
    },
    async notifications() {
      const r = await this.see("rows notification");
      return r && r.ok !== false && Array.isArray(r.rows) ? r.rows : [];
    },
    async jeff() {
      const r = await this.see("rows presence");
      const p = r && r.ok !== false && r.rows && r.rows[0];
      return p ? { state: p.state || "here", note: p.note || "" } : { state: doc.body.classList.contains("away") ? "away" : "here", note: "" };
    },
    async title(key) {
      if (this.noTitleWord) return null;           // the manager has no wm.title: ask once, not on every hover
      const r = await this.see("wm.title " + key);
      if (r && (r.ok === false || r.refused) && /nothing answers/.test(r.text || r.refused || "")) this.noTitleWord = true;
      const t = r && r.ok !== false && r.rows && r.rows[0];
      return t || null;
    },
    // actions: wm.* when the manager answers, the native shell otherwise
    async focus(w) {
      if (w.agora) return this.act(`window.focus ${w.agora}`);
      if (this.wmOK) return this.act(w.state === "minimised" ? `wm.restore ${w.key}` : `wm.focus ${w.key}`);
      return this.act(`window.activate handle=${w.key}`);
    },
    async minimise(w) {
      if (w.agora) return this.act(`window.focus ${w.agora}`);          // focus on the front window tucks it away
      if (this.wmOK) return this.act(`wm.minimise ${w.key}`);
      return this.act(`window.activate handle=${w.key}`);              // activate on the front window minimises it
    },
    async close(w) {
      if (w.agora) return this.act(`window.close ${w.agora}`);
      if (this.wmOK) return this.act(`wm.close ${w.key}`);
      return this.act(`window.activate handle=${w.key} do=close`);
    },
  };

  // ------------------------------------------------------------------------------------------------ the native side
  const Native = {
    api: () => (window.pywebview && window.pywebview.api) || null,
    async call(name, ...args) {
      if (window.__fx && window.__fx.native) return window.__fx.native(name, ...args);
      const a = this.api();
      if (!a || !a[name]) return null;
      try { return await a[name](...args); } catch (e) {
        try { KD.failed(`the window's native ${name} threw: ${(e && e.message) || e}`); } catch (_) { /* no door */ }
        return null;
      }
    },
    dpr: () => window.devicePixelRatio || 1,
    // what strip to reserve (CSS px) and where this window is solid (a list of {x,y,w,h,r} in CSS px)
    layout(spec) { window.__layout = spec; return this.call("layout", JSON.stringify(spec), this.dpr()); },
  };

  // ------------------------------------------------------------------------------------------------ popovers
  const Pop = {
    cur: null,
    open(id, anchor, build, opts = {}) {
      if (this.cur && this.cur.id === id) { this.close(); return null; }
      this.close(true);
      const body = build();
      const card = h("div", { cls: "pop " + (opts.cls || ""), role: "dialog", "aria-label": opts.label || id, tabindex: "-1", "data-pop": id }, body);
      doc.body.append(card);
      anchor.setAttribute("aria-expanded", "true");
      card.addEventListener("keydown", (e) => {
        if (doc.activeElement !== card || !["ArrowDown", "ArrowUp", "Tab"].includes(e.key)) return;
        const f = card.querySelector("[data-autofocus], button:not([disabled]), input");
        if (f) { e.preventDefault(); f.focus(); }
      });
      this.cur = { id, anchor, card, opts, returnTo: doc.activeElement };
      this.position();
      requestAnimationFrame(() => {
        card.classList.add("in");
        // opened by the keyboard: focus goes inside; opened by the pointer: the card holds it, so no ring is drawn on a row
        const first = card.querySelector("[data-autofocus]") || card.querySelector("button, input, [tabindex='0']");
        (Shell.lastInput === "key" && first ? first : card).focus({ preventScroll: true });
        Shell.report();
      });
      return card;
    },
    position() {
      const c = this.cur; if (!c) return;
      const a = c.anchor.getBoundingClientRect(), vw = innerWidth, vh = innerHeight, card = c.card;
      const w = card.offsetWidth, hh = card.offsetHeight, gap = c.opts.gap ?? 8;
      let x = a.left + a.width / 2 - w / 2;
      if (c.opts.align === "left") x = a.left;
      if (c.opts.align === "right") x = a.right - w;
      x = Math.max(10, Math.min(x, vw - w - 10));
      const y = c.opts.above ? a.top - hh - gap : a.bottom + gap;
      card.style.left = x + "px";
      card.style.top = Math.max(4, y) + "px";
      card.style.setProperty("--ox", (a.left + a.width / 2 - x) + "px");
    },
    close(quiet) {
      const c = this.cur; if (!c) return;
      this.cur = null;
      c.anchor.setAttribute("aria-expanded", "false");
      if (c.opts.onClose) c.opts.onClose();
      c.card.classList.remove("in");
      const gone = () => c.card.remove();
      if (quiet || root.dataset.reduce === "yes") gone(); else setTimeout(gone, 120);
      c.card.setAttribute("inert", "");
      if (!quiet) { const t = c.returnTo && c.returnTo.isConnected ? c.returnTo : c.anchor; t.focus({ preventScroll: true }); Shell.report(); }
    },
    init() {
      doc.addEventListener("keydown", () => { Shell.lastInput = "key"; }, true);
      doc.addEventListener("pointerdown", () => { Shell.lastInput = "pointer"; }, true);
      doc.addEventListener("pointerdown", (e) => {
        const c = this.cur; if (!c) return;
        if (c.card.contains(e.target) || c.anchor.contains(e.target)) return;
        this.close(true); Shell.report();
      }, true);
      doc.addEventListener("keydown", (e) => { if (e.key === "Escape" && this.cur) { e.preventDefault(); this.close(); } });
      addEventListener("blur", () => { if (this.cur && !this.cur.opts.sticky) { this.close(true); Shell.report(); } });
    },
  };

  // a menu is a popover of rows; arrow keys move, Enter acts
  function Menu(items) {
    const m = h("div", { cls: "menu", role: "menu" });
    for (const it of items) {
      if (it === "-") { m.append(h("div", { cls: "msep", role: "separator" })); continue; }
      if (it.head) { m.append(h("div", { cls: "mhead" }, it.icon || "", h("span", {}, it.head), it.note ? h("small", {}, it.note) : "")); continue; }
      const b = h("button", { cls: "mrow" + (it.danger ? " danger" : ""), role: "menuitem", disabled: it.disabled ? "" : null,
        on: { click: () => { Pop.close(); it.run && it.run(); } } },
        it.glyph ? glyph(it.glyph) : h("span", { cls: "gl" }), h("span", { cls: "mlabel" }, it.label), it.hint ? h("small", {}, it.hint) : "");
      m.append(b);
    }
    m.addEventListener("keydown", (e) => {
      const rows = [...m.querySelectorAll(".mrow:not([disabled])")];
      const i = rows.indexOf(doc.activeElement);
      if (e.key === "ArrowDown") { e.preventDefault(); (rows[(i + 1) % rows.length] || rows[0]).focus(); }
      if (e.key === "ArrowUp") { e.preventDefault(); (rows[(i - 1 + rows.length) % rows.length] || rows[0]).focus(); }
    });
    return m;
  }

  // a roving toolbar: one tab stop, arrows move between the buttons
  function roving(container, selector = "button") {
    const items = () => [...container.querySelectorAll(selector)].filter((b) => !b.disabled && b.offsetParent !== null);
    const sync = (cur) => items().forEach((b) => b.setAttribute("tabindex", b === cur ? "0" : "-1"));
    container.addEventListener("keydown", (e) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key)) return;
      const list = items(), i = list.indexOf(doc.activeElement);
      if (i < 0) return;
      e.preventDefault();
      const n = e.key === "Home" ? 0 : e.key === "End" ? list.length - 1 : (i + (e.key === "ArrowRight" ? 1 : -1) + list.length) % list.length;
      list[n].focus();
    });
    container.addEventListener("focusin", (e) => { if (e.target.matches(selector)) sync(e.target); });
    return { refresh() { const list = items(); const cur = list.find((b) => b.getAttribute("tabindex") === "0") || list[0]; sync(cur); } };
  }

  const toast = (text) => {
    let t = $("#live");
    if (!t) { t = h("div", { id: "live", role: "status", "aria-live": "polite", cls: "toast" }); doc.body.append(t); }
    t.textContent = text; t.classList.add("on");
    clearTimeout(toast.t); toast.t = setTimeout(() => { t.classList.remove("on"); Shell.report(); }, 3600);
    Shell.report();
  };
  const ran = async (p) => { const r = await p; if (r && (r.ok === false || /^refused/.test(r.text || ""))) toast((r.text || "That did not work").replace(/^refused:?\s*/, "")); return r; };

  // ------------------------------------------------------------------------------------------------ the top bar
  const fmt = {
    time: (d) => d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }).replace(/\s?([AP]M)$/i, " $1"),
    date: (d) => d.toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" }),
    long: (d) => d.toLocaleDateString([], { weekday: "long", year: "numeric", month: "long", day: "numeric" }),
  };

  const Top = {
    state: { wins: [], pins: [], sys: {}, media: null, notes: [], jeff: { state: "here" }, settings: {}, armed: false },
    parts: {},
    async build() {
      const S = this.state;
      const rail = h("header", { cls: "rail", role: "toolbar", "aria-label": "Agora top bar" });
      const mk = (cls, label, ...kids) => h("button", { cls: "btn " + cls, "aria-label": label, "aria-haspopup": "dialog", "aria-expanded": "false" }, ...kids);
      const P = this.parts;
      P.mark = mk("mark", "Agora launcher", Icon("agora:agora", "Agora", "bar"));
      P.focus = mk("focus", "Focused app", h("span", { cls: "fi" }), h("span", { cls: "fn" }));
      P.clock = mk("clock", "Calendar and notifications", h("b", { cls: "t" }), h("span", { cls: "d" }));
      P.bell = mk("bell", "Notifications", glyph("bell"), h("i", { cls: "badge" }));
      P.media = mk("media", "Media", h("span", { cls: "art" }), h("span", { cls: "mt" }));
      P.cpu = h("span", { cls: "read", "aria-hidden": "true" });
      P.mem = h("span", { cls: "read", "aria-hidden": "true" });
      P.qs = mk("qs", "Quick settings", glyph("wifi", "q-net"), glyph("volume", "q-vol"), h("span", { cls: "q-bat" }, glyph("battery", "q-batg"), h("span", { cls: "q-pct" })));
      P.jeff = mk("jeff", "JEFF", h("span", { cls: "dot" }), h("span", { cls: "jn" }, "JEFF"));
      P.off = h("button", { cls: "btn off", "aria-label": "Turn the desktop off (press twice)", "aria-pressed": "false" }, glyph("power"));
      P.spaces = h("div", { cls: "spaces", role: "group", "aria-label": "Spaces" });

      const left = h("div", { cls: "isle left", role: "group", "aria-label": "Launcher and app" }, P.mark, P.spaces, P.focus);
      const mid = h("div", { cls: "isle mid", role: "group", "aria-label": "Date and time" }, P.clock);
      const right = h("div", { cls: "isle right", role: "group", "aria-label": "Status" }, P.cpu, P.mem, P.bell, P.media, P.qs, P.jeff, P.off);
      rail.append(left, mid, right);
      doc.body.append(rail);
      this.rail = rail;
      this.rov = roving(rail);

      P.mark.onclick = () => this.launcher();
      P.focus.onclick = () => this.appMenu();
      P.clock.onclick = () => this.calendar();
      P.bell.onclick = () => this.inbox();
      P.media.onclick = () => this.mediaPop();
      P.qs.onclick = () => this.quick();
      P.jeff.onclick = () => this.jeffPop();
      P.off.onclick = () => this.offPress();
      doc.addEventListener("keydown", (e) => { if (e.altKey && e.key === " ") { e.preventDefault(); P.mark.click(); } });
      this.tick();
      setInterval(() => this.tick(), 1000);
      await this.refresh();
      setInterval(() => this.refresh(), 2500);
      setInterval(() => this.refreshSlow(), 4000);
      this.rov.refresh();
    },
    tick() {
      const d = new Date(), P = this.parts;
      const t = fmt.time(d), dd = fmt.date(d);
      if (P.clock.firstChild.textContent !== t) P.clock.firstChild.textContent = t;
      if (P.clock.lastChild.textContent !== dd) P.clock.lastChild.textContent = dd;
      P.clock.setAttribute("aria-label", `Calendar and notifications. ${fmt.long(d)}, ${t}`);
    },
    async refresh() {
      const S = this.state;
      const [wins, sys, media] = await Promise.all([Data.windows(), Data.system(), Data.media()]);
      S.wins = wins; S.sys = sys; S.media = media;
      this.paint();
    },
    async refreshSlow() {
      const S = this.state;
      [S.settings, S.notes, S.jeff] = await Promise.all([Data.settings(), Data.notifications(), Data.jeff()]);
      this.paint();
    },
    paint() {
      const S = this.state, P = this.parts;
      // focused app
      let f = S.wins.find((w) => w.focused) || null;
      if (f) this.lastKey = f.key; else f = S.wins.find((w) => w.key === this.lastKey) || null;   // while a bar has the focus, the app before it stays shown
      this.focused = f;
      P.focus.hidden = !f;
      if (f) {
        P.focus.firstChild.replaceChildren(Icon(f.icon, f.app, "bar"));
        P.focus.lastChild.textContent = f.app;
        P.focus.setAttribute("aria-label", `${f.app}, focused app. Open its window menu`);
      }
      // notifications
      const unread = S.notes.filter((n) => n.unread !== "no" && n.read !== "yes").length;
      P.bell.classList.toggle("has", unread > 0);
      P.bell.querySelector(".badge").textContent = unread > 9 ? "9+" : unread || "";
      P.bell.setAttribute("aria-label", unread ? `Notifications, ${unread} unread` : "Notifications, none unread");
      // media
      const m = S.media;
      P.media.hidden = !m;
      if (m) {
        const art = P.media.querySelector(".art");
        art.replaceChildren(m.art ? h("img", { src: m.art, alt: "" }) : glyph("play"));
        P.media.querySelector(".mt").textContent = m.title || "";
        P.media.classList.toggle("playing", !!m.playing);
        P.media.setAttribute("aria-label", `Media: ${m.title || "nothing"}${m.artist ? " by " + m.artist : ""}, ${m.playing ? "playing" : "paused"}`);
      }
      // quick settings cluster
      const vol = S.sys.volume, bat = S.sys.battery, net = S.sys.network;
      const vv = vol && vol.value ? vol.value : "";
      const volPct = parseInt(vv, 10);
      const qv = P.qs.querySelector(".q-vol");
      qv.replaceWith(Object.assign(glyph(vv === "muted" ? "volume-x" : volPct < 34 ? "volume-low" : "volume", "q-vol"), {}));
      const hasBat = bat && bat.value;
      P.qs.querySelector(".q-bat").hidden = !hasBat;
      if (hasBat) {
        P.qs.querySelector(".q-pct").textContent = bat.value;
        P.qs.querySelector(".q-batg").replaceWith(glyph(/charging/.test(bat.detail || "") ? "battery-charging" : "battery", "q-batg"));
      }
      P.qs.dataset.low = hasBat && parseInt(bat.value, 10) <= 15 && !/charging/.test(bat.detail || "") ? "yes" : "no";
      P.qs.setAttribute("aria-label", "Quick settings. " + [
        net ? "Network connected" : "Network unknown", vol ? (vv === "muted" ? "volume muted" : `volume ${vv}`) : "",
        hasBat ? `battery ${bat.value}${/charging/.test(bat.detail || "") ? ", charging" : ""}` : ""].filter(Boolean).join(", "));
      // optional readings, off unless the settings say so
      const on = (k) => /^(yes|on|true|1)$/i.test(String(S.settings["show_" + k] || ""));
      P.cpu.hidden = !(on("cpu") && S.sys.cpu); P.mem.hidden = !(on("memory") && S.sys.memory);
      if (!P.cpu.hidden) P.cpu.textContent = "CPU " + S.sys.cpu.value;
      if (!P.mem.hidden) P.mem.textContent = "RAM " + S.sys.memory.value;
      // JEFF
      const j = S.jeff || {};
      P.jeff.dataset.state = j.state || "here";
      P.jeff.setAttribute("aria-label", `JEFF is ${j.state || "here"}${j.note ? ": " + j.note : ""}. Open JEFF`);
      // spaces: only when there is more than one
      const spaces = [...new Set(S.wins.map((w) => w.space).filter(Boolean))];
      P.spaces.hidden = spaces.length < 2;
      P.spaces.replaceChildren(...spaces.map((s, i) => h("button", { cls: "btn chip", "aria-label": `Space ${s}`, on: { click: () => Data.act(`wm.space ${s}`) } }, String(i + 1))));
      this.rov.refresh();
      Shell.report();
    },

    // --- popovers
    async launcher() {
      const S = this.state;
      const lenses = await Data.lensNames();
      const names = (S.settings.dock_apps || "lines,help,board,taskboard,appearance,feed").split(/[ ,]+/).filter(Boolean)
        .filter((n) => ["lines", "help", "thing", "tasks"].includes(n) || lenses.has(n) || window.__fx);
      const pins = await Data.pins();
      const entries = [
        ...names.filter((n) => AGORA_APPS[n]).map((n) => ({ name: AGORA_APPS[n][0], icon: "agora:" + n, line: AGORA_APPS[n][1] })),
        ...pins.map((p) => ({ name: p.label || p.name || "Pinned", icon: p.path ? "exe:" + p.path : "agora:" + appOf(opensLens(p.does)), line: p.does || `window.launch path=${p.path}` })),
      ];
      const input = h("input", { type: "text", placeholder: "Open an app, or say a line", "aria-label": "Open an app or say a line", autocomplete: "off", spellcheck: "false", "data-autofocus": "" });
      const grid = h("div", { cls: "apps", role: "list" });
      const draw = () => {
        const t = input.value.trim().toLowerCase();
        const shown = entries.filter((e) => !t || e.name.toLowerCase().includes(t));
        grid.replaceChildren(...shown.map((e) => h("button", { cls: "app", role: "listitem", "aria-label": `Open ${e.name}`, on: { click: () => { Pop.close(); ran(Data.act(e.line)); } } }, Icon(e.icon, e.name, 40), h("span", {}, e.name))));
        draw.first = shown[0];
        if (!shown.length) grid.append(h("p", { cls: "empty" }, t ? `Press Enter to say "${input.value.trim()}" as a line.` : "Nothing here yet."));
      };
      input.oninput = draw;
      input.onkeydown = (e) => {
        if (e.key === "Enter") { e.preventDefault(); const t = input.value.trim(); Pop.close(); if (draw.first) ran(Data.act(draw.first.line)); else if (t) ran(Data.act(t)); }
        if (e.key === "ArrowDown") { e.preventDefault(); const b = grid.querySelector("button"); b && b.focus(); }
      };
      grid.addEventListener("keydown", (e) => {
        const bs = [...grid.querySelectorAll("button")], i = bs.indexOf(doc.activeElement);
        const cols = Math.max(1, Math.floor(grid.clientWidth / 92));
        const to = { ArrowRight: i + 1, ArrowLeft: i - 1, ArrowDown: i + cols, ArrowUp: i - cols }[e.key];
        if (to !== undefined) { e.preventDefault(); if (to < 0) input.focus(); else (bs[to] || bs[i]).focus(); }
      });
      draw();
      Pop.open("launcher", this.parts.mark, () => h("div", { cls: "launch" },
        h("div", { cls: "search" }, glyph("search"), input), grid,
        h("div", { cls: "foot" },
          h("button", { cls: "link", on: { click: () => { Pop.close(); ran(Data.act("window.open lines")); } } }, glyph("terminal"), "Lines"),
          h("button", { cls: "link", on: { click: () => { Pop.close(); ran(Data.act("window.start")); } } }, glyph("grid"), "Windows Start"))),
        { label: "Launcher", align: "left", cls: "wide" });
    },
    appMenu() {
      const f = this.focused; if (!f) return;
      const pinned = f.state === "pinned";
      const inDock = !!(this.state.pins || []).find((p) => (p.path || "").toLowerCase() === (f.exe || "").toLowerCase() && f.exe);
      Pop.open("app", this.parts.focus, () => Menu([
        { head: f.app, icon: Icon(f.icon, f.app, 26), note: f.managed === false && Data.wmOK ? "left alone" : "" },
        "-",
        { label: pinned ? "Unpin from its place" : "Pin in place", glyph: pinned ? "pin-off" : "pin", run: () => ran(Data.act(`${pinned ? "wm.unpin" : "wm.pin"} ${f.key}`)), disabled: !Data.wmOK && !f.agora, hint: Data.wmOK ? "" : "needs the window manager" },
        { label: "Minimise", glyph: "minus", run: () => ran(Data.minimise(f)) },
        { label: "Close", glyph: "x", danger: true, run: () => ran(Data.close(f)) },
        "-",
        { label: "Keep in dock", glyph: "grid", run: () => Dock.keep(f), disabled: !f.exe && !f.agora },
        ...(Data.wmOK && f.exe ? [{ label: f.managed === false ? "Arrange this app again" : "Leave this app alone", glyph: "settings", run: () => ran(Data.act(`${f.managed === false ? "wm.manage" : "wm.leave-alone"} ${f.app}`)) }] : []),
      ]), { label: `${f.app} window menu`, align: "left", cls: "narrow" });
    },
    calendar() {
      const S = this.state;
      let view = new Date(); view.setDate(1);
      const box = h("div", { cls: "cal" });
      const draw = () => {
        const today = new Date(), y = view.getFullYear(), m = view.getMonth();
        const first = new Date(y, m, 1).getDay(), days = new Date(y, m + 1, 0).getDate();
        const cells = [];
        for (let i = 0; i < first; i++) cells.push(h("i"));
        for (let d = 1; d <= days; d++) {
          const is = d === today.getDate() && m === today.getMonth() && y === today.getFullYear();
          cells.push(h("span", { cls: "day" + (is ? " today" : ""), "aria-current": is ? "date" : null, "aria-label": new Date(y, m, d).toLocaleDateString([], { weekday: "long", month: "long", day: "numeric" }) }, String(d)));
        }
        const dows = [...Array(7)].map((_, i) => new Date(2024, 0, 7 + i).toLocaleDateString([], { weekday: "narrow" }));
        box.replaceChildren(
          h("div", { cls: "calhead" },
            h("b", {}, view.toLocaleDateString([], { month: "long", year: "numeric" })),
            h("span", { cls: "grow" }),
            h("button", { cls: "btn sm", "aria-label": "Previous month", on: { click: () => { view = new Date(y, m - 1, 1); draw(); } } }, glyph("left")),
            h("button", { cls: "btn sm", "aria-label": "Next month", on: { click: () => { view = new Date(y, m + 1, 1); draw(); } } }, glyph("right"))),
          h("div", { cls: "grid7", role: "grid", "aria-label": view.toLocaleDateString([], { month: "long", year: "numeric" }) }, dows.map((d) => h("em", {}, d)), cells));
      };
      draw();
      const n = S.notes.length;
      Pop.open("clock", this.parts.clock, () => h("div", { cls: "calwrap" },
        h("div", { cls: "bigtime" }, h("b", {}, fmt.time(new Date())), h("span", {}, fmt.long(new Date()))), box,
        h("button", { cls: "link wide", on: { click: () => { Pop.close(); this.inbox(); } } }, glyph("bell"), n ? `${n} notification${n === 1 ? "" : "s"}` : "No notifications")),
        { label: "Calendar and notifications", cls: "cal-pop" });
    },
    inbox() {
      const S = this.state;
      Pop.open("bell", this.parts.bell, () => h("div", { cls: "inbox" },
        h("div", { cls: "ph" }, h("b", {}, "Notifications"), h("span", { cls: "grow" }),
          S.notes.length ? h("button", { cls: "link", on: { click: () => { Data.act("notice.clear"); toast("Cleared"); Pop.close(); } } }, "Clear") : ""),
        S.notes.length ? h("ul", {}, S.notes.slice(0, 8).map((n) => h("li", { cls: n.unread === "no" ? "" : "new" }, h("span", { cls: "dot" }), h("span", {}, n.text || n.title || "Something happened"), n.at ? h("small", {}, n.at) : "")))
          : h("p", { cls: "empty" }, "You are all caught up.")),
        { label: "Notifications", align: "right", cls: "narrow" });
    },
    mediaPop() {
      const m = this.state.media; if (!m) return;
      const act = (w) => ran(Data.act(w));
      Pop.open("media", this.parts.media, () => h("div", { cls: "mediapop" },
        h("div", { cls: "cover" }, m.art ? h("img", { src: m.art, alt: "" }) : glyph("play")),
        h("div", { cls: "meta" }, h("b", {}, m.title), h("span", {}, m.artist || m.player || ""), h("small", {}, m.player ? `${m.player} · ${m.playing ? "playing" : "paused"}` : "")),
        h("div", { cls: "ctl" },
          h("button", { cls: "btn", "aria-label": "Previous", on: { click: () => act("media.prev") } }, glyph("prev")),
          h("button", { cls: "btn big", "aria-label": m.playing ? "Pause" : "Play", "data-autofocus": "", on: { click: () => act("media.play") } }, glyph(m.playing ? "pause" : "play")),
          h("button", { cls: "btn", "aria-label": "Next", on: { click: () => act("media.next") } }, glyph("next"))),
        m.duration ? h("div", { cls: "prog", role: "progressbar", "aria-valuemin": "0", "aria-valuemax": "100", "aria-valuenow": String(Math.round(100 * (m.position || 0) / m.duration)) }, h("i", { style: { width: Math.min(100, 100 * (m.position || 0) / m.duration) + "%" } })) : ""),
        { label: "Media", align: "right", cls: "narrow" });
    },
    quick() {
      const S = this.state, sys = S.sys, st = S.settings;
      const row = (g, name, value, detail, which) => h("button", { cls: "qrow", on: { click: () => { Pop.close(); ran(Data.act(`window.settings which=${which}`)); } }, "aria-label": `${name}: ${value}. Open ${name.toLowerCase()} settings` },
        h("span", { cls: "qg" }, glyph(g)), h("span", { cls: "qt" }, h("b", {}, name), h("small", {}, detail || "")), h("span", { cls: "qv" }, value), glyph("right", "go"));
      const vol = sys.volume, bat = sys.battery, net = sys.network;
      const pct = vol && parseInt(vol.value, 10);
      const toggle = (key, label, on) => h("button", { cls: "sw", role: "switch", "aria-checked": on ? "true" : "false", "aria-label": label,
        on: { click: async (e) => { const b = e.currentTarget; const next = b.getAttribute("aria-checked") !== "true"; b.setAttribute("aria-checked", String(next));
          const id = S.settings.id; await ran(Data.act(id ? `set ${id} show_${key}=${next ? "yes" : "no"}` : `make kind=shell-settings show_${key}=${next ? "yes" : "no"}`)); this.refreshSlow(); } } },
        h("span", {}, label), h("i", {}));
      const yes = (k) => /^(yes|on|true|1)$/i.test(String(st["show_" + k] || ""));
      Pop.open("quick", this.parts.qs, () => h("div", { cls: "quick" },
        row(net ? "wifi" : "wifi-off", "Network", net ? "Online" : "Unknown", net ? `${net.value} ${net.detail || ""}`.trim() : "", "network"),
        row(vol && vol.value === "muted" ? "volume-x" : "volume", "Sound", vol ? vol.value : "n/a", vol && vol.value !== "muted" && pct >= 0 ? "Output volume" : "", "volume"),
        vol && pct >= 0 ? h("div", { cls: "meter", role: "meter", "aria-label": "Volume", "aria-valuemin": "0", "aria-valuemax": "100", "aria-valuenow": String(pct) }, h("i", { style: { width: pct + "%" } })) : "",
        ...(bat && bat.value ? [row(/charging/.test(bat.detail || "") ? "battery-charging" : "battery", "Battery", bat.value, bat.detail || "", "battery")] : []),
        h("div", { cls: "msep" }),
        h("div", { cls: "sub" }, "Show in the bar"),
        toggle("cpu", "CPU", yes("cpu")), toggle("memory", "Memory", yes("memory"))),
        { label: "Quick settings", align: "right", cls: "narrow" });
    },
    jeffPop() {
      const j = this.state.jeff || {};
      Pop.open("jeff", this.parts.jeff, () => h("div", { cls: "jeffpop" },
        h("div", { cls: "who" }, h("span", { cls: "dot big", "data-state": j.state }), h("div", {}, h("b", {}, "JEFF"), h("small", {}, ({ here: "Here with you", busy: "Working on something", away: "Away" })[j.state] || j.state || "Here"))),
        j.note ? h("p", {}, j.note) : "",
        h("button", { cls: "link wide", "data-autofocus": "", on: { click: () => { Pop.close(); ran(Data.act(this.state.settings.jeff_open || "window.open lines")); } } }, glyph("message"), "Open the conversation")),
        { label: "JEFF", align: "right", cls: "narrow" });
    },
    offPress() {
      const b = this.parts.off, S = this.state;
      if (!S.armed) {
        S.armed = true; b.classList.add("armed"); b.setAttribute("aria-pressed", "true");
        b.setAttribute("aria-label", "Press again to turn the desktop off");
        toast("Press the power button again to turn the Agora desktop off");
        clearTimeout(S.armT);
        S.armT = setTimeout(() => { S.armed = false; b.classList.remove("armed"); b.setAttribute("aria-pressed", "false"); b.setAttribute("aria-label", "Turn the desktop off (press twice)"); }, 4000);
        return;
      }
      clearTimeout(S.armT); S.armed = false;
      (async () => { if (Data.wmOK) await Data.act("wm.mode off"); await Data.act("off window"); })();
    },
    shape() {
      const r = this.rail.getBoundingClientRect(), out = [{ x: 0, y: 0, w: innerWidth, h: Math.ceil(r.bottom), r: 0 }];
      for (const el of doc.querySelectorAll(".pop.in, .toast.on")) { const b = el.getBoundingClientRect(); out.push({ x: b.left, y: b.top, w: b.width, h: b.height, r: el.classList.contains("toast") ? 12 : parseFloat(getComputedStyle(el).borderTopLeftRadius) || 0 }); }
      return { reserve: Math.ceil(r.bottom), shape: out };
    },
  };

  // ------------------------------------------------------------------------------------------------ the dock
  const Dock = {
    state: { wins: [], pins: [], lenses: new Set(), settings: {}, order: [], hover: null },
    async build() {
      const pill = h("nav", { cls: "pill", role: "toolbar", "aria-label": "Dock", "aria-orientation": "horizontal" });
      this.pill = pill;
      doc.body.append(pill);
      this.rov = roving(pill, ".item");
      pill.addEventListener("keydown", (e) => {
        const it = doc.activeElement && doc.activeElement.closest && doc.activeElement.closest(".item");
        if (!it) return;
        if (e.key === "ContextMenu" || (e.shiftKey && e.key === "F10")) { e.preventDefault(); this.menu(it); }
        if (e.key === "ArrowUp") { e.preventDefault(); this.hover(it, true); }
      });
      await this.refresh();
      setInterval(() => this.refresh(), 2500);       // 1 s saturated the kernel with wm.windows (26 Oct)
      addEventListener("resize", () => Shell.report());
    },
    async refresh() {
      const S = this.state;
      const [wins, pins, lenses, settings] = await Promise.all([Data.windows(), Data.pins(), Data.lensNames(), Data.settings()]);
      S.wins = wins; S.pins = pins; S.lenses = lenses; S.settings = settings;
      const f = wins.find((w) => w.focused);          // clicking the dock activates the dock: remember who was in front before
      S.noFocus = !f; if (f) S.lastFront = f.key;
      this.paint();
    },
    // one item per app: pinned apps first (in the order they were pinned), then running ones in the order they appeared,
    // then Agora's own windows, then the overview. The order is remembered so icons never jump.
    groups() {
      const S = this.state, g = new Map();
      const keyOf = (w) => w.agora ? "agora:" + w.key : (w.exe || w.app).toLowerCase();
      for (const w of S.wins) {
        const k = keyOf(w);
        if (!g.has(k)) g.set(k, { id: k, app: w.app, exe: w.exe, icon: w.icon, wins: [], agora: !!w.agora, pin: null });
        g.get(k).wins.push(w);
      }
      const apps = (S.settings.dock_apps || "lines,help,board,taskboard,appearance,feed").split(/[ ,]+/).filter(Boolean)
        .filter((n) => AGORA_APPS[n] && (["viewer", "lines", "help", "thing", "tasks"].includes(n) || S.lenses.has(n) || window.__fx));
      const pinned = [];
      for (const n of apps) pinned.push({ id: "app:" + n, app: AGORA_APPS[n][0], exe: "", icon: "agora:" + n, wins: [], line: AGORA_APPS[n][1], launcher: n, pin: { id: "" } });
      const launched = new Set(pinned.map((p) => p.line));
      for (const p of S.pins) {
        const exe = p.path || "";
        if (!exe && launched.has(p.does)) continue;           // the same app as a launcher already in the dock
        pinned.push({ id: exe ? exe.toLowerCase() : "pin:" + p.id, app: p.label || p.name || (exe.split(/[\\/]/).pop() || "Pinned").replace(/\.exe$/i, ""), exe, icon: exe ? "exe:" + exe : "agora:" + appOf(opensLens(p.does)), wins: [], line: p.does || `window.launch path=${exe}`, pin: p });
      }
      // a running Agora window shares the slot of whatever opens it (a launcher, or a button that says window.open)
      const slotted = new Set();
      for (const p of pinned) {
        const lens = opensLens(p.line);
        const k = lens ? [...g.keys()].find((x) => x.startsWith("agora:") && !slotted.has(x) && g.get(x).wins.some((w) => w.shows === lens)) : p.id;
        const run = k && g.get(k);
        if (run && !slotted.has(k)) { Object.assign(p, { wins: run.wins }); slotted.add(k); }
      }
      const running = [...g.values()].filter((x) => !slotted.has(x.id) && !x.agora);
      const own = [...g.values()].filter((x) => !slotted.has(x.id) && x.agora);
      const all = [...pinned, ...running, ...own];
      // remembered order among the unpinned ones
      const ord = S.order;
      for (const x of all) if (!ord.includes(x.id)) ord.push(x.id);
      const pinIds = new Set(pinned.map((x) => x.id));
      const rest = all.filter((x) => !pinIds.has(x.id)).sort((a, b) => ord.indexOf(a.id) - ord.indexOf(b.id));
      return [...pinned, ...rest];
    },
    paint() {
      const S = this.state, pill = this.pill;
      const keep = doc.activeElement && doc.activeElement.dataset && doc.activeElement.dataset.id;
      const items = this.groups();
      this.items = items;
      const nodes = [];
      nodes.push(this.brand());
      nodes.push(h("i", { cls: "sep", "aria-hidden": "true" }));
      items.forEach((x) => nodes.push(this.item(x)));
      nodes.push(h("i", { cls: "sep", "aria-hidden": "true" }));
      nodes.push(this.overview());
      pill.replaceChildren(...nodes);
      if (keep) { const k = pill.querySelector(`[data-id="${CSS.escape(keep)}"]`); k && k.focus({ preventScroll: true }); }
      this.rov.refresh();
      const f = items.find((x) => x.wins.some((w) => w.focused));
      pill.setAttribute("aria-label", `Dock, ${items.filter((x) => x.wins.length).length} apps running${f ? ", " + f.app + " in front" : ""}`);
      Shell.report();
    },
    brand() {
      const b = h("button", { cls: "item brand", "data-id": "brand", "aria-label": "Agora launcher", "aria-haspopup": "dialog", "aria-expanded": "false", tabindex: "-1",
        on: { click: () => this.launcher(b) } }, Icon("agora:agora", "Agora", "dock"));
      return b;
    },
    overview() {
      return h("button", { cls: "item overview", "data-id": "overview", "aria-label": "Overview: all windows", tabindex: "-1",
        on: { click: () => ran(Data.act("window.open tasks")) } }, Icon("agora:overview", "Overview", "dock"));
    },
    item(x) {
      const n = x.wins.length, front = x.wins.some((w) => w.focused), allMin = n > 0 && x.wins.every((w) => w.state === "minimised");
      const state = !n ? "closed" : front ? "front" : allMin ? "minimised" : "open";
      const b = h("button", { cls: `item ${state}`, "data-id": x.id, tabindex: "-1", "aria-label": `${x.app}${n ? `, ${n} window${n > 1 ? "s" : ""}${front ? ", in front" : allMin ? ", minimised" : ""}` : ", not running"}`,
        "aria-haspopup": "menu", draggable: "false",
        on: {
          click: () => this.click(x),
          auxclick: (e) => { if (e.button === 1) { e.preventDefault(); this.fresh(x); } },
          contextmenu: (e) => { e.preventDefault(); this.menu(b, x); },
          pointerenter: () => this.hover(b, false, x), pointerleave: () => this.unhover(),
          focus: () => { if (b.matches(":focus-visible")) this.hover(b, false, x); }, blur: () => this.unhover(true),
          mousedown: (e) => { if (e.button === 1) e.preventDefault(); },
        } }, Icon(x.icon, x.app, "dock"), n > 1 ? h("i", { cls: "count", "aria-hidden": "true" }, String(n)) : "", h("i", { cls: "mark", "aria-hidden": "true" }));
      b.__x = x;
      return b;
    },
    // click: focus; minimise if it is already in front; launch if it is not running
    async click(x) {
      const S = this.state;
      this.unhover(true);
      if (!x.wins.length) return ran(Data.act(x.line || `window.launch path=${x.exe}`));
      const front = x.wins.find((w) => w.focused) || x.wins.find((w) => w.key === S.lastFront && S.noFocus);
      if (front) return ran(Data.minimise(front));
      const w = x.wins.find((v) => v.state !== "minimised") || x.wins[0];
      return ran(Data.focus(w));
    },
    fresh(x) {
      if (x.launcher) return ran(Data.act(`${x.line} new=yes`));
      if (x.exe) return ran(Data.act(`window.launch path=${x.exe}`));
      if (x.wins[0] && x.wins[0].agora) return ran(Data.act(`window.open ${x.wins[0].shows} new=yes`));
    },
    async keep(f) {
      if (f.exe) { await ran(Data.act(`make kind=button bar=taskbar label=${JSON.stringify(f.app)} path=${JSON.stringify(f.exe)} does=${JSON.stringify("window.launch path=" + f.exe)}`)); toast(`${f.app} stays in the dock`); this.refresh(); }
    },
    async unkeep(x) { if (x.pin && x.pin.id) { await ran(Data.act(`forget ${x.pin.id}`)); toast(`${x.app} left the dock`); this.refresh(); } },
    menu(b, x) {
      x = x || b.__x; if (!x) return;
      this.unhover(true);
      const items = [{ head: x.app, icon: Icon(x.icon, x.app, 26), note: x.wins.length ? `${x.wins.length} window${x.wins.length > 1 ? "s" : ""}` : "not running" }];
      if (x.wins.length) {
        items.push("-");
        x.wins.slice(0, 6).forEach((w, i) => items.push({ label: w.title || `${x.app} window ${i + 1}`, glyph: w.focused ? "check" : "monitor", hint: w.state === "minimised" ? "minimised" : w.state === "pinned" ? "pinned" : "", run: () => ran(Data.focus(w)) }));
        if (x.wins.length > 6) items.push({ label: `${x.wins.length - 6} more`, disabled: true });
      }
      items.push("-");
      items.push({ label: x.wins.length ? "New window" : "Open", glyph: "external", run: () => this.fresh(x) || ran(Data.act(x.line || `window.launch path=${x.exe}`)) });
      if (x.pin) { if (x.pin.id || x.launcher) items.push({ label: "Remove from dock", glyph: "pin-off", run: () => (x.launcher ? toast("Agora apps are listed in the dock settings") : this.unkeep(x)), disabled: !!x.launcher }); }
      else if (x.exe) items.push({ label: "Keep in dock", glyph: "pin", run: () => this.keep({ app: x.app, exe: x.exe }) });
      const front = x.wins.find((w) => w.focused) || x.wins[0];
      if (front && Data.wmOK && !front.agora) items.push({ label: front.state === "pinned" ? "Unpin from its place" : "Pin in place", glyph: front.state === "pinned" ? "pin-off" : "pin", run: () => ran(Data.act(`${front.state === "pinned" ? "wm.unpin" : "wm.pin"} ${front.key}`)) });
      if (x.wins.length) {
        items.push("-");
        items.push({ label: x.wins.length > 1 ? "Close all windows" : "Close window", glyph: "x", danger: true, run: () => x.wins.forEach((w) => ran(Data.close(w))) });
      }
      Pop.open("menu", b, () => Menu(items), { label: `${x.app} menu`, above: true, gap: 12, cls: "narrow", onClose: () => this.rov.refresh() });
    },
    launcher(anchor) {
      Pop.open("launcher", anchor, () => {
        const entries = this.items.filter((x) => x.launcher || x.exe);
        const grid = h("div", { cls: "apps", role: "list" }, entries.map((e) => h("button", { cls: "app", role: "listitem", "aria-label": `Open ${e.app}`, on: { click: () => { Pop.close(); this.click(e); } } }, Icon(e.icon, e.app, 40), h("span", {}, e.app))));
        return h("div", { cls: "launch" }, grid, h("div", { cls: "foot" },
          h("button", { cls: "link", "data-autofocus": "", on: { click: () => { Pop.close(); ran(Data.act("window.open lines")); } } }, glyph("terminal"), "Lines"),
          h("button", { cls: "link", on: { click: () => { Pop.close(); ran(Data.act("window.start")); } } }, glyph("grid"), "Windows Start")));
      }, { label: "Launcher", above: true, gap: 12, cls: "wide" });
    },
    // hover: after a breath, a live preview of the app's windows. Titles are asked of the host now and never kept.
    hover(b, now, x) {
      x = x || b.__x;
      clearTimeout(this.ht);
      if (!x || !x.wins.length || (Pop.cur && Pop.cur.id === "menu")) return;
      this.ht = setTimeout(() => this.preview(b, x), now ? 0 : (window.__fx ? 30 : 380));
    },
    unhover(now) {
      clearTimeout(this.ht);
      const go = () => { this.closePreview(); };
      if (now) go(); else this.ht = setTimeout(go, 160);
    },
    async preview(b, x) {
      if (Pop.cur && Pop.cur.id === "menu") return;
      this.closePreview(true);
      const wins = x.wins.slice(0, 4);
      const info = await Promise.all(wins.map((w) => Data.title(w.key).then((t) => t || {})));
      const tile = (w, i) => {
        const t = info[i] || {};
        const th = h("div", { cls: "th", "data-key": w.key, "data-hwnd": t.hwnd || (/^\d+$/.test(w.key) ? w.key : "") },
          t.preview ? h("img", { src: t.preview, alt: "" }) : h("div", { cls: "ph" }, Icon(x.icon, x.app, 56)));
        return h("button", { cls: "tile" + (w.focused ? " front" : ""), "aria-label": `${t.title || x.app}${w.state === "minimised" ? ", minimised" : ""}. Switch to this window`,
          on: { click: () => { this.closePreview(true); ran(Data.focus(w)); } } },
          h("div", { cls: "tt" }, Icon(x.icon, x.app, 16), h("span", {}, t.title || w.title || x.app), h("i", { cls: "x", role: "button", "aria-label": "Close this window", on: { click: (e) => { e.stopPropagation(); ran(Data.close(w)); this.closePreview(true); } } }, glyph("x"))), th);
      };
      const card = h("div", { cls: "pop preview in", "data-pop": "preview", role: "group", "aria-label": `${x.app} windows`, on: { pointerenter: () => clearTimeout(this.ht), pointerleave: () => this.unhover() } },
        wins.map(tile));
      doc.body.append(card);
      this.pv = { card, b };
      const a = b.getBoundingClientRect(), w = card.offsetWidth;
      card.style.left = Math.max(10, Math.min(a.left + a.width / 2 - w / 2, innerWidth - w - 10)) + "px";
      card.style.top = Math.max(4, a.top - card.offsetHeight - 14) + "px";
      Shell.report();
      // ask the host for the real thing: one DWM thumbnail per tile, laid over the placeholder
      requestAnimationFrame(() => {
        const rects = [...card.querySelectorAll(".th")].map((t) => { const r = t.getBoundingClientRect(); return { hwnd: t.dataset.hwnd, key: t.dataset.key, x: r.left, y: r.top, w: r.width, h: r.height }; });
        Native.call("thumbs", JSON.stringify(rects), Native.dpr());
      });
    },
    closePreview(quiet) {
      if (!this.pv) return;
      this.pv.card.remove(); this.pv = null;
      Native.call("thumbs", "[]", Native.dpr());
      Shell.report();
    },
    shape() {
      // The window is solid over the pill and a little around it (its shadow), never further up than the strip the dock
      // reserves for itself: above that are other programs' windows, which this window must not cover.
      const p = this.pill.getBoundingClientRect(), go = parseFloat(css("--ag-gap-outer")) || 10, side = Math.min(go, 8);
      const pr = parseFloat(getComputedStyle(this.pill).borderTopLeftRadius) || 0;
      const out = [{ x: p.left - side, y: p.top - go, w: p.width + 2 * side, h: p.height + 2 * go + 2, r: Math.min(pr + go, (p.height + 2 * go) / 2) }];
      for (const el of doc.querySelectorAll(".pop.in, .toast.on")) { const b = el.getBoundingClientRect(); out.push({ x: b.left, y: b.top, w: b.width, h: b.height, r: parseFloat(getComputedStyle(el).borderTopLeftRadius) || 12 }); }
      return { reserve: Math.ceil(innerHeight - p.top + go), shape: out, pill: { x: p.left, y: p.top, w: p.width, h: p.height } };
    },
  };

  // ------------------------------------------------------------------------------------------------ the desktop layer
  const Desk = {
    async build() {
      doc.body.append(h("div", { cls: "dim", "aria-hidden": "true" }));
      doc.body.classList.add("desk");
    },
    shape() { return { reserve: 0, shape: [{ x: 0, y: 0, w: innerWidth, h: innerHeight, r: 0 }] }; },
  };

  // ------------------------------------------------------------------------------------------------ the component host
  // SHELL.md, "The bars as components": when the world has an on widget for this bar (shell-top, shell-dock) that holds
  // window.native, the page is only the wallpaper slice and the guarded painter frame (widget-host.js) in front of it.
  // Anything else (no widget, off, refused, no grant, or the frame stopping) paints the hand-written bar below instead.
  async function host(which) {
    const view = which === "top" ? "shell-top" : which === "dock" ? "shell-dock" : "";
    if (!view || q.get("fixture") || q.get("hand")) return Shell.start(which);   // the desktop layer, and the proof's own renders
    let widget = q.get("widget");
    if (!widget) {
      const r = await KD.see("rows widget name=" + view);
      const w = ((r && r.rows) || []).find((x) => x.on && x.component_lens && !x.forgotten);
      widget = w && w.id;
    }
    if (!widget) return Shell.start(which);
    doc.body.dataset.page = which;
    doc.body.classList.add("shell-host");
    // the frame is see-through only when it and this page agree on the colour scheme (else Chromium paints it opaque)
    root.style.setProperty("color-scheme", "normal", "important");
    if (q.get("hide")) doc.body.classList.add("hide");
    await Theme.init();
    Wall.init();
    KD.stream((ev) => { if (ev.word === "theme.changed") Theme.reload(); });
    doc.body.append(h("main", { id: "widget-surface", "aria-label": view === "shell-top" ? "Agora top bar" : "Agora dock" }));
    let fell = false;
    window.AGORA_SHELL = {
      page: which, widget, painted: false,
      fallback(text, painted) {
        if (fell) return;
        fell = true;
        console.warn("shell: the hand-written bar instead of the components:", text);
        window.__shellFallback = text;
        const s = $("#widget-surface"); if (s) s.remove();
        Shell.start(which);
        // a bar that was painting and stopped (a restart, a new version of its code) tries the components again
        if (painted) setTimeout(() => location.reload(), /changed|reopen/i.test(text || "") ? 3000 : 20000);
      },
    };
    for (const src of ["../theme-live.js", "../widget-host.js"]) {
      await new Promise((res) => { const s = h("script", { src }); s.onload = s.onerror = res; doc.body.append(s); });
    }
    window.__ready = true;
  }

  // ------------------------------------------------------------------------------------------------ page start
  let page = null, reportT = 0;
  const Shell = {
    q, h, glyph, Icon, Data, Theme, Pop, Menu, Native, Top, Dock, Desk, toast, fmt, host,
    report() {                       // tell the host (and the proof) where this window is solid and what strip it needs
      if (!page) return;
      cancelAnimationFrame(reportT);
      reportT = requestAnimationFrame(() => {
        const s = page.shape();
        window.__shape = s;
        Native.layout(s);
      });
    },
    async start(which) {
      if (page) return;
      page = which === "top" ? Top : which === "dock" ? Dock : Desk;
      doc.body.dataset.page = which;
      if (q.get("hide")) doc.body.classList.add("hide");          // the proof hides the parts to compare the wallpaper slice alone
      await Theme.init();
      Wall.init();
      Pop.init();
      Theme.listeners = [() => Shell.report()];
      KD.stream((ev) => {
        if (ev.word === "theme.changed") Theme.reload();
        else if (ev.word === "wm.changed" && page.refresh) page.refresh();
        else if ((ev.word === "window.opened" || ev.word === "world") && page.refresh) { clearTimeout(Shell.rt); Shell.rt = setTimeout(() => page.refresh(), 150); }
      });
      await page.build();
      this.report();
      window.__ready = true;
    },
  };
  return Shell;
})();

window.Shell = Shell;
