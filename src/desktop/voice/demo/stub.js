(() => {
  // a8901 film: a stand-in for the home base's bridge (window.pywebview.api.host), posting to fake_host.py
  const s = new URLSearchParams(location.search).get("session");
  window.__voiceLog = [];
  window.pywebview = { api: { host: async (verb, words) => {
    window.__voiceLog.push([verb, words]);
    const r = await fetch("http://127.0.0.1:8955/host", { method: "POST",
      body: JSON.stringify({ verb, words, session: s, door: location.origin }) });
    return await r.text();
  } } };
  // as hud.py's dress(): any press in the home base stops the voice
  document.addEventListener("pointerdown", () => window.pywebview.api.host("voice.hush", ""), true);
  return "stub for " + s;
})()
