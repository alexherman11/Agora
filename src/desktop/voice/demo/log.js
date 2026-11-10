fetch("http://127.0.0.1:8955/log").then(r => r.json()).then(t => {
  const s = new URLSearchParams(location.search).get("session");
  return { host_log: t.log.slice(-10), said_here: t.said[s] || [], bridge: window.__voiceLog };
})
