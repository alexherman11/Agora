// core.js : the one shared substrate. OWNER: Jeff (host). Change it by asking in Studio talk, not by editing.
//
// The world lives in deskd (python deskd.py). This file is the only thing that talks to it.
//   Desk.snapshot            the last world snapshot (subjects, nodes, links, rules, scripts, clock, outline)
//   Desk.do(line)            EVERY change goes through here, as a desk command line. Returns {text, error}.
//   Desk.on(fn)              fn(snapshot, newEvents) after every refresh
//   Desk.registerApp(app)    app = { id, title, glyph, accepts(node, subject) -> bool, open(host, ctx), text(ctx) -> string }
//                            open() draws into `host` (a window body). text() returns what a text-only inhabitant
//                            would read for this window right now; the shell shows it on demand (the "as text" toggle).
//   Desk.children(id), Desk.node(id), Desk.subject(id), Desk.title(id)
// Law of the house: no app keeps state the world does not have, except what is honestly view state
// (scroll, which window is in front), and an app may never change the world except through Desk.do.

const Desk = (() => {
  const q = new URLSearchParams(location.search);
  const session = q.get("session") || "desktop";
  const actor = (q.get("as") || "alex").toLowerCase();
  const apps = [], listeners = [], log = [];
  let snapshot = null, total = 0;

  async function refresh() {
    const r = await fetch(`/api/snapshot?session=${session}&as=${actor}`);
    snapshot = await r.json();
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
      if (e.total !== total) await refresh();
    } catch (_) { /* server away; keep the last picture, the shell says so */ }
    setTimeout(poll, 1500);
  }

  const nodes = () => snapshot ? snapshot.nodes : {};
  return {
    session, actor, apps, log,
    get snapshot() { return snapshot; },
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
    start: async () => { await refresh(); poll(); },
  };
})();
