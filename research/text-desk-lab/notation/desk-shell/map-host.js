// map-host.js (a7950): the living map's host. It holds the map frame isolated and is the only way the frame reaches the
// world. The contract is the world note a7875 (THE SEAM): one channel, agora-map/1; 'draw' goes in; 'press', 'drop'
// and 'move' come out; nothing else crosses.
//
// The frame is an <iframe sandbox="allow-scripts">: an opaque origin, so it cannot read this page, its storage or the
// HUD bridge, cannot navigate the top page or open windows, and every request it makes to the desk says Origin: null,
// which the door and deskd refuse (deskd answers only its own pages).
//
// Who is speaking (JEFF c7998: an opaque origin is 'null' for every sandboxed frame, so the string alone names no one):
// each time the frame loads, this page makes a new MessageChannel and hands one port, in a 'hello', to that frame's
// window and nothing else. From then on the frame speaks only on that port, and the draws go to it on that port.
// Nothing else holds the port (it cannot be guessed or named), so a message on it is that frame's; a message posted to
// this window instead is refused, whoever sent it. This page then judges the message's shape and channel, and deskd
// the rest (POST /api/map: op, fields, numbers, the thing, its revision, the scope). The line deskd answers goes to
// /api/do like any press, with the fence it was drawn at, so a stale move is refused there too. The frame never
// sends a string that runs.
(function (host) {
  "use strict";
  const CHANNEL = "agora-map/1";

  // a message posted to this window: always refused, with why (the frame speaks only on its port)
  function judge(e, frame) {
    if (e.origin !== "null") return `wrong origin ${String(e.origin).slice(0, 60)}: only the sandboxed map frame (an opaque origin) speaks here`;
    if (!frame || e.source !== frame) return "not from the map frame";
    return "the map frame speaks only on the port it was given";
  }

  // a message on the port: -> null when it may go on to deskd, else why not
  function judgePort(d) {
    if (d === null || typeof d !== "object" || Array.isArray(d)) return "a message is a JSON object";
    const bad = plain(d, 0);
    if (bad) return bad;
    if (d.channel !== CHANNEL) return `wrong channel ${String(d.channel).slice(0, 40)}: only ${CHANNEL}`;
    return null;
  }

  // structured clone carries more than JSON (NaN, Infinity, dates, maps, ports): only what JSON means passes, so deskd
  // sees the message exactly as the frame meant it
  function plain(v, depth) {
    if (depth > 4) return "a message is too deep";
    if (v === null || typeof v === "string" || typeof v === "boolean") return null;
    if (typeof v === "number") return Number.isFinite(v) ? null : "numbers must be finite";
    if (Array.isArray(v)) { for (const x of v) { const b = plain(x, depth + 1); if (b) return b; } return null; }
    if (typeof v === "object" && Object.getPrototypeOf(v) === Object.prototype) {
      for (const k of Object.keys(v)) { const b = plain(v[k], depth + 1); if (b) return b; }
      return null;
    }
    return "a message holds only JSON values";
  }

  function start(opts) {
    const { session, as, scope = "", frameSrc, el = document.body, status = null } = opts;
    const state = host.__mapHost = { draws: 0, hellos: 0, sent: [], refused: [], answered: [], last: null, problems: [] };
    const iframe = document.createElement("iframe");
    iframe.setAttribute("sandbox", "allow-scripts");          // no allow-same-origin, no top navigation, no popups
    iframe.setAttribute("referrerpolicy", "no-referrer");
    iframe.setAttribute("allow", "");
    iframe.setAttribute("title", "Living map");
    iframe.className = "map-frame";
    iframe.src = frameSrc;
    el.appendChild(iframe);
    const say = t => { if (status) status.textContent = t; };
    const refuse = (why, data) => {
      let raw = ""; try { raw = JSON.stringify(data); } catch (e) { raw = String(data); }
      state.refused.push({ why, data: (raw || "").slice(0, 2000) });
      say(`refused: ${why}`);
    };
    let port = null, pending = null;
    async function refresh() {
      if (!port) return;
      const q = new URLSearchParams({ session, as, scope });
      const r = await (await fetch(`/api/map?${q}`)).json();
      if (r.error) return say(r.error);
      state.last = r.draw; state.problems = r.problems || [];
      state.draws += 1;
      port.postMessage(r.draw);
      if (state.problems.length) say(`${state.problems.length} not drawn: ` + state.problems.map(([id, why]) => `${id}: ${why}`).join("; "));
    }
    const soon = () => { clearTimeout(pending); pending = setTimeout(() => refresh().catch(() => {}), 80); };
    async function heard(d) {
      const why = judgePort(d);
      if (why) return refuse(why, d);
      const r = await (await fetch("/api/map", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session, as, scope, message: d }) })).json();
      if (r.refused || r.error) { refuse(r.refused || r.error, d); return soon(); }
      const gesture = (crypto.randomUUID && crypto.randomUUID()) || String(Math.random()).slice(2);
      const body = { session, as, line: r.line, whole: true, gesture };
      if (r.observed) body.observed = r.observed;
      state.sent.push(r.line);
      const out = await (await fetch("/api/do", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })).json();
      if (out.error) refuse(out.error, d);
      else { state.answered.push({ op: r.op, id: r.id, line: r.line, events: out.events || [], created: out.created || [] }); say(""); }
      soon();                                              // a refused move gets a fresh draw (a7875)
    }
    // a new port for each load of the frame: whatever loaded before it keeps nothing
    iframe.addEventListener("load", () => {
      if (port) port.close();
      const ch = new MessageChannel();
      port = ch.port1;
      port.onmessage = e => { heard(e.data).catch(err => refuse(String(err), e.data)); };
      iframe.contentWindow.postMessage({ channel: CHANNEL, op: "hello" }, "*", [ch.port2]);   // an opaque origin has no name to target
      state.hellos += 1;
      soon();
    });
    host.addEventListener("message", e => refuse(judge(e, iframe.contentWindow), e.data));
    // the world's events repaint the map, as they repaint a page (the door's stream); a poll when there is no door
    if (host.EventSource) {
      const es = new EventSource(`/door/stream?session=${encodeURIComponent(session)}`);
      es.addEventListener("world", soon);
      es.onerror = () => { if (es.readyState === EventSource.CLOSED) es.close(); };
    }
    setInterval(soon, 5000);
    return state;
  }

  host.MapHost = { judge, judgePort, plain, start, CHANNEL };
})(window);
