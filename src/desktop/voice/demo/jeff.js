// a8901 film: JEFF's answer lands in the COPY's Conversation (this page's own door, a screen.py copy)
fetch("/api/do", { method: "POST", body: JSON.stringify({ session: new URLSearchParams(location.search).get("session"), as: "jeff",
  line: 'read a5080 :1; do append a5080 line="Done: the board is open. Three cards wait on you; the top one is the voice slice." to=alex' }) })
  .then(r => r.json()).then(r => (r.text || r.error || "").slice(0, 200))
