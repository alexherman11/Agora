(async () => {   // a10486 test: after Send, how long until the box is empty (sent), or what it says if it is not, at most 12 s
  const t0 = Date.now();
  const part = () => [...document.querySelectorAll('[data-key$="/say"]')].find(p => p.querySelector("textarea") && p.offsetHeight);
  const box = () => part() && part().querySelector("textarea");
  while (Date.now() - t0 < 12000) {
    if (box() && box().value === "") return `sent: the box emptied ${Date.now() - t0} ms after Send`;
    await new Promise(r => setTimeout(r, 25));
  }
  const st = part() && part().querySelector(".composer-actions span");
  return `NOT SENT in 12 s; the box keeps "${box() && box().value}"; it says "${st && st.textContent}"`;
})()
