(async () => {   // a10486 test: wait (at most 15 s) until nothing is coming and a chip stands on the draft
  const t0 = Date.now();
  while (Date.now() - t0 < 15000) {
    const c = document.querySelector('[data-key$="/coming"]');
    const chips = document.querySelectorAll('[data-key*="/attachments/cap-"]:not([data-key*="/cap-"] [data-key])');
    if ((!c || c.hidden || !c.offsetHeight) && chips.length) return `${chips.length} chip(s) landed, ${Date.now() - t0} ms after asking`;
    await new Promise(r => setTimeout(r, 50));
  }
  return "NOT LANDED in 15 s";
})()
