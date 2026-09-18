// core.js : the one shared substrate. OWNER: Wren (see OWNERS.md). Ask for changes with a to-wren note.
//
// The world lives in deskd (python deskd.py). This file is the only thing that talks to it.
//   Desk.snapshot            the last world snapshot (subjects, nodes, links, rules, scripts, clock, outline)
//   Desk.do(line)            EVERY change goes through here, as a desk command line. Returns {text, error}.
//   Desk.on(fn)              fn(snapshot, newEvents) after every refresh
//   Desk.registerApp(app)    app = { id, title, glyph, accepts(node, subject) -> bool, open(host, ctx), text(ctx) -> string }
//                            open() draws into `host` (a window body). text() returns what a text-only inhabitant
//                            would read for this window right now; the shell shows it on demand (the "as text" toggle).
//   Desk.children(id), Desk.node(id), Desk.subject(id), Desk.title(id)
//
// FOR APP OWNERS — the style. There is one style for the whole desktop and you never invent a colour:
//   el.className = Desk.style.role("card")       -> "r-card"; also "title" "body" "meta" "tag" "heading" "card.plain"
//   el.style.gap = Desk.style.var("gap")         -> "var(--t-gap)"; every token is a custom property --t-<name>
//   Desk.style.tokens                            -> the resolved tokens, if you must compute
//   Desk.style.look(thing)                       -> {role, css, layers, owner} : the resolved look AND why
// If a role you need does not exist, ask for it (to-wren). Do not write a hex colour into an app.
//
// FOR APP OWNERS — screens. An open window on a thing is a FACT IN THE WORLD: an appearance of that
// subject on your own `<actor> screen` surface, with the window's geometry. The other inhabitant can see
// what you have open, where it is, and how big. Nothing about that is view state.
//   Desk.screen()                                -> the surface id of your screen, or null until it exists
//   Desk.screenEnsure()                          -> creates it if absent, returns the id
//
// Law of the house: no app keeps state the world does not have, except what is honestly view state
// (scroll position, which window is in front), and an app may never change the world except through Desk.do.

const Desk = (() => {
  const q = new URLSearchParams(location.search);
  const session = q.get("session") || "desktop";
  const actor = (q.get("as") || "alex").toLowerCase();
  const apps = [], listeners = [], log = [];
  let snapshot = null, total = 0, offline = false;

  async function refresh() {
    try {
      const r = await fetch(`/api/snapshot?session=${session}&as=${actor}`);
      snapshot = await r.json(); offline = false;
    } catch (_) { offline = true; listeners.forEach(fn => snapshot && fn(snapshot, [])); return; }
    const fresh = [];
    if (snapshot.events_total > total && total > 0) {
      const e = await (await fetch(`/api/events?session=${session}&as=${actor}&since=${total}`)).json();
      fresh.push(...e.events);
    }
    total = snapshot.events_total;
    listeners.forEach(fn => fn(snapshot, fresh));
  }

  async function run(line) {
    const r = await (await fetch("/api/do", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session, as: actor, line }) })).json();
    log.push({ line, text: r.text, error: r.error, at: new Date() });
    await refresh();
    return r;
  }

  async function poll() {
    try {
      const e = await (await fetch(`/api/events?session=${session}&as=${actor}&since=${total}`)).json();
      offline = false;
      if (e.total !== total) await refresh();
    } catch (_) { offline = true; listeners.forEach(fn => snapshot && fn(snapshot, [])); }
    setTimeout(poll, 1500);
  }

  const nodes = () => snapshot ? snapshot.nodes : {};
  const SCREEN = `${actor} screen`;

  const api = {
    session, actor, apps, log,
    get snapshot() { return snapshot; },
    get offline() { return offline; },
    do: run, refresh,
    on: fn => listeners.push(fn),
    registerApp: app => { apps.push(app); listeners.forEach(fn => snapshot && fn(snapshot, [])); },
    node: id => nodes()[id],
    subject: id => snapshot.subjects[id],
    children: id => {   // tiled surfaces order by position along their axis; free surfaces by z (back to front)
      const p = nodes()[id], key = !p ? "z" : p.layout === "column" ? "y" : p.layout === "row" ? "x" : "z";
      return Object.values(nodes()).filter(n => n.parent === id).sort((a, b) => a[key] - b[key]);
    },
    title: id => { const n = nodes()[id]; return !n ? id : n.type === "surface" ? n.title : snapshot.subjects[n.subject].title; },

    screenName: SCREEN,
    screen() { const n = Object.values(nodes()).find(x => x.type === "surface" && x.title === SCREEN); return n ? n.id : null; },
    async screenEnsure() {
      let id = api.screen(); if (id) return id;
      const side = Object.values(nodes()).find(x => x.type === "surface" && (x.owner === actor || (x.title || "").toLowerCase() === actor))
                || Object.values(nodes()).find(x => x.type === "surface" && x.title === "Shared");
      if (!side) return null;
      await run(`do create ${side.id} kind=surface title="${SCREEN}" layout=free`);
      return api.screen();
    },

    style: {
      role: n => Style.roleClass(n),
      var: n => Style.varName(n),
      get tokens() { return Style.tokens; },
      look: (thing) => Style.look(thing, snapshot),
      present: n => Style.present(n),
    },

    start: async () => { await refresh(); poll(); },
  };
  return api;
})();
