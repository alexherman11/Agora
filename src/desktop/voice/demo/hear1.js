fetch("http://127.0.0.1:8955/engine", { method: "POST", body: JSON.stringify({ session: new URLSearchParams(location.search).get("session"), do: "hear", text: "show me the" }) }).then(r => r.text())
