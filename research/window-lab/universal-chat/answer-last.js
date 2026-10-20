// The key of the last visible Answer in the Conversation's feed (the newest line), so screen.py can press it.
(() => {
  const all = [...document.querySelectorAll("[data-key$='/acts/answer']")].filter(e => e.getClientRects().length);
  return all.length ? all[all.length - 1].dataset.key : "no Answer visible";
})()
