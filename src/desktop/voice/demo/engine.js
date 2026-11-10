// a8901 film: the fake voice ends its sentence on its own (as a voice that finished reading)
fetch("http://127.0.0.1:8955/engine", { method: "POST", body: JSON.stringify({ session: new URLSearchParams(location.search).get("session"), do: "done" }) }).then(r => r.text())
