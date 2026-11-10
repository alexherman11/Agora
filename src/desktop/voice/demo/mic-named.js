// a9138 film: the fake engine reports a wrong default, as Alex's PC could have
fetch("http://127.0.0.1:8955/engine", { method: "POST", body: JSON.stringify({
  session: new URLSearchParams(location.search).get("session"), do: "mic", text: "Microphone (Wireless Controller)" }) })
  .then(r => r.text())
