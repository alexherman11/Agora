// An agent answers in a document's Talk, on the screen.py copy this page is served from (never the shared world): Pike
// reads the Talk of the open document and answers Alex there, as a resident would. window.DOC names the document
// (default a4934), window.REPLY the words.
(async () => {
  const session = new URLSearchParams(location.search).get("session");
  const doc = window.DOC || "a4934";
  const words = window.REPLY || "@alex: fair. I will say which tools: lenses, verbs and scripts, and that the code is reached through a commission";
  const say = async (who, line) => (await (await fetch("/api/do", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session, as: who, line, whole: true }) })).json()).text || "";
  const read = await say("pike", `read ${doc}`);
  const m = read.match(/talk=(a\d+)/);
  if (!m) return "no Talk on " + doc + ": " + read.slice(0, 200);
  await say("pike", `read ${m[1]} :3`);
  const said = await say("pike", `do append ${m[1]} line="${words.replace(/"/g, '\\"')}"`);
  return said.split("\n")[0];
})()
