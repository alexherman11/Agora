// A stand-in for the seam (a7950 builds the real one): holds three test pins and one route in memory, and speaks
// to the frame as the contract says (a7875, THE SEAM, 'Who is speaking'): each time the frame loads, a new
// MessageChannel; one 'hello' to the frame's window carrying a port; draws out and press/drop/move in on that port
// only. Anything posted to this window is refused, even a well-formed message from the frame itself. A move at a
// rev that is not the pin's current one is refused and the frame is sent a fresh draw.
// Coordinates are the three footprint centroids pins.py took from the extract.
'use strict';
(() => {
  const CH = 'agora-map/1';
  const frame = document.getElementById('map');
  const state = {
    pins: [
      {id: 'p1', rev: 1, lat: 51.519371, lon: -0.127114, height: 0, label: 'British Museum', icon: '1', colour: '#e0603a'},
      {id: 'p2', rev: 1, lat: 51.518174, lon: -0.125872, height: 0, label: 'Museum Tavern', icon: '2', colour: '#e0603a'},
      {id: 'p3', rev: 1, lat: 51.51771, lon: -0.124729, height: 0, label: "St George's Bloomsbury", icon: '3', colour: '#e0603a'},
    ],
    routes: [{id: 'r1', rev: 1, label: 'Museum walk', pins: ['p1', 'p2', 'p3']}],
  };
  const log = [];
  let port = null;
  window.__host = {state, log, draw, frame};
  function say(s) { log.push(s); document.getElementById('log').textContent = s; }
  function draw() { if (port) port.postMessage({channel: CH, op: 'draw', pins: state.pins, routes: state.routes}); }
  frame.addEventListener('load', () => {
    if (port) port.close();
    const ch = new MessageChannel();
    port = ch.port1;
    port.onmessage = ev => answer(ev.data);
    frame.contentWindow.postMessage({channel: CH, op: 'hello'}, '*', [ch.port2]);
    draw();
  });
  window.addEventListener('message', () => say('refused: posted to the window, not on the port'));
  function answer(m) {
    if (!m || typeof m !== 'object' || Array.isArray(m) || m.channel !== CH) return say('refused: wrong channel');
    const ok = (v, lo, hi) => typeof v === 'number' && Number.isFinite(v) && v >= lo && v <= hi;
    if (m.op === 'press') {
      const p = state.pins.find(p => p.id === m.id);
      return say(p ? `pressed ${p.label}` : 'refused: press of an unknown pin');
    }
    if (m.op === 'drop') {
      if (!ok(m.lat, -90, 90) || !ok(m.lon, -180, 180)) return say('refused: drop out of range');
      return say(`dropped a pin at ${m.lat.toFixed(6)}, ${m.lon.toFixed(6)} (lat, lon); a stand-in makes no note`);
    }
    if (m.op === 'move') {
      const p = state.pins.find(p => p.id === m.id);
      if (!p) return say('refused: move of an unknown pin');
      if (!ok(m.lat, -90, 90) || !ok(m.lon, -180, 180)) return say('refused: move out of range');
      if (m.rev !== p.rev) { say(`refused: ${p.label} changed since (rev ${m.rev}, now ${p.rev})`); return draw(); }
      p.lat = m.lat; p.lon = m.lon; p.rev += 1;
      say(`moved ${p.label} to ${p.lat.toFixed(6)}, ${p.lon.toFixed(6)} (rev ${p.rev})`);
      return draw();
    }
    say('refused: unknown op');
  }
})();
