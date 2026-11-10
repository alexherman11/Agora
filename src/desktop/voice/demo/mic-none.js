// a9138 film: the fake engine reports no input device
fetch("http://127.0.0.1:8955/engine", { method: "POST", body: JSON.stringify({
  session: new URLSearchParams(location.search).get("session"), do: "mic", text: "" }) }).then(r => r.text())
