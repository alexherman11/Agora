// refused.js (a6010): the desk refuses a Looks good (a stand-in answer, nothing reaches the copy): the card hides on
// the press, then must be drawn again with the refusal said. Returns what was seen at the press and after the answer.
(async () => {
  const f0 = window.fetch;
  window.fetch = (u, o) => String(u).startsWith("/api/do")
    ? new Promise(res => setTimeout(() => res(new Response(JSON.stringify({ text: "ERR refused: a test refusal (refused.js)" }))), 250))
    : f0(u, o);
  const ok = [...document.querySelectorAll("[data-key]")].find(e => /\/reviews\/a\d+\/line\/ok$/.test(e.dataset.key) && e.getClientRects().length);
  const card = ok.closest('[data-fold-inline]');
  const shown = () => getComputedStyle(card).visibility !== "hidden" && card.isConnected;
  ok.click();
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  const atPress = shown();
  await new Promise(r => setTimeout(r, 1500));
  window.fetch = f0;
  const status = document.getElementById("status");
  return { card: card.dataset.key, shownAtPress: atPress, shownAfterRefusal: shown(), status: status && !status.hidden ? status.textContent : "(no status line)" };
})()
